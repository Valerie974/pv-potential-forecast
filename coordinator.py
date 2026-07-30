"""DataUpdateCoordinator — PV Potential Forecast.

Fichier : coordinator.py
Rôle : Orchestre la récupération des données (Forecast.Solar + météo Vevor),
gère le rate limit Forecast.Solar (12 req/heure, seuil 10), met en cache les
réponses et expose les données combinées aux sensors.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    CONFIDENCE_FRESH_120_MIN,
    CONFIDENCE_FRESH_240_MIN,
    CONFIDENCE_FRESH_60_MIN,
    CONFIDENCE_VALUE_2H,
    CONFIDENCE_VALUE_4H,
    CONFIDENCE_VALUE_FRESH,
    CONFIDENCE_VALUE_STALE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_METEO_FRANCE_ENTITY,
    CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
    CONF_WUNDERGROUND_PRECIP_ENTITY,
    CONF_WUNDERGROUND_TEMP_ENTITY,
    CONF_WUNDERGROUND_UV_INDEX_ENTITY,
    CONF_WUNDERGROUND_WEATHER_ENTITY,
    FORECAST_SOLAR_CALLS_PER_UPDATE,
    FORECAST_SOLAR_HOURLY_LIMIT,
    FORECAST_SOLAR_SAFETY_THRESHOLD,
    POLL_INTERVAL_MINUTES,
    SOURCE_ACTIVE_FORECAST_SOLAR,
    SOURCE_ACTIVE_NONE,
)
from .providers.forecast_solar_provider import (
    ForecastSolarError,
    ForecastSolarProvider,
)
from .providers.weather_provider import WeatherProvider
from .strategies.single_source_strategy import SingleSourceStrategy

_LOGGER = logging.getLogger(__name__)


class ForecastSolarRateLimiter:
    """Gère le rate limit Forecast.Solar (12 appels/heure par IP).

    Stratégie : 5 appels par mise à jour (1 par MPPT).
    Seuil de sécurité : 10 appels/heure (83 % du quota).

    Attributes:
        MAX_CALLS_PER_HOUR: Quota Forecast.Solar gratuit (12).
        SAFETY_THRESHOLD: Seuil de sécurité (10).
        CALLS_PER_UPDATE: Appels par mise à jour (5).
        MIN_INTERVAL_MINUTES: Intervalle minimum entre mises à jour (60).
    """

    MAX_CALLS_PER_HOUR: int = FORECAST_SOLAR_HOURLY_LIMIT
    SAFETY_THRESHOLD: int = FORECAST_SOLAR_SAFETY_THRESHOLD
    CALLS_PER_UPDATE: int = FORECAST_SOLAR_CALLS_PER_UPDATE
    MIN_INTERVAL_MINUTES: int = POLL_INTERVAL_MINUTES

    def __init__(self) -> None:
        """Initialise le rate limiter avec un historique vide."""
        self._call_history: list[datetime] = []

    def can_update(self) -> bool:
        """Vérifie si une mise à jour est possible sans dépasser le quota.

        Returns:
            True si une mise à jour (5 appels) est possible, False sinon.
        """
        self._clean_history()
        return (
            len(self._call_history) + self.CALLS_PER_UPDATE
            <= self.SAFETY_THRESHOLD
        )

    def register_calls(self, count: int | None = None) -> None:
        """Enregistre n appels dans l'historique.

        Args:
            count: Nombre d'appels à enregistrer.
                Défaut : CALLS_PER_UPDATE (5).
        """
        if count is None:
            count = self.CALLS_PER_UPDATE
        now = datetime.now(timezone.utc)
        for _ in range(count):
            self._call_history.append(now)

    def time_until_next_slot(self) -> timedelta:
        """Retourne le temps restant avant qu'un slot se libère.

        Returns:
            timedelta jusqu'au prochain slot disponible.
            Retourne timedelta(0) si un slot est disponible.
        """
        self._clean_history()
        if len(self._call_history) < self.SAFETY_THRESHOLD:
            return timedelta(0)

        # Trouver le plus ancien appel dans la fenêtre d'1 heure
        oldest = min(self._call_history)
        wait = timedelta(seconds=3600) - (
            datetime.now(timezone.utc) - oldest
        )
        return max(wait, timedelta(0))

    def remaining_calls(self) -> int:
        """Retourne le nombre d'appels restants dans la fenêtre courante.

        Returns:
            Nombre d'appels restants avant d'atteindre le seuil de sécurité.
        """
        self._clean_history()
        return max(0, self.SAFETY_THRESHOLD - len(self._call_history))

    def _clean_history(self) -> None:
        """Nettoie l'historique en supprimant les appels de plus d'1 heure."""
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=3600)
        self._call_history = [t for t in self._call_history if t > cutoff]


def calculate_confidence(
    source_active: str,
    last_success: datetime,
    now: datetime | None = None,
) -> float:
    """Calcule un indice de confiance heuristique [0, 1].

    Phase 1 — heuristique simple basée sur la fraîcheur des données :
        - 1.0 si les données sont fraîches (< 60 min)
        - 0.8 si les données ont < 2h
        - 0.5 si les données ont < 4h
        - 0.2 si les données sont anciennes (> 4h)
        - 0.0 si source_active == "none"

    Args:
        source_active: Source active ("forecast_solar" ou "none").
        last_success: Timestamp de la dernière mise à jour réussie.
        now: Heure de référence (défaut: maintenant).

    Returns:
        Indice de confiance [0.0, 1.0].
    """
    if source_active == SOURCE_ACTIVE_NONE:
        return 0.0

    if now is None:
        now = datetime.now(timezone.utc)

    age_minutes = (now - last_success).total_seconds() / 60

    if age_minutes < CONFIDENCE_FRESH_60_MIN:
        return CONFIDENCE_VALUE_FRESH
    elif age_minutes < CONFIDENCE_FRESH_120_MIN:
        return CONFIDENCE_VALUE_2H
    elif age_minutes < CONFIDENCE_FRESH_240_MIN:
        return CONFIDENCE_VALUE_4H
    else:
        return CONFIDENCE_VALUE_STALE


class PVForecastCoordinator(DataUpdateCoordinator):
    """Coordinator principal — gère le polling et le rate limit.

    Attributes:
        SCAN_INTERVAL_MINUTES: Intervalle de polling (60 min).
    """

    SCAN_INTERVAL_MINUTES: int = POLL_INTERVAL_MINUTES

    def __init__(
        self,
        hass: HomeAssistant,
        entry: Any,
    ) -> None:
        """Initialise le coordinator.

        Args:
            hass: Instance Home Assistant.
            entry: ConfigEntry avec les paramètres utilisateur.
        """
        super().__init__(
            hass,
            logger=_LOGGER,
            name="PV Potential Forecast",
            update_interval=timedelta(minutes=self.SCAN_INTERVAL_MINUTES),
        )

        self._entry = entry
        self._config = entry.data

        # Récupérer la session HTTP partagée de HA
        try:
            from homeassistant.helpers.aiohttp_client import (
                async_get_clientsession,
            )
            session = async_get_clientsession(hass)
        except ImportError:
            session = None

        # Instancier le rate limiter
        self.rate_limiter = ForecastSolarRateLimiter()

        # Instancier le provider Forecast.Solar
        self._forecast_solar_provider = ForecastSolarProvider(
            session=session,
            latitude=self._config.get(CONF_LATITUDE, -20.9295),
            longitude=self._config.get(CONF_LONGITUDE, 55.3520),
        )

        # Instancier le provider météo
        self._weather_provider = WeatherProvider(
            hass=hass,
            irradiance_entity=self._config.get(
                CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
                "sensor.ilapos13_solar_radiation",
            ),
            temp_entity=self._config.get(
                CONF_WUNDERGROUND_TEMP_ENTITY,
                "sensor.ilapos13_temperature",
            ),
            precip_entity=self._config.get(
                CONF_WUNDERGROUND_PRECIP_ENTITY,
                "sensor.ilapos13_precipitation_rate",
            ),
            uv_index_entity=self._config.get(
                CONF_WUNDERGROUND_UV_INDEX_ENTITY,
                "sensor.ilapos13_uv_index",
            ),
            weather_entity=self._config.get(
                CONF_WUNDERGROUND_WEATHER_ENTITY,
                "weather.ilapos13",
            ),
            meteo_france_entity=self._config.get(
                CONF_METEO_FRANCE_ENTITY,
                "sensor.meteo_france_forecast_for_city_la_possession_reunion_re_saint_denis_pressure",
            ),
        )

        # Instancier la stratégie
        self._strategy = SingleSourceStrategy(
            forecast_solar_provider=self._forecast_solar_provider,
            weather_provider=self._weather_provider,
        )

        # Suivi de l'état
        self._last_success: datetime | None = None
        self._source_active: str = SOURCE_ACTIVE_NONE
        self._calls_made: int = 0

    @property
    def strategy(self) -> SingleSourceStrategy:
        """Retourne la stratégie active."""
        return self._strategy

    @property
    def forecast_solar_provider(self) -> ForecastSolarProvider:
        """Retourne le provider Forecast.Solar."""
        return self._forecast_solar_provider

    @property
    def weather_provider(self) -> WeatherProvider:
        """Retourne le provider météo."""
        return self._weather_provider

    @property
    def last_success_time(self) -> datetime | None:
        """Retourne le timestamp de la dernière mise à jour réussie."""
        return self._last_success

    @property
    def source_active(self) -> str:
        """Retourne la source active courante."""
        return self._source_active

    @property
    def calls_made(self) -> int:
        """Retourne le nombre d'appels effectués lors de la dernière mise à jour."""
        return self._calls_made

    def get_confidence(self) -> float:
        """Calcule l'indice de confiance actuel.

        Returns:
            Indice de confiance [0.0, 1.0].
        """
        if self._last_success is None:
            return 0.0
        return calculate_confidence(
            self._source_active, self._last_success
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Mise à jour des données — respecte le rate limit.

        Returns:
            Dictionnaire structuré des données combinées :
                - hourly_forecast: liste de HourlyResult.to_dict()
                - today_kwh, tomorrow_kwh
                - source_active, confidence, last_update
                - sources_detail
                - weather_current
                - rate_limiter_remaining

        Raises:
            UpdateFailed: Si la mise à jour échoue complètement.
        """
        # Vérifier le rate limit
        if not self.rate_limiter.can_update():
            wait_time = self.rate_limiter.time_until_next_slot()
            _LOGGER.warning(
                "Rate limit Forecast.Solar atteint. "
                "Prochaine fenêtre dans %.1f minutes. "
                "Utilisation du cache.",
                wait_time.total_seconds() / 60,
            )
            # Retourner les données en cache si disponibles
            if self.data:
                return self.data
            raise UpdateFailed(
                f"Rate limit atteint, prochain slot dans "
                f"{wait_time.total_seconds() / 60:.1f} min"
            )

        try:
            # Effectuer les 5 appels Forecast.Solar
            all_forecasts = (
                await self._forecast_solar_provider.get_all_forecasts()
            )
            self.rate_limiter.register_calls(self.rate_limiter.CALLS_PER_UPDATE)
            self._calls_made = self.rate_limiter.CALLS_PER_UPDATE
            self._source_active = SOURCE_ACTIVE_FORECAST_SOLAR
            self._last_success = datetime.now(timezone.utc)
        except ForecastSolarError as exc:
            _LOGGER.error(
                "Erreur Forecast.Solar: %s — utilisation des données en cache",
                exc,
            )
            self._source_active = SOURCE_ACTIVE_NONE
            if self.data:
                return self.data
            raise UpdateFailed(f"Erreur Forecast.Solar: {exc}") from exc

        # Récupérer les données météo (Vevor + fallback)
        try:
            weather = await self._weather_provider.get_current_weather()
            weather_dict = weather.to_dict()
        except Exception as exc:
            _LOGGER.warning("Erreur météo: %s — continuons sans météo", exc)
            weather_dict = {"source": "none"}

        # Calculer la prévision horaire via la stratégie
        try:
            hourly_results = await self._strategy.compute_forecast(hours=48)
            hourly_list = [r.to_dict() for r in hourly_results]
        except Exception as exc:
            _LOGGER.error("Erreur calcul stratégie: %s", exc)
            hourly_list = []
            if self.data:
                return self.data

        # Calculer l'énergie potentielle aujourd'hui et demain
        try:
            today_kwh = await self._strategy.get_today_energy_kwh()
            tomorrow_kwh = await self._strategy.get_tomorrow_energy_kwh()
        except Exception as exc:
            _LOGGER.warning("Erreur calcul énergie: %s", exc)
            today_kwh = 0.0
            tomorrow_kwh = 0.0

        # Puissance courante (heure actuelle)
        current_power = 0.0
        for entry in hourly_list:
            if entry.get("is_current_hour"):
                current_power = entry.get("pv_total_w", 0.0)
                break

        # Détail des sources
        sources_detail = {
            "forecast_solar": {
                "status": "ok" if self._source_active == SOURCE_ACTIVE_FORECAST_SOLAR else "error",
                "calls_made": self._calls_made,
                "rate_limit_remaining": self.rate_limiter.remaining_calls(),
                "rate_limit_hourly_max": ForecastSolarRateLimiter.MAX_CALLS_PER_HOUR,
                "last_success": self._last_success.isoformat() if self._last_success else None,
            },
            "weather": {
                "primary_source": weather_dict.get("source", "unknown"),
                "cloud_cover_source": weather_dict.get("cloud_cover_source"),
                "fallback_source": "meteo_france",
                "irradiance_sensor": self._config.get(
                    CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
                    "sensor.ilapos13_solar_radiation",
                ),
                "irradiance_available_current_hour": weather_dict.get("irradiance_ghi") is not None,
                "irradiance_available_forecast": False,
                "uv_index_sensor": self._config.get(
                    CONF_WUNDERGROUND_UV_INDEX_ENTITY,
                    "sensor.ilapos13_uv_index",
                ),
            },
        }

        # Construire le dictionnaire de données
        data: dict[str, Any] = {
            "hourly_forecast": hourly_list,
            "today_kwh": round(today_kwh, 2),
            "tomorrow_kwh": round(tomorrow_kwh, 2),
            "current_power_w": round(current_power, 1),
            "source_active": self._source_active,
            "confidence": self.get_confidence(),
            "last_update": self._last_success.isoformat() if self._last_success else None,
            "sources_detail": sources_detail,
            "weather_current": weather_dict,
            "rate_limiter_remaining": self.rate_limiter.remaining_calls(),
        }

        _LOGGER.info(
            "Mise à jour PV Forecast: %d heures, today=%.2f kWh, "
            "tomorrow=%.2f kWh, courant=%.1f W, confidence=%.2f",
            len(hourly_list),
            today_kwh,
            tomorrow_kwh,
            current_power,
            self.get_confidence(),
        )

        return data
"""Provider Forecast.Solar — PV Potential Forecast.

Fichier : providers/forecast_solar_provider.py
Rôle : Effectue les 5 appels API Forecast.Solar (1 par MPPT) pour récupérer
les prévisions de potentiel photovoltaïque sur 48h.

URL : https://api.forecast.solar/estimate/{lat}/{lon}/{tilt}/{azimuth}/{capacity_kW}
Quota : 12 req/heure/IP (gratuit, pas de clé API)

Gestion du cache :
    - TTL 60 minutes (FORECAST_SOLAR_CACHE_TTL_MIN)
    - Si les données en cache sont < 60 min, réutilisées sans nouvel appel
    - Le cache est stocké par MPPT (clé = nom du MPPT)

Gestion des erreurs :
    - Timeout : 10 secondes par appel
    - Rate limit (HTTP 429) : lève ForecastSolarRateLimitError
    - API down (5xx) : lève ForecastSolarError
    - En cas d'erreur, le cache précédent est conservé

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp

from ..const import (
    ATON_PV1_AZIMUTH_API,
    ATON_PV1_CAPACITY_W,
    ATON_PV2_AZIMUTH_API,
    ATON_PV2_CAPACITY_W,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TILT,
    DEYE_PV1_AZIMUTH_API,
    DEYE_PV1_CAPACITY_W,
    DEYE_PV2_AZIMUTH_API,
    DEYE_PV2_CAPACITY_W,
    DEYE_PV3_AZIMUTH_API,
    DEYE_PV3_CAPACITY_W,
    FORECAST_SOLAR_BASE_URL,
    FORECAST_SOLAR_CACHE_TTL_MIN,
)

_LOGGER = logging.getLogger(__name__)

# Timeout HTTP pour chaque appel Forecast.Solar (secondes)
FORECAST_SOLAR_TIMEOUT_SECONDS = 10


class ForecastSolarError(Exception):
    """Erreur de base pour le provider Forecast.Solar."""


class ForecastSolarRateLimitError(ForecastSolarError):
    """Rate limit Forecast.Solar atteint (HTTP 429)."""


@dataclass
class MPPTForecast:
    """Prévision Forecast.Solar pour un MPPT donné.

    Attributes:
        mppt_name: Nom du MPPT (ex. "DEYE_PV1").
        azimuth: Azimuth utilisé pour l'appel API (-180 à +180).
        capacity_w: Capacité du MPPT en watts.
        watts: Dict {datetime ISO → puissance en W} — prévision nominale.
        watt_hours_period: Dict {datetime ISO → énergie horaire en Wh}.
        watt_hours: Dict {datetime ISO → énergie cumulée en Wh}.
        watt_hours_day: Dict {date ISO → énergie du jour en Wh}.
        fetched_at: Timestamp de récupération (UTC).
    """

    mppt_name: str
    azimuth: float
    capacity_w: float
    watts: dict[str, float] = field(default_factory=dict)
    watt_hours_period: dict[str, float] = field(default_factory=dict)
    watt_hours: dict[str, float] = field(default_factory=dict)
    watt_hours_day: dict[str, float] = field(default_factory=dict)
    fetched_at: datetime | None = None


class ForecastSolarProvider:
    """Provider Forecast.Solar — effectue les 5 appels API MPPT.

    Attributes:
        latitude: Latitude du site (-20.9295 par défaut).
        longitude: Longitude du site (55.3520 par défaut).
        tilt: Inclinaison des panneaux (3° par défaut).
    """

    def __init__(
        self,
        session: aiohttp.ClientSession | None = None,
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
        tilt: float = DEFAULT_TILT,
    ) -> None:
        """Initialise le provider Forecast.Solar.

        Args:
            session: Session aiohttp (recommandé — réutilise les connexions).
            latitude: Latitude du site.
            longitude: Longitude du site.
            tilt: Inclinaison des panneaux (degrés).
        """
        self._session = session
        self._latitude = latitude
        self._longitude = longitude
        self._tilt = tilt

        # Cache interne : {mppt_name: (MPPTForecast, datetime_fetched)}
        self._cache: dict[str, tuple[MPPTForecast, datetime]] = {}

        # Configuration des 5 MPPT pour Forecast.Solar
        self._mppt_configs: list[dict[str, Any]] = [
            {
                "name": "ATON_PV1",
                "azimuth": ATON_PV1_AZIMUTH_API,
                "capacity_w": ATON_PV1_CAPACITY_W,
            },
            {
                "name": "ATON_PV2",
                "azimuth": ATON_PV2_AZIMUTH_API,
                "capacity_w": ATON_PV2_CAPACITY_W,
            },
            {
                "name": "DEYE_PV1",
                "azimuth": DEYE_PV1_AZIMUTH_API,
                "capacity_w": DEYE_PV1_CAPACITY_W,
            },
            {
                "name": "DEYE_PV2",
                "azimuth": DEYE_PV2_AZIMUTH_API,
                "capacity_w": DEYE_PV2_CAPACITY_W,
            },
            {
                "name": "DEYE_PV3",
                "azimuth": DEYE_PV3_AZIMUTH_API,
                "capacity_w": DEYE_PV3_CAPACITY_W,
            },
        ]

    def _is_cache_valid(self, mppt_name: str) -> bool:
        """Vérifie si le cache pour un MPPT est encore valide (TTL 60 min).

        Args:
            mppt_name: Nom du MPPT.

        Returns:
            True si le cache est valide, False sinon.
        """
        if mppt_name not in self._cache:
            return False
        _, fetched_at = self._cache[mppt_name]
        age = datetime.now(timezone.utc) - fetched_at
        return age < timedelta(minutes=FORECAST_SOLAR_CACHE_TTL_MIN)

    def _get_cached(self, mppt_name: str) -> MPPTForecast | None:
        """Retourne la prévision en cache pour un MPPT, ou None.

        Args:
            mppt_name: Nom du MPPT.

        Returns:
            MPPTForecast en cache, ou None si le cache est invalide.
        """
        if self._is_cache_valid(mppt_name):
            return self._cache[mppt_name][0]
        return None

    def _store_cache(self, forecast: MPPTForecast) -> None:
        """Stocke une prévision dans le cache.

        Args:
            forecast: Prévision à mettre en cache.
        """
        self._cache[forecast.mppt_name] = (forecast, datetime.now(timezone.utc))

    def _build_url(self, mppt_config: dict[str, Any]) -> str:
        """Construit l'URL Forecast.Solar pour un MPPT.

        Args:
            mppt_config: Configuration du MPPT (name, azimuth, capacity_w).

        Returns:
            URL complète pour l'appel API.
        """
        capacity_kw = mppt_config["capacity_w"] / 1000.0
        url = (
            f"{FORECAST_SOLAR_BASE_URL}/"
            f"{self._latitude}/{self._longitude}/{self._tilt}/"
            f"{mppt_config['azimuth']}/{capacity_kw}"
        )
        return url

    async def _fetch_single_mppt(
        self, mppt_config: dict[str, Any]
    ) -> MPPTForecast:
        """Effectue un seul appel Forecast.Solar pour un MPPT.

        Args:
            mppt_config: Configuration du MPPT (name, azimuth, capacity_w).

        Returns:
            MPPTForecast — prévision pour ce MPPT.

        Raises:
            ForecastSolarRateLimitError: Si l'API retourne 429.
            ForecastSolarError: Si l'API retourne une erreur ou timeout.
        """
        url = self._build_url(mppt_config)
        mppt_name = mppt_config["name"]
        _LOGGER.debug("Appel Forecast.Solar : %s (%s)", url, mppt_name)

        timeout = aiohttp.ClientTimeout(total=FORECAST_SOLAR_TIMEOUT_SECONDS)

        try:
            if self._session is not None:
                session = self._session
                async with session.get(url, timeout=timeout) as response:
                    return await self._parse_response(response, mppt_config)
            else:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(url) as response:
                        return await self._parse_response(response, mppt_config)
        except aiohttp.ClientError as exc:
            _LOGGER.error("Erreur réseau Forecast.Solar (%s): %s", mppt_name, exc)
            raise ForecastSolarError(f"Erreur réseau: {exc}") from exc
        except TimeoutError as exc:
            _LOGGER.error("Timeout Forecast.Solar (%s)", mppt_name)
            raise ForecastSolarError(f"Timeout: {mppt_name}") from exc

    async def _parse_response(
        self,
        response: aiohttp.ClientResponse,
        mppt_config: dict[str, Any],
    ) -> MPPTForecast:
        """Parse la réponse JSON de Forecast.Solar.

        Args:
            response: Réponse HTTP aiohttp.
            mppt_config: Configuration du MPPT.

        Returns:
            MPPTForecast — prévision parsée.

        Raises:
            ForecastSolarRateLimitError: Si HTTP 429.
            ForecastSolarError: Si HTTP erreur ou JSON invalide.
        """
        mppt_name = mppt_config["name"]

        if response.status == 429:
            raise ForecastSolarRateLimitError(
                f"Rate limit atteint pour {mppt_name}"
            )
        if response.status != 200:
            body = await response.text()
            raise ForecastSolarError(
                f"HTTP {response.status} pour {mppt_name}: {body[:200]}"
            )

        data = await response.json()

        # Vérifier le code de message (0 = success)
        message = data.get("message", {})
        code = message.get("code", -1)
        if code != 0:
            text = message.get("text", "Erreur inconnue")
            raise ForecastSolarError(
                f"Erreur API Forecast.Solar ({mppt_name}): code={code}, text={text}"
            )

        result = data.get("result", {})

        forecast = MPPTForecast(
            mppt_name=mppt_name,
            azimuth=mppt_config["azimuth"],
            capacity_w=mppt_config["capacity_w"],
            watts=result.get("watts", {}),
            watt_hours_period=result.get("watt_hours_period", {}),
            watt_hours=result.get("watt_hours", {}),
            watt_hours_day=result.get("watt_hours_day", {}),
            fetched_at=datetime.now(timezone.utc),
        )

        self._store_cache(forecast)
        _LOGGER.debug(
            "Forecast.Solar %s: %d points horaires récupérés",
            mppt_name,
            len(forecast.watts),
        )
        return forecast

    async def get_mppt_forecast(self, mppt_name: str) -> MPPTForecast:
        """Retourne la prévision pour un MPPT (cache ou nouvel appel).

        Args:
            mppt_name: Nom du MPPT (ex. "DEYE_PV1").

        Returns:
            MPPTForecast — prévision pour ce MPPT.

        Raises:
            ValueError: Si mppt_name n'existe pas.
            ForecastSolarError: En cas d'erreur API (si pas de cache valide).
        """
        # Vérifier le cache d'abord
        cached = self._get_cached(mppt_name)
        if cached is not None:
            _LOGGER.debug("Cache valide pour %s", mppt_name)
            return cached

        # Trouver la config du MPPT
        mppt_config = None
        for cfg in self._mppt_configs:
            if cfg["name"] == mppt_name:
                mppt_config = cfg
                break
        if mppt_config is None:
            raise ValueError(f"MPPT inconnu: {mppt_name}")

        return await self._fetch_single_mppt(mppt_config)

    async def get_all_forecasts(self) -> dict[str, MPPTForecast]:
        """Effectue les 5 appels Forecast.Solar (1 par MPPT).

        Utilise le cache si les données sont fraîches (< 60 min).
        Si un MPPT est en cache valide, il n'est pas re-téléchargé.

        Returns:
            Dictionnaire {mppt_name: MPPTForecast} avec les 5 MPPT.

        Raises:
            ForecastSolarError: Si tous les appels échouent et aucun
                cache valide n'est disponible.
        """
        results: dict[str, MPPTForecast] = {}
        errors: list[str] = []

        for mppt_config in self._mppt_configs:
            name = mppt_config["name"]

            # Vérifier le cache
            cached = self._get_cached(name)
            if cached is not None:
                results[name] = cached
                continue

            # Effectuer l'appel
            try:
                forecast = await self._fetch_single_mppt(mppt_config)
                results[name] = forecast
            except ForecastSolarRateLimitError as exc:
                # Rate limit — utiliser le cache même s'il est ancien
                _LOGGER.warning(
                    "Rate limit Forecast.Solar pour %s: %s — utilisation cache",
                    name,
                    exc,
                )
                if name in self._cache:
                    results[name] = self._cache[name][0]
                else:
                    errors.append(f"{name}: rate_limit")
            except ForecastSolarError as exc:
                _LOGGER.error(
                    "Erreur Forecast.Solar pour %s: %s — utilisation cache",
                    name,
                    exc,
                )
                if name in self._cache:
                    results[name] = self._cache[name][0]
                else:
                    errors.append(f"{name}: {exc}")

        if not results and errors:
            raise ForecastSolarError(
                f"Tous les appels Forecast.Solar ont échoué: {errors}"
            )

        return results

    def clear_cache(self) -> None:
        """Vide le cache interne (tous les MPPT)."""
        self._cache.clear()
        _LOGGER.debug("Cache Forecast.Solar vidé")

    def get_cache_info(self) -> dict[str, dict[str, Any]]:
        """Retourne des informations sur l'état du cache.

        Returns:
            Dictionnaire {mppt_name: {fetched_at, age_minutes, valid}}.
        """
        info: dict[str, dict[str, Any]] = {}
        now = datetime.now(timezone.utc)
        for name, (forecast, fetched_at) in self._cache.items():
            age = now - fetched_at
            info[name] = {
                "fetched_at": fetched_at.isoformat(),
                "age_minutes": round(age.total_seconds() / 60, 1),
                "valid": self._is_cache_valid(name),
            }
        return info
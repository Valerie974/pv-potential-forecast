"""Provider météo — PV Potential Forecast.

Fichier : providers/weather_provider.py
Rôle : Récupère les données météo depuis la station Vevor (priorité 1)
+ weather.ilapos13 (couverture nuageuse locale, priorité 1b) + Météo-France
(fallback, priorité 2). Expose une interface unifiée pour le coordinator.

Sources :
    - Vevor sensors (sensor.ilapos13_*) : GHI, température, précipitations,
      UV, humidité, vent, pression, etc.
    - weather.ilapos13 : couverture nuageuse (mapping condition → %)
    - Météo-France : fallback (St-Denis — micro-climat différent)

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from ..const import (
    CONDITION_TO_CLOUD_COVER,
    METEO_FRANCE_FALLBACK_ENTITY,
    VEVOR_HUMIDITY_ENTITY,
    VEVOR_IRRADIANCE_ENTITY,
    VEVOR_PRECIP_RATE_ENTITY,
    VEVOR_TEMPERATURE_ENTITY,
    VEVOR_UV_INDEX_ENTITY,
    VEVOR_WEATHER_ENTITY,
    VEVOR_WIND_SPEED_ENTITY,
)

_LOGGER = logging.getLogger(__name__)


def _safe_float(value: Any) -> float | None:
    """Convertit une valeur en float de manière sécurisée.

    Args:
        value: Valeur à convertir (str, int, float, ou None).

    Returns:
        Float ou None si la conversion échoue.
    """
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


@dataclass
class WeatherData:
    """Données météo unifiées (Vevor + Météo-France fallback).

    Attributes:
        irradiance_ghi: Irradiance GHI W/m² (Vevor, heure courante uniquement).
        temperature_c: Température °C (Vevor prioritaire).
        cloud_cover_pct: Couverture nuageuse % (weather.ilapos13 prioritaire).
        cloud_cover_source: Source du cloud cover.
        cloud_cover_reliability: Fiabilité ("high" si Vevor, "low" si MF).
        precipitation_mm: Précipitations mm/h (Vevor).
        uv_index: Indice UV (Vevor).
        humidity_pct: Humidité relative % (Vevor).
        wind_speed_kmh: Vent km/h (Vevor).
        source: Source principale ("vevor_wunderground" ou "meteo_france_fallback").
    """

    irradiance_ghi: float | None = None
    temperature_c: float | None = None
    cloud_cover_pct: float | None = None
    cloud_cover_source: str | None = None
    cloud_cover_reliability: str | None = None
    precipitation_mm: float | None = None
    uv_index: float | None = None
    humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    source: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation JSON.

        Returns:
            Dictionnaire avec toutes les données météo.
        """
        return {
            "irradiance_ghi": self.irradiance_ghi,
            "temperature_c": self.temperature_c,
            "cloud_cover_pct": self.cloud_cover_pct,
            "cloud_cover_source": self.cloud_cover_source,
            "cloud_cover_reliability": self.cloud_cover_reliability,
            "precipitation_mm": self.precipitation_mm,
            "uv_index": self.uv_index,
            "humidity_pct": self.humidity_pct,
            "wind_speed_kmh": self.wind_speed_kmh,
            "source": self.source,
        }


class WeatherProvider:
    """Provider météo — Vevor (priorité) + Météo-France (fallback).

    Gère la hiérarchie des sources :
        1. Station Vevor (sensors) — source météo principale
        1b. weather.ilapos13 — couverture nuageuse locale
        2. Météo-France — fallback (St-Denis)
    """

    def __init__(
        self,
        hass: Any,
        irradiance_entity: str = VEVOR_IRRADIANCE_ENTITY,
        temp_entity: str = VEVOR_TEMPERATURE_ENTITY,
        precip_entity: str = VEVOR_PRECIP_RATE_ENTITY,
        uv_index_entity: str = VEVOR_UV_INDEX_ENTITY,
        weather_entity: str = VEVOR_WEATHER_ENTITY,
        meteo_france_entity: str = METEO_FRANCE_FALLBACK_ENTITY,
        humidity_entity: str = VEVOR_HUMIDITY_ENTITY,
        wind_speed_entity: str = VEVOR_WIND_SPEED_ENTITY,
    ) -> None:
        """Initialise le provider météo.

        Args:
            hass: Instance Home Assistant.
            irradiance_entity: Entity_id irradiance GHI Vevor.
            temp_entity: Entity_id température Vevor.
            precip_entity: Entity_id précipitations Vevor.
            uv_index_entity: Entity_id UV Vevor.
            weather_entity: Weather entity Vevor (cloud cover).
            meteo_france_entity: Entity_id Météo-France (fallback).
            humidity_entity: Entity_id humidité Vevor.
            wind_speed_entity: Entity_id vent Vevor.
        """
        self._hass = hass
        self._irradiance_entity = irradiance_entity
        self._temp_entity = temp_entity
        self._precip_entity = precip_entity
        self._uv_index_entity = uv_index_entity
        self._weather_entity = weather_entity
        self._meteo_france_entity = meteo_france_entity
        self._humidity_entity = humidity_entity
        self._wind_speed_entity = wind_speed_entity

    def _read_sensor(self, entity_id: str) -> float | None:
        """Lit la valeur d'un sensor HA via hass.states.get().

        Args:
            entity_id: Entity_id du sensor.

        Returns:
            Valeur float ou None si indisponible.
        """
        state = self._hass.states.get(entity_id)
        if state is None:
            _LOGGER.debug("Sensor indisponible: %s", entity_id)
            return None
        return _safe_float(state.state)

    def _read_weather_condition(
        self, weather_entity_id: str
    ) -> str | None:
        """Lit la condition d'une weather entity HA.

        Args:
            weather_entity_id: Entity_id de la weather entity.

        Returns:
            Condition (ex. "sunny", "partlycloudy") ou None.
        """
        state = self._hass.states.get(weather_entity_id)
        if state is None:
            _LOGGER.debug("Weather entity indisponible: %s", weather_entity_id)
            return None
        # La condition est dans l'attribut 'state' ou directement state.state
        condition = state.state
        if condition in (None, "", "unknown", "unavailable"):
            return None
        return condition

    def _condition_to_cloud_cover(self, condition: str) -> int:
        """Convertit une condition weather en couverture nuageuse (%).

        Args:
            condition: Condition weather HA (ex. "sunny", "partlycloudy").

        Returns:
            Couverture nuageuse en pourcentage (0-100).
        """
        return CONDITION_TO_CLOUD_COVER.get(condition, 50)

    async def get_current_weather(self) -> WeatherData:
        """Récupère les données météo courantes (Vevor + fallback).

        Hiérarchie :
            1. Vevor sensors (irradiance, temp, precip, UV, humidité, vent)
            1b. weather.ilapos13 (couverture nuageuse locale)
            2. Météo-France (fallback — si Vevor indisponible)

        Returns:
            WeatherData — données météo unifiées. Les champs indisponibles
            restent None.
        """
        # --- Lecture Vevor (priorité 1) ---
        irradiance = self._read_sensor(self._irradiance_entity)
        temperature = self._read_sensor(self._temp_entity)
        precipitation = self._read_sensor(self._precip_entity)
        uv_index = self._read_sensor(self._uv_index_entity)
        humidity = self._read_sensor(self._humidity_entity)
        wind_speed = self._read_sensor(self._wind_speed_entity)

        # --- Couverture nuageuse (priorité 1b: weather.ilapos13) ---
        cloud_cover_pct: float | None = None
        cloud_cover_source: str | None = None
        cloud_cover_reliability: str | None = None

        condition = self._read_weather_condition(self._weather_entity)
        if condition is not None:
            cloud_cover_pct = float(
                self._condition_to_cloud_cover(condition)
            )
            cloud_cover_source = self._weather_entity
            cloud_cover_reliability = "high"
            _LOGGER.debug(
                "Couverture nuageuse depuis %s: condition=%s → %d%%",
                self._weather_entity,
                condition,
                int(cloud_cover_pct),
            )
        else:
            # Fallback Météo-France pour la couverture nuageuse
            mf_condition = self._read_weather_condition(
                self._meteo_france_entity
            )
            if mf_condition is not None:
                cloud_cover_pct = float(
                    self._condition_to_cloud_cover(mf_condition)
                )
                cloud_cover_source = self._meteo_france_entity
                cloud_cover_reliability = "low"
                _LOGGER.debug(
                    "Couverture nuageuse (fallback MF): condition=%s → %d%%",
                    mf_condition,
                    int(cloud_cover_pct),
                )

        # Déterminer la source principale
        # Si au moins un sensor Vevor est disponible, source = vevor
        vevor_available = any(
            v is not None
            for v in [irradiance, temperature, precipitation, humidity]
        )
        source = "vevor_wunderground" if vevor_available else "meteo_france_fallback"

        weather = WeatherData(
            irradiance_ghi=irradiance,
            temperature_c=temperature,
            cloud_cover_pct=cloud_cover_pct,
            cloud_cover_source=cloud_cover_source,
            cloud_cover_reliability=cloud_cover_reliability,
            precipitation_mm=precipitation,
            uv_index=uv_index,
            humidity_pct=humidity,
            wind_speed_kmh=wind_speed,
            source=source,
        )

        _LOGGER.debug(
            "Météo courante: GHI=%s W/m², T=%s°C, cloud=%s%%, source=%s",
            irradiance,
            temperature,
            cloud_cover_pct,
            source,
        )

        return weather

    async def get_hourly_weather(
        self,
        target_time: Any | None = None,
        is_current_hour: bool = False,
    ) -> dict[str, Any]:
        """Retourne les données météo pour une heure donnée.

        Pour l'heure courante (is_current_hour=True), on dispose des
        mesures Vevor (GHI, température, etc.). Pour les heures futures,
        l'irradiance GHI est null (pas de prévision d'irradiance en Phase 1),
        mais la couverture nuageuse et la température sont disponibles via
        weather.ilapos13.

        Args:
            target_time: Heure cible (datetime ou None pour heure courante).
            is_current_hour: True si l'heure cible est l'heure courante.

        Returns:
            Dictionnaire météo pour pv_hourly_forecast :
                irradiance_ghi, temperature_c, cloud_cover_pct,
                cloud_cover_source, cloud_cover_reliability,
                precipitation_mm, uv_index, source
        """
        if is_current_hour:
            # Heure courante : données Vevor disponibles
            weather = await self.get_current_weather()
            return weather.to_dict()

        # Heure future : irradiance GHI null (pas de prévision),
        # couverture nuageuse et température depuis weather.ilapos13
        # (même condition que l'heure courante — pas de prévision horaire
        # détaillée en Phase 1, on utilise la condition courante)
        condition = self._read_weather_condition(self._weather_entity)
        cloud_cover_pct: float | None = None
        cloud_cover_source: str | None = None
        cloud_cover_reliability: str | None = None

        if condition is not None:
            cloud_cover_pct = float(self._condition_to_cloud_cover(condition))
            cloud_cover_source = self._weather_entity
            cloud_cover_reliability = "high"
        else:
            # Fallback Météo-France
            mf_condition = self._read_weather_condition(
                self._meteo_france_entity
            )
            if mf_condition is not None:
                cloud_cover_pct = float(
                    self._condition_to_cloud_cover(mf_condition)
                )
                cloud_cover_source = self._meteo_france_entity
                cloud_cover_reliability = "low"

        # Température : Vevor (même valeur que l'heure courante — pas de
        # prévision horaire en Phase 1)
        temperature = self._read_sensor(self._temp_entity)

        return {
            "irradiance_ghi": None,  # Null pour les heures futures (Phase 1)
            "temperature_c": temperature,
            "cloud_cover_pct": cloud_cover_pct,
            "cloud_cover_source": cloud_cover_source,
            "cloud_cover_reliability": cloud_cover_reliability,
            "precipitation_mm": None,  # Pas de prévision horaire (Phase 1)
            "uv_index": None,  # Pas de prévision UV (Phase 1)
            "source": "weather_ilapos13" if cloud_cover_reliability == "high"
            else "meteo_france_fallback",
        }
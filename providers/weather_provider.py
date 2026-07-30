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
from dataclasses import dataclass
from typing import Any

from .const import (
    ATON_REAL_PRODUCTION_ENTITY,
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


@dataclass
class WeatherData:
    """Données météo unifiées (Vevor + Météo-France fallback).

    Attributes:
        irradiance_ghi: Irradiance GHI W/m² (Vevor, heure courante uniquement).
        temperature_c: Température °C (Vevor prioritaire).
        cloud_cover_pct: Couverture nuageuse % (weather.ilapos13 prioritaire).
        cloud_cover_source: Source du cloud cover ("weather.ilapos13" ou "meteo_france").
        cloud_cover_reliability: Fiabilité ("high" si Vevor, "low" si MF).
        precipitation_mm: Précipitations mm (Vevor).
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

    async def get_current_weather(self) -> WeatherData:
        """Récupère les données météo courantes (Vevor + fallback).

        Returns:
            WeatherData — données météo unifiées.

        TODO Phase 1 :
            - Lire les states des sensors Vevor
            - Lire la condition de weather.ilapos13 → mapper en cloud_cover_pct
            - Si Vevor indisponible, fallback Météo-France
            - Marquer la fiabilité (high/low)
        """
        # TODO Phase 1 : implémenter la lecture des states
        return WeatherData(source="vevor_wunderground")

    def _condition_to_cloud_cover(self, condition: str) -> int:
        """Convertit une condition weather en couverture nuageuse (%).

        Args:
            condition: Condition weather HA (ex. "sunny", "partlycloudy").

        Returns:
            Couverture nuageuse en pourcentage (0-100).
        """
        return CONDITION_TO_CLOUD_COVER.get(condition, 50)

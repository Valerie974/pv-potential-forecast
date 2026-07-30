"""Configuration flow de la custom integration PV Potential Forecast.

Fichier : config_flow.py
Rôle : Définit l'assistant de configuration utilisateur (config_entry).
Demande les entity_ids Vevor, weather.ilapos13, Météo-France fallback,
production réelle ATON, et les coordonnées GPS de La Possession.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_ATON_REAL_PRODUCTION_SENSOR,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_METEO_FRANCE_ENTITY,
    CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
    CONF_WUNDERGROUND_PRECIP_ENTITY,
    CONF_WUNDERGROUND_TEMP_ENTITY,
    CONF_WUNDERGROUND_UV_INDEX_ENTITY,
    CONF_WUNDERGROUND_WEATHER_ENTITY,
    DEFAULT_ATON_REAL_PRODUCTION_SENSOR,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_METEO_FRANCE_ENTITY,
    DEFAULT_TILT,
    DEFAULT_WUNDERGROUND_IRRADIANCE_ENTITY,
    DEFAULT_WUNDERGROUND_PRECIP_ENTITY,
    DEFAULT_WUNDERGROUND_TEMP_ENTITY,
    DEFAULT_WUNDERGROUND_UV_INDEX_ENTITY,
    DEFAULT_WUNDERGROUND_WEATHER_ENTITY,
    DOMAIN,
)


class PVPotentialForecastConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Configuration flow pour PV Potential Forecast.

    Gère la création d'un ConfigEntry. Demande à l'utilisateur les
    entity_ids des capteurs Vevor, la weather entity, l'entité Météo-France
    (fallback) et le sensor de production réelle ATON.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Première étape du config flow — configuration principale.

        Args:
            user_input: Données saisies par l'utilisateur, ou None
                si le formulaire n'a pas encore été soumis.

        Returns:
            FlowResult — formulaire ou création de l'entrée.
        """
        # TODO Phase 1 : implémenter le schéma de validation
        # TODO Phase 1 : vérifier l'unicité de l'entrée (unique instance)
        # TODO Phase 1 : créer le ConfigEntry avec les valeurs utilisateur

        errors: dict[str, str] = {}

        if user_input is not None:
            # TODO Phase 1 : valider les entity_ids (existence dans HA)
            # TODO Phase 1 : valider les coordonnées GPS
            return self.async_create_entry(
                title="PV Potential Forecast",
                data=user_input,
            )

        # Schéma du formulaire de configuration
        data_schema = vol.Schema(
            {
                vol.Required(CONF_LATITUDE, default=DEFAULT_LATITUDE): float,
                vol.Required(CONF_LONGITUDE, default=DEFAULT_LONGITUDE): float,
                vol.Required(
                    CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
                    default=DEFAULT_WUNDERGROUND_IRRADIANCE_ENTITY,
                ): str,
                vol.Required(
                    CONF_WUNDERGROUND_TEMP_ENTITY,
                    default=DEFAULT_WUNDERGROUND_TEMP_ENTITY,
                ): str,
                vol.Required(
                    CONF_WUNDERGROUND_PRECIP_ENTITY,
                    default=DEFAULT_WUNDERGROUND_PRECIP_ENTITY,
                ): str,
                vol.Optional(
                    CONF_WUNDERGROUND_UV_INDEX_ENTITY,
                    default=DEFAULT_WUNDERGROUND_UV_INDEX_ENTITY,
                ): str,
                vol.Required(
                    CONF_WUNDERGROUND_WEATHER_ENTITY,
                    default=DEFAULT_WUNDERGROUND_WEATHER_ENTITY,
                ): str,
                vol.Required(
                    CONF_METEO_FRANCE_ENTITY,
                    default=DEFAULT_METEO_FRANCE_ENTITY,
                ): str,
                vol.Required(
                    CONF_ATON_REAL_PRODUCTION_SENSOR,
                    default=DEFAULT_ATON_REAL_PRODUCTION_SENSOR,
                ): str,
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

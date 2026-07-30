"""Configuration flow de la custom integration PV Potential Forecast.

Fichier : config_flow.py
Rôle : Définit l'assistant de configuration utilisateur (config_entry).
Demande les entity_ids Vevor, weather.ilapos13, Météo-France fallback,
production réelle ATON, et les coordonnées GPS de La Possession.

Inclut un options flow pour modifier la configuration sans réinstallation.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
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
    DEFAULT_WUNDERGROUND_IRRADIANCE_ENTITY,
    DEFAULT_WUNDERGROUND_PRECIP_ENTITY,
    DEFAULT_WUNDERGROUND_TEMP_ENTITY,
    DEFAULT_WUNDERGROUND_UV_INDEX_ENTITY,
    DEFAULT_WUNDERGROUND_WEATHER_ENTITY,
    DOMAIN,
)


def _get_config_schema(
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    """Construit le schéma de configuration avec les valeurs par défaut.

    Args:
        defaults: Valeurs par défaut (depuis l'entry existante pour options).

    Returns:
        Schéma voluptuous pour le formulaire.
    """
    d = defaults or {}

    return vol.Schema(
        {
            vol.Required(
                CONF_LATITUDE,
                default=d.get(CONF_LATITUDE, DEFAULT_LATITUDE),
            ): float,
            vol.Required(
                CONF_LONGITUDE,
                default=d.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
            ): float,
            vol.Required(
                CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
                default=d.get(
                    CONF_WUNDERGROUND_IRRADIANCE_ENTITY,
                    DEFAULT_WUNDERGROUND_IRRADIANCE_ENTITY,
                ),
            ): str,
            vol.Required(
                CONF_WUNDERGROUND_TEMP_ENTITY,
                default=d.get(
                    CONF_WUNDERGROUND_TEMP_ENTITY,
                    DEFAULT_WUNDERGROUND_TEMP_ENTITY,
                ),
            ): str,
            vol.Required(
                CONF_WUNDERGROUND_PRECIP_ENTITY,
                default=d.get(
                    CONF_WUNDERGROUND_PRECIP_ENTITY,
                    DEFAULT_WUNDERGROUND_PRECIP_ENTITY,
                ),
            ): str,
            vol.Optional(
                CONF_WUNDERGROUND_UV_INDEX_ENTITY,
                default=d.get(
                    CONF_WUNDERGROUND_UV_INDEX_ENTITY,
                    DEFAULT_WUNDERGROUND_UV_INDEX_ENTITY,
                ),
            ): str,
            vol.Required(
                CONF_WUNDERGROUND_WEATHER_ENTITY,
                default=d.get(
                    CONF_WUNDERGROUND_WEATHER_ENTITY,
                    DEFAULT_WUNDERGROUND_WEATHER_ENTITY,
                ),
            ): str,
            vol.Required(
                CONF_METEO_FRANCE_ENTITY,
                default=d.get(
                    CONF_METEO_FRANCE_ENTITY,
                    DEFAULT_METEO_FRANCE_ENTITY,
                ),
            ): str,
            vol.Required(
                CONF_ATON_REAL_PRODUCTION_SENSOR,
                default=d.get(
                    CONF_ATON_REAL_PRODUCTION_SENSOR,
                    DEFAULT_ATON_REAL_PRODUCTION_SENSOR,
                ),
            ): str,
        }
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
        errors: dict[str, str] = {}

        if user_input is not None:
            # Vérifier l'unicité de l'entrée (une seule instance autorisée)
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            # Valider les coordonnées GPS
            lat = user_input.get(CONF_LATITUDE, DEFAULT_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE, DEFAULT_LONGITUDE)
            if not (-90 <= lat <= 90):
                errors[CONF_LATITUDE] = "invalid_latitude"
            elif not (-180 <= lon <= 180):
                errors[CONF_LONGITUDE] = "invalid_longitude"

            if not errors:
                return self.async_create_entry(
                    title="PV Potential Forecast",
                    data=user_input,
                )

        # Schéma du formulaire de configuration
        data_schema = _get_config_schema()

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> "PVPotentialForecastOptionsFlow":
        """Retourne le flow d'options pour modifier la configuration.

        Args:
            config_entry: Configuration entry existante.

        Returns:
            Instance du options flow.
        """
        return PVPotentialForecastOptionsFlow(config_entry)


class PVPotentialForecastOptionsFlow(config_entries.OptionsFlow):
    """Options flow pour modifier la configuration sans réinstallation.

    Permet de modifier les entity_ids et coordonnées GPS après
    l'installation initiale.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialise le options flow.

        Args:
            config_entry: Configuration entry existante.
        """
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Étape initiale du options flow — formulaire de modification.

        Args:
            user_input: Données saisies par l'utilisateur, ou None.

        Returns:
            FlowResult — formulaire ou sauvegarde.
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            # Valider les coordonnées GPS
            lat = user_input.get(CONF_LATITUDE, DEFAULT_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE, DEFAULT_LONGITUDE)
            if not (-90 <= lat <= 90):
                errors[CONF_LATITUDE] = "invalid_latitude"
            elif not (-180 <= lon <= 180):
                errors[CONF_LONGITUDE] = "invalid_longitude"

            if not errors:
                # Mettre à jour les données de l'entry
                self.hass.config_entries.async_update_entry(
                    self._config_entry,
                    data=user_input,
                )
                return self.async_create_entry(title="", data=user_input)

        # Schéma avec les valeurs actuelles de l'entry
        data_schema = _get_config_schema(self._config_entry.data)

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )
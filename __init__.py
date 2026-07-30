"""Point d'entrée de la custom integration PV Potential Forecast.

Fichier : __init__.py
Rôle : Initialise la custom integration, configure le DataUpdateCoordinator
et enregistre les plateformes (sensor).

Architecture v3 — Forecast.Solar source PV unique, station Vevor source
météo principale, weather.ilapos13 couverture nuageuse locale,
Météo-France fallback uniquement.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Plateformes à charger (Phase 1 : sensor uniquement)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure la custom integration à partir d'un ConfigEntry.

    Args:
        hass: Instance Home Assistant.
        entry: Configuration entry créée par le config_flow.

    Returns:
        True si la configuration a réussi, False sinon.

    TODO Phase 1 :
        - Instancier le ForecastSolarProvider
        - Instancier le WeatherProvider (Vevor + Météo-France fallback)
        - Instancier le ForecastSolarRateLimiter
        - Créer le PVPotentialCoordinator (DataUpdateCoordinator)
        - Stocker le coordinator dans hass.data[DOMAIN][entry.entry_id]
        - Forwarder les plateformes (sensor)
    """
    _LOGGER.info(
        "Configuration de PV Potential Forecast (entry_id=%s)", entry.entry_id
    )

    # TODO Phase 1 : instancier le coordinator
    # coordinator = PVPotentialCoordinator(hass, ...)
    # hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    # await coordinator.async_config_entry_first_refresh()

    # TODO Phase 1 : forwarder les plateformes
    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharge la custom integration.

    Args:
        hass: Instance Home Assistant.
        entry: Configuration entry à décharger.

    Returns:
        True si le déchargement a réussi.
    """
    _LOGGER.info(
        "Déchargement de PV Potential Forecast (entry_id=%s)", entry.entry_id
    )

    # TODO Phase 1 : décharger les plateformes
    # unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    # if unload_ok:
    #     hass.data[DOMAIN].pop(entry.entry_id)
    # return unload_ok

    return True

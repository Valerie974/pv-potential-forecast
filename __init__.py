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
from .coordinator import PVForecastCoordinator

_LOGGER = logging.getLogger(__name__)

# Plateformes à charger (Phase 1 : sensor uniquement)
PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Configure la custom integration à partir d'un ConfigEntry.

    Étapes :
        1. Créer le PVForecastCoordinator
        2. Lancer le premier refresh
        3. Stocker le coordinator dans hass.data
        4. Forwarder les plateformes (sensor)

    Args:
        hass: Instance Home Assistant.
        entry: Configuration entry créée par le config_flow.

    Returns:
        True si la configuration a réussi, False sinon.
    """
    _LOGGER.info(
        "Configuration de PV Potential Forecast (entry_id=%s)", entry.entry_id
    )

    # Créer le coordinator
    coordinator = PVForecastCoordinator(hass, entry)

    # Stocker le coordinator dans hass.data avant le premier refresh
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Lancer le premier refresh
    await coordinator.async_config_entry_first_refresh()

    # Forwarder les plateformes (sensor)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

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

    # Décharger les plateformes
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
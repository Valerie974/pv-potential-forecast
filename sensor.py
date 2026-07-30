"""Plateforme sensor — PV Potential Forecast.

Fichier : sensor.py
Rôle : Enregistre les 11 SensorEntity de la Phase 1 auprès de Home Assistant.
Dispatche la création vers deye_sensors, aton_sensors, global_sensors.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ALL_PHASE1_SENSORS, DOMAIN
from .sensors.aton_sensors import create_aton_sensors
from .sensors.deye_sensors import create_deye_sensors
from .sensors.global_sensors import create_global_sensors

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Configure les sensors de la Phase 1.

    Crée les 11 sensors :
        - 4 sensors DEYE (potentiel panneaux)
        - 3 sensors ATON (estimé + réel + écart)
        - 4 sensors globaux (agrégats + prévisions)

    Args:
        hass: Instance Home Assistant.
        entry: Configuration entry.
        async_add_entities: Callback pour ajouter les entities.
    """
    _LOGGER.info(
        "Configuration des %d sensors PV Potential Forecast",
        len(ALL_PHASE1_SENSORS),
    )

    # Récupérer le coordinator depuis hass.data
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Créer et enregistrer les 11 sensors
    entities = []
    entities.extend(create_deye_sensors(coordinator))
    entities.extend(create_aton_sensors(coordinator, hass))
    entities.extend(create_global_sensors(coordinator))

    _LOGGER.info("Enregistrement de %d sensors", len(entities))
    async_add_entities(entities)
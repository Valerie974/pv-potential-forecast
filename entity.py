"""Entity de base — PV Potential Forecast.

Fichier : entity.py
Rôle : Définit la classe de base pour toutes les SensorEntity du projet.
Centralise les attributs communs (device_info, nom, icône).

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN


class PVPotentialEntity(CoordinatorEntity):
    """Classe de base pour toutes les entities PV Potential Forecast.

    Attributes:
        _attr_has_entity_name: Utilise le nom de l'entity (pas un nom global).
    """

    _attr_has_entity_name = True

    def __init__(self, coordinator: object, sensor_key: str) -> None:
        """Initialise l'entity de base.

        Args:
            coordinator: Le DataUpdateCoordinator.
            sensor_key: Clé du sensor (ex. "deye_mppt1_potential_power").
        """
        super().__init__(coordinator)
        self._sensor_key = sensor_key

        # TODO Phase 1 : définir les attributs communs
        # self._attr_unique_id = f"{config_entry.entry_id}_{sensor_key}"
        # self._attr_device_info = DeviceInfo(
        #     identifiers={(DOMAIN, "pv_potential_forecast")},
        #     name="PV Potential Forecast",
        #     manufacturer="Custom",
        #     model="PV Forecast Engine",
        #     entry_type=DeviceEntryType.SERVICE,
        # )

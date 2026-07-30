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

# Informations du device commun à tous les sensors
_DEVICE_INFO = DeviceInfo(
    identifiers={(DOMAIN, "pv_potential_forecast")},
    name="PV Potential Forecast",
    manufacturer="Custom",
    model="PV Forecast Engine",
    entry_type=DeviceEntryType.SERVICE,
    sw_version="0.1.0",
)


class PVPotentialEntity(CoordinatorEntity):
    """Classe de base pour toutes les entities PV Potential Forecast.

    Hérite de CoordinatorEntity pour bénéficier de la mise à jour
    automatique via le DataUpdateCoordinator (should_poll=False).

    Attributes:
        _attr_has_entity_name: Utilise le nom de l'entity (pas un nom global).
        _attr_should_poll: False — le coordinator gère le polling.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: object, sensor_key: str) -> None:
        """Initialise l'entity de base.

        Args:
            coordinator: Le DataUpdateCoordinator.
            sensor_key: Clé du sensor (ex. "deye_mppt1_potential_power").
        """
        super().__init__(coordinator)
        self._sensor_key = sensor_key

        # Identifiant unique basé sur la clé du sensor
        self._attr_unique_id = f"pv_potential_forecast_{sensor_key}"

        # Informations du device commun
        self._attr_device_info = _DEVICE_INFO

    @property
    def available(self) -> bool:
        """Retourne True si l'entity est disponible (données coordinator)."""
        return self.coordinator.data is not None
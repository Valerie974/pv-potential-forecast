"""Sensors DEYE — 4 sensors potentiel panneaux (off-grid).

Fichier : sensors/deye_sensors.py
Rôle : Définit les 4 SensorEntity pour le DEYE (off-grid, aucune validation) :
    1. deye_mppt1_potential_power  (W)  MPPT1 — 53° ENE, 4 060 Wc
    2. deye_mppt2_potential_power  (W)  MPPT2 — 308° NW, 2 900 Wc
    3. deye_mppt3_potential_power  (W)  MPPT3 — 27° NNE, 2 900 Wc
    4. deye_total_potential_power  (W)  Somme 3 MPPT

Note : Le DEYE n'est JAMAIS comparé à une production réelle (principe #0).

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower

from ..const import (
    DEYE_PV1_AZIMUTH_API,
    DEYE_PV1_CAPACITY_W,
    DEYE_PV2_AZIMUTH_API,
    DEYE_PV2_CAPACITY_W,
    DEYE_PV3_AZIMUTH_API,
    DEYE_PV3_CAPACITY_W,
    DEYE_TOTAL_POWER_W,
    SENSOR_DEYE_MPPT1_POTENTIAL_POWER,
    SENSOR_DEYE_MPPT2_POTENTIAL_POWER,
    SENSOR_DEYE_MPPT3_POTENTIAL_POWER,
    SENSOR_DEYE_TOTAL_POTENTIAL_POWER,
)
from ..entity import PVPotentialEntity

_LOGGER = logging.getLogger(__name__)


class DEYEMPPTSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel individuel pour un MPPT DEYE.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
        _attr_device_class: Classe de device (power).
        _attr_state_class: Classe de state (measurement).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(
        self,
        coordinator: Any,
        sensor_key: str,
        mppt_name: str,
        azimuth: float,
        capacity_w: float,
    ) -> None:
        """Initialise le sensor DEYE MPPT.

        Args:
            coordinator: Le DataUpdateCoordinator.
            sensor_key: Clé du sensor.
            mppt_name: Nom du MPPT (ex. "DEYE_PV1").
            azimuth: Azimuth du MPPT (convention Forecast.Solar).
            capacity_w: Capacité du MPPT en watts.
        """
        super().__init__(coordinator, sensor_key)
        self._mppt_name = mppt_name
        self._azimuth = azimuth
        self._capacity_w = capacity_w

        # TODO Phase 1 : définir unique_id, name, icon
        # self._attr_unique_id = f"pv_potential_forecast_{sensor_key}"
        # self._attr_name = sensor_key.replace("_", " ").title()

    @property
    def native_value(self) -> float | None:
        """Retourne la valeur du potentiel PV pour ce MPPT.

        TODO Phase 1 : récupérer depuis coordinator.data
        """
        # TODO Phase 1 : implémenter
        return None


class DEYETotalSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel total DEYE (somme des 3 MPPT).

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor total DEYE.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_DEYE_TOTAL_POTENTIAL_POWER)

    @property
    def native_value(self) -> float | None:
        """Retourne la valeur du potentiel total DEYE.

        TODO Phase 1 : récupérer depuis coordinator.data
        """
        # TODO Phase 1 : implémenter
        return None


def create_deye_sensors(coordinator: Any) -> list[SensorEntity]:
    """Crée les 4 sensors DEYE.

    Args:
        coordinator: Le DataUpdateCoordinator.

    Returns:
        Liste de 4 SensorEntity (3 MPPT + 1 total).
    """
    return [
        DEYEMPPTSensor(
            coordinator,
            SENSOR_DEYE_MPPT1_POTENTIAL_POWER,
            "DEYE_PV1",
            DEYE_PV1_AZIMUTH_API,
            DEYE_PV1_CAPACITY_W,
        ),
        DEYEMPPTSensor(
            coordinator,
            SENSOR_DEYE_MPPT2_POTENTIAL_POWER,
            "DEYE_PV2",
            DEYE_PV2_AZIMUTH_API,
            DEYE_PV2_CAPACITY_W,
        ),
        DEYEMPPTSensor(
            coordinator,
            SENSOR_DEYE_MPPT3_POTENTIAL_POWER,
            "DEYE_PV3",
            DEYE_PV3_AZIMUTH_API,
            DEYE_PV3_CAPACITY_W,
        ),
        DEYETotalSensor(coordinator),
    ]

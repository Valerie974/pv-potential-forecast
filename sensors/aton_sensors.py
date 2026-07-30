"""Sensors ATON — 3 sensors (estimation + réel + écart, grid-tie).

Fichier : sensors/aton_sensors.py
Rôle : Définit les 3 SensorEntity pour l'ATON (grid-tie, calibration) :
    5. aton_estimated_power   (W)  Estimé agrégé PV1+PV2 (Forecast.Solar)
    6. aton_actual_power       (W)  Source : sensor.philippeb_instant_solar_power
    7. aton_forecast_error     (W)  Estimé − Réel (instantané)

Note : L'ATON est la SEULE installation utilisée pour la calibration (Phase 4).
Le sensor de production réelle est lu depuis sensor.philippeb_instant_solar_power.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfPower

from ..const import (
    ATON_REAL_PRODUCTION_ENTITY,
    ATON_TOTAL_POWER_W,
    SENSOR_ATON_ACTUAL_POWER,
    SENSOR_ATON_ESTIMATED_POWER,
    SENSOR_ATON_FORECAST_ERROR,
)
from ..entity import PVPotentialEntity

_LOGGER = logging.getLogger(__name__)


class ATONEstimatedSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel estimé ATON (agrégé PV1 + PV2).

    Reçoit les métadonnées de source (source_active) car l'ATON est la
    seule installation calibrée.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor ATON estimé.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_ATON_ESTIMATED_POWER)

    @property
    def native_value(self) -> float | None:
        """Retourne le potentiel estimé de l'ATON.

        TODO Phase 1 : récupérer depuis coordinator.data
        """
        # TODO Phase 1 : implémenter
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active).

        TODO Phase 1 : ajouter source_active, confidence
        """
        # TODO Phase 1 : implémenter
        return None


class ATONActualSensor(PVPotentialEntity, SensorEntity):
    """Sensor de production réelle ATON.

    Lit la valeur depuis sensor.philippeb_instant_solar_power (puissance
    instantanée de l'onduleur ATON grid-tie).

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor ATON réel.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_ATON_ACTUAL_POWER)

    @property
    def native_value(self) -> float | None:
        """Retourne la production réelle de l'ATON.

        TODO Phase 1 : lire depuis hass.states.get(ATON_REAL_PRODUCTION_ENTITY)
        """
        # TODO Phase 1 : implémenter
        return None


class ATONForecastErrorSensor(PVPotentialEntity, SensorEntity):
    """Sensor d'écart entre estimation et production réelle ATON.

    Calcul : aton_forecast_error = aton_estimated_power - aton_actual_power
    Une valeur positive indique une surestimation, négative une sous-estimation.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor d'écart ATON.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_ATON_FORECAST_ERROR)

    @property
    def native_value(self) -> float | None:
        """Retourne l'écart (estimé − réel).

        TODO Phase 1 : calculer depuis les deux autres sensors ATON
        """
        # TODO Phase 1 : implémenter
        return None


def create_aton_sensors(coordinator: Any) -> list[SensorEntity]:
    """Crée les 3 sensors ATON.

    Args:
        coordinator: Le DataUpdateCoordinator.

    Returns:
        Liste de 3 SensorEntity (estimé + réel + écart).
    """
    return [
        ATONEstimatedSensor(coordinator),
        ATONActualSensor(coordinator),
        ATONForecastErrorSensor(coordinator),
    ]

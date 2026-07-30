"""Sensors globaux — 4 sensors (agrégats + prévisions).

Fichier : sensors/global_sensors.py
Rôle : Définit les 4 SensorEntity globaux :
    8.  pv_total_potential_power  (W)   DEYE + ATON (instantané)
    9.  pv_potential_today          (kWh) Énergie potentielle aujourd'hui
    10. pv_potential_tomorrow        (kWh) Énergie potentielle demain
    11. pv_hourly_forecast           (W)   État = heure courante, attributs = 48h

Les sensors 9, 10, 11 reçoivent les métadonnées de source (source_active,
confidence, sources_detail).

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfEnergy, UnitOfPower

from ..const import (
    DEYE_TOTAL_POWER_W,
    SENSOR_PV_HOURLY_FORECAST,
    SENSOR_PV_POTENTIAL_TODAY,
    SENSOR_PV_POTENTIAL_TOMORROW,
    SENSOR_PV_TOTAL_POTENTIAL_POWER,
)
from ..entity import PVPotentialEntity

_LOGGER = logging.getLogger(__name__)


class PVTotalPotentialSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel total installation (DEYE + ATON, instantané).

    Reçoit les métadonnées de source (source_active).

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor total potentiel.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_TOTAL_POTENTIAL_POWER)

    @property
    def native_value(self) -> float | None:
        """Retourne le potentiel total (DEYE + ATON).

        TODO Phase 1 : récupérer depuis coordinator.data
        """
        # TODO Phase 1 : implémenter
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active).

        TODO Phase 1 : ajouter source_active
        """
        # TODO Phase 1 : implémenter
        return None


class PVPotentialTodaySensor(PVPotentialEntity, SensorEntity):
    """Sensor d'énergie potentielle aujourd'hui (kWh).

    Reçoit les métadonnées de source (source_active, confidence).

    Attributes:
        _attr_native_unit_of_measurement: Unité (kWh).
    """

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.ENERGY
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.TOTAL

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor énergie aujourd'hui.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_POTENTIAL_TODAY)

    @property
    def native_value(self) -> float | None:
        """Retourne l'énergie potentielle du jour (kWh).

        TODO Phase 1 : intégrer les prévisions horaires du jour
        """
        # TODO Phase 1 : implémenter
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active, confidence).

        TODO Phase 1 : implémenter
        """
        # TODO Phase 1 : implémenter
        return None


class PVPotentialTomorrowSensor(PVPotentialEntity, SensorEntity):
    """Sensor d'énergie potentielle demain (kWh).

    Reçoit les métadonnées de source (source_active, confidence).

    Attributes:
        _attr_native_unit_of_measurement: Unité (kWh).
    """

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.ENERGY
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.TOTAL

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor énergie demain.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_POTENTIAL_TOMORROW)

    @property
    def native_value(self) -> float | None:
        """Retourne l'énergie potentielle du lendemain (kWh).

        TODO Phase 1 : intégrer les prévisions horaires du lendemain
        """
        # TODO Phase 1 : implémenter
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active, confidence).

        TODO Phase 1 : implémenter
        """
        # TODO Phase 1 : implémenter
        return None


class PVHourlyForecastSensor(PVPotentialEntity, SensorEntity):
    """Sensor principal de prévision horaire (48h × 5 MPPT + météo).

    État = puissance potentielle de l'heure courante (W).
    Attributs = structure JSON complète (voir architecture v3 §7) :
        - forecast : liste horaire (48h) avec détail par MPPT
        - forecast_today_kwh, forecast_tomorrow_kwh
        - source_active, confidence, sources_detail
        - last_update

    C'est le sensor le plus riche — il contient toute la prévision.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = None  # TODO Phase 1 : SensorDeviceClass.POWER
    _attr_state_class = None  # TODO Phase 1 : SensorStateClass.MEASUREMENT

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor de prévision horaire.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_HOURLY_FORECAST)

    @property
    def native_value(self) -> float | None:
        """Retourne la puissance potentielle de l'heure courante (W).

        TODO Phase 1 : récupérer l'heure courante depuis coordinator.data
        """
        # TODO Phase 1 : implémenter
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne la structure JSON complète de prévision (48h).

        Structure (voir architecture v3 §7) :
            - forecast : liste horaire (48h) avec détail MPPT + météo
            - forecast_today_kwh : énergie du jour (kWh)
            - forecast_tomorrow_kwh : énergie du lendemain (kWh)
            - source_active : "forecast_solar"
            - confidence : indice [0, 1]
            - sources_detail : détail des sources (Forecast.Solar + météo)
            - last_update : timestamp dernière mise à jour

        TODO Phase 1 : construire la structure JSON depuis coordinator.data
        """
        # TODO Phase 1 : implémenter
        return None


def create_global_sensors(coordinator: Any) -> list[SensorEntity]:
    """Crée les 4 sensors globaux.

    Args:
        coordinator: Le DataUpdateCoordinator.

    Returns:
        Liste de 4 SensorEntity (total + today + tomorrow + hourly_forecast).
    """
    return [
        PVTotalPotentialSensor(coordinator),
        PVPotentialTodaySensor(coordinator),
        PVPotentialTomorrowSensor(coordinator),
        PVHourlyForecastSensor(coordinator),
    ]

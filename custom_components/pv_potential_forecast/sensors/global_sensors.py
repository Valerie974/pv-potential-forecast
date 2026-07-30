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

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfEnergy, UnitOfPower

from ..const import (
    DEYE_TOTAL_POWER_W,
    INSTALLATION_TOTAL_POWER_W,
    SENSOR_PV_HOURLY_FORECAST,
    SENSOR_PV_POTENTIAL_TODAY,
    SENSOR_PV_POTENTIAL_TOMORROW,
    SENSOR_PV_TOTAL_POTENTIAL_POWER,
    SOURCE_ACTIVE_FORECAST_SOLAR,
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
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:solar-power-variant"

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor total potentiel.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_TOTAL_POTENTIAL_POWER)
        self._attr_name = "PV Total Potential Power"

    @property
    def native_value(self) -> float | None:
        """Retourne le potentiel total (DEYE + ATON estimé) en W."""
        data = self.coordinator.data
        if not data or "hourly_forecast" not in data:
            return None

        for entry in data["hourly_forecast"]:
            if entry.get("is_current_hour"):
                return round(entry.get("pv_total_w", 0.0), 1)

        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active)."""
        data = self.coordinator.data
        if not data:
            return None

        return {
            "source_active": data.get(
                "source_active", SOURCE_ACTIVE_FORECAST_SOLAR
            ),
            "total_capacity_w": INSTALLATION_TOTAL_POWER_W,
            "deye_capacity_w": DEYE_TOTAL_POWER_W,
            "aton_capacity_w": INSTALLATION_TOTAL_POWER_W - DEYE_TOTAL_POWER_W,
        }


class PVPotentialTodaySensor(PVPotentialEntity, SensorEntity):
    """Sensor d'énergie potentielle aujourd'hui (kWh).

    Reçoit les métadonnées de source (source_active, confidence).

    Attributes:
        _attr_native_unit_of_measurement: Unité (kWh).
    """

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor énergie aujourd'hui.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_POTENTIAL_TODAY)
        self._attr_name = "PV Potential Today"

    @property
    def native_value(self) -> float | None:
        """Retourne l'énergie potentielle du jour (kWh)."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("today_kwh", 0.0)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active, confidence)."""
        data = self.coordinator.data
        if not data:
            return None

        return {
            "source_active": data.get(
                "source_active", SOURCE_ACTIVE_FORECAST_SOLAR
            ),
            "confidence": data.get("confidence", 0.0),
            "last_update": data.get("last_update"),
        }


class PVPotentialTomorrowSensor(PVPotentialEntity, SensorEntity):
    """Sensor d'énergie potentielle demain (kWh).

    Reçoit les métadonnées de source (source_active, confidence).

    Attributes:
        _attr_native_unit_of_measurement: Unité (kWh).
    """

    _attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:solar-power-outline"

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor énergie demain.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_POTENTIAL_TOMORROW)
        self._attr_name = "PV Potential Tomorrow"

    @property
    def native_value(self) -> float | None:
        """Retourne l'énergie potentielle du lendemain (kWh)."""
        data = self.coordinator.data
        if not data:
            return None
        return data.get("tomorrow_kwh", 0.0)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source (source_active, confidence)."""
        data = self.coordinator.data
        if not data:
            return None

        return {
            "source_active": data.get(
                "source_active", SOURCE_ACTIVE_FORECAST_SOLAR
            ),
            "confidence": data.get("confidence", 0.0),
            "last_update": data.get("last_update"),
        }


class PVHourlyForecastSensor(PVPotentialEntity, SensorEntity):
    """Sensor principal de prévision horaire (48h × 5 MPPT + météo).

    État = puissance potentielle de l'heure courante (W).
    Attributs = structure JSON complète :
        - forecast : liste horaire (48h) avec détail par MPPT
        - forecast_today_kwh : énergie du jour (kWh)
        - forecast_tomorrow_kwh : énergie du lendemain (kWh)
        - source_active : "forecast_solar"
        - confidence : indice [0, 1]
        - sources_detail : détail des sources (Forecast.Solar + météo)
        - last_update : timestamp dernière mise à jour

    C'est le sensor le plus riche — il contient toute la prévision.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:weather-sunny"

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor de prévision horaire.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_PV_HOURLY_FORECAST)
        self._attr_name = "PV Hourly Forecast"

    @property
    def native_value(self) -> float | None:
        """Retourne la puissance potentielle de l'heure courante (W).

        Cherche l'entrée is_current_hour dans le forecast et retourne
        pv_total_w.
        """
        data = self.coordinator.data
        if not data or "hourly_forecast" not in data:
            return None

        for entry in data["hourly_forecast"]:
            if entry.get("is_current_hour"):
                return round(entry.get("pv_total_w", 0.0), 1)

        # Si pas d'heure courante trouvée, retourner 0
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne la structure JSON complète de prévision (48h).

        Structure :
            - forecast : liste horaire (48h) avec détail MPPT + météo
            - forecast_today_kwh : énergie du jour (kWh)
            - forecast_tomorrow_kwh : énergie du lendemain (kWh)
            - source_active : "forecast_solar"
            - confidence : indice [0, 1]
            - sources_detail : détail des sources (Forecast.Solar + météo)
            - last_update : timestamp dernière mise à jour
        """
        data = self.coordinator.data
        if not data:
            return None

        return {
            "forecast": data.get("hourly_forecast", []),
            "forecast_today_kwh": data.get("today_kwh", 0.0),
            "forecast_tomorrow_kwh": data.get("tomorrow_kwh", 0.0),
            "source_active": data.get(
                "source_active", SOURCE_ACTIVE_FORECAST_SOLAR
            ),
            "confidence": data.get("confidence", 0.0),
            "sources_detail": data.get("sources_detail", {}),
            "last_update": data.get("last_update"),
        }


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
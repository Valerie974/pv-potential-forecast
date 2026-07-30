"""Sensors DEYE — 4 sensors potentiel panneaux (off-grid).

Fichier : sensors/deye_sensors.py
Rôle : Définit les 4 SensorEntity pour le DEYE (off-grid, aucune validation) :
    1. deye_mppt1_potential_power  (W)  MPPT1 — 53° ENE, 4 060 Wc
    2. deye_mppt2_potential_power  (W)  MPPT2 — 308° NW, 2 900 Wc
    3. deye_mppt3_potential_power  (W)  MPPT3 — 27° NNE, 2 900 Wc
    4. deye_total_potential_power  (W)  Somme 3 MPPT

Note : Le DEYE n'est JAMAIS comparé à une production réelle (principe #0).
Le rendement onduleur DEYE = 1.00 (potentiel DC pur).

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPower

from ..const import (
    DEYE_PV1_AZIMUTH_API,
    DEYE_PV1_CAPACITY_W,
    DEYE_PV1_PANEL_TYPE,
    DEYE_PV1_TILT,
    DEYE_PV2_AZIMUTH_API,
    DEYE_PV2_CAPACITY_W,
    DEYE_PV2_PANEL_TYPE,
    DEYE_PV2_TILT,
    DEYE_PV3_AZIMUTH_API,
    DEYE_PV3_CAPACITY_W,
    DEYE_PV3_PANEL_TYPE,
    DEYE_PV3_TILT,
    DEYE_TOTAL_POWER_W,
    SENSOR_DEYE_MPPT1_POTENTIAL_POWER,
    SENSOR_DEYE_MPPT2_POTENTIAL_POWER,
    SENSOR_DEYE_MPPT3_POTENTIAL_POWER,
    SENSOR_DEYE_TOTAL_POTENTIAL_POWER,
    WINGOSOLAR_BIFACIAL,
)
from ..entity import PVPotentialEntity

_LOGGER = logging.getLogger(__name__)


class DEYEMPPTSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel individuel pour un MPPT DEYE.

    Le potentiel est DC pur (rendement onduleur = 1.00).
    Le gain bifacial est inclus (Wingosolar WGS-M10/78BH, 70%).

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
        _attr_device_class: Classe de device (power).
        _attr_state_class: Classe de state (measurement).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:solar-power"

    def __init__(
        self,
        coordinator: Any,
        sensor_key: str,
        mppt_name: str,
        azimuth: float,
        tilt: int,
        capacity_w: int,
        panel_type: str,
    ) -> None:
        """Initialise le sensor DEYE MPPT.

        Args:
            coordinator: Le DataUpdateCoordinator.
            sensor_key: Clé du sensor.
            mppt_name: Nom du MPPT (ex. "DEYE_PV1").
            azimuth: Azimuth du MPPT (convention Forecast.Solar).
            tilt: Inclinaison du MPPT (degrés).
            capacity_w: Capacité du MPPT en watts.
            panel_type: Type de panneau (ex. "Wingosolar WGS-M10/78BH").
        """
        super().__init__(coordinator, sensor_key)
        self._mppt_name = mppt_name
        self._azimuth = azimuth
        self._tilt = tilt
        self._capacity_w = capacity_w
        self._panel_type = panel_type

        # Nom d'affichage (title case)
        self._attr_name = sensor_key.replace("_", " ").title()

    @property
    def native_value(self) -> float | None:
        """Retourne la valeur du potentiel PV pour ce MPPT (W).

        Lit la puissance corrigée depuis les données du coordinator.
        """
        data = self.coordinator.data
        if not data or "hourly_forecast" not in data:
            return None

        # Trouver l'heure courante dans le forecast
        for entry in data["hourly_forecast"]:
            if entry.get("is_current_hour"):
                # Mapper le nom du MPPT vers la clé du dict
                key_map = {
                    "DEYE_PV1": "deye_mppt1_w",
                    "DEYE_PV2": "deye_mppt2_w",
                    "DEYE_PV3": "deye_mppt3_w",
                }
                key = key_map.get(self._mppt_name)
                if key:
                    return round(entry.get(key, 0.0), 1)
                break

        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les attributs du sensor DEYE MPPT.

        Attributs : mppt_name, azimuth, tilt, capacity_w, panel_type,
        bifacial, weather (irradiance, temp, cloud_cover).
        """
        data = self.coordinator.data
        if not data:
            return None

        # Récupérer les données météo courantes
        weather = data.get("weather_current", {})

        attrs = {
            "mppt_name": self._mppt_name,
            "azimuth": self._azimuth,
            "tilt": self._tilt,
            "capacity_w": self._capacity_w,
            "panel_type": self._panel_type,
            "bifacial": WINGOSOLAR_BIFACIAL,
            "inverter_efficiency": 1.00,
            "weather": {
                "irradiance": weather.get("irradiance_ghi"),
                "temperature": weather.get("temperature_c"),
                "cloud_cover": weather.get("cloud_cover_pct"),
            },
        }

        # Ajouter la métadonnée de source si présente
        if "source_active" in data:
            attrs["source_active"] = data["source_active"]

        return attrs


class DEYETotalSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel total DEYE (somme des 3 MPPT).

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:solar-power-variant"

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor total DEYE.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_DEYE_TOTAL_POTENTIAL_POWER)
        self._attr_name = "DEYE Total Potential Power"

    @property
    def native_value(self) -> float | None:
        """Retourne la valeur du potentiel total DEYE (W).

        Somme des 3 MPPT DEYE pour l'heure courante.
        """
        data = self.coordinator.data
        if not data or "hourly_forecast" not in data:
            return None

        for entry in data["hourly_forecast"]:
            if entry.get("is_current_hour"):
                return round(entry.get("deye_total_w", 0.0), 1)

        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les attributs du sensor total DEYE."""
        data = self.coordinator.data
        if not data:
            return None

        weather = data.get("weather_current", {})

        attrs = {
            "total_capacity_w": DEYE_TOTAL_POWER_W,
            "mppt_count": 3,
            "inverter_efficiency": 1.00,
            "weather": {
                "irradiance": weather.get("irradiance_ghi"),
                "temperature": weather.get("temperature_c"),
                "cloud_cover": weather.get("cloud_cover_pct"),
            },
        }

        if "source_active" in data:
            attrs["source_active"] = data["source_active"]

        return attrs


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
            DEYE_PV1_TILT,
            DEYE_PV1_CAPACITY_W,
            DEYE_PV1_PANEL_TYPE,
        ),
        DEYEMPPTSensor(
            coordinator,
            SENSOR_DEYE_MPPT2_POTENTIAL_POWER,
            "DEYE_PV2",
            DEYE_PV2_AZIMUTH_API,
            DEYE_PV2_TILT,
            DEYE_PV2_CAPACITY_W,
            DEYE_PV2_PANEL_TYPE,
        ),
        DEYEMPPTSensor(
            coordinator,
            SENSOR_DEYE_MPPT3_POTENTIAL_POWER,
            "DEYE_PV3",
            DEYE_PV3_AZIMUTH_API,
            DEYE_PV3_TILT,
            DEYE_PV3_CAPACITY_W,
            DEYE_PV3_PANEL_TYPE,
        ),
        DEYETotalSensor(coordinator),
    ]
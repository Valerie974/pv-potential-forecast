"""Sensors ATON — 3 sensors (estimation + réel + écart, grid-tie).

Fichier : sensors/aton_sensors.py
Rôle : Définit les 3 SensorEntity pour l'ATON (grid-tie, calibration) :
    5. aton_estimated_power   (W)  Estimé agrégé PV1+PV2 (Forecast.Solar)
    6. aton_actual_power       (W)  Source : sensor.philippeb_instant_solar_power
    7. aton_forecast_error     (W)  Estimé − Réel (instantané)

Note : L'ATON est la SEULE installation utilisée pour la calibration (Phase 4).
Le rendement onduleur ATON = 0.97 (comparaison avec production réelle AC).

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.const import UnitOfPower
from homeassistant.core import HomeAssistant

from ..const import (
    ATON_REAL_PRODUCTION_ENTITY,
    ATON_TOTAL_POWER_W,
    CONF_ATON_REAL_PRODUCTION_SENSOR,
    SENSOR_ATON_ACTUAL_POWER,
    SENSOR_ATON_ESTIMATED_POWER,
    SENSOR_ATON_FORECAST_ERROR,
    SOURCE_ACTIVE_FORECAST_SOLAR,
)
from ..entity import PVPotentialEntity

_LOGGER = logging.getLogger(__name__)


def _safe_float(value: Any) -> float | None:
    """Convertit une valeur en float de manière sécurisée."""
    if value is None:
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


class ATONEstimatedSensor(PVPotentialEntity, SensorEntity):
    """Sensor de potentiel estimé ATON (agrégé PV1 + PV2).

    Le potentiel est DC→AC (rendement onduleur = 0.97) pour la
    comparaison avec la production réelle AC.

    Reçoit les métadonnées de source (source_active) car l'ATON est la
    seule installation calibrée.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:solar-power"

    def __init__(self, coordinator: Any) -> None:
        """Initialise le sensor ATON estimé.

        Args:
            coordinator: Le DataUpdateCoordinator.
        """
        super().__init__(coordinator, SENSOR_ATON_ESTIMATED_POWER)
        self._attr_name = "ATON Estimated Power"

    @property
    def native_value(self) -> float | None:
        """Retourne le potentiel estimé de l'ATON (W).

        Lit la puissance estimée (PV1+PV2, après rendement onduleur 0.97)
        depuis les données du coordinator pour l'heure courante.
        """
        data = self.coordinator.data
        if not data or "hourly_forecast" not in data:
            return None

        for entry in data["hourly_forecast"]:
            if entry.get("is_current_hour"):
                return round(entry.get("aton_estimated_w", 0.0), 1)

        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les métadonnées de source et attributs.

        Attributs : source_active, source_weights (pas de pondération en
        Phase 1), confidence, inverter_efficiency, total_capacity_w.
        """
        data = self.coordinator.data
        if not data:
            return None

        return {
            "source_active": data.get(
                "source_active", SOURCE_ACTIVE_FORECAST_SOLAR
            ),
            "source_weights": {"forecast_solar": 1.0},
            "confidence": data.get("confidence", 0.0),
            "inverter_efficiency": 0.97,
            "total_capacity_w": ATON_TOTAL_POWER_W,
        }


class ATONActualSensor(PVPotentialEntity, SensorEntity):
    """Sensor de production réelle ATON.

    Lit la valeur depuis sensor.philippeb_instant_solar_power (puissance
    instantanée de l'onduleur ATON grid-tie).

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:flash"

    def __init__(self, coordinator: Any, hass: HomeAssistant) -> None:
        """Initialise le sensor ATON réel.

        Args:
            coordinator: Le DataUpdateCoordinator.
            hass: Instance Home Assistant pour lire les states.
        """
        super().__init__(coordinator, SENSOR_ATON_ACTUAL_POWER)
        self._attr_name = "ATON Actual Power"
        self._hass = hass

        # Récupérer l'entity_id de production réelle depuis la config
        config = coordinator._config if hasattr(coordinator, "_config") else {}
        self._production_entity = config.get(
            CONF_ATON_REAL_PRODUCTION_SENSOR,
            ATON_REAL_PRODUCTION_ENTITY,
        )

    @property
    def native_value(self) -> float | None:
        """Retourne la production réelle de l'ATON (W).

        Lit la valeur depuis sensor.philippeb_instant_solar_power.
        """
        state = self._hass.states.get(self._production_entity)
        if state is None:
            _LOGGER.debug(
                "Sensor production réelle indisponible: %s",
                self._production_entity,
            )
            return None
        return _safe_float(state.state)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les attributs du sensor ATON réel."""
        return {
            "source_entity": self._production_entity,
        }


class ATONForecastErrorSensor(PVPotentialEntity, SensorEntity):
    """Sensor d'écart entre estimation et production réelle ATON.

    Calcul : aton_forecast_error = aton_estimated_power - aton_actual_power
    Une valeur positive indique une surestimation, négative une sous-estimation.

    Attributes:
        _attr_native_unit_of_measurement: Unité (W).
    """

    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line-variant"

    def __init__(self, coordinator: Any, hass: HomeAssistant) -> None:
        """Initialise le sensor d'écart ATON.

        Args:
            coordinator: Le DataUpdateCoordinator.
            hass: Instance Home Assistant pour lire les states.
        """
        super().__init__(coordinator, SENSOR_ATON_FORECAST_ERROR)
        self._attr_name = "ATON Forecast Error"
        self._hass = hass

        config = coordinator._config if hasattr(coordinator, "_config") else {}
        self._production_entity = config.get(
            CONF_ATON_REAL_PRODUCTION_SENSOR,
            ATON_REAL_PRODUCTION_ENTITY,
        )

    @property
    def native_value(self) -> float | None:
        """Retourne l'écart (estimé − réel) en watts.

        Calculé en temps réel à partir du sensor ATON estimé et du
        sensor de production réelle.
        """
        # Récupérer l'estimé depuis le coordinator
        data = self.coordinator.data
        estimated = None
        if data and "hourly_forecast" in data:
            for entry in data["hourly_forecast"]:
                if entry.get("is_current_hour"):
                    estimated = entry.get("aton_estimated_w", 0.0)
                    break

        if estimated is None:
            return None

        # Récupérer la production réelle
        state = self._hass.states.get(self._production_entity)
        if state is None:
            return None
        actual = _safe_float(state.state)
        if actual is None:
            return None

        error = estimated - actual
        return round(error, 1)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Retourne les attributs du sensor d'écart."""
        return {
            "formula": "aton_estimated_power - aton_actual_power",
            "positive_means": "surestimation",
            "source_entity": self._production_entity,
        }


def create_aton_sensors(
    coordinator: Any, hass: HomeAssistant
) -> list[SensorEntity]:
    """Crée les 3 sensors ATON.

    Args:
        coordinator: Le DataUpdateCoordinator.
        hass: Instance Home Assistant.

    Returns:
        Liste de 3 SensorEntity (estimé + réel + écart).
    """
    return [
        ATONEstimatedSensor(coordinator),
        ATONActualSensor(coordinator, hass),
        ATONForecastErrorSensor(coordinator, hass),
    ]
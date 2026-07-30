"""Stratégie source unique — Forecast.Solar seul.

Fichier : strategies/single_source_strategy.py
Rôle : Applique les dégradations (température, bifacial) sur les
prévisions brutes Forecast.Solar pour produire le potentiel PV final.
Cette stratégie est **définitive** (pas un MVP temporaire) — Forecast.Solar
est la source PV unique.

Étapes pour chaque MPPT et chaque heure :
    1. Récupérer P_forecast_solar brute (watts)
    2. Appliquer correction température (γ, NOCT)
    3. Appliquer gain bifacial (DEYE uniquement)
    4. Appliquer rendement onduleur (DEYE=1.00, ATON=0.97)
    5. Agréger par onduleur et global

Règles :
    - DEYE = potentiel DC pur (onduleur 1.00) — jamais comparé au réel
    - ATON = potentiel DC→AC (onduleur 0.97) pour comparaison avec le réel
    - Bifacial uniquement pour le DEYE (Wingosolar, 70%)
    - Correction température pour tous les MPPT (γ respectif)

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from ..astronomy import is_night
from ..calculations.bifacial import calculate_bifacial_gain
from ..calculations.temperature import (
    calculate_cell_temperature,
    apply_temperature_correction,
)
from ..const import (
    ATON_PV1_AZIMUTH_API,
    ATON_PV1_CAPACITY_W,
    ATON_PV2_AZIMUTH_API,
    ATON_PV2_CAPACITY_W,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TIMEZONE,
    DEYE_PV1_AZIMUTH_API,
    DEYE_PV1_CAPACITY_W,
    DEYE_PV2_AZIMUTH_API,
    DEYE_PV2_CAPACITY_W,
    DEYE_PV3_AZIMUTH_API,
    DEYE_PV3_CAPACITY_W,
    JA_SOLAR_GAMMA,
    JA_SOLAR_NOCT,
    WINGOSOLAR_BIFACIAL,
    WINGOSOLAR_BIFACIALITY_FACTOR,
    WINGOSOLAR_GAMMA,
    WINGOSOLAR_NOCT,
)

_LOGGER = logging.getLogger(__name__)

# Rendements onduleurs
ATON_INVERTER_EFFICIENCY = 0.97   # Grid-tie — conversion DC→AC
DEYE_INVERTER_EFFICIENCY = 1.00   # Off-grid — potentiel DC pur


@dataclass
class MPPTConfig:
    """Configuration d'un MPPT pour la stratégie.

    Attributes:
        name: Nom du MPPT (ex. "DEYE_PV1").
        installation: "ATON" ou "DEYE".
        azimuth: Azimuth Forecast.Solar (-180 à +180).
        tilt: Inclinaison (degrés).
        capacity_w: Capacité en watts.
        gamma: Coefficient de température (%/°C).
        noct: NOCT (°C).
        bifacial: True si bifacial, False sinon.
        bifaciality_factor: Facteur bifacial (0.70 pour DEYE, 0.0 pour ATON).
        inverter_efficiency: Rendement onduleur (0.97 ATON, 1.00 DEYE).
    """

    name: str
    installation: str
    azimuth: float
    tilt: float
    capacity_w: float
    gamma: float
    noct: float
    bifacial: bool
    bifaciality_factor: float
    inverter_efficiency: float


# Configuration des 5 MPPT
MPPT_CONFIGS: list[MPPTConfig] = [
    MPPTConfig(
        name="ATON_PV1",
        installation="ATON",
        azimuth=ATON_PV1_AZIMUTH_API,
        tilt=3,
        capacity_w=ATON_PV1_CAPACITY_W,
        gamma=JA_SOLAR_GAMMA,
        noct=JA_SOLAR_NOCT,
        bifacial=False,
        bifaciality_factor=0.0,
        inverter_efficiency=ATON_INVERTER_EFFICIENCY,
    ),
    MPPTConfig(
        name="ATON_PV2",
        installation="ATON",
        azimuth=ATON_PV2_AZIMUTH_API,
        tilt=3,
        capacity_w=ATON_PV2_CAPACITY_W,
        gamma=JA_SOLAR_GAMMA,
        noct=JA_SOLAR_NOCT,
        bifacial=False,
        bifaciality_factor=0.0,
        inverter_efficiency=ATON_INVERTER_EFFICIENCY,
    ),
    MPPTConfig(
        name="DEYE_PV1",
        installation="DEYE",
        azimuth=DEYE_PV1_AZIMUTH_API,
        tilt=3,
        capacity_w=DEYE_PV1_CAPACITY_W,
        gamma=WINGOSOLAR_GAMMA,
        noct=WINGOSOLAR_NOCT,
        bifacial=True,
        bifaciality_factor=WINGOSOLAR_BIFACIALITY_FACTOR,
        inverter_efficiency=DEYE_INVERTER_EFFICIENCY,
    ),
    MPPTConfig(
        name="DEYE_PV2",
        installation="DEYE",
        azimuth=DEYE_PV2_AZIMUTH_API,
        tilt=3,
        capacity_w=DEYE_PV2_CAPACITY_W,
        gamma=WINGOSOLAR_GAMMA,
        noct=WINGOSOLAR_NOCT,
        bifacial=True,
        bifaciality_factor=WINGOSOLAR_BIFACIALITY_FACTOR,
        inverter_efficiency=DEYE_INVERTER_EFFICIENCY,
    ),
    MPPTConfig(
        name="DEYE_PV3",
        installation="DEYE",
        azimuth=DEYE_PV3_AZIMUTH_API,
        tilt=3,
        capacity_w=DEYE_PV3_CAPACITY_W,
        gamma=WINGOSOLAR_GAMMA,
        noct=WINGOSOLAR_NOCT,
        bifacial=True,
        bifaciality_factor=WINGOSOLAR_BIFACIALITY_FACTOR,
        inverter_efficiency=DEYE_INVERTER_EFFICIENCY,
    ),
]

# Index rapide par nom de MPPT
MPPT_BY_NAME: dict[str, MPPTConfig] = {cfg.name: cfg for cfg in MPPT_CONFIGS}


@dataclass
class HourlyResult:
    """Résultat du calcul de stratégie pour une heure donnée.

    Attributes:
        datetime: Timestamp ISO de l'heure.
        is_current_hour: True si c'est l'heure courante.
        deye_mppt1_w: Potentiel DEYE MPPT1 (W).
        deye_mppt2_w: Potentiel DEYE MPPT2 (W).
        deye_mppt3_w: Potentiel DEYE MPPT3 (W).
        deye_total_w: Potentiel total DEYE (W).
        aton_estimated_w: Potentiel estimé ATON (W) — après rendement onduleur.
        aton_dc_w: Potentiel DC ATON (W) — avant rendement onduleur.
        pv_total_w: Potentiel total installation (W).
        weather: Données météo pour cette heure.
    """

    datetime: str = ""
    is_current_hour: bool = False
    deye_mppt1_w: float = 0.0
    deye_mppt2_w: float = 0.0
    deye_mppt3_w: float = 0.0
    deye_total_w: float = 0.0
    aton_estimated_w: float = 0.0
    aton_dc_w: float = 0.0
    pv_total_w: float = 0.0
    weather: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convertit en dictionnaire pour sérialisation JSON."""
        return {
            "datetime": self.datetime,
            "is_current_hour": self.is_current_hour,
            "deye_mppt1_w": round(self.deye_mppt1_w, 1),
            "deye_mppt2_w": round(self.deye_mppt2_w, 1),
            "deye_mppt3_w": round(self.deye_mppt3_w, 1),
            "deye_total_w": round(self.deye_total_w, 1),
            "aton_estimated_w": round(self.aton_estimated_w, 1),
            "pv_total_w": round(self.pv_total_w, 1),
            "weather": self.weather,
        }


class SingleSourceStrategy:
    """Stratégie Forecast.Solar seul — applique les corrections.

    Utilise uniquement Forecast.Solar comme source PV (pas de pondération).
    Applique les corrections de température et de gain bifacial sur les
    prévisions brutes, puis agrège par onduleur et au niveau global.
    """

    def __init__(
        self,
        forecast_solar_provider: Any,
        weather_provider: Any,
    ) -> None:
        """Initialise la stratégie.

        Args:
            forecast_solar_provider: Provider Forecast.Solar.
            weather_provider: Provider météo (Vevor + fallback).
        """
        self._forecast_solar_provider = forecast_solar_provider
        self._weather_provider = weather_provider

    def _get_mppt_config(self, mppt_name: str) -> MPPTConfig:
        """Retourne la configuration d'un MPPT par son nom.

        Args:
            mppt_name: Nom du MPPT (ex. "DEYE_PV1").

        Returns:
            MPPTConfig correspondante.

        Raises:
            ValueError: Si le MPPT n'existe pas.
        """
        cfg = MPPT_BY_NAME.get(mppt_name)
        if cfg is None:
            raise ValueError(f"MPPT inconnu: {mppt_name}")
        return cfg

    def _parse_timestamp(self, ts: str) -> datetime:
        """Parse un timestamp Forecast.Solar en datetime aware.

        Forecast.Solar retourne soit "2026-07-30 07:00:00" (sans TZ)
        soit "2026-07-30T07:00:00+04:00" (ISO 8601 avec TZ).

        Args:
            ts: Timestamp à parser.

        Returns:
            datetime aware (UTC si pas de TZ dans la string).
        """
        # Essayer le format ISO 8601 d'abord
        try:
            dt = datetime.fromisoformat(ts)
            if dt.tzinfo is None:
                # Si pas de TZ, on assume UTC
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            pass

        # Essayer le format "YYYY-MM-DD HH:MM:SS"
        try:
            dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

        # Dernier recours : maintenant
        _LOGGER.warning("Timestamp non parsable: %s — utilisation maintenant", ts)
        return datetime.now(timezone.utc)

    def apply_corrections(
        self,
        power_w: float,
        mppt_config: MPPTConfig,
        temperature_c: float | None,
        irradiance_ghi: float | None,
    ) -> float:
        """Applique les corrections de température et bifacial sur la puissance.

        Étapes :
            1. Correction température (γ, NOCT) — si température disponible
            2. Gain bifacial — si DEYE (Wingosolar bifacial)
            3. Rendement onduleur (DEYE=1.00, ATON=0.97)

        Args:
            power_w: Puissance brute Forecast.Solar (W).
            mppt_config: Configuration du MPPT.
            temperature_c: Température ambiante (°C) ou None.
            irradiance_ghi: Irradiance GHI (W/m²) ou None.

        Returns:
            Puissance corrigée (W) après toutes les corrections.
        """
        if power_w <= 0:
            return 0.0

        corrected = power_w

        # 1. Correction température
        if temperature_c is not None:
            if irradiance_ghi is not None and irradiance_ghi > 0:
                cell_temp = calculate_cell_temperature(
                    temperature_c, irradiance_ghi, mppt_config.noct
                )
            else:
                # Pas d'irradiance — utiliser la température ambiante
                # comme approximation de la température de cellule
                cell_temp = temperature_c

            corrected = apply_temperature_correction(
                corrected, cell_temp, mppt_config.gamma
            )

        # 2. Gain bifacial (DEYE uniquement)
        if mppt_config.bifacial and mppt_config.bifaciality_factor > 0:
            bifacial_gain = calculate_bifacial_gain(
                corrected, mppt_config.bifaciality_factor
            )
            corrected += bifacial_gain

        # 3. Rendement onduleur
        corrected *= mppt_config.inverter_efficiency

        return max(corrected, 0.0)

    async def get_potential_power(
        self,
        mppt_name: str,
        weather_data: dict[str, Any] | None = None,
    ) -> float:
        """Retourne la puissance potentielle (W) pour l'heure courante.

        Args:
            mppt_name: Nom du MPPT (ex. "DEYE_PV1").
            weather_data: Données météo courantes (dict) ou None pour
                récupérer automatiquement.

        Returns:
            Puissance potentielle corrigée (W) pour l'heure courante.
            Retourne 0.0 si aucune donnée disponible OU si c'est la nuit.
        """
        # Vérification astronomique : forcer 0 W la nuit
        # Utiliser l'heure UTC pour la comparaison astronomique (is_night gère la conversion)
        now = datetime.now(timezone.utc)
        if is_night(now, DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE):
            return 0.0

        # Récupérer les données météo si non fournies
        if weather_data is None:
            weather = await self._weather_provider.get_current_weather()
            weather_data = weather.to_dict()

        temperature_c = weather_data.get("temperature_c")
        irradiance_ghi = weather_data.get("irradiance_ghi")

        # Récupérer la prévision Forecast.Solar
        forecast = await self._forecast_solar_provider.get_mppt_forecast(
            mppt_name
        )
        mppt_config = self._get_mppt_config(mppt_name)

        # Trouver la puissance pour l'heure courante
        current_power = self._get_power_for_hour(forecast.watts, now)

        if current_power is None:
            return 0.0

        # Appliquer les corrections
        return self.apply_corrections(
            current_power, mppt_config, temperature_c, irradiance_ghi
        )

    def _get_power_for_hour(
        self,
        watts: dict[str, float],
        target_time: datetime,
    ) -> float | None:
        """Retourne la puissance pour l'heure la plus proche du target.

        Args:
            watts: Dict {timestamp_str → puissance W}.
            target_time: Heure cible (datetime aware).

        Returns:
            Puissance (W) ou None si aucune donnée.
        """
        if not watts:
            return None

        # Arrondir target_time à l'heure
        target_hour = target_time.replace(minute=0, second=0, microsecond=0)

        best_ts = None
        best_diff = None

        for ts_str, power in watts.items():
            dt = self._parse_timestamp(ts_str)
            diff = abs((dt - target_hour).total_seconds())

            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_ts = power

        return best_ts

    async def get_hourly_forecast(
        self,
        mppt_name: str,
        hours: int = 48,
        weather_data: dict[str, Any] | None = None,
    ) -> list[dict[str, float]]:
        """Retourne une liste de prévisions horaires pour un MPPT.

        Args:
            mppt_name: Nom du MPPT.
            hours: Nombre d'heures de prévision (défaut 48).
            weather_data: Données météo courantes (dict) ou None.

        Returns:
            Liste de dicts horaires : [{datetime, power_w, is_current_hour}].
            La puissance est corrigée (température + bifacial + onduleur).
        """
        forecast = await self._forecast_solar_provider.get_mppt_forecast(
            mppt_name
        )
        mppt_config = self._get_mppt_config(mppt_name)

        # Récupérer les données météo si non fournies
        if weather_data is None:
            weather = await self._weather_provider.get_current_weather()
            weather_data = weather.to_dict()

        temperature_c = weather_data.get("temperature_c")
        irradiance_ghi = weather_data.get("irradiance_ghi")

        results: list[dict[str, float]] = []
        now = datetime.now(timezone.utc)
        target_hour = now.replace(minute=0, second=0, microsecond=0)

        # Trier les timestamps par ordre chronologique
        sorted_watts = sorted(forecast.watts.items())

        for ts_str, power in sorted_watts[:hours]:
            dt = self._parse_timestamp(ts_str)
            is_current = dt.replace(
                minute=0, second=0, microsecond=0
            ) == target_hour

            corrected = self.apply_corrections(
                power, mppt_config, temperature_c, irradiance_ghi
            )

            results.append({
                "datetime": dt.isoformat(),
                "power_w": round(corrected, 1),
                "is_current_hour": is_current,
            })

        return results

    async def get_daily_energy(
        self,
        mppt_name: str,
        day: datetime | None = None,
    ) -> float:
        """Retourne l'énergie potentielle (kWh) pour un jour donné.

        Args:
            mppt_name: Nom du MPPT.
            day: Jour cible (datetime). Si None, utilise aujourd'hui.

        Returns:
            Énergie potentielle en kWh. Retourne 0.0 si pas de données.
        """
        forecast = await self._forecast_solar_provider.get_mppt_forecast(
            mppt_name
        )

        if day is None:
            day = datetime.now(timezone.utc)

        # watt_hours_day contient {date_str → energy_Wh}
        # ex: {"2026-07-30": 6048}
        day_str = day.strftime("%Y-%m-%d")

        energy_wh = forecast.watt_hours_day.get(day_str, 0.0)
        return energy_wh / 1000.0

    async def compute_forecast(
        self,
        hours: int = 48,
    ) -> list[HourlyResult]:
        """Calcule le potentiel PV pour toutes les heures de prévision.

        Méthode principale de la stratégie — calcule le potentiel pour
        chaque heure en combinant les 5 MPPT avec les corrections et
        les données météo.

        Args:
            hours: Nombre d'heures de prévision (défaut 48).

        Returns:
            Liste de HourlyResult (une par heure), avec le détail par
            MPPT, les agrégats DEYE/ATON/total, et les données météo.
        """
        # 1. Récupérer les prévisions Forecast.Solar (5 MPPT)
        all_forecasts = (
            await self._forecast_solar_provider.get_all_forecasts()
        )

        # 2. Récupérer les données météo courantes
        weather = await self._weather_provider.get_current_weather()
        weather_dict = weather.to_dict()

        temperature_c = weather_dict.get("temperature_c")
        irradiance_ghi = weather_dict.get("irradiance_ghi")

        # 3. Collecter tous les timestamps uniques (depuis tous les MPPT)
        all_timestamps: set[str] = set()
        for mppt_name in MPPT_BY_NAME:
            forecast = all_forecasts.get(mppt_name)
            if forecast:
                all_timestamps.update(forecast.watts.keys())

        # Trier les timestamps chronologiquement
        sorted_ts = sorted(all_timestamps, key=self._parse_timestamp)

        # Limiter au nombre d'heures demandé
        sorted_ts = sorted_ts[:hours]

        # Heure courante pour comparaison
        now = datetime.now(timezone.utc)
        target_hour = now.replace(minute=0, second=0, microsecond=0)

        results: list[HourlyResult] = []

        for ts_str in sorted_ts:
            dt = self._parse_timestamp(ts_str)
            is_current = dt.replace(
                minute=0, second=0, microsecond=0
            ) == target_hour

            # Données météo pour cette heure
            if is_current:
                hour_weather = await (
                    self._weather_provider.get_hourly_weather(
                        target_time=dt, is_current_hour=True
                    )
                for ts_str in sorted_ts:
                    dt = self._parse_timestamp(ts_str)
                    is_current = dt.replace(
                        minute=0, second=0, microsecond=0
                    ) == target_hour

                    # Vérification astronomique : forcer 0 W la nuit pour cette heure
                    if is_night(dt, DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE):
                        # La nuit : tous les MPPT à 0 W
                        result = HourlyResult(
                            datetime=dt.isoformat(),
                            is_current_hour=is_current,
                            deye_mppt1_w=0.0,
                            deye_mppt2_w=0.0,
                            deye_mppt3_w=0.0,
                            deye_total_w=0.0,
                            aton_estimated_w=0.0,
                            aton_dc_w=0.0,
                            pv_total_w=0.0,
                            weather={},
                        )
                        results.append(result)
                        continue

                    # Données météo pour cette heure
                    if is_current:
                        hour_weather = await (
                            self._weather_provider.get_hourly_weather(
                                target_time=dt, is_current_hour=True
                            )
                        )
                    else:
                        hour_weather = await (
                            self._weather_provider.get_hourly_weather(
                                target_time=dt, is_current_hour=False
                            )
                        )

                    hour_temp = hour_weather.get("temperature_c")
                    hour_irradiance = hour_weather.get("irradiance_ghi")

                    # Calculer la puissance pour chaque MPPT
                    mppt_powers: dict[str, float] = {}

                    for mppt_name, mppt_config in MPPT_BY_NAME.items():
                        forecast = all_forecasts.get(mppt_name)
                        if forecast is None:
                            mppt_powers[mppt_name] = 0.0
                            continue

                        power = forecast.watts.get(ts_str, 0.0)

                        # Pour l'heure courante, utiliser l'irradiance Vevor
                        # pour la correction température. Pour les heures futures,
                        # irradiance est null — on utilise la température seule.
                        temp_for_correction = hour_temp if hour_temp else temperature_c
                        irr_for_correction = (
                            hour_irradiance if hour_irradiance else irradiance_ghi
                        )

                        corrected = self.apply_corrections(
                            power,
                            mppt_config,
                            temp_for_correction,
                            irr_for_correction,
                        )
                        mppt_powers[mppt_name] = corrected

            # Agréger par onduleur
            deye_total = (
                mppt_powers.get("DEYE_PV1", 0.0)
                + mppt_powers.get("DEYE_PV2", 0.0)
                + mppt_powers.get("DEYE_PV3", 0.0)
            )

            # ATON : la puissance corrigée inclut déjà le rendement onduleur
            aton_dc = (
                mppt_powers.get("ATON_PV1", 0.0)
                + mppt_powers.get("ATON_PV2", 0.0)
            ) / ATON_INVERTER_EFFICIENCY  # Diviser pour récupérer le DC pur

            aton_estimated = (
                mppt_powers.get("ATON_PV1", 0.0)
                + mppt_powers.get("ATON_PV2", 0.0)
            )  # Déjà multiplié par 0.97 dans apply_corrections

            pv_total = deye_total + aton_estimated

            result = HourlyResult(
                datetime=dt.isoformat(),
                is_current_hour=is_current,
                deye_mppt1_w=mppt_powers.get("DEYE_PV1", 0.0),
                deye_mppt2_w=mppt_powers.get("DEYE_PV2", 0.0),
                deye_mppt3_w=mppt_powers.get("DEYE_PV3", 0.0),
                deye_total_w=deye_total,
                aton_estimated_w=aton_estimated,
                aton_dc_w=aton_dc,
                pv_total_w=pv_total,
                weather=hour_weather,
            )
            results.append(result)

        _LOGGER.info(
            "Stratégie: %d heures calculées — %d MPPT, "
            "puissance courante totale=%.1f W",
            len(results),
            len(MPPT_CONFIGS),
            results[0].pv_total_w if results else 0.0,
        )

        return results

    async def get_today_energy_kwh(self) -> float:
        """Calcule l'énergie potentielle totale aujourd'hui (kWh).

        Somme des énergies des 5 MPPT pour aujourd'hui.

        Returns:
            Énergie potentielle en kWh.
        """
        all_forecasts = (
            await self._forecast_solar_provider.get_all_forecasts()
        )
        today = datetime.now(timezone.utc)
        day_str = today.strftime("%Y-%m-%d")

        total_wh = 0.0
        for mppt_name in MPPT_BY_NAME:
            forecast = all_forecasts.get(mppt_name)
            if forecast:
                # L'énergie brute de Forecast.Solar (watt_hours_day)
                # doit être ajustée par le rendement onduleur
                energy_wh = forecast.watt_hours_day.get(day_str, 0.0)
                mppt_config = MPPT_BY_NAME[mppt_name]
                energy_wh *= mppt_config.inverter_efficiency
                total_wh += energy_wh

        return total_wh / 1000.0

    async def get_tomorrow_energy_kwh(self) -> float:
        """Calcule l'énergie potentielle totale demain (kWh).

        Returns:
            Énergie potentielle en kWh.
        """
        all_forecasts = (
            await self._forecast_solar_provider.get_all_forecasts()
        )
        tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
        day_str = tomorrow.strftime("%Y-%m-%d")

        total_wh = 0.0
        for mppt_name in MPPT_BY_NAME:
            forecast = all_forecasts.get(mppt_name)
            if forecast:
                energy_wh = forecast.watt_hours_day.get(day_str, 0.0)
                mppt_config = MPPT_BY_NAME[mppt_name]
                energy_wh *= mppt_config.inverter_efficiency
                total_wh += energy_wh

        return total_wh / 1000.0
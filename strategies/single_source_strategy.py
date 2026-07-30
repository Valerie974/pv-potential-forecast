"""Stratégie source unique — Forecast.Solar seul.

Fichier : strategies/single_source_strategy.py
Rôle : Applique les dégradations (température, bifacial, soiling) sur les
prévisions brutes Forecast.Solar pour produire le potentiel PV final.
Cette stratégie est **définitive** (pas un MVP temporaire) — Forecast.Solar
est la source PV unique.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class StrategyResult:
    """Résultat du calcul de stratégie pour une heure donnée.

    Attributes:
        deye_mppt1_w: Potentiel DEYE MPPT1 (W).
        deye_mppt2_w: Potentiel DEYE MPPT2 (W).
        deye_mppt3_w: Potentiel DEYE MPPT3 (W).
        deye_total_w: Potentiel total DEYE (W).
        aton_estimated_w: Potentiel estimé ATON (W).
        pv_total_w: Potentiel total installation (W).
    """

    deye_mppt1_w: float = 0.0
    deye_mppt2_w: float = 0.0
    deye_mppt3_w: float = 0.0
    deye_total_w: float = 0.0
    aton_estimated_w: float = 0.0
    pv_total_w: float = 0.0


class SingleSourceStrategy:
    """Stratégie Forecast.Solar seul — applique les corrections.

    Étapes pour chaque MPPT et chaque heure :
        1. Récupérer P_forecast_solar brute
        2. Appliquer correction température (γ, NOCT)
        3. Appliquer gain bifacial (DEYE uniquement)
        4. Appliquer dégradations (soiling, rendement onduleur) — Phase 2+
        5. Agréger par onduleur et global
    """

    def __init__(self, forecast_solar_provider: Any, weather_provider: Any) -> None:
        """Initialise la stratégie.

        Args:
            forecast_solar_provider: Provider Forecast.Solar.
            weather_provider: Provider météo.
        """
        self._forecast_solar_provider = forecast_solar_provider
        self._weather_provider = weather_provider

    async def compute_forecast(self) -> list[StrategyResult]:
        """Calcule le potentiel PV pour toutes les heures de prévision.

        Returns:
            Liste de StrategyResult (48 heures).

        TODO Phase 1 :
            - Récupérer les prévisions Forecast.Solar (5 MPPT)
            - Récupérer les données météo (Vevor)
            - Appliquer correction température (calculations/temperature.py)
            - Appliquer gain bifacial DEYE (calculations/bifacial.py)
            - Agréger par onduleur et total
        """
        # TODO Phase 1 : implémenter le calcul complet
        return []

    def apply_derating(
        self,
        power_w: float,
        temperature_c: float,
        gamma: float,
        noct: float,
        bifacial_gain: float = 0.0,
    ) -> float:
        """Applique les corrections de température et bifacial.

        Args:
            power_w: Puissance brute Forecast.Solar (W).
            temperature_c: Température ambiante (°C).
            gamma: Coefficient de température (%/°C, négatif).
            noct: NOCT du panneau (°C).
            bifacial_gain: Gain bifacial (%) — 0.0 pour monofacial.

        Returns:
            Puissance corrigée (W).

        TODO Phase 1 : déléguer à calculations/temperature.py et bifacial.py
        """
        # TODO Phase 1 : implémenter
        return power_w

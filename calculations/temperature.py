"""Correction de température — PV Potential Forecast.

Fichier : calculations/temperature.py
Rôle : Calcule la température de cellule à partir de la température ambiante
et de l'irradiance, puis applique le coefficient de température (γ) pour
corriger la puissance des panneaux.

Paramètres :
    - γ (coefficient de température) : -0.290 %/°C (DEYE Wingosolar),
      -0.350 %/°C (ATON JA Solar)
    - NOCT : 42 °C (DEYE), 45 °C (ATON)
    - Référence STC : 25 °C, 1000 W/m²

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

# Conditions de test standard (STC)
STC_TEMPERATURE_C = 25.0
STC_IRRADIANCE_W_M2 = 1000.0


def calculate_cell_temperature(
    ambient_temperature_c: float,
    irradiance_w_m2: float,
    noct: float,
) -> float:
    """Calcule la température de cellule à partir de la température ambiante.

    Formule NOCT : T_cell = T_amb + (NOCT - 20) × G / 800

    Args:
        ambient_temperature_c: Température ambiante (°C).
        irradiance_w_m2: Irradiance GHI (W/m²).
        noct: NOCT du panneau (°C) — 42 pour DEYE, 45 pour ATON.

    Returns:
        Température de cellule estimée (°C).

    TODO Phase 1 : valider la formule avec les valeurs estimées
    """
    # TODO Phase 1 : implémenter
    if irradiance_w_m2 <= 0:
        return ambient_temperature_c
    return ambient_temperature_c + (noct - 20) * irradiance_w_m2 / 800


def apply_temperature_correction(
    power_w: float,
    cell_temperature_c: float,
    gamma: float,
) -> float:
    """Applique la correction de température sur la puissance.

    Formule : P_corrected = P × (1 + γ × (T_cell - T_STC))

    Args:
        power_w: Puissance à STC (W).
        cell_temperature_c: Température de cellule (°C).
        gamma: Coefficient de température (%/°C, négatif).
            -0.290 pour DEYE, -0.350 pour ATON.

    Returns:
        Puissance corrigée (W).

    TODO Phase 1 : implémenter
    """
    # TODO Phase 1 : implémenter
    delta_t = cell_temperature_c - STC_TEMPERATURE_C
    correction_factor = 1.0 + (gamma / 100.0) * delta_t
    return power_w * correction_factor

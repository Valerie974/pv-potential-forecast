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

# Irradiance de référence pour le calcul NOCT (800 W/m²)
NOCT_REFERENCE_IRRADIANCE_W_M2 = 800.0
NOCT_REFERENCE_AMBIENT_C = 20.0


def calculate_cell_temperature(
    ambient_temperature_c: float,
    irradiance_w_m2: float,
    noct: float,
) -> float:
    """Calcule la température de cellule à partir de la température ambiante.

    Formule NOCT :
        T_cell = T_amb + (NOCT - 20) × G / 800

    où G est l'irradiance GHI (W/m²) et NOCT la température nominale
    de fonctionnement des cellules (°C).

    Args:
        ambient_temperature_c: Température ambiante (°C).
        irradiance_w_m2: Irradiance GHI (W/m²).
        noct: NOCT du panneau (°C) — 42 pour DEYE Wingosolar, 45 pour
            ATON JA Solar.

    Returns:
        Température de cellule estimée (°C). Si l'irradiance est nulle
        ou négative (nuit), retourne la température ambiante.
    """
    if irradiance_w_m2 <= 0:
        return ambient_temperature_c

    delta_noct = noct - NOCT_REFERENCE_AMBIENT_C
    cell_temp = ambient_temperature_c + (
        delta_noct * irradiance_w_m2 / NOCT_REFERENCE_IRRADIANCE_W_M2
    )
    return cell_temp


def apply_temperature_correction(
    power_w: float,
    cell_temperature_c: float,
    gamma: float,
) -> float:
    """Applique la correction de température sur la puissance.

    Formule :
        P_corrected = P × (1 + γ/100 × (T_cell - T_STC))

    γ est exprimé en %/°C (négatif pour les cellules silicium).
    Une température de cellule supérieure à 25 °C réduit la puissance.

    Args:
        power_w: Puissance à STC (W).
        cell_temperature_c: Température de cellule (°C).
        gamma: Coefficient de température (%/°C, négatif).
            -0.290 pour DEYE Wingosolar, -0.350 pour ATON JA Solar.

    Returns:
        Puissance corrigée (W). Jamais négative.
    """
    if power_w <= 0:
        return 0.0

    delta_t = cell_temperature_c - STC_TEMPERATURE_C
    correction_factor = 1.0 + (gamma / 100.0) * delta_t

    # Le facteur de correction ne doit pas devenir négatif
    # (sécurité — en pratique γ × ΔT reste petit)
    correction_factor = max(correction_factor, 0.0)

    return power_w * correction_factor


def calculate_temp_degradation(
    temperature_c: float,
    gamma: float,
    irradiance_w_m2: float = 0.0,
    noct: float = 45.0,
) -> float:
    """Calcule le facteur de dégradation température (0.0 à ~1.1).

    Retourne un facteur multiplicatif à appliquer sur la puissance STC :
        - 1.0 à 25 °C (pas de dégradation)
        - < 1.0 au-dessus de 25 °C (perte de rendement)
        - > 1.0 en dessous de 25 °C (gain — rare en pratique)

    Si l'irradiance est fournie, la température de cellule est estimée
    via la formule NOCT. Sinon, on utilise directement temperature_c
    comme température de cellule.

    Args:
        temperature_c: Température ambiante (°C) ou température de cellule
            si irradiance_w_m2 = 0.
        gamma: Coefficient de température (%/°C, négatif).
        irradiance_w_m2: Irradiance GHI (W/m²). Si > 0, on calcule T_cell
            via NOCT. Si 0, temperature_c est utilisée directement comme
            T_cell.
        noct: NOCT du panneau (°C) — utilisé uniquement si irradiance > 0.

    Returns:
        Facteur de dégradation (float). Multiplier la puissance STC par
        ce facteur pour obtenir la puissance corrigée.
    """
    if irradiance_w_m2 > 0:
        cell_temp = calculate_cell_temperature(temperature_c, irradiance_w_m2, noct)
    else:
        cell_temp = temperature_c

    delta_t = cell_temp - STC_TEMPERATURE_C
    factor = 1.0 + (gamma / 100.0) * delta_t
    return max(factor, 0.0)
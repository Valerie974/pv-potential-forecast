"""Calcul du gain bifacial — DEYE (Wingosolar WGS-M10/78BH).

Fichier : calculations/bifacial.py
Rôle : Calcule le gain de production apporté par la face arrière des
panneaux bifacial du DEYE. Les panneaux ATON (JA Solar S17-325/MR) sont
monofacial — aucun gain.

Paramètres :
    - Bifaciality factor : 0.70 (Wingosolar)
    - Albedo : 0.3 par défaut (sol clair — Phase 1 simplifié)
    - Facteur de structure : 0.85 (montage standard — Phase 1)

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging

from ..const import WINGOSOLAR_BIFACIALITY_FACTOR

_LOGGER = logging.getLogger(__name__)

# Albedo par défaut (Phase 1 — simplifié)
# 0.3 = sol clair (toit blanc ou sol réfléchissant)
# À affiner en Phase 2+ selon le sol réel sous les panneaux DEYE
DEFAULT_ALBEDO = 0.3

# Facteur de structure (dépend du montage — espacement arrière)
# 0.85 = montage standard avec espacement arrière suffisant
DEFAULT_STRUCTURE_FACTOR = 0.85


def calculate_bifacial_gain(
    front_power_w: float,
    bifaciality_factor: float = WINGOSOLAR_BIFACIALITY_FACTOR,
    albedo: float = DEFAULT_ALBEDO,
    structure_factor: float = DEFAULT_STRUCTURE_FACTOR,
) -> float:
    """Calcule le gain de puissance de la face arrière (bifacial).

    Formule simplifiée Phase 1 :
        P_rear = P_front × bifaciality_factor × albedo × structure_factor

    Args:
        front_power_w: Puissance de la face avant (W).
        bifaciality_factor: Facteur bifacial (0.70 pour Wingosolar,
            0.0 pour les panneaux monofacial JA Solar).
        albedo: Réflectivité du sol (0.3 = sol clair par défaut).
        structure_factor: Facteur de structure (0.85 typique — dépend
            du montage et de l'espacement arrière).

    Returns:
        Gain de puissance arrière (W). Retourne 0.0 pour les panneaux
        monofacial (bifaciality_factor = 0.0) ou si la puissance avant
        est nulle/négative.

    Note:
        Phase 1 utilise une formule simplifiée. Phase 2+ affinera
        l'albedo selon le sol réel (toit vs sol) et prendra en compte
        l'ombrage arrière par rangée.
    """
    if front_power_w <= 0 or bifaciality_factor <= 0:
        return 0.0

    gain = front_power_w * bifaciality_factor * albedo * structure_factor
    return max(gain, 0.0)


def calculate_total_bifacial_power(
    front_power_w: float,
    bifaciality_factor: float = WINGOSOLAR_BIFACIALITY_FACTOR,
    albedo: float = DEFAULT_ALBEDO,
    structure_factor: float = DEFAULT_STRUCTURE_FACTOR,
) -> float:
    """Calcule la puissance totale (avant + arrière) d'un panneau bifacial.

    Args:
        front_power_w: Puissance de la face avant (W).
        bifaciality_factor: Facteur bifacial.
        albedo: Réflectivité du sol.
        structure_factor: Facteur de structure.

    Returns:
        Puissance totale (W) — face avant + gain arrière.
        Pour un panneau monofacial (bifaciality_factor = 0.0),
        retourne uniquement la puissance avant.
    """
    if front_power_w <= 0:
        return 0.0

    rear_gain = calculate_bifacial_gain(
        front_power_w, bifaciality_factor, albedo, structure_factor
    )
    return front_power_w + rear_gain
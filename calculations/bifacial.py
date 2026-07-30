"""Calcul du gain bifacial — DEYE (Wingosolar WGS-M10/78BH).

Fichier : calculations/bifacial.py
Rôle : Calcule le gain de production apporté par la face arrière des
panneaux bifacial du DEYE. Les panneaux ATON (JA Solar S17-325/MR) sont
monofacial — aucun gain.

Paramètres :
    - Bifaciality factor : 0.70 (Wingosolar)
    - Albedo : à déterminer (Phase 2+ — dépend du sol)
    - Facteur de structure : dépend de l'espacement arrière (Phase 2+)

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging

from .const import WINGOSOLAR_BIFACIALITY_FACTOR

_LOGGER = logging.getLogger(__name__)


def calculate_bifacial_gain(
    front_power_w: float,
    bifaciality_factor: float = WINGOSOLAR_BIFACIALITY_FACTOR,
    albedo: float = 0.2,
    structure_factor: float = 0.85,
) -> float:
    """Calcule le gain de puissance de la face arrière (bifacial).

    Formule : P_rear = P_front × bifaciality_factor × albedo × structure_factor

    Args:
        front_power_w: Puissance de la face avant (W).
        bifaciality_factor: Facteur bifacial (0.70 pour Wingosolar, 0.0 pour monofacial).
        albedo: Réflectivité du sol (0.2 = sol standard, 0.3 = sol clair).
        structure_factor: Facteur de structure (0.85 typique — dépend du montage).

    Returns:
        Gain de puissance arrière (W).

    TODO Phase 1 : valider la formule avec les valeurs estimées
    TODO Phase 2 : affiner l'albedo selon le sol réel (toit vs sol)
    """
    # TODO Phase 1 : implémenter
    return front_power_w * bifaciality_factor * albedo * structure_factor


def calculate_total_bifacial_power(
    front_power_w: float,
    bifaciality_factor: float = WINGOSOLAR_BIFACIALITY_FACTOR,
    albedo: float = 0.2,
    structure_factor: float = 0.85,
) -> float:
    """Calcule la puissance totale (avant + arrière) pour un panneau bifacial.

    Args:
        front_power_w: Puissance de la face avant (W).
        bifaciality_factor: Facteur bifacial.
        albedo: Réflectivité du sol.
        structure_factor: Facteur de structure.

    Returns:
        Puissance totale (W) — face avant + gain arrière.

    TODO Phase 1 : implémenter
    """
    # TODO Phase 1 : implémenter
    rear_gain = calculate_bifacial_gain(
        front_power_w, bifaciality_factor, albedo, structure_factor
    )
    return front_power_w + rear_gain

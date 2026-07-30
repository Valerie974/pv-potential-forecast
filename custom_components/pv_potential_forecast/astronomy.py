"""Calculs astronomiques — lever et coucher du soleil.

Fichier : astronomy.py
Rôle : Calcule les heures de lever (sunrise) et coucher (sunset) du soleil
pour une position géographique donnée, afin de forcer les capteurs de
puissance instantanée à 0 W pendant la nuit.

Utilise l'algorithme de Jean Meeus (Astronomical Algorithms) via le
package `astral` pour des calculs précis.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from astral import LocationInfo
from astral.sun import sun

from .const import DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE

_LOGGER = logging.getLogger(__name__)


def get_sun_times(
    date: datetime | None = None,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    tz: str = DEFAULT_TIMEZONE,
) -> dict[str, datetime]:
    """Calcule les heures de lever et coucher du soleil.

    Args:
        date: Date pour le calcul (datetime aware). Si None, utilise
            datetime.now(timezone.utc).
        latitude: Latitude du site.
        longitude: Longitude du site.
        tz: Timezone IANA (ex. "Indian/Reunion").

    Returns:
        Dictionnaire {
            "sunrise": datetime aware du lever du soleil,
            "sunset": datetime aware du coucher du soleil,
            "noon": datetime aware du midi solaire,
            "dusk": datetime aware du crépuscule civil,
            "dawn": datetime aware de l'aube civile,
        }.
    """
    if date is None:
        date = datetime.now(timezone.utc)

    # Créer une LocationInfo pour astral
    location = LocationInfo(
        name="Installation PV",
        region="La Réunion",
        timezone=tz,
        latitude=latitude,
        longitude=longitude,
    )

    try:
        s = sun(location.observer, date=date.date(), tzinfo=location.timezone)
        return {
            "sunrise": s["sunrise"],
            "sunset": s["sunset"],
            "noon": s["noon"],
            "dusk": s["dusk"],
            "dawn": s["dawn"],
        }
    except Exception as exc:
        _LOGGER.error(
            "Erreur calcul astronomique pour %s: %s",
            date.date(),
            exc,
        )
        # Fallback : retourner des valeurs par défaut (6h-18h UTC+4 = 2h-14h UTC)
        # pour La Réunion en hiver austral
        fallback_sunrise = date.replace(hour=2, minute=0, second=0, microsecond=0)
        fallback_sunset = date.replace(hour=14, minute=0, second=0, microsecond=0)
        return {
            "sunrise": fallback_sunrise,
            "sunset": fallback_sunset,
            "noon": date.replace(hour=8, minute=0, second=0, microsecond=0),
            "dusk": fallback_sunset,
            "dawn": fallback_sunrise,
        }


def is_night(
    check_time: datetime | None = None,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    tz: str = DEFAULT_TIMEZONE,
) -> bool:
    """Vérifie si une heure donnée est la nuit (après sunset, avant sunrise).

    Args:
        check_time: Heure à vérifier (datetime aware). Si None, utilise
            datetime.now(timezone.utc).
        latitude: Latitude du site.
        longitude: Longitude du site.
        tz: Timezone IANA.

    Returns:
        True si check_time est la nuit (après sunset OU avant sunrise du jour),
        False sinon (jour).
    """
    if check_time is None:
        check_time = datetime.now(timezone.utc)

    # S'assurer que check_time est aware
    if check_time.tzinfo is None:
        check_time = check_time.replace(tzinfo=timezone.utc)

    sun_times = get_sun_times(check_time, latitude, longitude, tz)
    sunrise = sun_times["sunrise"]
    sunset = sun_times["sunset"]

    # La nuit = après le coucher OU avant le lever
    # (pour gérer le cas où on est entre minuit et sunrise)
    is_after_sunset = check_time >= sunset
    is_before_sunrise = check_time < sunrise

    return is_after_sunset or is_before_sunrise


def get_daylight_hours(
    date: datetime | None = None,
    latitude: float = DEFAULT_LATITUDE,
    longitude: float = DEFAULT_LONGITUDE,
    tz: str = DEFAULT_TIMEZONE,
) -> float:
    """Calcule la durée du jour (heures d'ensoleillement).

    Args:
        date: Date pour le calcul. Si None, utilise aujourd'hui.
        latitude: Latitude du site.
        longitude: Longitude du site.
        tz: Timezone IANA.

    Returns:
        Durée du jour en heures (float).
    """
    sun_times = get_sun_times(date, latitude, longitude, tz)
    sunrise = sun_times["sunrise"]
    sunset = sun_times["sunset"]
    daylight_duration = (sunset - sunrise).total_seconds() / 3600.0
    return daylight_duration

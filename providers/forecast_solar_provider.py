"""Provider Forecast.Solar — PV Potential Forecast.

Fichier : providers/forecast_solar_provider.py
Rôle : Effectue les 5 appels API Forecast.Solar (1 par MPPT) pour récupérer
les prévisions de potentiel photovoltaïque sur 48h.

URL : https://api.forecast.solar/estimate/{lat}/{lon}/{tilt}/{azimuth}/{capacity_kW}
Quota : 12 req/heure/IP (gratuit, pas de clé API)

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from .const import (
    ATON_PV1_AZIMUTH_API,
    ATON_PV1_CAPACITY_W,
    ATON_PV2_AZIMUTH_API,
    ATON_PV2_CAPACITY_W,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_TILT,
    DEYE_PV1_AZIMUTH_API,
    DEYE_PV1_CAPACITY_W,
    DEYE_PV2_AZIMUTH_API,
    DEYE_PV2_CAPACITY_W,
    DEYE_PV3_AZIMUTH_API,
    DEYE_PV3_CAPACITY_W,
    FORECAST_SOLAR_BASE_URL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class MPPTForecast:
    """Prévision Forecast.Solar pour un MPPT donné.

    Attributes:
        mppt_name: Nom du MPPT (ex. "DEYE_PV1").
        azimuth: Azimuth utilisé pour l'appel API (-180 à +180).
        capacity_w: Capacité du MPPT en watts.
        pv_estimate: Prévision nominale (W).
        pv_estimate10: Prévision optimiste (W).
        pv_estimate90: Prévision pessimiste (W).
        timestamps: Liste des timestamps de prévision.
    """

    mppt_name: str
    azimuth: float
    capacity_w: float
    pv_estimate: list[float] | None = None
    pv_estimate10: list[float] | None = None
    pv_estimate90: list[float] | None = None
    timestamps: list[datetime] | None = None


class ForecastSolarProvider:
    """Provider Forecast.Solar — effectue les 5 appels API MPPT.

    Attributes:
        latitude: Latitude La Possession (-20.9295).
        longitude: Longitude La Possession (55.3520).
        tilt: Inclinaison de toutes les strings (3°).
    """

    def __init__(
        self,
        latitude: float = DEFAULT_LATITUDE,
        longitude: float = DEFAULT_LONGITUDE,
        tilt: float = DEFAULT_TILT,
    ) -> None:
        """Initialise le provider Forecast.Solar.

        Args:
            latitude: Latitude du site.
            longitude: Longitude du site.
            tilt: Inclinaison des panneaux (degrés).
        """
        self._latitude = latitude
        self._longitude = longitude
        self._tilt = tilt

        # Configuration des 5 MPPT pour Forecast.Solar
        self._mppt_configs: list[dict[str, Any]] = [
            {
                "name": "ATON_PV1",
                "azimuth": ATON_PV1_AZIMUTH_API,
                "capacity_w": ATON_PV1_CAPACITY_W,
            },
            {
                "name": "ATON_PV2",
                "azimuth": ATON_PV2_AZIMUTH_API,
                "capacity_w": ATON_PV2_CAPACITY_W,
            },
            {
                "name": "DEYE_PV1",
                "azimuth": DEYE_PV1_AZIMUTH_API,
                "capacity_w": DEYE_PV1_CAPACITY_W,
            },
            {
                "name": "DEYE_PV2",
                "azimuth": DEYE_PV2_AZIMUTH_API,
                "capacity_w": DEYE_PV2_CAPACITY_W,
            },
            {
                "name": "DEYE_PV3",
                "azimuth": DEYE_PV3_AZIMUTH_API,
                "capacity_w": DEYE_PV3_CAPACITY_W,
            },
        ]

    async def get_all_mppt_forecasts(self) -> dict[str, MPPTForecast]:
        """Effectue les 5 appels Forecast.Solar (1 par MPPT).

        Returns:
            Dictionnaire {mppt_name: MPPTForecast}.

        TODO Phase 1 :
            - Construire les 5 URLs
            - Effectuer les appels HTTP (async)
            - Parser les réponses (pv_estimate, pv_estimate10, pv_estimate90)
            - Gérer les erreurs (timeout, rate limit, HTTP error)
        """
        # TODO Phase 1 : implémenter les 5 appels
        return {}

    async def _fetch_single_mppt(self, mppt_config: dict[str, Any]) -> MPPTForecast:
        """Effectue un seul appel Forecast.Solar pour un MPPT.

        Args:
            mppt_config: Configuration du MPPT (name, azimuth, capacity_w).

        Returns:
            MPPTForecast — prévision pour ce MPPT.

        TODO Phase 1 : implémenter l'appel HTTP et le parsing
        """
        # URL : https://api.forecast.solar/estimate/{lat}/{lon}/{tilt}/{azimuth}/{kWc}
        url = (
            f"{FORECAST_SOLAR_BASE_URL}/"
            f"{self._latitude}/{self._longitude}/{self._tilt}/"
            f"{mppt_config['azimuth']}/{mppt_config['capacity_w'] / 1000}"
        )
        _LOGGER.debug("Appel Forecast.Solar : %s (%s)", url, mppt_config["name"])

        # TODO Phase 1 : effectuer l'appel HTTP
        # TODO Phase 1 : parser la réponse JSON
        return MPPTForecast(
            mppt_name=mppt_config["name"],
            azimuth=mppt_config["azimuth"],
            capacity_w=mppt_config["capacity_w"],
        )

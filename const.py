"""Constantes du moteur de prévision photovoltaïque — PV Potential Forecast.

Fichier : const.py
Rôle : Centralise toutes les constantes de la custom integration (domaine,
coordonnées GPS, configuration des 5 MPPT, entity_ids Vevor / ATON /
Météo-France, coefficients de panneaux, paramètres de rate limit Forecast.Solar,
intervalle de polling, noms des 11 sensors de la Phase 1).

Architecture : v3 — Forecast.Solar source PV unique, station Vevor source
météo principale, weather.ilapos13 couverture nuageuse locale,
Météo-France fallback uniquement.

Auteur : Victor, expert technique — équipe IA de Valérie
Date : 30 juillet 2026
"""

# ---------------------------------------------------------------------------
# Domaine de la custom integration
# ---------------------------------------------------------------------------

DOMAIN = "pv_potential_forecast"

# ---------------------------------------------------------------------------
# Localisation — La Possession, La Réunion (hémisphère Sud)
# ---------------------------------------------------------------------------

DEFAULT_LATITUDE = -20.9295
DEFAULT_LONGITUDE = 55.3520
DEFAULT_TIMEZONE = "Indian/Reunion"
DEFAULT_TILT = 3  # Toutes les strings ont ~3° d'inclinaison (quasi-horizontale)

# ---------------------------------------------------------------------------
# Configuration des 5 MPPT
# ---------------------------------------------------------------------------
# Convention azimuth Forecast.Solar : -180 à +180 (0° = Nord, valeurs
# négatives = Ouest). Conversion : si azimuth > 180°, soustraire 360°.

# ATON — Grid-tie, 2 MPPT (JA Solar S17-325/MR, monofacial)
ATON_PV1_AZIMUTH_API = -104.0   # 256° Valérie → -104° Forecast.Solar
ATON_PV1_TILT = 3
ATON_PV1_CAPACITY_W = 2275       # 7 × 325 Wc
ATON_PV1_PANEL_TYPE = "JA Solar S17-325/MR"

ATON_PV2_AZIMUTH_API = -77.0     # 283° Valérie → -77° Forecast.Solar
ATON_PV2_TILT = 3
ATON_PV2_CAPACITY_W = 3900       # 12 × 325 Wc
ATON_PV2_PANEL_TYPE = "JA Solar S17-325/MR"

# DEYE — Off-grid, 3 MPPT (Wingosolar WGS-M10/78BH, bifacial)
DEYE_PV1_AZIMUTH_API = 53.0     # 53° (pas de conversion nécessaire)
DEYE_PV1_TILT = 3
DEYE_PV1_CAPACITY_W = 4060       # 7 × 580 Wc
DEYE_PV1_PANEL_TYPE = "Wingosolar WGS-M10/78BH"

DEYE_PV2_AZIMUTH_API = -52.0    # 308° Valérie → -52° Forecast.Solar
DEYE_PV2_TILT = 3
DEYE_PV2_CAPACITY_W = 2900       # 5 × 580 Wc
DEYE_PV2_PANEL_TYPE = "Wingosolar WGS-M10/78BH"

DEYE_PV3_AZIMUTH_API = 27.0     # 27° (pas de conversion nécessaire)
DEYE_PV3_TILT = 3
DEYE_PV3_CAPACITY_W = 2900       # 5 × 580 Wc
DEYE_PV3_PANEL_TYPE = "Wingosolar WGS-M10/78BH"

# Puissances totales
ATON_TOTAL_POWER_W = 6175         # 2275 + 3900
DEYE_TOTAL_POWER_W = 9860         # 4060 + 2900 + 2900
INSTALLATION_TOTAL_POWER_W = 16035  # 6175 + 9860

# ---------------------------------------------------------------------------
# Entity_ids — Station Vevor (Wunderground, La Possession)
# Source météo principale (13 capteurs + 1 weather entity)
# ---------------------------------------------------------------------------

# Capteurs Vevor (sensor.ilapos13_*)
VEVOR_IRRADIANCE_ENTITY = "sensor.ilapos13_solar_radiation"          # GHI W/m²
VEVOR_TEMPERATURE_ENTITY = "sensor.ilapos13_temperature"             # °C
VEVOR_PRECIP_RATE_ENTITY = "sensor.ilapos13_precipitation_rate"     # mm/h
VEVOR_PRECIP_TODAY_ENTITY = "sensor.ilapos13_precipitation_today"   # mm
VEVOR_UV_INDEX_ENTITY = "sensor.ilapos13_uv_index"                  # UV index
VEVOR_HUMIDITY_ENTITY = "sensor.ilapos13_relative_humidity"          # %
VEVOR_PRESSURE_ENTITY = "sensor.ilapos13_pressure"                   # mbar
VEVOR_DEWPOINT_ENTITY = "sensor.ilapos13_dewpoint"                   # °C
VEVOR_HEAT_INDEX_ENTITY = "sensor.ilapos13_heat_index"               # °C
VEVOR_WIND_SPEED_ENTITY = "sensor.ilapos13_wind_speed"               # km/h
VEVOR_WIND_DIR_ENTITY = "sensor.ilapos13_wind_direction_degrees"      # °
VEVOR_WIND_GUST_ENTITY = "sensor.ilapos13_wind_gust"                 # km/h

# Weather entity Vevor — couverture nuageuse locale (mapping condition → %)
VEVOR_WEATHER_ENTITY = "weather.ilapos13"

# ---------------------------------------------------------------------------
# Entity_id — Production réelle ATON (Grid-tie, calibration)
# ---------------------------------------------------------------------------

ATON_REAL_PRODUCTION_ENTITY = "sensor.philippeb_instant_solar_power"

# ---------------------------------------------------------------------------
# Météo-France — Fallback uniquement (données St-Denis, pas La Possession)
# ---------------------------------------------------------------------------

METEO_FRANCE_FALLBACK_ENTITY = (
    "sensor.meteo_france_forecast_for_city_la_possession_reunion_re_"
    "saint_denis_pressure"
)

# ---------------------------------------------------------------------------
# Coefficients de panneaux
# ---------------------------------------------------------------------------

# JA Solar S17-325/MR (ATON — monofacial)
JA_SOLAR_GAMMA = -0.350     # %/°C — estimé (datasheet non disponible)
JA_SOLAR_NOCT = 45.0        # °C — estimé
JA_SOLAR_BIFACIAL = False
JA_SOLAR_BIFACIALITY_FACTOR = 0.0

# Wingosolar WGS-M10/78BH (DEYE — bifacial half-cut M10)
WINGOSOLAR_GAMMA = -0.290   # %/°C — estimé (datasheet non disponible)
WINGOSOLAR_NOCT = 42.0      # °C — estimé
WINGOSOLAR_BIFACIAL = True
WINGOSOLAR_BIFACIALITY_FACTOR = 0.70

# ---------------------------------------------------------------------------
# Rate limit Forecast.Solar (API gratuite, 12 req/heure/IP)
# ---------------------------------------------------------------------------

FORECAST_SOLAR_HOURLY_LIMIT = 12       # Quota gratuit
FORECAST_SOLAR_SAFETY_THRESHOLD = 10   # Seuil de sécurité (83 %)
FORECAST_SOLAR_CALLS_PER_UPDATE = 5    # 1 appel par MPPT
FORECAST_SOLAR_CACHE_TTL_MIN = 60     # TTL du cache (minutes)

# URL de base Forecast.Solar
FORECAST_SOLAR_BASE_URL = "https://api.forecast.solar/estimate"

# ---------------------------------------------------------------------------
# Intervalle de polling
# ---------------------------------------------------------------------------

POLL_INTERVAL_MINUTES = 60   # Stratégie B — 5 appels/heure = 42 % du quota

# ---------------------------------------------------------------------------
# Indice de confiance — seuils de fraîcheur (minutes)
# ---------------------------------------------------------------------------

CONFIDENCE_FRESH_60_MIN = 60
CONFIDENCE_FRESH_120_MIN = 120
CONFIDENCE_FRESH_240_MIN = 240

CONFIDENCE_VALUE_FRESH = 1.0
CONFIDENCE_VALUE_2H = 0.8
CONFIDENCE_VALUE_4H = 0.5
CONFIDENCE_VALUE_STALE = 0.2
CONFIDENCE_VALUE_NONE = 0.0

# ---------------------------------------------------------------------------
# Mapping condition weather → couverture nuageuse (%)
# ---------------------------------------------------------------------------

CONDITION_TO_CLOUD_COVER: dict[str, int] = {
    "clear-night": 0,
    "sunny": 0,
    "clear": 0,
    "windy": 10,
    "windy-variant": 10,
    "fog": 80,
    "partlycloudy": 50,
    "cloudy": 75,
    "rainy": 90,
    "pouring": 95,
    "lightning": 90,
    "lightning-rainy": 95,
    "snowy": 90,
    "snowy-rainy": 90,
    "hail": 90,
    "exceptional": 50,
}

# ---------------------------------------------------------------------------
# Noms des 11 sensors — Phase 1 MVP
# ---------------------------------------------------------------------------

# DEYE — 4 sensors (potentiel panneaux, off-grid, aucune validation)
SENSOR_DEYE_MPPT1_POTENTIAL_POWER = "deye_mppt1_potential_power"
SENSOR_DEYE_MPPT2_POTENTIAL_POWER = "deye_mppt2_potential_power"
SENSOR_DEYE_MPPT3_POTENTIAL_POWER = "deye_mppt3_potential_power"
SENSOR_DEYE_TOTAL_POTENTIAL_POWER = "deye_total_potential_power"

# ATON — 3 sensors (estimation + réel + écart, grid-tie)
SENSOR_ATON_ESTIMATED_POWER = "aton_estimated_power"
SENSOR_ATON_ACTUAL_POWER = "aton_actual_power"
SENSOR_ATON_FORECAST_ERROR = "aton_forecast_error"

# GLOBAL — 4 sensors (agrégats + prévisions)
SENSOR_PV_TOTAL_POTENTIAL_POWER = "pv_total_potential_power"
SENSOR_PV_POTENTIAL_TODAY = "pv_potential_today"
SENSOR_PV_POTENTIAL_TOMORROW = "pv_potential_tomorrow"
SENSOR_PV_HOURLY_FORECAST = "pv_hourly_forecast"

# Liste complète des 11 sensors Phase 1
ALL_PHASE1_SENSORS: list[str] = [
    SENSOR_DEYE_MPPT1_POTENTIAL_POWER,
    SENSOR_DEYE_MPPT2_POTENTIAL_POWER,
    SENSOR_DEYE_MPPT3_POTENTIAL_POWER,
    SENSOR_DEYE_TOTAL_POTENTIAL_POWER,
    SENSOR_ATON_ESTIMATED_POWER,
    SENSOR_ATON_ACTUAL_POWER,
    SENSOR_ATON_FORECAST_ERROR,
    SENSOR_PV_TOTAL_POTENTIAL_POWER,
    SENSOR_PV_POTENTIAL_TODAY,
    SENSOR_PV_POTENTIAL_TOMORROW,
    SENSOR_PV_HOURLY_FORECAST,
]

# ---------------------------------------------------------------------------
# Métadonnées de source (attributs ajoutés sur 5 sensors)
# ---------------------------------------------------------------------------

SOURCE_ACTIVE_FORECAST_SOLAR = "forecast_solar"
SOURCE_ACTIVE_NONE = "none"

# Sensors recevant les métadonnées de source
SENSORS_WITH_SOURCE_METADATA: list[str] = [
    SENSOR_PV_HOURLY_FORECAST,
    SENSOR_PV_POTENTIAL_TODAY,
    SENSOR_PV_POTENTIAL_TOMORROW,
    SENSOR_PV_TOTAL_POTENTIAL_POWER,
    SENSOR_ATON_ESTIMATED_POWER,
]

# ---------------------------------------------------------------------------
# Configuration flow — clés de données utilisateur
# ---------------------------------------------------------------------------

CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_WUNDERGROUND_IRRADIANCE_ENTITY = "wunderground_irradiance_entity"
CONF_WUNDERGROUND_TEMP_ENTITY = "wunderground_temp_entity"
CONF_WUNDERGROUND_PRECIP_ENTITY = "wunderground_precip_entity"
CONF_WUNDERGROUND_UV_INDEX_ENTITY = "wunderground_uv_index_entity"
CONF_WUNDERGROUND_WEATHER_ENTITY = "wunderground_weather_entity"
CONF_METEO_FRANCE_ENTITY = "meteo_france_entity"
CONF_ATON_REAL_PRODUCTION_SENSOR = "aton_real_production_sensor"

# Valeurs par défaut pour le config_flow
DEFAULT_WUNDERGROUND_IRRADIANCE_ENTITY = VEVOR_IRRADIANCE_ENTITY
DEFAULT_WUNDERGROUND_TEMP_ENTITY = VEVOR_TEMPERATURE_ENTITY
DEFAULT_WUNDERGROUND_PRECIP_ENTITY = VEVOR_PRECIP_RATE_ENTITY
DEFAULT_WUNDERGROUND_UV_INDEX_ENTITY = VEVOR_UV_INDEX_ENTITY
DEFAULT_WUNDERGROUND_WEATHER_ENTITY = VEVOR_WEATHER_ENTITY
DEFAULT_METEO_FRANCE_ENTITY = METEO_FRANCE_FALLBACK_ENTITY
DEFAULT_ATON_REAL_PRODUCTION_SENSOR = ATON_REAL_PRODUCTION_ENTITY

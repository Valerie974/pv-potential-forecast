# PV Potential Forecast — Moteur de prévision photovoltaïque pour Home Assistant

## Objectif du projet

**PV Potential Forecast** est une custom integration Home Assistant qui calcule
le **potentiel photovoltaïque** d'une installation multi-orientation (5 MPPT,
2 onduleurs) à La Possession, La Réunion.

> **⚠️ Principe fondateur #0 :** Ce moteur calcule le **potentiel des panneaux**
> (ce que les panneaux *peuvent* produire dans les conditions météo attendues),
> et **non** la production réelle de l'onduleur. Le DEYE (off-grid) n'est jamais
> comparé à une production réelle. L'ATON (grid-tie) est la seule installation
> utilisée pour la calibration (Phase 4).

## Installation

### Via HACS (Home Assistant Community Store)

1. Ouvrir HACS → **Integrations** → ⋮ → **Custom repositories**
2. Ajouter : `https://github.com/Valerie974/pv-potential-forecast`
3. Catégorie : **Integration**
4. Installer **PV Potential Forecast**
5. Redémarrer Home Assistant
6. **Paramètres** → **Appareils & Services** → **Ajouter une intégration**
   → Rechercher **PV Potential Forecast**

### Installation manuelle

1. Copier le dossier `pv-potential-forecast/` dans
   `config/custom_components/` de Home Assistant
2. Redémarrer Home Assistant
3. Configurer via **Paramètres** → **Appareils & Services**

## Configuration

La configuration se fait via le **config flow** (interface HA). Champs demandés :

| Champ | Défaut | Description |
|---|---|---|
| Latitude | -20.9295 | La Possession |
| Longitude | 55.3520 | La Possession |
| Entité irradiance Vevor | `sensor.ilapos13_solar_radiation` | GHI W/m² |
| Entité température Vevor | `sensor.ilapos13_temperature` | °C |
| Entité précipitations Vevor | `sensor.ilapos13_precipitation_rate` | mm/h |
| Entité UV Vevor | `sensor.ilapos13_uv_index` | Indice UV (optionnel) |
| Weather entity Vevor | `weather.ilapos13` | Couverture nuageuse locale |
| Entité Météo-France | `sensor.meteo_france_..._pressure` | Fallback (St-Denis) |
| Production réelle ATON | `sensor.philippeb_instant_solar_power` | Calibration |

Aucune clé API requise — Forecast.Solar est gratuit sans inscription.

## Sources de données

### Source PV — Forecast.Solar (unique)

- **API** : `https://api.forecast.solar/estimate/{lat}/{lon}/{tilt}/{azimuth}/{capacity_kW}`
- **5 appels** (1 par MPPT) — orientations différentes nécessitent des appels séparés
- **Quota gratuit** : 12 req/heure/IP → 5 appels = 42 % du quota
- **Polling** : 60 min avec rate limiter logiciel (seuil 10 appels/heure)
- **Cache** : TTL 60 min pour éviter les appels redondants

### Source météo — Station Vevor (Wunderground, La Possession)

- **13 capteurs** `sensor.ilapos13_*` : irradiance GHI, température, précipitations,
  UV, humidité, pression, vent, point de rosée, indice de chaleur
- **Weather entity** `weather.ilapos13` : couverture nuageuse locale
  (mapping condition → %)
- **Fiabilité** : ✅ Haute — mesure locale sur le toit

### Fallback météo — Météo-France (St-Denis)

- Utilisé uniquement si la station Vevor est indisponible
- **Fiabilité** : ⚠️ Faible — micro-climat de St-Denis ≠ La Possession

### Sources abandonnées

- **Solcast** : ne couvre pas La Réunion (erreur de couverture satellite)
- **OpenUV** : abandonné — la station Vevor fournit déjà `sensor.ilapos13_uv_index`

## Architecture modulaire

```
pv-potential-forecast/
├── manifest.json            # Manifeste de la custom integration
├── __init__.py              # Point d'entrée — setup coordinator
├── config_flow.py           # Configuration flow (config_entry)
├── const.py                 # Constantes (domain, entity_ids, coefficients)
├── coordinator.py           # DataUpdateCoordinator (poll 60 min, rate limiter)
├── entity.py                # Entity de base
├── sensor.py                # Plateforme sensor (enregistre les 11 sensors)
├── providers/
│   ├── forecast_solar_provider.py   # Provider Forecast.Solar (5 appels MPPT)
│   └── weather_provider.py          # Provider météo (Vevor + MF fallback)
├── strategies/
│   └── single_source_strategy.py    # Stratégie Forecast.Solar seul (définitive)
├── calculations/
│   ├── bifacial.py          # Calcul gain bifacial DEYE (Wingosolar)
│   └── temperature.py       # Correction température (γ, NOCT)
├── sensors/
│   ├── deye_sensors.py      # 4 sensors DEYE (potentiel)
│   ├── aton_sensors.py      # 3 sensors ATON (estimé + réel + écart)
│   └── global_sensors.py    # 4 sensors globaux (agrégats + prévisions)
├── hacs.json               # Configuration HACS
└── README.md               # Documentation
```

### Diagramme de flux

```
                ┌───────────────────────────────────┐
                │    DataUpdateCoordinator          │
                │    (poll 60 min, rate limiter)     │
                └───────────────┬───────────────────┘
                               │
            ┌──────────────────┼──────────────────┐
            ▼                  ▼                  ▼
  ┌──────────────────┐ ┌──────────────────┐  ┌──────────────┐
  │ Forecast.Solar    │ │ WeatherProvider   │  │ (Phase 3)    │
  │ Provider          │ │                   │  │ Physical     │
  │                   │ │ Vevor (priorité)  │  │ Model        │
  │ 5 appels MPPT :   │ │ MF (fallback)     │  │ Provider     │
  │ ATON_PV1 (-104°)  │ │                   │  │              │
  │ ATON_PV2 (-77°)   │ │ GHI, temp, UV,    │  └──────────────┘
  │ DEYE_PV1 (53°)    │ │ cloud cover       │
  │ DEYE_PV2 (-52°)   │ └────────┬──────────┘
  │ DEYE_PV3 (27°)    │          │
  └─────────┬─────────┘          │
            └────────────────────┼──┐
                                 ▼  │
                ┌──────────────────────────────┐
                │  SingleSourceStrategy         │
                │  (Forecast.Solar seul —       │
                │   stratégie définitive)       │
                └──────────────┬───────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
          ┌─────────┐   ┌──────────┐   ┌──────────┐
          │ DEYE    │   │  ATON    │   │ Global   │
          │ sensors │   │  sensors │   │ sensors  │
          │ (4)     │   │  (3)     │   │ (4)      │
          └─────────┘   └──────────┘   └──────────┘
```

## Les 11 sensors — Phase 1 MVP

```
DEYE (4 — potentiel panneaux, off-grid, aucune validation)
├── sensor.deye_mppt1_potential_power       (W)  MPPT1 — 53° ENE, 4 060 Wc
├── sensor.deye_mppt2_potential_power       (W)  MPPT2 — 308° NW, 2 900 Wc
├── sensor.deye_mppt3_potential_power       (W)  MPPT3 — 27° NNE, 2 900 Wc
└── sensor.deye_total_potential_power       (W)  Somme 3 MPPT

ATON (3 — estimation + réel + écart, grid-tie)
├── sensor.aton_estimated_power             (W)  Estimé agrégé PV1+PV2
├── sensor.aton_actual_power                (W)  Source : sensor.philippeb_instant_solar_power
└── sensor.aton_forecast_error              (W)  Estimé − Réel (instantané)

GLOBAL (4 — agrégats + prévisions)
├── sensor.pv_total_potential_power         (W)  DEYE + ATON (instantané)
├── sensor.pv_potential_today                (kWh) Énergie potentielle aujourd'hui
├── sensor.pv_potential_tomorrow             (kWh) Énergie potentielle demain
└── sensor.pv_hourly_forecast                (W)  État = heure courante, attributs = 48h
```

## Plan de développement — 5 phases

| Phase | Objectif | Durée | Statut |
|---|---|---|---|
| **Phase 0** — Préparation | Dépôt Git, structure, constantes | 2-3 jours | ✅ En cours |
| **Phase 1** — MVP | 11 sensors, Forecast.Solar, météo Vevor | 1-2 semaines | À venir |
| **Phase 2** — Contribution | Contribution par MPPT, agrégats horaires | 1 semaine | À venir |
| **Phase 3** — Modèle physique | Fallback complet, modèle astronomique | 2-3 semaines | À venir |
| **Phase 4** — Calibration | Calibration adaptative contre ATON | 2 semaines | À venir |
| **Phase 5** — Pilotage | Automatisation, délestage, optimisation | 2-3 semaines | À venir |

## Installation photovoltaïque

| Onduleur | Type | MPPT | Panneaux | Azimuth | Tilt | Puissance |
|---|---|---|---|---|---|---|
| DEYE | Off-grid | PV1 | Wingosolar WGS-M10/78BH (×7) | 53° ENE | 3° | 4 060 Wc |
| DEYE | Off-grid | PV2 | Wingosolar WGS-M10/78BH (×5) | 308° NW | 3° | 2 900 Wc |
| DEYE | Off-grid | PV3 | Wingosolar WGS-M10/78BH (×5) | 27° NNE | 3° | 2 900 Wc |
| ATON | Grid-tie | PV1 | JA Solar S17-325/MR (×7) | 256° WSW | 3° | 2 275 Wc |
| ATON | Grid-tie | PV2 | JA Solar S17-325/MR (×12) | 283° WNW | 3° | 3 900 Wc |
| **Total** | | | **36 panneaux** | | | **16 035 Wc** |

## Caractéristiques techniques

- **Home Assistant OS** 18.1 (VM100 sur Proxmox)
- **Localisation** : La Possession, La Réunion (-20.9295, 55.3520)
- **Timezone** : Indian/Reunion (UTC+4)
- **Climat** : Tropical, ensoleillement élevé, formations nuageuses convectives
  l'après-midi, saison cyclonique (nov.–avr.)

## Licence

Projet personnel — usage privé.

---

**Auteur :** Victor, expert technique — équipe IA de Valérie
**Architecture :** v3 — 30 juillet 2026

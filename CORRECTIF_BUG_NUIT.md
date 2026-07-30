# Correctif Bug Nuit - PV Potential Forecast

## Problème identifié

**Date** : 30 juillet 2026, 19:20 heure locale La Réunion  
**Bug critique** : Les capteurs PV Potential Forecast affichaient une production potentielle alors qu'il faisait nuit.

### Valeurs erronées affichées
- ATON Estimated Power: **770 W**
- DEYE MPPT1: **629 W**, MPPT2: **435 W**, MPPT3: **443 W**
- DEYE Total: **1 507 W**
- PV Total: **2 277 W**

**Attendu** : 0 W pour tous les capteurs de puissance instantanée la nuit.

## Cause racine

Le commit `950c104` avait tenté d'ajouter un filtre jour/nuit mais contenait **deux erreurs** :

1. **Boucle `for` dupliquée** dans `compute_forecast()` (ligne 558) créant une corruption syntaxique
2. **Filtre incomplet** : `get_potential_power()` avait le filtre mais pas `compute_forecast()`

Le code ne vérifiait pas si le soleil était couché avant de calculer et afficher les puissances.

## Solution implémentée

### 1. Restauration depuis commit propre
- Restauré `single_source_strategy.py` depuis le commit `4dec7e6` (version avant le filtre corrompu)

### 2. Ajout filtre jour/nuit correct

**Dans `compute_forecast()` (ligne 552)** :
```python
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
```

**Dans `get_potential_power()` (ligne 351)** :
```python
# Vérification astronomique : forcer 0 W la nuit
now = datetime.now(timezone.utc)
if is_night(now, DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE):
    return 0.0
```

### 3. Imports ajoutés
```python
from ..astronomy import is_night
from ..const import DEFAULT_LATITUDE, DEFAULT_LONGITUDE, DEFAULT_TIMEZONE
```

## Tests de validation

### Heures astronomiques (30 juillet 2026, La Réunion)
- **Lever du soleil** : 06:50 heure locale (02:50 UTC)
- **Coucher du soleil** : 17:59 heure locale (13:59 UTC)

### Résultats tests
```
Test 1 : 19:20 La Réunion (nuit)
  Heure UTC: 15:20
  is_night() = True ✅
  → Capteurs afficheront 0 W

Test 2 : 12:00 La Réunion (jour)
  Heure UTC: 08:00
  is_night() = False ✅
  → Capteurs afficheront les valeurs calculées
```

## Fichiers modifiés

- `custom_components/pv_potential_forecast/strategies/single_source_strategy.py`
  - Ligne 31 : Import `is_night`
  - Ligne 44-46 : Import constantes GPS/timezone
  - Ligne 351-354 : Filtre nuit dans `get_potential_power()`
  - Ligne 552-569 : Filtre nuit dans `compute_forecast()`

## Commit et déploiement

**Commit** : `78d116f`  
**Message** : "fix: filtre jour/nuit corrigé - forcer 0 W après coucher du soleil"

**Push** : ✅ Réussi sur `origin/main`

## Comportement attendu après correctif

### Capteurs de puissance instantanée (W)
- **Jour (06:50 - 17:59)** : Affichent les valeurs calculées avec corrections (température, bifacial, onduleur)
- **Nuit (17:59 - 06:50)** : Affichent **0 W**

### Capteurs d'énergie quotidienne (kWh)
- **PV Potential Today** : Non affecté par le filtre nuit
- **PV Potential Tomorrow** : Non affecté par le filtre nuit

## Vérification post-déploiement

À 19:20 heure locale La Réunion, vérifier que :
- [ ] ATON Estimated Power = 0 W
- [ ] DEYE MPPT1 = 0 W
- [ ] DEYE MPPT2 = 0 W
- [ ] DEYE MPPT3 = 0 W
- [ ] DEYE Total = 0 W
- [ ] PV Total = 0 W

À 12:00 heure locale La Réunion, vérifier que :
- [ ] Les capteurs affichent des valeurs cohérentes (> 0 W)
- [ ] Les corrections (température, bifacial) sont appliquées

---

**Auteur** : Victor, expert technique  
**Date** : 30 juillet 2026  
**Statut** : ✅ Corrigé et déployé

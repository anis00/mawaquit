# Mawaquit - Contexte du Projet pour Claude

Ce fichier contient les informations essentielles pour reprendre le travail sur le projet Mawaquit.

## Description du projet

**Mawaquit** est une application Python de calcul des heures de prière islamiques avec :
- Visualisation cartographique interactive (Tkinter + Matplotlib + GeoPandas)
- Courbes isochrones montrant les zones de même heure de prière
- Support de 40+ pays avec données GADM

## Structure des fichiers

| Fichier | Description |
|---------|-------------|
| `mawaquit_main.py` | Application principale (UI Tkinter, carte, interactions) |
| `praytimes.py` | Calcul des heures de prière (algorithmes astronomiques) |
| `isochrones.py` | Génération des courbes isochrones (3 classes disponibles) |
| `inverse_isochrone.py` | Ancien module de calcul inverse (obsolète) |
| `note_calcul_isochrones.html` | Documentation mathématique détaillée |
| `README.md` | Documentation utilisateur |

## Classes principales dans isochrones.py

1. **IsochroneGenerator** : Approche par grille (ancienne, lente)
2. **IsochroneGeneratorDirect** : Approche analytique lon=f(lat) - **RECOMMANDÉE**
3. **IsochroneGeneratorBands** : Bandes colorées au lieu de lignes

## Formules clés

### Calcul direct (position -> heure)
```
T = T_noon ± (1/15) × arccos[(-sin(α) - sin(δ) × sin(φ)) / (cos(δ) × cos(φ))]
```

### Calcul inverse (heure -> longitude) - Approche actuelle
```
λ = 15 × (12 - EqT + TZ_pays - T_cible) ± H
```
Où H = angle horaire calculé pour la latitude φ

## Historique des versions

### v2.1.0 (Février 2025)
- **Fuseau horaire fixe par pays** : Résolution du problème de saut d'1h aux longitudes frontières (±7.5°, ±22.5°, etc.)
- Dictionnaire `pays_timezones` dans `mawaquit_main.py`
- Paramètre `country_timezone` passé à `tracer_isochrones()`

### v2.0.0 (Janvier 2025)
- Nouvelle approche analytique `lon = f(lat)` au lieu de `lat = f(lon)`
- Bandes colorées avec `IsochroneGeneratorBands`
- Correction de la précision (±1-2 minutes corrigées par itération sur JD)
- Gestion des pays multi-fuseaux (segments séparés)

## Variables d'état importantes (mawaquit_main.py)

```python
self.current_timezone      # Fuseau horaire du pays actuel
self.current_country_name  # Nom du pays actuel
self.current_gdf           # GeoDataFrame de la carte
self.selected_date         # Date sélectionnée
self.pray_calc             # Instance de PrayTimes
self.isochrone_gen         # Instance de IsochroneGeneratorBands
```

## Dictionnaire des fuseaux horaires

Le dictionnaire `pays_timezones` dans `mawaquit_main.py` contient :
- France: 1 (CET)
- Tunisia: 1
- Morocco: 0 ou 1
- Saudi Arabia: 3
- USA: varie (-5 à -10, multi-fuseaux)
- etc.

## Points d'attention

1. **Asr** : L'angle dépend de la latitude → calcul spécifique
2. **Dhuhr** : Indépendant de la latitude → isochrones verticales
3. **Hautes latitudes** (> 60°) : Comportement non garanti
4. **DST** : Non géré automatiquement

## Dépendances

```
geopandas
matplotlib
numpy
tkinter (standard library)
```

## Commande de lancement

```bash
python mawaquit_main.py
```

## Tests à effectuer après modifications

1. Charger différents pays (France, Tunisie, USA)
2. Tracer les isochrones pour chaque prière
3. Cliquer sur la carte et vérifier que l'heure affichée correspond à la bande
4. Tester aux longitudes frontières (7.5°, 22.5°) pour vérifier l'absence de saut

## Problèmes résolus

- [x] Calcul trop lent → Approche analytique
- [x] Courbes incorrectes croisées → Segments par fuseau
- [x] Précision ±2 minutes → Itération sur JD
- [x] Sauts d'1h aux frontières de TZ → Fuseau fixe par pays

## Améliorations potentielles

- [ ] Gestion DST automatique (pytz/timezonefinder)
- [ ] Support altitudes (ajustement angle horizon)
- [ ] Multithreading pour les calculs
- [ ] Export PDF calendrier mensuel

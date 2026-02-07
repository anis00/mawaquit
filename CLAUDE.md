# Mawaquit - Contexte du Projet pour Claude

Ce fichier contient les informations essentielles pour reprendre le travail sur le projet Mawaquit.

## Description du projet

**Mawaquit** est une application de calcul des heures de prière islamiques avec visualisation cartographique et courbes isochrones. Le projet existe en deux versions :

1. **Version Desktop** (Python/Tkinter) - Application native
2. **Version Web** (HTML/JS/Leaflet) - Application web statique

## Structure du projet

```
mawaquit/
├── mawaquit_main.py       # Application desktop (Tkinter)
├── praytimes.py           # Calcul heures de prière (Python)
├── isochrones.py          # Génération isochrones (Python)
├── requirements.txt       # Dépendances Python
├── scripts/
│   └── download_gadm.py   # Script téléchargement données GADM
└── web/                   # Version web
    ├── index.html
    ├── css/custom.css
    ├── js/
    │   ├── app.js             # Orchestration
    │   ├── praytimes.js       # Port de praytimes.py
    │   ├── isochrones.js      # Interface isochrones
    │   ├── isochrones.worker.js  # Web Worker calculs
    │   ├── map.js             # Gestion Leaflet
    │   ├── ui.js              # Interface utilisateur
    │   ├── data.js            # Chargement données
    │   └── utils.js           # Utilitaires
    └── data/
        ├── countries.json     # Métadonnées 33 pays
        └── gadm/              # Données géographiques simplifiées (16 MB)
```

## Version Web

### URL de production
https://anis00.github.io/mawaquit/

### Technologies utilisées
- **Leaflet.js** - Carte interactive
- **Tailwind CSS** - Styles (via CDN)
- **Web Workers** - Calculs isochrones non-bloquants
- **Données GADM** - Frontières simplifiées (hébergées localement)

### Fonctionnalités
- 33 pays avec données géographiques pré-chargées
- 7 méthodes de calcul (MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari)
- Isochrones avec 2 nuances de bleu alternées
- Étiquettes toujours visibles

### Déploiement GitHub Pages
```bash
git subtree push --prefix web origin gh-pages
```

## Version Desktop (Python)

### Installation
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python mawaquit_main.py
```

### Dépendances
- geopandas >= 1.0.0
- matplotlib >= 3.8.0
- numpy >= 2.0.0
- shapely >= 2.0.0
- tkinter (standard library)

## Formules clés

### Calcul direct (position → heure)
```
T = T_noon ± (1/15) × arccos[(-sin(α) - sin(δ) × sin(φ)) / (cos(δ) × cos(φ))]
```

### Calcul inverse (heure → longitude)
```
λ = 15 × (12 - EqT + TZ_pays - T_cible) ± H
```
Où H = angle horaire calculé pour la latitude φ

## Classes isochrones (Python)

1. **IsochroneGenerator** : Approche par grille (ancienne, lente)
2. **IsochroneGeneratorDirect** : Approche analytique lon=f(lat)
3. **IsochroneGeneratorBands** : Bandes colorées - **UTILISÉE**

## Historique des versions

### v3.0.0 (Février 2025)
- **Version Web** : Migration vers HTML/JS/Leaflet
- Données GADM simplifiées et hébergées localement (16 MB)
- Chargement instantané sans proxy CORS
- Isochrones avec couleurs alternées

### v2.1.0 (Février 2025)
- Fuseau horaire fixe par pays
- Dictionnaire `pays_timezones`

### v2.0.0 (Janvier 2025)
- Approche analytique `lon = f(lat)`
- Bandes colorées avec `IsochroneGeneratorBands`
- Précision ±1-2 minutes

## Tests à effectuer

### Version Web
1. Ouvrir https://anis00.github.io/mawaquit/
2. Sélectionner un pays (France, Tunisie, USA)
3. Cliquer sur la carte → heures de prière affichées
4. Cliquer sur un bouton isochrone → bandes colorées
5. Vérifier que les étiquettes restent visibles

### Version Desktop
1. `python mawaquit_main.py`
2. Charger différents pays
3. Tracer les isochrones pour chaque prière
4. Vérifier la correspondance heure affichée / bande

## Points d'attention

1. **Asr** : L'angle dépend de la latitude → calcul spécifique
2. **Dhuhr** : Indépendant de la latitude → isochrones verticales
3. **Hautes latitudes** (> 60°) : Comportement non garanti
4. **DST** : Non géré automatiquement

## Problèmes résolus

- [x] Calcul trop lent → Approche analytique
- [x] Précision ±2 minutes → Itération sur JD
- [x] Sauts d'1h aux frontières TZ → Fuseau fixe par pays
- [x] CORS avec GADM → Données locales simplifiées
- [x] Chargement lent web → Fichiers GeoJSON optimisés

## Améliorations potentielles

- [ ] Gestion DST automatique
- [ ] Support altitudes
- [ ] Export PDF calendrier mensuel
- [ ] PWA (Progressive Web App)

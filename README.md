# Mawaquit 🕌

**Application de calcul des heures de prière islamiques avec visualisation cartographique et courbes isochrones**

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

![Capture](https://github.com/anis00/mawaquit/blob/master/Capture%20d%E2%80%99%C3%A9cran%202026-01-13%20113027.png)

---

## 📋 Table des matières

- [Description](#-description)
- [Fonctionnalités](#-fonctionnalités)
- [Installation](#-installation)
- [Structure du projet](#-structure-du-projet)
- [Utilisation](#-utilisation)
- [Méthodes de calcul](#-méthodes-de-calcul)
- [Documentation mathématique](#-documentation-mathématique)
- [Données géographiques](#-données-géographiques)
- [Architecture technique](#-architecture-technique)
- [Limitations connues](#-limitations-connues)
- [Améliorations futures](#-améliorations-futures)
- [Contributions](#-contributions)
- [Licence](#-licence)
- [Références](#-références)

---

## 📖 Description

**Mawaquit** (مواقيت - "les horaires" en arabe) est une application desktop Python permettant de :

1. **Calculer** les heures de prière islamiques pour n'importe quel point géographique
2. **Visualiser** ces heures sur une carte administrative interactive
3. **Tracer** des courbes isochrones montrant la variation géographique des heures de prière

### Cas d'usage principal

Un utilisateur sélectionne un pays, clique sur la carte pour placer un marqueur, et obtient instantanément les heures de prière pour ce point. Il peut ensuite visualiser les courbes isochrones qui montrent comment une heure de prière spécifique varie géographiquement à travers le pays (zones où la prière est à la même heure minute par minute).

---

## ✨ Fonctionnalités

### 🗺️ Cartographie interactive

- **3 niveaux administratifs** : Frontières nationales (niveau 0), régions/provinces (niveau 1), subdivisions fines (niveau 2 - optionnel)
- **40+ pays disponibles** : France, Tunisie, Maroc, Algérie, Arabie Saoudite, USA, Canada, etc.
- **Navigation complète** : Zoom molette, pan, zoom rectangle, navigation historique
- **Limitation du zoom** : Zoom maximum limité pour éviter les imprécisions visuelles

### 🕌 Calcul des heures de prière

- **6 prières calculées** : Fajr, Sunrise, Dhuhr, Asr, Maghrib, Isha
- **7 méthodes de calcul** : MWL, ISNA, Egypt, Makkah, Karachi, Tehran, Jafari
- **Sélection de date** : Calendrier intégré avec raccourcis (+7j, -7j, aujourd'hui)
- **Marqueur déplaçable** : Cliquez n'importe où pour calculer les heures

### 📊 Courbes isochrones

- **5 prières** : Fajr, Dhuhr, Asr, Maghrib, Isha
- **Courbes lisses** : Une courbe par minute (60 niveaux/heure)
- **Haute précision** : Grille de calcul 100×100 points avec timezone exact
- **Étiquettes intelligentes** : Format hh:mm toutes les 5 minutes, limitées aux frontières du pays
- **Titre dynamique** : Affiche "[Pays] - Courbes isochrones de [Prière]"
- **Effacement** : Bouton pour nettoyer la carte et restaurer le titre

### 🏙️ Affichage des villes

- **Source de données** : Natural Earth Data (fichier local)
- **Filtrage automatique** : Affichage des villes du pays sélectionné
- **Noms complets** : Toutes les villes affichées avec leurs noms
- **Activation/désactivation** : Checkbox pour gérer l'affichage

---

## 🚀 Installation

### Prérequis

- **Python 3.8+** (recommandé : Python 3.10)
- **Connexion Internet** : Pour le premier téléchargement des données GADM
- **Espace disque** : ~500 MB pour le cache des cartes

### Étapes d'installation

1. **Cloner ou télécharger le projet**

```bash
git clone https://github.com/anis00/mawaquit.git
cd mawaquit
```

2. **Créer un environnement virtuel (recommandé)**

```bash
# Sous Windows
python -m venv venv
venv\Scripts\activate

# Sous Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

3. **Installer les dépendances**

```bash
pip install geopandas matplotlib numpy
```

**Détail des bibliothèques :**
- `geopandas` : Manipulation de données géospatiales
- `matplotlib` : Visualisation et création de graphiques
- `numpy` : Calculs numériques
- `tkinter` : Interface graphique (inclus avec Python)

4. **Télécharger les données de villes (optionnel)**

Téléchargez le fichier `populated_places.geojson` depuis [Natural Earth Data](https://www.naturalearthdata.com/downloads/10m-cultural-vectors/) et placez-le dans le même répertoire que `mawaquit_main.py`.

**Lien direct** : [ne_10m_populated_places_simple](https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_populated_places_simple.zip)

Extraire le fichier et le convertir en GeoJSON si nécessaire.

5. **Lancer l'application**

```bash
python mawaquit_main.py
```

---

## 📁 Structure du projet

```
mawaquit/
│
├── mawaquit_main.py              # Application principale (interface + logique)
├── praytimes.py                  # Module de calcul des heures de prière
├── isochrones.py                 # Module de traçage des courbes isochrones
├── inverse_isochrone.py          # Module de calcul inverse (expérimental)
├── note_calcul_isochrones.html   # Documentation mathématique détaillée
├── populated_places.geojson      # Données des villes (optionnel)
├── README.md                     # Cette documentation
│
└── /tmp/gadm_cache/              # Cache automatique (créé à l'exécution)
    ├── gadm41_FRA_0.json
    ├── gadm41_FRA_1.json
    ├── gadm41_TUN_0.json
    └── ...
```

### Description des fichiers

| Fichier | Description | Taille |
|---------|-------------|--------|
| `mawaquit_main.py` | Interface Tkinter + gestion carte + interactions | ~450 lignes |
| `praytimes.py` | Classe PrayTimes avec algorithmes astronomiques | ~390 lignes |
| `isochrones.py` | Générateur de courbes isochrones (3 approches : grille, exact, **analytique**) | ~550 lignes |
| `inverse_isochrone.py` | Calcul inverse φ=f(λ) - obsolète, remplacé par approche λ=f(φ) | ~400 lignes |
| `note_calcul_isochrones.html` | Note de calcul mathématique détaillée (v2.0) | ~50 KB |
| `populated_places.geojson` | Base de données villes Natural Earth | ~50 MB |

---

## 🎯 Utilisation

### Démarrage rapide

1. **Lancer l'application**
   ```bash
   python mawaquit_main.py
   ```

2. **Sélectionner un pays**
   - Choisir dans la liste déroulante (ex: "France", "Tunisia")
   - Cliquer sur "Afficher Carte"

3. **Placer le marqueur**
   - Cliquer n'importe où sur la carte
   - Les heures de prière s'affichent automatiquement

4. **Tracer les isochrones**
   - Cliquer sur un bouton de prière (Fajr, Dhuhr, etc.)
   - Les courbes apparaissent en violet

### Interface détaillée

#### Barre de contrôles (ligne 1)

- **Pays** : Liste déroulante des pays disponibles
- **Afficher Carte** : Charge la carte du pays sélectionné
- **Méthode** : Choix de la méthode de calcul (MWL par défaut)
- **Status** : Messages d'information (chargement, erreurs, succès)

#### Barre de contrôles (ligne 2)

- **Date** : Champ de saisie au format JJ/MM/AAAA
- **📅** : Ouvre le sélecteur de date
- **Aujourd'hui** : Réinitialise à la date du jour
- **Afficher niveau 3** : Active les subdivisions administratives fines
- **Afficher villes** : Active l'affichage des villes

#### Panneau droit

**Heures de Prière**
- Position GPS (latitude/longitude)
- Date sélectionnée
- 6 heures de prière formatées (hh:mm)

**Courbes Isochrones**
- 5 boutons pour tracer les courbes
- Bouton "Effacer Courbes"

**Instructions**
- Guide d'utilisation rapide

### Navigation sur la carte

| Action | Effet |
|--------|-------|
| **Molette haut** | Zoom avant |
| **Molette bas** | Zoom arrière |
| **Clic + glisser** (outil Pan) | Déplacer la carte |
| **Clic rectangle** (outil Zoom) | Zoomer sur une zone |
| **🏠 Home** | Retour à la vue initiale |
| **← →** | Naviguer dans l'historique |
| **💾 Sauvegarder** | Exporter en image PNG |

### Raccourcis clavier (sélecteur de date)

- **Aujourd'hui** : Réinitialise à la date actuelle
- **-7j** : Recule de 7 jours
- **+7j** : Avance de 7 jours

---

## 📐 Méthodes de calcul

Mawaquit supporte 7 méthodes internationales de calcul des heures de prière :

| Code | Organisation | Angle Fajr | Angle Isha | Régions |
|------|--------------|------------|------------|---------|
| **MWL** | Muslim World League | 18° | 17° | Europe, Amérique |
| **ISNA** | Islamic Society of North America | 15° | 15° | Amérique du Nord |
| **Egypt** | Egyptian General Authority | 19.5° | 17.5° | Afrique, Moyen-Orient |
| **Makkah** | Umm Al-Qura, Makkah | 18.5° | 90 min après Maghrib | Arabie Saoudite |
| **Karachi** | University of Islamic Sciences | 18° | 18° | Pakistan, Bangladesh |
| **Tehran** | Institute of Geophysics | 17.7° | 14° | Iran, certaines régions chiites |
| **Jafari** | Shia Ithna-Ashari | 16° | 14° | Communautés chiites |

### Comment choisir ?

- **Recommandation générale** : MWL (défaut)
- **Amérique du Nord** : ISNA
- **Égypte et Proche-Orient** : Egypt
- **Arabie Saoudite** : Makkah
- **Pakistan/Bangladesh** : Karachi
- **Communautés chiites** : Jafari ou Tehran

---

## 📐 Documentation mathématique

Une documentation mathématique complète est disponible dans le fichier **`note_calcul_isochrones.html`**.

### Contenu de la documentation

1. **Paramètres astronomiques**
   - Calcul du jour julien
   - Position du soleil (déclinaison, équation du temps)
   - Midi solaire

2. **Calcul direct des heures de prière**
   - Formule générale avec démonstration
   - Tableau des angles par prière
   - Conditions d'existence aux hautes latitudes

3. **Calcul inverse pour les isochrones**
   - Dérivation mathématique complète
   - Transformation en équation linéaire trigonométrique
   - Résolution analytique

4. **Cas particulier de l'Asr**
   - Dépendance de l'angle avec la latitude
   - Propriété de non-monotonicité
   - Algorithme de résolution numérique

5. **Exemples numériques**
   - Calcul direct pour Paris
   - Calcul inverse détaillé
   - Vérification croisée

6. **Analyse de précision**
   - Sources d'erreur identifiées
   - Recommandations

### Formule principale

**Calcul direct** :
```
T = T_noon ± (1/15) × arccos[(-sin(α) - sin(δ) × sin(φ)) / (cos(δ) × cos(φ))]
```

**Calcul inverse** (pour une heure cible) :
```
A × cos(φ) + B × sin(φ) = C

Où :
- A = cos(δ) × cos(H)
- B = sin(δ)
- C = -sin(α)
- H = ±15 × (T_cible - T_noon)

Solution : φ = arctan2(B, A) ± arccos(C / √(A² + B²))
```

### Visualisation

Pour ouvrir la documentation, double-cliquez sur `note_calcul_isochrones.html` ou ouvrez-le dans un navigateur web. Les formules mathématiques sont rendues avec MathJax.

---

## 🌍 Données géographiques

### Source GADM 4.1

**GADM** (Global Administrative Areas) fournit les frontières administratives mondiales.

- **Site officiel** : [https://gadm.org/](https://gadm.org/)
- **Version utilisée** : 4.1
- **Format** : GeoJSON
- **Licence** : Libre pour usage académique et personnel

#### Niveaux disponibles

- **Niveau 0** : Frontières nationales
- **Niveau 1** : Régions, provinces, états
- **Niveau 2** : Départements, comtés, districts (optionnel)

#### URL pattern

```
https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_{CODE_PAYS}_{NIVEAU}.json
```

**Exemple** : 
- France niveau 0 : `gadm41_FRA_0.json`
- Tunisie niveau 1 : `gadm41_TUN_1.json`

### Source Natural Earth Data

**Natural Earth** fournit les données culturelles et physiques mondiales.

- **Site officiel** : [https://www.naturalearthdata.com/](https://www.naturalearthdata.com/)
- **Dataset utilisé** : Populated Places (10m)
- **Format** : GeoJSON (converti depuis Shapefile)
- **Contenu** : ~7500 villes mondiales

#### Structure de `populated_places.geojson`

```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "name": "Paris",
        "adm0_a3": "FRA",
        "adm0name": "France",
        "pop_max": 2138551,
        "latitude": 48.8566,
        "longitude": 2.3522
      },
      "geometry": {
        "type": "Point",
        "coordinates": [2.3522, 48.8566]
      }
    }
  ]
}
```

### Cache local

Les fichiers GADM sont automatiquement téléchargés et mis en cache :

**Emplacement** :
- **Windows** : `C:\Users\{USER}\AppData\Local\Temp\gadm_cache\`
- **Linux/Mac** : `/tmp/gadm_cache/`

**Avantages** :
- Chargement instantané après la première fois
- Pas de re-téléchargement à chaque lancement
- Économise la bande passante

**Inconvénient** :
- Pas de mise à jour automatique si GADM est mis à jour
- Peut accumuler de l'espace disque (5-50 MB par pays)

---

## 🏗️ Architecture technique

### Technologies utilisées

- **Langage** : Python 3.8+
- **Interface graphique** : Tkinter (standard library)
- **Cartographie** : GeoPandas + Matplotlib
- **Calculs astronomiques** : PrayTimes (implémentation Python)
- **Calculs numériques** : NumPy

### Structure modulaire

```
┌─────────────────────────────────────────┐
│         mawaquit_main.py                │
│  ┌────────────┐  ┌──────────────────┐   │
│  │   Tkinter  │  │   Matplotlib     │   │
│  │     UI     │  │   Canvas + Map   │   │
│  └────────────┘  └──────────────────┘   │
│         │                │               │
│         └────────┬───────┘               │
│                  │                       │
└──────────────────┼───────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
┌───────▼────────┐   ┌────────▼─────────┐
│  praytimes.py  │   │  isochrones.py   │
│                │   │                  │
│  - PrayTimes   │   │  - Generator     │
│  - getTimes()  │   │  - tracer()      │
│  - Algorithms  │   │  - clear()       │
└────────────────┘   └──────────────────┘
```

### Classe PrayTimes

**Responsabilités** :
- Calculs astronomiques (position du soleil, équation du temps)
- Conversion de dates (calendrier julien)
- Gestion des différentes méthodes de calcul
- Ajustement pour les hautes latitudes

**Méthodes principales** :
```python
getTimes(date, coords, timezone, format='24h')
# → dict: {'fajr': '05:30', 'sunrise': '06:45', ...}
```

### Classes de génération d'isochrones

**Trois classes disponibles** :

| Classe | Approche | Performance | Précision |
|--------|----------|-------------|-----------|
| `IsochroneGenerator` | Grille 60×60 + contour | Moyenne | Moyenne |
| `IsochroneGeneratorExact` | Grille 100×100 + contour | Lente | Bonne |
| `IsochroneGeneratorDirect` | **Calcul analytique λ=f(φ)** | **Rapide** | **Exacte** |

**Classe recommandée : `IsochroneGeneratorDirect`** (utilisée par défaut)

**Principe de l'approche analytique** :
- Pour chaque heure cible T et latitude φ, calcule directement la longitude λ
- Formule : `λ = 15 × (12 - EqT + TZ - T) ± H`
- Où H = arccos[(-sin(α) - sin(δ)×sin(φ)) / (cos(δ)×cos(φ))]

**Avantages** :
- Calcul direct sans itération ni bisection
- Une seule solution par latitude (pas d'ambiguïté)
- Gestion des pays multi-fuseaux horaires (segments séparés)
- ~200 calculs par courbe au lieu de 10 000 points de grille

### Classe MawaquitApp

**Responsabilités** :
- Interface utilisateur Tkinter
- Gestion de la carte (chargement, affichage, navigation)
- Gestion du marqueur et des interactions
- Coordination entre les modules

---

## 🐛 Limitations connues

### 1. ~~Précision des isochrones~~ (RÉSOLU v2.0)

**Statut** : ✅ Résolu avec la nouvelle approche analytique `IsochroneGeneratorDirect`

L'ancienne approche par grille causait des imprécisions dues à l'interpolation. La nouvelle approche calcule les courbes exactes analytiquement.

### 2. ~~Performance pour grands pays~~ (RÉSOLU v2.0)

**Statut** : ✅ Résolu avec la nouvelle approche analytique

**Temps de calcul avec `IsochroneGeneratorDirect`** :
- Tous les pays : < 1 seconde

L'ancienne approche par grille nécessitait 10 000 calculs. La nouvelle approche n'en nécessite que ~200 par courbe.

### 3. Latitudes extrêmes (Priorité : Faible)

**Description** : Comportement non testé pour les régions polaires (> 60° N/S).

**Problème théorique** :
- Nuits/jours continus en été/hiver
- Algorithmes standards peuvent retourner NaN
- Méthode `highLats` appliquée mais non vérifiée

**Pays concernés** : Groenland, nord Scandinavie, Antarctique

### 4. Absence de gestion DST (Priorité : Moyenne)

**Description** : L'heure d'été (Daylight Saving Time) n'est pas détectée automatiquement.

**Impact** : Les heures affichées peuvent être décalées d'1h durant les périodes DST

**Solution temporaire** : L'utilisateur doit manuellement ajuster

### 5. Cache non nettoyé (Priorité : Faible)

**Description** : Les fichiers GADM restent indéfiniment dans `/tmp/gadm_cache/`

**Impact** : Accumulation de fichiers (5-50 MB chacun)

**Risque** : Remplissage du disque à très long terme

### 6. Affichage dense des villes (Priorité : Moyenne)

**Description** : Pour les grands pays, afficher toutes les villes peut surcharger la carte.

**Impact** : Lisibilité réduite, nombreux labels superposés

**Workaround** : Désactiver l'affichage des villes si trop dense

---

## 🚀 Améliorations futures

### Priorité HAUTE

#### 1. Amélioration de la précision des isochrones

**Solutions implémentées** :
- ✓ Augmenter la résolution (100×100)
- ✓ Implémenter un timezone exact par point
- ✓ Calcul inverse exact (module `inverse_isochrone.py`)
- ✓ Étiquettes limitées aux frontières du pays
- ✓ Titre dynamique avec nom du pays et de la prière
- ✓ Documentation mathématique complète

**Solutions à explorer** :
- ◯ Algorithme de bissection pour courbes exactes
- ◯ Pré-calcul et stockage des grilles fréquentes

**Approche mathématique documentée** : Voir `note_calcul_isochrones.html` pour les formules détaillées du calcul inverse.

#### 2. Multithreading pour les calculs

**Objectif** : Ne pas figer l'interface pendant le calcul des isochrones

**Implémentation** :
```python
import threading

def calcul_async():
    thread = threading.Thread(target=self.tracer_isochrones, args=(prayer_name,))
    thread.start()
```

### Priorité MOYENNE

#### 3. Fonctionnalités additionnelles

- ◯ **Sélection d'heure** : Calculer pour une heure précise
- ◯ **Qibla** : Afficher la direction de la Mecque
- ◯ **Export PDF** : Générer un calendrier mensuel
- ◯ **Comparaison de méthodes** : Afficher plusieurs méthodes côte à côte
- ◯ **Alertes** : Notification sonore avant les prières
- ◯ **Multilangue** : Support arabe/anglais

#### 4. Gestion intelligente des villes

- ◯ Slider pour ajuster le nombre de villes affichées
- ◯ Filtrage par population (seuil ajustable)
- ◯ Zoom adaptatif (plus de villes quand on zoome)
- ◯ Clustering pour éviter la superposition

### Priorité FAIBLE

#### 5. Performance et UX

- ◯ Barre de progression pour les calculs longs
- ◯ Zoom intelligent (résolution adaptative)
- ◯ Interpolation adaptative (plus de points où nécessaire)
- ◯ Légende interactive (afficher/masquer certaines courbes)
- ◯ Paramètres utilisateur sauvegardés

#### 6. Données et précision

- ◯ Altitude prise en compte (actuellement fixé à 0)
- ◯ DST automatique avec bibliothèque pytz
- ◯ Timezone exact avec timezonefinder
- ◯ Support de shapefiles personnalisés
- ◯ Niveau 3 GADM pour plus de détails

#### 7. Tests et validation

- ◯ Tests unitaires avec pytest
- ◯ Comparaison avec sources officielles
- ◯ Validation sur latitudes extrêmes
- ◯ Documentation complète (docstrings)

---

## 🤝 Contributions

Les contributions sont les bienvenues ! Voici comment contribuer :

### Signaler un bug

1. Vérifier que le bug n'est pas déjà dans les [Limitations connues](#-limitations-connues)
2. Ouvrir une issue avec :
   - Description du problème
   - Étapes pour reproduire
   - Version de Python
   - Système d'exploitation
   - Logs d'erreur (si disponibles)

### Proposer une fonctionnalité

1. Vérifier que ce n'est pas dans [Améliorations futures](#-améliorations-futures)
2. Ouvrir une issue "Feature Request" avec :
   - Description de la fonctionnalité
   - Cas d'usage
   - Mockups/schémas (si applicable)

### Soumettre du code

1. Fork le projet
2. Créer une branche (`git checkout -b feature/AmazingFeature`)
3. Commiter les changements (`git commit -m 'Add AmazingFeature'`)
4. Push vers la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

### Guidelines de code

- **Style** : PEP 8
- **Docstrings** : Format Google/NumPy
- **Tests** : Ajouter des tests pour les nouvelles fonctionnalités
- **Documentation** : Mettre à jour le README si nécessaire

---

## 📄 Licence

Ce projet est sous licence **MIT**.

```
MIT License

Copyright (c) 2025 Mawaquit Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 📚 Références

### Calcul des heures de prière

- **Documentation officielle** : [PrayTimes.org - Calculation](https://praytimes.org/docs/calculation)
- **Équations détaillées** : [Prayer Times Calculation Wiki](https://praytimes.org/wiki/Prayer_Times_Calculation)
- **Implémentation JavaScript** : [zarrabi/praytime](https://github.com/zarrabi/praytime)

### Astronomie

- **Position du soleil** : Jean Meeus, "Astronomical Algorithms" (2nd Edition)
- **Équation du temps** : [Wikipedia - Equation of time](https://en.wikipedia.org/wiki/Equation_of_time)
- **Déclinaison solaire** : [NOAA Solar Calculator](https://www.esrl.noaa.gov/gmd/grad/solcalc/)

### Données géographiques

- **GADM** : [Global Administrative Areas](https://gadm.org/)
- **Natural Earth** : [Natural Earth Data](https://www.naturalearthdata.com/)
- **GeoJSON Specification** : [RFC 7946](https://tools.ietf.org/html/rfc7946)

### Bibliothèques Python

- **GeoPandas** : [Documentation](https://geopandas.org/)
- **Matplotlib** : [Documentation](https://matplotlib.org/)
- **NumPy** : [Documentation](https://numpy.org/)
- **Tkinter** : [Python Docs](https://docs.python.org/3/library/tkinter.html)

---

## 📞 Contact & Support

- **Email** : [anis.7armel@gmail.com]
- **Issues** : [GitHub Issues](https://github.com/anis00/mawaquit/issues)
- **Discussions** : [GitHub Discussions](https://github.com/anis00/mawaquit/discussions)

---

## 🙏 Remerciements

- **PrayTimes.org** pour les algorithmes de calcul
- **GADM** pour les données administratives mondiales
- **Natural Earth** pour les données culturelles et physiques
- **Communauté GeoPandas** pour l'excellente bibliothèque
- **Tous les contributeurs** qui ont aidé à améliorer ce projet

---

## 📊 Statistiques du projet

- **Lignes de code** : ~1800 lignes Python
- **Modules** : 4 fichiers principaux + documentation
- **Pays supportés** : 35+ (extensible facilement)
- **Méthodes de calcul** : 7 méthodes internationales
- **Approche isochrones** : Calcul analytique direct λ=f(φ) (~200 points/courbe)
- **Performance** : < 1 seconde pour tous les pays

---

**Fait avec ❤️ pour la communauté musulmane**

*"Et Nous avons fait de la nuit et du jour deux signes, puis Nous avons effacé le signe de la nuit, tandis que Nous avons rendu visible le signe du jour, pour que vous recherchiez les grâces de votre Seigneur, et que vous sachiez le nombre des années et le calcul du temps."* (Coran 17:12)

---

**Dernière mise à jour** : Janvier 2025
**Version** : 2.0.0

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module de traçage des courbes isochrones pour Mawaquit
Génère des courbes montrant les zones géographiques où une prière
a lieu à la même heure

Trois approches disponibles :
- IsochroneGenerator : Approche par grille (60×60)
- IsochroneGeneratorExact : Approche par grille haute résolution (100×100)
- IsochroneGeneratorDirect : Approche analytique lon = f(lat) - recommandée
"""

import numpy as np
import math


class IsochroneGenerator:
    """Classe pour générer et tracer les courbes isochrones"""

    def __init__(self, pray_calc, ax):
        """
        Initialise le générateur d'isochrones

        Args:
            pray_calc: Instance de PrayTimes pour les calculs
            ax: Axes matplotlib pour le dessin
        """
        self.pray_calc = pray_calc
        self.ax = ax
        self.isochrone_lines = []
        self.current_prayer = None
        self.current_country = None

    def tracer_isochrones(self, prayer_name, gdf, selected_date, country_name=None):
        """
        Trace les courbes isochrones pour une prière donnée

        Args:
            prayer_name (str): Nom de la prière ('fajr', 'dhuhr', etc.)
            gdf: GeoDataFrame du pays
            selected_date: Date pour le calcul
            country_name (str): Nom du pays pour le titre

        Returns:
            bool: True si succès, False sinon
        """
        if gdf is None:
            return False

        # Effacer anciennes courbes
        self.clear_isochrones()

        # Sauvegarder pour le titre
        self.current_prayer = prayer_name
        self.current_country = country_name

        # Obtenir limites géographiques
        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Créer grille de calcul
        n_lat = 60
        n_lon = 60
        lats = np.linspace(min_lat, max_lat, n_lat)
        lons = np.linspace(min_lon, max_lon, n_lon)

        # Matrice pour stocker les heures
        prayer_times_grid = np.zeros((n_lat, n_lon))

        # Calculer les heures pour chaque point de la grille
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                tz = round(lon / 15)
                times = self.pray_calc.getTimes(
                    selected_date,
                    (lat, lon, 0),
                    tz,
                    format='Float'
                )

                if prayer_name in times:
                    t = times[prayer_name]
                    if not math.isnan(t):
                        prayer_times_grid[i, j] = t * 60
                    else:
                        prayer_times_grid[i, j] = np.nan

        # Générer les niveaux de contour (une courbe par minute)
        min_time = np.nanmin(prayer_times_grid)
        max_time = np.nanmax(prayer_times_grid)

        if np.isnan(min_time) or np.isnan(max_time):
            return False

        levels = np.arange(np.floor(min_time), np.ceil(max_time) + 1, 1)

        if len(levels) < 2:
            return False

        # Tracer les courbes de niveau
        contours = self.ax.contour(
            lons, lats, prayer_times_grid,
            levels=levels,
            colors='purple',
            linewidths=1.2,
            alpha=0.7
        )

        # Ajouter les étiquettes (toutes les 5 minutes) avec vérification des limites
        label_levels = [l for l in levels if int(l) % 5 == 0]
        if label_levels:
            clabels = self.ax.clabel(
                contours,
                levels=label_levels,
                inline=True,
                fontsize=8,
                fmt=lambda x: self._format_time_label(x)
            )

            # Filtrer les étiquettes hors limites
            for label in clabels:
                x, y = label.get_position()
                if not (min_lon <= x <= max_lon and min_lat <= y <= max_lat):
                    label.set_visible(False)

            self.isochrone_lines.extend(clabels)

        # Sauvegarder les références pour pouvoir les effacer plus tard
        self.isochrone_lines.append(contours)

        # Mettre à jour le titre
        self._update_title()

        return True

    def _format_time_label(self, minutes):
        """
        Formate une valeur en minutes en hh:mm

        Args:
            minutes (float): Temps en minutes depuis minuit

        Returns:
            str: Temps formaté en hh:mm
        """
        hours = int(minutes // 60) % 24
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"

    def _update_title(self):
        """Met à jour le titre de la carte avec le pays et la prière"""
        if self.current_country and self.current_prayer:
            prayer_names_fr = {
                'fajr': 'Fajr',
                'sunrise': 'Lever du soleil',
                'dhuhr': 'Dhuhr',
                'asr': 'Asr',
                'sunset': 'Coucher du soleil',
                'maghrib': 'Maghrib',
                'isha': 'Isha'
            }
            prayer_display = prayer_names_fr.get(self.current_prayer, self.current_prayer.capitalize())
            title = f"{self.current_country} - Courbes isochrones de {prayer_display}"
            self.ax.set_title(title, fontsize=12, fontweight='bold')

    def clear_isochrones(self):
        """Efface toutes les courbes isochrones de la carte"""
        for item in self.isochrone_lines:
            try:
                if hasattr(item, 'remove'):
                    item.remove()
                elif hasattr(item, 'collections'):
                    for coll in item.collections:
                        coll.remove()
            except:
                pass
        self.isochrone_lines = []

    def get_isochrone_count(self):
        """Retourne le nombre de courbes actuellement affichées"""
        return len(self.isochrone_lines)


class IsochroneGeneratorExact(IsochroneGenerator):
    """
    Version haute précision du générateur d'isochrones.
    Utilise une grille plus fine avec timezone exact par point.
    """

    def __init__(self, pray_calc, ax):
        super().__init__(pray_calc, ax)
        self.grid_resolution = 100  # Résolution de la grille

    def tracer_isochrones(self, prayer_name, gdf, selected_date, country_name=None):
        """
        Trace les courbes isochrones avec haute précision.

        Args:
            prayer_name (str): Nom de la prière
            gdf: GeoDataFrame du pays
            selected_date: Date pour le calcul
            country_name (str): Nom du pays pour le titre

        Returns:
            bool: True si succès
        """
        if gdf is None:
            return False

        self.clear_isochrones()

        # Sauvegarder pour le titre
        self.current_prayer = prayer_name
        self.current_country = country_name

        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Grille haute résolution
        n_lat = self.grid_resolution
        n_lon = self.grid_resolution
        lats = np.linspace(min_lat, max_lat, n_lat)
        lons = np.linspace(min_lon, max_lon, n_lon)

        prayer_times_grid = np.zeros((n_lat, n_lon))

        # Calculer avec timezone exact pour chaque point
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                tz = round(lon / 15)

                times = self.pray_calc.getTimes(
                    selected_date,
                    (lat, lon, 0),
                    tz,
                    format='Float'
                )

                if prayer_name in times:
                    t = times[prayer_name]
                    if not math.isnan(t):
                        prayer_times_grid[i, j] = t * 60
                    else:
                        prayer_times_grid[i, j] = np.nan

        min_time = np.nanmin(prayer_times_grid)
        max_time = np.nanmax(prayer_times_grid)

        if np.isnan(min_time) or np.isnan(max_time):
            return False

        levels = np.arange(np.floor(min_time), np.ceil(max_time) + 1, 1)

        if len(levels) < 2:
            return False

        # Tracer les courbes
        contours = self.ax.contour(
            lons, lats, prayer_times_grid,
            levels=levels,
            colors='purple',
            linewidths=1.2,
            alpha=0.7
        )

        # Ajouter les étiquettes avec vérification des limites
        label_levels = [l for l in levels if int(l) % 5 == 0]
        if label_levels:
            clabels = self.ax.clabel(
                contours,
                levels=label_levels,
                inline=True,
                fontsize=8,
                fmt=lambda x: self._format_time_label(x)
            )

            # Masquer les étiquettes hors limites
            margin = 0.01 * (max_lon - min_lon)  # Petite marge
            for label in clabels:
                x, y = label.get_position()
                if not (min_lon + margin <= x <= max_lon - margin and
                        min_lat + margin <= y <= max_lat - margin):
                    label.set_visible(False)

            self.isochrone_lines.extend(clabels)

        self.isochrone_lines.append(contours)

        # Mettre à jour le titre
        self._update_title()

        return True


class IsochroneGeneratorDirect(IsochroneGenerator):
    """
    Générateur d'isochrones par calcul analytique direct.

    Approche : Pour chaque heure cible T, calcule lon = f(lat) directement.

    Avantages :
    - Calcul direct sans itération ni bisection
    - Une seule solution par latitude (pas d'ambiguïté)
    - Plus rapide que l'approche par grille
    - Courbes exactes (pas d'interpolation)
    """

    def __init__(self, pray_calc, ax):
        super().__init__(pray_calc, ax)
        self.num_lat_points = 200  # Points par courbe

    def tracer_isochrones(self, prayer_name, gdf, selected_date, country_name=None):
        """
        Trace les courbes isochrones par calcul analytique direct.

        Args:
            prayer_name (str): Nom de la prière
            gdf: GeoDataFrame du pays
            selected_date: Date pour le calcul
            country_name (str): Nom du pays pour le titre

        Returns:
            bool: True si succès
        """
        if gdf is None:
            return False

        self.clear_isochrones()

        # Sauvegarder pour le titre
        self.current_prayer = prayer_name
        self.current_country = country_name

        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Calculer les paramètres solaires au centre du pays
        center_lon = (min_lon + max_lon) / 2
        center_lat = (min_lat + max_lat) / 2
        tz_ref = round(center_lon / 15)

        # Convertir la date
        if type(selected_date).__name__ == 'date':
            date_tuple = (selected_date.year, selected_date.month, selected_date.day)
        else:
            date_tuple = selected_date

        # Calculer déclinaison et équation du temps
        jd = self._julian(date_tuple[0], date_tuple[1], date_tuple[2])
        decl, eqt = self._sun_position(jd)

        # Obtenir les paramètres de la prière
        prayer_params = self._get_prayer_params(prayer_name)
        if prayer_params is None:
            return False

        angle, direction, is_asr, asr_factor = prayer_params

        # Déterminer la plage d'heures à tracer
        # Échantillonner une grille sparse pour couvrir tout le pays
        sample_times = []
        n_samples = 10
        sample_lats = np.linspace(min_lat, max_lat, n_samples)
        sample_lons = np.linspace(min_lon, max_lon, n_samples)

        for lat in sample_lats:
            for lon in sample_lons:
                tz = round(lon / 15)
                times = self.pray_calc.getTimes(
                    selected_date,
                    (lat, lon, 0),
                    tz,
                    format='Float'
                )
                if prayer_name in times:
                    t = times[prayer_name]
                    if not math.isnan(t):
                        sample_times.append(t * 60)  # En minutes

        if not sample_times:
            return False

        # Ajouter une marge de sécurité (5 minutes de chaque côté)
        min_time = min(sample_times) - 5
        max_time = max(sample_times) + 5

        # Générer les niveaux (une courbe par minute)
        levels = list(range(int(np.floor(min_time)), int(np.ceil(max_time)) + 1))

        if len(levels) < 2:
            return False

        # Déterminer les fuseaux horaires couverts par le pays
        tz_min = int(np.floor(min_lon / 15))
        tz_max = int(np.ceil(max_lon / 15))
        timezones = list(range(tz_min, tz_max + 1))

        # Générer les latitudes
        lats = np.linspace(min_lat, max_lat, self.num_lat_points)

        # Tracer chaque isochrone
        for target_minutes in levels:
            target_time = target_minutes / 60.0  # Convertir en heures

            # Pour cette isochrone, collecter tous les segments (un par timezone)
            all_segments = []

            for tz in timezones:
                segment_points = []

                for lat in lats:
                    lon = self._compute_longitude(
                        lat, target_time, decl, eqt, tz,
                        angle, direction, is_asr, asr_factor
                    )

                    if lon is not None and min_lon <= lon <= max_lon:
                        # Vérifier que le point est dans le bon fuseau horaire
                        actual_tz = round(lon / 15)
                        if actual_tz == tz:
                            segment_points.append((lon, lat))

                # Ajouter ce segment s'il a assez de points
                if len(segment_points) >= 2:
                    all_segments.append(segment_points)

            # Tracer chaque segment séparément
            for segment in all_segments:
                curve_lons = [p[0] for p in segment]
                curve_lats = [p[1] for p in segment]

                line, = self.ax.plot(
                    curve_lons, curve_lats,
                    color='purple',
                    linewidth=1.2,
                    alpha=0.7
                )
                self.isochrone_lines.append(line)

            # Ajouter une étiquette toutes les 5 minutes (sur le premier segment valide)
            if target_minutes % 5 == 0 and all_segments:
                # Prendre le segment le plus long pour l'étiquette
                longest_segment = max(all_segments, key=len)
                mid_idx = len(longest_segment) // 2
                label_x = longest_segment[mid_idx][0]
                label_y = longest_segment[mid_idx][1]

                # Vérifier que l'étiquette est dans les limites
                margin = 0.02 * (max_lon - min_lon)
                if (min_lon + margin <= label_x <= max_lon - margin and
                        min_lat + margin <= label_y <= max_lat - margin):
                    label_text = self._format_time_label(target_minutes)
                    text = self.ax.text(
                        label_x, label_y, label_text,
                        fontsize=8,
                        ha='center', va='center',
                        bbox=dict(boxstyle='round,pad=0.2',
                                  facecolor='white',
                                  edgecolor='none',
                                  alpha=0.7)
                    )
                    self.isochrone_lines.append(text)

        # Mettre à jour le titre
        self._update_title()

        return True

    def _compute_longitude(self, lat, target_time, decl, eqt, tz_ref,
                           angle, direction, is_asr, asr_factor):
        """
        Calcule la longitude où la prière a lieu à target_time pour une latitude donnée.

        Formule : lon = 15 × (12 - EqT + tz_ref - T) ± H
        où H = arccos[(-sin(α) - sin(δ)×sin(φ)) / (cos(δ)×cos(φ))]

        Args:
            lat: Latitude en degrés
            target_time: Heure cible en heures décimales
            decl: Déclinaison solaire en degrés
            eqt: Équation du temps en heures
            tz_ref: Timezone de référence
            angle: Angle de la prière en degrés
            direction: 'ccw' (matin) ou 'cw' (soir)
            is_asr: True si c'est la prière Asr
            asr_factor: Facteur Asr (1 ou 2)

        Returns:
            float|None: Longitude en degrés ou None si pas de solution
        """
        # Cas spécial : Dhuhr (midi solaire)
        if direction is None:
            # Pour Dhuhr : T = 12 - EqT + tz - lon/15
            # => lon = 15 × (12 - EqT + tz - T)
            lon = 15 * (12 - eqt + tz_ref - target_time)
            return lon

        # Pour Asr, l'angle dépend de la latitude
        if is_asr:
            try:
                angle = -self._arccot(asr_factor + self._tan(abs(lat - decl)))
            except (ValueError, ZeroDivisionError):
                return None

        # Calculer l'angle horaire H
        try:
            cos_lat = self._cos(lat)
            sin_lat = self._sin(lat)
            cos_decl = self._cos(decl)
            sin_decl = self._sin(decl)

            if abs(cos_lat) < 1e-10 or abs(cos_decl) < 1e-10:
                return None

            cos_H = (-self._sin(angle) - sin_decl * sin_lat) / (cos_decl * cos_lat)

            if abs(cos_H) > 1:
                return None  # Pas de solution (hautes latitudes)

            H = self._arccos(cos_H)

        except (ValueError, ZeroDivisionError):
            return None

        # Calculer la longitude
        # T = T_noon ± H/15
        # T_noon = 12 - EqT + tz - lon/15
        # => lon = 15 × (12 - EqT + tz - T) ± H
        base_lon = 15 * (12 - eqt + tz_ref - target_time)

        if direction == 'ccw':
            # Matin : T = T_noon - H/15 => lon = base_lon - H
            lon = base_lon - H
        else:
            # Soir : T = T_noon + H/15 => lon = base_lon + H
            lon = base_lon + H

        return lon

    def _get_prayer_params(self, prayer):
        """
        Retourne les paramètres de calcul pour une prière.

        Returns:
            tuple: (angle, direction, is_asr, asr_factor) ou None
        """
        settings = self.pray_calc.settings

        # Extraire l'angle fajr
        fajr_angle = self._eval(settings.get('fajr', 18))
        isha_angle = self._eval(settings.get('isha', 17))
        maghrib_angle = self._eval(settings.get('maghrib', 0))

        # Facteur Asr
        asr_param = settings.get('asr', 'Standard')
        asr_factor = 1 if asr_param == 'Standard' else (2 if asr_param == 'Hanafi' else self._eval(asr_param))

        prayer_config = {
            'fajr': (fajr_angle, 'ccw', False, None),
            'sunrise': (0.833, 'ccw', False, None),
            'dhuhr': (0, None, False, None),  # Cas spécial
            'asr': (None, 'cw', True, asr_factor),
            'sunset': (0.833, 'cw', False, None),
            'maghrib': (maghrib_angle if maghrib_angle > 0 else 0.833, 'cw', False, None),
            'isha': (isha_angle, 'cw', False, None),
        }

        return prayer_config.get(prayer)

    def _eval(self, st):
        """Extrait une valeur numérique."""
        import re
        if isinstance(st, (int, float)):
            return float(st)
        val = re.split('[^0-9.+-]', str(st), 1)[0]
        return float(val) if val else 0

    def _julian(self, year, month, day):
        """Convertit une date en jour julien."""
        if month <= 2:
            year -= 1
            month += 12
        A = math.floor(year / 100)
        B = 2 - A + math.floor(A / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5

    def _sun_position(self, jd):
        """Calcule la position du soleil (déclinaison et équation du temps)."""
        D = jd - 2451545.0
        g = self._fixangle(357.529 + 0.98560028 * D)
        q = self._fixangle(280.459 + 0.98564736 * D)
        L = self._fixangle(q + 1.915 * self._sin(g) + 0.020 * self._sin(2 * g))
        e = 23.439 - 0.00000036 * D
        RA = self._arctan2(self._cos(e) * self._sin(L), self._cos(L)) / 15.0
        eqt = q / 15.0 - self._fixhour(RA)
        decl = self._arcsin(self._sin(e) * self._sin(L))
        return decl, eqt

    # Fonctions trigonométriques en degrés
    def _sin(self, d):
        return math.sin(math.radians(d))

    def _cos(self, d):
        return math.cos(math.radians(d))

    def _tan(self, d):
        return math.tan(math.radians(d))

    def _arcsin(self, x):
        return math.degrees(math.asin(x))

    def _arccos(self, x):
        return math.degrees(math.acos(x))

    def _arctan2(self, y, x):
        return math.degrees(math.atan2(y, x))

    def _arccot(self, x):
        return math.degrees(math.atan(1.0 / x))

    def _fixangle(self, angle):
        angle = angle - 360.0 * math.floor(angle / 360.0)
        return angle + 360.0 if angle < 0 else angle

    def _fixhour(self, hour):
        hour = hour - 24.0 * math.floor(hour / 24.0)
        return hour + 24.0 if hour < 0 else hour

#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module de traçage des courbes isochrones pour Mawaquit
Génère des courbes montrant les zones géographiques où une prière
a lieu à la même heure
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

    def tracer_isochrones(self, prayer_name, gdf, selected_date):
        """
        Trace les courbes isochrones pour une prière donnée

        Args:
            prayer_name (str): Nom de la prière ('fajr', 'dhuhr', etc.)
            gdf: GeoDataFrame du pays
            selected_date: Date pour le calcul

        Returns:
            bool: True si succès, False sinon
        """
        if gdf is None:
            return False

        # Effacer anciennes courbes
        self.clear_isochrones()

        # Obtenir limites géographiques
        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Créer grille de calcul (50x50 pour rapidité)
        n_lat = 50
        n_lon = 50
        lats = np.linspace(min_lat, max_lat, n_lat)
        lons = np.linspace(min_lon, max_lon, n_lon)

        # Calculer timezone unique pour tout le pays (version rapide)
        tz = round((min_lon + max_lon) / 30)

        # Matrice pour stocker les heures
        prayer_times_grid = np.zeros((n_lat, n_lon))

        # Calculer les heures pour chaque point de la grille
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                times = self.pray_calc.getTimes(
                    selected_date,
                    (lat, lon, 0),
                    tz,
                    format='Float'
                )

                if prayer_name in times:
                    t = times[prayer_name]
                    if not math.isnan(t):
                        # Convertir en minutes depuis minuit
                        # PAS d'arrondi pour garder les courbes lisses
                        prayer_times_grid[i, j] = t * 60
                    else:
                        prayer_times_grid[i, j] = np.nan

        # Générer les niveaux de contour (une courbe par minute)
        min_time = np.nanmin(prayer_times_grid)
        max_time = np.nanmax(prayer_times_grid)
        levels = np.arange(min_time, max_time, 1)

        # Tracer les courbes de niveau
        contours = self.ax.contour(
            lons, lats, prayer_times_grid,
            levels=levels,
            colors='purple',
            linewidths=1.2,
            alpha=0.7
        )

        # Ajouter les étiquettes (toutes les 5 minutes)
        label_levels = levels[::5]
        clabels = self.ax.clabel(
            contours,
            levels=label_levels,
            inline=True,
            fontsize=8,
            fmt=lambda x: self._format_time_label(x)
        )

        # Sauvegarder les références pour pouvoir les effacer plus tard
        self.isochrone_lines.append(contours)
        self.isochrone_lines.extend(clabels)

        return True

    def _format_time_label(self, minutes):
        """
        Formate une valeur en minutes en hh:mm

        Args:
            minutes (float): Temps en minutes depuis minuit

        Returns:
            str: Temps formaté en hh:mm
        """
        hours = int(minutes // 60)
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"

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


class IsochroneGeneratorPrecise(IsochroneGenerator):
    """
    Version haute précision du générateur d'isochrones
    Utilise une grille plus fine et un timezone exact par point
    Plus lent mais plus précis
    """

    def tracer_isochrones(self, prayer_name, gdf, selected_date):
        """
        Trace les courbes isochrones avec haute précision

        Args:
            prayer_name (str): Nom de la prière
            gdf: GeoDataFrame du pays
            selected_date: Date pour le calcul

        Returns:
            bool: True si succès
        """
        if gdf is None:
            return False

        self.clear_isochrones()

        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Grille plus fine pour meilleure précision (80x80)
        n_lat = 80
        n_lon = 80
        lats = np.linspace(min_lat, max_lat, n_lat)
        lons = np.linspace(min_lon, max_lon, n_lon)

        prayer_times_grid = np.zeros((n_lat, n_lon))

        # Calculer avec timezone exact pour chaque point
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                # Timezone exact basé sur la longitude
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
        levels = np.arange(min_time, max_time, 1)

        contours = self.ax.contour(
            lons, lats, prayer_times_grid,
            levels=levels,
            colors='purple',
            linewidths=1.2,
            alpha=0.7
        )

        label_levels = levels[::5]
        clabels = self.ax.clabel(
            contours,
            levels=label_levels,
            inline=True,
            fontsize=8,
            fmt=lambda x: self._format_time_label(x)
        )

        self.isochrone_lines.append(contours)
        self.isochrone_lines.extend(clabels)

        return True
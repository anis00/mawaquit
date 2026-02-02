#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module de traçage des courbes isochrones pour Mawaquit
Génère des courbes montrant les zones géographiques où une prière
a lieu à la même heure

Quatre classes disponibles :
- IsochroneGenerator : Approche par grille (60×60)
- IsochroneGeneratorExact : Approche par grille haute résolution (100×100)
- IsochroneGeneratorDirect : Approche analytique lon = f(lat) - lignes
- IsochroneGeneratorBands : Approche analytique lon = f(lat) - bandes colorées
"""

import numpy as np
import math


class IsochroneGenerator:
    """Classe de base pour générer et tracer les courbes isochrones"""

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

    def tracer_isochrones(self, prayer_name, gdf, selected_date, country_name=None, country_timezone=None):
        """
        Trace les courbes isochrones pour une prière donnée (méthode par grille)

        Args:
            prayer_name (str): Nom de la prière ('fajr', 'dhuhr', etc.)
            gdf: GeoDataFrame du pays
            selected_date: Date pour le calcul
            country_name (str): Nom du pays pour le titre
            country_timezone (int): Fuseau horaire fixe du pays

        Returns:
            bool: True si succès, False sinon
        """
        if gdf is None:
            return False

        self.clear_isochrones()
        self.current_prayer = prayer_name
        self.current_country = country_name

        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Utiliser le fuseau horaire fixe ou calculer au centre
        if country_timezone is not None:
            tz_fixed = country_timezone
        else:
            tz_fixed = round((min_lon + max_lon) / 2 / 15)

        n_lat, n_lon = 60, 60
        lats = np.linspace(min_lat, max_lat, n_lat)
        lons = np.linspace(min_lon, max_lon, n_lon)

        prayer_times_grid = np.zeros((n_lat, n_lon))

        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                times = self.pray_calc.getTimes(
                    selected_date, (lat, lon, 0), tz_fixed, format='Float'
                )
                if prayer_name in times:
                    t = times[prayer_name]
                    prayer_times_grid[i, j] = t * 60 if not math.isnan(t) else np.nan

        min_time = np.nanmin(prayer_times_grid)
        max_time = np.nanmax(prayer_times_grid)

        if np.isnan(min_time) or np.isnan(max_time):
            return False

        levels = np.arange(np.floor(min_time), np.ceil(max_time) + 1, 1)
        if len(levels) < 2:
            return False

        contours = self.ax.contour(
            lons, lats, prayer_times_grid,
            levels=levels, colors='purple', linewidths=1.2, alpha=0.7
        )

        label_levels = [l for l in levels if int(l) % 5 == 0]
        if label_levels:
            clabels = self.ax.clabel(
                contours, levels=label_levels, inline=True, fontsize=8,
                fmt=lambda x: self._format_time_label(x)
            )
            for label in clabels:
                x, y = label.get_position()
                if not (min_lon <= x <= max_lon and min_lat <= y <= max_lat):
                    label.set_visible(False)
            self.isochrone_lines.extend(clabels)

        self.isochrone_lines.append(contours)
        self._update_title()
        return True

    def _format_time_label(self, minutes):
        hours = int(minutes // 60) % 24
        mins = int(minutes % 60)
        return f"{hours:02d}:{mins:02d}"

    def _update_title(self):
        if self.current_country and self.current_prayer:
            prayer_names_fr = {
                'fajr': 'Fajr', 'sunrise': 'Lever du soleil', 'dhuhr': 'Dhuhr',
                'asr': 'Asr', 'sunset': 'Coucher du soleil', 'maghrib': 'Maghrib', 'isha': 'Isha'
            }
            prayer_display = prayer_names_fr.get(self.current_prayer, self.current_prayer.capitalize())
            self.ax.set_title(f"{self.current_country} - Courbes isochrones de {prayer_display}",
                            fontsize=12, fontweight='bold')

    def clear_isochrones(self):
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


class IsochroneGeneratorDirect(IsochroneGenerator):
    """
    Générateur d'isochrones par calcul analytique direct.
    Approche : Pour chaque heure cible T, calcule lon = f(lat) directement.
    """

    def __init__(self, pray_calc, ax):
        super().__init__(pray_calc, ax)
        self.num_lat_points = 200

    def tracer_isochrones(self, prayer_name, gdf, selected_date, country_name=None, country_timezone=None):
        if gdf is None:
            return False

        self.clear_isochrones()
        self.current_prayer = prayer_name
        self.current_country = country_name

        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Fuseau horaire fixe du pays
        if country_timezone is not None:
            tz_fixed = country_timezone
        else:
            tz_fixed = round((min_lon + max_lon) / 2 / 15)

        if type(selected_date).__name__ == 'date':
            date_tuple = (selected_date.year, selected_date.month, selected_date.day)
        else:
            date_tuple = selected_date

        jd = self._julian(date_tuple[0], date_tuple[1], date_tuple[2])
        decl, eqt = self._sun_position(jd)

        prayer_params = self._get_prayer_params(prayer_name)
        if prayer_params is None:
            return False

        angle, direction, is_asr, asr_factor = prayer_params

        # Échantillonner pour trouver la plage d'heures
        sample_times = []
        for lat in np.linspace(min_lat, max_lat, 10):
            for lon in np.linspace(min_lon, max_lon, 10):
                times = self.pray_calc.getTimes(selected_date, (lat, lon, 0), tz_fixed, format='Float')
                if prayer_name in times:
                    t = times[prayer_name]
                    if not math.isnan(t):
                        sample_times.append(t * 60)

        if not sample_times:
            return False

        min_time = min(sample_times) - 5
        max_time = max(sample_times) + 5
        levels = list(range(int(np.floor(min_time)), int(np.ceil(max_time)) + 1))

        if len(levels) < 2:
            return False

        lats = np.linspace(min_lat, max_lat, self.num_lat_points)

        for target_minutes in levels:
            target_time = target_minutes / 60.0
            segment_points = []

            for lat in lats:
                lon = self._compute_longitude(
                    lat, target_time, decl, eqt, tz_fixed,
                    angle, direction, is_asr, asr_factor, jd_base=jd
                )
                if lon is not None and min_lon <= lon <= max_lon:
                    segment_points.append((lon, lat))

            if len(segment_points) >= 2:
                curve_lons = [p[0] for p in segment_points]
                curve_lats = [p[1] for p in segment_points]
                line, = self.ax.plot(curve_lons, curve_lats, color='purple', linewidth=1.2, alpha=0.7)
                self.isochrone_lines.append(line)

                if target_minutes % 5 == 0:
                    mid_idx = len(segment_points) // 2
                    label_x, label_y = segment_points[mid_idx]
                    margin = 0.02 * (max_lon - min_lon)
                    if (min_lon + margin <= label_x <= max_lon - margin and
                            min_lat + margin <= label_y <= max_lat - margin):
                        text = self.ax.text(label_x, label_y, self._format_time_label(target_minutes),
                                          fontsize=8, ha='center', va='center',
                                          bbox=dict(boxstyle='round,pad=0.2', facecolor='white',
                                                   edgecolor='none', alpha=0.7))
                        self.isochrone_lines.append(text)

        self._update_title()
        return True

    def _compute_longitude(self, lat, target_time, decl, eqt, tz_ref,
                           angle, direction, is_asr, asr_factor, jd_base=None):
        if direction is None:  # Dhuhr
            lon = 15 * (12 - eqt + tz_ref - target_time)
            if jd_base is not None:
                for _ in range(2):
                    jd_adj = jd_base - lon / (15 * 24.0)
                    decl, eqt = self._sun_position(jd_adj)
                    lon = 15 * (12 - eqt + tz_ref - target_time)
            return lon

        lon = self._compute_lon_single(lat, target_time, decl, eqt, tz_ref,
                                       angle, direction, is_asr, asr_factor)
        if lon is None:
            return None

        if jd_base is not None:
            for _ in range(2):
                jd_adj = jd_base - lon / (15 * 24.0)
                decl_new, eqt_new = self._sun_position(jd_adj)
                lon_new = self._compute_lon_single(lat, target_time, decl_new, eqt_new,
                                                   tz_ref, angle, direction, is_asr, asr_factor)
                if lon_new is None:
                    return lon
                lon = lon_new

        return lon

    def _compute_lon_single(self, lat, target_time, decl, eqt, tz_ref,
                            angle, direction, is_asr, asr_factor):
        if is_asr:
            try:
                angle = -self._arccot(asr_factor + self._tan(abs(lat - decl)))
            except (ValueError, ZeroDivisionError):
                return None

        try:
            cos_lat = self._cos(lat)
            sin_lat = self._sin(lat)
            cos_decl = self._cos(decl)
            sin_decl = self._sin(decl)

            if abs(cos_lat) < 1e-10 or abs(cos_decl) < 1e-10:
                return None

            cos_H = (-self._sin(angle) - sin_decl * sin_lat) / (cos_decl * cos_lat)
            if abs(cos_H) > 1:
                return None

            H = self._arccos(cos_H)
        except (ValueError, ZeroDivisionError):
            return None

        base_lon = 15 * (12 - eqt + tz_ref - target_time)
        return base_lon - H if direction == 'ccw' else base_lon + H

    def _get_prayer_params(self, prayer):
        settings = self.pray_calc.settings
        fajr_angle = self._eval(settings.get('fajr', 18))
        isha_angle = self._eval(settings.get('isha', 17))
        maghrib_angle = self._eval(settings.get('maghrib', 0))
        asr_param = settings.get('asr', 'Standard')
        asr_factor = 1 if asr_param == 'Standard' else (2 if asr_param == 'Hanafi' else self._eval(asr_param))

        prayer_config = {
            'fajr': (fajr_angle, 'ccw', False, None),
            'sunrise': (0.833, 'ccw', False, None),
            'dhuhr': (0, None, False, None),
            'asr': (None, 'cw', True, asr_factor),
            'sunset': (0.833, 'cw', False, None),
            'maghrib': (maghrib_angle if maghrib_angle > 0 else 0.833, 'cw', False, None),
            'isha': (isha_angle, 'cw', False, None),
        }
        return prayer_config.get(prayer)

    def _eval(self, st):
        import re
        if isinstance(st, (int, float)):
            return float(st)
        val = re.split('[^0-9.+-]', str(st), 1)[0]
        return float(val) if val else 0

    def _julian(self, year, month, day):
        if month <= 2:
            year -= 1
            month += 12
        A = math.floor(year / 100)
        B = 2 - A + math.floor(A / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5

    def _sun_position(self, jd):
        D = jd - 2451545.0
        g = self._fixangle(357.529 + 0.98560028 * D)
        q = self._fixangle(280.459 + 0.98564736 * D)
        L = self._fixangle(q + 1.915 * self._sin(g) + 0.020 * self._sin(2 * g))
        e = 23.439 - 0.00000036 * D
        RA = self._arctan2(self._cos(e) * self._sin(L), self._cos(L)) / 15.0
        eqt = q / 15.0 - self._fixhour(RA)
        decl = self._arcsin(self._sin(e) * self._sin(L))
        return decl, eqt

    def _sin(self, d): return math.sin(math.radians(d))
    def _cos(self, d): return math.cos(math.radians(d))
    def _tan(self, d): return math.tan(math.radians(d))
    def _arcsin(self, x): return math.degrees(math.asin(x))
    def _arccos(self, x): return math.degrees(math.acos(x))
    def _arctan2(self, y, x): return math.degrees(math.atan2(y, x))
    def _arccot(self, x): return math.degrees(math.atan(1.0 / x))

    def _fixangle(self, angle):
        angle = angle - 360.0 * math.floor(angle / 360.0)
        return angle + 360.0 if angle < 0 else angle

    def _fixhour(self, hour):
        hour = hour - 24.0 * math.floor(hour / 24.0)
        return hour + 24.0 if hour < 0 else hour


class IsochroneGeneratorBands(IsochroneGeneratorDirect):
    """
    Générateur d'isochrones en bandes/polygones colorés.
    Chaque bande représente la zone où l'heure de prière arrondie est identique.
    """

    def __init__(self, pray_calc, ax):
        super().__init__(pray_calc, ax)
        self.colors = [
            '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5',
            '#2196F3', '#1E88E5', '#1976D2', '#1565C0', '#0D47A1'
        ]

    def tracer_isochrones(self, prayer_name, gdf, selected_date, country_name=None, country_timezone=None):
        if gdf is None:
            return False

        self.clear_isochrones()
        self.current_prayer = prayer_name
        self.current_country = country_name

        bounds = gdf.total_bounds
        min_lon, min_lat, max_lon, max_lat = bounds

        # Fuseau horaire fixe du pays
        if country_timezone is not None:
            tz_fixed = country_timezone
        else:
            tz_fixed = round((min_lon + max_lon) / 2 / 15)

        if type(selected_date).__name__ == 'date':
            date_tuple = (selected_date.year, selected_date.month, selected_date.day)
        else:
            date_tuple = selected_date

        jd = self._julian(date_tuple[0], date_tuple[1], date_tuple[2])
        decl, eqt = self._sun_position(jd)

        prayer_params = self._get_prayer_params(prayer_name)
        if prayer_params is None:
            return False

        angle, direction, is_asr, asr_factor = prayer_params

        # Échantillonner pour trouver la plage d'heures
        sample_times = []
        for lat in np.linspace(min_lat, max_lat, 10):
            for lon in np.linspace(min_lon, max_lon, 10):
                times = self.pray_calc.getTimes(selected_date, (lat, lon, 0), tz_fixed, format='Float')
                if prayer_name in times:
                    t = times[prayer_name]
                    if not math.isnan(t):
                        sample_times.append(t * 60)

        if not sample_times:
            return False

        min_time = min(sample_times) - 2
        max_time = max(sample_times) + 2
        minutes_list = list(range(int(np.floor(min_time)), int(np.ceil(max_time)) + 1))

        if len(minutes_list) < 2:
            return False

        lats = np.linspace(min_lat, max_lat, self.num_lat_points)

        for idx, target_minute in enumerate(minutes_list):
            time_low = (target_minute - 0.5) / 60.0
            time_high = (target_minute + 0.5) / 60.0

            curve_low = []
            curve_high = []

            for lat in lats:
                lon_low = self._compute_longitude(
                    lat, time_low, decl, eqt, tz_fixed,
                    angle, direction, is_asr, asr_factor, jd_base=jd
                )
                if lon_low is not None and min_lon <= lon_low <= max_lon:
                    curve_low.append((lon_low, lat))

                lon_high = self._compute_longitude(
                    lat, time_high, decl, eqt, tz_fixed,
                    angle, direction, is_asr, asr_factor, jd_base=jd
                )
                if lon_high is not None and min_lon <= lon_high <= max_lon:
                    curve_high.append((lon_high, lat))

            if len(curve_low) >= 2 and len(curve_high) >= 2:
                self._draw_band(curve_low, curve_high, idx, target_minute,
                               min_lon, max_lon, min_lat, max_lat)

        self._update_title()
        return True

    def _draw_band(self, curve_low, curve_high, color_idx, minute,
                   min_lon, max_lon, min_lat, max_lat):
        polygon_points = list(curve_low) + list(reversed(curve_high))
        if len(polygon_points) < 3:
            return

        polygon_points.append(polygon_points[0])
        poly_lons = [p[0] for p in polygon_points]
        poly_lats = [p[1] for p in polygon_points]

        color = self.colors[color_idx % len(self.colors)]
        fill = self.ax.fill(poly_lons, poly_lats, facecolor=color,
                           edgecolor='purple', linewidth=0.5, alpha=0.6)
        self.isochrone_lines.extend(fill)

        center_lon = np.mean([p[0] for p in curve_low + curve_high])
        center_lat = np.mean([p[1] for p in curve_low + curve_high])

        margin_lon = 0.05 * (max_lon - min_lon)
        margin_lat = 0.05 * (max_lat - min_lat)

        if (min_lon + margin_lon <= center_lon <= max_lon - margin_lon and
                min_lat + margin_lat <= center_lat <= max_lat - margin_lat):
            text = self.ax.text(center_lon, center_lat, self._format_time_label(minute),
                               fontsize=9, fontweight='bold', ha='center', va='center',
                               color='#1a237e',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                                        edgecolor='#1a237e', alpha=0.85))
            self.isochrone_lines.append(text)

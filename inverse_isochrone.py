#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Module de calcul inverse des isochrones pour Mawaquit
Calcul exact de la latitude pour une heure de prière donnée à chaque longitude
"""

import math


class InverseIsochroneCalculator:
    """
    Calculateur inverse d'isochrones.
    Pour une heure de prière cible T, trouve la latitude à chaque longitude.
    """

    def __init__(self, pray_calc, date, timezone_mode='exact'):
        """
        Initialise le calculateur inverse.

        Args:
            pray_calc: Instance de PrayTimes
            date: Date pour le calcul (objet date ou tuple)
            timezone_mode: 'exact' (longitude/15) ou 'fixed' (valeur unique)
        """
        self.pray_calc = pray_calc
        self.timezone_mode = timezone_mode

        # Convertir date en jour julien de base
        if type(date).__name__ == 'date':
            self.date = (date.year, date.month, date.day)
        else:
            self.date = date

        self.jd_base = self._julian(self.date[0], self.date[1], self.date[2])

    def _julian(self, year, month, day):
        """Convertit une date en jour julien."""
        if month <= 2:
            year -= 1
            month += 12
        A = math.floor(year / 100)
        B = 2 - A + math.floor(A / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5

    def get_solar_params(self, lon):
        """
        Calcule les paramètres solaires pour une longitude donnée.

        Args:
            lon: Longitude en degrés

        Returns:
            tuple: (decl, eqt, noon, tz) - déclinaison, équation du temps, midi solaire, timezone
        """
        # Timezone basé sur la longitude
        if self.timezone_mode == 'exact':
            tz = round(lon / 15)
        else:
            tz = self.timezone_mode

        # Jour julien ajusté pour la longitude
        jd = self.jd_base - lon / (15 * 24.0)

        # Position du soleil
        D = jd - 2451545.0
        g = self._fixangle(357.529 + 0.98560028 * D)
        q = self._fixangle(280.459 + 0.98564736 * D)
        L = self._fixangle(q + 1.915 * self._sin(g) + 0.020 * self._sin(2 * g))
        e = 23.439 - 0.00000036 * D
        RA = self._arctan2(self._cos(e) * self._sin(L), self._cos(L)) / 15.0
        eqt = q / 15.0 - self._fixhour(RA)
        decl = self._arcsin(self._sin(e) * self._sin(L))

        # Midi solaire (heure locale)
        noon = self._fixhour(12 - eqt) + tz - lon / 15.0

        return decl, eqt, noon, tz

    def solve_latitude_for_angle(self, lon, target_time, angle, direction='cw'):
        """
        Résout analytiquement pour trouver la latitude où la prière a lieu à target_time.

        Équation: T = noon ± (1/15) × arccos[(-sin(α) - sin(δ) × sin(lat)) / (cos(δ) × cos(lat))]

        Forme linéaire: A × cos(lat) + B × sin(lat) = C

        Args:
            lon: Longitude en degrés
            target_time: Heure cible en heures décimales
            angle: Angle de la prière en degrés (positif sous l'horizon)
            direction: 'ccw' pour avant midi (fajr), 'cw' pour après midi (maghrib)

        Returns:
            float|None: Latitude en degrés, ou None si pas de solution
        """
        decl, eqt, noon, tz = self.get_solar_params(lon)

        # Calcul de l'angle horaire H à partir de l'heure cible
        # T = noon ± H/15 => H = ±15 × (T - noon)
        if direction == 'ccw':
            H = -15 * (target_time - noon)  # Matin: H négatif
        else:
            H = 15 * (target_time - noon)   # Soir: H positif

        # Coefficients de l'équation A×cos(lat) + B×sin(lat) = C
        A = self._cos(decl) * self._cos(H)
        B = self._sin(decl)
        C = -self._sin(angle)

        # Solution: lat = phi - arccos(C/R)
        # où R = sqrt(A² + B²) et phi = arctan2(B, A)
        R = math.sqrt(A * A + B * B)

        if R < 1e-10:
            return None

        ratio = C / R

        # Vérifier si une solution existe
        if abs(ratio) > 1:
            return None

        phi = self._arctan2(B, A)

        # Deux solutions possibles: phi ± arccos(ratio)
        arccos_val = self._arccos(ratio)

        lat1 = phi - arccos_val
        lat2 = phi + arccos_val

        # Choisir la solution dans la plage valide [-90, 90]
        valid_lats = []
        for lat in [lat1, lat2]:
            if -90 <= lat <= 90:
                valid_lats.append(lat)

        if not valid_lats:
            return None

        # Vérifier quelle solution est correcte en recalculant l'heure
        for lat in valid_lats:
            computed_time = self._compute_prayer_time(lon, lat, angle, direction)
            if computed_time is not None and abs(computed_time - target_time) < 0.01:  # 36 secondes
                return lat

        # Si aucune vérification exacte, retourner la première solution valide
        return valid_lats[0] if valid_lats else None

    def _compute_prayer_time(self, lon, lat, angle, direction):
        """Calcule l'heure de prière pour vérification."""
        decl, eqt, noon, tz = self.get_solar_params(lon)

        try:
            cos_H = (-self._sin(angle) - self._sin(decl) * self._sin(lat)) / (self._cos(decl) * self._cos(lat))
            if abs(cos_H) > 1:
                return None
            H = self._arccos(cos_H)
            t = H / 15.0
            if direction == 'ccw':
                return noon - t
            else:
                return noon + t
        except (ValueError, ZeroDivisionError):
            return None

    def solve_latitude_for_asr(self, lon, target_time, factor=1, lat_hint=None):
        """
        Résout numériquement pour Asr (angle dépend de la latitude).

        L'angle Asr est: angle = -arccot(factor + tan(|lat - decl|))
        Note: La fonction n'est pas monotone - l'heure Asr atteint un maximum
        autour d'une certaine latitude.

        Args:
            lon: Longitude en degrés
            target_time: Heure cible en heures décimales
            factor: Facteur Asr (1 pour standard, 2 pour Hanafi)
            lat_hint: Latitude de référence pour choisir parmi les solutions

        Returns:
            float|None: Latitude en degrés, ou None si pas de solution
        """
        decl, eqt, noon, tz = self.get_solar_params(lon)

        def compute_asr_time(lat):
            """Calcule l'heure Asr pour une latitude donnée."""
            try:
                # Éviter les problèmes aux hautes latitudes
                if abs(lat - decl) > 89:
                    return None

                # Angle Asr
                angle = -self._arccot(factor + self._tan(abs(lat - decl)))

                # Calcul standard
                cos_H = (-self._sin(angle) - self._sin(decl) * self._sin(lat)) / (self._cos(decl) * self._cos(lat))
                if abs(cos_H) > 1:
                    return None
                H = self._arccos(cos_H)
                return noon + H / 15.0
            except (ValueError, ZeroDivisionError):
                return None

        # La fonction Asr n'est pas monotone - scanner pour trouver les régions candidates
        # Échantillonner sur la plage de latitudes
        n_samples = 180
        lat_samples = [-89 + i * 178 / (n_samples - 1) for i in range(n_samples)]
        time_samples = [(lat, compute_asr_time(lat)) for lat in lat_samples]
        time_samples = [(lat, t) for lat, t in time_samples if t is not None]

        if not time_samples:
            return None

        # Trouver les intervalles où la cible pourrait se trouver
        tolerance = 0.02  # ~1 minute de tolérance
        candidates = []
        for i in range(len(time_samples) - 1):
            lat1, t1 = time_samples[i]
            lat2, t2 = time_samples[i + 1]

            t_lo, t_hi = min(t1, t2), max(t1, t2)
            # Vérifier si target_time est entre t1 et t2 (avec tolérance)
            if t_lo - tolerance <= target_time <= t_hi + tolerance:
                candidates.append((lat1, lat2, t1, t2))

        if not candidates:
            # Fallback: trouver le point le plus proche
            best_lat, best_t = min(time_samples, key=lambda x: abs(x[1] - target_time))
            if abs(best_t - target_time) < 0.05:  # ~3 minutes
                return best_lat
            return None

        # S'il y a plusieurs candidats, retourner tous les résultats par bisection
        # puis choisir celui le plus proche de 0 (cas commun: équateur)
        results = []
        for lat_min, lat_max, t_min, t_max in candidates:
            result = self._bisect_for_asr(compute_asr_time, lat_min, lat_max, t_min, t_max, target_time)
            if result is not None:
                results.append(result)

        if not results:
            return None

        # Choisir le résultat le plus proche du hint (ou de 0 par défaut)
        reference = lat_hint if lat_hint is not None else 0
        return min(results, key=lambda x: abs(x - reference))

    def _bisect_for_asr(self, compute_fn, lat_min, lat_max, t_min, t_max, target_time):
        """Bisection pour trouver la latitude Asr."""
        for _ in range(50):
            lat_mid = (lat_min + lat_max) / 2
            t_mid = compute_fn(lat_mid)

            if t_mid is None:
                return None

            if abs(t_mid - target_time) < 1e-6:
                return lat_mid

            if (t_mid < target_time) == (t_min < t_max):
                lat_min = lat_mid
                t_min = t_mid
            else:
                lat_max = lat_mid
                t_max = t_mid

        return (lat_min + lat_max) / 2

    def solve_latitude_for_dhuhr(self, lon, target_time):
        """
        Pour Dhuhr, l'heure ne dépend que de la longitude (quasi-constante en latitude).
        Retourne la latitude médiane si l'heure correspond.

        Args:
            lon: Longitude en degrés
            target_time: Heure cible en heures décimales

        Returns:
            float|None: 0 (équateur) si l'heure correspond, None sinon
        """
        decl, eqt, noon, tz = self.get_solar_params(lon)

        # Dhuhr = noon (approximativement)
        if abs(noon - target_time) < 0.02:  # ~1 minute de tolérance
            return 0.0  # L'heure Dhuhr est la même pour toutes les latitudes

        return None

    def generate_isochrone(self, prayer, target_time, lon_min, lon_max, num_points=200, lat_hint=None):
        """
        Génère une courbe isochrone pour une prière et une heure données.

        Args:
            prayer: Nom de la prière ('fajr', 'dhuhr', 'asr', etc.)
            target_time: Heure cible en heures décimales
            lon_min, lon_max: Plage de longitudes
            num_points: Nombre de points à calculer
            lat_hint: Latitude de référence pour les prières à solutions multiples (Asr)

        Returns:
            list: Liste de tuples (lat, lon) formant la courbe
        """
        points = []

        # Obtenir les paramètres de la prière
        prayer_params = self._get_prayer_params(prayer)
        if prayer_params is None:
            return points

        angle, direction, is_asr = prayer_params

        lons = [lon_min + (lon_max - lon_min) * i / (num_points - 1) for i in range(num_points)]

        for lon in lons:
            if prayer == 'dhuhr':
                lat = self.solve_latitude_for_dhuhr(lon, target_time)
            elif is_asr:
                lat = self.solve_latitude_for_asr(lon, target_time, factor=angle, lat_hint=lat_hint)
            else:
                lat = self.solve_latitude_for_angle(lon, target_time, angle, direction)

            if lat is not None:
                points.append((lat, lon))

        return points

    def _get_prayer_params(self, prayer):
        """
        Retourne les paramètres de calcul pour une prière.

        Returns:
            tuple: (angle, direction, is_asr) ou None
        """
        settings = self.pray_calc.settings

        prayer_config = {
            'fajr': (self._eval(settings.get('fajr', 18)), 'ccw', False),
            'sunrise': (0.833, 'ccw', False),  # Angle de lever/coucher
            'dhuhr': (0, None, False),  # Cas spécial
            'asr': (self._asr_factor(settings.get('asr', 'Standard')), 'cw', True),
            'sunset': (0.833, 'cw', False),
            'maghrib': (self._eval(settings.get('maghrib', 0)), 'cw', False),
            'isha': (self._eval(settings.get('isha', 17)), 'cw', False),
        }

        return prayer_config.get(prayer)

    def _asr_factor(self, asr_param):
        """Retourne le facteur Asr."""
        methods = {'Standard': 1, 'Hanafi': 2}
        return methods.get(asr_param, self._eval(asr_param))

    def _eval(self, st):
        """Extrait une valeur numérique."""
        import re
        if isinstance(st, (int, float)):
            return float(st)
        val = re.split('[^0-9.+-]', str(st), 1)[0]
        return float(val) if val else 0

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
        return self._fix(angle, 360.0)

    def _fixhour(self, hour):
        return self._fix(hour, 24.0)

    def _fix(self, a, mode):
        if math.isnan(a):
            return a
        a = a - mode * math.floor(a / mode)
        return a + mode if a < 0 else a

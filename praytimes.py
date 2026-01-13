#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PrayTimes - Module de calcul des heures de prière islamiques
Basé sur les algorithmes de PrayTimes.org
"""

import math


class PrayTimes():
    """
    Classe pour calculer les heures de prière islamiques
    Supporte plusieurs méthodes de calcul internationales
    """

    timeNames = {
        'imsak': 'Imsak',
        'fajr': 'Fajr',
        'sunrise': 'Sunrise',
        'dhuhr': 'Dhuhr',
        'asr': 'Asr',
        'sunset': 'Sunset',
        'maghrib': 'Maghrib',
        'isha': 'Isha',
        'midnight': 'Midnight'
    }

    # Méthodes de calcul disponibles
    methods = {
        'MWL': {
            'name': 'Muslim World League',
            'params': {'fajr': 18, 'isha': 17}
        },
        'ISNA': {
            'name': 'Islamic Society of North America',
            'params': {'fajr': 15, 'isha': 15}
        },
        'Egypt': {
            'name': 'Egyptian General Authority',
            'params': {'fajr': 19.5, 'isha': 17.5}
        },
        'Makkah': {
            'name': 'Umm Al-Qura, Makkah',
            'params': {'fajr': 18.5, 'isha': '90 min'}
        },
        'Karachi': {
            'name': 'University of Islamic Sciences, Karachi',
            'params': {'fajr': 18, 'isha': 18}
        },
        'Tehran': {
            'name': 'Institute of Geophysics, Tehran',
            'params': {'fajr': 17.7, 'isha': 14, 'maghrib': 4.5, 'midnight': 'Jafari'}
        },
        'Jafari': {
            'name': 'Shia Ithna-Ashari, Qum',
            'params': {'fajr': 16, 'isha': 14, 'maghrib': 4, 'midnight': 'Jafari'}
        }
    }

    defaultParams = {
        'maghrib': '0 min',
        'midnight': 'Standard'
    }

    def __init__(self, method="MWL"):
        """
        Initialise le calculateur de prières

        Args:
            method (str): Méthode de calcul ('MWL', 'ISNA', 'Egypt', etc.)
        """
        self.calcMethod = method if method in self.methods else 'MWL'

        # Paramètres par défaut
        self.settings = {
            "imsak": '10 min',
            "dhuhr": '0 min',
            "asr": 'Standard',
            "highLats": 'NightMiddle'
        }

        # Initialiser les paramètres des méthodes
        for method, config in self.methods.items():
            for name, value in self.defaultParams.items():
                if name not in config['params'] or config['params'][name] is None:
                    config['params'][name] = value

        # Appliquer les paramètres de la méthode choisie
        params = self.methods[self.calcMethod]['params']
        for name, value in params.items():
            self.settings[name] = value

        self.timeFormat = '24h'
        self.timeSuffixes = ['am', 'pm']
        self.invalidTime = '-----'
        self.numIterations = 1
        self.offset = {name: 0 for name in self.timeNames}

    def getTimes(self, date, coords, timezone, dst=0, format=None):
        """
        Calcule les heures de prière pour une date et une position données

        Args:
            date: objet date ou tuple (year, month, day)
            coords: tuple (latitude, longitude, elevation)
            timezone: décalage horaire par rapport à UTC
            dst: 1 si heure d'été, 0 sinon
            format: '24h', '12h' ou 'Float'

        Returns:
            dict: Dictionnaire des heures de prière
        """
        self.lat = coords[0]
        self.lng = coords[1]
        self.elv = coords[2] if len(coords) > 2 else 0

        if format is None:
            format = '24h'
        self.timeFormat = format

        if type(date).__name__ == 'date':
            date = (date.year, date.month, date.day)

        self.timeZone = timezone + (1 if dst else 0)
        self.jDate = self.julian(date[0], date[1], date[2]) - self.lng / (15 * 24.0)

        return self.computeTimes()

    def midDay(self, time):
        """Calcule le moment du midi solaire"""
        eqt = self.sunPosition(self.jDate + time)[1]
        return self.fixhour(12 - eqt)

    def sunAngleTime(self, angle, time, direction=None):
        """Calcule l'heure à laquelle le soleil atteint un angle donné"""
        try:
            decl = self.sunPosition(self.jDate + time)[0]
            noon = self.midDay(time)
            t = 1 / 15.0 * self.arccos(
                (-self.sin(angle) - self.sin(decl) * self.sin(self.lat)) /
                (self.cos(decl) * self.cos(self.lat))
            )
            return noon + (-t if direction == 'ccw' else t)
        except ValueError:
            return float('nan')

    def asrTime(self, factor, time):
        """Calcule l'heure de la prière Asr"""
        decl = self.sunPosition(self.jDate + time)[0]
        angle = -self.arccot(factor + self.tan(abs(self.lat - decl)))
        return self.sunAngleTime(angle, time)

    def sunPosition(self, jd):
        """Calcule la position du soleil (déclinaison et équation du temps)"""
        D = jd - 2451545.0
        g = self.fixangle(357.529 + 0.98560028 * D)
        q = self.fixangle(280.459 + 0.98564736 * D)
        L = self.fixangle(q + 1.915 * self.sin(g) + 0.020 * self.sin(2 * g))
        e = 23.439 - 0.00000036 * D
        RA = self.arctan2(self.cos(e) * self.sin(L), self.cos(L)) / 15.0
        eqt = q / 15.0 - self.fixhour(RA)
        decl = self.arcsin(self.sin(e) * self.sin(L))
        return (decl, eqt)

    def julian(self, year, month, day):
        """Convertit une date en jour julien"""
        if month <= 2:
            year -= 1
            month += 12
        A = math.floor(year / 100)
        B = 2 - A + math.floor(A / 4)
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + B - 1524.5

    def computePrayerTimes(self, times):
        """Calcule toutes les heures de prière"""
        times = self.dayPortion(times)
        params = self.settings

        imsak = self.sunAngleTime(self.eval(params['imsak']), times['imsak'], 'ccw')
        fajr = self.sunAngleTime(self.eval(params['fajr']), times['fajr'], 'ccw')
        sunrise = self.sunAngleTime(self.riseSetAngle(self.elv), times['sunrise'], 'ccw')
        dhuhr = self.midDay(times['dhuhr'])
        asr = self.asrTime(self.asrFactor(params['asr']), times['asr'])
        sunset = self.sunAngleTime(self.riseSetAngle(self.elv), times['sunset'])
        maghrib = self.sunAngleTime(self.eval(params['maghrib']), times['maghrib'])
        isha = self.sunAngleTime(self.eval(params['isha']), times['isha'])

        return {
            'imsak': imsak, 'fajr': fajr, 'sunrise': sunrise, 'dhuhr': dhuhr,
            'asr': asr, 'sunset': sunset, 'maghrib': maghrib, 'isha': isha
        }

    def computeTimes(self):
        """Lance le calcul complet des heures de prière"""
        # Valeurs initiales approximatives
        times = {
            'imsak': 5, 'fajr': 5, 'sunrise': 6, 'dhuhr': 12,
            'asr': 13, 'sunset': 18, 'maghrib': 18, 'isha': 18
        }

        # Itérations pour affiner les résultats
        for i in range(self.numIterations):
            times = self.computePrayerTimes(times)

        times = self.adjustTimes(times)

        # Calcul de minuit
        if self.settings['midnight'] == 'Jafari':
            times['midnight'] = times['sunset'] + self.timeDiff(times['sunset'], times['fajr']) / 2
        else:
            times['midnight'] = times['sunset'] + self.timeDiff(times['sunset'], times['sunrise']) / 2

        times = self.tuneTimes(times)
        return self.modifyFormats(times)

    def adjustTimes(self, times):
        """Ajuste les heures selon le fuseau horaire et les paramètres"""
        params = self.settings
        tzAdjust = self.timeZone - self.lng / 15.0

        for t in times:
            times[t] += tzAdjust

        if params['highLats'] != 'None':
            times = self.adjustHighLats(times)

        if self.isMin(params['imsak']):
            times['imsak'] = times['fajr'] - self.eval(params['imsak']) / 60.0
        if self.isMin(params['maghrib']):
            times['maghrib'] = times['sunset'] - self.eval(params['maghrib']) / 60.0
        if self.isMin(params['isha']):
            times['isha'] = times['maghrib'] - self.eval(params['isha']) / 60.0

        times['dhuhr'] += self.eval(params['dhuhr']) / 60.0

        return times

    def asrFactor(self, asrParam):
        """Retourne le facteur pour le calcul de l'Asr"""
        methods = {'Standard': 1, 'Hanafi': 2}
        return methods[asrParam] if asrParam in methods else self.eval(asrParam)

    def riseSetAngle(self, elevation=0):
        """Calcule l'angle pour le lever/coucher du soleil"""
        elevation = 0 if elevation is None else elevation
        return 0.833 + 0.0347 * math.sqrt(elevation)

    def tuneTimes(self, times):
        """Applique les décalages personnalisés"""
        for name in times:
            times[name] += self.offset[name] / 60.0
        return times

    def modifyFormats(self, times):
        """Convertit les heures au format demandé"""
        for name in times:
            times[name] = self.getFormattedTime(times[name], self.timeFormat)
        return times

    def adjustHighLats(self, times):
        """Ajuste les heures pour les hautes latitudes"""
        params = self.settings
        nightTime = self.timeDiff(times['sunset'], times['sunrise'])

        times['imsak'] = self.adjustHLTime(
            times['imsak'], times['sunrise'],
            self.eval(params['imsak']), nightTime, 'ccw'
        )
        times['fajr'] = self.adjustHLTime(
            times['fajr'], times['sunrise'],
            self.eval(params['fajr']), nightTime, 'ccw'
        )
        times['isha'] = self.adjustHLTime(
            times['isha'], times['sunset'],
            self.eval(params['isha']), nightTime
        )
        times['maghrib'] = self.adjustHLTime(
            times['maghrib'], times['sunset'],
            self.eval(params['maghrib']), nightTime
        )

        return times

    def adjustHLTime(self, time, base, angle, night, direction=None):
        """Ajuste une heure spécifique pour les hautes latitudes"""
        portion = self.nightPortion(angle, night)
        diff = self.timeDiff(time, base) if direction == 'ccw' else self.timeDiff(base, time)

        if math.isnan(time) or diff > portion:
            time = base + (-portion if direction == 'ccw' else portion)

        return time

    def nightPortion(self, angle, night):
        """Calcule la portion de nuit à utiliser"""
        method = self.settings['highLats']
        portion = 1 / 2.0

        if method == 'AngleBased':
            portion = 1 / 60.0 * angle
        if method == 'OneSeventh':
            portion = 1 / 7.0

        return portion * night

    def dayPortion(self, times):
        """Convertit les heures en fraction de jour"""
        for i in times:
            times[i] /= 24.0
        return times

    def getFormattedTime(self, time, format, suffixes=None):
        """Formate une heure selon le format demandé"""
        if math.isnan(time):
            return self.invalidTime

        if format == 'Float':
            return time

        if suffixes is None:
            suffixes = self.timeSuffixes

        time = self.fixhour(time + 0.5 / 60)
        hours = math.floor(time)
        minutes = math.floor((time - hours) * 60)

        suffix = suffixes[0 if hours < 12 else 1] if format == '12h' else ''

        if format == "24h":
            formattedTime = "%02d:%02d" % (hours, minutes)
        else:
            formattedTime = "%d:%02d" % ((hours + 11) % 12 + 1, minutes)

        return formattedTime + suffix

    def timeDiff(self, time1, time2):
        """Calcule la différence entre deux heures"""
        return self.fixhour(time2 - time1)

    def eval(self, st):
        """Extrait une valeur numérique d'une chaîne"""
        import re
        val = re.split('[^0-9.+-]', str(st), 1)[0]
        return float(val) if val else 0

    def isMin(self, arg):
        """Vérifie si l'argument est en minutes"""
        return isinstance(arg, str) and arg.find('min') > -1

    # Fonctions trigonométriques en degrés
    def sin(self, d):
        return math.sin(math.radians(d))

    def cos(self, d):
        return math.cos(math.radians(d))

    def tan(self, d):
        return math.tan(math.radians(d))

    def arcsin(self, x):
        return math.degrees(math.asin(x))

    def arccos(self, x):
        return math.degrees(math.acos(x))

    def arctan(self, x):
        return math.degrees(math.atan(x))

    def arccot(self, x):
        return math.degrees(math.atan(1.0 / x))

    def arctan2(self, y, x):
        return math.degrees(math.atan2(y, x))

    def fixangle(self, angle):
        return self.fix(angle, 360.0)

    def fixhour(self, hour):
        return self.fix(hour, 24.0)

    def fix(self, a, mode):
        """Normalise une valeur dans un intervalle"""
        if math.isnan(a):
            return a
        a = a - mode * (math.floor(a / mode))
        return a + mode if a < 0 else a
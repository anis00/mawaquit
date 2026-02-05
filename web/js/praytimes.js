/**
 * PrayTimes - Islamic Prayer Times Calculator
 * Based on the algorithms from PrayTimes.org
 * Ported from Python to JavaScript
 */

class PrayTimes {
    static timeNames = {
        imsak: 'Imsak',
        fajr: 'Fajr',
        sunrise: 'Sunrise',
        dhuhr: 'Dhuhr',
        asr: 'Asr',
        sunset: 'Sunset',
        maghrib: 'Maghrib',
        isha: 'Isha',
        midnight: 'Midnight'
    };

    static methods = {
        MWL: {
            name: 'Muslim World League',
            params: { fajr: 18, isha: 17 }
        },
        ISNA: {
            name: 'Islamic Society of North America',
            params: { fajr: 15, isha: 15 }
        },
        Egypt: {
            name: 'Egyptian General Authority',
            params: { fajr: 19.5, isha: 17.5 }
        },
        Makkah: {
            name: 'Umm Al-Qura, Makkah',
            params: { fajr: 18.5, isha: '90 min' }
        },
        Karachi: {
            name: 'University of Islamic Sciences, Karachi',
            params: { fajr: 18, isha: 18 }
        },
        Tehran: {
            name: 'Institute of Geophysics, Tehran',
            params: { fajr: 17.7, isha: 14, maghrib: 4.5, midnight: 'Jafari' }
        },
        Jafari: {
            name: 'Shia Ithna-Ashari, Qum',
            params: { fajr: 16, isha: 14, maghrib: 4, midnight: 'Jafari' }
        }
    };

    static defaultParams = {
        maghrib: '0 min',
        midnight: 'Standard'
    };

    constructor(method = 'MWL') {
        this.calcMethod = method in PrayTimes.methods ? method : 'MWL';

        // Default settings
        this.settings = {
            imsak: '10 min',
            dhuhr: '0 min',
            asr: 'Standard',
            highLats: 'NightMiddle'
        };

        // Initialize method parameters with defaults
        for (const [methodName, config] of Object.entries(PrayTimes.methods)) {
            for (const [name, value] of Object.entries(PrayTimes.defaultParams)) {
                if (!(name in config.params) || config.params[name] === null) {
                    config.params[name] = value;
                }
            }
        }

        // Apply chosen method parameters
        const params = PrayTimes.methods[this.calcMethod].params;
        for (const [name, value] of Object.entries(params)) {
            this.settings[name] = value;
        }

        this.timeFormat = '24h';
        this.timeSuffixes = ['am', 'pm'];
        this.invalidTime = '-----';
        this.numIterations = 1;
        this.offset = {};
        for (const name of Object.keys(PrayTimes.timeNames)) {
            this.offset[name] = 0;
        }

        // Instance variables for calculations
        this.lat = 0;
        this.lng = 0;
        this.elv = 0;
        this.timeZone = 0;
        this.jDate = 0;
    }

    /**
     * Calculate prayer times for a given date and location
     * @param {Date|Array} date - Date object or [year, month, day] array
     * @param {Array} coords - [latitude, longitude, elevation?]
     * @param {number} timezone - Timezone offset from UTC
     * @param {number} dst - Daylight saving (0 or 1)
     * @param {string} format - Output format: '24h', '12h', or 'Float'
     * @returns {Object} Dictionary of prayer times
     */
    getTimes(date, coords, timezone, dst = 0, format = null) {
        this.lat = coords[0];
        this.lng = coords[1];
        this.elv = coords.length > 2 ? coords[2] : 0;

        if (format === null) {
            format = '24h';
        }
        this.timeFormat = format;

        // Handle Date object
        if (date instanceof Date) {
            date = [date.getFullYear(), date.getMonth() + 1, date.getDate()];
        }

        this.timeZone = timezone + (dst ? 1 : 0);
        this.jDate = this.julian(date[0], date[1], date[2]) - this.lng / (15 * 24.0);

        return this.computeTimes();
    }

    /**
     * Calculate solar noon
     */
    midDay(time) {
        const eqt = this.sunPosition(this.jDate + time)[1];
        return this.fixhour(12 - eqt);
    }

    /**
     * Calculate time when sun reaches given angle
     */
    sunAngleTime(angle, time, direction = null) {
        try {
            const decl = this.sunPosition(this.jDate + time)[0];
            const noon = this.midDay(time);
            const t = (1 / 15.0) * this.arccos(
                (-this.sin(angle) - this.sin(decl) * this.sin(this.lat)) /
                (this.cos(decl) * this.cos(this.lat))
            );
            return noon + (direction === 'ccw' ? -t : t);
        } catch (e) {
            return NaN;
        }
    }

    /**
     * Calculate Asr prayer time
     */
    asrTime(factor, time) {
        const decl = this.sunPosition(this.jDate + time)[0];
        const angle = -this.arccot(factor + this.tan(Math.abs(this.lat - decl)));
        return this.sunAngleTime(angle, time);
    }

    /**
     * Calculate sun position (declination and equation of time)
     */
    sunPosition(jd) {
        const D = jd - 2451545.0;
        const g = this.fixangle(357.529 + 0.98560028 * D);
        const q = this.fixangle(280.459 + 0.98564736 * D);
        const L = this.fixangle(q + 1.915 * this.sin(g) + 0.020 * this.sin(2 * g));
        const e = 23.439 - 0.00000036 * D;
        const RA = this.arctan2(this.cos(e) * this.sin(L), this.cos(L)) / 15.0;
        const eqt = q / 15.0 - this.fixhour(RA);
        const decl = this.arcsin(this.sin(e) * this.sin(L));
        return [decl, eqt];
    }

    /**
     * Convert date to Julian day
     */
    julian(year, month, day) {
        if (month <= 2) {
            year -= 1;
            month += 12;
        }
        const A = Math.floor(year / 100);
        const B = 2 - A + Math.floor(A / 4);
        return Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + B - 1524.5;
    }

    /**
     * Calculate all prayer times
     */
    computePrayerTimes(times) {
        times = this.dayPortion(times);
        const params = this.settings;

        const imsak = this.sunAngleTime(this.eval(params.imsak), times.imsak, 'ccw');
        const fajr = this.sunAngleTime(this.eval(params.fajr), times.fajr, 'ccw');
        const sunrise = this.sunAngleTime(this.riseSetAngle(this.elv), times.sunrise, 'ccw');
        const dhuhr = this.midDay(times.dhuhr);
        const asr = this.asrTime(this.asrFactor(params.asr), times.asr);
        const sunset = this.sunAngleTime(this.riseSetAngle(this.elv), times.sunset);
        const maghrib = this.sunAngleTime(this.eval(params.maghrib), times.maghrib);
        const isha = this.sunAngleTime(this.eval(params.isha), times.isha);

        return {
            imsak, fajr, sunrise, dhuhr,
            asr, sunset, maghrib, isha
        };
    }

    /**
     * Compute prayer times
     */
    computeTimes() {
        // Initial approximations
        let times = {
            imsak: 5, fajr: 5, sunrise: 6, dhuhr: 12,
            asr: 13, sunset: 18, maghrib: 18, isha: 18
        };

        // Refine through iterations
        for (let i = 0; i < this.numIterations; i++) {
            times = this.computePrayerTimes(times);
        }

        times = this.adjustTimes(times);

        // Calculate midnight
        if (this.settings.midnight === 'Jafari') {
            times.midnight = times.sunset + this.timeDiff(times.sunset, times.fajr) / 2;
        } else {
            times.midnight = times.sunset + this.timeDiff(times.sunset, times.sunrise) / 2;
        }

        times = this.tuneTimes(times);
        return this.modifyFormats(times);
    }

    /**
     * Adjust times for timezone and parameters
     */
    adjustTimes(times) {
        const params = this.settings;
        const tzAdjust = this.timeZone - this.lng / 15.0;

        for (const t in times) {
            times[t] += tzAdjust;
        }

        if (params.highLats !== 'None') {
            times = this.adjustHighLats(times);
        }

        if (this.isMin(params.imsak)) {
            times.imsak = times.fajr - this.eval(params.imsak) / 60.0;
        }
        if (this.isMin(params.maghrib)) {
            times.maghrib = times.sunset - this.eval(params.maghrib) / 60.0;
        }
        if (this.isMin(params.isha)) {
            times.isha = times.maghrib - this.eval(params.isha) / 60.0;
        }

        times.dhuhr += this.eval(params.dhuhr) / 60.0;

        return times;
    }

    /**
     * Get Asr shadow factor
     */
    asrFactor(asrParam) {
        const methods = { Standard: 1, Hanafi: 2 };
        return asrParam in methods ? methods[asrParam] : this.eval(asrParam);
    }

    /**
     * Calculate angle for sunrise/sunset
     */
    riseSetAngle(elevation = 0) {
        elevation = elevation === null ? 0 : elevation;
        return 0.833 + 0.0347 * Math.sqrt(elevation);
    }

    /**
     * Apply time offsets
     */
    tuneTimes(times) {
        for (const name in times) {
            times[name] += this.offset[name] / 60.0;
        }
        return times;
    }

    /**
     * Format times according to specified format
     */
    modifyFormats(times) {
        for (const name in times) {
            times[name] = this.getFormattedTime(times[name], this.timeFormat);
        }
        return times;
    }

    /**
     * Adjust times for high latitudes
     */
    adjustHighLats(times) {
        const params = this.settings;
        const nightTime = this.timeDiff(times.sunset, times.sunrise);

        times.imsak = this.adjustHLTime(
            times.imsak, times.sunrise,
            this.eval(params.imsak), nightTime, 'ccw'
        );
        times.fajr = this.adjustHLTime(
            times.fajr, times.sunrise,
            this.eval(params.fajr), nightTime, 'ccw'
        );
        times.isha = this.adjustHLTime(
            times.isha, times.sunset,
            this.eval(params.isha), nightTime
        );
        times.maghrib = this.adjustHLTime(
            times.maghrib, times.sunset,
            this.eval(params.maghrib), nightTime
        );

        return times;
    }

    /**
     * Adjust a specific time for high latitudes
     */
    adjustHLTime(time, base, angle, night, direction = null) {
        const portion = this.nightPortion(angle, night);
        const diff = direction === 'ccw' ?
            this.timeDiff(time, base) :
            this.timeDiff(base, time);

        if (isNaN(time) || diff > portion) {
            time = base + (direction === 'ccw' ? -portion : portion);
        }

        return time;
    }

    /**
     * Calculate portion of night to use
     */
    nightPortion(angle, night) {
        const method = this.settings.highLats;
        let portion = 1 / 2.0;

        if (method === 'AngleBased') {
            portion = (1 / 60.0) * angle;
        }
        if (method === 'OneSeventh') {
            portion = 1 / 7.0;
        }

        return portion * night;
    }

    /**
     * Convert times to day fraction
     */
    dayPortion(times) {
        for (const i in times) {
            times[i] /= 24.0;
        }
        return times;
    }

    /**
     * Format time according to specified format
     */
    getFormattedTime(time, format, suffixes = null) {
        if (isNaN(time)) {
            return this.invalidTime;
        }

        if (format === 'Float') {
            return time;
        }

        if (suffixes === null) {
            suffixes = this.timeSuffixes;
        }

        time = this.fixhour(time + 0.5 / 60);
        const hours = Math.floor(time);
        const minutes = Math.floor((time - hours) * 60);

        const suffix = format === '12h' ? suffixes[hours < 12 ? 0 : 1] : '';

        if (format === '24h') {
            return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}`;
        } else {
            return `${((hours + 11) % 12 + 1)}:${minutes.toString().padStart(2, '0')}${suffix}`;
        }
    }

    /**
     * Calculate time difference
     */
    timeDiff(time1, time2) {
        return this.fixhour(time2 - time1);
    }

    /**
     * Extract numeric value from string
     */
    eval(st) {
        const val = String(st).split(/[^0-9.+-]/)[0];
        return val ? parseFloat(val) : 0;
    }

    /**
     * Check if argument is in minutes
     */
    isMin(arg) {
        return typeof arg === 'string' && arg.indexOf('min') > -1;
    }

    // Trigonometric functions in degrees
    sin(d) {
        return Math.sin(d * Math.PI / 180);
    }

    cos(d) {
        return Math.cos(d * Math.PI / 180);
    }

    tan(d) {
        return Math.tan(d * Math.PI / 180);
    }

    arcsin(x) {
        return Math.asin(x) * 180 / Math.PI;
    }

    arccos(x) {
        return Math.acos(x) * 180 / Math.PI;
    }

    arctan(x) {
        return Math.atan(x) * 180 / Math.PI;
    }

    arccot(x) {
        return Math.atan(1.0 / x) * 180 / Math.PI;
    }

    arctan2(y, x) {
        return Math.atan2(y, x) * 180 / Math.PI;
    }

    fixangle(angle) {
        return this.fix(angle, 360.0);
    }

    fixhour(hour) {
        return this.fix(hour, 24.0);
    }

    fix(a, mode) {
        if (isNaN(a)) {
            return a;
        }
        a = a - mode * Math.floor(a / mode);
        return a < 0 ? a + mode : a;
    }
}

// Export for use in modules and workers
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PrayTimes;
}

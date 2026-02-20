/**
 * Web Worker for Isochrone Calculations
 * Performs heavy computations off the main thread
 */

// Trigonometric functions in degrees
const sin = (d) => Math.sin(d * Math.PI / 180);
const cos = (d) => Math.cos(d * Math.PI / 180);
const tan = (d) => Math.tan(d * Math.PI / 180);
const arcsin = (x) => Math.asin(x) * 180 / Math.PI;
const arccos = (x) => Math.acos(x) * 180 / Math.PI;
const arctan2 = (y, x) => Math.atan2(y, x) * 180 / Math.PI;
const arccot = (x) => Math.atan(1.0 / x) * 180 / Math.PI;

const fixangle = (angle) => {
    angle = angle - 360.0 * Math.floor(angle / 360.0);
    return angle < 0 ? angle + 360.0 : angle;
};

const fixhour = (hour) => {
    hour = hour - 24.0 * Math.floor(hour / 24.0);
    return hour < 0 ? hour + 24.0 : hour;
};

/**
 * Convert date to Julian day
 */
function julian(year, month, day) {
    if (month <= 2) {
        year -= 1;
        month += 12;
    }
    const A = Math.floor(year / 100);
    const B = 2 - A + Math.floor(A / 4);
    return Math.floor(365.25 * (year + 4716)) + Math.floor(30.6001 * (month + 1)) + day + B - 1524.5;
}

/**
 * Calculate sun position (declination and equation of time)
 */
function sunPosition(jd) {
    const D = jd - 2451545.0;
    const g = fixangle(357.529 + 0.98560028 * D);
    const q = fixangle(280.459 + 0.98564736 * D);
    const L = fixangle(q + 1.915 * sin(g) + 0.020 * sin(2 * g));
    const e = 23.439 - 0.00000036 * D;
    const RA = arctan2(cos(e) * sin(L), cos(L)) / 15.0;
    const eqt = q / 15.0 - fixhour(RA);
    const decl = arcsin(sin(e) * sin(L));
    return [decl, eqt];
}

/**
 * Extract numeric value from string
 */
function evalParam(st) {
    if (typeof st === 'number') {
        return st;
    }
    const val = String(st).split(/[^0-9.+-]/)[0];
    return val ? parseFloat(val) : 0;
}

/**
 * Get prayer calculation parameters
 */
function getPrayerParams(prayer, settings) {
    const fajrAngle = evalParam(settings.fajr || 18);
    const ishaAngle = evalParam(settings.isha || 17);
    const maghribAngle = evalParam(settings.maghrib || 0);
    const asrParam = settings.asr || 'Standard';
    const asrFactor = asrParam === 'Standard' ? 1 : (asrParam === 'Hanafi' ? 2 : evalParam(asrParam));

    const config = {
        imsak: [fajrAngle, 'ccw', false, null],  // Same angle as Fajr (offset handled elsewhere)
        fajr: [fajrAngle, 'ccw', false, null],
        sunrise: [0.833, 'ccw', false, null],
        dhuhr: [0, null, false, null],
        asr: [null, 'cw', true, asrFactor],
        sunset: [0.833, 'cw', false, null],
        maghrib: [maghribAngle > 0 ? maghribAngle : 0.833, 'cw', false, null],
        iftar: [maghribAngle > 0 ? maghribAngle : 0.833, 'cw', false, null],  // Same as Maghrib
        isha: [ishaAngle, 'cw', false, null]
    };

    return config[prayer] || null;
}

/**
 * Compute longitude for a single point (fallback method)
 */
function computeLonSingle(lat, targetTime, decl, eqt, tzRef, angle, direction, isAsr, asrFactor) {
    if (isAsr) {
        try {
            angle = -arccot(asrFactor + tan(Math.abs(lat - decl)));
        } catch (e) {
            return null;
        }
    }

    try {
        const cosLat = cos(lat);
        const sinLat = sin(lat);
        const cosDecl = cos(decl);
        const sinDecl = sin(decl);

        if (Math.abs(cosLat) < 1e-10 || Math.abs(cosDecl) < 1e-10) {
            return null;
        }

        const cosH = (-sin(angle) - sinDecl * sinLat) / (cosDecl * cosLat);
        if (Math.abs(cosH) > 1) {
            return null;
        }

        const H = arccos(cosH);
        const baseLon = 15 * (12 - eqt + tzRef - targetTime);

        return direction === 'ccw' ? baseLon - H : baseLon + H;
    } catch (e) {
        return null;
    }
}

/**
 * Compute longitude with JD refinement
 * Uses the same logic as praytimes.py for better precision
 */
function computeLongitude(lat, targetTime, decl, eqt, tzRef, angle, direction, isAsr, asrFactor, jdBase) {
    if (jdBase === null) {
        // Fallback to old method without refinement
        return computeLonSingle(lat, targetTime, decl, eqt, tzRef, angle, direction, isAsr, asrFactor);
    }

    // Convert targetTime to day fraction for JD adjustment
    const timeFraction = targetTime / 24.0;

    // Iterate to refine (like praytimes.numIterations)
    for (let iter = 0; iter < 2; iter++) {
        // JD adjusted by target time (like jDate + time in praytimes)
        const jdAdj = jdBase + timeFraction;
        const [newDecl, newEqt] = sunPosition(jdAdj);

        // Dhuhr case - vertical lines
        if (direction === null) {
            const lon = 15 * (12 - newEqt + tzRef - targetTime);
            return lon;
        }

        // Calculate angle for Asr if needed
        let effectiveAngle = angle;
        if (isAsr) {
            try {
                effectiveAngle = -arccot(asrFactor + tan(Math.abs(lat - newDecl)));
            } catch (e) {
                return null;
            }
        }

        try {
            const cosLat = cos(lat);
            const sinLat = sin(lat);
            const cosDecl = cos(newDecl);
            const sinDecl = sin(newDecl);

            if (Math.abs(cosLat) < 1e-10 || Math.abs(cosDecl) < 1e-10) {
                return null;
            }

            const cosH = (-sin(effectiveAngle) - sinDecl * sinLat) / (cosDecl * cosLat);
            if (Math.abs(cosH) > 1) {
                return null;
            }

            // t in hours (like praytimes.sunAngleTime)
            const t = arccos(cosH) / 15.0;

            // noon in hours (like praytimes.midDay)
            const noon = fixhour(12 - newEqt);

            // Prayer time in local solar time
            const prayerTimeSolar = direction === 'cw' ? noon + t : noon - t;

            // Calculate longitude where this prayer = targetTime
            // prayer_time_local = prayer_time_solar + (tz - lon/15)
            // targetTime = prayer_time_solar + tz - lon/15
            // lon = 15 * (prayer_time_solar + tz - targetTime)
            const lon = 15 * (prayerTimeSolar + tzRef - targetTime);

            return lon;

        } catch (e) {
            return null;
        }
    }

    return null;
}

/**
 * Format time as HH:MM
 */
function formatTime(minutes) {
    const hours = Math.floor(minutes / 60) % 24;
    const mins = Math.floor(minutes % 60);
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

/**
 * Generate isochrone bands for a prayer
 */
/**
 * Check if parameter is in minutes
 */
function isMin(arg) {
    return typeof arg === 'string' && arg.indexOf('min') > -1;
}

function generateIsochrones(params) {
    const {
        prayer,
        bounds,
        date,
        timezone,
        settings,
        numLatPoints = 200
    } = params;

    const { minLon, maxLon, minLat, maxLat } = bounds;

    // Get prayer parameters
    const prayerParams = getPrayerParams(prayer, settings);
    if (!prayerParams) {
        return { error: 'Invalid prayer name' };
    }

    const [angle, direction, isAsr, asrFactor] = prayerParams;

    // Time offset for Imsak (Imsak = Fajr - offset, so we add offset to target time)
    let timeOffset = 0;
    if (prayer === 'imsak') {
        const imsakParam = settings.imsak || '10 min';
        if (isMin(imsakParam)) {
            timeOffset = evalParam(imsakParam) / 60.0;  // Convert to hours
        }
    }

    // Calculate Julian date
    const jd = julian(date[0], date[1], date[2]);
    const [decl, eqt] = sunPosition(jd);

    // Sample to find time range
    const sampleTimes = [];
    for (let lat = minLat; lat <= maxLat; lat += (maxLat - minLat) / 10) {
        for (let lon = minLon; lon <= maxLon; lon += (maxLon - minLon) / 10) {
            // Calculate time at this point using simple formula
            const sampleLon = computeLongitude(lat, 12, decl, eqt, timezone, angle, direction, isAsr, asrFactor, jd);
            if (sampleLon !== null) {
                // Reverse to get time from longitude
                // This is approximate but good enough for range finding
                const baseTime = 12 - eqt + timezone - lon / 15;

                if (direction === null) {
                    // For Imsak, subtract offset to get actual Imsak time (not Fajr time)
                    sampleTimes.push((baseTime - timeOffset) * 60);
                } else {
                    try {
                        const cosLat = cos(lat);
                        const sinLat = sin(lat);
                        const cosDecl = cos(decl);
                        const sinDecl = sin(decl);

                        let effectiveAngle = angle;
                        if (isAsr) {
                            effectiveAngle = -arccot(asrFactor + tan(Math.abs(lat - decl)));
                        }

                        const cosH = (-sin(effectiveAngle) - sinDecl * sinLat) / (cosDecl * cosLat);
                        if (Math.abs(cosH) <= 1) {
                            const H = arccos(cosH);
                            const time = direction === 'ccw' ? baseTime - H / 15 : baseTime + H / 15;
                            // For Imsak, subtract offset to get actual Imsak time (not Fajr time)
                            sampleTimes.push((time - timeOffset) * 60);
                        }
                    } catch (e) {
                        // Skip invalid points
                    }
                }
            }
        }
    }

    if (sampleTimes.length === 0) {
        return { error: 'No valid sample times' };
    }

    const minTime = Math.min(...sampleTimes) - 2;
    const maxTime = Math.max(...sampleTimes) + 2;
    const minutesList = [];
    for (let m = Math.floor(minTime); m <= Math.ceil(maxTime); m++) {
        minutesList.push(m);
    }

    if (minutesList.length < 2) {
        return { error: 'Time range too small' };
    }

    // Generate latitude points
    const lats = [];
    for (let i = 0; i < numLatPoints; i++) {
        lats.push(minLat + (maxLat - minLat) * i / (numLatPoints - 1));
    }

    // Generate bands
    const bands = [];
    const colors = [
        '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5',
        '#2196F3', '#1E88E5', '#1976D2', '#1565C0', '#0D47A1'
    ];

    for (let idx = 0; idx < minutesList.length; idx++) {
        const targetMinute = minutesList[idx];
        // Apply time offset for Imsak
        const timeLow = (targetMinute - 0.5) / 60.0 + timeOffset;
        const timeHigh = (targetMinute + 0.5) / 60.0 + timeOffset;

        const curveLow = [];
        const curveHigh = [];

        for (const lat of lats) {
            const lonLow = computeLongitude(lat, timeLow, decl, eqt, timezone, angle, direction, isAsr, asrFactor, jd);
            if (lonLow !== null && lonLow >= minLon && lonLow <= maxLon) {
                curveLow.push([lonLow, lat]);
            }

            const lonHigh = computeLongitude(lat, timeHigh, decl, eqt, timezone, angle, direction, isAsr, asrFactor, jd);
            if (lonHigh !== null && lonHigh >= minLon && lonHigh <= maxLon) {
                curveHigh.push([lonHigh, lat]);
            }
        }

        if (curveLow.length >= 2 && curveHigh.length >= 2) {
            // Create polygon from low and high curves
            const polygon = [...curveLow, ...curveHigh.reverse()];
            polygon.push(polygon[0]); // Close the polygon

            // Calculate label position (center of all points)
            const allPoints = [...curveLow, ...curveHigh];
            const centerLon = allPoints.reduce((sum, p) => sum + p[0], 0) / allPoints.length;
            const centerLat = allPoints.reduce((sum, p) => sum + p[1], 0) / allPoints.length;

            // Check if label is within margins
            const marginLon = 0.05 * (maxLon - minLon);
            const marginLat = 0.05 * (maxLat - minLat);

            let labelPos = null;
            let label = null;

            if (centerLon >= minLon + marginLon && centerLon <= maxLon - marginLon &&
                centerLat >= minLat + marginLat && centerLat <= maxLat - marginLat) {
                labelPos = [centerLon, centerLat];
                label = formatTime(targetMinute);
            }

            bands.push({
                polygon,
                label,
                labelPos,
                minute: targetMinute,
                color: colors[idx % colors.length]
            });
        }
    }

    return { bands };
}

// Handle messages from main thread
self.onmessage = function(e) {
    const { type, params, id } = e.data;

    if (type === 'generateIsochrones') {
        try {
            const result = generateIsochrones(params);
            self.postMessage({ type: 'result', id, result });
        } catch (error) {
            self.postMessage({ type: 'error', id, error: error.message });
        }
    }
};

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
        fajr: [fajrAngle, 'ccw', false, null],
        sunrise: [0.833, 'ccw', false, null],
        dhuhr: [0, null, false, null],
        asr: [null, 'cw', true, asrFactor],
        sunset: [0.833, 'cw', false, null],
        maghrib: [maghribAngle > 0 ? maghribAngle : 0.833, 'cw', false, null],
        isha: [ishaAngle, 'cw', false, null]
    };

    return config[prayer] || null;
}

/**
 * Compute longitude for a single point
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
 */
function computeLongitude(lat, targetTime, decl, eqt, tzRef, angle, direction, isAsr, asrFactor, jdBase) {
    // Dhuhr case - vertical lines
    if (direction === null) {
        let lon = 15 * (12 - eqt + tzRef - targetTime);
        if (jdBase !== null) {
            for (let i = 0; i < 2; i++) {
                const jdAdj = jdBase - lon / (15 * 24.0);
                const [newDecl, newEqt] = sunPosition(jdAdj);
                lon = 15 * (12 - newEqt + tzRef - targetTime);
            }
        }
        return lon;
    }

    let lon = computeLonSingle(lat, targetTime, decl, eqt, tzRef, angle, direction, isAsr, asrFactor);
    if (lon === null) {
        return null;
    }

    // Refine with JD iteration
    if (jdBase !== null) {
        for (let i = 0; i < 2; i++) {
            const jdAdj = jdBase - lon / (15 * 24.0);
            const [newDecl, newEqt] = sunPosition(jdAdj);
            const lonNew = computeLonSingle(lat, targetTime, newDecl, newEqt, tzRef, angle, direction, isAsr, asrFactor);
            if (lonNew === null) {
                return lon;
            }
            lon = lonNew;
        }
    }

    return lon;
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
                    sampleTimes.push(baseTime * 60);
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
                            sampleTimes.push(time * 60);
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
        const timeLow = (targetMinute - 0.5) / 60.0;
        const timeHigh = (targetMinute + 0.5) / 60.0;

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

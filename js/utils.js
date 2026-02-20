/**
 * Utility functions for Mawaquit web application
 */

/**
 * Debounce function - limits the rate at which a function can fire
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function}
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function - ensures a function is called at most once in a specified time period
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function}
 */
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func(...args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Format a date as YYYY-MM-DD
 * @param {Date} date
 * @returns {string}
 */
function formatDate(date) {
    const yyyy = date.getFullYear();
    const mm = String(date.getMonth() + 1).padStart(2, '0');
    const dd = String(date.getDate()).padStart(2, '0');
    return `${yyyy}-${mm}-${dd}`;
}

/**
 * Parse a date string (YYYY-MM-DD) to [year, month, day] array
 * @param {string} dateStr
 * @returns {Array}
 */
function parseDate(dateStr) {
    const [year, month, day] = dateStr.split('-').map(Number);
    return [year, month, day];
}

/**
 * Format time in minutes to HH:MM string
 * @param {number} minutes
 * @returns {string}
 */
function formatTime(minutes) {
    const hours = Math.floor(minutes / 60) % 24;
    const mins = Math.floor(minutes % 60);
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
}

/**
 * Clamp a value between min and max
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
function clamp(value, min, max) {
    return Math.min(Math.max(value, min), max);
}

/**
 * Linear interpolation
 * @param {number} a - Start value
 * @param {number} b - End value
 * @param {number} t - Interpolation factor (0-1)
 * @returns {number}
 */
function lerp(a, b, t) {
    return a + (b - a) * t;
}

/**
 * Check if a value is within a range
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {boolean}
 */
function inRange(value, min, max) {
    return value >= min && value <= max;
}

/**
 * Deep clone an object
 * @param {Object} obj
 * @returns {Object}
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Generate a simple unique ID
 * @returns {string}
 */
function generateId() {
    return Math.random().toString(36).substr(2, 9);
}

/**
 * Sleep for a specified duration
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise}
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Check if running on mobile device
 * @returns {boolean}
 */
function isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
}

/**
 * Get query parameter from URL
 * @param {string} name
 * @returns {string|null}
 */
function getQueryParam(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

/**
 * Calculate distance between two points (Haversine formula)
 * @param {number} lat1
 * @param {number} lon1
 * @param {number} lat2
 * @param {number} lon2
 * @returns {number} Distance in kilometers
 */
function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat / 2) * Math.sin(dLat / 2) +
              Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
              Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
}

/**
 * Convert degrees to radians
 * @param {number} degrees
 * @returns {number}
 */
function toRadians(degrees) {
    return degrees * Math.PI / 180;
}

/**
 * Convert radians to degrees
 * @param {number} radians
 * @returns {number}
 */
function toDegrees(radians) {
    return radians * 180 / Math.PI;
}

/**
 * Clip isochrone bands by country boundary using Turf.js
 * @param {Array} bands - Array of band objects with polygons
 * @param {Object} countryGeoJSON - Country GeoJSON (level 0)
 * @returns {Array} Clipped bands
 */
function clipIsochrones(bands, countryGeoJSON) {
    if (!countryGeoJSON || !bands || bands.length === 0) {
        return bands;
    }

    // Check if turf is available
    if (typeof turf === 'undefined') {
        console.warn('Turf.js not loaded, skipping clipping');
        return bands;
    }

    try {
        // Get country geometry (handle FeatureCollection or single Feature)
        let countryFeature;
        if (countryGeoJSON.type === 'FeatureCollection') {
            // Merge all features into one MultiPolygon if needed
            const features = countryGeoJSON.features;
            if (features.length === 1) {
                countryFeature = features[0];
            } else {
                // Combine multiple features
                countryFeature = turf.combine(turf.featureCollection(features));
                if (countryFeature.features) {
                    countryFeature = countryFeature.features[0];
                }
            }
        } else if (countryGeoJSON.type === 'Feature') {
            countryFeature = countryGeoJSON;
        } else {
            countryFeature = turf.feature(countryGeoJSON);
        }

        const clippedBands = [];

        for (const band of bands) {
            if (!band.polygon || band.polygon.length < 4) {
                continue;
            }

            try {
                // Create polygon from band coordinates [lon, lat]
                // Ensure the polygon is closed
                const coords = [...band.polygon];
                if (coords[0][0] !== coords[coords.length - 1][0] ||
                    coords[0][1] !== coords[coords.length - 1][1]) {
                    coords.push(coords[0]);
                }

                const bandPolygon = turf.polygon([coords]);

                // Intersect with country boundary
                const clipped = turf.intersect(bandPolygon, countryFeature);

                if (clipped) {
                    // Handle different geometry types from intersection
                    const geomType = clipped.geometry.type;

                    if (geomType === 'Polygon') {
                        // Single polygon result
                        clippedBands.push({
                            ...band,
                            polygon: clipped.geometry.coordinates[0]
                        });
                    } else if (geomType === 'MultiPolygon') {
                        // Multiple polygons - create a band for each
                        for (const polyCoords of clipped.geometry.coordinates) {
                            clippedBands.push({
                                ...band,
                                polygon: polyCoords[0],
                                // Only keep label on first polygon
                                label: clippedBands.length === 0 ||
                                       clippedBands[clippedBands.length - 1].minute !== band.minute
                                       ? band.label : null,
                                labelPos: clippedBands.length === 0 ||
                                          clippedBands[clippedBands.length - 1].minute !== band.minute
                                          ? band.labelPos : null
                            });
                        }
                    } else if (geomType === 'GeometryCollection') {
                        // Extract polygons from collection
                        let firstForMinute = true;
                        for (const geom of clipped.geometry.geometries) {
                            if (geom.type === 'Polygon') {
                                clippedBands.push({
                                    ...band,
                                    polygon: geom.coordinates[0],
                                    label: firstForMinute ? band.label : null,
                                    labelPos: firstForMinute ? band.labelPos : null
                                });
                                firstForMinute = false;
                            } else if (geom.type === 'MultiPolygon') {
                                for (const polyCoords of geom.coordinates) {
                                    clippedBands.push({
                                        ...band,
                                        polygon: polyCoords[0],
                                        label: firstForMinute ? band.label : null,
                                        labelPos: firstForMinute ? band.labelPos : null
                                    });
                                    firstForMinute = false;
                                }
                            }
                        }
                    }
                }
            } catch (e) {
                // If clipping fails for a band, keep the original
                console.warn('Clipping failed for band:', e.message);
                clippedBands.push(band);
            }
        }

        return clippedBands;

    } catch (error) {
        console.error('Error in clipIsochrones:', error);
        return bands;
    }
}

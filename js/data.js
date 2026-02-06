/**
 * DataManager - Handles loading and caching of geographic data
 */

class DataManager {
    constructor() {
        // In-memory cache for GeoJSON data
        this.cache = new Map();
        this.countriesData = null;
        // Local GADM data path (simplified and hosted locally)
        this.gadmLocalPath = 'data/gadm';
    }

    /**
     * Load countries metadata from local JSON file
     * @returns {Promise<Array>} Array of country objects
     */
    async loadCountries() {
        if (this.countriesData) {
            return this.countriesData;
        }

        try {
            const response = await fetch('data/countries.json');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            this.countriesData = data.countries;
            return this.countriesData;
        } catch (error) {
            console.error('Error loading countries data:', error);
            throw error;
        }
    }

    /**
     * Get country by name
     * @param {string} name - Country name
     * @returns {Object|null} Country object or null
     */
    getCountryByName(name) {
        if (!this.countriesData) {
            return null;
        }
        return this.countriesData.find(c => c.name === name) || null;
    }

    /**
     * Build local GADM URL for a country and level
     * @param {string} countryCode - ISO 3-letter country code
     * @param {number} level - Administrative level (0 or 1)
     * @returns {string} URL
     */
    buildGadmUrl(countryCode, level) {
        return `${this.gadmLocalPath}/${countryCode}_${level}.json`;
    }

    /**
     * Get cache key for a country/level combination
     * @param {string} countryCode
     * @param {number} level
     * @returns {string}
     */
    getCacheKey(countryCode, level) {
        return `${countryCode}_${level}`;
    }

    /**
     * Load GADM GeoJSON data for a country
     * @param {string} countryCode - ISO 3-letter country code
     * @param {number} level - Administrative level (0 or 1)
     * @param {Function} onProgress - Progress callback
     * @returns {Promise<Object>} GeoJSON data
     */
    async loadGadmData(countryCode, level, onProgress = null) {
        const cacheKey = this.getCacheKey(countryCode, level);

        // Check cache first
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        const url = this.buildGadmUrl(countryCode, level);

        if (onProgress) {
            onProgress(`Loading ${countryCode} level ${level}...`);
        }

        try {
            const response = await fetch(url);

            if (!response.ok) {
                if (response.status === 404) {
                    // Level not available for this country
                    return null;
                }
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();

            // Cache the data
            this.cache.set(cacheKey, data);

            return data;
        } catch (error) {
            console.error(`Error loading GADM data for ${countryCode} level ${level}:`, error);
            throw error;
        }
    }

    /**
     * Load multiple GADM levels for a country
     * @param {string} countryCode - ISO 3-letter country code
     * @param {Array<number>} levels - Array of levels to load
     * @param {Function} onProgress - Progress callback
     * @returns {Promise<Object>} Object with level keys and GeoJSON values
     */
    async loadCountryData(countryCode, levels = [0, 1], onProgress = null) {
        const result = {};

        for (const level of levels) {
            try {
                const data = await this.loadGadmData(countryCode, level, onProgress);
                if (data) {
                    result[level] = data;
                }
            } catch (error) {
                console.warn(`Could not load level ${level} for ${countryCode}`);
            }
        }

        return result;
    }

    /**
     * Calculate bounds from GeoJSON data
     * @param {Object} geojson - GeoJSON object
     * @returns {Object} Bounds object with minLon, minLat, maxLon, maxLat
     */
    calculateBounds(geojson) {
        let minLon = Infinity;
        let minLat = Infinity;
        let maxLon = -Infinity;
        let maxLat = -Infinity;

        const processCoords = (coords) => {
            if (typeof coords[0] === 'number') {
                // This is a coordinate [lon, lat]
                minLon = Math.min(minLon, coords[0]);
                maxLon = Math.max(maxLon, coords[0]);
                minLat = Math.min(minLat, coords[1]);
                maxLat = Math.max(maxLat, coords[1]);
            } else {
                // This is an array of coordinates or nested arrays
                coords.forEach(processCoords);
            }
        };

        if (geojson.features) {
            geojson.features.forEach(feature => {
                if (feature.geometry && feature.geometry.coordinates) {
                    processCoords(feature.geometry.coordinates);
                }
            });
        } else if (geojson.geometry && geojson.geometry.coordinates) {
            processCoords(geojson.geometry.coordinates);
        }

        return { minLon, minLat, maxLon, maxLat };
    }

    /**
     * Clear all cached data
     */
    clearCache() {
        this.cache.clear();
    }

    /**
     * Get cache size
     * @returns {number}
     */
    getCacheSize() {
        return this.cache.size;
    }
}

// Create global instance
const dataManager = new DataManager();

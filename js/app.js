/**
 * Mawaquit Web Application - Main Entry Point
 * Orchestrates all modules and manages application state
 */

class MawaquitApp {
    constructor() {
        // Application state
        this.state = {
            currentCountry: null,
            currentTimezone: 0,
            markerPosition: null,
            countryData: {},
            activeIsochrone: null,
            lastClippedBands: null
        };

        // Module instances
        this.prayCalc = new PrayTimes('MWL');

        // Initialize on DOM ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            // Initialize UI manager
            uiManager = new UIManager();
            this.setupUICallbacks();

            // Initialize map
            mapManager = new MapManager('map');
            mapManager.init();
            mapManager.setClickHandler(this.onMapClick.bind(this));

            // Load countries data
            uiManager.showLoading('Loading countries...');
            const countries = await dataManager.loadCountries();
            uiManager.populateCountries(countries);

            uiManager.hideLoading();
            uiManager.setStatus('Ready. Select a country to begin.', 'info');

            // Disable isochrone buttons until country is loaded
            uiManager.setIsoButtonsEnabled(false);

        } catch (error) {
            console.error('Initialization error:', error);
            uiManager.hideLoading();
            uiManager.setStatus('Error initializing application: ' + error.message, 'error');
        }
    }

    /**
     * Setup UI callback handlers
     */
    setupUICallbacks() {
        uiManager.onCountryChange = this.onCountryChange.bind(this);
        uiManager.onMethodChange = this.onMethodChange.bind(this);
        uiManager.onDateChange = this.onDateChange.bind(this);
        uiManager.onLevel2Toggle = this.onLevel2Toggle.bind(this);
        uiManager.onIsochroneRequest = this.onIsochroneRequest.bind(this);
        uiManager.onClearIsochrones = this.onClearIsochrones.bind(this);
        uiManager.onExportRequest = this.onExportRequest.bind(this);
    }

    /**
     * Handle country selection change
     */
    async onCountryChange(countryName) {
        if (!countryName) return;

        try {
            uiManager.showLoading(`Loading ${countryName}...`);

            // Get country metadata
            const country = dataManager.getCountryByName(countryName);
            if (!country) {
                throw new Error('Country not found');
            }

            this.state.currentCountry = country;
            this.state.currentTimezone = country.timezone;

            // Load GADM data
            const levels = uiManager.isLevel2Enabled() ? [0, 1, 2] : [0, 1];
            const data = await dataManager.loadCountryData(
                country.code,
                levels,
                (msg) => uiManager.showLoading(msg)
            );

            this.state.countryData = data;

            // Check if country data was loaded successfully
            if (!data[0]) {
                throw new Error('Failed to load country boundaries. Please try again.');
            }

            // Display on map
            mapManager.loadCountry(data[0], data[1]);

            if (uiManager.isLevel2Enabled() && data[2]) {
                mapManager.toggleLevel2(data[2], true);
            }

            // Reset marker and prayer times
            this.state.markerPosition = null;
            mapManager.clearMarker();
            uiManager.resetCoordinates();
            uiManager.resetPrayerTimes();

            // Clear isochrones
            this.onClearIsochrones();

            // Enable isochrone buttons and export
            uiManager.setIsoButtonsEnabled(true);
            uiManager.setExportEnabled(true);

            uiManager.hideLoading();
            uiManager.setStatus(`${countryName} loaded. Click on the map to get prayer times.`, 'success');

        } catch (error) {
            console.error('Error loading country:', error);
            uiManager.hideLoading();
            uiManager.setStatus('Error loading country: ' + error.message, 'error');
            uiManager.setIsoButtonsEnabled(false);
            uiManager.setExportEnabled(false);
        }
    }

    /**
     * Handle calculation method change
     */
    onMethodChange(method) {
        this.prayCalc = new PrayTimes(method);

        // Recalculate prayer times if marker is placed
        if (this.state.markerPosition) {
            this.updatePrayerTimes();
        }

        uiManager.setStatus(`Calculation method changed to ${PrayTimes.methods[method].name}`, 'info');
    }

    /**
     * Handle date change
     */
    onDateChange(date) {
        // Recalculate prayer times if marker is placed
        if (this.state.markerPosition) {
            this.updatePrayerTimes();
        }

        // If isochrones are displayed, offer to refresh them
        if (this.state.activeIsochrone) {
            this.onIsochroneRequest(this.state.activeIsochrone);
        }
    }

    /**
     * Handle level 2 toggle
     */
    async onLevel2Toggle(enabled) {
        if (!this.state.currentCountry) return;

        try {
            if (enabled) {
                // Load level 2 if not already loaded
                if (!this.state.countryData[2]) {
                    uiManager.showLoading('Loading administrative level 2...');
                    const data = await dataManager.loadGadmData(
                        this.state.currentCountry.code,
                        2
                    );
                    this.state.countryData[2] = data;
                    uiManager.hideLoading();
                }

                mapManager.toggleLevel2(this.state.countryData[2], true);
                uiManager.setStatus('Administrative level 2 enabled', 'info');
            } else {
                mapManager.toggleLevel2(null, false);
                uiManager.setStatus('Administrative level 2 disabled', 'info');
            }
        } catch (error) {
            console.error('Error toggling level 2:', error);
            uiManager.hideLoading();
            uiManager.setStatus('Level 2 data not available for this country', 'warning');
        }
    }

    /**
     * Handle map click
     */
    onMapClick(lat, lng) {
        // Check if click is within country bounds
        if (!mapManager.isPointInBounds(lat, lng)) {
            return;
        }

        this.state.markerPosition = { lat, lng };
        mapManager.setMarker(lat, lng);
        uiManager.updateCoordinates(lat, lng);

        this.updatePrayerTimes();
    }

    /**
     * Update prayer times display
     */
    updatePrayerTimes() {
        if (!this.state.markerPosition) return;

        const { lat, lng } = this.state.markerPosition;
        const date = uiManager.getDate();
        const method = uiManager.getSelectedMethod();

        // Ensure we're using the selected method
        if (this.prayCalc.calcMethod !== method) {
            this.prayCalc = new PrayTimes(method);
        }

        const times = this.prayCalc.getTimes(
            date,
            [lat, lng, 0],
            this.state.currentTimezone,
            0,
            '24h'
        );

        uiManager.updatePrayerTimes(times);
    }

    /**
     * Clip isochrone bands to country boundaries using Turf.js
     * @param {Array} bands - Raw bands from worker
     * @param {Object} countryGeojson - Level 0 GeoJSON (country outline)
     * @returns {Array} Clipped bands with GeoJSON geometry
     */
    clipBands(bands, countryGeojson) {
        if (!countryGeojson || typeof turf === 'undefined') {
            return bands;
        }

        // Build a single country geometry (union of all features)
        let countryFeature;
        if (countryGeojson.type === 'FeatureCollection' && countryGeojson.features.length > 0) {
            if (countryGeojson.features.length === 1) {
                countryFeature = countryGeojson.features[0];
            } else {
                // Union all features into one
                countryFeature = countryGeojson.features[0];
                for (let i = 1; i < countryGeojson.features.length; i++) {
                    try {
                        countryFeature = turf.union(
                            turf.featureCollection([countryFeature, countryGeojson.features[i]])
                        );
                    } catch (e) {
                        // Skip invalid features
                    }
                }
            }
        } else if (countryGeojson.type === 'Feature') {
            countryFeature = countryGeojson;
        } else {
            return bands;
        }

        const clippedBands = [];

        for (let i = 0; i < bands.length; i++) {
            const band = bands[i];
            if (!band.polygon || band.polygon.length < 4) continue;

            try {
                // Create a Turf polygon from the band coordinates [lon, lat]
                const bandFeature = turf.polygon([band.polygon]);

                // Intersect with country
                const clipped = turf.intersect(
                    turf.featureCollection([bandFeature, countryFeature])
                );

                if (!clipped || !clipped.geometry) continue;

                // Compute centroid for label placement
                const centroid = turf.centroid(clipped);
                const labelPos = centroid.geometry.coordinates; // [lon, lat]

                clippedBands.push({
                    geometry: clipped.geometry,
                    label: band.label,
                    labelPos: labelPos,
                    minute: band.minute,
                    color: band.color
                });
            } catch (e) {
                // Fallback: use original band if clipping fails
                clippedBands.push(band);
            }
        }

        return clippedBands;
    }

    /**
     * Handle isochrone request
     */
    async onIsochroneRequest(prayer) {
        if (!this.state.currentCountry) {
            uiManager.setStatus('Please select a country first', 'warning');
            return;
        }

        try {
            uiManager.showLoading(`Calculating ${prayer} isochrones...`);
            uiManager.setActiveIsoButton(prayer);

            const bounds = mapManager.getBoundsObject();
            if (!bounds) {
                throw new Error('No country bounds available');
            }

            const date = uiManager.getDate();
            const settings = {
                fajr: this.prayCalc.settings.fajr,
                isha: this.prayCalc.settings.isha,
                maghrib: this.prayCalc.settings.maghrib,
                asr: this.prayCalc.settings.asr
            };

            const result = await isochroneGenerator.generate(
                prayer,
                bounds,
                date,
                this.state.currentTimezone,
                settings
            );

            if (result.error) {
                throw new Error(result.error);
            }

            // Clip bands to country boundaries
            const countryGeojson = this.state.countryData[0];
            const clippedBands = this.clipBands(result.bands, countryGeojson);

            mapManager.drawIsochrones(clippedBands);
            this.state.activeIsochrone = prayer;
            this.state.lastClippedBands = clippedBands;

            uiManager.hideLoading();
            uiManager.setStatus(`${prayer.charAt(0).toUpperCase() + prayer.slice(1)} isochrones displayed`, 'success');

            // Update export isochrone option
            if (uiManager.updateExportIsoOption) {
                uiManager.updateExportIsoOption(prayer);
            }

        } catch (error) {
            console.error('Error generating isochrones:', error);
            uiManager.hideLoading();
            uiManager.setActiveIsoButton(null);
            uiManager.setStatus('Error generating isochrones: ' + error.message, 'error');
        }
    }

    /**
     * Handle clear isochrones
     */
    onClearIsochrones() {
        mapManager.clearIsochrones();
        this.state.activeIsochrone = null;
        this.state.lastClippedBands = null;
        uiManager.setActiveIsoButton(null);
        uiManager.setStatus('Isochrone curves cleared', 'info');

        // Update export isochrone option
        if (uiManager.updateExportIsoOption) {
            uiManager.updateExportIsoOption(null);
        }
    }

    /**
     * Handle export request
     * @param {Object} layers - { borders, provinces, isochrones }
     */
    onExportRequest(layers) {
        if (!this.state.currentCountry) return;

        const countryName = this.state.currentCountry.name;
        const dateStr = uiManager.getDate().join('-');
        let exported = 0;

        if (layers.borders && this.state.countryData[0]) {
            this.downloadGeoJSON(this.state.countryData[0], `${countryName}_${dateStr}_borders.geojson`);
            exported++;
        }

        if (layers.provinces && this.state.countryData[1]) {
            this.downloadGeoJSON(this.state.countryData[1], `${countryName}_${dateStr}_provinces.geojson`);
            exported++;
        }

        if (layers.isochrones && this.state.lastClippedBands && this.state.activeIsochrone) {
            const geojson = this.bandsToGeoJSON(this.state.lastClippedBands);
            this.downloadGeoJSON(geojson, `${countryName}_${dateStr}_isochrones_${this.state.activeIsochrone}.geojson`);
            exported++;
        }

        if (exported > 0) {
            uiManager.setStatus(`${exported} GeoJSON file(s) exported`, 'success');
        } else {
            uiManager.setStatus('No layers selected for export', 'warning');
        }
    }

    /**
     * Convert clipped bands to a GeoJSON FeatureCollection
     * @param {Array} bands - Clipped bands
     * @returns {Object} GeoJSON FeatureCollection
     */
    bandsToGeoJSON(bands) {
        const features = bands.map((band, index) => {
            let geometry;
            if (band.geometry) {
                geometry = band.geometry;
            } else if (band.polygon) {
                geometry = {
                    type: 'Polygon',
                    coordinates: [band.polygon]
                };
            } else {
                return null;
            }

            return {
                type: 'Feature',
                geometry,
                properties: {
                    minute: band.minute,
                    label: band.label || '',
                    band_index: index
                }
            };
        }).filter(f => f !== null);

        return {
            type: 'FeatureCollection',
            features
        };
    }

    /**
     * Download a GeoJSON object as a file
     * @param {Object} geojson - GeoJSON object
     * @param {string} filename - File name
     */
    downloadGeoJSON(geojson, filename) {
        const blob = new Blob([JSON.stringify(geojson)], { type: 'application/geo+json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
}

// Create and start the application
const app = new MawaquitApp();

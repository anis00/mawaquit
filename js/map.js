/**
 * MapManager - Handles Leaflet map initialization and interactions
 */

class MapManager {
    constructor(containerId) {
        this.containerId = containerId;
        this.map = null;
        this.countryLayer = null;
        this.level1Layer = null;
        this.level2Layer = null;
        this.isochroneLayers = [];
        this.isochroneLabels = [];  // Separate array for labels
        this.isochroneBands = [];   // Store band data for dynamic label repositioning
        this.marker = null;
        this.bounds = null;
        this.maxZoom = 12;
        this.minZoom = 2;

        // Isochrone colors - two alternating shades of blue
        this.isochroneColors = ['#90CAF9', '#1E88E5'];  // Light blue, Dark blue

        this.onMapClick = null;
        this._updateLabelsHandler = null;
    }

    /**
     * Initialize the Leaflet map
     */
    init() {
        // Create map centered on world
        this.map = L.map(this.containerId, {
            center: [30, 0],
            zoom: 2,
            minZoom: this.minZoom,
            maxZoom: this.maxZoom,
            worldCopyJump: true
        });

        // Add OpenStreetMap tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(this.map);

        // Set up click handler
        this.map.on('click', (e) => {
            if (this.onMapClick) {
                this.onMapClick(e.latlng.lat, e.latlng.lng);
            }
        });

        // Set up handler for dynamic label repositioning
        this._updateLabelsHandler = this._updateLabelPositions.bind(this);
        this.map.on('moveend', this._updateLabelsHandler);
        this.map.on('zoomend', this._updateLabelsHandler);

        return this;
    }

    /**
     * Set map click callback
     * @param {Function} callback - Function to call on map click (lat, lng)
     */
    setClickHandler(callback) {
        this.onMapClick = callback;
    }

    /**
     * Load and display country boundaries
     * @param {Object} geojsonLevel0 - Level 0 GeoJSON (country outline)
     * @param {Object} geojsonLevel1 - Level 1 GeoJSON (provinces/states)
     */
    loadCountry(geojsonLevel0, geojsonLevel1 = null) {
        // Clear existing layers
        this.clearCountryLayers();

        // Add country boundary (level 0)
        if (geojsonLevel0) {
            this.countryLayer = L.geoJSON(geojsonLevel0, {
                style: {
                    color: '#1a237e',
                    weight: 2,
                    fillColor: '#bbdefb',
                    fillOpacity: 0.3
                }
            }).addTo(this.map);

            // Fit map to country bounds
            this.bounds = this.countryLayer.getBounds();
            this.map.fitBounds(this.bounds, { padding: [20, 20] });

            // Constrain panning to country bounds (with padding)
            const paddedBounds = this.bounds.pad(0.5);
            this.map.setMaxBounds(paddedBounds);
        }

        // Add level 1 boundaries (provinces/states)
        if (geojsonLevel1) {
            this.level1Layer = L.geoJSON(geojsonLevel1, {
                style: {
                    color: '#8b0000',
                    weight: 0.8,
                    fillOpacity: 0,
                    opacity: 0.6
                }
            }).addTo(this.map);
        }
    }

    /**
     * Toggle level 2 administrative boundaries
     * @param {Object} geojsonLevel2 - Level 2 GeoJSON data
     * @param {boolean} show - Whether to show or hide
     */
    toggleLevel2(geojsonLevel2, show) {
        if (this.level2Layer) {
            this.map.removeLayer(this.level2Layer);
            this.level2Layer = null;
        }

        if (show && geojsonLevel2) {
            this.level2Layer = L.geoJSON(geojsonLevel2, {
                style: {
                    color: '#228b22',
                    weight: 0.4,
                    fillOpacity: 0,
                    opacity: 0.4,
                    dashArray: '5, 5'
                }
            }).addTo(this.map);
        }
    }

    /**
     * Clear all country-related layers
     */
    clearCountryLayers() {
        if (this.countryLayer) {
            this.map.removeLayer(this.countryLayer);
            this.countryLayer = null;
        }
        if (this.level1Layer) {
            this.map.removeLayer(this.level1Layer);
            this.level1Layer = null;
        }
        if (this.level2Layer) {
            this.map.removeLayer(this.level2Layer);
            this.level2Layer = null;
        }
        this.bounds = null;
        this.map.setMaxBounds(null);
    }

    /**
     * Place or move marker on map
     * @param {number} lat - Latitude
     * @param {number} lng - Longitude
     */
    setMarker(lat, lng) {
        if (this.marker) {
            this.marker.setLatLng([lat, lng]);
        } else {
            // Create custom marker icon
            const icon = L.divIcon({
                className: 'marker-icon',
                html: '<div class="marker-cross"></div>',
                iconSize: [20, 20],
                iconAnchor: [10, 10]
            });

            this.marker = L.marker([lat, lng], { icon }).addTo(this.map);
        }
    }

    /**
     * Remove marker from map
     */
    clearMarker() {
        if (this.marker) {
            this.map.removeLayer(this.marker);
            this.marker = null;
        }
    }

    /**
     * Draw isochrone bands on the map
     * @param {Array} bands - Array of band objects with polygons and labels
     */
    drawIsochrones(bands) {
        // Clear existing isochrones
        this.clearIsochrones();

        // Group bands by minute to avoid duplicate labels
        const bandsByMinute = new Map();

        bands.forEach((band, index) => {
            if (band.polygon && band.polygon.length >= 3) {
                // Convert [lon, lat] to [lat, lon] for Leaflet
                const latLngs = band.polygon.map(p => [p[1], p[0]]);

                // Alternate between two blue colors based on minute
                const colorIndex = band.minute !== undefined ? band.minute % 2 : index % 2;
                const color = this.isochroneColors[colorIndex];

                const polygon = L.polygon(latLngs, {
                    color: '#1565C0',      // Border color (darker blue)
                    weight: 1,
                    fillColor: color,
                    fillOpacity: 0.5
                }).addTo(this.map);

                this.isochroneLayers.push(polygon);

                // Store band data for dynamic label positioning
                // Group polygons by minute
                if (band.label) {
                    const minute = band.minute;
                    if (!bandsByMinute.has(minute)) {
                        bandsByMinute.set(minute, {
                            label: band.label,
                            polygons: []
                        });
                    }
                    // Store polygon coordinates in [lon, lat] format for Turf
                    bandsByMinute.get(minute).polygons.push(band.polygon);
                }
            }
        });

        // Convert grouped bands to array
        this.isochroneBands = Array.from(bandsByMinute.values());

        // Create initial labels
        this._updateLabelPositions();
    }

    /**
     * Update label positions based on current viewport
     */
    _updateLabelPositions() {
        // Remove existing labels
        this.isochroneLabels.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.isochroneLabels = [];

        if (this.isochroneBands.length === 0) return;

        // Get current viewport bounds
        const mapBounds = this.map.getBounds();
        const viewportPoly = this._boundsToPolygon(mapBounds);

        if (!viewportPoly) return;

        // For each band group, find best label position within viewport
        for (const bandGroup of this.isochroneBands) {
            let bestCenter = null;
            let bestArea = 0;

            for (const polygonCoords of bandGroup.polygons) {
                try {
                    // Ensure polygon is closed
                    const coords = [...polygonCoords];
                    if (coords.length < 4) continue;
                    if (coords[0][0] !== coords[coords.length - 1][0] ||
                        coords[0][1] !== coords[coords.length - 1][1]) {
                        coords.push(coords[0]);
                    }

                    const bandPoly = turf.polygon([coords]);

                    // Intersect with viewport
                    const intersection = turf.intersect(
                        turf.featureCollection([bandPoly, viewportPoly])
                    );

                    if (intersection) {
                        const area = turf.area(intersection);
                        if (area > bestArea) {
                            bestArea = area;
                            bestCenter = turf.centroid(intersection).geometry.coordinates;
                        }
                    }
                } catch (e) {
                    // Skip invalid polygons
                }
            }

            // Create label at best position
            if (bestCenter && bestArea > 0) {
                const labelMarker = L.marker([bestCenter[1], bestCenter[0]], {
                    icon: L.divIcon({
                        className: 'isochrone-label',
                        html: `<div class="isochrone-time">${bandGroup.label}</div>`,
                        iconSize: [60, 24],
                        iconAnchor: [30, 12]
                    }),
                    interactive: false
                }).addTo(this.map);

                this.isochroneLabels.push(labelMarker);
            }
        }
    }

    /**
     * Convert Leaflet bounds to Turf polygon
     */
    _boundsToPolygon(bounds) {
        if (!bounds || typeof turf === 'undefined') return null;

        const sw = bounds.getSouthWest();
        const ne = bounds.getNorthEast();

        return turf.polygon([[
            [sw.lng, sw.lat],
            [ne.lng, sw.lat],
            [ne.lng, ne.lat],
            [sw.lng, ne.lat],
            [sw.lng, sw.lat]
        ]]);
    }

    /**
     * Clear all isochrone layers
     */
    clearIsochrones() {
        // Remove polygon layers
        this.isochroneLayers.forEach(layer => {
            this.map.removeLayer(layer);
        });
        this.isochroneLayers = [];

        // Remove label markers
        this.isochroneLabels.forEach(marker => {
            this.map.removeLayer(marker);
        });
        this.isochroneLabels = [];

        // Clear band data
        this.isochroneBands = [];
    }

    /**
     * Get current bounds as object
     * @returns {Object|null}
     */
    getBoundsObject() {
        if (!this.bounds) return null;
        return {
            minLon: this.bounds.getWest(),
            maxLon: this.bounds.getEast(),
            minLat: this.bounds.getSouth(),
            maxLat: this.bounds.getNorth()
        };
    }

    /**
     * Check if a point is within current bounds
     * @param {number} lat
     * @param {number} lng
     * @returns {boolean}
     */
    isPointInBounds(lat, lng) {
        if (!this.bounds) return true;
        return this.bounds.contains([lat, lng]);
    }

    /**
     * Invalidate map size (call after container resize)
     */
    invalidateSize() {
        if (this.map) {
            this.map.invalidateSize();
        }
    }
}

// Create global instance
let mapManager = null;

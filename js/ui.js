/**
 * UIManager - Handles user interface interactions
 */

class UIManager {
    constructor() {
        // DOM elements
        this.elements = {
            countrySelect: document.getElementById('country-select'),
            methodSelect: document.getElementById('method-select'),
            dateInput: document.getElementById('date-input'),
            showLevel2: document.getElementById('show-level2'),
            coordinates: document.getElementById('coordinates'),
            statusBar: document.getElementById('status-bar'),
            loadingOverlay: document.getElementById('loading-overlay'),
            loadingText: document.getElementById('loading-text'),
            clearIsochrones: document.getElementById('clear-isochrones'),
            exportBtn: document.getElementById('export-btn'),
            exportModal: document.getElementById('export-modal'),
            exportBorders: document.getElementById('export-borders'),
            exportProvinces: document.getElementById('export-provinces'),
            exportIsochrones: document.getElementById('export-isochrones'),
            exportIsoLabel: document.getElementById('export-iso-label'),
            exportIsoText: document.getElementById('export-iso-text'),
            exportCancel: document.getElementById('export-cancel'),
            exportDownload: document.getElementById('export-download')
        };

        // Prayer time elements
        this.prayerElements = {
            fajr: document.getElementById('time-fajr'),
            sunrise: document.getElementById('time-sunrise'),
            dhuhr: document.getElementById('time-dhuhr'),
            asr: document.getElementById('time-asr'),
            maghrib: document.getElementById('time-maghrib'),
            isha: document.getElementById('time-isha')
        };

        // Isochrone buttons
        this.isoButtons = {
            fajr: document.getElementById('iso-fajr'),
            dhuhr: document.getElementById('iso-dhuhr'),
            asr: document.getElementById('iso-asr'),
            maghrib: document.getElementById('iso-maghrib'),
            isha: document.getElementById('iso-isha')
        };

        // Callbacks
        this.onCountryChange = null;
        this.onMethodChange = null;
        this.onDateChange = null;
        this.onLevel2Toggle = null;
        this.onIsochroneRequest = null;
        this.onClearIsochrones = null;
        this.onExportRequest = null;

        this.setupEventListeners();
        this.initDate();
    }

    /**
     * Setup event listeners for UI elements
     */
    setupEventListeners() {
        // Country selection
        this.elements.countrySelect.addEventListener('change', () => {
            if (this.onCountryChange) {
                this.onCountryChange(this.elements.countrySelect.value);
            }
        });

        // Method selection
        this.elements.methodSelect.addEventListener('change', () => {
            if (this.onMethodChange) {
                this.onMethodChange(this.elements.methodSelect.value);
            }
        });

        // Date change
        this.elements.dateInput.addEventListener('change', () => {
            if (this.onDateChange) {
                this.onDateChange(this.getDate());
            }
        });

        // Level 2 toggle
        this.elements.showLevel2.addEventListener('change', () => {
            if (this.onLevel2Toggle) {
                this.onLevel2Toggle(this.elements.showLevel2.checked);
            }
        });

        // Isochrone buttons
        for (const [prayer, button] of Object.entries(this.isoButtons)) {
            button.addEventListener('click', () => {
                if (this.onIsochroneRequest) {
                    this.onIsochroneRequest(prayer);
                }
            });
        }

        // Clear isochrones
        this.elements.clearIsochrones.addEventListener('click', () => {
            if (this.onClearIsochrones) {
                this.onClearIsochrones();
            }
        });

        // Export button
        this.elements.exportBtn.addEventListener('click', () => {
            this.showExportModal();
        });

        // Export cancel
        this.elements.exportCancel.addEventListener('click', () => {
            this.hideExportModal();
        });

        // Export download
        this.elements.exportDownload.addEventListener('click', () => {
            const layers = {
                borders: this.elements.exportBorders.checked,
                provinces: this.elements.exportProvinces.checked,
                isochrones: this.elements.exportIsochrones.checked && !this.elements.exportIsochrones.disabled
            };
            this.hideExportModal();
            if (this.onExportRequest) {
                this.onExportRequest(layers);
            }
        });

        // Close modal on backdrop click
        this.elements.exportModal.addEventListener('click', (e) => {
            if (e.target === this.elements.exportModal) {
                this.hideExportModal();
            }
        });
    }

    /**
     * Initialize date input with today's date
     */
    initDate() {
        const today = new Date();
        const yyyy = today.getFullYear();
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const dd = String(today.getDate()).padStart(2, '0');
        this.elements.dateInput.value = `${yyyy}-${mm}-${dd}`;
    }

    /**
     * Populate country dropdown
     * @param {Array} countries - Array of country objects
     */
    populateCountries(countries) {
        // Clear existing options except the first one
        while (this.elements.countrySelect.options.length > 1) {
            this.elements.countrySelect.remove(1);
        }

        // Add country options
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.name;
            option.textContent = country.name;
            this.elements.countrySelect.appendChild(option);
        });
    }

    /**
     * Get currently selected country
     * @returns {string}
     */
    getSelectedCountry() {
        return this.elements.countrySelect.value;
    }

    /**
     * Get currently selected calculation method
     * @returns {string}
     */
    getSelectedMethod() {
        return this.elements.methodSelect.value;
    }

    /**
     * Get selected date as array [year, month, day]
     * @returns {Array}
     */
    getDate() {
        const dateStr = this.elements.dateInput.value;
        const [year, month, day] = dateStr.split('-').map(Number);
        return [year, month, day];
    }

    /**
     * Get selected date as Date object
     * @returns {Date}
     */
    getDateObject() {
        return new Date(this.elements.dateInput.value);
    }

    /**
     * Check if level 2 is enabled
     * @returns {boolean}
     */
    isLevel2Enabled() {
        return this.elements.showLevel2.checked;
    }

    /**
     * Update coordinates display
     * @param {number} lat
     * @param {number} lng
     */
    updateCoordinates(lat, lng) {
        this.elements.coordinates.textContent = `${lat.toFixed(4)}°N, ${lng.toFixed(4)}°E`;
    }

    /**
     * Reset coordinates display
     */
    resetCoordinates() {
        this.elements.coordinates.textContent = 'Click on the map to select a location';
    }

    /**
     * Update prayer times display
     * @param {Object} times - Object with prayer names as keys and times as values
     */
    updatePrayerTimes(times) {
        for (const [prayer, element] of Object.entries(this.prayerElements)) {
            if (times && times[prayer]) {
                element.textContent = times[prayer];
            } else {
                element.textContent = '--:--';
            }
        }
    }

    /**
     * Reset prayer times display
     */
    resetPrayerTimes() {
        for (const element of Object.values(this.prayerElements)) {
            element.textContent = '--:--';
        }
    }

    /**
     * Update status bar message
     * @param {string} message
     * @param {string} type - 'info', 'success', 'warning', 'error'
     */
    setStatus(message, type = 'info') {
        const colorMap = {
            info: 'bg-gray-800',
            success: 'bg-green-700',
            warning: 'bg-yellow-600',
            error: 'bg-red-700'
        };

        // Remove all color classes
        this.elements.statusBar.classList.remove('bg-gray-800', 'bg-green-700', 'bg-yellow-600', 'bg-red-700');
        // Add the appropriate color class
        this.elements.statusBar.classList.add(colorMap[type] || colorMap.info);
        this.elements.statusBar.textContent = message;
    }

    /**
     * Show loading overlay
     * @param {string} message
     */
    showLoading(message = 'Loading...') {
        this.elements.loadingText.textContent = message;
        this.elements.loadingOverlay.classList.remove('hidden');
    }

    /**
     * Hide loading overlay
     */
    hideLoading() {
        this.elements.loadingOverlay.classList.add('hidden');
    }

    /**
     * Enable/disable isochrone buttons
     * @param {boolean} enabled
     */
    setIsoButtonsEnabled(enabled) {
        for (const button of Object.values(this.isoButtons)) {
            button.disabled = !enabled;
            if (enabled) {
                button.classList.remove('opacity-50', 'cursor-not-allowed');
            } else {
                button.classList.add('opacity-50', 'cursor-not-allowed');
            }
        }
    }

    /**
     * Highlight active isochrone button
     * @param {string|null} prayer - Prayer name or null to clear
     */
    setActiveIsoButton(prayer) {
        for (const [p, button] of Object.entries(this.isoButtons)) {
            if (p === prayer) {
                button.classList.remove('bg-blue-100', 'text-blue-800');
                button.classList.add('bg-blue-600', 'text-white');
            } else {
                button.classList.remove('bg-blue-600', 'text-white');
                button.classList.add('bg-blue-100', 'text-blue-800');
            }
        }
    }

    /**
     * Enable/disable export button
     * @param {boolean} enabled
     */
    setExportEnabled(enabled) {
        this.elements.exportBtn.disabled = !enabled;
        if (enabled) {
            this.elements.exportBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        } else {
            this.elements.exportBtn.classList.add('opacity-50', 'cursor-not-allowed');
        }
    }

    /**
     * Update the isochrone export option based on current prayer
     * @param {string|null} prayer - Prayer name or null if none
     */
    updateExportIsoOption(prayer) {
        if (prayer) {
            this.elements.exportIsochrones.disabled = false;
            this.elements.exportIsochrones.checked = true;
            this.elements.exportIsoLabel.classList.remove('opacity-50');
            this.elements.exportIsoText.textContent = `Isochrones (${prayer.charAt(0).toUpperCase() + prayer.slice(1)})`;
        } else {
            this.elements.exportIsochrones.disabled = true;
            this.elements.exportIsochrones.checked = false;
            this.elements.exportIsoLabel.classList.add('opacity-50');
            this.elements.exportIsoText.textContent = 'Isochrones (no prayer selected)';
        }
    }

    /**
     * Show export modal
     */
    showExportModal() {
        this.elements.exportModal.classList.remove('hidden');
    }

    /**
     * Hide export modal
     */
    hideExportModal() {
        this.elements.exportModal.classList.add('hidden');
    }
}

// Create global instance
let uiManager = null;

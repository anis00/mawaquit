/**
 * IsochroneGenerator - Interface for generating isochrone curves
 * Uses Web Worker for heavy calculations
 */

class IsochroneGenerator {
    constructor() {
        this.worker = null;
        this.pendingRequests = new Map();
        this.requestId = 0;
        this.initWorker();
    }

    /**
     * Initialize the Web Worker
     */
    initWorker() {
        try {
            this.worker = new Worker('js/isochrones.worker.js');
            this.worker.onmessage = this.handleWorkerMessage.bind(this);
            this.worker.onerror = this.handleWorkerError.bind(this);
        } catch (error) {
            console.error('Failed to initialize isochrone worker:', error);
            this.worker = null;
        }
    }

    /**
     * Handle messages from the worker
     */
    handleWorkerMessage(e) {
        const { type, id, result, error } = e.data;

        const pending = this.pendingRequests.get(id);
        if (!pending) return;

        this.pendingRequests.delete(id);

        if (type === 'error' || error) {
            pending.reject(new Error(error || 'Worker error'));
        } else {
            pending.resolve(result);
        }
    }

    /**
     * Handle worker errors
     */
    handleWorkerError(error) {
        console.error('Isochrone worker error:', error);
        // Reject all pending requests
        for (const [id, pending] of this.pendingRequests) {
            pending.reject(new Error('Worker crashed'));
        }
        this.pendingRequests.clear();
    }

    /**
     * Generate isochrone bands for a prayer
     * @param {string} prayer - Prayer name
     * @param {Object} bounds - Bounds object {minLon, maxLon, minLat, maxLat}
     * @param {Array} date - Date as [year, month, day]
     * @param {number} timezone - Timezone offset
     * @param {Object} settings - Prayer calculation settings
     * @returns {Promise<Object>} Promise resolving to bands array
     */
    async generate(prayer, bounds, date, timezone, settings) {
        if (!this.worker) {
            // Fallback to main thread calculation if worker unavailable
            return this.generateSync(prayer, bounds, date, timezone, settings);
        }

        const id = ++this.requestId;

        return new Promise((resolve, reject) => {
            this.pendingRequests.set(id, { resolve, reject });

            this.worker.postMessage({
                type: 'generateIsochrones',
                id,
                params: {
                    prayer,
                    bounds,
                    date,
                    timezone,
                    settings
                }
            });

            // Timeout after 30 seconds
            setTimeout(() => {
                if (this.pendingRequests.has(id)) {
                    this.pendingRequests.delete(id);
                    reject(new Error('Isochrone calculation timed out'));
                }
            }, 30000);
        });
    }

    /**
     * Synchronous fallback for isochrone generation
     * (simplified version for when worker is unavailable)
     */
    generateSync(prayer, bounds, date, timezone, settings) {
        // This is a simplified synchronous version
        // In practice, the worker should always be available in modern browsers
        console.warn('Using synchronous isochrone calculation (may block UI)');

        const { minLon, maxLon, minLat, maxLat } = bounds;
        const colors = [
            '#E3F2FD', '#BBDEFB', '#90CAF9', '#64B5F6', '#42A5F5',
            '#2196F3', '#1E88E5', '#1976D2', '#1565C0', '#0D47A1'
        ];

        // Create a simple PrayTimes instance for sampling
        const prayCalc = new PrayTimes('MWL');
        Object.assign(prayCalc.settings, settings);

        // Sample points to find time range
        const sampleTimes = [];
        for (let lat = minLat; lat <= maxLat; lat += (maxLat - minLat) / 10) {
            for (let lon = minLon; lon <= maxLon; lon += (maxLon - minLon) / 10) {
                const times = prayCalc.getTimes(date, [lat, lon], timezone, 0, 'Float');
                if (times[prayer] && !isNaN(times[prayer])) {
                    sampleTimes.push(times[prayer] * 60);
                }
            }
        }

        if (sampleTimes.length === 0) {
            return { error: 'No valid times found' };
        }

        const minTime = Math.min(...sampleTimes) - 2;
        const maxTime = Math.max(...sampleTimes) + 2;

        // Generate simplified bands (just colored rectangles for fallback)
        const bands = [];
        const numBands = Math.min(Math.ceil(maxTime - minTime), 20);

        for (let i = 0; i < numBands; i++) {
            const minute = Math.floor(minTime) + i;
            const frac = i / numBands;

            const lonLeft = minLon + frac * (maxLon - minLon);
            const lonRight = minLon + (frac + 1 / numBands) * (maxLon - minLon);

            const polygon = [
                [lonLeft, minLat],
                [lonRight, minLat],
                [lonRight, maxLat],
                [lonLeft, maxLat],
                [lonLeft, minLat]
            ];

            bands.push({
                polygon,
                label: this.formatTime(minute),
                labelPos: [(lonLeft + lonRight) / 2, (minLat + maxLat) / 2],
                minute,
                color: colors[i % colors.length]
            });
        }

        return { bands };
    }

    /**
     * Format minutes to HH:MM
     */
    formatTime(minutes) {
        const hours = Math.floor(minutes / 60) % 24;
        const mins = Math.floor(minutes % 60);
        return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}`;
    }

    /**
     * Terminate the worker
     */
    terminate() {
        if (this.worker) {
            this.worker.terminate();
            this.worker = null;
        }
    }
}

// Create global instance
const isochroneGenerator = new IsochroneGenerator();

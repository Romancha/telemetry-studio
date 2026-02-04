/**
 * GPSQualityIndicator - Compact GPS quality badge for header
 * Shows color-coded quality with tooltip details
 */

class GPSQualityIndicator {
    constructor(container, state) {
        this.container = container;
        this.state = state;

        this._init();
    }

    _init() {
        this._render();

        // Listen for file changes
        this.state.on('session:changed', () => this._update());
        this.state.on('session:cleared', () => this._update());
        this.state.on('files:changed', () => this._update());
    }

    _render() {
        this.container.innerHTML = `
            <span class="gps-indicator" id="gps-indicator" style="display: none;">
                <span class="gps-indicator-dot"></span>
                <span class="gps-indicator-text"></span>
                <span class="gps-indicator-tooltip"></span>
            </span>
        `;

        this.indicator = document.getElementById('gps-indicator');
        this.dot = this.indicator.querySelector('.gps-indicator-dot');
        this.text = this.indicator.querySelector('.gps-indicator-text');
        this.tooltip = this.indicator.querySelector('.gps-indicator-tooltip');
    }

    _update() {
        const primaryFile = this.state.getPrimaryFile();
        const gpsQuality = primaryFile?.gps_quality;

        if (!gpsQuality) {
            this.indicator.style.display = 'none';
            return;
        }

        this.indicator.style.display = 'inline-flex';
        this._renderIndicator(gpsQuality);
    }

    _renderIndicator(quality) {
        const info = this._getIndicatorInfo(quality.quality_score);

        // Update indicator
        this.indicator.className = `gps-indicator gps-indicator-${quality.quality_score}`;
        this.text.textContent = `GPS: ${info.label}`;

        // Update tooltip
        let tooltipHtml = `<strong>${info.label}</strong>`;

        if (quality.quality_score !== 'no_signal') {
            tooltipHtml += `
                <br>DOP avg: ${quality.dop_mean?.toFixed(2) || 'N/A'}
                <br>Lock rate: ${quality.lock_rate}%
                <br>Usable: ${quality.usable_percentage}%
            `;
        } else {
            tooltipHtml += `
                <br>No GPS lock acquired
                <br>Use external GPX file
            `;
        }

        this.tooltip.innerHTML = tooltipHtml;
    }

    _getIndicatorInfo(score) {
        const info = {
            'excellent': { label: 'Excellent' },
            'good': { label: 'Good' },
            'ok': { label: 'OK' },
            'poor': { label: 'Poor' },
            'no_signal': { label: 'No Signal' }
        };
        return info[score] || info['no_signal'];
    }

    /**
     * Get current quality score
     */
    getQualityScore() {
        const primaryFile = this.state.getPrimaryFile();
        return primaryFile?.gps_quality?.quality_score || null;
    }
}

// Export
window.GPSQualityIndicator = GPSQualityIndicator;

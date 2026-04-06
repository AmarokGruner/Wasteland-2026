/**
 * Gamelog Service - Extrahiert aus admin.html
 * Gamelog-Ladung, Filter, Suche, Auto-Refresh
 */

export const GamelogService = {
    /**
     * Auto-Refresh Interval (ms)
     */
    _refreshInterval: null,
    _intervalMs: 30000, // 30 Sekunden

    /**
     * Lädt Gamelog mit Filter
     */
    async loadGamelog(search = '', type = 'all') {
        try {
            let url = '/admin/gamelog?search=' + encodeURIComponent(search);
            if (type && type !== 'all') {
                url += '&type=' + encodeURIComponent(type);
            }
            
            const res = await adminFetch(url);
            const data = await res.json();
            
            this.renderTable(data);
            
            return data;
        } catch (e) {
            console.error('GamelogService.loadGamelog:', e);
            this.showError('Fehler beim Laden des Gamelogs');
            return [];
        }
    },

    /**
     * Rendert Gamelog-Tabelle
     */
    renderTable(data) {
        const tbody = document.querySelector('#adminGamelogTable tbody');
        if (!tbody) return;
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-muted">Keine Einträge</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(g => `
            <tr>
                <td>${new Date(g.created_at).toLocaleTimeString('de-DE')}</td>
                <td>${this.escapeHtml(g.player_name || '-')}</td>
                <td><span class="badge" style="background:gray">${this.escapeHtml(g.event_type)}</span></td>
                <td>${this.escapeHtml(g.province_name || '-')}</td>
                <td>${this.escapeHtml(g.message)}</td>
            </tr>
        `).join('');
    },

    /**
     * Startet Auto-Refresh
     */
    startAutoRefresh() {
        if (this._refreshInterval) {
            this.stopAutoRefresh();
        }
        
        this._refreshInterval = setInterval(() => {
            const searchInput = document.getElementById('gamelog-search');
            const typeSelect = document.getElementById('gamelog-type');
            
            const search = searchInput ? searchInput.value : '';
            const type = typeSelect ? typeSelect.value : 'all';
            
            this.loadGamelog(search, type);
            
            if (window.showSnackbar) {
                // Nur im Console loggen, um User nicht zu nerven
                console.log('Gamelog auto-refreshed');
            }
        }, this._intervalMs);
        
        return true;
    },

    /**
     * Stoppt Auto-Refresh
     */
    stopAutoRefresh() {
        if (this._refreshInterval) {
            clearInterval(this._refreshInterval);
            this._refreshInterval = null;
        }
        return true;
    },

    /**
     * Toggle Auto-Refresh
     */
    toggleAutoRefresh(isRunning) {
        if (isRunning) {
            return this.startAutoRefresh();
        } else {
            return this.stopAutoRefresh();
        }
    },

    /**
     * Setzt Refresh-Intervall
     */
    setRefreshInterval(ms) {
        this._intervalMs = ms;
        if (this._refreshInterval) {
            this.stopAutoRefresh();
            this.startAutoRefresh();
        }
    },

    /**
     * Filtert nach Typ (Dropdown-Optionen)
     */
    getEventTypes() {
        // Wird typischerweise vom Backend kommen
        return [
            'all',
            'combat',
            'construction',
            'resource',
            'movement',
            'trade',
            'event'
        ];
    },

    /**
     * Sucht nach einem bestimmten Event
     */
    async searchEvents(search, type = null) {
        return this.loadGamelog(search, type);
    },

    /**
     * Fallback Error Handler
     */
    showError(message) {
        if (window.showSnackbar) {
            showSnackbar('❌ ' + message);
        } else {
            console.error(message);
        }
    },

    /**
     * HTML escaping
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
};

// Globale Funktionen
window.loadAdminGamelog = function() {
    const searchInput = document.getElementById('gamelog-search');
    const typeSelect = document.getElementById('gamelog-type');
    
    const search = searchInput ? searchInput.value : '';
    const type = typeSelect ? typeSelect.value : 'all';
    
    GamelogService.loadGamelog(search, type).catch(console.error);
};

// Auto-Refresh Checkbox Handler
document.addEventListener('DOMContentLoaded', function() {
    const checkbox = document.getElementById('gamelog-autorefresh');
    if (checkbox) {
        checkbox.addEventListener('change', (e) => {
            GamelogService.toggleAutoRefresh(e.target.checked);
        });
    }
    
    // Initial load beim Tab-Change (wird von Router aufgerufen)
    window.loadAdminGamelog = function() {
        GamelogService.loadGamelog().catch(console.error);
    };
});

export default GamelogService;

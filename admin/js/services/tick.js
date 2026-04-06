/**
 * Tick Service - Extrahiert aus admin.html
 * Tick-Engine Status, Historie, manueller Trigger
 */

export const TickService = {
    /**
     * Lädt Tick-Engine Status
     */
    async loadStatus() {
        try {
            const res = await adminFetch('/admin/ticks/status');
            if (!res.ok) throw new Error('Status API returned: ' + res.status);
            
            const s = await res.json();
            
            this.updateUI({
                is_running: s.is_running,
                last_run: s.last_run,
                error_count: s.error_count,
                last_duration: s.last_tick_duration,
                last_status: s.last_tick_status
            });
            
            return s;
        } catch (e) {
            console.error('TickService.loadStatus:', e);
            this.showError('Fehler beim Laden des Tick-Status');
            return null;
        }
    },

    /**
     * Lädt Tick-Historie
     */
    async loadHistory() {
        try {
            const res = await adminFetch('/admin/ticks');
            if (!res.ok) throw new Error('History API returned: ' + res.status);
            
            const data = await res.json();
            this.renderHistoryTable(data);
            
            return data;
        } catch (e) {
            console.error('TickService.loadHistory:', e);
            this.showError('Fehler beim Laden der Historie');
            return [];
        }
    },

    /**
     * Lädt Status und Historie
     */
    async loadTickEngine() {
        await this.loadStatus();
        await this.loadHistory();
    },

    /**
     * Erzwingt einen manuellen Tick
     */
    async forceTick() {
        if (!confirm('Manuellen Tick wirklich erzwingen?')) {
            return false;
        }
        
        try {
            const res = await adminFetch('/admin/ticks/force', {
                method: 'POST'
            });
            
            const d = await res.json();
            
            if (window.showSnackbar) {
                showSnackbar(d.message || '✅ Tick ausgelöst');
            } else {
                alert(d.message || 'Tick ausgelöst');
            }
            
            await this.loadTickEngine();
            return true;
            
        } catch (e) {
            console.error('TickService.forceTick:', e);
            alert('Fehler: ' + e.message);
            return false;
        }
    },

    /**
     * Update UI-Elemente
     */
    updateUI(state) {
        // Status
        const stateEl = document.getElementById('tickEngineState');
        if (stateEl) {
            stateEl.textContent = state.is_running ? 'LÄUFT' : 'BEendet';
            stateEl.style.color = state.is_running ? 'var(--accent)' : 'var(--success)';
        }
        
        // Last Run
        const lastRunEl = document.getElementById('tickLastRun');
        if (lastRunEl && state.last_run) {
            lastRunEl.textContent = new Date(state.last_run).toLocaleString('de-DE');
        } else if (lastRunEl) {
            lastRunEl.textContent = 'Nie';
        }
        
        // Error Count
        const errorEl = document.getElementById('tickErrorCount');
        if (errorEl) {
            errorEl.textContent = state.error_count || 0;
        }
        
        // Duration
        const durationEl = document.getElementById('tickLastDuration');
        if (durationEl) {
            durationEl.textContent = state.last_duration || '-';
        }
        
        // Last Status
        const statusEl = document.getElementById('tickLastStatus');
        if (statusEl) {
            statusEl.textContent = state.last_status === 1 ? 'ERFOLG' : 
                                  (state.last_status === 0 ? 'FEHLER' : '-');
            statusEl.style.color = state.last_status === 1 ? 'var(--success)' :
                                  (state.last_status === 0 ? 'var(--danger)' : '');
        }
    },

    /**
     * Rendert Historie-Tabelle
     */
    renderHistoryTable(data) {
        const tbody = document.getElementById('ticksTable');
        if (!tbody) return;
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-muted">Keine Einträge</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(t => `
            <tr>
                <td>${new Date(t.timestamp).toLocaleString('de-DE')}</td>
                <td>${t.duration_ms}ms</td>
                <td>${t.provinces_processed || 0}</td>
                <td style="color: ${t.status === 1 ? 'var(--success)' : 'var(--danger)'}">
                    ${t.status === 1 ? 'OK' : 'FEHLER'}
                </td>
                <td style="font-size: 11px; max-width: 250px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" 
                    title="${this.escapeHtml(t.details || '')}">
                    ${this.escapeHtml(t.details || '-')}
                </td>
            </tr>
        `).join('');
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
window.loadTickEngine = function() {
    TickService.loadTickEngine().catch(console.error);
};

window.forceTick = function() {
    TickService.forceTick().catch(console.error);
};

document.addEventListener('DOMContentLoaded', function() {
    // Initial load wenn Ticks Tab aktiv
    if (window.location.hash.includes('ticks')) {
        setTimeout(() => {
            TickService.loadTickEngine().catch(console.error);
        }, 200);
    }
});

export default TickService;

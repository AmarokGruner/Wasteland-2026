/**
 * Dashboard Service - Extrahiert aus admin.html
 * Liefert Dashboard-Statistiken und KPI-Daten
 */

export const DashboardService = {
    /**
     * Lädt alle Dashboard-Daten
     */
    async loadDashboard() {
        try {
            const res = await adminFetch('/admin/dashboard');
            const data = await res.json();
            
            // Update KPIs
            this.updateKPI('kpi-active-players', data.active_players_today);
            this.updateKPI('kpi-total-provinces', data.total_provinces);
            this.updateKPI('kpi-active-combats', data.active_combats);
            this.updateKPI('kpi-open-revolts', data.open_revolts);

            // Render Tabellen
            this.renderRevoltRisks(data.revolt_risks);
            this.renderHungerWarnings(data.hunger_warnings);
            this.renderInactivePlayers(data.inactive_players);

            return data;
        } catch (e) {
            console.error('DashboardService.loadDashboard:', e);
            throw e;
        }
    },

    /**
     * Aktualisiert einen KPI-Wert
     */
    updateKPI(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value ?? '-';
    },

    /**
     * Rendert Revolten-Risiken
     */
    renderRevoltRisks(data) {
        const tbody = document.querySelector('#table-revolt-risks tbody');
        if (!tbody) return;
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-muted">Keine Einträge</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(r => `
            <tr>
                <td>${this.escapeHtml(r.player)}</td>
                <td>${this.escapeHtml(r.province)}</td>
                <td style="color:${r.moral < 15 ? 'var(--danger)' : 'var(--warning)'}">
                    ${r.moral}%
                </td>
            </tr>
        `).join('');
    },

    /**
     * Rendert Hunger-Warnungen
     */
    renderHungerWarnings(data) {
        const tbody = document.querySelector('#table-hunger-warnings tbody');
        if (!tbody) return;
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="text-muted">Keine Einträge</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(h => `
            <tr>
                <td>${this.escapeHtml(h.province)}</td>
                <td>${h.hours_left}h</td>
            </tr>
        `).join('');
    },

    /**
     * Rendert inaktive Spieler
     */
    renderInactivePlayers(data) {
        const tbody = document.querySelector('#table-inactive-players tbody');
        if (!tbody) return;
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="3" class="text-muted">Keine Einträge</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(i => `
            <tr>
                <td>${this.escapeHtml(i.player)}</td>
                <td>${i.last_login ? this.escapeHtml(i.last_login) : '<span class="text-muted">Nie</span>'}</td>
                <td>${i.province_count}</td>
            </tr>
        `).join('');
    },

    /**
     * HTML Escaping für Sicherheit
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Refresh Dashboard (für manuelle Aktualisierung)
     */
    async refresh() {
        return this.loadDashboard();
    }
};

// Globale Funktion für onclick Handler
window.loadDashboard = function() {
    DashboardService.loadDashboard().catch(console.error);
};

export default DashboardService;

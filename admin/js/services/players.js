/**
 * Players Service - Extrahiert aus admin.html
 * Spieler-Verwaltung: List, Actions, Statistics
 */

export const PlayersService = {
    /**
     * Speichert Spieler-Daten global (für Dropdowns)
     */
    _players: [],

    /**
     * Lädt alle Spieler
     */
    async loadPlayers() {
        try {
            const res = await adminFetch('/admin/players');
            const data = await res.json();
            this._players = Array.isArray(data) ? data : [];
            
            // Update broadcast recipient list
            this.updateBroadcastRecipients();
            
            return this._players;
        } catch (e) {
            console.error('PlayersService.loadPlayers:', e);
            throw e;
        }
    },

    /**
     * Aktualisiert Broadcast-Empfänger-Liste
     */
    updateBroadcastRecipients() {
        const select = document.getElementById('broadcast-recipient');
        if (!select) return;
        
        select.innerHTML = '<option value="all">Alle Spieler</option>' +
            this._players.map(p => 
                `<option value="${p.id}">${this.escapeHtml(p.name)} (ID: ${p.id})</option>`
            ).join('');
    },

    /**
     * Setzt Spieler-Statistik (Provinz-Wert)
     */
    async setProvinceValue(playerId, stat, value) {
        try {
            await apiFetch(`/admin/province/${playerId}/set`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ [stat]: parseInt(value) })
            });
            showSnackbar('✅ Wert gesetzt');
        } catch (e) {
            console.error(e);
            alert('Fehler: ' + e.message);
        }
    },

    /**
     * Add MIPS zu Spieler
     */
    async addMips(playerId, amount) {
        try {
            await apiFetch(`/admin/province/${playerId}/add-mips`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ amount: parseFloat(amount) })
            });
            showSnackbar('✅ MIPS hinzugefügt');
        } catch (e) {
            console.error(e);
            alert('Fehler: ' + e.message);
        }
    },

    /**
     * Sperrt einen Spieler permanent
     */
    async banPlayer(playerId) {
        if (!confirm('Soll dieser Spieler wirklich permanent gesperrt werden?')) {
            return false;
        }
        
        try {
            await apiFetch(`/admin/player/${playerId}/ban`, { method: 'POST' });
            showSnackbar('🚫 Spieler gesperrt');
            return true;
        } catch (e) {
            console.error(e);
            alert('Fehler: ' + e.message);
            return false;
        }
    },

    /**
     * Reset Spieler-Status
     */
    async resetPlayer(playerId) {
        if (!confirm('Spieler-Status zurücksetzen? (24h Cooldown)')) {
            return false;
        }
        
        try {
            await apiFetch(`/admin/player/${playerId}/reset`, { method: 'POST' });
            showSnackbar('✅ Spieler-Status zurückgesetzt');
            return true;
        } catch (e) {
            console.error(e);
            alert('Fehler: ' + e.message);
            return false;
        }
    },

    /**
     * Filtert Spieler nach Status
     */
    filterByStatus(status) {
        if (status === 'all') return this._players;
        return this._players.filter(p => p.status == status);
    },

    /**
     * Search Spielernach Name
     */
    searchByName(name) {
        if (!name) return this._players;
        return this._players.filter(p => 
            p.name.toLowerCase().includes(name.toLowerCase())
        );
    },

    /**
     * HTML Escaping
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    // Globale Funktionen für onclick Handler
    getPlayers() {
        return this._players;
    }
};

// Global functions
window.loadAdminPlayers = function() {
    PlayersService.loadPlayers().catch(console.error);
};

window.filterPlayers = function() {
    // Wird von UI aufgerufen
};

export default PlayersService;

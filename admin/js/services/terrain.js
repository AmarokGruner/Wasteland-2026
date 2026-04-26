/**
 * Terrain Service - Extrahiert aus admin.html
 * Terrain-Verwaltung: CRUD, Bilder, Regen
 */

export const TerrainService = {
    /**
     * Speichert Terrain-Daten lokal
     */
    _terrains: [],

    /**
     * Lädt alle Terrains
     */
    async loadTerrains() {
        try {
            const res = await adminFetch('/admin/terrain');
            if (!res.ok) throw new Error('Response not OK: ' + res.status);
            
            const data = await res.json();
            this._terrains = data;
            this.renderTable(data);
            
            return data;
        } catch (e) {
            console.error('TerrainService.loadTerrains:', e);
            this.showError('Fehler beim Laden der Terrains');
            return [];
        }
    },

    /**
     * Rendert Terrain-Tabelle
     */
    renderTable(data) {
        const tbody = document.getElementById('terrainTable');
        if (!tbody) return;
        
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-muted">Keine Einträge</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(t => `
            <tr>
                <td>${t.id}</td>
                <td>${t.bild_url ? `<img src="${t.bild_url}" style="width:30px; height:30px; vertical-align:middle; margin-right:8px; border:1px solid #444;">` : ''}${this.escapeHtml(t.name || '-')}</td>
                <td>${t.startgebiet ? 'Ja' : 'Nein'}</td>
                <td>${t.regen_pct || 0}%</td>
                <td class="actions">
                    <button class="btn btn-primary btn-small" onclick="TerrainService.editTerrain('${t.id}')">
                        Bearbeiten
                    </button>
                    <button class="btn btn-danger btn-small" onclick="TerrainService.deleteTerrain('${t.id}')">
                        Löschen
                    </button>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Bearbeitet ein Terrain
     */
    editTerrain(id) {
        const terrain = this._terrains.find(t => t.id === id);
        if (terrain) {
            if (window.openGenericModal) {
                openGenericModal('edit', 'terrain', terrain);
            } else {
                alert('Modal-Funktion nicht verfügbar');
            }
        }
    },

    /**
     * Löscht ein Terrain
     */
    async deleteTerrain(id) {
        if (!confirm(`Terrain ID ${id} wirklich löschen?`)) {
            return { success: false };
        }
        
        try {
            const res = await adminFetch(`/admin/terrain/${id}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                await this.loadTerrains();
                if (window.showSnackbar) {
                    showSnackbar('✅ Terrain gelöscht');
                }
                return { success: true };
            } else {
                alert('Fehler beim Löschen');
                return { success: false };
            }
        } catch (e) {
            console.error('TerrainService.deleteTerrain:', e);
            alert('Verbindungsfehler');
            return { success: false };
        }
    },

    /**
     * Aktualisiert ein Terrain
     */
    async updateTerrain(id, data) {
        try {
            const res = await adminFetch(`/admin/terrain/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                await this.loadTerrains();
                if (window.showSnackbar) {
                    showSnackbar('✅ Terrain aktualisiert');
                }
                return { success: true };
            } else {
                return { success: false, message: 'Fehler beim Aktualisieren' };
            }
        } catch (e) {
            console.error('TerrainService.updateTerrain:', e);
            return { success: false, message: 'Verbindungsfehler' };
        }
    },

    /**
     * Erstellt ein neues Terrain
     */
    async createTerrain(data) {
        try {
            const res = await adminFetch('/admin/terrain', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                await this.loadTerrains();
                if (window.showSnackbar) {
                    showSnackbar('✅ Terrain erstellt');
                }
                return { success: true };
            } else {
                return { success: false, message: 'Fehler beim Erstellen' };
            }
        } catch (e) {
            console.error('TerrainService.createTerrain:', e);
            return { success: false, message: 'Verbindungsfehler' };
        }
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
window.loadTerrain = function() {
    TerrainService.loadTerrains().catch(console.error);
};

document.addEventListener('DOMContentLoaded', function() {
    // Initial load wenn Terrain Tab aktiv
    if (window.location.hash.includes('terrain')) {
        setTimeout(() => {
            TerrainService.loadTerrains().catch(console.error);
        }, 100);
    }
});

export default TerrainService;

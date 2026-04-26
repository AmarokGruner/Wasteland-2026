/**
 * Building Service - Extrahiert aus admin.html
 * Gebäude-Verwaltung: CRUD, Produktion, Verbrauch
 */

export const BuildingService = {
    /**
     * Speichert Gebäude-Daten lokal
     */
    _buildings: [],

    /**
     * Lädt alle Gebäude-Typen
     */
    async loadBuildings() {
        try {
            const res = await adminFetch('/admin/gebaeude_typen');
            if (!res.ok) throw new Error('Response not OK: ' + res.status);
            
            const buildings = await res.json();
            if (!Array.isArray(buildings)) throw new Error('Data is not an array');
            
            this._buildings = buildings;
            this.renderTable(buildings);
            
            return buildings;
        } catch (e) {
            console.error('BuildingService.loadBuildings:', e);
            this.showError('Fehler beim Laden der Gebäude');
            return [];
        }
    },

    /**
     * Rendert Gebäude-Tabelle
     */
    renderTable(buildings) {
        const tbody = document.getElementById('buildingsTable');
        if (!tbody) return;
        
        if (buildings.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-muted">Keine Einträge</td></tr>';
            return;
        }
        
        tbody.innerHTML = buildings.map(b => {
            const prod = this.safeParseArray(b.produktion);
            const prodTags = prod.slice(0, 3).map(p => 
                p.ressource ? `<span class="badge" style="background:var(--success)">${this.escapeHtml(p.ressource)}</span>` : ''
            ).join(' ');
            
            const special = this.safeParseArray(b.spezial_eigenschaften);
            const specTags = special.map(s => 
                `<span class="badge" title="${this.escapeHtml(s)}">✨</span>`
            ).join('');
            
            return `
                <tr>
                    <td>${b.id}</td>
                    <td><b>${this.escapeHtml(b.name || '-')}</b></td>
                    <td>${this.escapeHtml(b.kategorie || '-')}</td>
                    <td>${b.baukosten_mips || 0}</td>
                    <td>${b.arbeiter || 0} ${prodTags}</td>
                    <td>${b.wohnraum || 0} ${specTags}</td>
                    <td>${b.lagerkapazitaet || 0}</td>
                    <td class="actions">
                        <button class="btn btn-primary btn-small" onclick="BuildingService.editBuilding(${b.id})">
                            Bearbeiten
                        </button>
                        <button class="btn btn-danger btn-small" onclick="BuildingService.deleteBuilding(${b.id})">
                            Löschen
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    },

    /**
     * Bearbeitet ein Gebäude
     */
    editBuilding(id) {
        const building = this._buildings.find(b => b.id === id);
        if (building) {
            if (window.openGenericModal) {
                openGenericModal('edit', 'buildings', building);
            } else {
                alert('Modal-Funktion nicht verfügbar');
            }
        }
    },

    /**
     * Löscht ein Gebäude
     */
    async deleteBuilding(id) {
        if (!confirm(`Gebäude ID ${id} wirklich löschen?`)) {
            return { success: false };
        }
        
        try {
            const res = await adminFetch(`/admin/gebaeude_typen/${id}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                await this.loadBuildings();
                if (window.showSnackbar) {
                    showSnackbar('✅ Gebäude gelöscht');
                }
                return { success: true };
            } else {
                alert('Fehler beim Löschen');
                return { success: false };
            }
        } catch (e) {
            console.error('BuildingService.deleteBuilding:', e);
            alert('Verbindungsfehler');
            return { success: false };
        }
    },

    /**
     * Erstellt ein neues Gebäude
     */
    async createBuilding(data) {
        try {
            const res = await adminFetch('/admin/gebaeude_typen', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                await this.loadBuildings();
                if (window.showSnackbar) {
                    showSnackbar('✅ Gebäude erstellt');
                }
                return { success: true };
            } else {
                return { success: false, message: 'Fehler beim Erstellen' };
            }
        } catch (e) {
            console.error('BuildingService.createBuilding:', e);
            return { success: false, message: 'Verbindungsfehler' };
        }
    },

    /**
     * Aktualisiert ein Gebäude
     */
    async updateBuilding(id, data) {
        try {
            const res = await adminFetch(`/admin/gebaeude_typen/${id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            
            if (res.ok) {
                await this.loadBuildings();
                if (window.showSnackbar) {
                    showSnackbar('✅ Gebäude aktualisiert');
                }
                return { success: true };
            } else {
                return { success: false, message: 'Fehler beim Aktualisieren' };
            }
        } catch (e) {
            console.error('BuildingService.updateBuilding:', e);
            return { success: false, message: 'Verbindungsfehler' };
        }
    },

    /**
     * Helper: Parse Array aus String
     */
    safeParseArray(data, defaultVal = []) {
        if (!data) return defaultVal;
        if (Array.isArray(data)) return data;
        try {
            const parsed = JSON.parse(data);
            return Array.isArray(parsed) ? parsed : defaultVal;
        } catch (e) {
            console.error('JSON Parse Error:', e, data);
            return defaultVal;
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
    },

    /**
     * Alle Gebäude
     */
    getAll() {
        return this._buildings;
    },

    /**
     * Gebäude nach ID
     */
    getById(id) {
        return this._buildings.find(b => b.id === id);
    }
};

// Globale Funktionen
window.loadBuildings = function() {
    BuildingService.loadBuildings().catch(console.error);
};

window.editBuilding = function(id) {
    BuildingService.editBuilding(id);
};

window.deleteBuilding = function(id) {
    BuildingService.deleteBuilding(id).catch(console.error);
};

// Event Listener
document.addEventListener('DOMContentLoaded', function() {
    // Initial load wenn Buildings Tab aktiv
    window.addEventListener('hashchange', () => {
        if (window.location.hash.includes('buildings')) {
            BuildingService.loadBuildings().catch(console.error);
        }
    });
    
    // Erster Load
    if (window.location.hash.includes('buildings')) {
        setTimeout(() => {
            BuildingService.loadBuildings().catch(console.error);
        }, 100);
    }
});

export default BuildingService;

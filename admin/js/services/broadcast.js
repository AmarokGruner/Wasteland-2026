/**
 * Broadcast Service - Extrahiert aus admin.html
 * Nachrichten versenden, History anzeigen
 */

export const BroadcastService = {
    /**
     * Sendet einen Broadcast
     */
    async sendBroadcast(data) {
        try {
            const res = await adminFetch('/admin/broadcast', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    recipient: data.recipient,
                    subject: data.subject,
                    body: data.body,
                    type: data.type || 'info'
                })
            });
            
            if (res.ok) {
                if (window.showSnackbar) {
                    showSnackbar('🚀 Broadcast versendet!');
                }
                await this.loadHistory();
                return { success: true };
            } else {
                if (window.showSnackbar) {
                    showSnackbar('❌ Fehler beim Senden');
                }
                return { success: false };
            }
        } catch (e) {
            console.error('BroadcastService.sendBroadcast:', e);
            if (window.showSnackbar) {
                showSnackbar('❌ Verbindungsfehler');
            }
            return { success: false };
        }
    },

    /**
     * Lädt Broadcast-Historie
     */
    async loadHistory() {
        try {
            const res = await adminFetch('/admin/broadcast/history');
            const data = await res.json();
            
            this.renderHistoryTable(data);
            
            return data;
        } catch (e) {
            console.error('BroadcastService.loadHistory:', e);
            this.showError('Fehler beim Laden der Historie');
            return [];
        }
    },

    /**
     * Rendert Historie-Tabelle
     */
    renderHistoryTable(data) {
        const tbody = document.querySelector('#broadcastHistoryTable tbody');
        if (!tbody) return;
        
        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-muted">Keine Einträge</td></tr>';
            return;
        }
        
        tbody.innerHTML = data.map(b => `
            <tr>
                <td>${new Date(b.sent_at).toLocaleString('de-DE')}</td>
                <td>${this.escapeHtml(b.recipient)}</td>
                <td>${this.escapeHtml(b.subject)}</td>
                <td>${b.events_generated || 0} Events</td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="BroadcastService.viewDetails(${b.id})">
                        Details
                    </button>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Zeigt Broadcast-Details
     */
    async viewDetails(id) {
        try {
            const res = await adminFetch(`/admin/broadcast/id/${id}`);
            const data = await res.json();
            
            // Details in einer Alert (kann später zu Modal erweitert werden)
            alert(`Broadcast ID: ${id}\nEmpfänger: ${data.recipient}\nBetreff: ${data.subject}\nNachricht:\n\n${data.body}`);
            
        } catch (e) {
            console.error('BroadcastService.viewDetails:', e);
            alert('Fehler beim Laden der Details');
        }
    },

    /**
     * Validiert Broadcast-Daten
     */
    validate(data) {
        const errors = [];
        
        if (!data.recipient || data.recipient.trim() === '') {
            errors.push('Empfänger ist erforderlich');
        }
        if (!data.subject || data.subject.trim() === '') {
            errors.push('Betreff ist erforderlich');
        }
        if (!data.body || data.body.trim() === '') {
            errors.push('Nachricht ist erforderlich');
        }
        
        return {
            valid: errors.length === 0,
            errors
        };
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
window.sendBroadcast = function() {
    const recipient = document.getElementById('broadcast-recipient').value;
    const subject = document.getElementById('broadcast-subject').value;
    const body = document.getElementById('broadcast-body').value;
    const type = document.querySelector('input[name="bc-type"]:checked').value;
    
    if (!recipient || !subject || !body) {
        alert('Bitte alle Felder ausfüllen');
        return;
    }
    
    BroadcastService.sendBroadcast({ recipient, subject, body, type });
};

window.loadBroadcastHistory = function() {
    BroadcastService.loadHistory().catch(console.error);
};

// Event Listener für Form-Submit
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('broadcastForm');
    if (form) {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            window.sendBroadcast();
        });
    }
    
    // Initial load der Historie
    setTimeout(() => {
        BroadcastService.loadHistory().catch(console.error);
    }, 500);
});

export default BroadcastService;

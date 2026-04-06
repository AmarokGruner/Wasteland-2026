/**
 * User Service - Extrahiert aus admin.html
 * Benutzer-Verwaltung: CRUD, Rollen, Zuordnungen
 */

export const UserService = {
    /**
     * Speichert Benutzer-Daten lokal
     */
    _users: [],

    /**
     * Lädt alle Benutzer
     */
    async loadUsers() {
        try {
            const res = await adminFetch('/admin/users');
            if (res.status === 401 || res.status === 403) {
                window.logout && window.logout();
                return [];
            }
            
            const users = await res.json();
            this._users = Array.isArray(users) ? users : [];
            
            // Tabelle rendern
            this.renderUsersTable(this._users);
            
            return this._users;
        } catch (e) {
            console.error('UserService.loadUsers:', e);
            this.showError('Fehler beim Laden der Benutzer');
            return [];
        }
    },

    /**
     * Rendert die Benutzer-Tabelle
     */
    renderUsersTable(users) {
        const tbody = document.getElementById('usersTable');
        if (!tbody) return;
        
        if (users.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-muted">Keine Einträge</td></tr>';
            return;
        }
        
        tbody.innerHTML = users.map(u => `
            <tr>
                <td>${u.id}</td>
                <td>${this.escapeHtml(u.username)}</td>
                <td><span class="badge badge-${u.role}">${u.role}</span></td>
                <td>${u.player_name || '-'}</td>
                <td>${u.created_at ? new Date(u.created_at).toLocaleDateString('de-DE') : '-'}</td>
                <td class="actions">
                    <button class="btn btn-danger btn-small" onclick="UserService.deleteUser(${u.id})">
                        Löschen
                    </button>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Erstellt einen neuen Benutzer
     */
    async createUser(data) {
        try {
            const res = await adminFetch('/admin/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: data.username,
                    password: data.password,
                    role: data.role,
                    player_id: data.player_id ? parseInt(data.player_id) : null
                })
            });
            
            if (res.ok) {
                return { success: true, message: 'Benutzer erstellt' };
            } else {
                return { success: false, message: 'Fehler beim Erstellen' };
            }
        } catch (e) {
            console.error('UserService.createUser:', e);
            return { success: false, message: 'Verbindungsfehler' };
        }
    },

    /**
     * Löscht einen Benutzer
     */
    async deleteUser(id) {
        if (!confirm(`Benutzer ID ${id} wirklich löschen?`)) {
            return { success: false };
        }
        
        try {
            const res = await adminFetch(`/admin/users/${id}`, {
                method: 'DELETE'
            });
            
            if (res.ok) {
                await this.loadUsers();
                if (window.showSnackbar) {
                    showSnackbar('✅ Benutzer gelöscht');
                }
                return { success: true };
            } else {
                alert('Fehler beim Löschen');
                return { success: false };
            }
        } catch (e) {
            console.error('UserService.deleteUser:', e);
            alert('Verbindungsfehler');
            return { success: false };
        }
    },

    /**
     * Öffnet das Erstellungs-Modal
     */
    showCreateModal() {
        const modal = document.getElementById('createUserModal');
        if (modal) {
            modal.classList.add('active');
        }
    },

    /**
     * Schließt das Erstellungs-Modal
     */
    closeCreateModal() {
        const modal = document.getElementById('createUserModal');
        const form = document.getElementById('createUserForm');
        if (modal) modal.classList.remove('active');
        if (form) form.reset();
    },

    /**
     * Aktualisiert eine Benutzer-Zeile
     */
    updateUser(userId, updates) {
        const user = this._users.find(u => u.id === userId);
        if (user) {
            Object.assign(user, updates);
            this.renderUsersTable(this._users);
        }
    },

    /**
     * Sucht Benutzer nach ID
     */
    getById(userId) {
        return this._users.find(u => u.id === userId);
    },

    /**
     * Sucht Benutzer nach Username
     */
    getByUsername(username) {
        return this._users.find(u => u.username === username);
    },

    /**
     * Filtert nach Rolle
     */
    filterByRole(role) {
        if (role === 'all') return this._users;
        return this._users.filter(u => u.role === role);
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
     * Verfügbare Rollen
     */
    getRoles() {
        return ['player', 'admin', 'moderator'];
    }
};

// Globale Funktionen für onclick Handler
window.loadUsers = function() {
    UserService.loadUsers().catch(console.error);
};

window.showCreateUserModal = function() {
    UserService.showCreateModal();
};

window.closeCreateUserModal = function() {
    UserService.closeCreateModal();
};

window.deleteUser = function(id) {
    UserService.deleteUser(id).catch(console.error);
};

// Event Listener für CreateUserForm
document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('createUserForm');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            
            const result = await UserService.createUser({
                username: formData.get('username'),
                password: formData.get('password'),
                role: formData.get('role'),
                player_id: formData.get('player_id')
            });
            
            if (result.success) {
                UserService.closeCreateModal();
                await UserService.loadUsers();
                if (window.showSnackbar) {
                    showSnackbar('✅ ' + result.message);
                }
            } else {
                alert(result.message);
            }
            
            form.reset();
        });
    }
});

export default UserService;

/**
 * Offline-Sync für Wasteland Browser Game.
 * 
 * Ermöglicht Spielern, offline zu spielen und Änderungen
 * werden synchronisiert wenn sie wieder online sind.
 * 
 * Verwendung:
 * - Änderungen werden automatisch im LocalStorage gespeichert
 * - Beim Wiederverbinden werden Änderungen mit dem Server synchronisiert
 * - Konflikte werden dem Spieler gemeldet
 */

class OfflineSync {
    constructor() {
        this.storageKey = 'wasteland_offline_changes';
        this.lastSyncTime = 'wasteland_last_sync_time';
        this.isOnline = navigator.onLine;
        
        // Event Listener für Online/Offline-Wechsel
        window.addEventListener('online', () => this.handleOnline());
        window.addEventListener('offline', () => this.handleOffline());
        
        // Automatische Sync-Prüfung alle 30 Sekunden wenn online
        this.syncInterval = setInterval(() => {
            if (this.isOnline) {
                this.checkAndSync();
            }
        }, 30000);
    }
    
    /**
     * Speichert eine Änderung im LocalStorage.
     */
    saveChange(changeType, data) {
        if (!this.isOnline) return;
        
        const changes = this.getStoredChanges();
        const timestamp = new Date().toISOString();
        
        changes.push({
            type: changeType,
            data: data,
            timestamp: timestamp,
            synced: false
        });
        
        localStorage.setItem(this.storageKey, JSON.stringify(changes));
    }
    
    /**
     * Ruft alle gespeicherten Offline-Änderungen ab.
     */
    getStoredChanges() {
        try {
            const data = localStorage.getItem(this.storageKey);
            return data ? JSON.parse(data) : [];
        } catch (e) {
            console.error('OfflineSync: Fehler beim Lesen von LocalStorage:', e);
            return [];
        }
    }
    
    /**
     * Prüft ob Sync mit Server erforderlich ist.
     */
    async checkAndSync() {
        const changes = this.getStoredChanges();
        const unsynced = changes.filter(c => !c.synced);
        
        if (unsynced.length === 0) return;
        
        console.log(`OfflineSync: ${unsynced.length} Änderungen zum Synchronisieren`);
        await this.syncChanges(unsynced);
    }
    
    /**
     * Synchronisiert Änderungen mit dem Server.
     */
    async syncChanges(changes) {
        const token = this.getAuthToken();
        if (!token) {
            console.warn('OfflineSync: Kein Auth-Token verfügbar');
            return;
        }
        
        // Gruppieren nach Typ
        const provinces = changes.filter(c => c.type === 'province').map(c => c.data);
        const armies = changes.filter(c => c.type === 'army').map(c => c.data);
        
        try {
            const response = await fetch(`/api/offline/sync?token=${encodeURIComponent(token)}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provinces, armies })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // Als synchronisiert markieren
                changes.forEach(c => c.synced = true);
                localStorage.setItem(this.storageKey, JSON.stringify(changes));
                
                // Konflikte melden
                if (result.conflicts && result.conflicts.length > 0) {
                    this.showConflictAlert(result.conflicts);
                }
                
                console.log(`OfflineSync: ${result.applied_changes} Änderungen synchronisiert`);
            } else {
                console.error('OfflineSync: Sync fehlgeschlagen', result);
            }
        } catch (e) {
            console.error('OfflineSync: Netzwerkfehler beim Synchronisieren:', e);
        }
    }
    
    /**
     * Ruft aktuelle Server-Daten ab.
     */
    async fetchServerData() {
        const token = this.getAuthToken();
        if (!token) return null;
        
        try {
            const response = await fetch(`/api/offline/changes?token=${encodeURIComponent(token)}`);
            const result = await response.json();
            
            if (result.success) {
                return result.data;
            }
        } catch (e) {
            console.error('OfflineSync: Fehler beim Abrufen der Server-Daten:', e);
        }
        
        return null;
    }
    
    /**
     * Behandelt Online-Wechsel.
     */
    handleOnline() {
        this.isOnline = true;
        console.log('OfflineSync: Online — Synchronisierung gestartet');
        
        // Sofortigen Sync versuchen
        this.checkAndSync();
    }
    
    /**
     * Behandelt Offline-Wechsel.
     */
    handleOffline() {
        this.isOnline = false;
        console.log('OfflineSync: Offline — Änderungen werden lokal gespeichert');
    }
    
    /**
     * Zeigt Konflikt-Warnung an.
     */
    showConflictAlert(conflicts) {
        const conflictMessages = conflicts.map(c => 
            `Konflikt bei Provinz ${c.province_id}: Server hat neuere Änderungen`
        ).join('\n');
        
        alert(`Sync-Konflikte:\n\n${conflictMessages}\n\nBitte laden Sie die Seite neu.`);
    }
    
    /**
     * Ruft das Auth-Token aus LocalStorage ab.
     */
    getAuthToken() {
        try {
            const data = JSON.parse(localStorage.getItem('wasteland_auth') || '{}');
            return data.access_token || null;
        } catch (e) {
            return null;
        }
    }
    
    /**
     * Bereinigt alte Sync-Daten (älter als 7 Tage).
     */
    cleanupOldData() {
        const changes = this.getStoredChanges();
        const cutoff = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
        
        const cleaned = changes.filter(c => {
            const changeDate = new Date(c.timestamp);
            return changeDate > cutoff;
        });
        
        localStorage.setItem(this.storageKey, JSON.stringify(cleaned));
    }
    
    /**
     * Cleanup alle 6 Stunden.
     */
    startCleanup() {
        setInterval(() => this.cleanupOldData(), 6 * 60 * 60 * 1000);
    }
    
    /**
     * Cleanup beim Laden der Seite.
     */
    init() {
        this.cleanupOldData();
        this.startCleanup();
        
        // Ersten Sync versuchen wenn online
        if (this.isOnline) {
            this.checkAndSync();
        }
    }
    
    /**
     * Cleanup beim Verlassen der Seite.
     */
    destroy() {
        clearInterval(this.syncInterval);
    }
}

// Initialisieren wenn DOM geladen ist
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const sync = new OfflineSync();
        sync.init();
        
        // Global verfügbar machen für andere Skripte
        window.offlineSync = sync;
    });
} else {
    const sync = new OfflineSync();
    sync.init();
    window.offlineSync = sync;
}

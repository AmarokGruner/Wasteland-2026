/**
 * Webcrawler Service - Extrahiert aus admin.html
 * Crawler starten, Status prüfen, Änderungen freigeben/ablehnen
 */

export const CrawlerService = {
    /**
     * Lädt Crawler-Status
     */
    async loadStatus() {
        try {
            const res = await adminFetch('/api/admin/crawler/status');
            const data = await res.json();
            
            if (data.running) {
                this.showRunningStatus();
                this.pollStatus();
            } else if (data.last_run) {
                this.showCompletedStatus();
                await this.loadResults();
            }
            
            return data;
        } catch (e) {
            console.error('CrawlerService.loadStatus:', e);
            this.showError('Fehler beim Laden des Status');
            return null;
        }
    },

    /**
     * Zeigt laufenden Status an
     */
    showRunningStatus() {
        const statusEl = document.getElementById('crawlerStatus');
        if (statusEl) {
            statusEl.style.display = 'block';
            const indicator = statusEl.querySelector('.status-running');
            if (indicator) {
                indicator.textContent = '🔄 Crawler läuft...';
            }
        }
        
        const resultsEl = document.getElementById('crawlerResults');
        if (resultsEl) {
            resultsEl.style.display = 'none';
        }
    },

    /**
     * Zeigt abgeschlossenen Status an
     */
    showCompletedStatus() {
        const statusEl = document.getElementById('crawlerStatus');
        if (statusEl) {
            const indicator = statusEl.querySelector('.status-running');
            if (indicator) {
                indicator.textContent = '✅ Crawler abgeschlossen';
            }
        }
    },

    /**
     * Pollt den Status alle 2 Sekunden
     */
    pollStatus() {
        this._pollInterval = setInterval(async () => {
            try {
                const res = await adminFetch('/api/admin/crawler/status');
                const data = await res.json();
                
                if (!data.running) {
                    clearInterval(this._pollInterval);
                    this.showCompletedStatus();
                    
                    if (window.showSnackbar) {
                        showSnackbar('✅ Crawler abgeschlossen');
                    }
                    
                    await this.loadResults();
                }
            } catch (e) {
                console.error('Poll status error:', e);
            }
        }, 2000);
    },

    /**
     * Lädtpending Änderungen
     */
    async loadResults() {
        try {
            const res = await adminFetch('/api/admin/crawler/pending');
            const data = await res.json();
            
            if (data.pending && data.pending.length > 0) {
                document.getElementById('crawlerResults').style.display = 'block';
                document.getElementById('resultsSummary').textContent = 
                    `Gefunden: ${data.total} ausstehende Änderungen`;
                
                this.renderResultsTable(data.pending);
            } else {
                document.getElementById('crawlerResults').style.display = 'none';
            }
        } catch (e) {
            console.error('CrawlerService.loadResults:', e);
            this.showError('Fehler beim Laden der Ergebnisse');
        }
    },

    /**
     * Rendert die Ergebnisse-Tabelle
     */
    renderResultsTable(pending) {
        const tbody = document.querySelector('#crawlerChangesTable tbody');
        if (!tbody) return;
        
        tbody.innerHTML = pending.map(item => `
            <tr>
                <td>
                    <span class="badge badge-${item.action === 'INSERT' ? 'success' : 
                                  item.action === 'UPDATE' ? 'warning' : 'danger'}">
                        ${item.action}
                    </span>
                </td>
                <td>${this.escapeHtml(item.category)}</td>
                <td>${item.record_id}</td>
                <td>-</td>
                <td>
                    <button class="btn btn-small btn-primary" onclick="CrawlerService.viewChange(${item.id})">👁️</button>
                    <button class="btn btn-small btn-success" onclick="CrawlerService.approveChange(${item.id})">✅</button>
                    <button class="btn btn-small btn-danger" onclick="CrawlerService.rejectChange(${item.id})">❌</button>
                </td>
            </tr>
        `).join('');
    },

    /**
     * Startet den Crawler
     */
    async startCrawler(categories = null, dryRun = false) {
        try {
            const res = await adminFetch('/api/admin/crawler/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    categories: categories && categories.length ? categories : null,
                    dry_run: dryRun
                })
            });
            
            if (res.ok) {
                if (window.showSnackbar) {
                    showSnackbar('🤖 Crawler gestartet');
                }
                
                document.getElementById('crawlerStatus').style.display = 'block';
                document.getElementById('crawlerResults').style.display = 'none';
                
                await this.loadStatus();
                return true;
            } else {
                if (window.showSnackbar) {
                    showSnackbar('❌ Fehler beim Starten');
                }
                return false;
            }
        } catch (e) {
            console.error('CrawlerService.startCrawler:', e);
            if (window.showSnackbar) {
                showSnackbar('❌ Verbindungsfehler');
            }
            return false;
        }
    },

    /**
     * Genehmigt eine Änderung
     */
    async approveChange(itemId) {
        try {
            const res = await adminFetch(`/api/admin/crawler/approve/${itemId}`, {
                method: 'POST'
            });
            
            if (res.ok) {
                if (window.showSnackbar) {
                    showSnackbar('✅ Änderung freigegeben');
                }
                await this.loadResults();
                return true;
            } else {
                if (window.showSnackbar) {
                    showSnackbar('❌ Fehler beim Freigeben');
                }
                return false;
            }
        } catch (e) {
            console.error('CrawlerService.approveChange:', e);
            return false;
        }
    },

    /**
     * Lehnt eine Änderung ab
     */
    async rejectChange(itemId) {
        try {
            const res = await adminFetch(`/api/admin/crawler/reject/${itemId}`, {
                method: 'POST'
            });
            
            if (res.ok) {
                if (window.showSnackbar) {
                    showSnackbar('❌ Änderung abgelehnt');
                }
                await this.loadResults();
                return true;
            } else {
                if (window.showSnackbar) {
                    showSnackbar('❌ Fehler beim Ablehnen');
                }
                return false;
            }
        } catch (e) {
            console.error('CrawlerService.rejectChange:', e);
            return false;
        }
    },

    /**
     * Zeigt Änderungsdetails (Placeholder)
     */
    async viewChange(itemId) {
        alert(`Details für Änderung ${itemId} werden bald angezeigt`);
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
     * Stoppt den Poll-Interval
     */
    stopPoll() {
        if (this._pollInterval) {
            clearInterval(this._pollInterval);
            this._pollInterval = null;
        }
    }
};

// Globale Funktionen für onclick Handler
window.loadCrawlerStatus = function() {
    CrawlerService.loadStatus().catch(console.error);
};

window.startCrawler = function() {
    const checkboxes = document.querySelectorAll('input[name="crawl-category"]:checked');
    const categories = Array.from(checkboxes).map(cb => cb.value).filter(v => v !== 'all');
    const dryRun = document.getElementById('dry-run')?.checked || false;
    
    CrawlerService.startCrawler(categories, dryRun).catch(console.error);
};

window.approveCrawlChange = function(itemId) {
    CrawlerService.approveChange(itemId).catch(console.error);
};

window.rejectCrawlChange = function(itemId) {
    CrawlerService.rejectChange(itemId).catch(console.error);
};

window.viewCrawlChange = function(itemId) {
    CrawlerService.viewChange(itemId);
};

// Event Listener
document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('startCrawl');
    if (startBtn) {
        startBtn.addEventListener('click', () => {
            window.startCrawler();
        });
    }
    
    const stopBtn = document.getElementById('stopCrawl');
    if (stopBtn) {
        stopBtn.addEventListener('click', () => {
            CrawlerService.stopPoll();
            showSnackbar('Crawler wurde gestoppt');
        });
    }
});

export default CrawlerService;

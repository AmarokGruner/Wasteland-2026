// Admin Router - Tab-Navigation und State-Management
// Extrahiert aus admin.html für bessere Wartbarkeit

export const AdminRouter = {
    /**
     * Zeige einen spezifischen Tab und speichere State
     */
    navigate(tabId) {
        // Remove active class from all tabs
        document.querySelectorAll('.admin-nav-item').forEach(item => {
            item.classList.remove('active');
        });
        
        // Hide all sections
        document.querySelectorAll('.admin-section').forEach(section => {
            section.classList.remove('active');
        });
        
        // Activate requested tab
        const tabElement = document.querySelector(`.admin-nav-item[data-tab="${tabId}"]`);
        if (tabElement) {
            tabElement.classList.add('active');
        }
        
        // Show corresponding section
        const sectionElement = document.getElementById(`${tabId}-section`);
        if (sectionElement) {
            sectionElement.classList.add('active');
        }
        
        // Save to localStorage for persistence
        localStorage.setItem('admin_active_tab', tabId);
        
        // Update URL hash
        window.location.hash = tabId;
        
        // Load data for this tab
        this.loadTabData(tabId);
    },
    
    /**
     * Lade Daten basierend auf Tab-ID
     */
    loadTabData(tabId) {
        const loaders = {
            'dashboard': () => window.loadDashboard && window.loadDashboard(),
            'players_list': () => window.loadAdminPlayers && window.loadAdminPlayers(),
            'broadcast': () => window.loadBroadcast && window.loadBroadcast(),
            'gamelog': () => window.loadGamelog && window.loadGamelog(),
            'users': () => window.loadUsers && window.loadUsers(),
            'buildings': () => window.loadBuildings && window.loadBuildings(),
            'ressourcen': () => window.loadRessourcen && window.loadRessourcen(),
            'vorkommen': () => window.loadVorkommen && window.loadVorkommen(),
            'city_grid': () => window.loadCityGridConfig && window.loadCityGridConfig(),
            'gebaeude_felder': () => window.loadGebaeudeFelder && window.loadGebaeudeFelder(),
            'terrain': () => window.loadTerrain && window.loadTerrain(),
            'artikel': () => window.loadArtikel && window.loadArtikel(),
            'einheiten': () => window.loadEinheiten && window.loadEinheiten(),
            'lebewesen': () => window.loadLebewesen && window.loadLebewesen(),
            'regierungsformen': () => window.loadRegierungsformen && window.loadRegierungsformen(),
            'armies': () => window.loadArmies && window.loadArmies(),
            'audit_logs': () => window.loadAuditLogs && window.loadAuditLogs(),
            'players': () => window.loadPlayerAdmin && window.loadPlayerAdmin(),
            'worldmap': () => window.loadWorldMapAdmin && window.loadWorldMapAdmin(),
            'ticks': () => window.loadTickEngine && window.loadTickEngine(),
        };
        
        if (loaders[tabId]) {
            loaders[tabId]();
        }
    },
    
    /**
     * Initialisiere Tab-Navigation
     */
    init() {
        // Get initial tab from URL hash or localStorage
        const savedTab = localStorage.getItem('admin_active_tab') || 
                         window.location.hash.substring(1) || 
                         'dashboard';
        
        // Set initial active state
        this.navigate(savedTab);
        
        // Add click listeners to nav items
        document.querySelectorAll('.admin-nav-item[data-tab]').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const tabId = item.getAttribute('data-tab');
                this.navigate(tabId);
            });
        });
    }
};

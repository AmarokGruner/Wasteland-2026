// worldmap.js – Weltkarten-Logik
// Verbrannte Zone v2.1.1 – Fix: case-insensitiver Terrain-Key-Lookup
// Stand: 2026-02-25

const WORLD_SIZE = 50;
window.WORLD_MAP  = [];

// ─────────────────────────────────────────────────────────────────────────────
// TERRAIN-GRAFIK-KONFIGURATION
// ─────────────────────────────────────────────────────────────────────────────

// Interner Key / Terrain-Name → Dateiname in /terrains/ (ohne Extension)
// WICHTIG: Map wird in Kleinbuchstaben normalisiert (toLowerCase) damit
// sowohl 'Grasland' als auch 'grasland' aus world-data.js funktionieren.
const TERRAIN_FILENAME_MAP_RAW = {
    // ── Interne Weltkarten-Keys (englisch) ───────────────────────────────
    ocean:     'Ozean',
    grass:     'Grasland',
    forest:    'Wald',
    mountain:  'Grasgebirge',
    desert:    'Wueste',
    wasteland: 'Oedland',
    player:    'Grasland',

    // ── Deutsche Terrain-Namen ────────────────────────────────────────────
    'brachfelsland':   'Brachfelsland',
    'brachgebirge':    'Brachgebirge',
    'brachhügel':      'Brachhuegel',
    'brachland':       'Brachland',
    'dschungel':       'Dschungel',
    'eiswüste':        'Eiswueste',
    'felsgebirge':     'Felsgebirge',
    'grasfelsland':    'Grasfelsland',
    'grasgebirge':     'Grasgebirge',
    'grashügel':       'Grashuegel',
    'grasland':        'Grasland',
    'grünfelsland':    'Gruenfelsland',
    'grüngebirge':     'Gruengebirge',
    'grünhügel':       'Gruenhuegel',
    'grünland':        'Gruenland',
    'hochnebelwald':   'Hochnebelwald',
    'ozean':           'Ozean',
    'pampa':           'Pampa',
    'pampafelsland':   'Pampafelsland',
    'pampagebirge':    'Pampagebirge',
    'plateau':         'Plateau',
    'regenwald':       'Regenwald',
    'sanddünen':       'Sandduenen',
    'savanne':         'Savanne',
    'savannenfelsland':'Savannenfelsland',
    'savannengebirge': 'Savannengebirge',
    'savannenhügel':   'Savannenhuegel',
    'steppe':          'Steppe',
    'steppfelsland':   'Steppfelsland',
    'steppgebirge':    'Steppgebirge',
    'stepphügel':      'Stepphuegel',
    'sumpfland':       'Sumpfland',
    'tropensumpf':     'Tropensumpf',
    'wald':            'Wald',
    'weidefelsland':   'Weidefelsland',
    'weideland':       'Weideland',
    'wüste':           'Wueste',
    'ödfelsland':      'Oedfelsland',
    'ödgebirge':       'Oedgebirge',
    'ödhügel':         'Oedhuegel',
    'ödland':          'Oedland',
    'steinwüste':      'Steinwueste',
};

// Normalisierte Map (alle Keys lowercase) für robusten Lookup
const TERRAIN_FILENAME_MAP = {};
for (const [k, v] of Object.entries(TERRAIN_FILENAME_MAP_RAW)) {
    TERRAIN_FILENAME_MAP[k.toLowerCase()] = v;
}

const TERRAIN_IMG_BASE = '/terrains/';
const TERRAIN_IMG_EXT  = '.gif';

// Cache: Dateiname → true (vorhanden) | false (nicht gefunden)
const terrainImageCache = {};

// ─────────────────────────────────────────────────────────────────────────────
// HILFSFUNKTIONEN
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Wandelt beliebige deutsche Terrain-Namen in gültige Dateinamen um.
 * Wird als Fallback genutzt wenn der Key nicht in TERRAIN_FILENAME_MAP steht.
 */
function toTerrainFilename(name) {
    return name
        .replace(/ä/g, 'ae').replace(/Ä/g, 'Ae')
        .replace(/ö/g, 'oe').replace(/Ö/g, 'Oe')
        .replace(/ü/g, 'ue').replace(/Ü/g, 'Ue')
        .replace(/ß/g, 'ss')
        .replace(/\s+/g, '');
}

/**
 * Gibt die backgroundImage-URL zurück oder null (→ CSS-Fallbackfarbe).
 * Key wird normalisiert (toLowerCase + trim) vor dem Lookup.
 */
function getTerrainBgImage(terrainKey) {
    const key = terrainKey.toLowerCase().trim();
    let filename;

    if (Object.prototype.hasOwnProperty.call(TERRAIN_FILENAME_MAP, key)) {
        filename = TERRAIN_FILENAME_MAP[key];
    } else {
        // Fallback: Umlaute konvertieren
        filename = toTerrainFilename(terrainKey);
    }

    if (!filename) return null;
    if (terrainImageCache[filename] === false) return null;
    return `url('${TERRAIN_IMG_BASE}${filename}${TERRAIN_IMG_EXT}')`;
}

// ─────────────────────────────────────────────────────────────────────────────
// BILD-PRELOADER
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Lädt ALLE Terrain-Grafiken vorab und füllt terrainImageCache.
 * renderWorldMap() wird erst nach Abschluss aufgerufen.
 */
async function preloadTerrainImages() {
    const filenames = new Set(
        Object.values(TERRAIN_FILENAME_MAP).filter(Boolean)
    );

    const promises = [...filenames].map(filename => new Promise(resolve => {
        const img    = new Image();
        img.onload  = () => { terrainImageCache[filename] = true;  resolve(); };
        img.onerror = () => { terrainImageCache[filename] = false; resolve(); };
        img.src     = `${TERRAIN_IMG_BASE}${filename}${TERRAIN_IMG_EXT}`;
    }));

    await Promise.all(promises);

    const loaded  = Object.values(terrainImageCache).filter(v => v === true).length;
    const missing = Object.values(terrainImageCache).filter(v => v === false).length;
    console.log(`🖼️ Terrain-Grafiken: ${loaded} geladen, ${missing} nicht gefunden (Farbfallback)`);

    if (missing > 0) {
        const missingList = Object.entries(terrainImageCache)
            .filter(([,v]) => v === false)
            .map(([k]) => k)
            .join(', ');
        console.log(`   ⚠️ Fehlende GIFs (Farbfallback aktiv): ${missingList}`);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// WELTKARTE
// ─────────────────────────────────────────────────────────────────────────────

function initWorldMap() {
    console.log('🗺️ Lade statische Weltkarte...');
    if (typeof window.FIXED_WORLD_MAP !== 'undefined') {
        window.WORLD_MAP = window.FIXED_WORLD_MAP;
        console.log('✅ Statische Weltkarte geladen');
    } else {
        console.error('⚠️ FIXED_WORLD_MAP nicht gefunden!');
        window.WORLD_MAP = generateEmptyMap();
    }

    preloadTerrainImages().then(() => renderWorldMap());
}

function generateEmptyMap() {
    const map = [];
    for (let y = 0; y < WORLD_SIZE; y++) {
        const row = [];
        for (let x = 0; x < WORLD_SIZE; x++) row.push('ocean');
        map.push(row);
    }
    return map;
}

function renderWorldMap() {
    const container = document.getElementById('worldmap');
    container.innerHTML = '';
    container.style.gridTemplateColumns = `repeat(${WORLD_SIZE}, var(--cell-size))`;
    container.style.gridTemplateRows    = `repeat(${WORLD_SIZE}, var(--cell-size))`;

    for (let y = 0; y < WORLD_SIZE; y++) {
        for (let x = 0; x < WORLD_SIZE; x++) {
            const terrainKey = window.WORLD_MAP[y][x];
            const cell       = document.createElement('div');

            cell.className         = `world-cell ${terrainKey}`;
            cell.dataset.x         = x;
            cell.dataset.y         = y;
            cell.dataset.terrain   = terrainKey;

            // ── Terrain-Grafik (Grafik vorhanden → anzeigen, sonst CSS-Farbe)
            const bgImage = getTerrainBgImage(terrainKey);
            if (bgImage) {
                cell.style.backgroundImage    = bgImage;
                cell.style.backgroundSize     = 'cover';
                cell.style.backgroundRepeat   = 'no-repeat';
                cell.style.backgroundPosition = 'center';
            }

            // ── Spieler-Marker
            if (terrainKey === 'player') {
                cell.classList.add('player-cell');
                const marker     = document.createElement('span');
                marker.className = 'player-marker';
                marker.textContent = '🏠';
                cell.appendChild(marker);
            }

            // ── Tooltip
            if (typeof window.TERRAIN_TYPES !== 'undefined') {
                const terrain = window.TERRAIN_TYPES[terrainKey];
                cell.title = terrain
                    ? `(${x}, ${y}) – ${terrain.name}\n${terrain.description}`
                    : `(${x}, ${y}) – ${terrainKey}`;
            } else {
                cell.title = `(${x}, ${y}) – ${terrainKey}`;
            }

            cell.onclick = () => selectWorldProvince(x, y);
            container.appendChild(cell);
        }
    }

    console.log(`✅ Weltkarte gerendert: ${WORLD_SIZE}×${WORLD_SIZE} Felder`);
}

// ─────────────────────────────────────────────────────────────────────────────
// PROVINZ AUSWÄHLEN
// ─────────────────────────────────────────────────────────────────────────────

function selectWorldProvince(x, y) {
    const terrainType = window.WORLD_MAP[y][x];
    if (typeof window.TERRAIN_TYPES !== 'undefined') {
        const terrain = window.TERRAIN_TYPES[terrainType];
        if (terrain && !terrain.playable) {
            alert(`${terrain.icon} ${terrain.name} ist nicht spielbar!`);
            return;
        }
    }
    console.log(`Provinz ausgewählt: (${x}, ${y}) – ${terrainType}`);
    if (typeof window.switchView === 'function') {
        window.switchView('province', x, y);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// EXPORTS
// ─────────────────────────────────────────────────────────────────────────────

if (typeof window !== 'undefined') {
    window.initWorldMap         = initWorldMap;
    window.renderWorldMap       = renderWorldMap;
    window.selectWorldProvince  = selectWorldProvince;
    window.toTerrainFilename    = toTerrainFilename;
    window.getTerrainBgImage    = getTerrainBgImage;
    window.terrainImageCache    = terrainImageCache;
    window.WORLD_SIZE           = WORLD_SIZE;
    window.TERRAIN_FILENAME_MAP = TERRAIN_FILENAME_MAP;
}

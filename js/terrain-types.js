// terrain-types.js - Terrain-Definitionen und Eigenschaften (Synchronisiert mit Backend)

const TERRAIN_TYPES = {
    // ── OLD KEYS (for backward compatibility with world-data.js) ──────────
    ocean: { name: 'Ozean', color: '#1a4d7a', icon: '🌊', playable: false, description: 'Nicht bebaubar' },
    desert: { name: 'Wüste', color: '#d4a76a', icon: '🏜️', playable: true, description: 'Reich an Mineralien' },
    grass: { name: 'Grasland', color: '#5a8c3a', icon: '🌾', playable: true, description: 'Ideal für Landwirtschaft' },
    mountain: { name: 'Grasgebirge', color: '#888888', icon: '⛰️', playable: true, description: 'Reich an Erzen' },
    forest: { name: 'Wald', color: '#2d5016', icon: '🌲', playable: true, description: 'Holzabbau möglich' },
    wasteland: { name: 'Ödland', color: '#3a2a1a', icon: '☠️', playable: true, description: 'Verbrannte Zone' },
    player: { name: 'Startposition', color: '#5a8c3a', icon: '🏠', playable: true, description: 'Deine Hauptbasis' },

    // ── NEW 42 TERRAINS (Backend Sync) ───────────────────────────────────
    'Grasland': { name: 'Grasland', color: '#5a8c3a', icon: '🌾', playable: true, description: 'Saftige, weite, grüne Wiesen. Ideal für Viehzucht und Landwirtschaft.' },
    'Steppe': { name: 'Steppe', color: '#8c8c3a', icon: '🌾', playable: true, description: 'Trockener Boden, gelbes Gras. Gut für genügsame Tiere und Lehmabbau.' },
    'Ödland': { name: 'Ödland', color: '#3a2a1a', icon: '☠️', playable: true, description: 'Gefährliche Einöde. Reich an Lehm, Sand und gelegentlich Erdöl.' },
    'Wald': { name: 'Wald', color: '#2d5016', icon: '🌲', playable: true, description: 'Dichtes Buschwerk und mächtige Bäume. Hervorragend für Holzabbau.' },
    'Grasfelsland': { name: 'Grasfelsland', color: '#5a5a3a', icon: '⛰️', playable: true, description: 'Wiesen mit felsigen Abschnitten. Gut für Steine und Kies.' },
    'Sumpfland': { name: 'Sumpfland', color: '#1a3a1a', icon: '🌱', playable: true, description: 'Sehr feucht. Reich an Wasser, Schilf und Holz.' },
    'Grashügel': { name: 'Grashügel', color: '#4a7c2a', icon: '⛰️', playable: true, description: 'Hügelige Graslandschaft. Gut für Tierzucht und Braunkohle.' },
    'Grasgebirge': { name: 'Grasgebirge', color: '#444444', icon: '⛰️', playable: true, description: 'Gebirgig mit Grasflächen. Ausgezeichnete Wasserversorgung und Erze.' },
    'Eiswüste': { name: 'Eiswüste', color: '#ffffff', icon: '❄️', playable: true, description: 'Eiskalte Einöde. Beherbergt oft Erdölvorkommen.' },
    'Wüste': { name: 'Wüste', color: '#d4a76a', icon: '🏜️', playable: true, description: 'Unwirtlich und trocken. Reich an Sand, Salz und Erdöl.' },
    'Tropensumpf': { name: 'Tropensumpf', color: '#0d3d0d', icon: '🌴', playable: true, description: 'Schwüle Hitze und Sumpf. Quelle für wertvolle Edelhölzer.' },
    'Dschungel': { name: 'Dschungel', color: '#006400', icon: '🌴', playable: true, description: 'Wilde Pflanzenwelt. Bietet reichlich Nahrung und Tropenholz.' },
    'Sanddünen': { name: 'Sanddünen', color: '#edc9af', icon: '🏜️', playable: true, description: 'Wandernde Sandberge. Garantierte Sandvorkommen.' },
    'Felsgebirge': { name: 'Felsgebirge', color: '#555555', icon: '⛰️', playable: true, description: 'Karge, trockene Gipfel. Reich an verschiedensten Ressourcen.' },
    'Ödhügel': { name: 'Ödhügel', color: '#4a3a2a', icon: '⛰️', playable: true, description: 'Einsame Hügel. Gut geeignet zum Abbau von Lehm und Braunkohle.' },
    'Ödgebirge': { name: 'Ödgebirge', color: '#333333', icon: '⛰️', playable: true, description: 'Steiniges Gebirge. Heimat der Bluescorpions und reicher Erze.' },
    'Stepphügel': { name: 'Stepphügel', color: '#7c7c2a', icon: '⛰️', playable: true, description: 'Trockene Hügel. Bietet Chancen auf viele verschiedene Ressourcen.' },
    'Steppgebirge': { name: 'Steppgebirge', color: '#666666', icon: '⛰️', playable: true, description: 'Karges Hochgebirge. Sehr ertragreich im Bergbau.' },
    'Ödfelsland': { name: 'Ödfelsland', color: '#4a4a2a', icon: '⛰️', playable: true, description: 'Steinige Einöde. Lockt durch zahlreiche verborgene Schätze.' },
    'Steppfelsland': { name: 'Steppfelsland', color: '#6c6c2a', icon: '⛰️', playable: true, description: 'Grassteppen auf felsigem Grund. Gut für Kies und Braunkohle.' },
    'Grünland': { name: 'Grünland', color: '#32cd32', icon: '🪴', playable: true, description: 'Saftige Wiesen. Ideal für hochwertige Plantagen (Tabak, Orangen).' },
    'Savanne': { name: 'Savanne', color: '#eee8aa', icon: '🦓', playable: true, description: 'Trockenes Grasland. Heimat großer Ziegenherden.' },
    'Grünhügel': { name: 'Grünhügel', color: '#228b22', icon: '⛰️', playable: true, description: 'Hügeliges Grünland. Gut für Weinbau und Bodenschätze.' },
    'Savannenhügel': { name: 'Savannenhügel', color: '#f0e68c', icon: '⛰️', playable: true, description: 'Hügelige Savanne. Gut für Ziegenzucht und Lehm.' },
    'Grüngebirge': { name: 'Grüngebirge', color: '#2e8b57', icon: '⛰️', playable: true, description: 'Grüne Bergriesen mit exzellenter Wasserversorgung.' },
    'Savannengebirge': { name: 'Savannengebirge', color: '#bdb76b', icon: '⛰️', playable: true, description: 'Karges Gebirge, reich an Metallerzen und Schwefel.' },
    'Grünfelsland': { name: 'Grünfelsland', color: '#00fa9a', icon: '⛰️', playable: true, description: 'Felsiges Grünland. Bietet Steine und seltene Ressourcen.' },
    'Savannenfelsland': { name: 'Savannenfelsland', color: '#f5f5dc', icon: '⛰️', playable: true, description: 'Steinige Savanne. Geeignet für Ziegen und Kiesabbau.' },
    'Brachland': { name: 'Brachland', color: '#8b4513', icon: '🍂', playable: true, description: 'Unwirtliches Land, Heimat der Bukhts. Reich an Lehm.' },
    'Brachfelsland': { name: 'Brachfelsland', color: '#a0522d', icon: '⛰️', playable: true, description: 'Karges Steinland mit Verlockung auf Reichtum durch Bergbau.' },
    'Brachhügel': { name: 'Brachhügel', color: '#d2691e', icon: '⛰️', playable: true, description: 'Einsame Hügel. Geeignet zum Abbau von Lehm und Sand.' },
    'Brachgebirge': { name: 'Brachgebirge', color: '#5d4037', icon: '⛰️', playable: true, description: 'Schroffe Gipfel, reich an Bodenschätzen und Steinen.' },
    'Ozean': { name: 'Ozean', color: '#1a4d7a', icon: '🌊', playable: false, description: 'Unerforschte Tiefen. Quelle für Fisch, Wasser und Salz.' },
    'Pampa': { name: 'Pampa', color: '#7cfc00', icon: '🐃', playable: true, description: 'Trockenes Grasland für Lamas. Bietet ölige Gräser.' },
    'Weideland': { name: 'Weideland', color: '#adff2f', icon: '🐄', playable: true, description: 'Saftige Weiden. Ideal für intensive Landwirtschaft.' },
    'Regenwald': { name: 'Regenwald', color: '#2e8b57', icon: '🌧️', playable: true, description: 'Ständige Regengüsse. Reich an Nahrung und Tropenholz.' },
    'Pampagebirge': { name: 'Pampagebirge', color: '#556b2f', icon: '⛰️', playable: true, description: 'Karges Gebirge mit öligen Gräsern und vielen Erzen.' },
    'Plateau': { name: 'Plateau', color: '#808000', icon: '🪜', playable: true, description: 'Hochgelegenes, ebenes Terrain mit guter Wasserversorgung.' },
    'Hochnebelwald': { name: 'Hochnebelwald', color: '#2f4f4f', icon: '🌫️', playable: true, description: 'Hochgelegener Nebelwald. Feucht und vegetationsreich.' },
    'Pampafelsland': { name: 'Pampafelsland', color: '#6b8e23', icon: '⛰️', playable: true, description: 'Trockene Pampasteppe über steinigem Grund.' },
    'Weidefelsland': { name: 'Weidefelsland', color: '#9acd32', icon: '⛰️', playable: true, description: 'Grüne Weiden über Fels. Gut für Steingewinnung.' },
    'Steinwüste': { name: 'Steinwüste', color: '#a9a9a9', icon: '⛰️', playable: true, description: 'Extrem trockenes Steinland. Landwirtschaft fast unmöglich.' },
};

// Gebäude-Definitionen
const BUILDING_TYPES = {
    building_mine: {
        name: 'Mine',
        icon: '⛏️',
        cost: { iron: 500, steel: 200 },
        requiredTerrain: ['mountain', 'desert', 'player', 'Felsgebirge', 'Ödgebirge', 'Steppgebirge', 'Brachgebirge', 'Grüngebirge', 'Savannengebirge', 'Pampagebirge', 'Grasgebirge'],
        produces: { iron: 10, stone: 5 },
        description: 'Fördert Erz aus dem Boden'
    },
    building_farm: {
        name: 'Farm',
        icon: '🌾',
        cost: { iron: 300, wood: 200 },
        requiredTerrain: ['grass', 'player', 'Grasland', 'Grünland', 'Weideland', 'Pampa', 'Savanne', 'Steppe'],
        produces: { food: 15 },
        description: 'Produziert Nahrung'
    },
    building_sawmill: {
        name: 'Sägewerk',
        icon: '🪓',
        cost: { iron: 400, steel: 100 },
        requiredTerrain: ['forest', 'Wald', 'Dschungel', 'Regenwald', 'Hochnebelwald'],
        produces: { wood: 20 },
        description: 'Verarbeitet Holz'
    },
    building_quarry: {
        name: 'Steinbruch',
        icon: '🪨',
        cost: { iron: 600, steel: 200 },
        requiredTerrain: ['mountain', 'Felsgebirge', 'Ödgebirge', 'Steppgebirge', 'Brachgebirge', 'Grasfelsland', 'Grünfelsland', 'Savannenfelsland', 'Pampafelsland', 'Weidefelsland', 'Steinwüste'],
        produces: { stone: 15 },
        description: 'Gewinnt Stein'
    },
    building_solar: {
        name: 'Solarkraftwerk',
        icon: '☀️',
        cost: { iron: 800, steel: 400 },
        requiredTerrain: ['desert', 'Wüste', 'Sanddünen'],
        produces: { energy: 25 },
        description: 'Nutzt Sonnenkraft'
    },
    building_windmill: {
        name: 'Windmühle',
        icon: '💨',
        cost: { iron: 500, steel: 300 },
        requiredTerrain: ['grass', 'Grasland', 'Grünland', 'Weideland', 'Pampa', 'Steppe', 'Savanne'],
        produces: { energy: 15 },
        description: 'Erzeugt Windenergie'
    },
    building_hunter: {
        name: 'Jägerhütte',
        icon: '🏹',
        cost: { wood: 300, iron: 100 },
        requiredTerrain: ['forest', 'Wald', 'Dschungel', 'Regenwald', 'Hochnebelwald'],
        produces: { food: 10 },
        description: 'Jagt Wild'
    },
    building_scrapyard: {
        name: 'Schrottplatz',
        icon: '🔩',
        cost: { iron: 200 },
        requiredTerrain: ['wasteland', 'Ödland', 'Brachland'],
        produces: { scrap: 20, iron: 5 },
        description: 'Sammelt Schrott'
    },
    building_refinery: {
        name: 'Raffinerie',
        icon: '🏗️',
        cost: { iron: 1200, steel: 500 },
        requiredTerrain: ['wasteland', 'desert', 'player', 'Ödland', 'Wüste', 'Eiswüste'],
        produces: { fuel: 10 },
        description: 'Raffiniert Treibstoff'
    },
    building_factory: {
        name: 'Fabrik',
        icon: '🏭',
        cost: { iron: 1000, steel: 400 },
        requiredTerrain: ['grass', 'player', 'wasteland', 'Grasland', 'Grünland', 'Weideland', 'Ödland'],
        produces: { steel: 8 },
        description: 'Verarbeitet Eisen zu Stahl'
    },
    building_bunker: {
        name: 'Bunker',
        icon: '🛡️',
        cost: { steel: 2000, concrete: 500 },
        requiredTerrain: ['mountain', 'grass', 'forest', 'player', 'Grasland', 'Wald', 'Felsgebirge'],
        produces: { defense: 50 },
        description: 'Verteidigungsanlage'
    },
    building_powerplant: {
        name: 'Kraftwerk',
        icon: '⚡',
        cost: { iron: 1500, steel: 600, fuel: 200 },
        requiredTerrain: ['player', 'grass', 'wasteland', 'Grasland', 'Ödland'],
        produces: { energy: 30 },
        description: 'Großes Energiekraftwerk'
    }
};

// Case-insensitive Normalisierung der Keys für den globalen Zugriff
const FINAL_TERRAIN_TYPES = {};
for (const [k, v] of Object.entries(TERRAIN_TYPES)) {
    FINAL_TERRAIN_TYPES[k.toLowerCase()] = v;
    FINAL_TERRAIN_TYPES[k] = v; // Auch Case-sensitive behalten
}

// Exportiere für globalen Zugriff
if (typeof window !== 'undefined') {
    window.TERRAIN_TYPES = FINAL_TERRAIN_TYPES;
    window.BUILDING_TYPES = BUILDING_TYPES;
}

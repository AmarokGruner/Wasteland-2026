// terrain-types.js - Terrain-Definitionen und Eigenschaften (Synchronisiert mit Backend)

// TERRAIN_TYPES wird nun dynamisch vom Backend (in worldmap.js) geladen.
const TERRAIN_TYPES = {};

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

// Exportiere für globalen Zugriff
if (typeof window !== 'undefined') {
    // Falls noch nicht befüllt (z.B. vor initWorldMap Aufruf)
    if (!window.TERRAIN_TYPES) window.TERRAIN_TYPES = TERRAIN_TYPES;
    window.BUILDING_TYPES = BUILDING_TYPES;
}

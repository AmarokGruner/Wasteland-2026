// terrain-types.js - Terrain-Definitionen und Eigenschaften

const TERRAIN_TYPES = {
    ocean: {
        name: 'Ozean',
        color: '#1a4d7a',
        icon: '🌊',
        playable: false,
        resources: [],
        allowedBuildings: [],
        description: 'Nicht bebaubar'
    },
    desert: {
        name: 'Wüste',
        color: '#d4a76a',
        icon: '🏜️',
        playable: true,
        resources: ['sand', 'stone'],
        allowedBuildings: ['building_mine', 'building_solar'],
        description: 'Reich an Mineralien, Solar-Energie nutzbar'
    },
    grass: {
        name: 'Grasland',
        color: '#5a8c3a',
        icon: '🌾',
        playable: true,
        resources: ['food', 'water'],
        allowedBuildings: ['building_farm', 'building_windmill', 'building_bunker'],
        description: 'Ideal für Landwirtschaft'
    },
    mountain: {
        name: 'Gebirge',
        color: '#888888',
        icon: '⛰️',
        playable: true,
        resources: ['iron', 'stone', 'coal'],
        allowedBuildings: ['building_mine', 'building_quarry', 'building_bunker'],
        description: 'Reich an Erzen und Mineralien'
    },
    forest: {
        name: 'Wald',
        color: '#2d5016',
        icon: '🌲',
        playable: true,
        resources: ['wood', 'food'],
        allowedBuildings: ['building_sawmill', 'building_hunter', 'building_bunker'],
        description: 'Holzabbau möglich'
    },
    wasteland: {
        name: 'Ödland',
        color: '#3a2a1a',
        icon: '☠️',
        playable: true,
        resources: ['scrap', 'fuel'],
        allowedBuildings: ['building_scrapyard', 'building_refinery', 'building_bunker'],
        description: 'Verbrannte Zone - Schrottplünderung möglich'
    },
    player: {
        name: 'Startposition',
        color: '#5a8c3a',
        icon: '🏠',
        playable: true,
        resources: ['iron', 'food', 'water'],
        allowedBuildings: ['building_mine', 'building_farm', 'building_factory', 'building_bunker', 'building_powerplant'],
        description: 'Deine Hauptbasis'
    }
};

// Gebäude-Definitionen (erweitert mit Terrain-Anforderungen)
const BUILDING_TYPES = {
    building_mine: {
        name: 'Mine',
        icon: '⛏️',
        cost: { iron: 500, steel: 200 },
        requiredTerrain: ['mountain', 'desert', 'player'],
        produces: { iron: 10, stone: 5 },
        description: 'Fördert Erz aus dem Boden'
    },
    building_farm: {
        name: 'Farm',
        icon: '🌾',
        cost: { iron: 300, wood: 200 },
        requiredTerrain: ['grass', 'player'],
        produces: { food: 15 },
        description: 'Produziert Nahrung auf Grasland'
    },
    building_sawmill: {
        name: 'Sägewerk',
        icon: '🪓',
        cost: { iron: 400, steel: 100 },
        requiredTerrain: ['forest'],
        produces: { wood: 20 },
        description: 'Verarbeitet Holz aus Wäldern'
    },
    building_quarry: {
        name: 'Steinbruch',
        icon: '🪨',
        cost: { iron: 600, steel: 200 },
        requiredTerrain: ['mountain'],
        produces: { stone: 15 },
        description: 'Gewinnt Stein aus Gebirge'
    },
    building_solar: {
        name: 'Solarkraftwerk',
        icon: '☀️',
        cost: { iron: 800, steel: 400 },
        requiredTerrain: ['desert'],
        produces: { energy: 25 },
        description: 'Nutzt Sonnenkraft in der Wüste'
    },
    building_windmill: {
        name: 'Windmühle',
        icon: '💨',
        cost: { iron: 500, steel: 300 },
        requiredTerrain: ['grass'],
        produces: { energy: 15 },
        description: 'Erzeugt Windenergie auf freiem Feld'
    },
    building_hunter: {
        name: 'Jägerhütte',
        icon: '🏹',
        cost: { wood: 300, iron: 100 },
        requiredTerrain: ['forest'],
        produces: { food: 10 },
        description: 'Jagt Wild im Wald'
    },
    building_scrapyard: {
        name: 'Schrottplatz',
        icon: '🔩',
        cost: { iron: 200 },
        requiredTerrain: ['wasteland'],
        produces: { scrap: 20, iron: 5 },
        description: 'Sammelt Schrott im Ödland'
    },
    building_refinery: {
        name: 'Raffinerie',
        icon: '🏗️',
        cost: { iron: 1200, steel: 500 },
        requiredTerrain: ['wasteland', 'desert', 'player'],
        produces: { fuel: 10 },
        description: 'Raffiniert Treibstoff'
    },
    building_factory: {
        name: 'Fabrik',
        icon: '🏭',
        cost: { iron: 1000, steel: 400 },
        requiredTerrain: ['grass', 'player', 'wasteland'],
        produces: { steel: 8 },
        description: 'Verarbeitet Eisen zu Stahl'
    },
    building_bunker: {
        name: 'Bunker',
        icon: '🛡️',
        cost: { steel: 2000, concrete: 500 },
        requiredTerrain: ['mountain', 'grass', 'forest', 'player'],
        produces: { defense: 50 },
        description: 'Befestigte Verteidigungsanlage'
    },
    building_powerplant: {
        name: 'Kraftwerk',
        icon: '⚡',
        cost: { iron: 1500, steel: 600, fuel: 200 },
        requiredTerrain: ['player', 'grass', 'wasteland'],
        produces: { energy: 30 },
        description: 'Großes Energiekraftwerk'
    }
};

// Exportiere für globalen Zugriff
if (typeof window !== 'undefined') {
    window.TERRAIN_TYPES = TERRAIN_TYPES;
    window.BUILDING_TYPES = BUILDING_TYPES;
}

// province.js - Provinzlogik mit Terrain-System

const BUILDING_FIELDS = 15;
const GRID_SIZE = 31;
const BUILDING_CELL_SIZE = 45;
const ROAD_CELL_SIZE = 15;
const CROSSING_CELL_SIZE = 15;

const OBJECT_TYPES = {
    CROSSING: 'crossing',
    ROAD: 'road',
    BUILDING: 'building'
};

const ROAD_LEVELS = {
    1: { name: 'Feldweg', color: '#8b7355', cost: 50 },
    2: { name: 'Kiesweg', color: '#9d8566', cost: 100 },
    3: { name: 'Pflasterweg', color: '#a89784', cost: 200 },
    4: { name: 'Betonweg', color: '#b8b8b8', cost: 400 }
};

const CROSSING_LEVELS = {
    1: { name: 'Feldwegkreuzung', color: '#7a6345', cost: 100 },
    2: { name: 'Kieskreuzung', color: '#8d7556', cost: 200 },
    3: { name: 'Pflasterkreuzung', color: '#988774', cost: 400 },
    4: { name: 'Betonkreuzung', color: '#a8a8a8', cost: 800 }
};

// Lädt und zeigt eine Provinz-Ansicht
async function loadProvince(worldX, worldY) {
    console.log(`📍 Lade Provinz (${worldX}, ${worldY})`);

    // 1. Provinz-ID auflösen (falls noch nicht geschehen)
    if (!window.currentProvinzId) {
        await window.resolveProvinzId(worldX, worldY);
    }
    const provId = window.currentProvinzId;
    if (!provId) {
        console.error("Provinz-ID konnte nicht ermittelt werden.");
        return;
    }

    // 2. Daten vom Backend laden
    let backendData = { buildings: [], vorkommen: [], lager: [] };
    try {
        const res = await fetch(`${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${provId}`);
        if (res.ok) backendData = await res.json();
    } catch (e) { console.error("Fehler beim Laden der Provinzdaten:", e); }

    const provinceTerrain = window.WORLD_MAP[worldY][worldX];
    window.currentProvinceTerrain = provinceTerrain;

    // Header aktualisieren
    const nameInput = document.getElementById('province-name-input');
    const coordsDisplay = document.getElementById('province-coords-display');
    if (nameInput) nameInput.value = backendData.name || `Provinz ${worldX},${worldY}`;
    if (coordsDisplay) coordsDisplay.textContent = `[${worldX}, ${worldY}]`;

    const container = document.getElementById('province-grid');
    container.innerHTML = '';
    container.style.display = 'grid';

    const template = buildGridTemplate();
    container.style.gridTemplateColumns = template;
    container.style.gridTemplateRows = template;
    container.style.gap = '0';

    const provinceData = generateProvinceData(worldX, worldY, provinceTerrain, backendData.buildings);

    // Rendere Grid
    for (let gridY = 0; gridY < GRID_SIZE; gridY++) {
        for (let gridX = 0; gridX < GRID_SIZE; gridX++) {
            const cell = document.createElement('div');
            cell.className = 'province-cell';
            cell.dataset.gridX = gridX;
            cell.dataset.gridY = gridY;

            const cellData = provinceData[gridY][gridX];
            const cellType = cellData.cellType;

            if (cellType === 'road') {
                const level = cellData.level || 1;
                cell.style.backgroundColor = ROAD_LEVELS[level].color;
                cell.style.fontSize = '10px';
                cell.style.color = '#3a2a1a';
                cell.textContent = 'W';
                cell.title = `${ROAD_LEVELS[level].name} (${gridX}, ${gridY})`;
            } else if (cellType === 'crossing') {
                const level = cellData.level || 1;
                cell.style.backgroundColor = CROSSING_LEVELS[level].color;
                cell.style.fontSize = '8px';
                cell.style.color = '#2a1a0a';
                cell.textContent = 'K';
                cell.title = `${CROSSING_LEVELS[level].name} (${gridX}, ${gridY})`;
            } else if (cellType === 'building') {
                const terrain = cellData.terrain;
                cell.style.backgroundColor = getTerrainColor(terrain);
                cell.title = `Gebäudefeld (${cellData.buildingX}, ${cellData.buildingY})`;

                if (cellData.placedBuilding) {
                    const b = cellData.placedBuilding;
                    const icon = document.createElement('div');
                    icon.className = 'placed-building-icon';
                    icon.textContent = b.icon || '🏢';
                    icon.style.fontSize = '28px';
                    icon.style.textShadow = '0 0 3px black';
                    cell.style.display = 'flex';
                    cell.style.alignItems = 'center';
                    cell.style.justifyContent = 'center';
                    cell.appendChild(icon);
                    if (b.level > 1) {
                        const lvlTag = document.createElement('span');
                        lvlTag.textContent = `L${b.level}`;
                        lvlTag.style.position = 'absolute';
                        lvlTag.style.bottom = '2px';
                        lvlTag.style.right = '2px';
                        lvlTag.style.fontSize = '10px';
                        lvlTag.style.background = 'rgba(0,0,0,0.7)';
                        lvlTag.style.padding = '1px 3px';
                        lvlTag.style.borderRadius = '3px';
                        cell.appendChild(lvlTag);
                    }
                }
            }

            cell.dataset.cellType = cellType;
            cell.onclick = () => selectProvinceCell(cellData, backendData);
            container.appendChild(cell);
        }
    }

    // Info-Panel aktualisieren mit Terrain-Info & Vorkommen
    updateProvinceInfo(worldX, worldY, provinceTerrain, backendData.vorkommen);
}

function updateProvinceInfo(x, y, terrainType, vorkommen = []) {
    const terrain = window.TERRAIN_TYPES ? window.TERRAIN_TYPES[terrainType] : null;

    let infoHTML = `<p><strong>Provinz:</strong> (${x}, ${y})</p>`;

    if (terrain) {
        infoHTML += `<p><strong>Terrain:</strong> ${terrain.icon} ${terrain.name}</p>`;
    }

    infoHTML += `<hr style="margin: 10px 0; border-color: var(--border);">`;
    infoHTML += `<p><strong>💎 Vorkommen:</strong></p>`;
    if (vorkommen && vorkommen.length > 0) {
        vorkommen.forEach(v => {
            infoHTML += `<p style="font-size: 11px;">• ${v.name}: ${v.menge.toLocaleString()} (${v.qualitaet}%)</p>`;
        });
    } else {
        infoHTML += `<p style="font-size: 11px; color: var(--text-muted);">Keine Vorkommen bekannt.</p>`;
    }

    infoHTML += `<hr style="margin: 10px 0; border-color: var(--border);">`;
    infoHTML += `<p style="font-size: 11px;">Klicke auf ein Feld für Details.</p>`;

    document.getElementById('selected-info').innerHTML = infoHTML;
}

function buildGridTemplate() {
    const parts = [];
    for (let i = 0; i < GRID_SIZE; i++) {
        if (i % 2 === 0) {
            parts.push(`${ROAD_CELL_SIZE}px`);
        } else {
            parts.push(`${BUILDING_CELL_SIZE}px`);
        }
    }
    return parts.join(' ');
}

function generateProvinceData(worldX, worldY, provinceTerrain, backendBuildings = []) {
    const data = [];

    // Pre-Map for buildings
    const bMap = {};
    backendBuildings.forEach(b => {
        bMap[`${b.building_x},${b.building_y}`] = b;
    });

    for (let gridY = 0; gridY < GRID_SIZE; gridY++) {
        const row = [];
        for (let gridX = 0; gridX < GRID_SIZE; gridX++) {
            let cellData = {};

            if (gridX % 2 === 0 && gridY % 2 === 0) {
                cellData = { cellType: 'crossing', gridX, gridY, level: 1 };
            } else if (gridX % 2 === 0 || gridY % 2 === 0) {
                cellData = { cellType: 'road', gridX, gridY, level: 1 };
            } else {
                const bX = Math.floor(gridX / 2);
                const bY = Math.floor(gridY / 2);
                const placed = bMap[`${bX},${bY}`];

                let buildingInfo = null;
                if (placed) {
                    // Suche Icon in BuildingsAPI Fallback oder Cache
                    const typeInfo = BUILDINGS_FALLBACK.find(t => t.name === placed.building_type);
                    buildingInfo = {
                        name: placed.building_type,
                        icon: typeInfo ? typeInfo.symbol_emoji : '🏢',
                        level: placed.level || 1
                    };
                }

                cellData = {
                    cellType: 'building', gridX, gridY,
                    buildingX: bX, buildingY: bY,
                    terrain: provinceTerrain,
                    placedBuilding: buildingInfo
                };
            }
            row.push(cellData);
        }
        data.push(row);
    }
    return data;
}

async function selectProvinceCell(cellData, backendData) {
    let infoHTML = `<p><strong>Position:</strong> (${cellData.gridX}, ${cellData.gridY})</p>`;
    const cellType = cellData.cellType;

    if (cellType === 'building') {
        const bX = cellData.buildingX;
        const bY = cellData.buildingY;
        infoHTML += `<p><strong>Typ:</strong> Gebäudefeld</p>`;
        infoHTML += `<p><strong>Position:</strong> (${bX}, ${bY})</p>`;

        if (cellData.placedBuilding) {
            const b = cellData.placedBuilding;
            infoHTML += `<hr style="margin: 10px 0; border-color: var(--border);">`;
            infoHTML += `<p style="font-size: 20px;">${b.icon} <strong>${b.name}</strong></p>`;
            infoHTML += `<p>Stufe: ${b.level}</p>`;

            // Upgrade Button
            infoHTML += `<button class="btn-action" onclick="upgradeBuilding(${bX}, ${bY})">⬆️ Ausbauen (100 Eisen)</button>`;
            infoHTML += `<button class="btn-action danger" onclick="removeBuilding(${bX}, ${bY})">🗑️ Abreißen</button>`;
        } else {
            infoHTML += `<p style="color: var(--accent-success);">✅ Bebaubar!</p>`;
            infoHTML += `<hr style="margin: 10px 0; border-color: var(--border);">`;
            infoHTML += `<p><strong>Gebäude errichten:</strong></p>`;

            // Nutze Fallback-Liste für Bau-Optionen
            BUILDINGS_FALLBACK.filter(t => t.baubar).forEach(t => {
                infoHTML += `
                    <div class="build-option" onclick="placeBuilding('${t.name}', ${bX}, ${bY})">
                        <span>${t.symbol_emoji} ${t.name}</span>
                        <span style="font-size: 10px; color: var(--text-muted)">Bauen</span>
                    </div>`;
            });
        }
    } else {
        infoHTML += `<p>Keine Aktionen für ${cellType} verfügbar.</p>`;
    }

    document.getElementById('selected-info').innerHTML = infoHTML;
}

async function placeBuilding(type, x, y) {
    if (!confirm(`${type} auf (${x},${y}) errichten?`)) return;
    try {
        const res = await fetch(`${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}/build`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ building_type: type, x: x, y: y })
        });
        if (res.ok) {
            loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
            window.loadResources();
        } else {
            const err = await res.json();
            alert("Fehler beim Bau: " + (err.detail || "Unbekannt"));
        }
    } catch (e) { alert("Serverfehler beim Bau"); }
}

async function upgradeBuilding(x, y) {
    try {
        const res = await fetch(`${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}/upgrade`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ building_x: x, building_y: y })
        });
        if (res.ok) {
            loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
            window.loadResources();
        } else {
            const err = await res.json();
            alert("Fehler beim Ausbau: " + (err.detail || "Unbekannt"));
        }
    } catch (e) { alert("Serverfehler beim Ausbau"); }
}

function getTerrainColor(terrain) {
    if (window.TERRAIN_TYPES && window.TERRAIN_TYPES[terrain]) {
        return window.TERRAIN_TYPES[terrain].color;
    }
    return '#5a8c3a';
}

function backToWorld() {
    if (typeof window.switchView === 'function') {
        window.switchView('world');
    }
}

// Exportiere Funktionen
if (typeof window !== 'undefined') {
    window.loadProvince = loadProvince;
    window.backToWorld = backToWorld;
}

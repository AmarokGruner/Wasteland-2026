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

let currentQuickSession = null;
let provinceBackendData = null; // Global cache for current province buildings

// ── Provinz Tab-Navigation ───────────────────────────────────
const PROVINCE_TABS = ['karte','lager','produktion','transport','militaer','vorschau'];

function showProvinceTab(tab) {
  PROVINCE_TABS.forEach(t => {
    const content = document.getElementById(`ptab-content-${t}`);
    const btn = document.getElementById(`ptab-btn-${t}`);
    if (content) content.style.display = 'none';
    if (btn) btn.classList.remove('active');
  });
  
  const targetContent = document.getElementById(`ptab-content-${tab}`);
  const targetBtn = document.getElementById(`ptab-btn-${tab}`);
  if (targetContent) targetContent.style.display = 'block';
  if (targetBtn) targetBtn.classList.add('active');
  
  localStorage.setItem('last_province_tab', tab);

  // Resolve and store active province ID
  if (window.selectedProvinceCoords) {
    const resolvePromise = window.resolveProvinzId?.(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
    if (resolvePromise && typeof resolvePromise.then === 'function') {
      resolvePromise.then(id => {
        window.currentProvinzId = id;
      });
    } else {
      window.currentProvinzId = window.resolveProvinzId?.(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y) || null;
    }
  }

  // Tab-spezifische Loader
  
  // Tab-spezifische Loader
  if (tab === 'lager') loadLager();
  if (tab === 'produktion') loadProductionOverview(); // Shared with global production view
  if (tab === 'transport') loadTransport();
  if (tab === 'militaer') loadMilitary();
  if (tab === 'vorschau') loadProvincePreview();
}

// Kompatibilität für alte Aufrufe
function showProvinceSubView(sub) {
    const map = { 'map': 'karte', 'vorschau': 'vorschau', 'lager': 'lager', 'militaer': 'militaer', 'transport': 'transport' };
    showProvinceTab(map[sub] || 'karte');
}

window.showProvinceTab = showProvinceTab;
window.showProvinceSubView = showProvinceSubView;

// ── Sidebar-Komponenten Rendering (NEU) ──────────────────────
function renderSidebarComponent(type, data) {
  const panel = document.getElementById('selected-info');
  if (!panel) return;
  panel.innerHTML = ''; // clear

  if (type === 'empty_building') {
    panel.appendChild(createBuildMenu(data));
  } else if (type === 'placed_building') {
    panel.appendChild(createBuildingDetail(data));
  } else if (type === 'road' || type === 'crossing') {
    panel.appendChild(createRoadMenu(data));
  } else {
    panel.innerHTML = '<p>Wähle ein Feld aus, um Details zu sehen.</p>';
  }
}

function createBuildMenu({ bX, bY, terrain }) {
  const container = document.createElement('div');
  container.className = 'build-menu';
  container.innerHTML = `
    <h4>🏗️ Bauen auf (${bX}, ${bY})</h4>
    <p style="font-size: 11px; color: var(--text-muted)">Terrain: <strong>${terrain}</strong></p>
    <div class="building-grid" id="available-buildings-grid">
      <p>Lade Gebäude...</p>
    </div>
  `;
  
  loadAvailableBuildings(bX, bY, terrain);
  return container;
}

async function loadAvailableBuildings(bX, bY, terrain) {
  const grid = document.getElementById('available-buildings-grid');
  if (!grid) return;
  
  try {
    const res = await gameFetch(`${window.APIBASE}/player/${window.currentPlayerId}/buildings/available?terrain=${terrain}&province_id=${window.currentProvinzId}`);
    if (res.ok) {
      const buildings = await res.json();
      grid.innerHTML = '';
      
      buildings.forEach(b => {
        const card = document.createElement('div');
        card.className = `building-card ${!b.baubar ? 'disabled' : ''}`;
        
        const effClass = b.terrain_effektivitaet >= 100 ? 'eff-100' : (b.terrain_effektivitaet >= 75 ? 'eff-75' : 'eff-50');
        
        card.innerHTML = `
          <div style="font-size: 20px">${b.icon || '🏠'}</div>
          <div style="font-size: 11px; font-weight: bold; margin-top: 4px">${b.name}</div>
          <div class="eff-badge ${effClass}">${b.terrain_effektivitaet}%</div>
          <div style="font-size: 10px; color: #aaa; margin-top: 4px">💰 ${b.baukosten}</div>
        `;
        
        if (b.baubar) {
          card.onclick = () => confirmBuild(b, bX, bY);
        } else {
          card.title = b.grund || "Nicht verfügbar";
        }
        grid.appendChild(card);
      });
    }
  } catch (e) {
    grid.innerHTML = '<p>Fehler beim Laden.</p>';
  }
}

function confirmBuild(building, bX, bY) {
    const panel = document.getElementById('selected-info');
    const originalContent = panel.innerHTML;
    
    panel.innerHTML = `
        <div style="background: rgba(0,0,0,0.3); padding: 15px; border-radius: 8px; border: 1px solid var(--accent-success)">
            <h4>${building.icon} ${building.name} bauen?</h4>
            <p>Kosten: 💰 ${building.baukosten}</p>
            <div style="display: flex; gap: 10px; margin-top: 15px">
                <button class="btn-action success" onclick="executeBuild(${building.id}, ${bX}, ${bY})">✅ Ja, bauen</button>
                <button class="btn-action" id="cancel-build">❌ Abbrechen</button>
            </div>
        </div>
    `;
    
    document.getElementById('cancel-build').onclick = () => {
        panel.innerHTML = originalContent;
        // Re-attach event listeners if needed, or just re-render
        renderSidebarComponent('empty_building', { bX, bY, terrain: window.currentProvinceTerrain });
    };
}

async function executeBuild(buildingId, bX, bY) {
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/build`, {
            method: 'POST',
            body: JSON.stringify({ building_id: buildingId, bX, bY })
        });
        
        if (res.ok) {
            window.showToast("Gebäude erfolgreich in Auftrag gegeben!", "success");
            loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
            renderSidebarComponent('none');
        } else {
            const err = await res.json();
            window.showToast(err.detail || "Bau fehlgeschlagen", "error");
        }
    } catch (e) {
        window.showToast("Verbindungsfehler", "error");
    }
}

function createBuildingDetail({ building, bX, bY }) {
  const container = document.createElement('div');
  container.className = 'building-detail';
  container.innerHTML = `
    <h4>${building.icon || '🏠'} ${building.name}</h4>
    <p>Position: (${bX}, ${bY}) | Level: ${building.level || 1}</p>
    <hr style="border: 0; border-top: 1px solid #444; margin: 10px 0">
    <div style="display: flex; flex-direction: column; gap: 8px">
        <button class="btn-action" onclick="upgradeBuilding(${building.instance_id})">⬆️ Aufstufen</button>
        <button class="btn-action danger" onclick="confirmDemolish(${building.instance_id})">🗑️ Abreißen</button>
    </div>
  `;
  return container;
}

function confirmDemolish(instanceId) {
    const panel = document.getElementById('selected-info');
    panel.innerHTML = `
        <div style="background: rgba(155,44,44,0.2); padding: 15px; border-radius: 8px; border: 1px solid var(--accent-danger)">
            <h4>Wirklich abreißen?</h4>
            <p>Das Gebäude geht unwiderruflich verloren.</p>
            <div style="display: flex; gap: 10px; margin-top: 15px">
                <button class="btn-action danger" onclick="executeDemolish(${instanceId})">✅ Ja, abreißen</button>
                <button class="btn-action" onclick="renderSidebarComponent('none')">❌ Nein</button>
            </div>
        </div>
    `;
}

async function executeDemolish(instanceId) {
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/demolish/${instanceId}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            window.showToast("Gebäude abgerissen.", "info");
            loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
            renderSidebarComponent('none');
        }
    } catch (e) { window.showToast("Fehler beim Abriss", "error"); }
}

function createRoadMenu(data) {
    const container = document.createElement('div');
    container.innerHTML = `<h4>🛣️ Weg (${data.gridX}, ${data.gridY})</h4><p>Details folgen...</p>`;
    return container;
}

// ── Minimap Logik ───────────────────────────────────────────
function renderMinimap() {
    let canvas = document.getElementById('minimap-canvas');
    if (!canvas) {
        const container = document.getElementById('province-map-container');
        if (!container) return;
        canvas = document.createElement('canvas');
        canvas.id = 'minimap-canvas';
        canvas.width = 100;
        canvas.height = 100;
        canvas.style.position = 'absolute';
        canvas.style.bottom = '10px';
        canvas.style.right = '10px';
        canvas.style.border = '1px solid #666';
        canvas.style.background = '#000';
        canvas.style.borderRadius = '4px';
        canvas.style.boxShadow = '0 0 10px rgba(0,0,0,0.5)';
        container.style.position = 'relative';
        container.appendChild(canvas);
    }
    
    const ctx = canvas.getContext('2d');
    const { x, y } = window.selectedProvinceCoords;
    
    // Draw grid points (50x50 world)
    // Scale: 2px per cell
    ctx.clearRect(0,0,100,100);
    ctx.fillStyle = '#111';
    ctx.fillRect(0,0,100,100);
    
    // Blinking dot for current position
    const blink = (Date.now() % 1000) < 500;
    if (blink) {
        ctx.fillStyle = '#ff4444';
        ctx.beginPath();
        ctx.arc(x * 2 + 1, y * 2 + 1, 2, 0, Math.PI * 2);
        ctx.fill();
    }
    
    requestAnimationFrame(renderMinimap);
}

// ── Bestehende Funktionen anpassen ──────────────────────────
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
        const res = await gameFetch(`${window.APIBASE}/province/${provId}`);
        if (res.ok) {
            backendData = await res.json();
            provinceBackendData = backendData;
        }
    } catch (e) { console.error("Fehler beim Laden der Provinzdaten:", e); }

    await checkQuickSession();

    const provinceTerrain = window.WORLD_MAP[worldY][worldX];
    window.currentProvinceTerrain = provinceTerrain;

    // Header aktualisieren
    const nameInput = document.getElementById('province-name-input');
    const coordsDisplay = document.getElementById('province-coords-display');
    if (nameInput) nameInput.value = backendData.name || `Provinz ${worldX},${worldY}`;
    if (coordsDisplay) coordsDisplay.textContent = `[${worldX}, ${worldY}]`;

    // Start Minimap
    renderMinimap();
    
    // Start City Grid (15x15)
    loadProvinceCityGrid(provId);

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
                
                // GIF-Hintergrund setzen falls vorhanden
                const terrainConfig = window.TERRAINS?.find(t => t.name === terrain);
                if (terrainConfig && terrainConfig.gif_filename) {
                    cell.style.backgroundImage = `url('terrains/${terrainConfig.gif_filename}')`;
                    cell.style.backgroundSize = 'cover';
                }

                if (cellData.placedBuilding) {
                    cell.title = `${cellData.placedBuilding.name} (${cellData.buildingX}, ${cellData.buildingY})`;
                } else {
                    cell.title = `Gebäudefeld (${cellData.buildingX}, ${cellData.buildingY})`;
                }

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
    const cellType = cellData.cellType;

    if (cellType === 'building') {
        const bX = cellData.buildingX;
        const bY = cellData.buildingY;

        if (cellData.placedBuilding) {
            // Finde Instanz-Details aus dem Backend-Cache
            const instance = provinceBackendData?.buildings?.find(b => b.building_x === bX && b.building_y === bY);
            renderSidebarComponent('placed_building', { 
                building: { ...cellData.placedBuilding, instance_id: instance?.id }, 
                bX, bY 
            });
        } else {
            renderSidebarComponent('empty_building', { bX, bY, terrain: cellData.terrain });
        }
    } else if (cellType === 'road' || cellType === 'crossing') {
        renderSidebarComponent(cellType, { gridX: cellData.gridX, gridY: cellData.gridY });
    } else {
        renderSidebarComponent('none');
    }
}

async function placeBuilding(type, x, y) {
    const isQuick = currentQuickSession && currentQuickSession.mode === 'build' && currentQuickSession.template_name === type;
    if (!isQuick && !confirm(`${type} on (${x},${y}) errichten?`)) return;
    
    try {
        const template = BUILDINGS_FALLBACK.find(t => t.name === type);
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/build${isQuick ? '?session=true' : ''}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template_id: template.id, position: x }) // Backend expects position mapped to x
        });
        if (res.ok) {
            const result = await res.json();
            if (isQuick) {
                // Update local status instead of full reload
                updateAPCounter(result.ap_remaining);
                // Simple feedback or mini-reload? For now, reload province to catch all changes
                loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
            } else {
                loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
                window.loadResources();
            }
        } else {
            const err = await res.json();
            alert("Fehler beim Bau: " + (err.detail || "Unbekannt"));
        }
    } catch (e) { alert("Serverfehler beim Bau"); }
}

async function removeBuilding(x, y) {
    const isQuick = currentQuickSession && currentQuickSession.mode === 'demolish';
    if (!isQuick && !confirm(`Gebäude auf (${x},${y}) wirklich abreißen?`)) return;

    try {
        // Find instance ID from backend data
        const instance = provinceBackendData.buildings.find(b => b.building_x === x && b.building_y === y);
        if (!instance) {
            alert("Fehler: Gebäude-Instanz nicht gefunden.");
            return;
        }

        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/demolish/${instance.id}${isQuick ? '?session=true' : ''}`, {
            method: 'POST'
        });
        
        if (res.ok) {
            const result = await res.json();
            if (isQuick) {
                updateAPCounter(result.ap_remaining);
                loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
            } else {
                loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
                window.loadResources();
            }
        } else {
            const err = await res.json();
            alert("Fehler beim Abriss: " + (err.detail || "Unbekannt"));
        }
    } catch (e) { alert("Serverfehler beim Abriss"); }
}

async function placeRoad(type, x, y) {
    if (!confirm(`${type} auf (${x},${y}) bauen?`)) return;
    try {
        const res = await gameFetch(`${window.APIBASE}/player/${window.currentPlayerId}/roads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ road_type: type, x: x, y: y })
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
        const res = await gameFetch(`${window.APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}/upgrade`, {
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

async function checkQuickSession() {
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/quickbuild/session`);
        if (res.ok) {
            const data = await res.json();
            if (data.active) {
                currentQuickSession = data;
                showQuickOverlay(data);
            } else {
                currentQuickSession = null;
                hideQuickOverlay();
            }
        }
    } catch (e) { console.error("Session Check Failed", e); }
}

async function activateQuickMode(mode, templateName = null) {
    let templateId = null;
    if (templateName) {
        const t = BUILDINGS_FALLBACK.find(b => b.name === templateName);
        if (t) templateId = t.id;
    }

    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/quickbuild/activate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode, template_id: templateId })
        });
        if (res.ok) {
            await checkQuickSession();
        }
    } catch (e) { alert("Fehler beim Aktivieren"); }
}

async function deactivateQuickMode() {
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/quickbuild/deactivate`, {
            method: 'POST'
        });
        if (res.ok) {
            currentQuickSession = null;
            hideQuickOverlay();
        }
    } catch (e) { alert("Fehler beim Deaktivieren"); }
}

function showQuickOverlay(session) {
    const overlay = document.getElementById('quickbuild-overlay');
    const modeText = document.getElementById('qb-mode-text');
    const apText = document.getElementById('qb-ap-text');
    
    if (overlay && modeText) {
        overlay.style.display = 'flex';
        const label = session.mode === 'build' ? `Schnellbau: ${session.template_name}` : 'Schnellabriss-Modus';
        modeText.textContent = label;
        // AP will be updated via backend soon, for now placeholder
        apText.textContent = `Mind. ${session.ap_cost_per_build} AP pro Aktion`;
    }
}

function hideQuickOverlay() {
    const overlay = document.getElementById('quickbuild-overlay');
    if (overlay) overlay.style.display = 'none';
}

function updateAPCounter(apRemaining) {
    const apText = document.getElementById('qb-ap-text');
    if (apText && apRemaining !== undefined) {
        apText.textContent = `Verbleibende AP: ${apRemaining}`;
    }
}

function backToWorld() {
    if (typeof window.switchView === 'function') {
        window.switchView('world');
    }
}

async function loadMilitaryStatus() {
    if (!window.currentProvinzId) return;
    const statusEl = document.getElementById('mil-count');
    const fitnessEl = document.getElementById('mil-fitness');
    const securityEl = document.getElementById('mil-security-bonus');
    
    if (!statusEl) return;
    
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/military/status`);
        if (res.ok) {
            const data = await res.json();
            statusEl.textContent = data.soldier_count;
            fitnessEl.textContent = Math.round(data.fitness * 100);
            securityEl.textContent = Math.round(data.security_bonus * 100);
        }
    } catch (e) { console.warn("Fehler beim Laden des Militär-Status:", e); }
}

async function trainUnits() {
    const amount = parseInt(document.getElementById('mil-train-amount').value);
    if (!amount || amount < 1) return;
    
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/military/train`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ Ausbildung von ${amount} Einheiten gestartet!`);
            loadMilitaryStatus();
            window.loadResources();
        } else {
            alert("❌ Fehler: " + (data.detail || JSON.stringify(data)));
        }
    } catch (e) { alert("Serverfehler beim Training: " + e.message); }
}

async function dismissUnits() {
    const amount = parseInt(document.getElementById('mil-dismiss-amount').value);
    if (!amount || amount < 1) return;
    
    if (!confirm(`${amount} Einheiten wirklich entlassen?`)) return;
    
    try {
        const res = await gameFetch(`${window.APIBASE}/province/${window.currentProvinzId}/military/dismiss`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: amount })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`✅ ${amount} Einheiten entlassen.`);
            loadMilitaryStatus();
        } else {
            alert("❌ Fehler: " + (data.detail || JSON.stringify(data)));
        }
    } catch (e) { alert("Serverfehler beim Entlassen: " + e.message); }
}

// Exportiere Funktionen
if (typeof window !== 'undefined') {
    window.loadProvince = loadProvince;
    window.backToWorld = backToWorld;
    window.loadMilitaryStatus = loadMilitaryStatus;
    window.trainUnits = trainUnits;
    window.dismissUnits = dismissUnits;
}

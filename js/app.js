// ============================================================
// Hauptlogik – Verbrannte Zone
// ============================================================

const APIBASE = window.location.protocol === 'https:' 
  ? `https://${window.location.host}` 
  : 'http://localhost:8000';
window.APIBASE = APIBASE;

// Auth check on load
const savedToken = localStorage.getItem('token');
const savedPlayerId = localStorage.getItem('player_id');
const savedUsername = localStorage.getItem('username');
const savedRole = localStorage.getItem('role');

if (!savedToken || !savedPlayerId) {
  // Redirect to login if not authenticated
  window.location.href = 'login.html';
}

window.currentPlayerId = savedPlayerId ? parseInt(savedPlayerId) : 1;
window.currentView = 'world';
window.selectedProvinceCoords = null;
window.currentProvinzId = null;
window.resourceMap = {}; // Cache für Ressourcen-Namen [ID] -> Name

// ── Initialisierung ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  console.log('Verbrannte Zone lädt...');
  
  // Display user info
  const userDisplay = document.getElementById('user-display');
  if (userDisplay && savedUsername) {
    userDisplay.textContent = `👤 ${savedUsername}`;
  }
  
  loadResources();
  initWorldMap();
  loadResourceMap(); // Ressourcen-Namen laden
  switchView('world');
});

// Logout function
function logout() {
  const token = localStorage.getItem('token');
  fetch(`${APIBASE}/auth/logout`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token })
  }).finally(() => {
    localStorage.clear();
    window.location.href = 'login.html';
  });
}

// ── Spieler-Ressourcen laden ─────────────────────────────────
async function loadResources() {
  try {
    const response = await fetch(`${APIBASE}/player/${window.currentPlayerId}/resources/total`);
    if (response.ok) {
      const data = await response.json();
      document.getElementById('iron-count').textContent = (data.iron || 0).toLocaleString('de-DE');
      document.getElementById('steel-count').textContent = (data.steel || 0).toLocaleString('de-DE');
      document.getElementById('fuel-count').textContent = (data.fuel || 0).toLocaleString('de-DE');
    }
  } catch (error) {
    console.error('Fehler beim Laden der Ressourcen', error);
  }
}

// ── Zwischen Weltkarte und Provinzansicht wechseln ───────────
function switchView(viewId, x = null, y = null) {
  window.currentView = viewId;

  // Alle Hauptansichten ausblenden
  document.getElementById('worldmap-view').style.display = 'none';
  document.getElementById('province-view').style.display = 'none';
  document.getElementById('production-view').style.display = 'none';

  // Alle Sidebar-Inhalte ausblenden
  document.getElementById('sidebar-world-content').style.display = 'none';
  document.getElementById('sidebar-province-content').style.display = 'none';

  if (viewId === 'world') {
    document.getElementById('worldmap-view').style.display = 'flex'; // Changed from block to flex to match original
    document.getElementById('sidebar-world-content').style.display = 'block';
    if (typeof window.loadWorldMap === 'function') loadWorldMap(); // Assuming loadWorldMap exists
    window.selectedProvinceCoords = null;
    window.currentProvinzId = null;
    document.getElementById('selected-info').innerHTML =
      '<p>Wähle eine Provinz aus, um sie zu verwalten.</p>';
  } else if (viewId === 'province') {
    document.getElementById('province-view').style.display = 'flex'; // Changed from block to flex to match original
    document.getElementById('sidebar-province-content').style.display = 'block';
    if (x !== null && y !== null) {
      window.selectedProvinceCoords = { x, y };
      window.currentProvinzId = null;
      if (typeof window.loadProvince === 'function') window.loadProvince(x, y);
      showProvinceSubView('map');
      resolveProvinzId(x, y);
    }
  } else if (viewId === 'production') {
    document.getElementById('production-view').style.display = 'block';
    document.getElementById('sidebar-world-content').style.display = 'block'; // Production view uses world sidebar
    loadProductionOverview();
  }

  // Zeitguthaben immer aktualisieren wenn in einer Ansicht
  updateCreditDisplay();
}

// ── Provinz-ID aus Backend holen und cachen ──────────────────
// Backend: GET /player/{id}/provinzen
// Response: { player_id, provinzen: [{id, world_x, world_y, name, ...}], anzahl }
async function resolveProvinzId(x, y) {
  try {
    const url = `${APIBASE}/player/${window.currentPlayerId}/provinzen`;
    const res = await fetch(url);
    if (!res.ok) { console.warn(`resolveProvinzId: HTTP ${res.status}`); return; }
    const data = await res.json();
    // ⚠️ Response ist { provinzen: [...] }, NICHT direkt ein Array
    const prov = data.provinzen.find(p => p.world_x === x && p.world_y === y);
    if (prov) {
      window.currentProvinzId = prov.id;
      console.log(`Provinz-ID gecacht: ${prov.id} für (${x},${y})`);
    } else {
      console.warn(`Keine Provinz für (${x},${y}) im Backend. Beansprucht?`);
      const infoPanel = document.getElementById('selected-info');
      const terrainKey = window.WORLD_MAP[y][x];
      const terrain = (window.TERRAIN_TYPES && window.TERRAIN_TYPES[terrainKey]) ? window.TERRAIN_TYPES[terrainKey].name : terrainKey;

      infoPanel.innerHTML = `
        <p><strong>Position:</strong> (${x}, ${y})</p>
        <p><strong>Gelände:</strong> ${terrain}</p>
        <p style="color:var(--text-muted); margin-bottom: 15px;">Diese Provinz gehört dir noch nicht.</p>
        <button class="btn-action" onclick="claimProvince(${x}, ${y}, '${terrain}')">🚩 Diese Provinz besetzen</button>
      `;
    }
  } catch (e) {
    console.warn('resolveProvinzId fehlgeschlagen:', e.message);
  }
}

async function claimProvince(x, y, terrain) {
  try {
    const url = `${APIBASE}/player/${window.currentPlayerId}/provinzen`;
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ world_x: x, world_y: y, name: `Provinz ${x},${y}`, terrain: terrain })
    });
    const data = await res.json();
    if (res.ok) {
      alert("✅ Provinz erfolgreich besetzt!");
      window.currentProvinzId = data.provinz.id;
      switchView('province', x, y);
    } else {
      alert("❌ Fehler: " + (data.detail || JSON.stringify(data)));
    }
  } catch (e) {
    console.error("Besetzen fehlgeschlagen:", e);
    alert("Besetzen fehlgeschlagen: " + e.message);
  }
}

// ── Sub-View Provinz umschalten ──────────────────────────────
function showProvinceSubView(sub) {
  const mapContainer = document.getElementById('province-map-container');
  const lagerContainer = document.getElementById('province-lager-container');
  const transportContainer = document.getElementById('province-transport-container');
  const btnMap = document.getElementById('menu-btn-map');
  const btnLager = document.getElementById('menu-btn-lager');
  const btnTransport = document.getElementById('menu-btn-transport');

  if (sub === 'map') {
    mapContainer.style.display = 'block';
    lagerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'none';
    btnMap.classList.add('active');
    btnLager.classList.remove('active');
    if (btnTransport) btnTransport.classList.remove('active');
  } else if (sub === 'lager') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'block';
    if (transportContainer) transportContainer.style.display = 'none';
    btnMap.classList.remove('active');
    btnLager.classList.add('active');
    if (btnTransport) btnTransport.classList.remove('active');
    loadProvinceLager();
  } else if (sub === 'transport') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'block';
    btnMap.classList.remove('active');
    btnLager.classList.remove('active');
    if (btnTransport) btnTransport.classList.add('active');
    if (typeof window.loadTransportView === 'function') loadTransportView();
  } else if (sub === 'vorschau') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'none';
    const vContainer = document.getElementById('province-vorschau-container');
    if (vContainer) vContainer.style.display = 'block';

    // Buttons in der Sidebar
    btnMap.classList.remove('active');
    btnLager.classList.remove('active');
    if (btnTransport) btnTransport.classList.remove('active');
    const btnVorschau = document.getElementById('menu-btn-vorschau');
    if (btnVorschau) btnVorschau.classList.add('active');
  }
}

// ── Lagerbestand laden ───────────────────────────────────────
// Backend-Responses:
//   /provinzen       → { player_id, provinzen: [...], anzahl }
//   /provinzen/{id}/lager → { provinz_id, eintraege: [{ressource_name, typ, menge, ...}], anzahl_positionen, gesamtwert }
async function loadProvinceLager() {
  const lagerContent = document.getElementById('lager-content');
  const coords = window.selectedProvinceCoords;

  if (!coords) {
    lagerContent.innerHTML = '<p style="color:var(--text-muted)">Keine Provinz ausgewählt.</p>';
    return;
  }

  lagerContent.innerHTML = '<p style="color:var(--text-muted)">Lade Lager...</p>';

  try {
    // Provinz-ID: gecacht oder nachladen
    let provinzId = window.currentProvinzId;

    if (!provinzId) {
      const listUrl = `${APIBASE}/player/${window.currentPlayerId}/provinzen`;
      const listRes = await fetch(listUrl);
      if (!listRes.ok) throw new Error(`GET ${listUrl} → HTTP ${listRes.status}`);
      const listData = await listRes.json();
      // Response: { player_id, provinzen: [...], anzahl }  ← Array ist unter .provinzen
      const prov = listData.provinzen.find(p => p.world_x === coords.x && p.world_y === coords.y);
      if (!prov) throw new Error(
        `Provinz (${coords.x},${coords.y}) nicht im Backend. ` +
        `POST /player/1/provinzen ausgeführt?`
      );
      provinzId = prov.id;
      window.currentProvinzId = provinzId;
    }

    // Lagereinträge laden
    const lagerUrl = `${APIBASE}/player/${window.currentPlayerId}/provinzen/${provinzId}/lager`;
    const lagerRes = await fetch(lagerUrl);
    if (!lagerRes.ok) throw new Error(`GET ${lagerUrl} → HTTP ${lagerRes.status}`);
    const lagerData = await lagerRes.json();
    // Response: { provinz_id, eintraege: [...], anzahl_positionen, gesamtwert }
    // Backend filtert bereits WHERE menge > 0, kein eigener Filter nötig
    const eintraege = lagerData.eintraege;

    // Kapazitätsbalken
    const totalMenge = eintraege.reduce((sum, i) => sum + i.menge, 0);
    const kapazitaet = lagerData.kapazitaet || 1000;
    const prozent = Math.min(100, Math.round((totalMenge / kapazitaet) * 100));
    const barColor = prozent > 80 ? '#ff4444' : prozent > 50 ? '#ffaa00' : '#48bb78';

    let html = `
      <div class="lager-header"><h2>🏪 Provinzlager</h2></div>
      <div class="lager-kapazitaet">
        <div class="lager-bar-label">
          <span>Kapazität</span>
          <span>${totalMenge.toLocaleString('de-DE')} / ${kapazitaet.toLocaleString('de-DE')}</span>
        </div>
        <div class="lager-bar-bg">
          <div class="lager-bar-fill" style="width:${prozent}%; background:${barColor}"></div>
        </div>
      </div>`;

    if (eintraege.length === 0) {
      html += '<p style="color:var(--text-muted); margin-top:12px">Lager ist leer.</p>';
    } else {
      html += `
        <table class="lager-tabelle">
          <thead><tr><th>Ressource</th><th style="text-align:right">Menge</th></tr></thead>
          <tbody>
            ${eintraege.map(item => `
              <tr>
                <td>
                  ${item.ressource_name}
                  ${item.typ ? `<span class="lager-typ">${item.typ}</span>` : ''}
                </td>
                <td class="lager-menge">${item.menge.toLocaleString('de-DE')}</td>
              </tr>`).join('')}
          </tbody>
        </table>`;
    }

    lagerContent.innerHTML = html;

  } catch (error) {
    console.error('Fehler Lager:', error);
    lagerContent.innerHTML = `
      <div style="color:var(--accent-danger); font-size:0.9rem; line-height:1.8">
        <strong>⚠️ Lager konnte nicht geladen werden</strong><br>
        ${error.message}
      </div>`;
  }
}

async function nextTurn() {
  console.log('⏳ Nächste Runde wird berechnet...');
  try {
    const response = await fetch(`${APIBASE}/player/${window.currentPlayerId}/resources/produce`, { method: 'POST' });
    const data = await response.json();

    if (response.ok) {
      alert(`Runde beendet!\n\n${data.message}`);
      loadResources();
      if (window.currentView === 'production') loadProductionOverview();
      if (window.currentView === 'province') {
        if (typeof window.loadProvince === 'function') window.loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
        loadProvinceLager();
      }
    } else {
      alert('Fehler: ' + data.detail);
    }
  } catch (error) {
    console.error('Fehler beim Rundenwechsel', error);
  }
}

async function loadProductionOverview() {
  const content = document.getElementById('production-content');
  if (!content) return;
  content.innerHTML = '<p style="color: var(--text-muted)">Lade Produktionsdaten...</p>';

  try {
    const res = await fetch(`${APIBASE}/player/${window.currentPlayerId}/production/stats`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    if (!data.stats || data.stats.length === 0) {
      content.innerHTML = '<p>Keine Provinzen mit Produktion gefunden.</p>';
      return;
    }

    let html = `
      <table class="lager-tabelle">
        <thead>
          <tr>
            <th>Provinz</th>
            <th>Produktion</th>
            <th>Verbrauch</th>
          </tr>
        </thead>
        <tbody>
    `;

    data.stats.forEach(p => {
      let prodItems = [];
      for (const [res, menge] of Object.entries(p.production)) {
        prodItems.push(`<span style="color:var(--accent-success)">+${menge} ${res}</span>`);
      }

      let consItems = [];
      for (const [res, menge] of Object.entries(p.consumption)) {
        consItems.push(`<span style="color:var(--accent-danger)">-${menge} ${res}</span>`);
      }

      html += `
        <tr>
          <td><strong>${p.name}</strong></td>
          <td>${prodItems.join(', ') || '–'}</td>
          <td>${consItems.join(', ') || '–'}</td>
        </tr>
      `;
    });

    html += '</tbody></table>';
    content.innerHTML = html;

  } catch (e) {
    content.innerHTML = `<p style="color: var(--accent-danger)">Fehler: ${e.message}</p>`;
  }
}

// ── Zeit-System & Vorschau ───────────────────────────────────

async function updateCreditDisplay() {
  const display = document.getElementById('credit-hours');
  if (!display) return;
  try {
    const res = await fetch(`${APIBASE}/player/${window.currentPlayerId}/credit`);
    if (res.ok) {
      const data = await res.json();
      display.textContent = data.credit_hours;
      const badge = document.getElementById('time-credit-display');
      if (badge) {
        if (data.credit_hours > 0) badge.style.opacity = "1";
        else badge.style.opacity = "0.5";
      }
    }
  } catch (e) { console.warn("Credit-Update fehlgeschlagen", e); }
}

async function saveProvinceName() {
  const input = document.getElementById('province-name-input');
  if (!input || !window.currentProvinzId) return;
  const newName = input.value.trim();
  if (!newName) return;

  try {
    const res = await fetch(`${APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName })
    });
    if (res.ok) {
      console.log("Provinzname gespeichert:", newName);
    }
  } catch (e) { console.error("Namensänderung fehlgeschlagen", e); }
}

async function loadProvincePreview() {
  const content = document.getElementById('vorschau-content');
  const hoursSelect = document.getElementById('preview-hours-select');
  if (!content || !hoursSelect) return;

  // Sicherstellen, dass die Map geladen ist
  if (Object.keys(window.resourceMap).length === 0) {
    await loadResourceMap();
  }

  const hours = hoursSelect.value;
  content.innerHTML = `<p style="color: var(--text-muted)">Simuliere ${hours} Stunden...</p>`;

  try {
    const url = `${APIBASE}/player/${window.currentPlayerId}/resources/produce?preview_only=true&hours=${hours}`;
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();
    renderPreviewReport(data.bericht, hours);
  } catch (e) {
    content.innerHTML = `<p style="color: var(--accent-danger)">Fehler bei Vorschau: ${e.message}</p>`;
  }
}

function renderPreviewReport(bericht, hours) {
  const content = document.getElementById('vorschau-content');
  // Wir nehmen den Bericht der aktuellen Provinz
  const provIdx = bericht.findIndex(b => b.provinz_id === window.currentProvinzId);
  if (provIdx === -1) {
    content.innerHTML = "<p>Keine Daten für diese Provinz in der Simulation.</p>";
    return;
  }
  const b = bericht[provIdx];

  let html = `
    <div class="preview-report">
      <div class="preview-section-title">Bevölkerung & Effizienz</div>
      <table class="lager-tabelle">
        <thead><tr><th>Kategorie</th><th style="text-align:right">Wert</th></tr></thead>
        <tbody>
          <tr><td>Wohnraum / Max. Pop</td><td style="text-align:right">${b.stats.wohnraum}</td></tr>
          <tr><td>Bevölkerung (Ist)</td><td style="text-align:right">${b.stats.bevoelkerung}</td></tr>
          <tr><td>Arbeitskraft-Bedarf</td><td style="text-align:right">${b.stats.bedarf}</td></tr>
          <tr><td>Produktions-Effizienz</td><td style="text-align:right" class="${b.effizienz < 1 ? 'delta-neg' : 'delta-neu'}">${(b.effizienz * 100).toFixed(0)}%</td></tr>
        </tbody>
      </table>

      <div class="preview-section-title">Rohstoff-Bilanz (über ${hours}h)</div>
      <table class="lager-tabelle">
        <thead>
          <tr>
            <th>Ressource</th>
            <th style="text-align:right">Änderung</th>
            <th style="text-align:right">Prognose</th>
          </tr>
        </thead>
        <tbody>
  `;

  // Wir brauchen Ressourcennamen (wir haben nur IDs in deltas/neues_lager vom Backend)
  // Das Backend gibt IDs zurück, was unpraktisch ist. 
  // TODO: Backend anpassen oder hier mappen. 
  // Kurzer Fix: Wir nutzen die vorhandenen Lagereinträge für Namen-Mapping
  const deltas = b.deltas;
  const forecasts = b.neues_lager;

  for (const [rid, delta] of Object.entries(deltas)) {
    const forecast = forecasts[rid] || 0;
    const colorClass = delta > 0 ? 'delta-pos' : (delta < 0 ? 'delta-neg' : 'delta-neu');
    const sign = delta > 0 ? '+' : '';
    const resName = window.resourceMap[rid] || `Ressource ${rid}`;

    html += `
      <tr>
        <td>${resName}</td>
        <td style="text-align:right" class="${colorClass}">${sign}${delta.toLocaleString('de-DE')}</td>
        <td style="text-align:right">${forecast.toLocaleString('de-DE')}</td>
      </tr>
    `;
  }

  html += `
        </tbody>
      </table>
    </div>
  `;
  content.innerHTML = html;
}

async function executeTurn(hours) {
  if (!confirm(`${hours} Stunden vorspulen? Dies verbraucht dein Zeitguthaben.`)) return;

  try {
    const url = `${APIBASE}/player/${window.currentPlayerId}/resources/produce?hours=${hours}`;
    const res = await fetch(url, { method: 'POST' });
    const data = await res.json();

    if (res.ok) {
      alert(`Erfolg: ${data.message}`);
      loadResources();
      updateCreditDisplay();
      if (window.currentView === 'province') {
        window.loadProvince(window.selectedProvinceCoords.x, window.selectedProvinceCoords.y);
        loadProvinceLager();
      }
    } else {
      alert("Fehler: " + (data.detail || JSON.stringify(data)));
    }
  } catch (e) {
    alert("Serverfehler beim Rundenwechsel: " + e.message);
  }
}

async function loadResourceMap() {
  try {
    const res = await fetch(`${APIBASE}/player/${window.currentPlayerId}/provinzen`);
    if (!res.ok) return;
    const data = await res.json();
    if (data.provinzen && data.provinzen.length > 0) {
      const pid = data.provinzen[0].id;
      // Wir "missbrauchen" den Lager-Endpunkt für EINE Provinz, um alle Namen zu bekommen
      // Alternativ: Neuen Backend-Endpunkt erstellen. Hier machen wir es einfach via Lager.
      const lagerRes = await fetch(`${APIBASE}/player/${window.currentPlayerId}/provinzen/${pid}/lager`);
      if (lagerRes.ok) {
        const lagerData = await lagerRes.json();
        lagerData.eintraege.forEach(item => {
          window.resourceMap[item.ressource_id] = item.ressource_name;
        });
        console.log("Ressourcen-Map geladen:", window.resourceMap);
      }
    }
  } catch (e) { console.warn("Laden der Ressourcen-Map fehlgeschlagen", e); }
}

// ── Exports ──────────────────────────────────────────────────
if (typeof window !== 'undefined') {
  window.loadResources = loadResources;
  window.switchView = switchView;
  window.nextTurn = nextTurn;
  window.showProvinceSubView = showProvinceSubView;
  window.loadProvinceLager = loadProvinceLager;
  window.resolveProvinzId = resolveProvinzId;
  window.updateCreditDisplay = updateCreditDisplay;
  window.saveProvinceName = saveProvinceName;
  window.loadProvincePreview = loadProvincePreview;
  window.executeTurn = executeTurn;
}

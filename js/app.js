// ============================================================
// Hauptlogik – Verbrannte Zone
// ============================================================

const APIBASE = ""; // gameFetch in index.html handles /api prefix now
window.APIBASE = APIBASE;

// Auth check on load
if (!AuthService.getAccessToken()) {
  window.location.href = 'login.html';
}

window.currentPlayerId = AuthService.getPlayerId() ? parseInt(AuthService.getPlayerId()) : null;
if (!window.currentPlayerId) {
  console.error("FATAL: Keine Player-ID gefunden. Authentifizierung fehlerhaft oder Account unvollständig.");
}
window.currentView = 'world';
window.selectedProvinceCoords = null;
window.currentProvinzId = null;
window.resourceMap = {}; // Cache für Ressourcen-Namen [ID] -> Name

// ── Initialisierung ──────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  console.log('Verbrannte Zone lädt...');

  // Display user info
  const userDisplay = document.getElementById('user-display');
  if (userDisplay) {
    userDisplay.textContent = `👤 ${AuthService.getUsername() || 'Spieler'}`;
  }

  loadResources();
  initWorldMap();
  loadResourceMap(); // Ressourcen-Namen laden
  loadMyProvincesDropdown(); // NEU: Dropdown befüllen
  showView('world');

  // Polling für Ressourcen & Notifications
  setInterval(() => {
    loadResources();
    updateNotifications();
  }, 60000);

  // Onboarding: Neuer Spieler → Welcome-Screen, bestehender → Tutorial prüfen
    if (typeof window.checkOnboarding === 'function') {
        checkOnboarding();
    }
    
    updateNotifications();
});

// Logout function
function logout() {
  AuthService.logout();
}

// ── Spieler-Ressourcen laden ─────────────────────────────────
async function loadResources() {
  try {
    const response = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/resources/total`);
    if (response.ok) {
      const data = await response.json();
      
      // Topbar Ressourcen
      updateCount('iron-count', data.iron);
      updateCount('steel-count', data.steel);
      updateCount('fuel-count', data.fuel);
      updateCount('coins-count', data.coins);
      updateCount('pop-count', data.pop_total);
      
      const moralEl = document.getElementById('moral-avg');
      if (moralEl) {
          moralEl.textContent = data.moral_avg !== undefined ? data.moral_avg : '–';
          const resMoral = document.getElementById('res-moral');
          if (resMoral) {
              resMoral.classList.remove('warn', 'danger');
              if (data.moral_avg < 30) resMoral.classList.add('danger');
              else if (data.moral_avg < 50) resMoral.classList.add('warn');
          }
      }

      // Zeitguthaben (an zwei Stellen möglich)
      const creditHours = data.time_credit !== undefined ? data.time_credit : 0;
      updateCount('credit-hours', creditHours);
      
      // Player Info (aus localStorage als Fallback falls API Feld nicht liefert)
      const userDisplay = document.getElementById('user-display');
      if (userDisplay) {
          userDisplay.textContent = `👤 ${data.player_name || AuthService.getUsername() || 'Spieler'}`;
      }
    }
  } catch (error) {
    console.error('Fehler beim Laden der Ressourcen', error);
  }
}

function updateCount(id, val) {
    const el = document.getElementById(id);
    if (el) el.textContent = (val || 0).toLocaleString('de-DE');
}

// ── Haupt-View-System (NEU) ───────────────────────────────────
const VIEWS = ['world', 'province', 'production', 'diplomacy', 'messages', 'gamelog'];

function showView(viewId, params = {}) {
  const { x = null, y = null } = params;

  // Armee-Move-Logik beibehalten
  if (viewId === 'province' && window.movingArmyId) {
      executeArmyMove(window.movingArmyId, x, y);
      return;
  }

  window.currentView = viewId;

  // Alle Hauptansichten ausblenden
  VIEWS.forEach(v => {
      const el = document.getElementById(`${v}-view`);
      if (el) el.style.display = 'none';
  });

  // Alle Sidebar-Inhalte ausblenden
  const sidebarWorld = document.getElementById('sidebar-world-content');
  const sidebarProv = document.getElementById('sidebar-province-content');
  if (sidebarWorld) sidebarWorld.style.display = 'none';
  if (sidebarProv) sidebarProv.style.display = 'none';

  // Navigation Highlight
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  const activeNav = document.getElementById(`nav-${viewId}`);
  if (activeNav) activeNav.classList.add('active');

  // View-spezifische Logik
  if (viewId === 'world') {
    const worldView = document.getElementById('worldmap-view');
    if (worldView) worldView.style.display = 'flex';
    if (sidebarWorld) sidebarWorld.style.display = 'block';
    
    if (typeof window.loadWorldMap === 'function') loadWorldMap();
    window.selectedProvinceCoords = null;
    window.currentProvinzId = null;
    const selectedInfo = document.getElementById('selected-info');
    if (selectedInfo) selectedInfo.innerHTML = '<p>Wähle eine Provinz aus, um sie zu verwalten.</p>';

  } else if (viewId === 'province') {
    const provView = document.getElementById('province-view');
    if (provView) provView.style.display = 'flex';
    if (sidebarProv) sidebarProv.style.display = 'block';

    if (x !== null && y !== null) {
      window.selectedProvinceCoords = { x, y };
      window.currentProvinzId = null;
      if (typeof window.loadProvince === 'function') window.loadProvince(x, y);
      
      // Tab-Logik (letzten Tab oder 'karte')
      const lastTab = localStorage.getItem('last_province_tab') || 'karte';
      if (typeof showProvinceTab === 'function') showProvinceTab(lastTab);
      else if (typeof showProvinceSubView === 'function') showProvinceSubView('map');
      
      resolveProvinzId(x, y);
    }
  } else {
    const targetView = document.getElementById(`${viewId}-view`);
    if (targetView) targetView.style.display = 'block';
    if (sidebarWorld) sidebarWorld.style.display = 'block'; // Fallback sidebar
    
    // Loader aufrufen
    if (viewId === 'production') loadProductionOverview();
    else if (viewId === 'diplomacy') loadDiplomacy();
    else if (viewId === 'messages') loadMessages();
    else if (viewId === 'gamelog') loadGamelog();
  }
  
  loadResources(); // Ressourcen bei jedem View-Wechsel aktualisieren
  updateCreditDisplay();
}

// Kompatibilitätsschicht für alte Aufrufe
function switchView(viewId, x = null, y = null) {
    showView(viewId, { x, y });
}

// ── Dropdown für eigene Provinzen befüllen ───────────────────
async function loadMyProvincesDropdown() {
    try {
        const response = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/provinzen`);
        if (response.ok) {
            const data = await response.json();
            const list = document.getElementById('my-provinces-list');
            if (!list) return;
            
            list.innerHTML = '';
            if (data.provinzen && data.provinzen.length > 0) {
                data.provinzen.forEach(p => {
                    const a = document.createElement('a');
                    a.href = '#';
                    a.textContent = `${p.name || 'Provinz'} [${p.world_x}, ${p.world_y}]`;
                    a.onclick = (e) => {
                        e.preventDefault();
                        showView('province', { x: p.world_x, y: p.world_y });
                    };
                    list.appendChild(a);
                });
            } else {
                list.innerHTML = '<a href="#">Keine Provinzen</a>';
            }
        }
    } catch (e) {
        console.error("Fehler beim Laden der Provinzen fürs Dropdown", e);
    }
}

// ── Notifications aktualisieren ──────────────────────────────
async function updateNotifications() {
    try {
        const res = await gameFetch(`${APIBASE}/messages/unread-count/${window.currentPlayerId}`);
        if (res.ok) {
            const data = await res.json();
            const badge = document.getElementById('unread-badge');
            if (badge) {
                badge.textContent = data.unread_count;
                badge.style.display = data.unread_count > 0 ? 'inline-block' : 'none';
            }
        }
    } catch (e) {
        console.warn("Notification poll failed", e);
    }
}

// ── Toast Notifications ──────────────────────────────────────
function showToast(message, type = 'success') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = { success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' };
    toast.innerHTML = `<span>${icons[type] || ''}</span> <span>${message}</span>`;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ── Gamelog Logik ──────────────────────────────────────────
async function loadGamelog() {
    const list = document.getElementById('gamelog-list');
    if (!list) return;
    list.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px;">Lade Gamelog...</td></tr>';
    
    try {
        const res = await gameFetch(`${APIBASE}/gamelog/?player=${window.currentPlayerId}`);
        if (res.ok) {
            const data = await res.json();
            renderGamelog(data);
        }
    } catch (e) {
        console.error("Fehler beim Laden des Gamelogs", e);
        list.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px; color: #e74c3c;">Fehler beim Laden.</td></tr>';
    }
}

async function searchGamelog() {
    const query = document.getElementById('gamelog-search').value;
    if (!query) return loadGamelog();
    
    const list = document.getElementById('gamelog-list');
    list.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px;">Suche...</td></tr>';
    
    try {
        const res = await gameFetch(`${APIBASE}/gamelog/search?q=${encodeURIComponent(query)}&player=${window.currentPlayerId}`);
        if (res.ok) {
            const data = await res.json();
            renderGamelog(data);
        }
    } catch (e) {
        console.error("Fehler bei Gamelog-Suche", e);
    }
}

function renderGamelog(entries) {
    const list = document.getElementById('gamelog-list');
    if (!entries || entries.length === 0) {
        list.innerHTML = '<tr><td colspan="3" style="text-align:center; padding: 20px; color: #aaa;">Keine Einträge gefunden.</td></tr>';
        return;
    }
    
    list.innerHTML = entries.map(entry => {
        const date = new Date(entry.created_at).toLocaleString('de-DE');
        let typeLabel = entry.event_type;
        let rowStyle = "";
        
        if (entry.event_type === "WAR_DECLARED") rowStyle = "color: #ff5555; font-weight: bold;";
        if (entry.event_type === "PROVINCE_COLONIZED") rowStyle = "color: #55ff55;";
        
        return `<tr style="${rowStyle} border-bottom: 1px solid #333;">
            <td style="padding: 10px; font-size: 0.85rem; color: #888;">${date}</td>
            <td style="padding: 10px; font-size: 0.85rem;"><code>${typeLabel}</code></td>
            <td style="padding: 10px;">${entry.message}</td>
        </tr>`;
    }).join('');
}

// ── Nachrichten Logik ────────────────────────────────────────
window.currentMessageFolder = 'inbox';

async function loadMessages() {
    if (window.currentMessageFolder === 'inbox') showInbox();
    else showOutbox();
}

async function showInbox() {
    window.currentMessageFolder = 'inbox';
    document.getElementById('msg-nav-inbox').classList.add('active');
    document.getElementById('msg-nav-outbox').classList.remove('active');
    
    const list = document.getElementById('messages-list');
    list.innerHTML = '<p style="text-align:center; padding: 20px;">Lade Posteingang...</p>';
    
    try {
        const res = await gameFetch(`${APIBASE}/messages/inbox/${window.currentPlayerId}`);
        if (res.ok) {
            const data = await res.json();
            renderMessagesList(data, 'inbox');
        }
    } catch (e) {
        console.error("Fehler beim Laden des Posteingangs", e);
    }
}

async function showOutbox() {
    window.currentMessageFolder = 'outbox';
    document.getElementById('msg-nav-outbox').classList.add('active');
    document.getElementById('msg-nav-inbox').classList.remove('active');
    
    const list = document.getElementById('messages-list');
    list.innerHTML = '<p style="text-align:center; padding: 20px;">Lade gesendete Nachrichten...</p>';
    
    try {
        const res = await gameFetch(`${APIBASE}/messages/outbox/${window.currentPlayerId}`);
        if (res.ok) {
            const data = await res.json();
            renderMessagesList(data, 'outbox');
        }
    } catch (e) {
        console.error("Fehler beim Laden des Postausgangs", e);
    }
}

function renderMessagesList(messages, folder) {
    const list = document.getElementById('messages-list');
    if (!messages || messages.length === 0) {
        list.innerHTML = `<p style="text-align:center; padding: 20px; color: #aaa;">Keine Nachrichten in ${folder === 'inbox' ? 'deinem Posteingang' : 'deinem Postausgang'}.</p>`;
        return;
    }
    
    list.innerHTML = messages.map(msg => {
        const date = new Date(msg.sent_at).toLocaleString('de-DE');
        const unreadClass = (folder === 'inbox' && !msg.read) ? 'font-weight: bold; border-left: 3px solid #2e7d32;' : '';
        const partner = folder === 'inbox' ? `Von: ${msg.sender_name || 'Unbekannt'}` : `An: ${msg.recipient_name || 'Unbekannt'}`;
        
        return `<div onclick="openMessageDetail(${msg.id})" style="padding: 15px; border-bottom: 1px solid #333; cursor: pointer; display: flex; justify-content: space-between; align-items: center; ${unreadClass}" class="msg-item-hover">
            <div>
                <div style="font-size: 1.05rem; margin-bottom: 3px;">${msg.subject}</div>
                <div style="font-size: 0.85rem; color: #aaa;">${partner}</div>
            </div>
            <div style="font-size: 0.8rem; color: #666;">${date}</div>
        </div>`;
    }).join('');
}

function openNewMessageModal(recipientId = '', subject = '') {
    document.getElementById('msg-recipient-id').value = recipientId;
    document.getElementById('msg-subject').value = subject;
    document.getElementById('msg-body').value = '';
    document.getElementById('new-message-modal').style.display = 'flex';
}

function closeNewMessageModal() {
    document.getElementById('new-message-modal').style.display = 'none';
}

async function sendMessage() {
    const recipientId = parseInt(document.getElementById('msg-recipient-id').value);
    const subject = document.getElementById('msg-subject').value;
    const body = document.getElementById('msg-body').value;
    
    if (!recipientId || !subject || !body) {
        alert("Bitte alle Felder ausfüllen.");
        return;
    }
    
    try {
        const res = await gameFetch(`${APIBASE}/messages/send?sender_id=${window.currentPlayerId}`, {
            method: 'POST',
            body: JSON.stringify({ recipient_id: recipientId, subject, body })
        });
        
        if (res.ok) {
            showToast("Nachricht gesendet!");
            closeNewMessageModal();
            if (window.currentMessageFolder === 'outbox') showOutbox();
        } else {
            const err = await res.json();
            alert("Fehler: " + (err.detail || "Unbekannt"));
        }
    } catch (e) {
        console.error("Fehler beim Senden", e);
    }
}

async function openMessageDetail(msgId) {
    try {
        const res = await gameFetch(`${APIBASE}/messages/${msgId}?player_id=${window.currentPlayerId}`);
        if (res.ok) {
            const msg = await res.json();
            document.getElementById('detail-subject').textContent = msg.subject;
            document.getElementById('detail-from-to').textContent = `Partner: ${msg.sender_name || msg.recipient_name} (ID: ${msg.sender_id === window.currentPlayerId ? msg.recipient_id : msg.sender_id})`;
            document.getElementById('detail-date').textContent = new Date(msg.sent_at).toLocaleString('de-DE');
            document.getElementById('detail-body').textContent = msg.body;
            
            // Buttons
            const btnReply = document.getElementById('btn-reply');
            btnReply.onclick = () => {
                closeMessageDetail();
                openNewMessageModal(msg.sender_id === window.currentPlayerId ? msg.recipient_id : msg.sender_id, "Re: " + msg.subject);
            };
            
            const btnDelete = document.getElementById('btn-delete-msg');
            btnDelete.onclick = () => deleteMessage(msg.id);
            
            document.getElementById('message-detail-modal').style.display = 'flex';
            
            if (window.currentMessageFolder === 'inbox') {
                updateNotifications();
                showInbox();
            }
        }
    } catch (e) {
        console.error("Fehler beim Laden der Nachrichtendetails", e);
    }
}

function closeMessageDetail() {
    document.getElementById('message-detail-modal').style.display = 'none';
}

async function deleteMessage(msgId) {
    if (!confirm("Nachricht wirklich löschen?")) return;
    
    try {
        const res = await gameFetch(`${APIBASE}/messages/${msgId}?player_id=${window.currentPlayerId}`, {
            method: 'DELETE'
        });
        if (res.ok) {
            showToast("Nachricht gelöscht.");
            closeMessageDetail();
            loadMessages();
        }
    } catch (e) {
        console.error("Fehler beim Löschen", e);
    }
}

// Global verfügbar machen
window.showToast = showToast;
window.showView = showView;

// Compatibility aliases
window.switchView = switchView;
// Backend: GET /player/{id}/provinzen
// Response: { player_id, provinzen: [{id, world_x, world_y, name, ...}], anzahl }
async function resolveProvinzId(x, y) {
  try {
    // 1. Zuerst Details zur Zelle/Provinz an diesen Koordinaten holen
    const detailsRes = await gameFetch(`${APIBASE}/world/provinces/at?x=${x}&y=${y}`);
    if (!detailsRes.ok) return;
    const details = await detailsRes.json();
    
    const infoPanel = document.getElementById('selected-info');
    if (!infoPanel) return;
    
    let html = `<p><strong>Position:</strong> (${x}, ${y})</p>`;
    html += `<p><strong>Gelände:</strong> ${details.terrain}</p>`;
    
    if (details.owner_id === parseInt(window.currentPlayerId)) {
      window.currentProvinzId = details.province_id;
      html += `<p style="color: #4caf50">✅ Deine Provinz: <strong>${details.province_name}</strong></p>`;
      
      // Armee an dieser Position?
      const army = window.ARMY_LOCATIONS ? window.ARMY_LOCATIONS[details.province_id] : null;
      if (army) {
        html += `<div style="background: #333; padding: 10px; margin: 10px 0; border-radius: 4px;">`;
        html += `<strong>🪖 Armee #${army.id}</strong><br>Status: ${army.status}<br>Truppen: ${army.units_count}`;
        if (army.status === 'stationed') {
            html += `<br><button class="btn-action" style="margin-top: 5px; font-size: 0.8em;" onclick="prepareArmyMove(${army.id})">Marschbefehl</button>`;
        } else if (army.status === 'in_combat') {
            html += `<br><button class="btn-action" style="margin-top: 5px; font-size: 0.8em; background: #d32f2f;" onclick="retreatArmy(${army.id})">Rückzug</button>`;
        }
        html += `</div>`;
      }
      
      html += `<button class="btn-action" onclick="showProvinceSubView('map')">Verwalten</button>`;
    } else if (details.owner_id) {
      html += `<p style="color: #ff9800">🚩 Fremde Provinz: <strong>${details.province_name}</strong> (Spieler ${details.owner_id})</p>`;
      html += `<button class="btn-action" style="background: #d32f2f">Angreifen (Beta)</button>`;
    } else {
      html += `<p style="color: var(--text-muted); margin-bottom: 15px;">Diese Provinz gehört dir noch nicht.</p>`;
      
      // Check if it's a bunker province (Startprovinz)
      if (details.terrain.toLowerCase().includes('ruine') || details.terrain.toLowerCase().includes('bunker')) {
         html += `<button class="btn-action" onclick="claimBunker(${x}, ${y})" style="background: #2e7d32">🔒 Bunker öffnen (Startprovinz)</button>`;
      } else {
         html += `<button class="btn-action" onclick="claimProvince(${x}, ${y}, '${details.terrain}')">🚩 Besetzen</button>`;
      }
    }
    
    infoPanel.innerHTML = html;
    
  } catch (e) {
    console.warn("ResolveProvinzId failed:", e);
  }
}

async function claimBunker(x, y) {
    // ...
}

// ── Armee-Steuerung (Weltkarte) ──────────────────────────────
window.movingArmyId = null;

function prepareArmyMove(armyId) {
    window.movingArmyId = armyId;
    alert("Wähle nun ein angrenzendes Zielfeld auf der Weltkarte aus.");
}

async function retreatArmy(armyId) {
    try {
        const res = await gameFetch(`${APIBASE}/army/${armyId}/retreat`, { method: 'POST' });
        if (res.ok) {
            alert("Rückzug eingeleitet!");
            if (typeof initWorldMap === 'function') initWorldMap();
        }
    } catch (e) { alert("Fehler beim Rückzug: " + e.message); }
}

async function executeArmyMove(armyId, targetX, targetY) {
    try {
        // 1. Ziel-Provinz-ID holen
        const detailsRes = await gameFetch(`${APIBASE}/world/provinces/at?x=${targetX}&y=${targetY}`);
        const details = await detailsRes.json();
        
        if (!details.province_id) {
            alert("Marsch nur in besetzte Provinzen möglich!");
            return;
        }

        const res = await gameFetch(`${APIBASE}/army/${armyId}/move`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ target_province_id: details.province_id })
        });
        const data = await res.json();
        if (res.ok) {
            alert(`Marschbefehl erteilt! Dauer: ${data.ticks} Ticks.`);
            window.movingArmyId = null;
            if (typeof initWorldMap === 'function') initWorldMap();
        } else {
            alert("Fehler: " + (data.detail || JSON.stringify(data)));
        }
    } catch (e) { alert("Fehler beim Marschbefehl: " + e.message); }
}

async function claimProvince(x, y, terrain) {
  try {
    const url = `${APIBASE}/player/${window.currentPlayerId}/provinzen`;
    const res = await gameFetch(url, {
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
  const militaerContainer = document.getElementById('province-militaer-container');
  const transportContainer = document.getElementById('province-transport-container');
  const btnMap = document.getElementById('menu-btn-map');
  const btnLager = document.getElementById('menu-btn-lager');
  const btnMilitaer = document.getElementById('menu-btn-militaer');
  const btnTransport = document.getElementById('menu-btn-transport');

  if (sub === 'map') {
    mapContainer.style.display = 'block';
    lagerContainer.style.display = 'none';
    if (militaerContainer) militaerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'none';
    btnMap.classList.add('active');
    btnLager.classList.remove('active');
    if (btnMilitaer) btnMilitaer.classList.remove('active');
    if (btnTransport) btnTransport.classList.remove('active');
  } else if (sub === 'lager') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'block';
    if (militaerContainer) militaerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'none';
    btnMap.classList.remove('active');
    btnLager.classList.add('active');
    if (btnMilitaer) btnMilitaer.classList.remove('active');
    if (btnTransport) btnTransport.classList.remove('active');
    loadProvinceLager();
  } else if (sub === 'militaer') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'none';
    if (militaerContainer) militaerContainer.style.display = 'block';
    if (transportContainer) transportContainer.style.display = 'none';
    btnMap.classList.remove('active');
    btnLager.classList.remove('active');
    if (btnMilitaer) btnMilitaer.classList.add('active');
    if (btnTransport) btnTransport.classList.remove('active');
    if (typeof window.loadMilitaryStatus === 'function') window.loadMilitaryStatus();
  } else if (sub === 'transport') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'none';
    if (militaerContainer) militaerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'block';
    btnMap.classList.remove('active');
    btnLager.classList.remove('active');
    if (btnMilitaer) btnMilitaer.classList.remove('active');
    if (btnTransport) btnTransport.classList.add('active');
    if (typeof window.loadTransportView === 'function') loadTransportView();
  } else if (sub === 'vorschau') {
    mapContainer.style.display = 'none';
    lagerContainer.style.display = 'none';
    if (militaerContainer) militaerContainer.style.display = 'none';
    if (transportContainer) transportContainer.style.display = 'none';
    const vContainer = document.getElementById('province-vorschau-container');
    if (vContainer) vContainer.style.display = 'block';

    // Buttons in der Sidebar
    btnMap.classList.remove('active');
    btnLager.classList.remove('active');
    if (btnMilitaer) btnMilitaer.classList.remove('active');
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
      const listRes = await gameFetch(listUrl);
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
    const lagerRes = await gameFetch(lagerUrl);
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
    const response = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/resources/produce`, { method: 'POST' });
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
    const res = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/production/stats`);
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
    const res = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/credit`);
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
    const res = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/provinzen/${window.currentProvinzId}`, {
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
    const res = await gameFetch(url, { method: 'POST' });
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
    const res = await gameFetch(url, { method: 'POST' });
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
  // ... (Code gekürzt für Platz)
}

// ── Diplomatie-Logik ─────────────────────────────────────────

async function loadDiplomacy() {
  const list = document.getElementById('diplomacy-list');
  if (!list) return;

  try {
    const res = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/diplomacy`);
    if (!res.ok) throw new Error("HTTP " + res.status);
    const data = await res.json();

    if (!data.relations || data.relations.length === 0) {
      list.innerHTML = '<tr><td colspan="5" style="padding: 20px; text-align: center;">Keine anderen Spieler bekannt.</td></tr>';
      return;
    }

    list.innerHTML = data.relations.map(rel => `
      <tr style="border-bottom: 1px solid #333;">
        <td style="padding: 10px;"><strong>${rel.target_player_name}</strong></td>
        <td style="padding: 10px;"><span class="status-badge status-${rel.status}">${rel.status.toUpperCase()}</span></td>
        <td style="padding: 10px;">${rel.points}</td>
        <td style="padding: 10px;">${rel.handelsabkommen ? '✅ Aktiv' : '❌ Nein'} ${rel.handels_bonus > 0 ? `(+${rel.handels_bonus}%)` : ''}</td>
        <td style="padding: 10px;">
          <button class="btn-action" style="padding: 4px 8px; font-size: 0.8em;" onclick="updateRelation(${rel.target_player_id}, 'neutral')">Neutral</button>
          <button class="btn-action" style="padding: 4px 8px; font-size: 0.8em; background: #d32f2f;" onclick="updateRelation(${rel.target_player_id}, 'feind')">Krieg</button>
        </td>
      </tr>
    `).join('');

  } catch (e) {
    list.innerHTML = `<tr><td colspan="5" style="color: var(--accent-danger); padding: 20px;">Fehler: ${e.message}</td></tr>`;
  }
}

async function updateRelation(targetId, status) {
  try {
    const res = await gameFetch(`${APIBASE}/player/${window.currentPlayerId}/diplomacy/${targetId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ status: status })
    });
    if (res.ok) {
      loadDiplomacy();
    } else {
      const data = await res.json();
      alert("Fehler: " + (data.detail || JSON.stringify(data)));
    }
  } catch (e) { alert("Serverfehler: " + e.message); }
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

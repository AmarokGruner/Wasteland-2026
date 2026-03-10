# Feature: Spieler-UI Überarbeitung – Navigation, Menüführung & UX

## Ist-Zustand (Probleme)

### Top-Navigation
- Zeigt nur: Eisen | Stahl | Treibstoff + Zeitguthaben
- Fehlt: Münzen, Moral, Bevölkerung (werden nirgendwo angezeigt)
- Kein Benachrichtigungs-Badge (neue Nachrichten, Revolte-Warnung)
- Kein globaler Spieler-Status auf einen Blick

### Haupt-Views (switchView)
- 3 Views: `world` | `province` | `production`
- `production` benutzt Weltkarte-Sidebar → konzeptionell unklar
- Neue Features (Diplomatie, Kampf, Siedler, Nachrichten) haben keinen Platz

### Provinz Sub-Navigation
- 4 Buttons: [Karte] [Lager] [Transport] [Vorschau]
- Fehlt: Militär, Diplomatie, Nachrichten
- Buttons sind sidebar-gebunden → kein klarer visueller Fokus

### Sidebar / Infopanel
- `innerHTML` mit raw HTML-Strings → fehleranfällig, schwer wartbar
- Building-Liste zeigt keine Terrain-Effektivität (kein % Badge)
- Gebäude-Auswahl nicht gefiltert nach aktuellem Terrain der Provinz
- `confirm()` + `alert()` für Bau/Fehler → kein UX-Standard

### Weitere UX-Probleme
- Kein Zurück-Knopf zur eigenen Startprovinz
- Kein Minimap-Overlay in Provinzansicht (wo bin ich auf der Weltkarte?)
- Provinzname-Speichern: kein visuelles Feedback
- Kein Loading-State bei API-Calls
- `BUILDINGS_FALLBACK` hardcoded in province.js → soll durch API ersetzt werden

---

## Ziel: Neue UI-Architektur

```
┌────────────────────────────────────────────────────────────────────┐
│ TOPBAR                                                             │
│ [🌍] Verbrannte Zone   [👤 Spielername]   [🔔3]   [⚙️]  [Logout] │
│ ⚔️ 1.234  🔩 567  ⛽ 89  💰 2.300  😊 Moral: 72%  👥 Pop: 450   │
└────────────────────────────────────────────────────────────────────┘
┌──────────────────────────────────┬─────────────────────────────────┐
│  HAUPTBEREICH                    │ KONTEXTSIDEBAR                  │
│  (Karte / Provinz / Tab-Inhalt)  │ (wechselt je nach View/Tab)     │
└──────────────────────────────────┴─────────────────────────────────┘
```

---

## 1. Topbar Überarbeitung (index.html)

### Ressourcenleiste (immer sichtbar)
```html
<div id="topbar-resources">
  <span class="res-item" id="res-iron">⚔️ <span id="iron-count">0</span></span>
  <span class="res-item" id="res-steel">🔩 <span id="steel-count">0</span></span>
  <span class="res-item" id="res-fuel">⛽ <span id="fuel-count">0</span></span>
  <span class="res-item" id="res-coins">💰 <span id="coins-count">0</span></span>
  <span class="res-item res-moral" id="res-moral">😊 <span id="moral-avg">–</span>%</span>
  <span class="res-item" id="res-pop">👥 <span id="pop-count">0</span></span>
  <span class="res-item res-time" id="time-credit-display">⏳ <span id="credit-hours">0</span>h</span>
</div>
```

### Notification Badge
```html
<button id="notif-btn" onclick="showView('nachrichten')">
  🔔 <span id="notif-badge" class="badge hidden">0</span>
</button>
```
- Badge zählt: ungelesene Nachrichten + aktive Revolte-Warnings
- Rot bei Revolte, Gelb bei ungelesenen Nachrichten, unsichtbar bei 0
- Polling alle 60s: GET /player/{id}/notifications/count → {unread, revolt_count}

---

## 2. Haupt-View-System (app-2.js)

### Bisherige Views → Neue Struktur
```
ALT: world | province | production
NEU: world | province | diplomatie | nachrichten | gamelog
     (production wird Tab innerhalb von province)
```

```javascript
const VIEWS = ['world', 'province', 'diplomatie', 'nachrichten', 'gamelog']

function showView(viewId, params = {}) {
  VIEWS.forEach(v => document.getElementById(`view-${v}`).style.display = 'none')
  document.getElementById(`view-${viewId}`).style.display = 'flex'
  window.currentView = viewId
  // Aktualisiere Nav-Highlight
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'))
  document.getElementById(`nav-${viewId}`)?.classList.add('active')
  // Lade View-Daten
  VIEW_LOADERS[viewId]?.(params)
  updateCreditDisplay()
}
```

### Haupt-Navigation (unterhalb Topbar)
```
[🌍 Weltkarte] [🗺️ Provinzen ▾] [🤝 Diplomatie] [📬 Nachrichten] [📋 Gamelog]
```
- "Provinzen ▾" Dropdown: listet eigene Provinzen, Klick → öffnet Provinzansicht
- Aktiver View = Button highlighted

---

## 3. Provinzansicht – Tab-Navigation (app-2.js + province.js)

### Neue Sub-Tabs (ersetzt die 4 bisherigen Buttons)
```
[🗺️ Karte] [📦 Lager] [🏭 Produktion] [🚛 Transport] [⚔️ Militär] [📊 Vorschau]
```

- Tabs horizontal in Provinz-Header (nicht mehr in Sidebar)
- Jeder Tab = eigener Container-Div, je nach Feature-Verfügbarkeit greyed-out
- `showProvinceTab(tab)` ersetzt `showProvinceSubView(sub)`

```javascript
const PROVINCE_TABS = ['karte','lager','produktion','transport','militaer','vorschau']

function showProvinceTab(tab) {
  PROVINCE_TABS.forEach(t => {
    document.getElementById(`ptab-content-${t}`).style.display = 'none'
    document.getElementById(`ptab-btn-${t}`).classList.remove('active')
  })
  document.getElementById(`ptab-content-${tab}`).style.display = 'block'
  document.getElementById(`ptab-btn-${tab}`).classList.add('active')
  localStorage.setItem('last_province_tab', tab)
  PROVINCE_TAB_LOADERS[tab]?.()
}
// Beim Öffnen einer Provinz: letzten Tab wiederherstellen (außer 'karte' wenn neue Provinz)
```

### Karte-Tab (Provinzgrid)
Bleibt im Wesentlichen wie gehabt (province.js), aber:
- Terrain-Hintergrund durch `.gif` (aus Terrain-API) statt Farbe
- Minimap-Overlay: Kleines 50×50 Canvas in Ecke zeigt Position auf Weltkarte
  - Aktuell angezeigte Provinz = blinkender Punkt

### Sidebar im Karte-Tab (selectProvinceCell → neu)
```
VORHER: innerHTML string-concat
NACHHER: renderSidebarComponent(type, data)
```

```javascript
function renderSidebarComponent(type, data) {
  const panel = document.getElementById('cell-info-panel')
  panel.innerHTML = ''  // clear

  if (type === 'empty_building') {
    panel.appendChild(createBuildMenu(data))
  } else if (type === 'placed_building') {
    panel.appendChild(createBuildingDetail(data))
  } else if (type === 'road') {
    panel.appendChild(createRoadMenu(data))
  }
}

function createBuildMenu({bX, bY, terrain}) {
  // Lädt Gebäude-Liste aus API gefiltert nach Terrain
  // GET /player/{id}/buildings/available?terrain={terrain}&province_id={id}
  // Response: [{id, name, icon, baukosten, terrain_effektivitaet, baubar: true/false, grund}]

  // Rendert:
  // Header: "Gebäudefeld (bX, bY) | Terrain: Grasland (30% Regen)"
  // Filter-Buttons: [Alle] [Nahrung] [Ressourcen] [Industrie] [Militär]
  // Gebäude-Grid: je Karte mit Icon + Name + Effektivitäts-Badge + Kosten-Tag
  //   Grün = 100%, Gelb = 75-99%, Orange = 50-74%, Rot < 50%
  //   Ausgegraut = nicht baubar (Hover zeigt Grund)
  // [Bauen]-Button pro Gebäude → kein confirm(), sondern:
  //   Button → zeigt inline Bestätigungs-Row: "Wirklich bauen?" [✅ Ja] [❌ Nein]
}

function createBuildingDetail({building, bX, bY}) {
  // Rendert: Icon | Name | Level | Produktion (Tabelle)
  // Aktions-Buttons: [⬆️ Aufstufen] [🔧 Reparieren] [🗑️ Abreißen]
  // Abriss ebenfalls mit inline-Confirm (kein Browser confirm())
  // Loading-Spinner während API-Call
}
```

---

## 4. Neue Views

### Diplomatie-View (`view-diplomatie`)
```
Provinzliste des Spielers links (Sidebar) → Details rechts
Details: Spieler-Relationen-Tabelle:
  | Spieler | Status | Handel | Angriff erlaubt | Aktionen |
  Aktionen: [Krieg erklären] [Friedensangebot] [Handelsabkommen]
Warnbanner oben wenn aktiver Kriegszustand
```

### Nachrichten-View (`view-nachrichten`)
```
[📥 Eingang] [📤 Gesendet] [✍️ Neue Nachricht]

Eingang:
  Liste: Sender | Betreff | Zeit | Gelesen?
  Klick → Nachrichtentext rechts
  [Antworten] [Löschen]

Neue Nachricht:
  An: [Spieler suchen...]
  Betreff: [______________]
  Text: [textarea]
  [Senden]
```

### Gamelog-View (`view-gamelog`)
```
Filter: [Provinz ▾] [Typ ▾] [Von: Datum]
Tabelle: Zeit | Typ-Badge | Provinz | Ereignis
Typ-Badges: BAU=blau, REVOLTE=rot, HUNGER=orange, HANDEL=grün, KAMPF=dunkelrot
Unendliches Scrollen (load more bei Scroll-Ende)
```

---

## 5. Loading-States & Feedback

```javascript
// Standard-Muster für alle API-Calls:
async function apiCall(url, options, targetElement) {
  targetElement?.classList.add('loading')
  try {
    const res = await fetch(url, options)
    if (!res.ok) {
      showToast('❌ ' + (await res.json()).detail, 'error')
      return null
    }
    return await res.json()
  } catch(e) {
    showToast('❌ Verbindungsfehler', 'error')
    return null
  } finally {
    targetElement?.classList.remove('loading')
  }
}

function showToast(message, type = 'success') {
  // Snackbar unten rechts, 3s sichtbar, slide-in/out
  // Typen: 'success' (grün), 'error' (rot), 'warning' (gelb), 'info' (blau)
  // Kein alert() / confirm() mehr irgendwo in der App
}
```

---

## 6. CSS-Ergänzungen (style.css)

```css
/* Topbar Ressourcenleiste */
.res-item { display: inline-flex; align-items: center; gap: 4px; padding: 4px 8px;
            background: rgba(0,0,0,0.3); border-radius: 4px; font-size: 13px; }
.res-item.res-moral { color: #48bb78; }
.res-item.res-moral.warn { color: #f59e0b; }
.res-item.res-moral.danger { color: #ef4444; }

/* Notification Badge */
.badge { background: #ef4444; color: white; border-radius: 50%;
         font-size: 10px; padding: 2px 5px; margin-left: 2px; }
.badge.hidden { display: none; }

/* Province Tabs */
.province-tabs { display: flex; gap: 4px; padding: 8px; background: rgba(0,0,0,0.2); }
.province-tabs .tab-btn { padding: 6px 12px; border-radius: 4px; cursor: pointer;
                          background: rgba(255,255,255,0.1); border: none; color: #ddd; }
.province-tabs .tab-btn.active { background: #48bb78; color: #000; font-weight: bold; }
.province-tabs .tab-btn:disabled { opacity: 0.3; cursor: not-allowed; }

/* Building card grid */
.building-grid { display: grid; grid-template-columns: repeat(auto-fill, 80px); gap: 8px; }
.building-card { border-radius: 6px; padding: 6px; text-align: center; cursor: pointer;
                 background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); }
.building-card:hover { background: rgba(255,255,255,0.15); }
.building-card.disabled { opacity: 0.35; cursor: not-allowed; pointer-events: none; }
.eff-badge { font-size: 10px; border-radius: 10px; padding: 1px 5px; font-weight: bold; }
.eff-100 { background: #22543d; color: #9ae6b4; }
.eff-75  { background: #744210; color: #fbd38d; }
.eff-50  { background: #7b341e; color: #feb2b2; }

/* Toast Snackbar */
#toast-container { position: fixed; bottom: 20px; right: 20px; z-index: 9999;
                   display: flex; flex-direction: column; gap: 8px; }
.toast { padding: 12px 20px; border-radius: 8px; color: white; font-weight: 500;
         animation: slideIn 0.3s ease; min-width: 200px; }
.toast.success { background: #276749; }
.toast.error   { background: #9b2c2c; }
.toast.warning { background: #7b6117; }
@keyframes slideIn { from { transform: translateX(100%); opacity: 0; }
                     to   { transform: translateX(0);    opacity: 1; } }
```

---

## Migration-Reihenfolge

```
1. Topbar: Münzen + Moral + Pop ergänzen (loadResources() erweitern)
2. Notification-Badge-Polling einbauen
3. switchView() → showView() umbenennen + neue Views registrieren
4. Province Sub-Tabs: showProvinceSubView() → showProvinceTab() + Tabs ergänzen
5. selectProvinceCell() → renderSidebarComponent() mit API-gefilterter Gebäudeliste
6. alert()/confirm() durch showToast() + inline-Confirm ersetzen
7. Diplomatie-View + Nachrichten-View + Gamelog-View als leere Container anlegen
8. CSS: Building-Cards, Tabs, Toast, Badge
9. BUILDINGS_FALLBACK komplett entfernen → nur noch API
```

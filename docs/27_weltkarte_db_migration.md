# Feature: Weltkarte DB-Migration & Visueller Admin-Karteneditor

## Problem (Ist-Zustand)
Three hardcoded JS files drive the world map – disconnected from DB:

| File | Content | Problem |
|---|---|---|
| world-data.js | FIXED_WORLD_MAP[50][50] hardcoded JS array | Cannot be edited without code deploy |
| terrain-types.js | TERRAIN_TYPES{} color/icon/playable only | Missing regen_pct, gebaeude_effektivitaet, aufwertungen |
| worldmap.js | TERRAIN_FILENAME_MAP (name→gif) | Maintained separately from DB |

seed_terrains.py → DB table "terrain_typen" contains the REAL data:
  id, name, startgebiet, regen_pct, aufwertungen, abwertungen,
  beschreibung, gebaeude_effektivitaet{building_name: pct}
→ Frontend currently IGNORES this table completely

## Target Architecture
```
DB: terrain_typen     ← single source of truth for all terrain properties
DB: world_map_cells   ← replaces FIXED_WORLD_MAP hardcoded array
    (x, y, terrain_id, owner_id, special_flags)

Backend APIs → serve both to frontend
Frontend → loads from API on startup, NO hardcoded JS constants
Admin  → visual 50×50 canvas editor → saves to world_map_cells
```

---

## 1. Backend: New DB Table

```python
WorldMapCell: x(int), y(int), terrain_id(FK terrain_typen.id),
              owner_id(FK players.id nullable),
              is_ruin_province(bool), has_ocean_border(bool)
# Primary key: (x, y) — unique per cell
# Index on owner_id for fast player-province lookup
```

## 2. Backend: Migration Endpoint (one-time)

```
POST /admin/world/import-static
  Reads FIXED_WORLD_MAP from hardcoded Python dict (copy of world-data.js)
  Maps string names to terrain_typen.id via name lookup
  Inserts into world_map_cells (skip existing)
  Sets has_ocean_border = True for cells adjacent to Ozean
  → {"imported": 2500, "skipped": 0}
```

## 3. Backend: Terrain API (replaces terrain-types.js)

```
GET /terrains
→ [{id, name, regen_pct, startgebiet, color(hex), icon, playable,
    beschreibung, gebaeude_effektivitaet{name:pct},
    aufwertungen[str], abwertungen[str], gif_filename}]

# gif_filename: computed from name using same umlaut-replace logic as worldmap.js
# color: new field in terrain_typen, seeded from terrain-types.js values
```

## 4. Backend: World Map API (replaces world-data.js)

```
GET /world/map
→ {size: 50, cells: [[terrain_name, ...] × 50] × 50}
  Format identical to current FIXED_WORLD_MAP for drop-in replacement

GET /world/map/full
→ {size: 50, cells: [{x,y,terrain_id,terrain_name,owner_id,owner_color,
                       is_ruin,has_ocean_border}]}
  Used by Admin editor and diplomacy color overlay

PATCH /world/map/cell (admin only)
  Body: {x:int, y:int, terrain_id:int}
  → updates single cell, recalculates adjacent has_ocean_border

POST /world/map/cells/bulk (admin only)
  Body: {cells:[{x,y,terrain_id}]}  # batch update for brush tool
  → updates multiple cells in one transaction
```

## 5. Frontend Migration (worldmap.js + terrain-types.js)

```javascript
// REMOVE: hardcoded FIXED_WORLD_MAP, TERRAIN_TYPES, TERRAIN_FILENAME_MAP
// ADD: async init sequence

async function initWorldMap() {
  // Load terrain definitions from DB
  const terrains = await fetch('/terrains').then(r => r.json())
  window.TERRAIN_TYPES = {}
  window.TERRAIN_FILENAME_MAP = {}
  for (const t of terrains) {
    window.TERRAIN_TYPES[t.name] = { ...t }
    window.TERRAIN_TYPES[t.name.toLowerCase()] = { ...t }  // compat
    window.TERRAIN_FILENAME_MAP[t.name.toLowerCase()] = t.gif_filename
  }

  // Load map from DB
  const mapData = await fetch('/world/map').then(r => r.json())
  window.WORLD_MAP = mapData.cells  // drop-in for FIXED_WORLD_MAP

  await preloadTerrainImages()
  renderWorldMap()
}

// KEEP: renderWorldMap(), selectWorldProvince(), getTerrainBgImage()
// KEEP: TERRAIN_FILENAME_MAP_RAW → remove english aliases (ocean/grass/forest etc.)
//       old-key compat handled via terrain-types fallback
```

## 6. Admin: Visueller Karteneditor (admin.html – Weltkarte Tab)

### Layout
```
┌─────────────────────────────────────────────┐
│  [🖌️ Malen] [🔍 Inspect] [📋 Info]          │
│  Terrain: [Grasland ▾]  Pinsel: [1x1][3x3]  │
│  [💾 Speichern]  [↩ Rückgängig]  [🔄 Reload]│
├─────────────────────────────────────────────┤
│          50×50 Karten-Canvas                │
│  (Hover: Tooltip  |  Click: paint cell)     │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────▼──────────────┐
    │  TERRAIN PALETTE (rechts)   │
    │  42 Terrain-Typen als Grid  │
    │  Klick = aktives Terrain    │
    │  Farbe+Icon+Name angezeigt  │
    └─────────────────────────────┘
```

### Editor Logic (Vanilla JS)
```javascript
let editorMode = 'paint'  // 'paint' | 'inspect'
let selectedTerrainId = 1  // default: Grasland
let brushSize = 1  // 1 or 3
let pendingChanges = []  // {x,y,terrain_id} – batch before save

canvas.addEventListener('mousemove', (e) => {
  const {x, y} = getCellFromEvent(e)
  showTooltip(x, y)  // terrain + owner + regen_pct
  if (isMouseDown && editorMode === 'paint') paintCell(x, y)
})

function paintCell(cx, cy) {
  const affected = getBrushCells(cx, cy, brushSize)
  for (const {x,y} of affected) {
    window.WORLD_MAP[y][x] = selectedTerrainName
    pendingChanges.push({x, y, terrain_id: selectedTerrainId})
    rerenderCell(x, y)  // update DOM cell only, no full re-render
  }
  updateChangeCounter()  // "47 ungespeicherte Änderungen"
}

async function saveChanges() {
  await fetch('/admin/world/map/cells/bulk', {
    method: 'POST',
    body: JSON.stringify({cells: pendingChanges})
  })
  pendingChanges = []
  showSnackbar('✅ Karte gespeichert')
}

function undoLast() {
  // Restore previous terrain for last painted cell
  // Simple: re-fetch from API (no complex undo stack needed)
}
```

### Inspect Mode (click cell → sidebar)
```
Klick auf Zelle → Sidebar zeigt:
  Position: (x, y)
  Terrain: Grasland | Regen: 30% | Startgebiet: ✅
  Baubare Gebäude: Kartoffelfarm 100%, Imkerei 100%...
  Aufwertung → : keine
  ← Abwertung: keine
  Besitzer: [Spielername] oder "Unbesetzt"
  [Ruinen-Provinz markieren] [Terrain ändern ▾]
```

## 7. Admin: Terrain-Typ Editor (Daten-Editoren Tab)

Replace current stub with full editor:
```
Tabelle: ID | Name | Regen% | Startgebiet | Gebäude (count) | Aufwertung | Aktionen
Klick auf Zeile → Expand:
  Alle Felder editierbar inkl. gebaeude_effektivitaet JSON-Editor
  Farbpicker für map-color
  Vorschau: wie die Zelle auf der Karte aussieht
PATCH /admin/terrains/{id} {"regen_pct":int, "gebaeude_effektivitaet":{...}, ...}
```

## 8. Backend Endpoints Summary

```
GET  /terrains                    → all terrain types (replaces terrain-types.js)
GET  /terrains/{id}               → single terrain with full gebaeude list
PATCH /admin/terrains/{id}        → update terrain properties (admin)

GET  /world/map                   → 50×50 string grid (compat format)
GET  /world/map/full              → rich cell data for admin
PATCH /world/map/cell             → update single cell (admin)
POST /world/map/cells/bulk        → batch update cells (admin editor)
POST /admin/world/import-static   → one-time migration from hardcoded data
```

## Migration Plan (order matters)
```
1. Add world_map_cells table + run POST /admin/world/import-static
2. Deploy GET /terrains + GET /world/map endpoints
3. Update worldmap.js: async initWorldMap() using APIs
4. Update terrain-types.js: remove hardcoded data (keep as empty fallback)
5. Remove world-data.js from index.html script tags (dead file)
6. Deploy Admin editor canvas
7. Verify: admin paints cell → player sees change on next page load
```

## Validation
- PATCH /world/map/cell: terrain_id must exist in terrain_typen table
- Ozean cells adjacent to land: auto-set has_ocean_border on neighbors
- Cannot set player-owned cell to Ozean
- Admin editor: confirmation dialog for bulk-paint of >50 cells
- /world/map response cached 60s server-side (Redis or in-memory dict)

# 📄 Abschnitt 7: Weltkarte & Navigation

## 7.0 Überblick

Die Weltkarte zeigt alle Provinzen der Spieler auf einem gemeinsamen Grid. Sie ermöglicht die Navigation zu eigenen und fremden Provinzen, zeigt diplomatische Beziehungen und militärische Positionen.

---

## 7.1 Weltkarten-Struktur

### 7.1.1 50x50 Grid-System

```javascript
// Welt-Grid (50x50 = 2500 mögliche Provinzen)
{
  "welt": {
    "breite": 50,
    "hoehe": 50,
    "totalZellen": 2500
  }
}
```

**Koordinaten-System:**
```javascript
// Jede Provinz hat world_x und world_y
{
  "id": 42,
  "name": "Siedlung Alpha",
  "player_id": 15,
  "world_x": 12,  // Spalte 12 (0-49)
  "world_y": 8,   // Zeile 8 (0-49)
  "terrain": "Grasland"
}
```

### 7.1.2 Karten-Eigenschaften

```javascript
// Zellen können unterschiedliche Inhalte haben
const cellTypes = {
  PROVINZ: { hasProvince: true, player_id: 42 },
  RUINE: { hasProvince: null, special: 'ruine', buildings: [...] },
  EVENT: { hasProvince: null, special: 'event_combat' },
  FREI: { hasProvince: null, special: null }
};
```

---

## 7.2 Karten-Ansicht

### 7.2.1 World Map Widget

```javascript
<WorldMap 
  centerX={player.province.world_x}
  centerY={player.province.world_y}
  zoom={1.0}  // 1x = 1 Pixel = 1 Grid-Zelle
  playerProvinces={player.provinces}
  visiblePlayerProvinces={getVisibleProvinces(camera)}
/>
```

### 7.2.2 Zoom-Level

| Zoom | Sichtbares Grid | Detailgrad |
|------|---|--------------|
| 0.25x | 200x200 | Große Übersicht |
| 0.5x | 100x100 | Region-Ansicht |
| 1.0x | 50x50 | Ganze Karte |
| 2.0x | 25x25 | Detail-Ansicht |
| 4.0x | 12x12 | Sehr detailiert |

---

## 7.3 Provinz-Icons & Darstellung

### 7.3.1 Icon-Bestimmung

```javascript
function getProvinceIcon(province, viewerPlayerId) {
  // 1. Eigene Provinz
  if (province.player_id === viewerPlayerId) {
    return { icon: '🟦', label: 'Deine Provinz', color: 'blue' };
  }
  
  // 2. Diplomatischer Status
  const relation = getDiplomatieRelation(viewerPlayerId, province.player_id);
  
  if (relation === 'ally') {
    return { icon: '🟩', label: 'Verbündet', color: 'green' };
  }
  
  if (relation === 'friend') {
    return { icon: '🟩', label: 'Freund', color: 'green' };
  }
  
  if (relation === 'enemy') {
    return { icon: '🟥', label: 'Feind', color: 'red' };
  }
  
  if (relation === 'unwanted') {
    return { icon: '🟧', label: 'Unerwünscht', color: 'orange' };
  }
  
  // 3. Neutral
  return { icon: '🟨', label: 'Neutral', color: 'yellow' };
}
```

### 7.3.2 Sonder-Icons

```javascript
// Bunker-Province
if (province.isBunkerProvince) {
  icon += ' (B)';
  tooltip = 'Bunkerprovinz';
}

// Regierungsform-Hauptstadt
if (province.hasRegierungssitz) {
  icon = '👑 ' + icon;
  tooltip = 'Hauptstadt';
}

// Hafen/Küste
if (province.hasHafen) {
  icon = '⚓ ' + icon;
  tooltip = 'Hafen';
}

// Flughafen
if (province.hasFlughafen) {
  icon = '✈️ ' + icon;
  tooltip = 'Flughafen';
}

// Belagert
if (isBelagert(province.id)) {
  icon = '⚔️ ' + icon;
  tooltip = 'Wird belagert';
}
```

### 7.3.3 Ruinen & Freie Provinzen

```javascript
// Freie Provinz (kein Besitzer)
if (!province.player_id) {
  if (province.hasBuildings) {
    // Ruine mit Gebäuden
    return { icon: '🏚️', label: 'Ruine', color: 'gray' };
  } else {
    // Komplett freie Province
    return { icon: '🟫', label: 'Freies Gebiet', color: 'brown' };
  }
}
```

---

## 7.4 Armee-Darstellung

### 7.4.1 Stationierte Armeen

```javascript
// Armee in Provinz
{
  "id": 42,
  "province_id": 88,
  "status": "stationed",
  "owner_id": 15,
  "units_json": '[{"id": 1, "anzahl": 50, "typ": "Rekrut"}]'
}
```

**Darstellung:**
```javascript
function getArmyIcon(armee, viewerplayerId) {
  if (armee.owner_id === viewerPlayerId) {
    return '⚪';  // Weiß = Eigen
  }
  
  const relation = getDiplomatieRelation(viewerPlayerId, armee.owner_id);
  
  if (relation === 'ally' || relation === 'friend') {
    return '🟩';  // Grün = Freund
  }
  
  if (relation === 'enemy') {
    return '🔴';  // Rot = Feind
  }
  
  return '🟨';  // Gelb = Neutral
}
```

### 7.4.2 Marschierende Armeen

```javascript
// Armee unterwegs
if (armee.status === 'marching') {
  const start = getProvince(armee.start_province_id);
  const target = getProvince(armee.target_province_id);
  
  const progress = 1 - (armee.travel_ticks_remaining / army.total_ticks);
  
  // Interpolierte Position
  const currentX = start.world_x + (target.world_x - start.world_x) * progress;
  const currentY = start.world_y + (target.world_y - start.world_y) * progress;
  
  // Darstellung
  return {
    type: 'marcierende_armee',
    x: currentX,
    y: currentY,
    icon: getArmyIcon(armee, viewerPlayerId),
    label: `→ ${target.name}`,
    verbleibend: armee.travel_ticks_remaining
  };
}
```

---

## 7.5 Navigation & Aktionen

### 7.5.1 Klick auf Provinz

```javascript
function onProvinceClick(province, event) {
  // Eigene Province
  if (province.player_id === currentPlayerId) {
    navigateToProvince(province.id);
    return;
  }
  
  // Fremde Province
  const relation = getDiplomatieRelation(currentPlayerId, province.player_id);
  
  if (relation === 'banned' || relation === null) {
    showNotification('Diese Provinz ist nicht verfügbar');
    return;
  }
  
  // Vorschau anzeigen (ohne direkten Zugriff)
  showProvincePreview({
    name: province.name,
    terrain: province.terrain,
    owner: province.player_name,
    level: province.city_level,
    relation: relation
  });
}
```

### 7.5.2 Armee bewegen

```javascript
function sendArmyToProvince(armeeId, targetProvinceId) {
  const armee = getArmee(armee_id);
  const target = getProvince(targetProvinceId);
  
  // Validierung
  if (armee.status !== 'stationed') {
    throw new Error('Armee ist nicht stationiert');
  }
  
  // Distanz-Berechnung
  const start = getProvince(armee.province_id);
  const distance = Math.sqrt(
    Math.pow(target.world_x - start.world_x, 2) +
    Math.pow(target.world_y - start.world_y, 2)
  );
  
  const speed = getMovementSpeed(armee);  // Basierend auf Einheiten
  const ticks = Math.ceil(distance / speed);
  
  // Armee updaten
  armee.status = 'marching';
  armee.start_province_id = armee.province_id;
  armee.target_province_id = targetProvinceId;
  armee.travel_ticks_remaining = ticks;
  armee.total_ticks = ticks;
  
  saveArmee(armee);
  
  logEvent('Armee bewegt', 
    `Armee ${armee.name} (${armee.einheiten_count} Einheit) bewegt sich nach ${target.name}`
  );
}
```

### 7.5.3 Zentrieren auf eigene Provinz

```javascript
function centerMapOnPlayerProvince() {
  const playerProvince = player.provinces[0];  // Erste Province
  
  setCamera({
    centerX: playerProvince.world_x,
    centerY: playerProvince.world_y,
    zoom: currentZoom
  });
  
  logInfo('Karte auf "Siedlung Alpha" zentriert');
}
```

---

## 7.6 UI-Implementierung

### 7.6.1 Weltkarte-Modal

```javascript
<WorldMapModal>
  <Header>
    <Title>🗺️ Weltkarte</Title>
    
    <ZoomControls>
      <Button onClick={() => setZoom(zoom - 0.5)} disabled={zoom <= 0.25}>−</Button>
      <Text>{(zoom * 100).toFixed(0)}%</Text>
      <Button onClick={() => setZoom(zoom + 0.5)} disabled={zoom >= 4.0}>+</Button>
    </ZoomControls>
    
    <Actions>
      <Button onClick={centerOnPlayer}>🎯 Meine Provinz</Button>
      <Button onClick={showPlayerProvinces}>🟦 Nur eigene</Button>
      <Button onClick={toggleArmees}>⚔️ Armeen {showArmee ? 'aus' : 'ein'}</Button>
    </Actions>
  </Header>
  
  <MapContainer>
    <GridCanvas
      width={50}
      height={50}
      zoom={zoom}
      centerX={camera.centerX}
      centerY={camera.centerY}
      cells={worldMapCells}
      armee={visibleArmee}
      onProvinceClick={onProvinceClick}
      onProvinceHover={onProvinceHover}
    />
    
    <CameraIndicator>
      Zeigt: ({Math.round(camera.centerX)}, {Math.round(camera.centerY)})
    </CameraIndicator>
  </MapContainer>
  
  <Legend>
    <h4>Provinzen</h4>
    <LegendItem color="🟦" label="Deine Provinzen" />
    <LegendItem color="🟩" label="Freunde/Verbündete" />
    <LegendItem color="🟨" label="Neutral" />
    <LegendItem color="🟧" label="Unerwünscht" />
    <LegendItem color="🟥" label="Feinde" />
    <LegendItem icon="🏚️" color="🟫" label="Ruinen/Freie Gebiete" />
    
    <h4>Armeen</h4>
    <LegendItem icon="⚪" label="Deine Armeen" />
    <LegendItem icon="🟩" label="Alliierte Armeen" />
    <LegendItem icon="🟨" label="Neutrale Armeen" />
    <LegendItem icon="🔴" label="Feindliche Armeen" />
  </Legend>
</WorldMapModal>
```

### 7.6.2 Provinz-Vorschau-Modal

```javascript
<ProvincePreviewModal province={selectedProvince}>
  <Header>
    <Title>{province.name}</Title>
    <Owner>{province.owner_name}</Owner>
    <Relation status={relation} />
  </Header>
  
  <InfoGrid>
    <InfoItem label="Terrain" value={province.terrain} />
    <InfoItem label="Stadt-Level" value={`Level ${province.city_level}`} />
    <InfoItem label="Koordinaten" value={`(${province.world_x}, ${province.world_y})`} />
  </InfoGrid>
  
  <Actions>
    {relation === 'friend' && (
      <Button onClick={() => navigateToProvince(province.id)}>
        Zu dieser Provinz
      </Button>
    )}
    
    {relation === 'enemy' && (
      <Button onClick={() => showArmyMoveModal(province.id)}>
        Armee schicken
      </Button>
    )}
    
    <Button onClick={showDiplomatieAction}>
      Diplomatie ändern
    </Button>
  </Actions>
</ProvincePreviewModal>
```

---

## 7.7 Datenbank-Strukturen

### 7.7.1 Weltkarte-Tabelle

| Tabelle | Zweck | Wichtige Felder |
|---------|------|-----------------|
| `world_map_cells` | Kartenzellen | `x`, `y`, `province_id`, `special` |
| `provinzen` | Provinz-Daten | `world_x`, `world_y`, `player_id` |

```sql
-- world_map_cells
CREATE TABLE world_map_cells (
  x INTEGER NOT NULL,
  y INTEGER NOT NULL,
  province_id INTEGER,
  special TEXT,  -- 'ruine', 'event_combat', NULL
  PRIMARY KEY (x, y)
);

-- Beispiel-Daten:
INSERT INTO world_map_cells VALUES (12, 8, 42, NULL);  // Province bei (12,8)
INSERT INTO world_map_cells VALUES (25, 30, NULL, 'ruine');  // Ruine
INSERT INTO world_map_cells VALUES (15, 15, NULL, NULL);  // Frei
```

### 7.7.2 Diplomatie-Tabelle

```sql
-- diplomatie
CREATE TABLE diplomatie (
  id INTEGER PRIMARY KEY,
  player1_id INTEGER NOT NULL,
  player2_id INTEGER NOT NULL,
  status TEXT NOT NULL,  -- 'ally', 'friend', 'neutral', 'unwanted', 'enemy'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Beispiel:
INSERT INTO diplomatie VALUES (1, 15, 23, 'ally');  // Spieler 15 & 23 sind Verbündet
```

---

## 7.8 Zusammenfassung & Checkliste

### 7.8.1 To-Do
- [ ] Weltkarte mit 50x50 Grid rendern
- [ ] Zoom-Funktion (0.25x bis 4.0x)
- [ ] Provinzen an Koordinaten anzeigen
- [ ] Diplomatie-Farben anwenden
- [ ] Armeen auf Karte anzeigen
- [ ] Marschierende Armeen animieren
- [ ] Zentriere-Knopf ("Meine Provinz")
- [ ] Provinz-Vorschau beim Klick
- [ ] Weltkarte-Modal mit Legend
- [ ] Ruinen & freie Gebiete anzeigen
- [ ] Armee-Bewegungsformular
- [ ] Koordination in der UI anzeigen
### 7.8.2 Offene Fragen

1. **Karten-Größe**: Ist 50x50 korrekt oder gibt es mehrere Inseln/Regionen?  
   → **Gewählter Ansatz:** Prozedural generierte Karte + Admin-Editor (statisch für Spieler)

**Implementierung:**
```javascript
class AdminWeltEditor {
  constructor() {
    this.breite = 50;
    this.hoehe = 50;
    this.grid = []; // 50×50 Array
    
    // Terrain-Verteilung (Admin-Einstellungen)
    this.terrainDistribution = {
      wasser: 10,      // 10% Wasser (unbewohnbar)
      wueste: 15,      // 15% Wüste (unbewohnbar)
      gebirge: 15,     // 15% Gebirge (schwerer zu erreichen)
      dschungel: 15,   // 15% Dschungel (Spezial-Rohstoffe)
      vulkan: 5,       // 5% Vulkane (Events)
      grasland: 40     // 40% Grasland (Standard)
    };
    
    this.islandShape = 'organic'; // "circle", "rectangle", "organic"
  }
  
  generiereWelt() {
    // Prozedural generieren (Perlin Noise oder Zufall)
    for (let y = 0; y < this.hoehe; y++) {
      for (let x = 0; x < this.breite; x++) {
        const rand = Math.random(); // 0.0 bis 1.0
        
        if (rand < this.terrainDistribution.wasser / 100) {
          this.grid[y][x] = 'wasser'; // 10% Wasser (unbewohnbar)
        } else if (rand < (this.terrainDistribution.wasser + this.terrainDistribution.wueste) / 100) {
          this.grid[y][x] = 'wueste'; // 15% Wüste (unbewohnbar)
        } else if (rand < (this.terrainDistribution.wasser + this.terrainDistribution.wueste + this.terrainDistribution.gebirge) / 100) {
          this.grid[y][x] = 'gebirge'; // 15% Gebirge (schwerer zu erreichen)
        } else if (rand < (this.terrainDistribution.wasser + this.terrainDistribution.wueste + this.terrainDistribution.gebirge + this.terrainDistribution.dschungel) / 100) {
          this.grid[y][x] = 'dschungel'; // 15% Dschungel (Spezial-Rohstoffe)
        } else if (rand < (this.terrainDistribution.wasser + this.terrainDistribution.wueste + this.terrainDistribution.gebirge + this.terrainDistribution.dschungel + this.terrainDistribution.vulkan) / 100) {
          this.grid[y][x] = 'vulkan'; // 5% Vulkane (Events)
        } else {
          this.grid[y][x] = 'grasland'; // 40% Grasland (Standard)
        }
      }
    }
    
    // Insel-Form anwenden (optional)
    if (this.islandShape === 'circle') {
      this.wendeInselForm('circle');
    } else if (this.islandShape === 'rectangle') {
      this.wendeInselForm('rectangle');
    } else if (this.islandShape === 'organic') {
      this.wendeInselForm('organic'); // Prozedural (Perlin Noise)
    }
  }
  
  speichereWelt(weltId) {
    // Grid als JSON speichern (statisch für Spieler!)
    const gridJson = JSON.stringify(this.grid);
    
    // In Datenbank speichern (welt_id, x, y, terrain)
    database.welten.update(weltId, { grid: gridJson });
    
    for (let y = 0; y < this.hoehe; y++) {
      for (let x = 0; x < this.breite; x++) {
        database.welten_grid.insert({
          welt_id: weltId,
          x, y,
          terrain: this.grid[y][x],
          special: this.getSpecial(x, y) // z.B. "vulkan", null
        });
      }
    }
    
    // Welt als "aktiv" markieren (für Spieler freigegeben)
    database.welten.update(weltId, { status: 'aktiv' });
  }
  
  getSpecial(x, y) {
    const terrain = this.grid[y][x];
    
    if (terrain === 'vulkan') {
      return 'vulkan'; // Event-Zelle!
    } else if (terrain === 'dschungel') {
      return Math.random() < 0.1 ? 'ruine' : null; // 10% Chance auf Ruine im Dschungel!
    } else {
      return null; // Keine Special-Zelle
    }
  }
}

// Beispiel:
// Admin erstellt Welt "Alpha" (50×50 Grid)
// 10% Wasser, 15% Wüste, 15% Gebirge, 15% Dschungel, 5% Vulkane, 40% Grasland
// Insel-Form: "organic" (prozedural)
// Nach Speichern: Welt ist für Spieler sichtbar und statisch!

// Spieler können sich auf derselben Welt bewegen (Multiplayer)!
```

**Datenbank:**
```sql
CREATE TABLE welten (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,              -- z.B. "Welt Alpha", "Welt Beta"
  breite INTEGER DEFAULT 50,       -- Standard: 50×50 Grid
  hoehe INTEGER DEFAULT 50,        -- Standard: 50×50 Grid
  status TEXT DEFAULT 'generiert', -- 'generiert', 'aktiv', 'archiviert'
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  grid TEXT NOT NULL               -- 50×50 Grid als JSON (z.B. "grasland", "wasser")
);

CREATE TABLE welten_grid (
  welt_id INTEGER NOT NULL,
  x INTEGER NOT NULL,
  y INTEGER NOT NULL,
  terrain TEXT NOT NULL,           -- "grasland", "wasser", "gebirge"
  special TEXT,                    -- "vulkan", "ruine", null
  
  PRIMARY KEY (welt_id, x, y),
  FOREIGN KEY (welt_id) REFERENCES welten(id)
);

-- Beispiel-Daten:
INSERT INTO welten VALUES (1, 'Welt Alpha', 50, 50, 'aktiv', NOW(), '[["grasland", "wasser"], ...]');

INSERT INTO welten_grid (welt_id, x, y, terrain) VALUES 
  (1, 0, 0, 'wasser'),
  (1, 1, 1, 'grasland'),
  (1, 2, 2, 'gebirge');

-- Admin-Editor:
{
  "welt_id": 1,
  "name": "Welt Alpha",
  "grid_size": [50, 50],
  "terrain_distribution": {
    "wasser": 10,      // 10% Wasser (unbewohnbar)
    "wueste": 15,      // 15% Wüste (unbewohnbar)
    "gebirge": 15,     // 15% Gebirge (schwerer zu erreichen)
    "dschungel": 15,   // 15% Dschungel (Spezial-Rohstoffe)
    "vulkan": 5,       // 5% Vulkane (Events)
    "grasland": 40     // 40% Grasland (Standard)
  },
  "island_shape": "organic", // "circle", "rectangle", "organic" (prozedural)
  "coastline_smoothness": 0.7 // Wie stark Küsten geglättet werden (0-1)
}
```

2. **Sichtweite**: Gibt es "Nebel des Krieges" (nur erforschte Bereiche sichtbar)?  
   → **Nein** - Spieler sehen alle 50×50 Grid-Zellen (Multiplayer-Browserspiel).

3. **Spezial-Zellen**: Welche Events gibt es außer Ruinen?  
   → Vulkane (5% Chance auf Events), Dschungel-Ruinen (10% Chance).

4. **Armee-Geschwindigkeit**: Variiert sie nach Einheitentyp?  
   → **Ja** - 1 Provinz/Stunde Standard, Kavallerie +200% (3×).

---

## 7.9 Zusammenfassung & Checkliste (Aktualisiert)

### 7.9.1 To-Do
- [ ] Weltkarte mit 50x50 Grid rendern
- [ ] Zoom-Funktion (0.25x bis 4.0x)
- [ ] Provinzen an Koordinaten anzeigen
- [ ] Diplomatie-Farben anwenden
- [ ] Armeen auf Karte anzeigen
- [ ] Marschierende Armeen animieren
- [ ] Zentriere-Knopf ("Meine Provinz")
- [ ] Provinz-Vorschau beim Klick
- [ ] Weltkarte-Modal mit Legend
- [ ] Ruinen & freie Gebiete anzeigen
- [ ] Armee-Bewegungsformular
- [ ] Koordination in der UI anzeigen

### 7.9.2 Weltkarte prozedural generiert (NEU!)
- [ ] **Admin-Welteditor** implementieren (50×50 Grid)
- [ ] **Terrain-Verteilung** konfigurieren (10% Wasser, 15% Wüste, etc.)
- [ ] **Insel-Form** anwenden (circle, rectangle, organic)
- [ ] **Grid als JSON speichern** (statisch für Spieler!)
- [ ] **Special-Zellen** hinzufügen (Vulkane, Dschungel-Ruinen)
- [ ] **Welt als "aktiv" markieren** (für Spieler freigegeben)

---

**Abschnitt 7 abgeschlossen ✅**

*Dokument erstellt: 2026-04-06*  
*Stand: Basierend auf FAQ-Analysen + prozedural generierte Karte + Admin-Editor (statisch für Spieler)*

**Nächster Schritt:** Soll ich mit Abschnitt 8 (Spieler-Infos & Einstellungen) fortfahren? ⚙️

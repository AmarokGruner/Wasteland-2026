# Feature: Weltgenerierung & Admin-Tools

**Status:** ✅ Dokumentation an aktuelles Schema angepasst (2026-10-14)  
**Letzte Änderung:** 2026-10-14

---

## Source (FAQ 2.1, 3.2.1, admin.html)

- Weltkarte: Grid von Provinzen (world_map_cells), jede mit Terrain-Typ
- Admin platziert Start-Provinzen (mit Bunker-Slots) und Ruinen-Provinzen
- Account Reset: einmal pro 24h, stellt Spieler zum Start-Zustand zurück
- Admin kann force-build, force-transfer, Tech/MIPS setzen, Events triggern

---

## Aktuelle Datenmodelle (tatsächlich implementiert)

```python
# Terrain-Typen (16 verschiedene)
TerrainType: id, name, playable, color, icon, beschreibung, bild_url, gif_filename
             startgebiet, regen_pct, aufwertungen_json, abwertungen_json, 
             gebaeude_effektivitaet_json, grundwasserspiegel, durchschnittliche_feuchtigkeit

# Weltkarte: Grid von Zellen mit Terrain
world_map_cells (MapCell): id, world_x, world_y, terrain_id, owner_id
                           bild_url, gif_filename

# Provinzen (Spieler-Verwaltung)
Province: id, player_id, world_x, world_y, name, terrain, population, mips, moral
          gesundheit, marktpunkte, strassennetz, einheiten_count
          kulturpunkte, kultureinfluss_total, tech_production, size_level (1-7)
          fields_total, fields_city, arbeitspunkte_current/max
          terrain_yield_malus, sea_access, min_soldiers, security_bonus
          current_city_level (0-8), next_required_building_id
          has_bunker, is_bunker_province, bunker_defense_bonus

# Admin-Protokoll
AdminLog: id, admin_id, action, target_type, target_id, payload(JSON), timestamp
```

---

## Weltgenerierung (tatsächliche Implementierung)

### Aktuelle Struktur

Die Weltkarte besteht aus `world_map_cells` (Grid-Zellen), die über `terrain_id` 
auf `TerrainType` verweisen. Spieler-Provinzen (`Province`) haben Koordinaten 
(`world_x`, `world_y`), die auf eine Zelle zeigen.

```
Weltkarte = Grid von world_map_cells (x, y)
  └── Jede Zelle hat einen terrain_id → TerrainType
  
Provinzen = Spieler-Verwaltung
  └── Jede Provinz hat world_x, world_y → zeigt auf eine Zelle
```

### Admin-Tools (implementiert)

Die folgenden Admin-Funktionen sind über `admin.html` und die API verfügbar:

```
# Weltkarten-Verwaltung (Admin)
GET  /admin/world/*          — Weltkarten-Daten abrufen
POST /admin/world/*          — Weltkarte bearbeiten (Terrain setzen, etc.)

# Provinz-Verwaltung
POST /admin/player/{id}/reset    — Account zurücksetzen (24h Cooldown)
POST /admin/player/{id}/tech     — Tech-Level setzen
POST /admin/player/{id}/mips     — MIPS zuschreiben

# Gebäude-Override
POST /admin/province/{id}/build  — Gebäude erzwingen (bypass checks)

# Events
POST /admin/broadcast            — Broadcast-Nachricht an alle Spieler
```

---

## Admin Tool Endpunkte (vollständige Liste)

### World Management (`/admin/world/*`)
```
GET    /admin/world/map          — Weltkarten-Daten (alle world_map_cells)
POST   /admin/world/terrain      — Terrain-Typen verwalten
GET    /admin/world/provinces    — Alle Provinzen auflisten
```

### Player Management (`/admin/player/*`)
```
POST   /admin/player/{id}/reset      # Account reset (once per 24h enforced)
POST   /admin/player/{id}/tech       # Tech-Level setzen
POST   /admin/player/{id}/mips       # MIPS zuschreiben
```

### Province Override (`/admin/province/*`)
```
POST   /admin/province/{id}/build    # Gebäude erzwingen (bypass checks)
POST   /admin/province/{id}/event    # Event triggern
```

### Logs (`/admin/log`)
```
GET    /admin/log?action=&player=&limit=100  # Admin-Logbuch
```

---

## Validation

- Alle Admin-Endpoints erfordern `role=="admin"` (JWT Token als Query Parameter)
- Account Reset: timestamp check (max einmal pro 24h pro Spieler)
- CSRF-Token erforderlich für alle state-modifying Admin-Requests

---

## Offene Punkte / Verbesserungsvorschläge

### 1. WorldMap/WorldProvince Modelle (optional)
Die ursprüngliche Dokumentation erwähnte `WorldMap` und `WorldProvince` als abstrakte Schicht. 
Das aktuelle Schema verwendet direkt `world_map_cells` und `Province`.

**Option A — Dokumentation anpassen (empfohlen):**
- Bestehende Struktur beibehalten (`world_map_cells` + `Province`)
- Dokumentation auf aktuelles Schema aktualisieren ✅ **UMGESETZT**

**Option B — Abstraktionsschicht implementieren:**
```python
class WorldMap(Base):
    __tablename__ = 'world_maps'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    width = Column(Integer)
    height = Column(Integer)

class WorldProvince(Base):
    __tablename__ = 'world_provinces'
    id = Column(Integer, primary_key=True)
    world_map_id = Column(Integer, ForeignKey('world_maps.id'))
    x = Column(Integer)
    y = Column(Integer)
    terrain_id = Column(Integer, ForeignKey('terrain_typen.id'))
```

**Empfehlung:** Option A wählen — die aktuelle Struktur ist funktional und 
erfordert keine zusätzliche Abstraktionsschicht.

### 2. Ruinen-Provinzen
Die ursprüngliche Dokumentation erwähnte `is_ruin_province` und `preset_buildings`. 
Diese Features sind nicht implementiert.

**Empfohlene Lösung:**
- Neue Spalte `is_ruin_province` in Province Model hinzufügen
- Admin-Endpoint zum Markieren von Ruinen-Provinzen erstellen

### 3. Ocean Border Detection
Die ursprüngliche Dokumentation erwähnte `has_ocean_border` und `coast_field_ids`.

**Aktueller Stand:**
- `sea_access` Feld existiert in Province Model (None, "boats", "ships")
- Keine automatische Küsten-Erkennung implementiert

**Empfohlene Lösung:**
```python
def detect_ocean_border(db: Session, province_id: int) -> bool:
    """Prüft ob Provinz an Ozean grenzt."""
    province = db.query(Province).get(province_id)
    
    # Prüfe benachbarte Zellen auf Ozean-Terrain
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        neighbor = db.query(world_map_cells).filter(
            world_map_cells.world_x == province.world_x + dx,
            world_map_cells.world_y == province.world_y + dy
        ).first()
        
        if neighbor and "Ozean" in neighbor.terrain_name:
            return True
    
    return False
```

---

## Zusammenfassung

| Aspekt | Status |
|--------|--------|
| Weltkarte (world_map_cells) | ✅ Implementiert |
| Terrain-Typen (16 Typen) | ✅ Implementiert |
| Provinz-Verwaltung | ✅ Implementiert |
| Admin-Tools (Reset, Tech, MIPS) | ✅ Implementiert |
| WorldMap/WorldProvince Abstraktion | ❌ Nicht implementiert (Dokumentation angepasst) |
| Ruinen-Provinzen | ❌ Nicht implementiert |
| Ocean Border Detection (automatisch) | ⚠️ Teilweise (`sea_access` Feld existiert) |

**Empfohlene nächste Schritte:**
1. ✅ Dokumentation an aktuelles Schema anpassen (ERLEDIGT)
2. Ruinen-Provinzen implementieren (optional, mittel)
3. Ocean Border Detection automatisieren (optional, niedrig)

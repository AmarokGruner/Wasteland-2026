# 📄 Abschnitt 1: Grid-System & Provinz-Struktur

## 1.0 Überblick

Die Provinz ist auf einem ausführbaren Grid dargestellt. Das Grid-System ist zentral für das Bauen, Navigation und alle räumlichen Aktionen.

---

## 1.1 Grid-Struktur

### 1.1.1 Grundlayout

```
┌──────────────────────────────────────────────┐
│              15×15 Gebäudfelder            │
│     (40×40px) umgeben von einem Ring aus Wegen   │
│                                            │
│  Gitter-Struktur:                          │
│  ├── 15×15 = 225  Gebäudfelder (Land/Stadt) │
│  ├── 16×15 = 240  horizontale Wegfelder (40×10px) │
│  ├── 15×16 = 240  vertikale Wegfelder (10×40px)   │
│  └── 16×16 = 256  Kreuzungsfelder (10×10px)       │
│                                            │
│  Canvas-Dimensionen:                       │
│  ├── Gebäud: 15 × 40px = 600px           │
│  ├── Wege:   16 × 10px = 160px          │
│  ├── Grid-Total: 760px                   │
│  └── Canvas: 800px × 800px (inkl. 20px Rand) │
└──────────────────────────────────────────────┘
```

### 1.1.2 Feldtypen (aus `provinz_feldtypen`)

| Feldtyp | DB-ID | Größe (px) | Baubar | Kategorie | Farbe (leer) |
|---------|-----|--------|--------|-----------|----------|
| **Gebäudefeld (Land)** | `gebaeude` | 40×40 | ✅ Ja | Land | `#5a7a3a` (Grün) |
| **Stadtfeld** | `stadt` | 40×40 | ✅ Ja | Stadt | `#6a6a8a` (Blau-Grau) |
| **Wegfeld** | `weg` | 40×10 (horizontal)<br>10×40 (vertikal) | ✅ Ja | Infrastruktur | `#8b7355` (Braun) |
| **Kreuzung** | `kreuzung` | 10×10 | ✅ Ja | Infrastruktur | `#7a6345` (Dunkelbraun) |

**STADTAUSBAU ist KEIN Feldtyp!**
- Stadtausbau = Prozess, der weitere **Stadtfelder** freischaltet
- Die Position/Menge wird im **Admin: Stadt-Grid Konfiguration** festgelegt
- Spiel-Logik: `current_city_level` (1-8) → prüft `city_expansion_configs`

### 1.1.3 Grid-Dimensionen (KORRIGIERT: 800×800px mit Rand)

```javascript
// Canvas-Größe mit 10px Rand um das Grid
const canvasWidth = 800;   // 760px Grid + 20px Rand (10px links/rechts)
const canvasHeight = 800;  // 760px Grid + 20px Rand (10px oben/unten)

// Grid-Berechnung:
const BUILDING_CELL = 40;  // Gebäude: 40×40px
const PATH_CELL = 10;      // Weg/Crossing: 10×10px

// 15×15 Grid-Layout mit äußerem Wegrand:
//  Gebäudfelder:  15 × 40px = 600px
//  Wege:          16 × 10px = 160px
//  Grid-Total:    760px
//  + Rand:        2 × 10px = 20px
//  Canvas:        800px × 800px
```

---

## 1.2 Stadt-Grid-Konfiguration (Admin-Editor)

### 1.2.1 Konzept

**Stadtausbau wird vom Admin im Editor konfiguriert!**
- Keine feste 10×10-Matrix im Spielcode
- Admin wählt im **Stadt-Grid Konfiguration**-Editor:
  1. Level aus (1-8)
  2. Markiert die Felder, die bei diesem Level freigeschaltet werden
  3. Speichert Konfiguration
- Spiel-Logik liest Konfiguration aus `city_expansion_configs`

### 1.2.2 Datenbank-Struktur

```sql
-- city_expansion_configs
-- level: 1-8 (Stadt-Level)
-- unlocked_fields_json: Array von Feld-IDs

-- Feld-ID Berechnung: zeile × 15 + spalte (0-indexiert)
-- Beispiel: Zeile 6, Spalte 4 → ID = 6×15 + 4 = 94

INSERT INTO city_expansion_configs VALUES (1, '[94, 109, 110, 111, 116]');
-- Level 1 (Camp): 5 Felder freigeschaltet
```

---

*[Der Rest der Datei bleibt unverändert...]*

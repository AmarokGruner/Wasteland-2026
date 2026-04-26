# 📄 Abschnitt 5: Forschung & Tech-System

## 5.0 Überblick

Das Tech-System bestimmt, welche Gebäude ein Spieler bauen kann. Tech-Punkte werden akkumulativ produziert und dienen ausschließlich zur Freischaltung von Gebäuden. Es gibt keine Tech-Verluste oder Upgrades - nur Freischaltung durch Erreichen bestimmter Tech-Level-Werte.

---

## 5.1 Tech-System-Grundlagen

### 5.1.1 Tech-Punkte (Forschungspunkte)

```
Rolle: FREISCHALT-MEHRLEISTUNG
Produktion: Durch spezielle Gebäude (1-5 Punkte/Tag)
Speicher: UNLIMITED (akkumulativ)
Verwendung: Gebäude freischalten
Verfall: NEIN (bleiben erhalten)
```

**Tech-Punkte sind KEINE Währung!**
- Kein Verbrauch (nur Threshold-basierte Freischaltung)
- Immer steigend (1250, 1300, 1350, ...)
- Pro Gebäude wird ein Mindest-Tech-Level benötigt

### 5.1.2 Gebäudetechnologie-Level

```javascript
// Jede Gebäudetyp hat ein tech_level
{
  "id": 1,
  "name": "Bunker",
  "tech_level": 0,      // Sofort verfügbar
  "produktion": "[{\"ressource\": \"Wasser\", \"menge\": 50}]"
}

{
  "id": 3,
  "name": "Erdnussfarm",
  "tech_level": 50,     // Benötigt 50 Tech-Punkte
  "produktion": "[{\"ressource\": \"Erdnüsse\", \"menge\": 20}]"
}

{
  "id": 8,
  "name": "Kakteenplantage",
  "tech_level": 100,    // Benötigt 100 Tech-Punkte
  "produktion": "[{\"ressource\": \"unbekannter Rohstoff\", \"menge\": 10}]"
}
```

**Freischaltungs-Logik:**
```javascript
function isBuildingUnlocked(player, building) {
  return player.total_tech >= building.tech_level;
}

// Beispiel:
// Spieler hat 1,250 Tech-Punkte
// Kakteenplantage benötigt 100
// Ergebnis: ✅ FREIGESCHALTET (1250 >= 100)
```

### 5.1.3 Tech-Produktion durch Gebäude

| Gebäude | Tech/Tag | Tech-Level | Kategorie |
|---------|---------|------------|----------|
| **Bunker** | 2 | 0 | Start-Gebäude |
| **Feuerstelle** | 1 | 0 | Basis |
| **Schule** | 5 | 10 | Bildung |
| **Ruine-Laboratorium** | 2 | 15 | Sonder |
| **Schulungszelt** | 4 | 5 | Bildung |
| **Erfinderwerkstatt** | 3 | 20 | Produktion |
| **Grabungsstätte** | 1 | 10 | Sonder |

**Tech-Berechnung pro Provinz:**
```javascript
function calculateTechProduction(province) {
  const buildings = province.buildings;
  
  let totalTech = 0;
  for (const building of buildings) {
    const type = getBuildingType(building.type_id);
    if (type.spezialeigenschaften && type.spezialeigenschaften.techproduktion) {
      totalTech += type.spezialeigenschaften.techproduktion;
    }
  }
  
  return totalTech;
}

// Beispiel:
// 1 Bunker (+2) + 2 Schulen (+10) = 12 Tech/Tag
```

---

## 5.2 Tech-Level-Verteilung

### 5.2.1 Gebäudetechnologie-Level in Datenbank

Aus der Datenbankanalyse (verbrannte_zone.db):

```
Tech-Level-Bereiche:
├── Level 0-10:  🟢 40+ Gebäude (Basis)
├── Level 15-50:  🟡 60+ Gebäude (Frühe Tech)
├── Level 55-100: 🟠 45+ Gebäude (Mittlere Tech)
├── Level 105-150: 🔴 25+ Gebäude (Hohe Tech)
└── Level 155-200: ⚫ 15+ Gebäude (Späte Tech)
```

**Anzahl Gebäude pro Tech-Level (DB-Auszug):**
```
Tech    2:  3 Gebäude
Tech    5:  9 Gebäude
Tech   10:  9 Gebäude
Tech   15:  4 Gebäude
Tech   20:  5 Gebäude
Tech   25:  9 Gebäude
Tech   50:  5 Gebäude
Tech  100:  9 Gebäude
Tech  150:  3 Gebäude
Tech  200:  5 Gebäude
...
```

### 5.2.2 Tech-Verteilung-Strategie

```javascript
// Spieler-Progression
const techProgression = {
  // Phase 1: Start (Day 0-10)
  phase1: {
    target: 50,
    description: "Basis-Gebäude freischalten",
    timeEstimate: "5-10 Tage bei +5-10 Tech/Tag",
    unlockedBuildings: "Bunker, Feuerstelle, Kartoffelfarm, ..."
  },
  
  // Phase 2: Frühe Tech (Day 10-30)
  phase2: {
    target: 100,
    description: "Frühe Infrastruktur",
    timeEstimate: "10-20 Tage bei +8-15 Tech/Tag",
    unlockedBuildings: "Schule, Brunnen, Webstube, ..."
  },
  
  // Phase 3: Mittlere Tech (Day 30-60)
  phase3: {
    target: 250,
    description: "Industrie & Handel",
    timeEstimate: "20-40 Tage bei +12-20 Tech/Tag",
    unlockedBuildings: "Münzerei, Kontor, Bank, ..."
  },
  
  // Phase 4: Hohe Tech (Day 60-120)
  phase4: {
    target: 500,
    description: "Fortgeschrittene Gebäude",
    timeEstimate: "40-80 Tage bei +15-25 Tech/Tag",
    unlockedBuildings: "Hightech-Labor, Spezialgebäude"
  },
  
  // Phase 5: Späte Tech (Day 120+)
  phase5: {
    target: 1000,
    description: "Alle Gebäude freischalten",
    timeEstimate: "80-150 Tage bei +20-30 Tech/Tag",
    unlockedBuildings: "Alle Gebäude"
  }
};
```

---

## 5.3 Tech-Berechnung & Optimierung

### 5.3.1 Aktuelle Produktionsrate

```javascript
function getTechStatus(player) {
  // 1. Aktuelle Produktion berechnen
  const productionPerDay = calculatePlayerTechProduction(player);
  
  // 2. Nächsten Meilenstein berechnen
  const nextThreshold = getNextTechThreshold(player.total_tech);
  const pointsNeeded = nextThreshold - player.total_tech;
  const daysEstimate = Math.ceil(pointsNeeded / productionPerDay);
  
  return {
    total: player.total_tech,
    productionPerDay: productionPerDay,
    nextThreshold: nextThreshold,
    pointsNeeded: pointsNeeded,
    daysEstimate: daysEstimate,
    unlockedBuildings: calculateUnlockedBuildings(player.total_tech)
  };
}

// Beispiel:
// Total: 1,250 Tech
// Produktion: +12/Tag
// Nächster Schwellwert: 1,500
// Benötigt: 250 Punkte
// Geschätzt: 21 Tage
```

### 5.3.2 Tech-Optimierung

```javascript
// Build-Empfehlungen für mehr Tech
function getTechOptimizationSuggestions(player) {
  const suggestions = [];
  
  // 1. Analyse fehlender Tech-Gebäude
  const unlockedBuildings = getBuildingsWithTechProduction(player);
  
  // 2. Fehlende Gebäude vorschlagen
  const potentialBuildings = [
    { name: "Schule", techProduction: 5, cost: 5000, unlocked: player.total_tech >= 10 },
    { name: "Schulungszelt", techProduction: 4, cost: 3200, unlocked: player.total_tech >= 5 },
    { name: "Erfinderwerkstatt", techProduction: 3, cost: 12000, unlocked: player.total_tech >= 20 }
  ];
  
  for (const building of potentialBuildings) {
    if (building.unlocked && !hasBuilding(player, building.name)) {
      suggestions.push({
        building: building.name,
        techBonus: building.techProduction,
        cost: building.cost,
        description: `+${building.techProduction} Tech/Tag`
      });
    }
  }
  
  return suggestions;
}
```

---

## 5.4 Tech-Baum-Visualisierung

### 5.4.1 Tech-Baum-Konzept

```
┌─────────────────────────────────────┐
│         🔬 Tech-Baum               │
│                                     │
│   1,250/10,000 gesammelte Tech    │
│   🔓 85/127 Gebäude freigeschaltet │
│                                     │
│      ┌─────────────────┐           │
│      │   LEVEL 0       │           │
│      │  🔓 ALLES      │           │
│      └───────┬─────────┘           │
│              │                      │
│        ┌─────▼─────┐               │
│        │  LEVEL 5  │               │
│        │ 🔓 12/15  │               │
│        └─────┬─────┘               │
│              │                      │
│        ┌─────▼─────┐               │
│        │  LEVEL 10 │               │
│        │ 🔓 8/10   │               │
│        └─────┬─────┘               │
│              │                      │
│        ┌─────▼─────┐               │
│        │  LEVEL 50 │               │
│        │ 🔒 0/5    │ 🎯 Nächster! │
│        └───────────┘               │
│                                     │
│ 🎯 Nächste Gruppe (Level 50):     │
│ ├── Erdnussfarm (50)              │
│ ├── [4 weitere Gebäude...]        │
│ └── Benötigt: 1,500 weitere Tech  │
└─────────────────────────────────────┘
```

### 5.4.2 Gebäude nach Tech-Level gruppieren

```javascript
const buildingsByTechLevel = {
  0: [
    { name: "Bunker", tech: 0, unlocked: true },
    { name: "Kartoffelfarm", tech: 0, unlocked: true },
    { name: "Imkerei", tech: 0, unlocked: true }
  ],
  5: [
    { name: "Schulungszelt", tech: 5, unlocked: true },
    { name: "Tabakplantage", tech: 5, unlocked: true },
    { name: "Wollspinnenzucht", tech: 5, unlocked: true }
  ],
  10: [
    { name: "Schule", tech: 10, unlocked: true },
    { name: "Brunnen", tech: 10, unlocked: true },
    { name: "Webstube", tech: 10, unlocked: true }
  ],
  50: [
    { name: "Erdnussfarm", tech: 50, unlocked: false },
    { name: "Vorratskammer", tech: 50, unlocked: false }
  ],
  100: [
    { name: "Kakteenplantage", tech: 100, unlocked: false }
  ]
  // ...
};
```

---

## 5.5 UI-Implementierung

### 5.5.1 Tech-Widget (Dashboard)

```javascript
// Dashboard-Widget
{
  "tech": {
    "total": 1250,
    "productionPerDay": 12,
    "nextThreshold": 1500,
    "pointsNeeded": 250,
    "daysEstimate": 21,
    "unlockedCount": 85,
    "totalCount": 127,
    "progressPercentage": 67
  },
  "productionBreakdown": [
    { "building": "Schule", "count": 2, "techPerDay": 10 },
    { "building": "Bunker", "count": 1, "techPerDay": 2 },
    { "building": "Feuerstelle", "count": 0, "techPerDay": 0 }
  ]
}
```

### 5.5.2 Tech-Übersichts-Screen

```javascript
// Tech-Baum-Überblick
<TechOverview>
  <TechSummary total={1250} production={12} next={1500} />
  <TechProgressBar current={1250} max={10000} />
  
  <BuildingGroups>
    <TechGroup level={0} buildings={buildingsByTechLevel[0]} unlocked={true} />
    <TechGroup level={5} buildings={buildingsByTechLevel[5]} unlocked={true} />
    <TechGroup level={10} buildings={buildingsByTechLevel[10]} unlocked={true} />
    <TechGroup level={50} buildings={buildingsByTechLevel[50]} unlocked={false} />
    {/* ... */}
  </BuildingGroups>
  
  <OptimizationSuggestions>
    <Suggestion>
      Schulungszelt bauen (+4 Tech/Tag)
    </Suggestion>
    <Suggestion>
      Schule bauen (+5 Tech/Tag)
    </Suggestion>
  </OptimizationSuggestions>
</TechOverview>
```

### 5.5.3 Gebäudetechnologie-Freischalt-Info

```javascript
// Detail-Modal für Gebäude
<BuildingDetail building={building}>
  {building.unlocked ? (
    <Status unlocked={true}>
      <Icon>🔓</Icon>
      <Text>FREIGESCHALTET</Text>
    </Status>
    <Button>Bauen</Button>
  ) : (
    <Status unlocked={false}>
      <Icon>🔒</Icon>
      <Text>Benötigt Level {building.techLevel}</Text>
      <Progress current={player.tech} required={building.techLevel} />
      <Text>Noch: {building.techLevel - player.tech} Tech</Text>
    </Status>
    <Estimate>
      {daysNeeded} Tage bei aktueller Produktion
    </Estimate>
  )}
</BuildingDetail>
```

---

## 5.6 Datenbank-Strukturen

### 5.6.1 Wichtige Tabellen

| Tabelle | Zweck | Wichtige Felder |
|---------|-----|--------------------|
| `gebaeude_typen` | Gebäudedefinitionen | `tech_level`, `produktion`, `spezial_eigenschaften` |
| `provinzen` | Provinz-Daten | `tech_level` (veraltet), `tech_production` |
| `players` | Spieler-Daten | `tech_level` (gesammelte Tech-Punkte) |

### 5.6.2 Tech-Produktion in DB

```sql
-- players Tabelle
CREATE TABLE players (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL,
  tech_level INTEGER DEFAULT 0,        -- Gesammelte Tech-Punkte
  tech_production INTEGER DEFAULT 0,   -- Aktuelle Produktion/Tag (berechnet)
  -- ... andere Felder
);

-- gebaeude_typen Tabelle
CREATE TABLE gebaeude_typen (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  tech_level INTEGER DEFAULT 0,        -- Erforderliches Tech für Freischaltung
  produktion TEXT,                     -- JSON: Ressourcen-Produktion
  spezial_eigenschaften TEXT,          -- JSON: { "techproduktion": 2 }
  -- ... andere Felder
);
```

**Hinweis:** `tech_level` in `players` ist hier die gesammelte Punktzahl, nicht das aktuelle "Level".

---

## 5.7 Tick-Logik (Server)

### 5.7.1 Tägliche Tech-Produktion

```javascript
// Server Tick (täglich für Tech)
async function processTechProduction() {
  const provinces = await database.provinzen.all();
  
  for (const province of provinces) {
    const player = await database.players.get(province.player_id);
    
    // Tech-Produktion berechnen
    const production = calculateTechProduction(province);
    
    // Addieren (unbegrenzt speicherbar)
    player.tech_level += production;
    
    // Update DB
    await database.players.update(player);
    
    // Gamelog-Eintrag
    if (production > 0) {
      await database.game_logs.insert({
        player_id: player.id,
        event_type: 'tech_production',
        message: `Produziert ${production} Tech-Punkte`,
        details: JSON.stringify({ province: province.name, production })
      });
    }
  }
}
```

---

## 5.8 Zusammenfassung & Checkliste

### 5.8.1 To-Do für Implementierung

- [ ] **Tech-Punkte** akkumulativ speichern (keine Obergrenze)
- [ ] **Tech-Produktion** pro Gebäude berechnen & täglich addieren
- [ ] **Tech-Freischaltung** prüfen (player.tech >= building.tech_level)
- [ ] **Tech-Übersicht** mit Baumb-Struktur anzeigen
- [ ] **Optimierungsvorschläge** für fehlende Tech-Gebäude
- [ ] **Tech-Widget** im Dashboard (Produktion, Fortschritt)
- [ ] **Gebäude-Filter** nach Freischalt-Status
- [ ] **Estimate** für nächste Freischaltung (Tage berechnet)
- [ ] **Tick-Logik** für tägliche Tech-Produktion

### 5.8.2 Offene Fragen (für später)

- [x] **Tech-Produktion in DB:** *Ist `tech_level` in `players` die gesammelte Punktzahl?*  
  → Wir führen eine separate Spalte `total_tech` ein; `tech_level` bleibt für andere Zwecke.

- [x] **Build-Verfeinerung:** *Gibt es Gebäude, die nur mit bestimmten combos freigeschaltet werden?*  
  → Wir bleiben bei einem simplen Schwellenwert (`tech_level` ≥ X); keine Kombinations‑Flags.

- [x] **Tech-Verlust:** *Gibt es Szenarien, in denen Tech verloren geht? (Antwort: Nein)*  
  → Tech‑Punkte werden ausschließlich additiv erworben (kein Verlust).

- [x] **Resource-Suche via Tech-Level:** *Der Tech-Level bestimmt, welche Rohstoffe durch Geldsuche gefunden werden können; eine Suche kostet Geld und nutzt eine Wahrscheinlichkeits-Tabelle + Terraintyp-Modifikator.*  
  → **Gewählter Ansatz:** Wahrscheinlichkeits-Tabelle + Terraintyp-Modifikator (60% Basis × Terrain)

**Implementierung:**
```javascript
function sucheRohstoff(province, rohrstoffTyp) {
  // Tech-Level prüfen ob Rohstoff freigeschaltet ist
  const requiredTech = rohrstoffTyp.required_tech_level; // z.B. 50, 100, 200
  
  if (province.player.tech_level < requiredTech) {
    throw new Error(`Benötigt Tech-Level ${requiredTech}`);
  }
  
  // Kosten abziehen (immer gleich)
  const kosten = rohrstoffTyp.suchkosten; // z.B. 100, 200, 500 MIPS
  if (province.provinzkonto < kosten) {
    throw new Error('Nicht genug MIPS');
  }
  
  province.provinzkonto -= kosten;
  
  // Terraintyp-Modifikator aus JSON lesen
  const terrainModifiers = JSON.parse(rohrstoffTyp.terrain_modifiers); // {"grasland": 1.0, "wüste": 0.5}
  const terrain = province.terrain; // z.B. "grasland", "wüste"
  const modifikator = terrainModifiers[terrain] || 1.0; // Standard: 1.0
  
  // Fundwahrscheinlichkeit berechnen (Basis × Terraintyp-Modifikator)
  const baseWahrscheinlichkeit = rohrstoffTyp.base_fund_wahrscheinlichkeit; // z.B. 0.6 (60%)
  const effectiveWahrscheinlichkeit = baseWahrscheinlichkeit * modifikator; // z.B. 0.6 × 1.0 = 0.6 (Grasland)
  
  // Maximal auf 1.0 begrenzen, Minimum auf 0.05 (5%)
  const fundWahrscheinlichkeit = Math.min(Math.max(effectiveWahrscheinlichkeit, 0.05), 1.0);
  
  // Zufall prüfen (Zufall!)
  const zufall = Math.random(); // 0.0 bis 1.0
  
  if (zufall < fundWahrscheinlichkeit) {
    // Fund! Rohstoff hinzufügen
    province.rohstoffe.push(rohrstoffTyp);
    
    logEvent('Bodenschatz', `${rohrstoffTyp.name} in ${province.name} (${province.terrain}) gefunden!`);
    
    return true; // Erfolgreich!
  } else {
    // Kein Fund (Ressourcen verschwendet)
    logEvent('Bodenschatz', `Keine Vorkommen von ${rohrstoffTyp.name} in ${province.name} (${province.terrain})`);
    
    return false; // Nicht erfolgreich!
  }
}

// Beispiel:
// Tech = 100, Suche nach Eisen (60% Basis) in Grasland (Modifikator 1.0) → 60% Fundwahrscheinlichkeit
// Tech = 100, Suche nach Eisen (60% Basis) in Wüste (Modifikator 0.5) → 30% Fundwahrscheinlichkeit
```

**Datenbank:**
```sql
CREATE TABLE vorkommen (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,              -- z.B. "Eisen", "Gold"
  required_tech_level INTEGER NOT NULL, -- z.B. 50, 100, 200
  suchkosten INTEGER NOT NULL,     -- z.B. 100, 200, 500 MIPS
  base_fund_wahrscheinlichkeit REAL NOT NULL, -- z.B. 0.6 (60%)
  terrain_modifiers TEXT           -- {"grasland": 1.0, "wüste": 0.5}
);

-- Beispiel-Daten:
INSERT INTO vorkommen VALUES (1, 'Eisen', 50, 200, 0.6, '{"grasland": 1.0, "wüste": 0.5}');
```

---

## 5.9 Zusammenfassung & Checkliste (Aktualisiert)

### 5.9.1 To-Do für Implementierung

- [ ] **Tech-Punkte** akkumulativ speichern (keine Obergrenze)
- [ ] **Tech-Produktion** pro Gebäude berechnen & täglich addieren
- [ ] **Tech-Freischaltung** prüfen (player.tech >= building.tech_level)
- [ ] **Tech-Übersicht** mit Baumb-Struktur anzeigen
- [ ] **Optimierungsvorschläge** für fehlende Tech-Gebäude
- [ ] **Tech-Widget** im Dashboard (Produktion, Fortschritt)
- [ ] **Gebäude-Filter** nach Freischalt-Status
- [ ] **Estimate** für nächste Freischaltung (Tage berechnet)
- [ ] **Tick-Logik** für tägliche Tech-Produktion

### 5.9.2 Rohstoff-Suche (NEU!)

- [ ] **vorkommen Tabelle** erstellen (name, required_tech_level, suchkosten, base_fund_wahrscheinlichkeit, terrain_modifiers)
- [ ] **Suche-Funktion** implementieren (Tech-Level prüfen, Kosten abziehen, Wahrscheinlichkeit berechnen)
- [ ] **Terraintyp-Modifikator** aus JSON lesen (z.B. {"grasland": 1.0, "wüste": 0.5})
- [ ] **Fundwahrscheinlichkeit** berechnen (Basis × Terrain)
- [ ] **Zufall prüfen** (Math.random() < Wahrscheinlichkeit)
- [ ] **Gamelog-Einträge** für Funde/Nicht-Funde

---

**Abschnitt 5 abgeschlossen ✅**

*Dokument erstellt: 2026-04-05*  
*Stand: Basierend auf Datenbank-Analysen + Wahrscheinlichkeits-Tabelle + Terraintyp-Modifikator*

**Nächster Schritt:** Soll ich mit Abschnitt 6 (Rohstoffe & Lager) fortfahren? 🏭

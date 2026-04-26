# 📄 UI-Implementierung - Zusammenfassung aller Entscheidungen

**Erstellt:** 2026-04-26  
**Status:** Alle 8 Fragen entschieden ✅

---

## ❓ Frage 1: Bevölkerungsalterung - Bildungseinfluss auf Kinderphase

**Gewählter Ansatz:** Lineare Skalierung  
**Formel:** `Kinderphase = 1 - (Bildung / 1000)`  
**Effekt:** Bei Bildung = 500 → Kinderphase = 0.5 Tage (-50%)

**Implementierung:**
```javascript
function berechneKinderPhase(bildungLevel) {
  const baseDauer = 1.0; // 1 Tag Basis
  const maxReduktion = 0.5; // Maximal -50%
  
  let reduktion = bildungLevel / 1000; // Lineare Reduktion
  reduktion = Math.min(reduktion, maxReduktion); // Max. 50%
  
  return baseDauer - reduktion; // Ergebnis: 1.0 bis 0.5 Tage
}

// Beispiel:
// Bildung = 99 → Kinderphase = 1.0 Tag (Standard)
// Bildung = 500 → Kinderphase = 0.5 Tage (-50%)
```

**Dokument:** `docs/player-ui/02_bevoelkerung_alterssystem.md`

---

## ❓ Frage 2: Handelsrouten-Geschwindigkeit

**Gewählter Ansatz:** Fixe Geschwindigkeit + Ausrüstungs-Bonus  
**Regel:** 1 Provinz pro Stunde (Standard) + Ausrüstungsmodifikator

**Implementierung:**
```javascript
function berechneReisezeit(distanz, einheitentyp, ausstattung) {
  const baseGeschwindigkeit = {
    handelskarren: 1,      // 1 Provinz/Stunde Basis
    militaer: 2,           // 2 Provinzen/Stunde Basis (schneller)
    siedler: 1.5           // 1.5 Provinzen/Stunde Basis
  };
  
  const ausstattungModifikator = {
    pferd: 1.5,            // +50% Geschwindigkeit (Handelskarren mit Pferd)
    reitsattel: 1.3,       // +30% Geschwindigkeit (Rekrut mit Reitsattel)
    standard: 1.0          // +0% (Standard)
  };
  
  const baseSpeed = baseGeschwindigkeit[einheitentyp];
  const modifikator = ausstattungModifikator[ausstattung] || 1.0;
  
  const effectiveSpeed = baseSpeed * modifikator;
  return Math.ceil(distanz / effectiveSpeed); // Reisezeit in Stunden (Provinzen!)
}

// Beispiel:
// Distanz = 3 Provinzen, Handelskarren (ohne Ausrüstung) → 3 Stunden
// Distanz = 3 Provinzen, Handelskarren mit Pferd → 2 Stunden (1.5x schneller)
```

**Dokument:** `docs/player-ui/03_handel_karrensystem.md`

---

## ❓ Frage 3: Verlustformel bei Kämpfen

**Gewählter Ansatz:** Exponentielle Formel  
**Formel:** `Kampfkraft = exp(Training / 200) × exp(Fitness / 150)`

**Implementierung:**
```javascript
function berechneKampfkraft(training, fitness) {
  // Exponentielle Formel: exp(Training / 200) × exp(Fitness / 150)
  const trainingFaktor = Math.exp(training / 200); // exp(Training/200)
  const fitnessFaktor = Math.exp(fitness / 150);   // exp(Fitness/150)
  
  const kampfkraft = trainingFaktor * fitnessFaktor; // Multiplikation!
  
  return kampfkraft;
}

// Beispiel:
// Training = 80, Fitness = 90 → exp(0.4) × exp(0.6) = 1.49 × 1.82 = 2.71
// Verluste bei gleicher Stärke: (1.0 - 2.71) × 100 = -171% (massiver Vorteil!)
```

**Dokument:** `docs/player-ui/04_militaer_einheiten.md`

---

## ❓ Frage 4: Tech-Level & Rohstoff-Suche

**Gewählter Ansatz:** Wahrscheinlichkeits-Tabelle + Terraintyp-Modifikator  
**Formel:** `Fundwahrscheinlichkeit = Basis-Wahrscheinlichkeit × Terraintyp-Modifikator`

**Datenbank-Struktur:**
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

**Dokument:** `docs/player-ui/05_forschung_tech_system.md`

---

## ❓ Frage 5: Lager-Kapazität pro Ressource

**Gewählter Ansatz:** Hybrid-Lösung (Mischung aus allen drein)  
**Regel:** Gesamtkapazität = Summe aller Lager-Gebäude + Pro-Ressource-Limit manuell einstellbar

**Implementierung:**
```javascript
function berechneLagerBelegung(province, benutzerLimiten) {
  // 1. Gesamtkapazität = Summe aller Lager-Gebäude (Ansatz 3)
  let gesamtkapazitaet = 0;
  
  for (const gebaeude of province.buildings) {
    if (gebaeude.lagerkapazitaet > 0) {
      gesamtkapazitaet += gebaeude.lagerkapazitaet; // z.B. 500 + 2000 = 2500
    }
  }
  
  // 2. Pro-Ressource-Limit manuell einstellbar (Ansatz 2)
  // benutzerLimiten = { "Kartoffeln": 1500, "Bauholz": null, ... }
  
  let belegung = 0;
  const ressourcenStatus = [];
  
  for (const ressource of province.lager.ressourcen) {
    // Limit bestimmen: Benutzer-Eingabe ODER dynamisch (Ansatz 1)
    let limit = benutzerLimiten[ressource.name]; // z.B. 1500
    
    if (limit === null || limit === undefined) {
      // Kein Limit gesetzt → dynamisch bis zur Gesamtkapazität (Ansatz 1)
      limit = gesamtkapazitaet; // z.B. 2500
    }
    
    // Menge begrenzen (überschüssige Rohstoffe gehen verloren!)
    const effectiveMenge = Math.min(ressource.menge, limit);
    
    belegung += effectiveMenge;
    
    const status = ressource.menge > limit ? 'ueberlimit' : (belegung >= gesamtkapazitaet ? 'voll' : 'ok');
    
    ressourcenStatus.push({
      name: ressource.name,
      menge: ressource.menge, // Original-Menge (vor Limit)
      effectiveMenge: effectiveMenge, // Begrenzte Menge (nach Limit)
      limit: limit, // Benutzer-Limit oder dynamisch
      status: status,
      verloren: ressource.menge - effectiveMenge // Verlorene Menge!
    });
  }
  
  const belegungProzent = (belegung / gesamtkapazitaet) * 100;
  
  return {
    gesamt: belegung, // Summe aller begrenzten Ressourcen
    kapazitaet: gesamtkapazitaet, // Summe aller Lager-Gebäude
    belegungProzent: belegungProzent,
    voll: belegung >= gesamtkapazitaet,
    ressourcenStatus: ressourcenStatus // Detail-Informationen pro Ressource
  };
}

// Beispiel:
// Bunker (500) + Vorratskammer (2000) = 2500 Gesamtkapazität
// Kartoffeln: 3000 (Limit = 1500) → ❌ ÜBERLIMIT (1500 verloren!)
// Bauholz: 2000 (Limit = null → dynamisch) → ✅ OK (Summe = 3500 < 2500? NEIN!)
```

**Dokument:** `docs/player-ui/06_ressourcen_lager.md`

---

## ❓ Frage 6: Karten-Größe & Sichtweite

**Gewählter Ansatz:** Prozedural generierte Karte + Admin-Editor  
**Regel:** Welt wird im Admin-Menü erzeugt, dann für Spieler statisch (Multiplayer-Browserspiel)

**Datenbank-Struktur:**
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

**Dokument:** `docs/player-ui/07_weltkarte_navigation.md`

---

## ❓ Frage 7: Armee-Geschwindigkeit

**Gewählter Ansatz:** Einheitentyp-basiert (zwischen Provinzen)  
**Regel:** 1 Provinz pro Stunde (Standard) + Einheitentyp-Modifikator

**Datenbank-Struktur:**
```sql
CREATE TABLE einheiten_typen (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,              -- z.B. "Rekrut", "Kavallerie"
  kategorie TEXT NOT NULL,         -- "Infanterie", "Kavallerie"
  beschreibung TEXT NOT NULL,      -- JSON: {"basis_speed": 1.0, "ausstattung": ["pferd"]}
  
  -- Geschwindigkeit zwischen Provinzen (neu!)
  geschwindigkeit_pro_stunde REAL DEFAULT 1.0, -- Standard: 1 Provinz/Stunde
  
  -- Beispiel:
  {"basis_speed": 1.0, "ausstattung": ["pferd"]} → 1 Provinz/Stunde
  {"basis_speed": 3.0, "ausstattung": ["pferd", "reitsattel"]} → 3 Provinzen/Stunde!
);

-- Beispiel-Daten:
INSERT INTO einheiten_typen VALUES (1, 'Rekrut', 'Infanterie', '{"basis_speed": 1.0}', 1.0);
INSERT INTO einheiten_typen VALUES (2, 'Kavallerie', 'Kavallerie', '{"basis_speed": 3.0}', 3.0);
INSERT INTO einheiten_typen VALUES (3, 'Siedler', 'Siedler', '{"basis_speed": 1.5}', 1.5);
```

**Implementierung:**
```javascript
function berechneReisezeit(distanz, einheitentyp) {
  // Distanz = Anzahl der Provinzen zwischen Start und Ziel (nicht Grid-Felder!)
  
  const baseGeschwindigkeit = {
    rekrut: 1,      // 1 Provinz/Stunde Basis (Standard)
    bogenschuetze: 1,   // 1 Provinz/Stunde Basis (Standard)
    axtkampf: 0.8,   // 0.8 Provinzen/Stunde (-20%)
    kavallerie: 3,   // 3 Provinzen/Stunde (+200%!)
    siedler: 1.5   // 1.5 Provinzen/Stunde (+50%)
  };
  
  const speed = baseGeschwindigkeit[einheitentyp];
  return Math.ceil(distanz / speed); // Reisezeit in Stunden (Provinzen!)
}

// Beispiel:
// Distanz = 3 Provinzen, Rekrut → 3 Stunden (1 Provinz/Stunde)
// Distanz = 3 Provinzen, Kavallerie → 1 Stunde (3 Provinzen/Stunde!)
// Distanz = 5 Provinzen, Siedler → 3.3 Stunden (1.5 Provinzen/Stunde)
```

**Dokument:** `docs/player-ui/04_militaer_einheiten.md`

---

## ❓ Frage 8: Power-Balance bei Provinz-Transfer

**Gewählter Ansatz:** Multi-Kriterien-Check + Admin-Approval (kombiniert)  
**Regel:** Automatisierte Checks (MIPS, Tech, Bevölkerung, Provinzen) + Admin-Genehmigung bei starkem Ungleichgewicht

**Implementierung:**
```javascript
function canProvinceTransfer(sender, receiver, province) {
  // Automatischer Check (Multi-Kriterien-Check wie Ansatz 2)
  const autoCheck = {
    // 1. MIPS: Sender ≤ Empfänger × 2
    mips: sender.mips <= receiver.mips * 2,
    
    // 2. Tech-Level: Sender ≤ Empfänger × 2
    tech: sender.tech_level <= receiver.tech_level * 2,
    
    // 3. Bevölkerung: Sender ≤ Empfänger × 2
    population: sender.population <= receiver.population * 2,
    
    // 4. Provinzen-Anzahl: Sender ≤ Empfänger + 2 (nicht ×, sondern +)
    provinces: sender.provinzen_count <= receiver.provinzen_count + 2,
    
    // 5. Allianz: Beide Spieler müssen verbündet sein (wenn nicht, blockiert)
    alliance: areAllies(sender, receiver),
    
    // 6. Gleiche Insel (wenn nicht, blockiert)
    sameIsland: sender.island === receiver.island
  };
  
  // Wenn alle Checks erfüllt → automatisch genehmigt!
  if (Object.values(autoCheck).every(Boolean)) {
    return { allowed: true, requiresAdminApproval: false };
  }
  
  // Wenn nicht alle Checks erfüllt → Admin-Approval nötig! (Ansatz 3)
  const ratio = sender.mips / receiver.mips; // z.B. 3.3×
  
  if (ratio > 5) {
    // Sehr starkes Ungleichgewicht → Admin muss genehmigen!
    return { 
      allowed: false, 
      requiresAdminApproval: true,
      reason: `Sehr starkes Ungleichgewicht (${ratio.toFixed(1)}×). Admin muss Transfer genehmigen!`
    };
  } else {
    // Moderates Ungleichgewicht → Admin kann genehmigen (optional)
    return { 
      allowed: false, 
      requiresAdminApproval: true,
      reason: `Ungleichgewicht (${ratio.toFixed(1)}×). Admin kann Transfer genehmigen.`
    };
  }
}

function getTransferReason(checks) {
  const failedChecks = Object.entries(checks).filter(([key, value]) => !value);
  
  if (failedChecks.length === 0) {
    return 'Alle Checks erfüllt!';
  }
  
  const reasons = [];
  for (const [key, value] of failedChecks) {
    if (key === 'mips') {
      reasons.push(`MIPS: Sender hat ${sender.mips} MIPS, Empfänger nur ${receiver.mips} (max. 2×)`);
    } else if (key === 'tech') {
      reasons.push(`Tech-Level: Sender hat ${sender.tech_level}, Empfänger nur ${receiver.tech_level} (max. 2×)`);
    } else if (key === 'population') {
      reasons.push(`Bevölkerung: Sender hat ${sender.population}, Empfänger nur ${receiver.population} (max. 2×)`);
    } else if (key === 'provinces') {
      reasons.push(`Provinzen: Sender hat ${sender.provinzen_count}, Empfänger nur ${receiver.provinzen_count} (max. +2)`);
    } else if (key === 'alliance') {
      reasons.push('Nicht verbündet!');
    } else if (key === 'sameIsland') {
      reasons.push('Nicht auf derselben Insel!');
    }
  }
  
  return reasons.join(', ');
}

// Beispiel:
// Sender = { mips: 100,000, tech_level: 1,500, population: 800, provinzen_count: 5 }
// Empfänger = { mips: 60,000, tech_level: 800, population: 500, provinzen_count: 4 }
// Status: ✅ OK (alle Checks erfüllt!)

// Sender = { mips: 100,000 }, Empfänger = { mips: 30,000 } → Ratio = 3.3×
// Status: ⚠️ Admin-Approval nötig (aber nicht blockiert!)

// Sender = { mips: 100,000 }, Empfänger = { mips: 20,000 } → Ratio = 5×
// Status: ❌ Blockiert (sehr starkes Ungleichgewicht!)
```

**Dokument:** `docs/player-ui/09_verwaltung_spezialfunktionen.md`

---

## ✅ Nächste Schritte: Dokument-Updates

Jetzt aktualisiere ich alle 9 Player UI Dokumente mit den gewählten Lösungen:

1. **01_grid_provinz_struktur.md** - Keine Änderungen nötig (bereits abgeschlossen)
2. **02_bevoelkerung_alterssystem.md** - Lineare Skalierung einfügen
3. **03_handel_karrensystem.md** - Fixe Geschwindigkeit + Ausrüstung einfügen
4. **04_militaer_einheiten.md** - Exponentielle Formel + Einheitentyp-basiert einfügen
5. **05_forschung_tech_system.md** - Wahrscheinlichkeits-Tabelle + Terraintyp einfügen
6. **06_ressourcen_lager.md** - Hybrid-Lösung einfügen
7. **07_weltkarte_navigation.md** - Prozedural generierte Karte + Admin-Editor einfügen
8. **08_pieler_infos_einstellungen.md** - Keine Änderungen nötig (bereits abgeschlossen)
9. **09_verwaltung_spezialfunktionen.md** - Multi-Kriterien-Check + Admin-Approval einfügen

Soll ich jetzt mit den Dokument-Updates beginnen? 🚀

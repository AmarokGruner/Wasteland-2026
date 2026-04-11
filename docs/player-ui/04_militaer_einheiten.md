# 📄 Abschnitt 4: Militär & Einheiten

## 4.0 Überblick

Das Militärsystem umfasst die Rekrutierung, Ausbildung, Bewegung und den Kampf von Einheiten. Spieler können Armeen aufstellen, die in Provinzen stationiert oder zu anderen Provinzen geschickt werden können.

---

## 4.1 Armee-Struktur & Einheiten

### 4.1.1 Einheiten-Typen

| Kategorie | Beispiele | Funktionen | Besonderheiten |
|-----------|-----|------------|----------------|
| **Infanterie** | Rekrut, Bogenschütze, Axtkämpfer | Boden-Truppen, Stadt-Schutz | Rekrutierung aus Bevölkerung |
| **Siedler** | Siedler, berittene Siedler | Provinzerstellung | Besondere Einheit |
| **Handelskarren** | Handelskarren | Waren-Transport | Kann zu Einheit werden |
| **See-Einheiten** | Segelboot, Schiff | Küsten-Handel, Seehandel | Benötigen Hafen/Anlegestelle |

**Einheitendatenbank (einheiten_typen):**
```javascript
{
  "id": 1,
  "name": "Rekrut(en)",
  "kategorie": "Infanterie",
  "kosten_mips": 0,
  "kosten_muenzen": 0,
  "beschreibung": "{\"mips\": 50, \"material\": {\"eisen\": 10}}"
}
```

**Wichtig:** Der Bedarf steht in `beschreibung` als JSON, nicht in separaten Feldern!

### 4.1.2 Rekrutierungskosten

```javascript
// Rekrutierungs-Formel (aus DB beschreibung)
function calculateRekrutierungskosten(einheitenTyp) {
  const bedarf = JSON.parse(einheitenTyp.beschreibung);
  
  return {
    mips: bedarf.mips || 0,
    material: bedarf.material || {},  // { "eisen": 10, "holz": 5 }
    arbeitspunkte: bedarf.ap || 0
  };
}

// Beispiel: Rekrut
// MIPS: 50
// Material: 10 Eisen
// AP: 100
```

### 4.1.3 Rekrutierungs-Logik

```javascript
// Einheiten ausbilden (benötigt Ausbildungscamp/Kaserne)
function rekrutiereEinheiten(province, einheitenTyp, anzahl) {
  // 1. Gebäude prüfen
  if (!province.hasAusbildungscamp) {
    throw new Error('Ausbildungscamp oder Kaserne benötigt!');
  }
  
  // 2. Ressourcen prüfen
  const kosten = calculateRekrutierungskosten(einheitenTyp);
  if (!hasResources(province, kosten)) {
    throw new Error('Nicht genug Ressourcen!');
  }
  
  // 3. Bevölkerung prüfen (nur Erwachsene)
  if (province.population.erwachsene < anzahl) {
    throw new Error('Nicht genug Erwachsene!');
  }
  
  // 4. Einheiten-Request erstellen
  const rekrutierung = {
    id: generateId(),
    province: province.id,
    einheitenTyp: einheitenTyp.id,
    anzahl: anzahl,
    status: 'training',
    fertigBei: new Date(Date.now() + 24 * 60 * 60 * 1000)  // 1 Tag
  };
  
  // 5. Ressourcen abziehen
  consumeResources(province, kosten);
  
  // 6. Bevölkerung vorübergehend "buchstabieren"
  province.population.erwachsene -= anzahl;
  province.population.inTraining += anzahl;
  
  // 7. Speichern
  saveRekrutierung(rekrutierung);
  
  return rekrutierung;
}
```

---

## 4.2 Armee-Management

### 4.2.1 Stationierte Armeen

```javascript
// Armeen in Provinz
function getStationedArmies(provinceId) {
  return database.armies.where({
    province_id: provinceId,
    status: 'stationed'
  });
}

// Armee-Daten
{
  "id": 42,
  "owner_id": 15,
  "province_id": 88,
  "units_json": '[{"id": 1, "anzahl": 50}, {"id": 5, "anzahl": 20}]',
  "status": "stationed",
  "target_province_id": null
}
```

### 4.2.2 Armeen bewegen

```javascript
// Armee zu Ziel-Province bewegen
function moveArmee(armee, targetProvince) {
  // 1. Status prüfen
  if (armee.status !== 'stationed') {
    throw new Error('Armee ist nicht stationiert!');
  }
  
  // 2. Ziel prüfen
  if (!targetProvince) {
    throw new Error('Ziel-Province muss definiert sein!');
  }
  
  // 3. Bewegung berechnen
  const distance = calculateDistance(armee.province_id, targetProvince.id);
  const speed = calculateSpeed(armee.units);
  const travelTicks = distance / speed;
  
  // 4. Armee updaten
  armee.status = 'marching';
  armee.target_province_id = targetProvince.id;
  armee.travel_ticks_remaining = travelTicks;
  armee.departureTime = new Date();
  
  // 5. Speichern
  saveArmee(armee);
  
  logEvent('Armee bewegt', `Armee ${armee.id} bewegt sich nach ${targetProvince.name}`);
  
  return armee;
}
```

### 4.2.3 Bewegung in Echtzeit

```javascript
// Armeen bewegen (pro Tick)
function updateArmies() {
  const armies = database.armies.where("status = 'marching'");
  
  for (const armee of armies) {
    armee.travel_ticks_remaining--;
    
    if (armee.travel_ticks_remaining <= 0) {
      // Armee erreicht!
      armee.status = 'stationed';
      armee.province_id = armee.target_province_id;
      armee.target_province_id = null;
      
      logEvent('Armee angekommen', `Armee ${armee.id} erreicht Provinz ${armee.province_id}`);
      
      // Check für Kampf (wenn feindliche Armee da)
      checkCombat(armee);
    }
  }
  
  saveArmies(armies);
}
```

---

## 4.3 Kampf-System

### 4.3.1 Automatische Kämpfe

```javascript
// Kampf-Check bei Ankunft
function checkCombat(arrivingArmee) {
  // Andere Armeen in Ziel-Province suchen
  const otherArmies = getStationedArmies(arrivingArmee.target_province_id);
  
  // Feindliche Armeen finden
  const enemies = otherArmies.filter(other => {
    const relation = getDiplomatieRelation(
      arrivingArmee.owner_id, 
      other.owner_id
    );
    return relation === 'enemy' || relation === 'unwanted';
  });
  
  if (enemies.length > 0) {
    // Automatisch angreifen!
    initiateCombat(arrivingArmee, enemies[0]);
  }
}
```

### 4.3.2 Kampf-Logik

```javascript
// Kampfsimulation (on-demand)
function initiateCombat(attacker, defender) {
  // 1. Einheiten analysieren
  const attackerUnits = JSON.parse(attacker.units_json);
  const defenderUnits = JSON.parse(defender.units_json);
  
  // 2. Stärke berechnen
  const attackerStrength = calculateTotalStrength(attackerUnits);
  const defenderStrength = calculateTotalStrength(defenderUnits);
  
  // Bunker-Bonus für Verteidiger
  const defenderProvince = getProvince(defender.province_id);
  const bunkerBonus = defenderProvince.hasBunker ? 1.3 : 1.0;
  
  const effectiveDefenderStrength = defenderStrength * bunkerBonus;
  
  // 3. Ergebnis berechnen
  const attackerLoss = calculateLoss(effektiveDefenderStrength);
  const defenderLoss = calculateLoss(attackerStrength);
  
  // 4. Verluste anwenden
  applyLosses(attacker, attackerLoss);
  applyLosses(defender, defenderLoss);
  
  // 5. Ergebnis protokollieren
  const winner = defenderLoss > attackerLoss ? defender : attacker;
  const loser = winner === defender ? attacker : defender;
  
  logCombat({
    attacker,
    defender,
    winner,
    loser,
    attackerLoss,
    defenderLoss,
    timestamp: new Date()
  });
  
  // 6. Gefangener erstellen (wenn Bewohner-Province getroffen)
  if (defender.province_id === defender.owner_proVINZ_id) {
    createGefangener(defender.owner_id, defender.province_id);
  }
}
```

### 4.3.3 Trainings & Fitness

```javascript
// Einheitenausbildung (wenn keine neuen Einheiten)
function trainArmies(armee) {
  const units = JSON.parse(armee.units_json);
  
  for (const unit of units) {
    // Training + Fitness erhöhen
    if (unit.training < 100) {
      unit.training += Math.random() * 5;  // 0-5 pro Tag
    }
    
    if (unit.fitness < 100) {
      unit.fitness += Math.random() * 3;  // 0-3 pro Tag
    }
  }
  
  // Maximal auf 100 begrenzen
  units.forEach(unit => {
    unit.training = Math.min(100, unit.training);
    unit.fitness = Math.min(100, unit.fitness);
  });
  
  armee.units_json = JSON.stringify(units);
  saveArmee(armee);
}

// Kampfkraft-Berechnung
function calculateTotalStrength(units) {
  return units.reduce((total, unit) => {
    // Training & Fitness beeinflussen Stärke
    const factor = (unit.training / 100) * 0.5 + 
                   (unit.fitness / 100) * 0.5;
    
    total += unit.anzahl * factor;
    return total;
  }, 0);
}
```

---

## 4.4 Bunker-System

### 4.4.1 Bunker-Bonus

```javascript
// Bunker-Bonus-Berechnung
function calculateBunkerBonus(province, totalBesetzung) {
  // Bunker fasst max 100 Personen
  const bunkerCapacity = 100;
  
  if (totalBesetzung <= bunkerCapacity) {
    // Volle 80% Bonus
    return 0.8;
  } else {
    // Reduzierter Bonus
    const effective = (bunkerCapacity / totalBesetzung) * 0.8;
    return effective;
  }
}

// Beispiel:
// Bevölkerung: 200, Armee: 50 = Total 250
// BunkerBonus = (100 / 250) * 0.8 = 0.32 (32% Bonus)
```

### 4.4.2 Bunker-Positionierung

```javascript
// Bunker in neuer Provinz platzieren
function placeBunker(province) {
  // 1. Zufälliges Landfeld auswählen (5-10 Felder vom Zentrum)
  const center = { x: 7, y: 7 };  // 15x15 Grid Mitte
  const radius = 5 + Math.random() * 5;  // 5-10 Felder
  
  let position;
  do {
    const angle = Math.random() * 2 * Math.PI;
    const x = center.x + Math.round(radius * Math.cos(angle));
    const y = center.y + Math.round(radius * Math.sin(angle));
    position = { x, y };
  } while (!isValidBuildingPosition(province, position));
  
  // 2. Bunker bauen
  const bunker = {
    type: 'bunker',
    x: position.x,
    y: position.y,
    hasBunker: true,
    isStartProvince: true,
    lager: {  // Startmaterialien
      holz: 50,
      stein: 25
    }
  };
  
  province.buildings.push(bunker);
  province.hasBunker = true;
  province.isBunkerProvince = true;
  
  // 3. Wegenetz um Bunker erstellen
  createRoadNetworkAroundBunker(province, position);
  
  return bunker;
}
```

---

## 4.5 UI-Implementierung

### 4.5.1 Militär-Widget

```javascript
// Militär-Übersicht
{
  "armeen": [
    {
      "id": 42,
      "name": "1. Garde",
      "einheiten": [
        { "typ": "Rekrut", "anzahl": 50, "training": 85, "fitness": 90 },
        { "typ": "Bogenschütze", "anzahl": 20, "training": 30, "fitness": 50 }
      ],
      "status": "stationed",
      "province": "Siedlung Alpha",
      "gesamtstaerke": 67.5
    },
    {
      "id": 43,
      "name": "2. Expedition",
      "status": "marching",
      "ziel": "Provinz Delta",
      "ankunft": "3h 45m",
      "gesamtstaerke": 45.2
    }
  ],
  "rekrutierung": {
    "available": true,
    "campCapacity": 10,
    "activeTraining": 3,
    "canRekrutieren": 7
  },
  "bunker": {
    "hasBunker": true,
    "kapazitaet": 100,
    "aktuell": 200,
    "bonus": "32%"
  }
}
```

### 4.5.2 Rekrutierung-Modal

```javascript
// Modal: Einheiten ausbilden
<Modal title="Einheiten ausbilden">
  <Select 
    label="Einheitentyp" 
    options={einheitenTypen.filter(t => canRekrutieren(t))}
  />
  
  <NumberInput 
    label="Anzahl" 
    min={1} 
    max={maxRekrutierbar}
  />
  
  <InfoBox>
    Kosten: {kosten.mips} MIPS, {kosten.material.holz} Holz, 
    {kosten.material.eisen} Eisen
  </InfoBox>
  
  <Button onClick={startRekrutierung}>
    {anzahl}x {ausgewaehlterEinheit} ausbilden
  </Button>
</Modal>
```

### 4.5.3 Armee-Bewegung

```javascript
// Armee bewegen (Klick auf Karte)
function onProvinceClick(province) {
  if (selectedArmee) {
    // Armee zu dieser Provinz bewegen
    moveArmee(selectedArmee, province);
  }
}

// Armee auswählen
function selectArmee(armee) {
  selectedArmee = armee;
  showArmyMenu(armee);
}
```

---

## 4.6 Datenbank-Strukturen

### 4.6.1 Militärtabellen

| Tabelle | Zweck | Wichtige Felder |
|---------|-----|-----------------|
| `einheiten_typen` | Einheitendefinitionen | `name`, `kategorie`, `beschreibung` (JSON) |
| `armeen` | Armeen | `owner_id`, `province_id`, `units_json`, `status` |
| `provinz_einheiten` | Stationierte Einheiten | `province_id`, `einheiten_typ_id`, `anzahl` |
| `combat_logs` | Kampf-Protokolle | `attacker_id`, `defender_id`, `winner_id`, `losses` |

### 4.6.2 Armeen Tabelle

```sql
-- armies
-- Speichert aktive Armeen

INSERT INTO armies VALUES (?, ?, ?, ?, ?, ?, ?, ?);
-- ID=1, Owner=42, Province=88, units_json='[{"id":1,"anzahl":50}]',
--   Status='stationed', Target=NULL, TravelTicks=0

-- Bewegung:
-- status = 'marching'
-- target_province_id = 99
-- travel_ticks_remaining = 15

-- Ankunft:
-- status = 'stationed'
-- province_id = 99
-- travel_ticks_remaining = 0
```

---

## 4.7 Zusammenfassung & Checkliste

### 4.7.1 To-Do für Implementierung

- [ ] **Einheiten-Typen** aus DB lesen (beschreibung als JSON parsen)
- [ ] **Rekrutierung** mit Ressourcen-Check
- [ ] **Ausbildungsgebäude** (Camp/Kaserne) benötigen
- [ ] **Armeen bewegen** mit Reisezeit-Berechnung
- [ ] **Automatische Kämpfe** bei feindlicher Begegnung
- [ ] **Training & Fitness** pro Tag erhöhen
- [ ] **Bunker-Bonus** berechnen (80% max)
- [ ] **Gefangene** bei Provinzeroberung erstellen
- [ ] **Militär-Widget** im Spiel
- [ ] **Rekrutierung-Modal** (Einheit & Anzahl)

### 4.7.2 Offene Fragen (für später)

- [ ] Rekrutierungskosten: Exakte Formel aus DB beschreibung JSON?
- [ ] Reisezeit: Wie viele Tage pro Feld? Abhängig von Wegenetz?
- [ ] Verlustformel: Wie wirken sich Training & Fitness aus?
- [ ] Besonderheiten: Gibt es Spezial‑Einheiten?

---

**Abschnitt 4 abgeschlossen ✅**

*Dokument erstellt: 2026-04-05*  
*Stand: Basierend auf FAQ-Analysen*

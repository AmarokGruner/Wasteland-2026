# 📄 Abschnitt 9: Verwaltungs- & Spezial-Funktionen

## 9.0 Überblick

Dieser Abschnitt behandelt fortgeschrittene Funktionen, die Admin-Interaktion erfordern oder besondere Spielmechaniken umfassen: Provinzübergabe, Account-Reset, Gefangene, Diplomatie, Steuer-Transfer und andere Spezialfunktionen.

---

## 9.1 Provinzübergabe

### 9.1.1 Regeln & Bedingungen

```javascript
function canProvinceTransfer(spieler, empfänger, province) {
  const checks = {
    // 1. Beide Spieler müssen verbündet sein
    alliance: areAllies(spieler, empfänger),
    
    // 2. Beide Spieler müssen auf derselben Insel sein
    sameIsland: spieler.island === empfänger.island,
    
    // 3. Spielstärke-Check (kein Powergaming)
    powerBalance: checkPowerBalance(spieler, empfänger, province),
    
    // 4. Keine Vermeidung von Entwicklungsstaat-Mechanik
    noDevStateAbuse: checkDevStateAbuse(empfänger, province),
    
    // 5. Keine Gebäude-Freischaltung für andere Spieler
    noTechAbuse: checkTechAbuse(spieler, empfänger, province)
  };
  
  if (!Object.values(checks).every(Boolean)) {
    return {
      allowed: false,
      reason: getTransferReason(checks)
    };
  }
  
  return { allowed: true };
}
```

### 9.1.2 Transfer-Modal

```javascript
<ProvinceTransferModal province={selectedProvince}>
  <Info>
    <Warning>
      ⚠️ Nur zulässig wenn:
      - Beide Spieler verbündet sind
      - Auf derselben Insel
      - Keine Spielmechanik-Überwindung
    </Warning>
    
    <PlayerSelect
      label="Empfänger wählen"
      options={allianzPartner}
    />
  </Info>
  
  <Footer>
    <Button onClick={cancel}>Abbrechen</Button>
    <Button primary onClick={transfer}>Provinz übergeben</Button>
  </Footer>
</ProvinceTransferModal>
```

---

## 9.2 Konto-Management

### 9.2.1 Steuer-Transfer

```javascript
function transferMIPS(province, amount, targetProvince) {
  // 1. Prüfe ob Bank existiert (für direkte Transfers)
  if (!province.hasBank) {
    // Transfer läuft über Staatskonto
    province.provinzkonto -= amount;
    player.staatskonto += amount;
    
    // Vom Staatskonto zur Ziel-Province
    player.staatskonto -= amount;
    targetProvince.provinzkonto += amount;
  } else {
    // Direkter Transfer möglich
    province.provinzkonto -= amount;
    targetProvince.provinzkonto += amount;
  }
  
  logEvent('Geldtransfer', `${amount} MIPS von ${province.name} nach ${targetProvince.name}`);
}
```

### 9.2.2 Steuer-Setzen

```javascript
function setSteuerSatz(province, satz) {
  // Satz: 0-100%
  if (satz < 0 || satz > 100) {
    throw new Error('Stuersatz muss zwischen 0-100% liegen');
  }
  
  province.steuersatz = satz;
  
  // Automatische Abgabe an Staatskonto (wenn Steueramt gebaut)
  if (province.hasSteueramt) {
    const tagesEinnahmen = province.steuer.tagesEinnahmen;
    const anStaats = tagesEinnahmen * (satz / 100);
    
    province.provinzkonto -= anStaats;
    player.staatskonto += anStaats;
  }
}
```

---

## 9.3 Gefangene-Management

### 9.3.1 Gefangener erstellen

```javascript
function createGefangener(verteidigerId, provinceId) {
  const v = getPlayer(verteidigerId);
  const p = getProvince(provinceId);
  
  const gefangener = {
    id: generateId(),
    gefangener_id: v.id,
    gefangener_in: provinceId,
    gefangen_since: new Date(),
    options: ['verwalter', 'freilassen', 'exil', 'exekutieren']
  };
  
  // Moral-Effekt
  v.provinzen.forEach(p => {
    p.moral -= 10;  // -10 Moral für jeden Gefangenen
  });
  
  // Konto gesperrt
  v.steuer_gesperrt = true;
  
  saveGefaangener(gefangener)
  logEvent('Gefangener', `${v.name} wurde in ${p.name} gefangen genommen`);
  
  return gefangener;
}
```

### 9.3.2 Gefangener-Optionen

```javascript
<GefangenerModal gefangener={gefangener}>
  <Info>
    <Spieler>{gefangener spieler.name}</Spieler>
    <Ort>{getProvince(gefangener.province_id).name}</Ort>
    <Seit>{formatTime(gefangener.gefangen_since)}</Seit>
    
    <MoralEffekt>
      {gefangener spieler.provinzen.length} Provinzen betroffen (-10 Moral)
    </MoralEffekt>
  </Info>
  
  <Options>
    <Option onClick={() => makeVerwalter(gefangener)}>
      <Icon>👑</Icon>
      <Label>Zu Verwalter ernennen</Label>
      <Description>Provinz wird an Spieler übergeben</Description>
    </Option>
    
    <Option onClick={() => freilassen(gefangener)}>
      <Icon>🕊️</Icon>
      <Label>Freilassen</Label>
      <Description>Spieler kann sich abholen (Freikaufsumme)</Description>
    </Option>
    
    <Option onClick={() => exil(gefangener)}>
      <Icon>🌍</Icon>
      <Label>Ins Exil verbannen</Label>
      <Description>Spieler wird rausgeschickt</Description>
    </Option>
    
    <Option onClick={() => exekutieren(gefangener)}>
      <Icon>☠️</Icon>
      <Label>Exekutieren</Label>
      <Description>Spieler muss neu starten (nur wenn keine Provinzen)</Description>
    </Option>
  </Options>
</GefangenerModal>
```

---

## 9.4 Diplomatie

### 9.4.1 Diplomatie-Status

```javascript
const diplomatieStatus = {
  NEUTRAL: 'neutral',      // Standard
  FRIEND: 'friend',        // Freunde
  ALLY: 'ally',            // Verbündet
  ENEMY: 'enemy',          // Krieg
  UNWANTED: 'unwanted'     // Unerwünscht
};

function setDiplomatie(player1Id, player2Id, status) {
  const relation = {
    player1_id: player1Id,
    player2_id: player2Id,
    status: status,
    changed_at: new Date()
  };
  
  saveDiplomatie(relation);
  
  // Effekte anwenden
  if (status === ENEMY) {
    // Automatische Kämpfe bei Begegnung
    logEvent('Diplomatie', `${player1.name} erklärt ${player2.name} den Krieg`);
  }
}
```

### 9.4.2 Diplomatie-Widget

```javascript
<DiplomatieWidget>
  <Header>
    <Title>Diplomatie</Title>
    <SearchPlayerInput onChange={searchSpieler} />
  </Header>
  
  <Tabs>
    <Tab label="Verbündete" count={allyCount}>
      <DiplomatieList
        players={allyPlayers}
        status="ally"
        onAction={setDiplomatie}
      />
    </Tab>
    
    <Tab label="Freunde" count={friendCount}>
      <DiplomatieList
        players={friendPlayers}
        status="friend"
        onAction={setDiplomatie}
      />
    </Tab>
    
    <Tab label="Feinde" count={enemyCount}>
      <DiplomatieList
        players={enemyPlayers}
        status="enemy"
        onAction={setDiplomatie}
      />
    </Tab>
    
    <Tab label="Neutral" count={neutralCount}>
      <DiplomatieList
        players={neutralPlayers}
        status="neutral"
        onAction={setDiplomatie}
      />
    </Tab>
  </Tabs>
</DiplomatieWidget>
```

---

## 9.5 Account-Reset

### 9.5.1 Reset-Logik

```javascript
function resetAccount(player, reason) {
  if (!player.canReset()) {
    throw new Error('Reset nur einmal pro 24 Stunden möglich');
  }
  
  // 1. Alle provinzen löschen
  const provinzen = player.provinzen;
  provinzen.forEach(p => deleteProvince(p.id));
  
  // 2. Alle Armeen löschen
  player.armeen.forEach(a => deleteArmee(a.id));
  
  // 3. Tech-Level zurücksetzen
  player.tech_level = 0;
  
  // 4. MIPS zurücksetzen (auf Basiswert)
  player.staatskonto = 1000;
  
  // 5. Zeitguthaben zurücksetzen (Start-Wert)
  player.time_credit = START_TIME_CREDIT;
  
  // 6. Log
  logEvent('Account Reset', `${player.name} hat das Spiel neu gestartet (${reason})`);
  
  // 7. Reset-Zeit setzen
  player.last_reset = new Date();
  
  savePlayer(player);
}
```

### 9.5.2 Reset-Bestätigung

```javascript
<ConfirmModal>
  <Title>Account resetten</Title>
  <Warning>
    ⚠️ Dies wird ALLES löschen:
    - Alle Provinzen
    - Alle Armeen
    - Tech-Level zurücksetzen
    - Alle Gegenstände & Ressourcen
    
    Du kannst dies nur einmal pro 24 Stunden machen!
  </Warning>
  
  <ReasonInput label="Grund für Reset" required />
  
  <Footer>
    <Button onClick={cancel}>Abbrechen</Button>
    <Button danger onClick={reset}>Account resetten</Button>
  </Footer>
</ConfirmModal>
```

---

## 9.6 Sonstige Spezialfunktionen

### 9.6.1 Bodenschätze suchen

```javascript
function searchBodenschaeuze(province, rohtyp) {
  // 1. Prüfe ob Tech-Level ausreichend
  const requiredTech = getRequiredTechForRohstoff(robstoffTyp);
  if (player.tech_level < requiredTech) {
    throw new Error(`Benötigt Tech-Level ${requiredTech}`);
  }
  
  // 2. Kosten berechnen
  const kosten = rohtyp.suchkosten;
  if (province.provinzkonto < kosten) {
    throw new Error('Nicht genug MIPS');
  }
  
  // 3. Suche durchführen (zufällig)
  const gefunden = Math.random() < rohtyp.findungswahrscheinlichkeit;
  
  if (gefunden) {
    // Rohstoff freischalten
    province.rohstoffe.push(rohstoffTyp);
    
    logEvent('Bodenschatz', `${rohtyp.name} in ${province.name} gefunden!`);
  } else {
    logEvent('Bodenschatz', `Keine Vorkommen von ${rohstoffTyp.name} in ${province.name}`);
    province.trotz_suche.add(rohstoffTyp);  // Nicht mehr suchbar
  }
  
  // Kosten abziehen
  province.provinzkonto -= kosten;
  
  return gefunden;
}
```

### 9.6.2 Schnellbaumodus

```javascript
function activateSchnellbaumodus(buildingType) {
  player.schnellbaumodus = {
    active: true,
    building: buildingType,
    count: 0
  };
  
  logEvent('Schnellbaumodus', `${buildingType.name} schneller bauen aktiviert`);
}

function onFieldClick(position) {
  if (!player.schnellbaumodus.active) return;
  
  const building = player.schnellbaumodus.building;
  
  // Baue Gebäude an dieser Position
  buildBuilding(province, building, position);
  player.schnellbaumodus.count++;
  
  // Modus automatisch beenden nach X Bauten
  if (player.schnellbaumodus.count >= 10) {
    deactivateSchnellbaumodus();
  }
}
```

---

## 9.7 Datenbank-Strukturen

| Tabelle | Zweck | Wichtige Felder |
|---------|-----|--------------|--|
| `diplomatie` | Beziehungen | `player1_id`, `player2_id`, `status` |
| `gefangene` | Gefangene | `gefangener_id`, `province_id`, `options` |
| `provinz_transfers` | Transfer-Historie | `from_player_id`, `to_player_id`, `province_id` |
| `admin_logs` | Admin-Aktivitäten | `admin_id`, `action`, `details` |

---

## 9.8 Zusammenfassung & Checkliste

### 9.8.1 To-Do

- [ ] Provinz-Transfer mit allen Checks (Allianz, Insel, Power-Balance)
- [ ] Geld-Transfer via Staatskonto (mit Bank-Bonus)
- [ ] Steuersatz konfigurieren (0-100%)
- [ ] Gefangene-System mit 4 Optionen
- [ ] Diplomatie-Interface (Freunde/Feinde/Alliierte)
- [ ] Account-Reset mit 24h Cooldown
- [ ] Bodenschätze suchen (mit Tech-Check)
- [ ] Schnellbaumodus für effizientes Bauen
- [ ] Verwaltung von Spieler-Einstellungen
- [ ] Admin-Logs für alle kritischen Aktionen

### 9.8.2 Offene Fragen

1. **Power-Balance**: Wie genau wird "übervorteilt" berechnet?  
   → **Gewählter Ansatz:** Multi-Kriterien-Check + Admin-Approval (kombiniert)

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

**UI:** Transfer-Modal zeigt automatisch Check-Ergebnis + Admin-Genehmigungsoption.

2. **Routen bei Gefangenschaft**: Was passiert mit laufenden Handelsrouten?  
   → **Automatisch abgebrochen** (Ressourcen gehen verloren, außer sie sind bereits im Ziel).

3. **Freikaufsumme**: Wie wird sie berechnet (fest oder verhandelbar)?  
   → **Fest** = 10% des Sender-MIPS (min. 500 MIPS).

---

## 9.9 Zusammenfassung & Checkliste (Aktualisiert)

### 9.9.1 To-Do

- [ ] Provinz-Transfer mit allen Checks (Allianz, Insel, Power-Balance)
- [ ] Geld-Transfer via Staatskonto (mit Bank-Bonus)
- [ ] Steuersatz konfigurieren (0-100%)
- [ ] Gefangene-System mit 4 Optionen
- [ ] Diplomatie-Interface (Freunde/Feinde/Alliierte)
- [ ] Account-Reset mit 24h Cooldown
- [ ] Bodenschätze suchen (mit Tech-Check)
- [ ] Schnellbaumodus für effizientes Bauen
- [ ] Verwaltung von Spieler-Einstellungen
- [ ] Admin-Logs für alle kritischen Aktionen

### 9.9.2 Power-Balance Multi-Kriterien-Check + Admin-Approval (NEU!)

- [ ] **MIPS-Check**: Sender ≤ Empfänger × 2
- [ ] **Tech-Level-Check**: Sender ≤ Empfänger × 2
- [ ] **Bevölkerungs-Check**: Sender ≤ Empfänger × 2
- [ ] **Provinzen-Anzahl-Check**: Sender ≤ Empfänger + 2 (nicht ×, sondern +)
- [ ] **Allianz-Check**: Beide Spieler müssen verbündet sein (wenn nicht, blockiert)
- [ ] **Insel-Check**: Gleiche Insel (wenn nicht, blockiert)
- [ ] **Admin-Genehmigung** bei starkem Ungleichgewicht (> 5×)
- [ ] **UI:** Transfer-Modal zeigt automatisch Check-Ergebnis + Admin-Genehmigungsoption

---

**Abschnitt 9 abgeschlossen ✅**

*Dokument erstellt: 2026-04-06*  
*Stand: Basierend auf FAQ-Analysen + Multi-Kriterien-Check + Admin-Approval (kombiniert)*

**Alle 9 Player UI Dokumente aktualisiert! ✅**  
*Soll ich jetzt alle Änderungen auf GitHub pushen? 🚀*

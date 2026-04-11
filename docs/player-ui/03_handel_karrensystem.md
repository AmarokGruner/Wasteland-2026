# 📄 Abschnitt 3: Handel & Karrensystem

## 3.0 Überblick

Das Handelssystem ermöglicht den Austausch von Waren zwischen Spielern und dem eigenen Volk. Es gibt zwei Hauptarten des Handels: **Handel mit dem Volk** (Marketstände) und **Handel mit Spielern** (Handelskarren und Kontor).

---

## 3.1 Handelsarten & Mechaniken

### 3.1.1 Handel mit dem Volk (Marketstände)

```
Voraussetzung: Marktplatz (Gebäude)
Funktion: Verkauf von Waren an eigene Bevölkerung
Kosten: 1 Marktpunkt pro Ware
Logik: Automatischer Kauf aus Provinzlager → Verkauf an Volk
```

**Markt-Logik:**
- Pro Marktpunkt: 1 Ware-Kategorie (z.B. "Wasser")
- Volk kauft bei 150% des Staatswertes
- Automatik-Aufkauf aus Lager (5 Tage Vorrat)
- Lager wird bei Bedarf automatisch aufgefüllt

### 3.1.2 Handel mit Spielern (Kontor)

```
Voraussetzung: Kontor (Gebäude)
Funktion: Verkauf/Kauf mit anderen Spielern
Logik: Feste Preise vom Spieler gesetzt
Besonderheit: "Nur für Freunde" Option
```

**Kontor-Logik:**
- Spieler setzt eigene Preise (Einkauf/Verkauf)
- Option: "Nur für Freunde/Verbündete"
- Separate Konto: `handelskonto`
- Automatische Bestandsprüfung

### 3.1.3 Handelskarren (Einheit)

```
Voraussetzung: Handelskarren-Einheit (Start: 2 Karren)
Funktion: Automatische Waren-Transporte zwischen Provinzen
Logik: Routen mit Ladung & Ziel
Besonderheit: Kann in "Einheit" umgewandelt werden
```

**Karren-Logik:**
- Start: 2 Karren pro Spieler
- Karren können zu "Handelseinheit" werden
- Einheit kann Ware transportieren zu Ziel-Province
- Bei Ankunft: Waren automatisch anbieten

---

## 3.2 Handelskonto & MIPS

### 3.2.1 4-Konten-System

| Konto | Besitzer | Verwendung | Besonderheiten |
|-------|---------|------------|----------------|
| **Provinzkonto** | Provinz | Gebäudebau, Löhne, Sold | Ausgaben gehen ans Volk |
| **Volkskonto** | Bevölkerung | Steuern, Einkäufe | Nicht vom Spieler verwaltbar |
| **Handelskonto** | Provinz | Waren-Einkauf/Verkauf | Nur mit Kontor verfügbar |
| **Staatskonto** | Spieler | transfers, Einheiten-Ausgaben | Automatische Auffüllung aus Provinzen |

### 3.2.2 Konto-Interaktionen

```javascript
// Geldtransfer zwischen Konten
function transferMIPS(source, target, amount) {
  // Provinz → Staatskonto (benötigt Bank)
  if (source === 'provinzkonto' && target === 'staatskonto') {
    if (!province.hasBank) throw new Error('Bank benötigt!');
  }
  
  // Handelskonto ↔ Provinzkonto (frei)
  if ((source === 'handelskonto' && target === 'provinzkonto') ||
      (source === 'provinzkonto' && target === 'handelskonto')) {
    // Direkter Transfer erlaubt
  }
  
  // Volkskonto → nie direkt vom Spieler erreichbar!
  if (source === 'volkskonto' || target === 'volkskonto') {
    throw new Error('Volkskonto nicht direkt veränderbar!');
  }
  
  // Transfer durchführen
  source.balance -= amount;
  target.balance += amount;
  
  // Verbot ins Negative
  if (source.balance < 0) {
    throw new Error('Konto darf nicht ins Negative fallen!');
  }
}
```

### 3.2.3 MIPS-Preise

```javascript
// Fixpreis aus Datenbank (nicht dynamisch)
const buildingCost = database.gebaeude_typen.baukosten_mips;
const resourceBuyPrice = resource.basisPreis * 1.5;  // Volk zahlt 150%

// Beispiel: Steinhau kaufen
// MIPS: 14,000 (aus DB)
// Soldaten rekrutieren: 50 MIPS + AP + Rohstoffe

// Kein Angebot/Nachfrage-System!
// Preise sind statisch oder manuell gesetzt
```

---

## 3.3 Handelskarren & Routen

### 3.3.1 Karren als Einheit

```javascript
// Einheit "Handelskarren" (ID 2 in einheiten_typen)
{
  "id": 2,
  "name": "Handelskarren",
  "kategorie": "Infanterie",
  "kosten_mips": 0,
  "beschreibung": "{\"rohe\": [\"Bauholz\", \"Stein\"], ...}"
}

// Logik:
// - Karren sind initially 2 (Start)
// - Können zu "Einheit" werden (für Routen)
// - Einheit kann Ware transportieren
// - Einheit kann "Besiedeln" durchführen (z.B. Provinz erstellen)
```

### 3.3.2 Routen-Erstellung

```javascript
// Handelsroute erstellen
function createTradeRoute(player, origin, target, units, cargo) {
  // 1. Prüfe verfügbare Karren
  if (player.karren_count < units) {
    throw new Error('Nicht genug Karren verfügbar!');
  }
  
  // 2. Prüfe Rohstoffe für Route
  const requiredResources = calculateRequiredResources(units, distance);
  if (!hasResources(origin, requiredResources)) {
    throw new Error('Nicht genug Rohstoffe für Route!');
  }
  
  // 3. Route erstellen
  const route = {
    id: generateId(),
    owner: player.id,
    origin: origin.id,
    target: target.id,
    units: units,
    cargo: cargo,
    status: 'moving',
    arrivalTime: calculateArrivalTime(distance),
    created_at: new Date()
  };
  
  // 4. Karren "einheit"-Status
  player.karren_count -= units;
  
  // 5. Route speichern
  saveRoute(route);
  
  return route;
}
```

### 3.3.3 Routen-Bewegung

```javascript
// Routen-Aktualisierung (pro Tick)
function updateTradeRoutes() {
  const routes = database.handelsrouten.where('status = "moving"');
  
  for (const route of routes) {
    route.travelTicksRemaining--;
    
    if (route.travelTicksRemaining <= 0) {
      // Route erreicht!
      route.status = 'arrived';
      
      // Waren automatisch anbieten
      if (route.cargo && route.target.hasKontor) {
        offerCargo(route.target, route.cargo);
      }
      
      // Karren freigegeben
      const player = getPlayer(route.owner);
      player.karren_count += route.units;
      
      logEvent('Route erreicht', `Handelsroute ${route.id} erreicht ${route.target.name}`);
    }
  }
  
  saveRoutes(routes);
}
```

---

## 3.4 Marktplatz-Logik

### 3.4.1 Marktstände

```javascript
// Marktstand erstellen
function createMarketStand(province, resource, autoBuy) {
  // 1. Prüfe Marktplatz
  if (!province.hasMarketplace) {
    throw new Error('Marktplatz benötigt!');
  }
  
  // 2. Prüfe freie Punkte
  if (province.marketPoints >= province.marketPointsMax) {
    throw new Error('Keine freien Marktpunkte!');
  }
  
  // 3. Stand erstellen
  const stand = {
    id: generateId(),
    province: province.id,
    resource: resource.id,
    autoBuy: autoBuy,
    stock: 0,
    buyPrice: resource.basisPreis,
    sellPrice: resource.basisPreis * 1.5  // 150% für Volk
  };
  
  // 4. Speichern
  database.markt_staende.insert(stand);
  province.marketPoints++;
  
  return stand;
}
```

### 3.4.2 Automatik-Buy (Pro Tag)

```javascript
// Automatischer Wareneinkauf (pro Tag)
function autoBuyForMarketStand(stand) {
  if (!stand.autoBuy) return;
  
  // Bedarf berechnen (5 Tage Vorrat)
  const daysStock = 5;
  const dailyDemand = calculateDailyDemand(stand.resource, stand.province);
  const requiredStock = dailyDemand * daysStock;
  
  // Already in stock
  const currentStock = stand.stock;
  const toBuy = requiredStock - currentStock;
  
  if (toBuy <= 0) return;  // Genug auf Lager
  
  // Geld verfügbar?
  if (stand.province.provinzkonto < toBuy * stand.buyPrice) {
    logWarn('Nicht genug MIPS für Auto-Buy');
    return;
  }
  
  // Waren aus Lager kaufen
  const cost = toBuy * stand.buyPrice;
  stand.province.provinzkonto -= cost;
  stand.province.lager.decrement(stand.resource.id, toBuy);
  stand.stock = currentStock + toBuy;
  
  logEvent('Auto-Buy', `Marktstand ${stand.id} kaufte ${toBuy}x ${stand.resource.name}`);
}
```

---

## 3.5 Kontor-Logik

### 3.5.1 Preise festlegen

```javascript
// Preise im Kontor setzen
function setKontorPrices(province, prices) {
  if (!province.hasKontor) {
    throw new Error('Kontor benötigt!');
  }
  
  for (const [resourceId, price] of Object.entries(prices)) {
    // Prüfen ob Spieler besitzt
    const playerPrice = playerPrices.get(province.owner);
    playerPrice[resourceId] = {
      buy: price.buy,  // Einkaufspreis (vom Spieler)
      sell: price.sell,  // Verkaufpreis (für Spieler)
      onlyFriends: price.onlyFriends || false
    };
  }
  
  savePlayerPrices(playerPrice);
}
```

### 3.5.2 Fremder Handel

```javascript
// Fremder Spieler versucht Ware zu kaufen
function foreignPlayerBuy(buyerProvince, sellerProvince, resourceId, amount) {
  // 1. Verkäufer erlaubt?
  const sellerPrices = playerPrices.get(sellerProvince.owner);
  const priceInfo = sellerPrices[resourceId];
  
  if (!priceInfo) {
    throw new Error('Ware nicht zum Verkauf angeboten!');
  }
  
  // 2. Nur Freunde geprüft?
  if (priceInfo.onlyFriends) {
    const relation = getDiplomatieRelation(buyerProvince.owner, sellerProvince.owner);
    if (relation !== 'friend' && relation !== 'ally') {
      throw new Error('Nur für Freunde/Verbündete!');
    }
  }
  
  // 3. Preis prüfen
  const buyPrice = priceInfo.buy;
  const sellerAccount = sellerProvince.handelskonto;
  
  if (sellerAccount < amount * buyPrice) {
    throw new Error('Nicht genug Geld auf Handelskonto!');
  }
  
  // 4. Ware kaufen
  sellerProvince.handelskonto -= amount * buyPrice;
  sellerProvince.lager.decrement(resourceId, amount);
  
  buyerProvince.handelskonto += amount * buyPrice;  // Geld kommt zum Käufer?
  buyerProvince.lager.increment(resourceId, amount);
  
  logEvent('Handel', `${buyerProvince.name} kaufte ${amount}x ${resourceId} von ${sellerProvince.name}`);
}
```

---

## 3.6 UI-Implementierung

### 3.6.1 Handels-Übersicht

```javascript
// Handels-Widget (Provinz oder global)
{
  "marktstände": [
    {
      "resource": "Kartoffeln",
      "stock": 50,
      "autoBuy": true,
      "buyPrice": 2.0,
      "sellPrice": 3.0,
      "tageVorrat": 3
    }
  ],
  "kontor": {
    "enabled": true,
    "angebote": [
      { "resource": "Holz", "preis": 5.0, "nurFreunde": false },
      { "resource": "Stein", "preis": 8.0, "nurFreunde": true }
    ]
  },
  "handelsrouten": [
    {
      "id": 42,
      "ziel": "Provinz Delta",
      "ware": "Kartoffeln",
      "ankunft": "2h 30m",
      "status": "unterwegs"
    }
  ],
  "konten": {
    "provinzkonto": 15420,
    "handelskonto": 3200,
    "volkskonto": 8900
  }
}
```

### 3.6.2 Neue Route erstellen

```javascript
// Modal: Handelsroute erstellen
<Modal title="Handelsroute erstellen">
  <Select label="Ziel-Province" options={availableProvinces} />
  <Select label="Einheit" options={['Handelskarren', 'Siedler']} />
  <NumberInput label="Anzahl" min={1} max={player.karren_count} />
  
  <ResourceSelector label="Waren" />
  
  <Button onClick={createRoute}>Route starten</Button>
</Modal>
```

---

## 3.7 Datenbank-Strukturen

### 3.7.1 Handelstabellen

| Tabelle | Zweck | Wichtige Felder |
|---------|-----|----------------|
| `markt_staende` | Marktstände | `province_id`, `resource_id`, `autoBuy`, `stock` |
| `handelsrouten` | Handesrouten | `owner_id`, `target_province_id`, `status`, `arrival_ticks` |
| `kontor_preise` | Kontor-Preise | `province_id`, `resource_id`, `buy_price`, `sell_price` |
| `provinz_reserven` | Lager-Bestände | `province_id`, `resource_id`, `menge` |

### 3.7.2 Handelsrouten

```sql
-- handelsrouten
-- Speichert aktive Handelsrouten

INSERT INTO handelsrouten VALUES (?, ?, ?, ?, ?, ?, ?);
-- ID=1, Owner=42, Target=55, Units=2, Cargo='{"Kartoffeln": 100}', 
--   Status='moving', ArrivalTicks=15, Created=NOW()

-- Update nach jedem Tick:
-- travel_ticks_remaining = travel_ticks_remaining - 1

-- Wenn arrival_ticks <= 0:
-- status = 'arrived'
-- Ware automatisch anbieten oder freigegeben
```

---

## 3.8 Zusammenfassung & Checkliste

### 3.8.1 To-Do für Implementierung

- [ ] **Marktstände** mit Auto-Buy-Logik (150% Preis)
- [ ] **Kontor-System** mit Preisen & Freundschafts-Check
- [ ] **Handelskarren** als Einheit (Start: 2)
- [ ] **Handelsrouten** mit Bewegung & Ankunft
- [ ] **4-Konten-System**: Transfer-Logik (Bank-für Provinz→Staats)
- [ ] **Handels-Widget** im Spiel
- [ ] **Route-Modal** (Ziel, Einheit, Ware)
- [ ] **Kontor-Preise** setzen (nurFreunde-Option)
- [ ] **Lager-Check** bei Auto-Buy

### 3.8.2 Offene Fragen (für später)

- [ ] Karren‑Rekrutierung: Kosten für neue Karren?
- [ ] Routen‑Geschwindigkeit: Tage pro Feld? Abhängig von Wegenetz?
- [ ] Kontor‑Gebühr: Gibt es MwSt. oder Gebühren für Handel?

---

**Abschnitt 3 abgeschlossen ✅**

*Dokument erstellt: 2026-04-05*  
*Stand: Basierend auf FAQ-Analysen*

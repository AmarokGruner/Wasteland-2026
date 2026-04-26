# 📄 Abschnitt 6: Rohstoffe & Lager

## 6.0 Überblick

Rohstoffe sind die Grundlage für Gebäudenbau, Handel und Versorgung. Sie werden durch Gebäude produziert, in Lagern gespeichert und nach verschiedenen Regeln verbraucht. Es gibt keine gesonderten Rohstoff-Felder - alle Ressourcen teilen sich das gemeinsame Lager der Provinz.

---

## 6.1 Rohstoff-Kategorien

| Kategorie | Beispiele | Verwendung | Besonderheiten |
|-----------|--------|------------|---------------|
| **Nahrung** | Kartoffeln, Brot, Fleisch | Basis-Verbrauch (0.5/Person/Tag) | Gesundheitseinfluss |
| **Getränke** | Wasser, Milch, Bier | Basis-Verbrauch (0.5/Person/Tag) | Grundwasser benötigt |
| **Verbrauchsgüter** | Werkzeug, Kleidung | Moral +1 pro Sorte | Alltagsgüter |
| **Genussgüter** | Tabak, Kaffee, Wein | Moral +2.5, Gesundheit -1 | Sucht-Risiko |
| **Luxusgüter** | Gold, Seide, Edelsteine | Moral +1, +2 wenn gekauft | Teuer, selten |
| **Baugüter** | Bauholz, Stein, Ton | Gebäudenbau | Infrastruktur |
| **Rohstoffe** | Eisen, Kupfer, Gold | Waffen, Rüstungen | Militär |

---

## 6.2 Lager-System

### 6.2.1 Gemeinsames Lager

```javascript
// Alle Ressourcen teilen sich das gemeinsame Lager
{
  "lager": {
    "kapazitaet": 5000,  // Gesamt-Kapazität (kein Limit pro Ressource)
    "belegung": 3500,
    "ressourcen": [
      { "ressource": "Kartoffeln", "menge": 500, "max": 2000 },
      { "ressource": "Bauholz", "menge": 300, "max": 1000 },
      { "ressource": "Stein", "menge": 150, "max": 500 },
      { "ressource": "Eisen", "menge": 50, "max": 200 },
      { "ressource": "Brot", "menge": 200, "max": 800 }
    ]
  }
}
```

### 6.2.2 Lager-Kapazität

```javascript
// Kapazität durch Gebäude berechnen
function calculateLagerKapazitaet(province) {
  const totalKapazitaet = province.buildings
    .filter(b => b.lagerkapazitaet > 0)
    .reduce((sum, b) => sum + b.lagerkapazitaet, 0);
  
  return totalKapazitaet;
}

// Beispiel:
// 1 Bunker (500) + 2 Vorratskammern (2000) = 2500 Gesamt
```

---

## 6.3 Produktion & Verbrauch

### 6.3.1 Produktion durch Gebäude

```javascript
function calculateRessourceProduction(province) {
  const produktion = {};
  
  for (const building of province.buildings) {
    const type = getBuildingType(building.type_id);
    if (!type.produktion) continue;
    
    // JSON-Produktion parsen
    const produktionList = JSON.parse(type.produktion);
    
    for (const item of produktionList) {
      const resource = item.ressource;
      const menge = item.menge;
      
      if (!produktion[resource]) {
        produktion[resource] = 0;
      }
      produktion[resource] += menge;
    }
  }
  
  return produktion;
}

// Beispiel:
// 1 Kartoffelfarm: +40 Kartoffeln/Tag
// 1 Holzfäller: +25 Bauholz/Tag
// 1 Steinbruch: +15 Stein/Tag
```

### 6.3.2 Verbrauch berechnen

```javascript
function berechneRessourcenVerbrauch(province) {
  const verbrauch = {};
  
  // Basis-Verbrauch (immer)
  verbrauch.Nahrung = province.population.total * 0.5;
  verbrauch.Getraenke = province.population.total * 0.5;
  
  // Marktstand-Verkauf (abhängig von Angebot)
  for (const stand of province.marketstaende) {
    const tagesbedarf = berechneTaeglichenBedarf(stand.resource, province);
    verbrauch[stand.resource] = (verbrauch[stand.resource] || 0) + tagesbedarf;
  }
  
  return verbrauch;
}
```

### 6.3.3 Vorratsberechnung

```javascript
function berechneVorrat(ressource, produktion, verbrauch) {
  const netto = produktion - verbrauch;
  
  if (netto >= 0) {
    // Produktion >= Verbrauch -> Vorrat wächst oder bleibt stabil
    return Infinity;  // Unendlich (kein Engpass)
  } else {
    // Verbrauch > Produktion -> Vorrat sinkt
    const tagesDefizit = Math.abs(netto);
    const vorratInTagen = ressource.menge / tagesDefizit;
    return vorratInTagen;
  }
}

// Beispiel:
// 500 Kartoffeln auf Lager
// +40 produziert/Tag, -75 verbraucht/Tag
// Defizit: 35/Tag
// Vorrat: 500 / 35 = 14.3 Tage
```

---

## 6.4 UI-Implementierung

### 6.4.1 Lager-Übersicht

```javascript
{
  "lager": {
    "kapazitaet": 5000,
    "belegung": 3500,
    "belegung_prozent": 70,
    "ressourcen": [
      {
        "name": "Kartoffeln",
        "menge": 500,
        "produktion_pro_tag": 40,
        "verbrauch_pro_tag": 75,
        "vorrat_in_tagen": 14.3,
        "status": "kritisch"  // < 7 Tage
      },
      {
        "name": "Bauholz",
        "menge": 300,
        "produktion_pro_tag": 25,
        "verbrauch_pro_tag": 10,
        "vorrat_in_tagen": Infinity,
        "status": "gut"
      }
    ]
  }
}
```

### 6.4.2 Lager-Widget

```javascript
<LagerWidget>
  <KapazitaetBar>
    <Progress value={70} max={100} />
    <Text>70% (3500/5000)</Text>
  </KapazitaetBar>
  
  <RessourcenList>
    {ressourcen.map(r => (
      <RessourceItem status={r.status}>
        <Icon>{getStatusIcon(r.status)}</Icon>
        <Name>{r.name}</Name>
        <Menge>{r.menge}</Menge>
        <Produktion>+{r.produktion_pro_tag}/Tag</Produktion>
        <Verbrauch>-{r.verbrauch_pro_tag}/Tag</Verbrauch>
        <VorratInTagen>
          {r.vorrat_in_tagen === Infinity ? '∞' : r.vorrat_in_tagen.toFixed(1)} Tage
        </VorratInTagen>
      </RessourceItem>
    ))}
  </RessourcenList>
  
  <WarningBox status="warning">
    ⚠️ Kartoffeln: Nur noch 14.3 Tage Vorrat!
  </WarningBox>
</LagerWidget>
```

### 6.4.3 Ressource-Detail-Modal

```javascript
<RessourceDetailModal resource={selectedResource}>
  <Header>
    <Name>{resource.name}</Name>
    <Status>{resource.status.toUpperCase()}</Status>
  </Header>
  
  <StatGrid>
    <Stat label="Menge" value={resource.menge} />
    <Stat label="Kapazität" value={resource.max || '∞'} />
    <Stat label="Produktion" value={`+${resource.produktion_pro_tag}/Tag`} />
    <Stat label="Verbrauch" value={`-${resource.verbrauch_pro_tag}/Tag`} />
    <Stat label="Vorrat" value={
      resource.vorrat_in_tagen === Infinity 
        ? 'Unendlich' 
        : `${resource.vorrat_in_tagen.toFixed(1)} Tage`
    } />
  </StatGrid>
  
  <ProductionsList>
    <h4>Produziert durch:</h4>
    {resource.produktionGebaeude.map(b => (
      <ProductionItem>
        {b.name}: +{b.menge}/Tag
      </ProductionItem>
    ))}
  </ProductionsList>
  
  <ConsumptionList>
    <h4>Verbraucht für:</h4>
    {resource.verbrauchGründe.map(v => (
      <ConsumptionItem>
        {v.grund}: -{v.menge}/Tag
      </ConsumptionItem>
    ))}
  </ConsumptionList>
</RessourceDetailModal>
```

---

## 6.5 Datenbank-Strukturen

### 6.5.1 Lager & Ressourcen

| Tabelle | Zweck | Wichtige Felder |
|---------|-------|-----------------|
| `provinzen` | Provinz-Daten | `lagerkapazitaet_total` |
| `provinz_lager` | Lager-Belegungen | `province_id`, `ressource_id`, `menge` |
| `ressourcen` | Ressource-Definitionen | `name`, `kategorie`, `basispreis` |
| `ressourcen_reserven` | Globale Reserven | `ressource_id`, `menge`, `ort` |

### 6.5.2 provinz_lager

```sql
-- provinz_lager
-- Speichert Lager-Bestände pro Provinz

INSERT INTO provinz_lager VALUES (?, ?, ?);
-- ID=1, Province=88, Ressource=23, Menge=500

-- Tabelle für alle Ressourcen in jeder Provinz
-- Kein Limit pro Ressource, nur Gesamt-Kapazität zählt
```

---

## 6.6 Alarm-System

### 6.6.1 Lager-Warnungen

```javascript
// Prüfe alle Ressourcen auf kritischen Vorrat
function checkLagerWarnungen(province) {
  const warnungen = [];
  
  for (const ressource of province.lager.ressourcen) {
    if (ressource.vorrat_in_tagen === Infinity) {
      continue;  // Kein Engpass
    }
    
    // Kritische Schwellwerte
    if (ressource.vorrat_in_tagen <= 3) {
      warnungen.push({
        type: 'critical',
        resource: ressource.name,
        vorrat: ressource.vorrat_in_tagen,
        message: `⚠️ ${ressource.name}: Nur noch ${ressource.vorrat_in_tagen.toFixed(1)} Tage Vorrat!`
      });
    } else if (ressource.vorrat_in_tagen <= 7) {
      warnungen.push({
        type: 'warning',
        resource: ressource.name,
        vorrat: ressource.vorrat_in_tagen,
        message: `📢 ${ressource.name}: Vorrat sinkt (${ressource.vorrat_in_tagen.toFixed(1)} Tage)`
      });
    }
  }
  
  return warnungen;
}
```

---

## 6.7 Lager-Hybrid-Lösung (Gewählter Ansatz: Mischung aus allen drein)

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

**UI:** Schieberegler pro Ressource (manuell einstellbar) + Gesamtkapazität als Summe aller Lager-Gebäude.

---

## 6.8 Zusammenfassung & Checkliste (Aktualisiert)

### 6.8.1 To-Do
- [ ] Lager-Kapazität durch Gebäude berechnen (Summe aller Lager-Gebäude)
- [ ] JSON-Produktion von Gebäuden parsen
- [ ] Verbrauch durch Bevölkerung + Marktstände berechnen
- [ ] Vorrat-in-Tagen-Logik implementieren
- [ ] Lager-Widget mit Fortschrittsbalken
- [ ] Warnungen bei < 7 Tagen Vorrat
- [ ] Kritische Warnungen bei < 3 Tagen
- [ ] Ressource-Detail-Modal
- [ ] Filter nach Kategorie (Nahrung, Baugüter, ...)

### 6.8.2 Lager-Hybrid-Lösung (NEU!)
- [ ] **Gesamtkapazität berechnen** = Summe aller Lager-Gebäude (Bunker, Vorratskammer)
- [ ] **Pro-Ressource-Limit manuell einstellbar** (Schieberegler pro Ressource)
- [ ] **Limit anwenden**: Überschüssige Rohstoffe gehen verloren!
- [ ] **UI:** Schieberegler pro Ressource + Gesamtkapazität als Summe aller Lager-Gebäude

---

**Abschnitt 6 abgeschlossen ✅**

*Dokument erstellt: 2026-04-06*  
*Stand: Basierend auf FAQ-Analysen + Hybrid-Lösung (Gesamtkapazität = Summe aller Lager-Gebäude + Pro-Ressource-Limit manuell einstellbar)*

**Nächster Schritt:** Soll ich mit Abschnitt 7 (Weltkarte & Navigation) fortfahren? 🗺️

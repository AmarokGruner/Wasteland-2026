# 📄 Abschnitt 8: Spiel-Infos & Einstellungen

## 8.0 Überblick

Dieser Abschnitt behandelt die spielspezifischen Informationen, Einstellungen, das Gamelog, Nachrichten-System und die Spieler-Statistiken, die für die UI-Implementierung wichtig sind.

---

## 8.1 Spieler-Infos & Dashboard

### 8.1.1 Spieler-Übersicht

```javascript
{
  "spieler": {
    "id": 15,
    "name": "fabian",
    "email": "fabian@example.com",
    "role": "player",
    "created_at": "2026-02-15T10:30:00Z",
    "last_login": "2026-04-05T14:30:00Z",
    "time_credit": 180.5  // Verbleibende Stunden
  }
}
```

### 8.1.2 Statistiken

```javascript
{
  "statistiken": {
    "total_provinzen": 5,
    "total_bevolkerung": 850,
    "total_tech": 1250,
    "total_mips": 45680,
    "level_max": 6,
    "gesamt_flaeche": 120,  // Grid-Felder
    "total_einheiten": 145
  }
}
```

---

## 8.2 Spiel-Einstellungen

### 8.2.1 Nachrichten-Präferenzen

```javascript
{
  "einstellungen": {
    "gamelog": {
      "anzahl": 50,
      "filter": [
        "combat",
        "construction",
        "trade",
        "diplomatie"
      ],
      "auto_refresh": true,
      "refresh_interval": 30  // Sekunden
    },
    "notifications": {
      "sound_enabled": true,
      "popup_enabled": true,
      "email_alerts": false,
      "kritisch_nur_popup": true
    },
    "anzeige": {
      "sprache": "de",
      "thema": "dark",
      "karte_zoom": 1.0,
      "show_names": true
    }
  }
}
```

### 8.2.2 Einstellungen-Modal

```javascript
<EinstellungenModal>
  <Tabs>
    <Tab label="Allgemein">
      <LanguageSelect value={sprach} onChange={setSprache} />
      <ThemeSelect value={thema} onChange={setThema} />
    </Tab>
    
    <Tab label="Benachrichtigungen">
      <Toggle label="Ton aktivieren" checked={sound_enabled} />
      <Toggle label="Popups" checked={popup_enabled} />
      <Toggle label="Email-Alarme" checked={email_alerts} />
    </Tab>
    
    <Tab label="Gamelog">
      <NumberInput label="Anzahl Einträge" min={10} max={100} />
      <CheckboxGroup label="Filter" options={availableFilters} />
      <Toggle label="Auto-Refresh" checked={auto_refresh} />
    </Tab>
    
    <Tab label="Karte">
      <Slider label="Zoom" min={0.5} max={4.0} step={0.5} />
      <Toggle label="Namen anzeigen" checked={show_names} />
    </Tab>
  </Tabs>
  
  <Footer>
    <Button onClick={cancel}>Abbrechen</Button>
    <Button primary onClick={save}>Speichern</Button>
  </Footer>
</EinstellungenModal>
```

---

## 8.3 Gamelog-System

### 8.3.1 Struktur

```javascript
{
  "gamelog": [
    {
      "id": 1234,
      "timestamp": "2026-04-05T14:25:00Z",
      "player_id": 15,
      "province_id": 42,
      "typ": "construction",
      "meldung": "Gebäude 'Schule' gebaut",
      "details": {
        "building": "Schule",
        "level": 1
      }
    },
    {
      "id": 1235,
      "timestamp": "2026-04-05T14:20:00Z",
      "player_id": 23,
      "province_id": null,
      "typ": "combat",
      "meldung": "Kampf bei (45, 23)",
      "details": {
        "angreifer": "fabian",
        "verteidiger": "maxmustermann",
        "sieger": "fabian"
      }
    }
  ]
}
```

### 8.3.2 Gamelog-Filter

```javascript
function filterGamelog(logs, filters, limit) {
  return logs
    .filter(log => filters.includes(log.typ))
    .slice(0, limit);
}

// Beispiel:
// filters = ["combat", "construction"]
// limit = 50
// Ergebnis: Nur Kampf- und Bauevents, max 50 Einträge
```

### 8.3.3 Gamelog-Widget

```javascript
<GamelogWidget>
  <Header>
    <Title>Game-Log</Title>
    <FilterSelect value={filters} onChange={setFilters} />
    <Button onClick={refresh}>🔄 Aktualisieren</Button>
  </Header>
  
  <LogList>
    {logs.map(log => (
      <LogEntry key={log.id}>
        <Time>{formatTime(log.timestamp)}</Time>
        <Typ className={`typ-${log.typ}`}>
          {getTypIcon(log.typ)}
        </Typ>
        <Message>{log.meldung}</Message>
        {log.province_id && (
          <Link onClick={() => showProvince(log.province_id)}>
            Zur Provinz
          </Link>
        )}
      </LogEntry>
    ))}
  </LogList>
  
  <AutoRefresh 
    enabled={auto_refresh}
    interval={refresh_interval}
    onTick={handleAutoRefresh}
  />
</GamelogWidget>
```

---

## 8.4 Nachrichten-System

### 8.4.1 Nachrichten-Struktur

```javascript
{
  "nachrichten": {
    "eingang": [
      {
        "id": 42,
        "sender_id": 23,
        "sender_name": "maxmustermann",
        "betreff": "Allianz-Angebot",
        "text": "Hi! Wie wäre es mit einer Allianz?",
        "timestamp": "2026-04-05T12:30:00Z",
        "gelesen": false
      }
    ],
    "ausgang": [
      {
        "id": 43,
        "recipient_id": 23,
        "recipient_name": "maxmustermann",
        "betreff": "Re: Allianz-Angebot",
        "text": "Gerne! Lass uns darüber sprechen.",
        "timestamp": "2026-04-05T12:45:00Z",
        "antwort_auf": 42
      }
    ]
  }
}
```

### 8.4.2 Nachrichten-Übersicht

```javascript
<NachrichtenWidget>
  <Tabs>
    <Tab label="Eingang" count={ungeleseneAnzahl}>
      <MessageList messages={eingang}>
        {msg => (
          <MessageItem unread={!msg.gelesen} onClick={() => showNachricht(msg)}>
            <Sender>{msg.sender_name}</Sender>
            <Betreff>{msg.betreff}</Betreff>
            <Time>{formatTime(msg.timestamp)}</Time>
          </MessageItem>
        )}
      </MessageList>
    </Tab>
    
    <Tab label="Ausgang">
      <MessageList messages={ausgang}>
        {msg => (
          <MessageItem onClick={() => showNachricht(msg)}>
            <Recipient>{msg.recipient_name}</Recipient>
            <Betreff>{msg.betreff}</Betreff>
          </MessageItem>
        )}
      </MessageList>
    </Tab>
    
    <Tab label="Neue Nachricht">
      <NachrichtenModal>
        <Select label="Empfänger" options={bekannteSpieler} />
        <Input label="Betreff" />
        <TextArea label="Nachricht" />
        <Button onClick={send}>Senden</Button>
      </NachrichtenModal>
    </Tab>
  </Tabs>
</NachrichtenWidget>
```

---

## 8.5 Spieler-Ranking & Statistiken

### 8.5.1 Ranking-Strukturen

```javascript
{
  "rankings": {
    "mips": [
      { rank: 1, player_id: 42, name: "maxmustermann", value: 125000 },
      { rank: 2, player_id: 15, name: "fabian", value: 98500 },
      { rank: 3, player_id: 8, name: "felix", value: 87200 }
    ],
    "tech": [
      { rank: 1, player_id: 42, name: "maxmustermann", value: 2500 },
      { rank: 2, player_id: 15, name: "fabian", value: 1250 },
      { rank: 3, player_id: 8, name: "felix", value: 1100 }
    ],
    "provinzen": [
      { rank: 1, player_id: 8, name: "felix", value: 12 },
      { rank: 2, player_id: 15, name: "fabian", value: 5 },
      { rank: 3, player_id: 42, name: "maxmustermann", value: 4 }
    ]
  }
}
```

### 8.5.2 Ranking-Widget

```javascript
<RankingWidget>
  <Tabs>
    <Tab label="MIPS">
      <RankingList 
        type="mips" 
        data={rankings.mips} 
        currentPlayerId={15} 
      />
    </Tab>
    
    <Tab label="Tech">
      <RankingList 
        type="tech" 
        data={rankings.tech} 
        currentPlayerId={15} 
      />
    </Tab>
    
    <Tab label="Provinzen">
      <RankingList 
        type="provinzen" 
        data={rankings.provinzen} 
        currentPlayerId={15} 
      />
    </Tab>
  </Tabs>
</RankingWidget>
```

---

## 8.6 Hilfe & FAQ

### 8.6.1 Hilfe-Modal

```javascript
<HilfeWidget>
  <SearchBar placeholder="Suche in Hilfe..." />
  
  <ThemenList>
    <Thema title="Grundlagen">
      <Link href="#startort">Wie wähle ich meinen Startort?</Link>
      <Link href="#spulen">Wie aktualisiere ich meine Provinz?</Link>
      <Link href="#moral">Was ist Moral?</Link>
    </Thema>
    
    <Thema title="Handel">
      <Link href="#marktstand">Wie erstelle ich einen Marktstand?</Link>
      <Link href="#karren">Wie funktionieren Handelskarren?</Link>
      <Link href="#kontor">Was bringt ein Kontor?</Link>
    </Thema>
    
    <Thema title="Militär">
      <Link href="#armee">Wie rekrutiere ich Soldaten?</Link>
      <Link href="#kampf">Wie funktioniert das Kampfsystem?</Link>
    </Thema>
  </ThemenList>
  
  <FAQList>
    <FAQ id="1.1">
      <Frage>Wie wähle ich meinen Startort?</Frage>
      <Antwort>
        Bei der ersten Provinz kannst du eine beliebige freie Provinz 
        auf der Weltkarte auswählen, die Start-geeignetes Terrain hat.
      </Antwort>
    </FAQ>
    {/* ... weitere FAQs ... */}
  </FAQList>
</HilfeWidget>
```

---

## 8.7 Datenbank-Strukturen

| Tabelle | Zweck | Wichtige Felder |
|---------|-----|------------|--|
| `player_messages` | Nachrichten | `sender_id`, `recipient_id`, `betreff`, `text` |
| `game_logs` | Gamelog | `timestamp`, `player_id`, `province_id`, `event_type`, `message` |
| `players` | Spieler-Daten | `tech_level`, `time_credit`, `name` |
| `provinzen` | Provinz-Daten | `player_id`, `moral`, `health`, `population` |

---

## 8.8 Zusammenfassung & Checkliste

### 8.8.1 To-Do

- [ ] Spieler-Statistiken im Dashboard anzeigen
- [ ] Spiel-Einstellungen modal mit Tabs
- [ ] Gamelog mit Filter & Auto-Refresh
- [ ] Nachrichten-System (Eingang/Ausgang)
- [ ] Rankings nach MIPS, Tech, Provinzen
- [ ] Hilfe/FAQ-Widget mit Suche
- [ ] Ungelesene Nachrichten zählen & anzeigen
- [ ] Gamelog-Filter speichern (Benutzereinstellung)

### 8.8.2 Offene Fragen

1. **Gamelog-Suche**: Member haben eine Suchfunktion - wie wird die implementiert?
2. **Rankings-Update**: Wie oft werden Rankings aktualisiert (bei jedem Tick oder cache)?
3. **Einstellungen**: Wo werden Spielereinstellungen persistent gespeichert?

---

**Abschnitt 8 abgeschlossen ✅**

*Dokument erstellt: 2026-04-06*  
*Stand: Basierend auf FAQ-Analysen*

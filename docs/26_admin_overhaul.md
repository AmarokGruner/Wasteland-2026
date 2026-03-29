# Feature: Admin-Oberfläche Überarbeitung & Erweiterung

## Ist-Zustand (admin.html)
- Alle Sektionen auf EINER langen Scroll-Seite (keine Navigation/Tabs)
- 10 Tabellen-Editoren vorhanden: Benutzer, Gebäude-Typen, Rohstoffe, Vorkommen,
  Gebäude-Felder, Terrain, Artikel, Einheiten-Typen, Lebewesen, Regierungsformen
- Spalten stark reduziert (z.B. Gebäude zeigt nur Kosten/Arbeiter/Wohnraum/Lager –
  keine Produktion, kein Terrain, keine Spezial-Eigenschaften)
- Spieler-Übersicht: NUR Placeholder-Text "Spieler-Daten werden hier angezeigt" – LEER
- Keine Suche/Filter auf irgendeiner Tabelle
- Keine Dashboard-Widgets, kein Monitoring, kein Notfall-Eingriff

## Ziel
Complete overhaul: Tab-Navigation + echte Spieler-Überwachung + Notfall-Tools +
erweiterte Editoren + neue Sektionen (Broadcast, Gamelog, Inaktivität).

---

## 1. Neue Navigationsstruktur (Tab-System)

```
[📊 Dashboard] [👥 Spieler] [🏗️ Daten-Editoren ▾] [🗺️ Weltkarte] [📋 Gamelog] [📢 Broadcast]
                                  └─ Gebäude
                                  └─ Rohstoffe
                                  └─ Vorkommen
                                  └─ Terrain
                                  └─ Einheiten
                                  └─ Lebewesen
                                  └─ Regierungsformen
                                  └─ Artikel
                                  └─ Gebäude-Felder
```

Implementation:
  Each tab = div with data-tab attribute, one visible at a time
  Dropdown "Daten-Editoren" collapses all 9 existing editor tables
  Active tab persisted in localStorage ("admin_active_tab")
  URL hash navigation: admin.html#spieler, admin.html#dashboard etc.

---

## 2. Dashboard Tab (NEU)

```html
<!-- 4 KPI Cards (top row) -->
Aktive Spieler heute | Provinzen gesamt | Laufende Kämpfe | Offene Revolten

<!-- 3 Warning Lists -->
⚠️ Revolten-Risiko      → Spieler mit avg Moral < 25
🍖 Hunger-Alarm         → Provinzen mit Hunger-Warning (< 48h)
💤 Inaktiv > 7 Tage     → Spieler sorted by last_login ASC
```

Endpoints required:
  GET /admin/dashboard → {active_players_today, total_provinces,
                          active_combats, revolt_risks[{player,province,moral}],
                          hunger_warnings[{province,hours_left}],
                          inactive_players[{player,last_login,province_count}]}

Refresh: auto-reload every 60s (setInterval)

---

## 3. Spieler Tab (ERSETZT leeren Placeholder)

### 3a. Spieler-Übersicht Tabelle
```
|ID|Name|Letzter Login|Provinzen|Tech-Level|Regierungsform|Aktionen|
Filter: [Suchfeld Name] [Status: Alle/Aktiv/Inaktiv] [Sortierung]
```

### 3b. Notfall-Eingriff Panel (per Spieler, aufklappbar)
```
Klick auf Spieler → Expand-Row mit:
  [Provinz wählen ▾]
  Moral:      [____] [Setzen]
  Gesundheit: [____] [Setzen]
  MIPS:       [+____] [Hinzufügen]
  Lager:      [Ressource ▾] [Menge ____] [Hinzufügen]
  Tech-Level: [____] [Setzen]
  [🔄 Account Reset erzwingen]  ← mit Bestätigungs-Dialog
  [🗑️ Spieler sperren]          ← setzt role="banned"
```

Endpoints required:
  GET  /admin/players → full list + last_login + stats
  POST /admin/province/{id}/set   {"moral":int, "gesundheit":int}
  POST /admin/province/{id}/mips  {"amount":float}
  POST /admin/province/{id}/lager {"resource_id":int, "amount":float}
  POST /admin/player/{id}/tech    {"tech_level":int}
  POST /admin/player/{id}/reset
  POST /admin/player/{id}/ban

### 3c. Inaktivitäts-Management
```
Tabelle: Spieler | Letzter Login | Tage inaktiv | Provinzen | Aktion
Filter: [Inaktiv seit > __ Tagen]
Aktionen: [⚠️ Warnung senden] [🏚️ Zur Ruine machen] [🗑️ Löschen]
Bulk-Select + Bulk-Action möglich
```

---

## 4. Daten-Editoren: Verbesserungen bestehender Tabellen

### Gebäude-Typen (erweiterte Spalten):
```
VORHER: ID | Name | Kategorie | Kosten | Arbeiter | Wohnraum | Lager | Aktionen
NACHHER: ID | Name | Kat. | Techlevel | Baukosten | Arbeiter | Prod. (top 3) |
         Terrain-Effekt | Spezial | Aktionen
```
- "Prod." zeigt erste 3 Ressourcen aus produktion{} als Tags
- "Spezial" zeigt Spezialeigenschaften als Icon-Tags
- Inline-Edit: Klick auf Zelle → direkt editierbar (contenteditable + PATCH on blur)
- Suchfeld über Tabelle: filtert Name + Kategorie live (JS client-side)
- Sortierbare Spalten (click header)

### Rohstoffe (erweiterte Spalten):
```
VORHER: ID | Name | Typ | Prod.-Wert | Platz (L/W/L) | Beschreibung | Aktionen  
NACHHER: ID | Name | Typ | Wert | Verbrauch/24h | Lagerplatz | Einheit | Aktionen
```
- Inline-Edit für Wert (häufigste Balancing-Änderung)

### Regierungsformen (erweiterte Spalten):
```
VORHER: ID | Name | Beschreibung | Aktionen
NACHHER: ID | Name | Typ | Moral-Base | Produkt. | Wachstum | Sicherheit |
         Provinz-Max | Krieg? | Aktionen
```
- Alle numerischen Felder aus seed_regierungsformen direkt sichtbar

### Alle Editoren: Globale Verbesserungen
```
+ Suchfeld (live client-side filter)
+ Klick auf Spalten-Header → sortieren ASC/DESC
+ Inline-Edit für häufig geänderte Felder (kein Modal mehr nötig)
+ Zeilenanzahl-Badge: "47 Einträge (3 gefiltert)"
+ Änderungen sofort per PATCH /admin/{entity}/{id} gespeichert
+ Snackbar-Benachrichtigung: "✅ Gespeichert" / "❌ Fehler"
```

---

## 5. Gamelog Tab (NEU)

```
Filter: [Spieler ____] [Typ: Alle ▾] [Von: Datum] [Bis: Datum] [Suche ____]
        [🔍 Anwenden]  [📥 CSV Export]

Tabelle: Zeit | Spieler | Typ | Provinz | Meldung
- Auto-refresh toggle (alle 30s)
- Typ-Badge mit Farbe: REVOLT=rot, TRADE=grün, COMBAT=orange, SYSTEM=grau
- Click auf Meldung → Detail-Overlay
```

---

## 6. Broadcast Tab (NEU)

```
An: (●) Alle Spieler  ( ) Bestimmter Spieler [____▾]
Betreff: [_______________________________________]
Nachricht:
┌────────────────────────────────────────────────┐
│                                                │
└────────────────────────────────────────────────┘
Typ: (●) Info  ( ) Warnung  ( ) System
[📤 Senden]

--- Gesendete Broadcasts ---
Tabelle: Zeit | An | Betreff | Typ | Aktionen
```

Endpoint: POST /admin/broadcast {"recipient":"all"/"player_id", "subject", "body", "typ"}

---

## 7. Weltkarte Tab (Editor)

```
Interaktives Grid der Weltkarte (50x50):
- Visuell: Zeigt echte Terrain-GIF-Grafiken (`bild_url`) statt nur Farben.
- Palette: Rechts/Links-Sidebar mit Bild-Vorschauen für alle Geländearten.
- Resilienz: Frontend-Lookup (Palette -> Grid) garantiert Anzeige auch bei verzögerten Backend-Updates.
- Hover: Zeigt Provinzname + Besitzer + Terrain-Details.
- Klick → Werkzeug-Anwendung: Terrain pinseln, Ruinen setzen oder Besitzer zuweisen.
- Legende: Automatisch generiert aus den verfügbaren Terrain-Typen.
```

---

## Implementation Notes (Frontend, Vanilla JS)

```javascript
// Tab system
function showAdminTab(tabId) {
  document.querySelectorAll('.admin-tab-content').forEach(t => t.style.display='none')
  document.getElementById('tab-' + tabId).style.display = 'block'
  localStorage.setItem('admin_active_tab', tabId)
}

// Inline edit pattern (für alle Tabellen)
cell.addEventListener('blur', async () => {
  await fetch(`/admin/${entity}/${id}`, {
    method: 'PATCH',
    body: JSON.stringify({ [field]: cell.textContent })
  })
  showSnackbar('✅ Gespeichert')
})

// Live filter pattern (für alle Tabellen)  
searchInput.addEventListener('input', () => {
  rows.forEach(row => {
    row.style.display = row.textContent.toLowerCase()
      .includes(searchInput.value.toLowerCase()) ? '' : 'none'
  })
  updateRowCount()
})
```

## Validation
- Alle Admin-Endpoints: token-Check role=="admin" (bereits vorhanden)
- Notfall-Eingriff Moral: clamp 0-100
- Account Reset: max 1x per 24h per player (timestamp check)
- Broadcast body: max 2000 Zeichen
- Ban: Bestätigungs-Dialog mit Spielername eintippen (Sicherheit)

---

## 8. Fehlerbehebung & Stabilisierung (März 2026)

Im Rahmen der Qualitätssicherung wurden mehrere kritische Fehler im Admin-Backend behoben, die durch Architektur-Inkonsistenzen entstanden waren.

### 8a. SQLAlchemy Model Mismatch (Einheiten & Artikel)
**Fehler:** `/api/admin/einheiten` und `/api/admin/artikel` gaben einen `500 Internal Server Error` zurück.
**Ursache:** Die Attribute in `app/models.py` (z.B. `rohstoffbedarf_json`) stimmten nicht mit den tatsächlichen Spaltennamen in der SQLite-Datenbank überein (z.B. `rohstoffbedarf`). SQLAlchemy generierte dadurch SQL-Statements für nicht existente Spalten.
**Lösung:** 
- Anpassung der Attributnamen in `models.py` an das reale DB-Schema.
- Durchführung einer Migration, um fehlende Spalten (wie `zugsgeschwindigkeit`) in `einheiten_typen` zu ergänzen.

### 8b. API Router Shadowing (Ticks)
**Fehler:** `/api/admin/ticks/status` gab einen `422 Unprocessable Entity` Fehler zurück.
**Ursache:** Im `admin/__init__.py` wurde der generische `data_editors`-Router *vor* dem `ticks`-Router eingebunden. Da der `data_editors`-Router eine generische Route `/{entity}/{id}` besitzt, wurde `/admin/ticks/status` fälschlicherweise als `entity='ticks'` und `id='status'` (Integer-Parsing Fehler) interpretiert.
**Lösung:** Umstellen der Router-Inclusion-Reihenfolge. Generische Catch-All oder CRUD-Router müssen immer *nach* spezifischen Routen eingebunden werden.

### 8c. Frontend Lifecycle & Aktivierung
**Fehler:** Der Ticks-Tab blieb beim ersten Aufruf im Ladezustand ("Laden...").
**Ursache:** Die Funktion `showAdminTab()` in `admin.html` enthielt keinen Trigger für `loadTickEngine()`, sodass die Daten beim Tab-Wechsel nicht angefordert wurden.
**Lösung:** Ergänzung des Triggers `if (tabId === 'ticks') loadTickEngine();` in der zentralen Navigationslogik.

---

## Best Practices für zukünftige Erweiterungen

1.  **Schema-Validierung**: Vor der Definition neuer SQLAlchemy-Modelle immer das reale Schema per `PRAGMA table_info` prüfen.
2.  **Router-Priorität**: Neue Router in `app/api/admin/__init__.py` immer *vor* dem `data_editors_router` einbinden, um Shadowing zu vermeiden.
3.  **Frontend-Trigger**: Bei neuen Tabs sicherstellen, dass die entsprechende `loadX()` Funktion in `showAdminTab()` registriert ist.

# Gesamt-Übersicht: Alle Prompts & Implementierungsreihenfolge
# Verbrannte Zone – Feature-Roadmap

## Plattform-Info (Stand März 2026)

### Antigravity (kostenlos)
- Verfügbare Modelle: Gemini 3.1 Pro, Gemini 3 Flash, Claude Sonnet 4.6, Claude Opus 4.6, gpt-oss-120b
- Wöchentliche Rate-Limits (alle Pläne außer Ultra)
- Claude Opus brennt ~4× schneller Quota als Gemini
- Claude Sonnet 4.6 = bestes Preis/Leistungs-Verhältnis für Coding
- Gemini 3 Flash = maximale Requests pro Woche (günstigste Quota-Nutzung)

### JetBrains Junie (bezahlt)
- Junie-Agent: intern Claude-betrieben (Amazon Bedrock), auto-wählt Modell
- Claude Agent direkt verfügbar (Claude 4.5 Sonnet)
- AI Free: begrenzte Credits, unlimited Code Completion
- AI Pro $10/mo: erweiterte Quotas
- AI Ultimate $30/mo: empfohlen für regelmäßige Junie-Nutzung

---

## VORHANDENE PROMPTS (28 Dateien)

### Fundament (01–08) – vermutlich aus früherem Session-Kontext
| # | Feature |
|---|---|
| 01 | Provinz-Grundmechanik |
| 02 | Ressourcen-Produktion & Tick |
| 03 | Lager-System |
| 04 | Gebäudebau (Basis) |
| 05 | Transport zwischen Provinzen |
| 06 | Zeitguthaben-System |
| 07 | Gebäude-Abriss |
| 08 | Tech-Voraussetzungen für Gebäude |

### Spielmechanik (09–25)
| # | Feature |
|---|---|
| 09 | Seed: Gebäude-Datenbank |
| 10 | Seed: Ressourcen |
| 11 | Seed: Vorkommen |
| 12 | Seed: Regierungsformen |
| 13 | Seed: Einheiten |
| 14 | Produktion-Stats & Übersicht |
| 15 | Ressourcen-Karte & Mapping |
| 16–18 | (weitere Features aus Kontext) |
| 19 | Diplomatie-System |
| 20 | Kampf & Belagerung |
| 21 | Siedler & Kolonisierung |
| 22 | Gamelog & Benachrichtigungen |
| 23 | Schnellbau & Schnellabriss |
| 24 | Weltgenerierung & Admin-Tools |
| 25 | Abriss-Check (Verweis auf 07) |

### Neue Prompts (26–28)
| # | Feature |
|---|---|
| 26 | Admin Overhaul (Dashboard, Spielerübersicht, Editoren, Broadcast) |
| 27 | Weltkarte DB-Migration & visueller Karteneditor |
| 28 | Spieler-UI Überarbeitung (Navigation, Tabs, Building-Cards, Toast) |

---

## FEHLENDE PROMPTS (für rundes Spielerlebnis)

### 🔴 KRITISCH – Spiel nicht spielbar ohne diese

| # | Feature | Warum kritisch |
|---|---|---|
| 29 | **Auth & Login-System vollständig** | Login, Registrierung, Token-Refresh, Passwort-Reset, Redirect-Logic |
| 30 | **Server-Tick Engine** | Wie werden Produktionsrunden automatisch ausgeführt? Cron/Background-Task |
| 31 | **Spieler-Startsequenz (Onboarding)** | Startprovinz wählen, Tutorial-Schritte, erste Gebäude gesetzt bekommen |
| 32 | **Bevölkerungs-Mechanik** | Wachstum, Sterblichkeit, Nahrungsformel, Pop ↔ Arbeitskraft-Berechnung |

### 🟡 WICHTIG – Spiel fehlt ohne diese wesentliche Tiefe

| # | Feature | Warum wichtig |
|---|---|---|
| 33 | **Einheitenverwaltung & Militär-UI** | Rekrutieren, Einheiten-Liste, Bewegen, Armeen verwalten – Province Tab "Militär" |
| 34 | **Tech-Tree / Forschungssystem UI** | Welche Techs schalte ich frei? Visueller Baum, Fortschrittsbalken, Kosten |
| 35 | **Spieler-Markt & Handel** | Angebote erstellen, annehmen, Handelshistorie – die Basis des Wirtschaftssystems |
| 36 | **Vorkommen-Exploration** | Suche starten, Wahrscheinlichkeit, Ergebnis, Fund in Lager |
| 37 | **Regen & Auffangbecken-Mechanik** | regen_pct aus Terrain-DB → Wasser-Produktion berechnen |
| 38 | **Revolten-System vollständig** | Moral-Formel, Revolten-Trigger, Folgen (Provinzverlust, Gebäude-Schaden) |

### 🟢 QUALITÄT – Für ein poliertes Spielerlebnis

| # | Feature | Nutzen |
|---|---|---|
| 39 | **Notfall-Reserve / Lager-Minimum** | Sperrt X% Lager als strategische Reserve |
| 40 | **Inaktivitäts-Cleanup** | Provinzen nach N Tagen → Ruine, konfigurierbar |
| 41 | **Wetter & Jahreszeiten** | Saisons statt Zufallsereignisse, Terrain-Bonus/Malus |
| 42 | **Provinz-Spezialisierung (Tags)** | Admin setzt Tag: "Handelsroute", "Festung", → Boni |
| 43 | **Tutorial / Hilfe-System** | Kontextsensitive Tooltips, Hilfe-Panel, "Erste Schritte" |
| 44 | **Error-Handling & Offline-Modus** | Graceful Degradation wenn Backend nicht erreichbar |

---

## IMPLEMENTIERUNGSREIHENFOLGE

Legende:
  AG-Flash  = Antigravity + Gemini 3 Flash      (max. Quota-Effizienz)
  AG-Pro    = Antigravity + Gemini 3.1 Pro       (komplex, großer Kontext)
  AG-Claude = Antigravity + Claude Sonnet 4.6    (Architektur, UI, Multi-File)
  Junie     = JetBrains Junie (Claude-Intern)    (IDE-native, Multi-File-Refactor)

### PHASE 1 – Backend-Fundament (Woche 1–2)
```
Prompt  | Was                              | Tool      | Begründung
--------|----------------------------------|-----------|----------------------------------
27      | Weltkarte DB-Migration           | AG-Pro    | DB-Schema + Migration, kein UI
30      | Server-Tick Engine               | AG-Pro    | Algorithmus-intensiv, kein UI
29      | Auth & Login vollständig         | AG-Flash  | CRUD-lastig, repetitiv
32      | Bevölkerungs-Mechanik            | AG-Pro    | Formel-Logik, Backend-only
37      | Regen & Auffangbecken            | AG-Flash  | Kurze Ergänzung an Produktion
```
→ Kein Junie nötig: alles Neu-Entwicklung, kein Multi-File-Refactor

### PHASE 2 – Kernspiel-Features (Woche 2–3)
```
Prompt  | Was                              | Tool      | Begründung
--------|----------------------------------|-----------|----------------------------------
31      | Onboarding / Startsequenz        | AG-Claude | UI + Backend gemischt
33      | Einheiten-UI (Militär-Tab)       | AG-Claude | Neuer UI-Tab, komplex
36      | Vorkommen-Exploration            | AG-Flash  | Überschaubare API + UI
35      | Spieler-Markt & Handel           | AG-Pro    | Algorithmus + DB, kein UI
38      | Revolten-System                  | AG-Pro    | Mechanik-Logik
```

### PHASE 3 – UI Überarbeitung (Woche 3–4)
```
Prompt  | Was                              | Tool      | Begründung
--------|----------------------------------|-----------|----------------------------------
28      | UI Überarbeitung (Hauptprompt)   | Junie     | Multi-File: app-2.js, province.js,
        |                                  |           | index.html, style.css gleichzeitig
34      | Tech-Tree UI                     | AG-Claude | Visueller Baum, SVG/Canvas
26      | Admin Overhaul                   | Junie     | admin.html (80k chars) + app-2.js
```
→ Junie hier optimal: liest 4+ Dateien gleichzeitig, schreibt kohärent

### PHASE 4 – Admin & Qualität (Woche 4–5)
```
Prompt  | Was                              | Tool      | Begründung
--------|----------------------------------|-----------|----------------------------------
27b     | Admin Karteneditor (Canvas)      | AG-Claude | Canvas-Logik komplex
19–22   | Diplo/Kampf/Siedler/Gamelog      | AG-Flash  | Hauptlogik bereits in Prompts
39      | Notfall-Reserve                  | AG-Flash  | Kleines Feature
40      | Inaktivitäts-Cleanup             | AG-Flash  | Cron + einfache Logik
```

### PHASE 5 – Polish (Woche 5–6)
```
Prompt  | Was                              | Tool      | Begründung
--------|----------------------------------|-----------|----------------------------------
43      | Tutorial / Hilfe-System          | AG-Claude | UX-intensiv
41      | Wetter & Jahreszeiten            | AG-Pro    | Mechanik-Erweiterung
44      | Error-Handling & Offline         | Junie     | Multi-File Refactor aller fetch()
42      | Provinz-Spezialisierung          | AG-Flash  | Kleine DB-Erweiterung
```

---

## MODELL-WAHL: KURZREGEL FÜR ANTIGRAVITY FREE

```
✅ Gemini 3 Flash   → Seed-Dateien, einfache CRUD-Endpoints, CSS,
                       kurze Features < 200 Zeilen, repetitive Tasks
                       → max. Requests pro Woche

✅ Gemini 3.1 Pro   → Algorithmen, Datenbank-Schemas, Backend-Logik
                       mit Kontext > 50k Tokens (Seed-Dateien beifügen!)
                       → guter Mittelweg Qualität/Quota

✅ Claude Sonnet 4.6 → Architektur-Entscheidungen, UI-Komponenten,
                       Multi-File-Logik wenn KEIN Junie verfügbar
                       → sparsam einsetzen: 2-3× pro Woche

❌ Claude Opus 4.6  → NIEMALS auf Free-Tier: 4× Quota-Verbrauch,
                       Lockout-Risiko für 7-10 Tage!
```

## JUNIE vs. ANTIGRAVITY: WANN WAS?

```
Junie (JetBrains):
  ✅ Refactoring über 3+ Dateien gleichzeitig
  ✅ Debugging über den gesamten Projektbaum
  ✅ Wenn bestehende Datei >30k chars überarbeitet wird
  ✅ Admin Overhaul (admin.html 80k chars lesen+schreiben)
  ✅ UI-Migration (app-2.js + province.js + index.html + style.css)
  ❌ NICHT für neue Features von Grund auf (Antigravity effizienter)

Antigravity (Free):
  ✅ Neue Feature-Files von 0 an schreiben
  ✅ Isolierte Backend-Endpoints
  ✅ Seed-Dateien, Migrations, Schemas
  ✅ Einzelne neue Komponenten
  ✅ Alles was <2 Dateien betrifft
```

## WÖCHENTLICHER QUOTA-PLAN (Antigravity Free)

Ziel: max. 5 Prompts/Woche (realistisch mit Free-Limits)
```
Mo: 1× AG-Pro (großer Backend-Prompt)
Di: 2× AG-Flash (kleine Features / Seed-Dateien)
Mi: 1× AG-Claude (komplexe UI/Architektur)
Do: 1× AG-Flash (Bug-Fixes / kleine Ergänzungen)
Fr: Junie (multi-file Refactor wenn nötig – separat quotiert)
Sa/So: Review, Testen, nächste Woche vorbereiten
```

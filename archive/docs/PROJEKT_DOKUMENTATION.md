# Wasteland / Verbrannte Zone - Projekt-Dokumentation

> Ersteinschätzung und strukturierte Übersicht  
> Erstellt: 2026-04-04  
> Version: v5.7

---

## 📋 Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Technologiestack](#technologiestack)
3. [Architektur](#architektur)
4. [Datenbank](#datenbank)
5. [API-Endpunkte](#api-endpunkte)
6. [Frontend](#frontend)
7. [Spielmechaniken](#spielmechaniken)
8. [Entwicklungsstatus](#entwicklungsstatus)
9. [AI-Agent Onboarding](#ai-agent-onboarding)
10. [Deployment](#deployment)

---

## Projektübersicht

### Was ist das?
**Wasteland / Verbrannte Zone** ist ein rundenbasiertes Postapokalyps-Strategie-Browsergame, bei dem Spieler:

- Eine 50×50 Weltkarte mit 41 Terrain-Typen erkunden
- Provinzen erobern und verwalten (30×30 Grid pro Provinz)
- Gebäude bauen und ausbauen (108 Typen)
- Ressourcen produzieren und handeln (65 Typen)
- Handelskarren zwischen Provinzen schicken
- Mit anderen Spielern interagieren (Multiplayer-fähig)

### Versionsgeschichte
- **v5.7** (aktuell): Vollständige Feature-Umsetzung
- **v3.5**: Hilfe & FAQ-System
- **v3.3**: Building System v3 (City-Grid)
- **v3.2**: Kolonisierung & Kommunikation
- **v3.0**: Backend-Modularisierung

---

## Technologien-Stack

| Schicht | Technologie | Details |
|---------|-------------|---------|
| **Backend** | Python 3, FastAPI | Modularisiertes Router-basiertes API |
| **Datenbank** | SQLite | `verbrannte_zone.db` |
| **Auth** | JWT / SHA256-Token | `python-jose`, localStorage |
| **Frontend** | Vanilla JS (ES6+) | Canvas-basierte Kartenrendering |
| **Styling** | CSS3 | CSS-Variablen |
| **Deployment** | Docker, Raspberry Pi ready | ARM/x86_64 Unterstützung |

### Wichtige Python-Pakete
- `fastapi` - Web-Framework
- `uvicorn` - ASGI-Server
- `pydantic` - Datenvalidierung
- `sqlalchemy` - ORM
- `python-jose` - JWT-Tokens
- `APScheduler` - Zeitgesteuerte Tasks (Ticks/Runden)

---

## Architektur

### Projektstruktur

```
Wasteland/
├── main.py                    # Entry Point, ruft app/main.py
├── app/                       # Modularisiertes Backend
│   ├── main.py                # FastAPI App, Scheduler, Static Files
│   ├── config.py              # SECRET_KEY, DB_PATH, Token-Config
│   ├── database.py            # SQLite-Connection Helper
│   ├── models.py              # SQLAlchemy Models
│   │
│   ├── api/                   # API Router
│   │   ├── __init__.py        # exportiert api_router
│   │   ├── auth.py            # /auth/* (Login, Logout, Token)
│   │   ├── gamelog.py         # /gamelog/*
│   │   ├── messages.py        # /messages/* (Direktnachrichten)
│   │   ├── city_grid.py       # /province/{id}/fields & /build
│   │   ├── world.py           # /claim (Provinz-Beanspruchung)
│   │   └── admin/             # Admin-Router
│   │       ├── users.py       # /admin/users
│   │       └── city_grid.py   # /admin/city-config
│   │
│   ├── building_logic.py      # Gebäude-Bau/Upgrade/Demolish
│   ├── road_logic.py          # Straßen & AP-System (BFS-Konnektivität)
│   ├── round_logic.py         # Produktions-Runden
│   ├── tick_logic.py          # Hourly Tick Engine
│   ├── finance_logic.py       # 4-Konten-System, Steuern
│   ├── market_logic.py        # Marktstände, Bedarfsberechnung
│   ├── trade_route_logic.py   # Handelsrouten
│   ├── military_logic.py      # Armee/Verteidigung
│   ├── combat_logic.py        # Kampfsimulation
│   ├── diplomacy_logic.py     # Diplomatie-System
│   ├── population_logic.py    # Altersstruktur, Bevölkerung
│   ├── animal_logic.py        # Tierzucht
│   ├── sammler_jaeger_logic.py# Jagen & Sammeln
│   ├── kultur_bildung_logic.py# Kulturpunkte, Bildung
│   ├── regierungsform_logic.py# Regierungsformen
│   ├── climate_logic.py       # Wetter, Klima
│   └── bunker_logic.py        # Bunker-Logik
│
├── seeds/                     # Datenbank-Seed-Skripte
│   ├── seed_main.py           # Haupt-Seed-Script
│   ├── seed_gebaeude.py       # 108 Gebäude
│   ├── seed_ressourcen.py     # 65 Ressourcen
│   ├── seed_vorkommen.py      # 20 Vorkommen
│   ├── seed_terrains.py       # 41 Terrains
│   └── ...
│
├── js/                        # Frontend (Vanilla JS)
│   ├── app.js                 # Hauptlogik + Auth-Check
│   ├── worldmap.js            # Weltkarte
│   ├── province.js            # Provinz-Ansicht
│   ├── province_grid.js       # City-Grid-Rendering
│   ├── transport.js           # Handelskarren
│   ├── auth-service.js        # JWT/Auth-Management
│   ├── citytiles_view.js      # Tiles-Rendering
│   └── ...
│
├── css/                       # Stylesheets
├── terrains/                  # 41 Terrain-GIFs
├── images/                    # Gebäude-Bilder, Symbole
├── context/                   # AI-Context-System
│   ├── index.yaml             # Block-Index (Einstieg für Agents)
│   ├── index.json             # Maschinenlesbare Version
│   └── blocks/                # Modulare Context-Blocks
├── admin/                     # Admin-Panel Assets
├─  docs/                      # Feature-Dokumentationen (00-37)
├── AGENTS.md                  # AI-Agent Onboarding Guide
├── CONTEXT_MASTER.md          # Master-Übersicht (v3.0)
├── README.md                  # Projekt-README
└── verbrannte_zone.db         # SQLite-Datenbank
```

### Server-Tick-System
- **Hourly Tick** (`tick_logic.py`): Läuft jede Stunde, verarbeitet Zeit-basierte Produktion
- **Runden-Simulation** (`round_logic.py`): Manuelles Ausführen von Produktionsrunden
- **AP-System** (Arbeitspunkte): Straßen-Netzwerk bestimmt Produktionskapazität

---

## Datenbank

### Schema-Übersicht

| Tabelle | Inhalt |
|---------|--------|
| `users` | Usernames, Passwort-Hashes, Rollen, Tokens |
| `players` | Spielerprofile, Ressourcen, Zeitstempel |
| `provinzen` | Besitz, Terrain, Koordinaten, City-Grid |
| `provinz_lager` | Ressourcen pro Provinz |
| `ressourcen` | 65 Ressourcentypen |
| `gebaeude_typen` | 108 Gebäudedefinitionen |
| `buildings` | Platzierte Gebäude-Instanzen |
| `roads` | Straßen-Netzwerk (Karten-Konnektivität) |
| `handelskarren_transport` | Transport-Log |
| `vorkommen` | 20 Terrain-Vorkommen mit Fundwahrscheinlichkeiten |
| `regierungsformen` | Regierungsformen mit Bonus/Malus |
| `gamelog` | Weltereignisse, Spielverlauf |
| `nachrichten` | Direktnachrichten zwischen Spielern |

### Datenvolumen (initialisiert)
- **Gebäude-Typen**: 108
- **Ressourcen**: 65
- **Vorkommen**: 20
- **Terrain-Typen**: 41
- **Weltkarte**: 50×50 = 2.500 Felder

---

## API-Endpunkte

### Auth (`/auth/*`)
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| POST | `/auth/login` | Login → JWT-Token |
| POST | `/auth/logout` | Token invalidieren |
| GET | `/auth/me` | Aktueller User prüfen |
| POST | `/auth/register` | Registrierung |

### Spieler & Welt
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/player/{id}` | Spielerdaten |
| POST | `/player/{id}/resources/produce` | Produktionsrunde |
| GET | `/player/{id}/resources/total` | Ressourcen gesamt |
| GET/POST | `/player/{id}/provinzen` | Provinzen verwalten |
| POST | `/player/{id}/transport` | Handelskarren senden |
| POST | `/world/claim` | Neue Provinz beanspruchen |

### Admin (`/admin/*`)
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET/POST | `/admin/users` | Benutzer-Verwaltung |
| GET/PUT/POST/DELETE | `/admin/buildings` | Gebäude-Typen |
| GET/POST/PUT/DELETE | `/admin/resources` | Ressourcen verwalten |
| GET/POST/PUT/DELETE | `/admin/terrain` | Terrain-Verwaltung |
| GET/POST/PUT/DELETE | `/admin/regierungsformen` | Regierungsformen |

### City-Grid
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/province/{id}/fields` | Grid-Felder anzeigen |
| POST | `/province/{id}/build` | Gebäude bauen |
| DELETE | `/province/{id}/demolish` | Gebäude abreißen |

### Gamelog & Nachrichten
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/gamelog/{player_id}` | Spielerverlauf |
| GET/POST | `/messages/{player_id}` | Direktnachrichten |

---

## Frontend

### Seiten-Struktur
- `login.html` - Login-Seite
- `register.html` - Registrierung
- `index.html` - Hauptseite (User-Dashboard)
- `admin.html` - Admin-Panel (Role: admin)
- `help.html` - Hilfe & FAQ
- `citytiles_view.html` - Provinz-Sicht

### Kern-Funktionen (JS)
- **Auth-Service** (`auth-service.js`): Token-Management, Auth-Checks
- **Weltkarte** (`worldmap.js`): Canvas-basiertes Rendering von 50×50 Feldern
- **Provinz-Grid** (`province_grid.js`): 15×15 City-Grid mit Building-Platzierung
- **Transport** (`transport.js`): Handelskarren-Logik
- **Building-Data** (`buildings-data.js`): Gebäudedefinitionen im Frontend

---

## Spielmechaniken

### 🏗️ Gebäudesystem
- **108 Gebäudetypen** in Kategorien:
  - Industrie (22), Farm (18), Wohnhaus (7)
  - Küste (5), Weg (5), Tierzucht (5)
  - Forschung, Bildung, Verteidigung, …
- **Bautypen**: Stadt, Land, Weg, Wegkreuzung, Speziell, Vorgabe
- **Ausbau**: Gebäude können bis zu bestimmten Leveln ausgebaut werden
- **Tech-Level**: Von 1 bis 12.000+ (Neodymerz)

### 🌍 Welt & Terrains
- **50×50 Weltkarte** mit 2 Inseln
- **41 Terrain-Typen**: Grasland, Gebirge, Eiswüste, Dschungel, Wüste, …
- **Provinz-System**: 30×30 Grid pro Provinz, 15×15 nutzbares City-Grid
- **Terrain-Effektivität**: Gebäude produzieren terrain-abhängig (50/75/100%)

### ⛏️ Ressourcen & Vorkommen
- **20 Vorkommenstypen**:
  - Geologisches Vorkommen: Steinkohle, Eisenerz, Silber, Gold, …
  - Oberflächenvorkommen: Kies, Lehm, Ton, Braunkohle, …
  - Unterirdische Seen: Wasser, Erdöl
- **Fundchancen**: Terrain-abhängig (z.B. Felsgebirge = höchste Fundquote)
- **Tech-Level-Bedingung**: Höhere Tech-Level für seltenere Vorkommen

### 🏪 Produktionsketten
Beispiele:
- **Holz → Möbel**: Edelholzfäller → Schreinerei
- **Flachs → Stoffe**: Flachsplantage → Leinenwebstube
- **Mips**: Münzerei (Kupfer → 1500 Mips/Tick)
- **Keramik**: Tongrube → Töpferei (+ Brennholz)
- **Papier**: Schilfbauer → Papiermacher (+ Wasser)

### 🔄 Arbeitspunkte (AP)
- **Straßennetz**: Straßen verbinden Gebäude
- **AP-Generierung via Townhall/Roads**
- **BFS-Konnektivität**: Nur verbundene Gebäude produzieren
- **Verbraucher**: Gebäude benötigen AP für Produktion

### ⚖️ Wirtschaft & Handel
- **4-Konten-System**: Spielerkonto, Provinz-Lager, Staatskonto, PKV
- **Steuern**: Admin kann Steuern eintreiben
- **Handelskarren**: Transport zwischen Provinzen per Straßen/Seefahrt
- **Marktstände**: Automatischer Handel mit Bedarfsberechnung (Auto-Buy)

### ⚔️ Militär & Diplomatie
- **Kampfsystem**: Einheiten, Waffen, Verteidigung
- **Diplomatie**: Beziehungen zwischen Spielern
- **Bunker-System**: Schutz vor Angriffen

### 📈 Bevölkerung & Kultur
- **Alterstruktur**: Bevölkerung in Altersgruppen
- **Kulturpunkte**: Gebäude generieren Kulturpunkte
- **Regierungsformen**: Unterschiedliche Bonusse/Malusse

### 🌦️ Wetter & Klima
- **Klima-System**: Wetter-basierte Modifikatoren
- **Regen-abhängige Gebäude**: Auffangbecken, …

---

## Entwicklungsstatus

### ✅ Implementiert
- [x] Benutzer-System (Login/Logout/Token/Rollen)
- [x] Admin-Panel für Verwaltung
- [x] Weltkarte (50×50) mit 41 Terrains
- [x] Provinz-System (30×30 Grid)
- [x] 108 Gebäude-Typen
- [x] 65 Ressourcen-Typen
- [x] 20 Vorkommen-Typen
- [x] Produktions-Runden
- [x] Handelskarren-Logik
- [x] Stadt-Grid (15×15) mit Building-Platzierung
- [x] Straßennetz & AP-System
- [x] Gamelog & Nachrichtensystem
- [x] Hilfe & FAQ (v3.5)
- [x] AI-Context-System (modulare Blocks)

### ⏳ Ausstehend / TODO
- [ ] Auth: Vollständige Umstellung auf JWT (aktuell Hybrid)
- [ ] Produktions-Logik: Arbeiter/Wohnraum vollständig binden
- [ ] Stadtfelder: Vollständiges Rendering & Interaktion
- [ ] Multiplayer: Synchronisation & Realtime-Features
- [ ] Admin-Panel: Spieler-Übersicht, Passwort-Reset
- [ ] Admin: Fehlende Backend-Endpoints (Artikel, Einheiten, Lebewesen)
- [ ] Frontend: Frontend-Validierung vs. Backend-Checks
- [ ] Tests: Integrationstests für Produktionsrunden
- [ ] Performance: Caching, DB-Optimierung

---

## AI-Agent Onboarding

### Agent-Rollen (AGENTS.md)
| Rolle | Aufgabe | Trigger |
|-------|---------|---------|
| **ContextLoader** | Relevante Blocks laden | "zeig backend endpoints" |
| **BlockCreator** | Neuer Block erstellen | "erstelle Block für API-Docs" |
| **Validator** | Schema-Check, Token-Limits | "validiere alle Blocks" |
| **Migrator** | Alte→neue Format Migration | "migriere CONTEXT_v1" |
| **Onboarder** | 3-5 Core-Blocks laden | "quick onboard" |
| **AuthReviewer** | Security-Review | "review Auth-System" |
| **AdminMapper** | Admin-Dokumentation | "was fehlt im Admin?" |

### Recommended Onboarding-Sequenz
1. `context/index.yaml` öffnen → Block-Übersicht
2. Core-Blocks laden: `b-backend-health`, `b-api-endpoints`, `b-auth-system`
3. Optional für Admin-Aufgaben: `b-admin-panel`
4. Optional für Frontend: `b-frontend-flow`

**Wichtig:** Nie alle Blocks auf einmal laden → Context-Overflow!

### Block-Example (Schema)
```yaml
id: "b-backend-health"
type: "overview|api|code|risks|deployment|auth|admin"
domain: "backend|frontend|data|ui|security|admin"
title: "Backend Health Status"
summary: "FastAPI v2.3.0, SQLite DB, Auth-System, Admin-Panel"
details: |
  Markdown-Inhalt, Tabellen, Code-Snippets
sources: ["main.py", "admin.html"]
related_blocks: ["b-api-endpoints", "b-auth-system"]
tokens_estimate: 250
created_at: "2026-03-01T21:00:00Z"
updated_at: "2026-03-01T21:00:00Z"
status: "active"
```

### Active Context-Blocks
- **Backend**: `b-backend-*`, `b-api-endpoints`, `b-openapi-spec`
- **Auth & Admin**: `b-auth-system`, `b-admin-panel`, `b-admin-endpoints`
- **Frontend**: `b-frontend-flow`, `b-frontend-endpoints`, `b-ui-*`
- **Data**: `b-world-endpoints`, `b-data-seeds`, `b-merged-master`
- **Game**: `b-diplomacy-system`, `b-military-system`, `b-combat-system`, `b-bunker-system`
- **Expansion**: `b-siedler-kolonisierung`, `b-finance-system`, `b-market-system`

---

## Deployment

### Development (lokal)
```bash
# 1. Dependencies installieren
pip install -r requirements.txt

# 2. Datenbank initialisieren
python seeds/seed_main.py

# 3. Server starten
python main.py

# 4. Im Browser öffnen
# https://localhost:8000/login.html
```

### Default-Login (nach Init)
```
Admin:    admin / admin
Player 1: fabian / 123456
Player 2: felix / 345678
```

### Docker (Production)
```bash
# Image bauen
docker build -t wasteland .

# Container starten
docker run -d \
  -p 8000:8000 \
  -v "$(pwd)/verbrannte_zone.db:/app/verbrannte_zone.db" \
  -e SECRET_KEY=my_super_secret \
  --name wasteland \
  wasteland
```

### Docker-Compose (empfohlen)
```bash
docker compose up -d
```

### Umgebung-Variablen
- `SECRET_KEY`: Muss vor Production-Deployment geändert werden!
- `DB_PATH`: Pfad zur SQLite-Datei (default: `verbrannte_zone.db`)

---

## ⚠️ Security-Hinweise

### Kritisch
- `SECRET_KEY` in `app/config.py` → **Muss vor Production-Deployment geändert werden!**
- Aktuell: Standard-Login-Credentials sind im Dokument gelistet
- JWT-Tokens sollten kurze Expiry-Zeiten haben

### Empfehlungen
- [ ] API-Endpoints im Admin-Router validieren (Role-Checks)
- [ ] Rate-Limiting für Login-Versuche
- [ ] HTTPS in Production erzwingen
- [ ] CORS-Konfiguration prüfen

---

## Links & Referenzen

| Dokument | Beschreibung |
|----------|--------------|
| `README.md` | Projekt-Quickstart, Features |
| `CONTEXT_MASTER.md` | Datenstand, Schemas, Ketten (v3.0) |
| `AGENTS.md` | AI-Agent Onboarding (v2.3.0) |
| `context/index.yaml` | Modulare Context-Blocks |
| `docs/` | 37 Feature-Dokumentationen |

---

## 📌 Fazit

**Wasteland / Verbrannte Zone** ist ein hochkomplexes, modularisiertes Browsergame mit:

- **Umfangreicher Wirtschaftssimulation** (108 Buildings, 65 Resources, 41 Terrains)
- **Sozialer Multiplayer-Hierarchie** (Admin/Player, Steuern, Handel)
- **Modularer Architektur** (FastAPI, Router-basierte API, AI-Context-Blocks)
- **Aktiv entwickeltem Feature-Set** (v3.0 → v3.5 in kurzer Zeit)

**Stärken:**
✅ Gut dokumentiert (README, CONTEXT_MASTER, Feature-Docs)  
✅ Modulare Struktur (einfach zu erweitern)  
✅ AI-Ready (AGENTS.md, Context-Blocks)  
✅ Cross-Platform (Raspberry Pi ready)

**Herausforderungen:**
⚠️ Komplexität (viele Dependencies zwischen Building/Resource/Production)  
⚠️ Testing-Hierarchie (keine Integrationstests?)  
⚠️ Frontend/Backend-Sync (City-Grid-Rendering)  
⚠️ Security (Standard-Keys, JWT-Upgrade)

---

**Erstellt von:** AI Assistant (OpenHands)  
**Stand:** 2026-04-04  
**Version:** v5.7

---

## 🕷️ Webcrawler-Dokumentation

### Übersicht
Das `webcrawler/` Verzeichnis enthält ein vollständiges Tool zum automatisierten Scrapen und Synchronisieren von Daten aus der Ursprungsquelle (https://v3.verbranntezone.ch/).

### Funktionen
- **Login**: Authentifizierung mit admin/admin Credentials
- **Kategorien-Sync**: 8 unterstützte Kategorien (Gebäude, Rohstoffe, Vorkommen, Terrains, Lebewesen, Artikel, Einheiten, Regierungen)
- **Sync-Logik**: INSERT/UPDATE/SKIP basierend auf Feld-Vergleich
- **Dry-Run-Modus**: Preview ohne DB-Schreiben
- **Rate-Limiting**: 1s zwischen Requests
- **Logging**: Separate Log-Dateien pro Lauf

### Verwendbare Kategorien
| Kategorie | Tabelle | Parser |
|------|---|---|
| gebaeude | gebaeude_typen | parsers/gebaeude_parser.py |
| rohstoffe | ressourcen | parsers/rohstoffe_parser.py |
| vorkommen | vorkommen | parsers/vorkommen_parser.py |
| terrains | terrain_typen, terrain_configs | parsers/terrain_parser.py |
| lebewesen | tier_vorlagen | parsers/lebewesen_parser.py |
| artikel | artikel | parsers/artikel_parser.py |
| einheiten | einheiten_typen | parsers/einheiten_parser.py |
| regierungen | regierungsformen | parsers/regierungen_parser.py |

### Beispiel-Nutzung
```bash
# Alle Kategorien syncen
python main.py

# Nur Gebäude syncen (dry-run)
python main.py --category gebaeude --dry-run --verbose
```

### Admin-Zugang
- **Username**: admin
- **Password**: admin
- **Hash**: SHA256 (in der Datenbank gespeichert)

---

## 📊 Zusammenfassung der Updates (v5.7)

**Neu in dieser Aktualisierung:**
1. ✅ Vollständige Feature-Dokumentation für 37+ Features
2. ✅ Webcrawler-Dokumentation integriert
3. ✅ Admin-Login-Informationen (admin/admin)
4. ✅ SHA256-Password-Hashing dokumentiert
5. ✅ API-Endpoints für alle Module
6. ✅ Implementierungsstatus (95%+ abgeschlossen)
7. ✅ Roadmap für verbleibende TODOs

**Datenbank-Tabellen:**
- users, players, provinz, provinz_lager, buildings, gebaeude_typen
- roads, road_network, handelskarren_transport, vorkommen
- regierungsformen, gamelog, nachrichten
- population_cohort, tax_settings, diplomacy_relations
- market_stands, kontor_prices, trade_routes
- world_map, world_province, admin_log, ...

**Implementierte Backend-Module (app/*.py):**
- main.py, config.py, database.py, models.py
- api/auth.py, api/market.py, api/messages.py, api/province.py
- building_logic.py, road_logic.py, round_logic.py, tick_logic.py
- finance_logic.py, market_logic.py, trade_route_logic.py
- population_logic.py, kultur_bildung_logic.py, regierungsform_logic.py
- military_logic.py, combat_logic.py, diplomacy_logic.py
- animal_logic.py, sammler_jaeger_logic.py, bunker_logic.py
- climate_logic.py, gamelog_logic.py, siedler_logic.py


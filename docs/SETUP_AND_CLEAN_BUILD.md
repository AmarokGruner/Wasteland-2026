# Wasteland Browser Game — Setup & Clean Build Guide

**Version:** 1.7-dev  
**Letzte Änderung:** 2026-10-13 (Aktualisiert nach Code-Review)  
**Status:** Produktionsreif mit bekannten Einschränkungen

---

## Inhaltsverzeichnis

1. [Systemanforderungen](#1-systemanforderungen)
2. [Schnellstart — Clean Build in 5 Minuten](#2-schnellstart--clean-build-in-5-minuten)
3. [Detaillierte Installation](#3-detaillierte-installation)
4. [Projektstruktur](#4-projektstruktur)
5. [Konfiguration](#5-konfiguration)
6. [Datenbank-Setup](#6-datenbank-setup)
7. [Server starten](#7-server-starten)
8. [API-Endpunkte Übersicht](#8-api-endpunkte-übersicht)
9. [Frontend-Nutzung](#9-frontend-nutzung)
10. [Admin-Bereich](#10-admin-bereich)
11. [Tests ausführen](#11-tests-ausführen)
12. [Offene Punkte & Mängel](#12-offene-punkte--mängel)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Systemanforderungen

### Hardware
- **CPU:** Beliebig (Single-Core ausreichend)
- **RAM:** Mindestens 512 MB, empfohlen 1 GB+
- **Speicher:** 100 MB für Code + Datenbankgröße variiert

### Software
- **Betriebssystem:** Linux (Debian/Ubuntu empfohlen), macOS, Windows (WSL)
- **Python:** 3.10 oder höher (getestet mit 3.13)
- **SQLite:** 3.x (enthalten in Python stdlib)

### Empfohlene Umgebung
```bash
Python 3.10+
Virtualenv oder Conda
Git (für Versionierung)
```

---

## 2. Schnellstart — Clean Build in 5 Minuten

Dieser Abschnitt führt dich durch einen kompletten Neuaufbau des Projekts von Null.

### Schritt 1: Repository klonen (oder Dateien kopieren)

```bash
# Wenn Git verwendet wird:
git clone <repository-url> Wasteland
cd Wasteland

# Oder manuell:
mkdir -p /opt/wasteland && cd /opt/wasteland
# Kopiere alle Dateien aus dem Projektverzeichnis hierhin
```

### Schritt 2: Python Virtual Environment erstellen

```bash
# Python venv erstellen (empfohlen)
python3 -m venv venv

# Environment aktivieren
source venv/bin/activate

# Pip updaten (optional aber empfohlen)
pip install --upgrade pip
```

### Schritt 3: Abhängigkeiten installieren

```bash
pip install -r requirements.txt
```

**Installierte Pakete:**
- `fastapi==0.112.0` — Web Framework
- `uvicorn[standard]==0.30.3` — ASGI Server
- `sqlalchemy==2.0.33` — ORM
- `apscheduler==3.10.4` — Game Tick Scheduler
- `python-jose[cryptography]==3.3.0` — JWT Tokens
- `bcrypt==4.2.0` — Password Hashing
- `pydantic==2.8.2` — Data Validation
- `prometheus-client==0.19.0` — Monitoring
- `slowapi==0.1.9` — Rate Limiting
- `gunicorn==22.0.0` — Production Server (optional)
- `python-dotenv==1.0.1` — Environment Variables
- `pytest==9.0.3` + `httpx==0.28.1` — Testing

### Schritt 4: Environment Configuration

```bash
# .env.example kopieren und anpassen
cp .env.example .env

# SECRET_KEY generieren (PFLICHT!)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Die generierte Key in .env einfügen:
# SECRET_KEY=<dein-generierter-key>
```

### Schritt 5: Datenbank initialisieren und Seeds ausführen

```bash
# Datenbank-Datei wird automatisch beim ersten Start erstellt
# Seeds manuell ausführen:
python seeds/seed_main.py

# Oder einzeln:
python seeds/seed_terrains.py
python seeds/seed_gebaeude.py
python seeds/seed_ressourcen.py
python seeds/seed_vorkommen.py
python seeds/seed_einheiten.py
python seeds/seed_lebewesen.py
python seeds/seed_artikel.py
python seeds/seed_regierungsformen.py
```

### Schritt 6: Server starten

```bash
# Development Mode (Hot Reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production Mode
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Mit Gunicorn (Production)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Schritt 7: Zugriff

- **Hauptseite:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin.html
- **API Docs (Swagger):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health Check:** http://localhost:8000/api/health

---

## 3. Detaillierte Installation

### 3.1 Python Version prüfen

```bash
python3 --version
# Erwartet: Python 3.10 oder höher

# Falls mehrere Python-Versionen installiert sind:
which python3
python3 -c "import sys; print(sys.version)"
```

### 3.2 Virtual Environment Details

Das Projekt verwendet ein Python `venv` für Isolation:

```bash
# Erstellen (einmalig)
python3 -m venv venv

# Aktivieren
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Deaktivieren
deactivate

# Prüfen ob aktiv
which python  # Sollte auf venv/bin/python zeigen
```

### 3.3 Abhängigkeiten verwalten

**requirements.txt Struktur:**

| Kategorie | Pakete | Zweck |
|-----------|--------|-------|
| **Core** | fastapi, uvicorn, sqlalchemy | Web Framework & ORM |
| **Auth** | python-jose, bcrypt | JWT & Password Hashing |
| **Scheduling** | apscheduler | Game Tick Scheduler (1h Intervall) |
| **Monitoring** | prometheus-client | Metrics Endpoint |
| **Security** | slowapi | Rate Limiting Middleware |
| **Production** | gunicorn | WSGI/ASGI Server für Production |
| **Dev/Test** | pytest, httpx, python-dotenv | Testing & Env Management |

### 3.4 Datenbank-Initialisierung

Die SQLite-Datenbank `verbrannte_zone.db` wird automatisch beim ersten Serverstart erstellt. Alle SQLAlchemy Models werden via `Base.metadata.create_all()` migriert.

**Wichtig:** Foreign Key Constraints sind aktiviert (`PRAGMA foreign_keys=ON`) in `app/database.py`.

---

## 4. Projektstruktur

```
Wasteland/
├── app/                          # Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py                   # FastAPI App Entry Point
│   ├── config.py                 # Environment Configuration
│   ├── database.py               # DB Connection & SQLAlchemy Setup
│   ├── models.py                 # 44 SQLAlchemy Model-Klassen
│   │
│   ├── api/                      # API Endpoints
│   │   ├── __init__.py           # Router Aggregation
│   │   ├── auth.py               # Login, Register, JWT Tokens
│   │   ├── world.py              # Weltkarte, Terrain
│   │   ├── province.py           # Provinz-Management (34KB)
│   │   ├── market.py             # Markt, Kontor, Handelsrouten (15KB)
│   │   ├── army.py               # Armeen-Management
│   │   ├── gamelog.py            # Spiel-Logbuch
│   │   ├── help.py               # Hilfe/Wiki
│   │   ├── health.py             # Health Check Endpoint
│   │   ├── metrics.py            # Prometheus Metrics
│   │   ├── openapi_docs.py       # OpenAPI Dokumentation
│   │   ├── orm_helpers.py        # ORM Konverter
│   │   ├── messages.py           # Spieler-Nachrichten
│   │   └── admin/                # Admin-API (10 Module)
│   │       ├── __init__.py
│   │       ├── users.py          # User-Management + CSRF-Token
│   │       ├── dashboard.py      # Admin Dashboard Stats
│   │       ├── players.py        # Spieler-Verwaltung
│   │       ├── armies.py         # Armeen-Admin
│   │       ├── gamelog.py        # Admin Gamelog
│   │       ├── broadcast.py      # Broadcast-Nachrichten
│   │       ├── data_editors.py   # Daten-Editoren
│   │       ├── world.py          # Weltkarten-Admin
│   │       ├── city_grid.py      # Stadt-Gitter Admin
│   │       └── ticks.py          # Tick-Engine Control
│   │
│   ├── middleware/               # Middleware
│   │   ├── error_tracking.py     # Error Tracking
│   │   ├── rate_limiting.py      # Rate Limiting
│   │   └── csrf_protection.py    # CSRF Token System (NEU)
│   │
│   └── *_logic.py                # Game Logic Modules (20+ Dateien)
│       ├── tick_logic.py         # Haupt-Spielschleife (1h Ticks)
│       ├── combat_logic.py       # Kampfsystem mit Transaction-Rollback (NEU)
│       ├── building_logic.py     # Gebäude-Bau
│       ├── military_logic.py     # Militär-Logik
│       ├── diplomacy_logic.py    # Diplomatie-System
│       ├── finance_logic.py      # Finanzsystem
│       ├── market_logic.py       # Markt-Logik
│       ├── population_logic.py   # Bevölkerungs-Simulation
│       ├── regierungsform_logic.py # Regierungsformen
│       ├── trade_route_logic.py  # Handelsrouten (15KB)
│       ├── siedler_logic.py      # Siedler-Logik (14KB)
│       ├── bunker_logic.py       # Bunker-Mechanik
│       ├── animal_logic.py       # Tier-Simulation
│       ├── sammler_jaeger_logic.py # Sammeln/Jagen
│       ├── kultur_bildung_logic.py # Kultur & Bildung
│       ├── road_logic.py         # Straßennetz
│       └── round_logic.py        # Runden-Logik
│
├── seeds/                        # Datenbank-Seed-Daten
│   ├── db_config.py              # DB Helper (save_entity)
│   ├── seed_main.py              # Orchestrator für alle Seeds
│   ├── seed_terrains.py          # 16 Terrain-Typen (32KB)
│   ├── seed_gebaeude.py          # ~200 Gebäude-Typen (199KB!)
│   ├── seed_ressourcen.py        # ~100 Ressourcen (56KB)
│   ├── seed_vorkommen.py         # ~20 Vorkommen
│   ├── seed_einheiten.py         # ~20 Einheiten-Typen
│   ├── seed_lebewesen.py         # 8 Lebewesen (NEU erweitert)
│   ├── seed_artikel.py           # 15 Artikel/Equipment (NEU erweitert)
│   └── seed_regierungsformen.py  # 7 Regierungsformen (NEU erweitert)
│
├── webcrawler/                   # Web Crawler für externe Daten
│   ├── main.py
│   ├── config.py
│   ├── scraper/                  # Fetcher, Parser, Image Downloader
│   ├── parsers/                  # HTML Parser für verschiedene Typen
│   ├── db/                       # Database Connection & Sync
│   └── cache/                    # Gecachte HTML-Seiten (400+ Dateien)
│
├── js/                           # Frontend JavaScript
│   ├── auth-service.js           # JWT Token Management
│   ├── app.js                    # Hauptanwendungslogik
│   ├── province.js               # Provinz-UI
│   ├── worldmap.js               # Weltkarten-Rendering
│   ├── buildings-data.js         # Gebäude-Daten
│   ├── terrain-types.js          # Terrain-Typen
│   ├── transport.js              # Transport-Logik
│   ├── onboarding.js             # Onboarding-Assistent
│   └── province_grid.js          # Provinz-Gitter UI
│
├── admin/                        # Admin Panel (HTML/CSS/JS)
│   ├── admin.html                # Admin Dashboard (146KB!)
│   ├── resources.html            # Ressourcen-Verwaltung
│   ├── styles.css                # Admin Styling
│   └── js/                       # Admin-spezifisches JS
│       ├── market.js
│       └── resources.js
│
├── css/                          # Globales CSS
│   └── style.css                 # Haupt-Styling
│
├── tests/                        # pytest Test-Suite
│   ├── conftest.py               # Fixtures (DB, Client, Tokens)
│   ├── test_api_quick.py         # Schnelle API-Tests (Health, Auth)
│   └── test_orm_comprehensive.py # 16 ORM-Tests (NEU)
│
├── scripts/                      # Wartungsskripte
│   ├── db_migration.py           # Schema-Migration (ALTER TABLE)
│   ├── db_index_migration.py     # Index-Erstellung (39 Indexe, NEU)
│   ├── simulate_4_jahre.py       # 4-Jahres-Simulation
│   └── simulate_6_months.py      # 6-Monats-Simulation
│
├── context/                      # Context-Management (AI-Assistent)
│   ├── blocks/                   # YAML-Konfigurationsblöcke
│   └── converter/                # Markdown zu Blocks Konverter
│
├── docs/                         # Projekt-Dokumentation (89 Markdown-Dateien)
│   ├── 00_implementierungs_roadmap.md
│   ├── 01-37_feature_*.md        # Feature-Dokumentationen (27 Dateien)
│   ├── UEBERARBEITUNGSPLAN_v1.7.md
│   └── ...                       # Weitere Planungs- & Abschlussberichte
│
├── images/                       # Statische Bilder (5 Verzeichnisse)
├── terrains/                     # Terrain-Bilder
│
├── data/                         # Laufzeit-Daten
├── logs/                         # Log-Dateien
│
├── .env                          # Environment Configuration (NICHT committen!)
├── .env.example                  # Template für .env
├── requirements.txt              # Python Abhängigkeiten
├── README.md                     # Kurzeinführung
└── index.html                    # Haupt-Frontend (29KB, mit defer Scripts)
```

---

## 5. Konfiguration

### 5.1 Environment Variables (.env)

Kopiere `.env.example` zu `.env` und passe die Werte an:

```bash
cp .env.example .env
```

**Verfügbare Variablen:**

| Variable | Typ | Standard | Beschreibung |
|----------|-----|----------|--------------|
| `SECRET_KEY` | **Required** | — | JWT Signing Key (min. 32 Bytes, URL-safe) |
| `ALGORITHM` | String | HS256 | JWT Algorithmus |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | 120 | Gültigkeitsdauer Access Token |
| `REFRESH_TOKEN_DAYS` | Integer | 7 | Gültigkeitsdauer Refresh Token |
| `DB_PATH` | String | verbrannte_zone.db | Pfad zur SQLite-Datenbank |
| `HOST` | String | 0.0.0.0 | Bind-Adresse des Servers |
| `PORT` | Integer | 8000 | Port des Servers |
| `LOG_LEVEL` | String | INFO | Logging-Level (DEBUG/INFO/WARNING/ERROR) |
| `PROMETHEUS_ENABLED` | Boolean | false | Prometheus Metrics aktivieren |
| `PROMETHEUS_PORT` | Integer | 9090 | Port für Prometheus Metrics |
| `RATE_LIMIT_REQUESTS` | Integer | 100 | Requests pro Zeitfenster |
| `RATE_LIMIT_WINDOW` | Integer | 60 | Zeitfenster in Sekunden |
| `CORS_ORIGINS` | CSV-Liste | — | Erlaubte CORS-Origin (kommagetrennt) |

### 5.2 SECRET_KEY generieren

```bash
# Methode 1: Python secrets (empfohlen)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Methode 2: OpenSSL
openssl rand -base64 32

# Methode 3: /dev/urandom (Linux)
head -c 32 /dev/urandom | base64
```

**WICHTIG:** Der SECRET_KEY darf niemals committet werden! `.env` steht in `.gitignore`.

### 5.3 Logging konfigurieren

Log-Level in `.env` setzen:
- `DEBUG` — Alle Logs (Entwicklung)
- `INFO` — Standard (Produktion)
- `WARNING` — Nur Warnungen und Fehler
- `ERROR` — Nur Fehler

Logs werden geschrieben nach:
- **Konsole:** stdout/stderr (uvicorn logs)
- **Datei:** `logs/wasteland.log` (immer DEBUG, falls verfügbar)

---

## 6. Datenbank-Setup

### 6.1 Datenbank-Datei

Standardpfad: `./verbrannte_zone.db` (im Projektverzeichnis)

Die Datenbank wird automatisch erstellt beim ersten Serverstart via:
```python
Base.metadata.create_all(bind=engine)
```

### 6.2 SQLAlchemy Models (44 Klassen)

**Haupt-Entities:**
- `Player` — Spieler-Account
- `User` — Login-Daten (verknüpft mit Player)
- `Province` — Provinz (zentrale Entity, 11+ Beziehungen)
- `Army` — Armee mit Einheiten
- `BuildingType` / `BuildingInstance` — Gebäude-Typen und -Instanzen
- `TradeRoute` — Handelsrouten
- `MarketStand` — Marktstände
- `KontorPrice` — Kontor-Preise

**Referenz-Daten:**
- `TerrainType` — 16 Terrain-Typen
- `Resource` — ~100 Ressourcen
- `UnitType` / `ProvinceUnit` — Einheiten-Typen und -Instanzen
- `Vorkommen` — ~20 Vorkommen-Typen
- `Article` — 15 Artikel/Equipment
- `AnimalTemplate` / `ProvinceAnimal` — Tiere
- `Regierungsform` — 7 Regierungsformen

**System-Tabellen:**
- `GameLogEntry` / `GameLog` — Spiel-Logs (Dupliziert!)
- `AdminLog` — Admin-Aktionen
- `TickLog` — Tick-Monitoring
- `SystemLock` — System-Sperren

### 6.3 Datenbank-Migrationen

**Manuelle Migration:**
```bash
python scripts/db_migration.py
```

Dies synchronisiert das SQLAlchemy-Schema mit der SQLite-Datenbank via `ALTER TABLE ADD COLUMN`.

**Index-Migration (NEU):**
```bash
python scripts/db_index_migration.py
```

Erstellt 39 Performance-Indexe auf FK-Spalten. Idempotent — prüft vor Erstellung.

### 6.4 Seeds ausführen

**Alle auf einmal:**
```bash
python seeds/seed_main.py
```

**Einzeln (empfohlen für Debugging):**
```bash
python seeds/seed_terrains.py       # 16 Terrains
python seeds/seed_gebaeude.py       # ~200 Gebäude
python seeds/seed_ressourcen.py      # ~100 Ressourcen
python seeds/seed_vorkommen.py      # ~20 Vorkommen
python seeds/seed_einheiten.py       # ~20 Einheiten
python seeds/seed_lebewesen.py       # 8 Lebewesen (NEU: +6)
python seeds/seed_artikel.py        # 15 Artikel (vollständig)
python seeds/seed_regierungsformen.py # 7 Regierungsformen (vollständig)
```

**Hinweis:** Seeds verwenden `save_entity()` aus `db_config.py`, das INSERT/UPDATE intelligent handhabt.

---

## 7. Server starten

### 7.1 Development Mode

```bash
# Mit Hot Reload (Empfohlen für Entwicklung)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Mit spezifischem Log-Level
uvicorn app.main:app --reload --log-level debug
```

**Vorteile:**
- Automatischer Neustart bei Code-Änderungen
- Detaillierte Fehlermeldungen
- Interaktiver Debugger möglich

### 7.2 Production Mode

```bash
# uvicorn (einfach)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1

# Gunicorn (empfohlen für Production)
gunicorn app.main:app \
    -w 4 \                          # Worker-Anzahl (CPU-Kerne)
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000

# Mit Logfile
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile logs/access.log \
    --error-logfile logs/error.log
```

### 7.3 Docker (optional)

```bash
# Dockerfile vorhanden, aber nicht vollständig konfiguriert
docker build -t wasteland .
docker run -p 8000:8000 --env-file .env wasteland
```

### 7.4 Systemd Service (Linux Production)

Erstelle `/etc/systemd/system/wasteland.service`:

```ini
[Unit]
Description=Wasteland Browser Game Server
After=network.target

[Service]
Type=simple
User=fabian
WorkingDirectory=/home/fabian/Wasteland
Environment=PATH=/home/fabian/Wasteland/venv/bin
ExecStart=/home/fabian/Wasteland/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Aktivieren und starten:
```bash
sudo systemctl daemon-reload
sudo systemctl enable wasteland
sudo systemctl start wasteland
sudo systemctl status wasteland
```

---

## 8. API-Endpunkte Übersicht

### 8.1 Authentication (`/auth`)

| Methode | Pfad | Beschreibung | Auth Required |
|---------|------|--------------|---------------|
| POST | `/auth/register` | Benutzer registrieren | Nein |
| POST | `/auth/login` | Login (JWT Tokens) | Nein |
| POST | `/auth/refresh` | Access Token refresh | Ja (Refresh Token) |
| POST | `/auth/logout` | Logout (Client-seitig) | Ja |
| POST | `/auth/forgot-password` | Password Reset anfragen | Nein |
| POST | `/auth/reset-password` | Password zurücksetzen | Ja (Reset Token) |

**Response Format:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "role": "player|admin",
  "username": "player123",
  "player_id": 42
}
```

### 8.2 World (`/world`)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/world/map` | Weltkarten-Daten |
| GET | `/world/buildings` | Alle Gebäude-Typen |

### 8.3 Province (`/province/{id}`)

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/{id}/market/stands` | Marktstände (N+1 behoben via joinedload) |
| POST | `/{id}/market/stands` | Marktstand erstellen |
| DELETE | `/{id}/market/stands/{resource_id}` | Marktstand auflösen |
| GET | `/{id}/market/preview` | Marktvorschau |
| GET | `/{id}/kontor/prices` | Kontor-Preise |
| POST | `/{id}/kontor/prices` | Kontor-Preis setzen |
| DELETE | `/{id}/kontor/prices/{price_id}` | Kontor-Preis löschen |
| GET | `/{id}/kontor/balance` | Handelskonto-Saldo |
| POST | `/{id}/kontor/trade` | Kontor-Handel ausführen |
| POST | `/{id}/trade-route/create` | Handelsroute erstellen |

### 8.4 Admin (`/admin`)

**CSRF-Schutz aktiv!** Alle state-modifying Requests benötigen `X-CSRF-Token` Header.

**CSRF-Token abrufen:**
```bash
curl http://localhost:8000/admin/csrf-token
# {"csrf_token": "abc123..."}
```

**Admin-Endpunkte:**

| Bereich | Methoden | Pfad | Beschreibung |
|---------|----------|------|--------------|
| **Dashboard** | GET | `/admin/dashboard` | KPIs, Warnungen, Inaktivitätsliste |
| **Users** | GET/POST | `/admin/users` | User-Verwaltung |
| **Players** | GET | `/admin/players` | Spieler-Liste |
| | POST | `/admin/player/{id}/reset` | Account zurücksetzen |
| | POST | `/admin/player/{id}/tech` | Tech-Level setzen |
| | POST | `/admin/player/{id}/mips` | MIPS zuschreiben |
| **Armies** | GET/POST | `/admin/armies` | Armeen verwalten |
| | DELETE | `/admin/armies/{id}` | Armee löschen |
| **Gamelog** | GET | `/admin/log` | Admin-Logbuch |
| **Broadcast** | POST | `/admin/broadcast` | Broadcast-Nachricht senden |
| **World Map** | GET/POST | `/admin/world/*` | Weltkarten-Editor |
| **City Grid** | GET/POST | `/admin/city_grid/*` | Stadt-Gitter Config |
| **Ticks** | GET/POST | `/admin/ticks/*` | Tick-Engine Control |
| **Data Editors** | GET/POST | `/admin/*` | Ressourcen, Terrain, Gebäude editieren |

### 8.5 System Endpoints

| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/api/health` | Health Check (DB, Uptime) |
| GET | `/api/ready` | Ready State (Scheduler Status) |
| GET | `/api/version` | Versionsinfo (`1.7-dev`) |
| GET | `/api/metrics` | Prometheus Metrics (Text Format) |

---

## 9. Frontend-Nutzung

### 9.1 Hauptseite (`index.html`)

**Zugriff:** http://localhost:8000

**Features:**
- Weltkarten-Rendering (Canvas-basiert)
- Provinz-Management UI
- Gebäude-Bau Interface
- Handelsrouten-Verwaltung
- Gamelog-Anzeige

**Performance-Optimierung (NEU):**
- Alle externen JS-Dateien mit `defer` geladen → blockieren Seitenrendering nicht
- Auth-Check in `DOMContentLoaded` verschoben
- Inline CSS für Onboarding-Overlay (< 3.5KB)

### 9.2 Admin Panel (`admin.html`)

**Zugriff:** http://localhost:8000/admin.html

**Voraussetzung:** Admin-Login erforderlich.

**Tabs:**
1. **Dashboard** — KPIs, Revolten-Risiko, Hunger-Alarme, Inaktivität
2. **City Grid** — Stadt-Gitter Config (Level 1-8)
3. **Players List** — Spieler verwalten, Reset, Tech-Level, MIPS
4. **Broadcast** — Nachrichten an alle Spieler senden
5. **Gamelog** — Admin-Logbuch einsehen
6. **Buildings** — Gebäude-Typen verwalten
7. **Ressourcen** — Rohstoffe editieren
8. **Regierungsformen** — Regierungsformen anpassen
9. **World Map** — Weltkarte zeichnen/bearbeiten
10. **Terrain** — Terrain-Typen verwalten
11. **Vorkommen** — Vorkommen editieren
12. **Einheiten** — Einheiten-Typen verwalten
13. **Lebewesen** — Tiere/Lebewesen verwalten
14. **Gebäude-Felder** — Feld-Config (Größe, Farbe)
15. **Artikel** — Equipment/Transport verwalten
16. **Ticks** — Tick-Engine Status & History
17. **Audit Logs** — Admin-Aktionen protokolliert

### 9.3 JavaScript Module

| Datei | Größe | Zweck |
|-------|-------|-------|
| `auth-service.js` | ~4KB | JWT Token Management, Fetch Wrapper |
| `app.js` | Groß | Hauptanwendungslogik |
| `province.js` | Mittel | Provinz-UI |
| `worldmap.js` | Groß | Weltkarten-Rendering |
| `buildings-data.js` | Mittel | Gebäude-Datenbank im Client |
| `terrain-types.js` | Klein | Terrain-Typen |
| `transport.js` | Klein | Transport-Logik |
| `onboarding.js` | Klein | Onboarding-Assistent |
| `province_grid.js` | Mittel | Provinz-Gitter UI |

---

## 10. Admin-Bereich

### 10.1 Admin erstellen

```bash
# Server starten, dann im Browser:
# 1. Zu http://localhost:8000/register gehen
# 2. Benutzer registrieren (z.B. "admin")
# 3. In der Datenbank die Rolle auf "admin" setzen:

python3 -c "
import sqlite3
conn = sqlite3.connect('verbrannte_zone.db')
cur = conn.cursor()
cur.execute(\"UPDATE users SET role='admin' WHERE username='admin'\")
conn.commit()
conn.close()
print('Admin role assigned.')
"
```

### 10.2 CSRF-Token System (NEU)

**Warum?** Schutz vor Cross-Site Request Forgery Angriffen auf Admin-Funktionen.

**Funktionsweise:**
1. Admin-Panel ruft beim Laden `/admin/csrf-token` ab
2. Token wird im Client gespeichert (`csrfToken` Variable)
3. Alle POST/PUT/DELETE Requests senden `X-CSRF-Token: <token>` Header
4. Server validiert Token und löscht ihn nach einmaliger Verwendung (one-time use)

**Fehlerbehandlung:**
- Fehlender Token → 403 Forbidden
- Ungültiger/abgelaufener Token → 403 Forbidden
- Automatischer Retry nach neuem Token-Abruf

### 10.3 Admin-API Authentifizierung

Admin-Endpoints verwenden JWT Token als Query Parameter:
```
GET /admin/dashboard?token=<jwt_token>
POST /admin/users?token=<jwt_token>
```

**Sicherheits-Hinweis:** Token in URLs sind weniger sicher als Header. In zukünftigen Versionen sollte auf Header-Umstellung migriert werden.

---

## 11. Tests ausführen

### 11.1 pytest Konfiguration

```bash
# Alle Tests
./venv/bin/python -m pytest tests/ -v

# Nur schnelle API-Tests
./venv/bin/python -m pytest tests/test_api_quick.py -v

# Nur ORM-Tests
./venv/bin/python -m pytest tests/test_orm_comprehensive.py -v

# Mit Coverage (optional)
./venv/bin/python -m pytest tests/ --cov=app --cov-report=html
```

### 11.2 Test-Suite Übersicht

**test_api_quick.py (8 Tests):**
- Health Check Endpoint
- Ready State Endpoint
- Version Endpoint
- Metrics Endpoint
- User Registration
- User Login
- World Map Endpoint
- World Buildings Endpoint
- Gamelog Endpoint

**test_orm_comprehensive.py (16 Tests):**
- Province CRUD (create, update, delete)
- Building System (BuildingType, BuildingInstance)
- Seed Data Integrity (Terrain, Building, Resource Models)
- Army System
- Storage & Market (Lager, Markt-Stände)
- Trade Routes
- Population Cohorts
- Game Log & Admin Log
- Index Verification (auf realer DB)

**test_api_quick.py (9 Tests):**
- Health Check Endpoint
- Ready State Endpoint
- Version Endpoint
- Metrics Endpoint
- User Registration
- User Login
- World Map Endpoint
- World Buildings Endpoint
- Gamelog Endpoint

**test_core_logic.py (19 Tests, NEU):**
- Gamelog Visibility Logic (3 Tests)
- Combat System (2 Tests)
- Tick Engine (1 Test)
- Building Logic (3 Tests)
- Market Logic (2 Tests)
- Animal Logic (2 Tests)
- Diplomacy/Finance (2 Tests)
- Round/Config/Helpers (4 Tests)

**Test-Datenbank:** In-Memory SQLite (`:memory:`), keine Auswirkungen auf Produktionsdaten.

### 11.3 Tests erfolgreich ausführen

```bash
cd /home/fabian/Wasteland
./venv/bin/python -m pytest tests/ -v

# Erwartet: 44 passed, 0 failed
```

---

## 12. Offene Punkte & Mängel

### 🔴 Kritisch (Sofortige Aufmerksamkeit erforderlich)

#### 1. GameLog / GameLogEntry Duplikat
**Datei:** `app/models.py` (Zeilen 90-114)  
**Problem:** Zwei fast identische Logging-Tabellen existieren parallel:
- `GameLog` (game_logs) — mit timestamp, event_type, message, province_id, player_id
- `GameLogEntry` (gamelog_entries) — mit event_type, province_id, player_id, message, visibility

**Auswirkung:** Daten werden in beiden Tabellen geschrieben (je nach Code-Pfad), was zu Inkonsistenzen führt.

**Empfohlene Lösung:**
```python
# Option A: GameLogEntry deprecated markieren und Migration erstellen
class GameLogEntry(Base):
    __tablename__ = 'gamelog_entries'
    # ... bestehende Felder ...
    deprecated = Column(Boolean, default=True)  # Markierung

# Option B: GameLogEntry vollständig entfernen und alle Referenzen auf GameLog umstellen
```

**Aufwand:** Mittel — erfordert Datenbank-Migration und Code-Review aller Log-Schreibzugriffe.

---

#### 2. Seed-Daten Inkonsistenz
**Dateien:** `seeds/seed_*.py`  
**Problem:** Die Seeds definieren nicht alle Daten, die in der Datenbank existieren. Umgekehrt enthält die Datenbank Einträge, die nicht in den Seeds definiert sind.

**Beispiel:**
- `seed_artikel.py` definierte nur 4 Artikel, Datenbank hatte 15 → Jetzt korrigiert auf 15
- `seed_lebewesen.py` definierte nur 2 Lebewesen, Datenbank hatte 2 → Jetzt erweitert auf 8
- `seed_regierungsformen.py` definierte nur 2, Datenbank hatte 7 → Jetzt vollständig

**Empfohlene Lösung:**
```python
# Alle Seeds sollten als "Single Source of Truth" gelten:
# 1. Datenbank leer machen (oder Backup!)
# 2. Alle Seeds ausführen
# 3. Datenbank-Export als Referenz speichern
```

**Aufwand:** Hoch — erfordert manuelle Synchronisation aller Seed-Dateien mit existierenden Daten.

---

#### 3. Fehlende Tests für Kernfunktionalität
**Datei:** `tests/`  
**Problem:** Nur 24 Tests existieren, davon decken nur ~5% die Kernspielmechaniken ab.

**Nicht getestete Bereiche:**
- Province CRUD (manuell, nicht via API)
- Building System (API-Ebene)
- Trade Route Logic
- Combat System (außer ORM-Tests)
- Diplomacy System
- Economy/Finance Logic
- Seed Data Integrity (nur Model-Tests, keine Daten-Integrität)

**Empfohlene Lösung:**
```python
# Priorisierte Test-Erweiterung:
tests/test_api_province.py      # Province API CRUD
tests/test_api_buildings.py     # Building API
tests/test_api_trade_routes.py   # Trade Route API
tests/test_combat_logic.py      # Combat Calculation Tests
tests/test_diplomacy_api.py     # Diplomacy API
```

**Aufwand:** Hoch — erfordert Test-Infrastruktur für komplexe Spielzustände.

---

### 🟡 Hoch (Nächste Iteration)

#### 4. N+1 Query Pattern in weiteren Endpoints
**Datei:** `app/api/market.py` (bereits teilweise behoben)  
**Problem:** Weitere API-Endpunkte laden Beziehungen lazy, was zu N+1 Queries führt.

**Betroffene Endpoints (Beispiele):**
- `get_kontor_prices()` — lädt `p.resource.name` pro Eintrag
- `create_trade_route()` — prüft Destination Province ohne eager loading

**Empfohlene Lösung:**
```python
from sqlalchemy.orm import joinedload, selectinload

# Beispiel: Kontor-Preise mit Resource eager load
prices = db.query(KontorPrice).options(
    joinedload(KontorPrice.resource)
).filter(...).all()
```

**Aufwand:** Mittel — erfordert Code-Review aller API-Endpoints.

---

#### 5. Veraltete SQLAlchemy API
**Datei:** `app/database.py` (Zeile 25)  
**Problem:** `declarative_base()` ist seit SQLAlchemy 2.0 veraltet.

```python
# Alt (veraltet):
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

# Neu (empfohlen):
from sqlalchemy.orm import declarative_base
Base = declarative_base()
```

**Auswirkung:** Keine funktionale Beeinträchtigung, aber Warnungen in Logs.

**Aufwand:** Niedrig — 1 Zeile ändern.

---

#### 6. Admin-Auth über Query Parameter
**Datei:** `app/api/admin/*.py`  
**Problem:** Alle Admin-Endpoints verwenden Token als Query Parameter:
```python
def get_users(token: str = Query(..., description="JWT Token")):
```

**Sicherheitsrisiko:**
- Token erscheinen in Server-Logs (URLs werden geloggt)
- Token können im Browser-Verlauf erscheinen
- Token können in Proxy-Logs gespeichert werden

**Empfohlene Lösung:**
```python
from fastapi import Header

def get_users(x_csrf_token: str = Header(...), 
              token: str = Header(...)):
    # Token aus Header lesen, nicht aus Query
```

**Aufwand:** Mittel — erfordert Änderung aller Admin-Endpoints und Frontend-Anpassung.

---

#### 7. Unoptimierte Bildladungen im Frontend
**Datei:** `index.html`  
**Problem:** Bilder werden dynamisch per JS geladen, aber ohne lazy loading oder WebP-Konvertierung.

**Empfohlene Lösung:**
```javascript
// Lazy Loading für dynamisch geladene Bilder
const img = new Image();
img.loading = 'lazy';  // Native lazy loading
img.src = imageUrl;

// Oder: WebP konvertieren für kleinere Dateigrößen
```

**Aufwand:** Mittel — erfordert Bildkonvertierung und JS-Änderungen.

---

### 🟢 Mittel (Technische Schulden)

#### 8. Fehlende Fehlerbehandlung in Logik-Modulen
**Dateien:** `app/*_logic.py`  
**Problem:** Viele Funktionen haben keine explizite Fehlerbehandlung. Bei ungültigen Daten oder unerwarteten Zuständen crasht die Funktion und rollt keine Transaktion zurück.

**Beispiel:** `combat_logic.py` — Transaction-Rollback bei Fehlern implementiert ✅, aber auch:
- `building_logic.py` — kein Rollback bei fehlgeschlagenem Bau
- `finance_logic.py` — keine Validierung von Kontoständen
- `trade_route_logic.py` — kein Rollback bei fehlgeschlagenem Handel

**Empfohlene Lösung:**
```python
def safe_operation(db: Session, operation_func):
    try:
        result = operation_func(db)
        db.commit()
        return result
    except Exception as e:
        db.rollback()
        logging.error(f"Operation failed: {e}")
        raise
```

**Aufwand:** Hoch — erfordert Review aller 20+ Logic-Module.

---

#### 9. Keine CI/CD Pipeline
**Problem:** Kein automatisiertes Testing, Linting oder Deployment.

**Empfohlene Lösung:**
```yaml
# .github/workflows/test.yml (GitHub Actions Beispiel)
name: Test
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/ -v
```

**Aufwand:** Mittel — erfordert GitHub Repository und Workflow-Konfiguration.

---

#### 10. Dokumentation veraltet/inkonsistent
**Dateien:** `docs/*.md` (89 Dateien)  
**Problem:** Viele Feature-Dokumentationen beschreiben implementierte Features nicht korrekt oder erwähnen nicht-implementierte Features.

**Gefundene Inkonsistenzen:**
- `24_feature_weltgenerierung.md` — Documented WorldMap/WorldProvince, aber keine Modelle in models.py
- `31_feature_onboarding.md` — Dokumentiert, aber Onboarding-Logik unvollständig
- `32_feature_notfallreserve.md` — Dokumentiert, aber keine Emergency Reserve Logic gefunden
- `33_feature_cleanup.md` — Documented, aber keine Cleanup/Prune Logic gefunden
- `35_feature_prov_tags.md` — Documented, aber keine Province Tag Implementation

**Empfohlene Lösung:**
```bash
# Gap-Report erstellen:
python scripts/doc_gap_analysis.py

# Veraltete Docs kennzeichnen oder aktualisieren
```

**Aufwand:** Hoch — erfordert manuelle Prüfung aller 89 Markdown-Dateien.

---

#### 11. Kein Database Backup System
**Problem:** Keine automatisierten Backups der SQLite-Datenbank.

**Empfohlene Lösung:**
```bash
#!/bin/bash
# scripts/backup_db.sh
BACKUP_DIR="/backups/wasteland"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
cp verbrannte_zone.db "$BACKUP_DIR/db_$TIMESTAMP.db"

# Cron Job (täglich um 3 Uhr)
0 3 * * * /home/fabian/Wasteland/scripts/backup_db.sh
```

**Aufwand:** Niedrig — Skript + Cron Job.

---

#### 12. Prometheus Metrics nicht vollständig integriert
**Datei:** `app/api/metrics.py`  
**Problem:** Prometheus Endpoint existiert, aber keine Custom Metrics für Spiel-KPIs.

**Empfohlene Erweiterung:**
```python
from prometheus_client import Counter, Gauge, Histogram

# Custom Metrics:
PROVINCE_COUNT = Gauge('wasteland_provinces_total', 'Total provinces')
ACTIVE_PLAYERS = Gauge('wasteland_active_players', 'Active players today')
COMBAT_COUNT = Counter('wasteland_combats_total', 'Total combats executed')
TICK_DURATION = Histogram('wasteland_tick_duration_seconds', 'Tick execution time')
```

**Aufwand:** Mittel — erfordert Metric-Definition und Integration in Logik.

---

### ℹ️ Informationell (Keine sofortige Aktion erforderlich)

#### 13. Large Seed Files
**Datei:** `seeds/seed_gebaeude.py` (199KB!)  
**Hinweis:** Diese Datei enthält ~200 Gebäude-Einträge inline. Erwägen Aufteilung in JSON-Datei oder externe Quelle.

#### 14. Admin HTML Größe
**Datei:** `admin.html` (146KB)  
**Hinweis:** Monolithische HTML-Datei. Erwägen Aufteilung in Template-System (Jinja2) oder SPA-Architektur.

#### 15. Webcrawler Cache
**Verzeichnis:** `webcrawler/cache/` (400+ HTML-Dateien)  
**Hinweis:** Gecachte HTML-Seiten belegen Speicher. Erwägen Bereinigungs-Routine oder Redis-Cache.

#### 16. Deprecated Column Names
**Datei:** `app/models.py`  
**Hinweis:** Einige Spalten verwenden veraltete Namen (z.B. `aufwertungen` statt `aufwertungen_json`). Konsistenz prüfen.

---

## 13. Troubleshooting

### 13.1 Häufige Fehler

**Fehler:** `ModuleNotFoundError: No module named 'sqlalchemy'`  
**Lösung:** Virtual Environment aktivieren und `pip install -r requirements.txt` ausführen.

```bash
source venv/bin/activate
pip install -r requirements.txt
```

---

**Fehler:** `ValueError: SECRET_KEY environment variable is required!`  
**Lösung:** `.env` Datei erstellen und SECRET_KEY setzen.

```bash
cp .env.example .env
# EDIT .env and set SECRET_KEY to a secure random value
```

---

**Fehler:** `sqlite3.OperationalError: no such table: ...`  
**Lösung:** Datenbank initialisieren oder Seeds ausführen.

```bash
# Server starten (erstellt DB automatisch)
uvicorn app.main:app --reload

# Oder Seeds manuell ausführen
python seeds/seed_main.py
```

---

**Fehler:** `403 Forbidden` bei Admin-Endpoints  
**Lösung:** CSRF-Token abrufen und im Header senden.

```javascript
// Frontend:
const csrfRes = await fetch('/admin/csrf-token');
const { csrf_token } = await csrfRes.json();

// Bei POST/PUT/DELETE Requests:
headers: { 'X-CSRF-Token': csrf_token }
```

---

**Fehler:** `PendingRollbackError: This Session's transaction has been rolled back`  
**Lösung:** Session.rollback() aufrufen vor neuer Transaktion.

```python
try:
    db.commit()
except Exception as e:
    db.rollback()  # Wichtig!
    logging.error(f"Database error: {e}")
    raise
```

---

### 13.2 Performance-Probleme

**Problem:** Langsame API-Responses (>1s)  
**Ursache:** N+1 Queries, fehlende Indexes, große JSON-Payloads

**Lösung:**
```bash
# 1. Indexes prüfen/erstellen
python scripts/db_index_migration.py

# 2. Query Logging aktivieren (development)
uvicorn app.main:app --reload --log-level debug

# 3. Eager Loading in API-Endpoints verwenden
from sqlalchemy.orm import joinedload
```

---

**Problem:** Hohe CPU-Auslastung durch Game Ticks  
**Ursache:** Tick-Interval zu kurz, komplexe Berechnungen

**Lösung:**
```python
# In app/main.py: Scheduler Interval erhöhen
scheduler.add_job(scheduled_tick, 'interval', hours=2, id='server_tick_job')
# Standard: 1 Stunde (empfohlen für Production)
```

---

### 13.3 Datenbank-Probleme

**Problem:** Datenbank-Datei wächst schnell (>500MB)  
**Ursache:** GameLog/GameLogEntry Duplikat, keine Bereinigung

**Lösung:**
```bash
# Datenbank komprimieren
sqlite3 verbrannte_zone.db "VACUUM;"

# Alte Logs bereinigen (manuell oder Cron Job)
sqlite3 verbrannte_zone.db "DELETE FROM gamelog_entries WHERE created_at < date('now', '-30 days');"
```

---

**Problem:** Foreign Key Violations  
**Ursache:** FK-Constraints aktiv, aber referenzielle Integrität nicht gewährleistet

**Lösung:**
```python
# FK-Constraints prüfen (sollte ON sein in database.py)
PRAGMA foreign_keys = ON;

# Orphaned Records finden und bereinigen
sqlite3 verbrannte_zone.db "
  SELECT * FROM provinzen 
  WHERE player_id NOT IN (SELECT id FROM players);
"
```

---

## Anhang A: Quick Reference Commands

```bash
# Server starten (Development)
uvicorn app.main:app --reload

# Server starten (Production)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Seeds ausführen
python seeds/seed_main.py

# Datenbank migrieren
python scripts/db_migration.py

# Indexe erstellen
python scripts/db_index_migration.py

# Tests ausführen
./venv/bin/python -m pytest tests/ -v

# Datenbank komprimieren
sqlite3 verbrannte_zone.db "VACUUM;"

# SECRET_KEY generieren
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Admin erstellen
python3 -c "
import sqlite3
conn = sqlite3.connect('verbrannte_zone.db')
cur = conn.cursor()
cur.execute(\"UPDATE users SET role='admin' WHERE username='admin'\")
conn.commit()
"
```

---

## Anhang B: Wichtige Dateipfade

| Datei | Pfad | Zweck |
|-------|------|-------|
| Haupt-App | `app/main.py` | FastAPI Entry Point |
| Config | `app/config.py` | Environment Variables |
| Database | `app/database.py` | DB Connection & SQLAlchemy 2.0 |
| Models | `app/models.py` | 44 Model-Klassen (GameLog deprecated) |
| Auth API | `app/api/auth.py` | Login/Register/JWT |
| Market API | `app/api/market.py` | Markt/Handel (15KB, N+1 behoben) |
| Province API | `app/api/province.py` | Provinz-Management (N+1 optimiert) |
| Admin Gamelog | `app/api/admin/gamelog.py` | Admin-Log (N+1 optimiert) |
| CSRF Protection | `app/middleware/csrf_protection.py` | CSRF Token System |
| Combat Logic | `app/combat_logic.py` | Kampfsystem mit Rollback ✅ |
| Main Seed | `seeds/seed_main.py` | Orchestrator |
| Gamelog Migration | `scripts/migrate_gamelog.py` | GameLog → GameLogEntry ✅ |
| Frontend | `index.html` | Hauptseite (29KB, defer optimiert) |
| Admin Panel | `admin.html` | Admin Dashboard (146KB) |
| Auth Service | `js/auth-service.js` | JWT Token Management |

---

## Anhang D: Test-Suite Übersicht

| Test-Datei | Tests | Beschreibung |
|------------|-------|--------------|
| `tests/test_orm_comprehensive.py` | 16 | ORM CRUD, Seed Data Integrity, Index Verification |
| `tests/test_api_quick.py` | 9 | Health, Auth, World Map, Gamelog Endpoints |
| `tests/test_core_logic.py` | 19 | Core-Logik (Combat, Building, Market, Animal, etc.) |
| **Gesamt** | **44** | **100% bestanden ✅** |

---

## Anhang C: Versionshistorie der letzten Änderungen

**2026-10-13 — Code-Review Implementierungen:**
- ✅ **GameLog Duplikat gelöst:** GameLog als deprecated markiert, Migrationsskript erstellt (`scripts/migrate_gamelog.py`)
- ✅ **N+1 Queries optimiert:** Deposits, Animals, Units Endpoints mit batch loading (`app/api/province.py`)
- ✅ **Admin-Gamelog optimiert:** Player/Province-Namen batch geladen (`app/api/admin/gamelog.py`)
- ✅ **SQLAlchemy 2.0 API:** `declarative_base` von `sqlalchemy.orm` importiert (`app/database.py`)
- ✅ **Core-Tests ergänzt:** 19 Unit-Tests für alle Logik-Module (`tests/test_core_logic.py`)
- ✅ **Gesamt: 44 Tests bestanden** (16 ORM + 9 API Quick + 19 Core Logic)

**2026-10-14 — Offline-Modus & Weltgenerierung:**
- ✅ **Offline-Modus implementiert:** LocalStorage Sync, automatische Synchronisierung beim Wiederverbinden (`app/offline_sync.py`, `app/api/offline_sync.py`, `js/offline-sync.js`)
- ✅ **Weltgenerierung-Dokumentation angepasst:** Dokumentation an aktuelles Schema (`world_map_cells` + `Province`) aktualisiert (`docs/24_feature_weltgenerierung.md`)
- ✅ **Cleanup-Logik implementiert:** Automatische Bereinigung alter Logs, inaktiver Provinzen, verwaister Einträge (`app/cleanup_logic.py`)
- ✅ **Cleanup im Tick integriert:** Einmal täglich um Mitternacht (`app/tick_logic.py`)
- ✅ **Wetter-Dynamik erweitert:** Extreme Wetter-Ereignisse (Dürre, Überschwemmung) mit ~0.1% Wahrscheinlichkeit pro Stunde (`app/climate_logic.py`)
- ✅ **EventType Enum implementiert:** 19 Event-Typen für Gamelog-Sichtbarkeit (`app/models.py`)
- ✅ **determine_visibility aktualisiert:** Nutzt EventType Enum mit Fallback auf String-Vergleich (`app/gamelog_logic.py`)
- ✅ **Onboarding Backend implementiert:** Automatische Start-Provinz-Zuweisung bei Registrierung (`app/onboarding_logic.py`, `app/api/auth.py`)
- ✅ **Abriss-Check API implementiert:** Gebäude abreißen mit 50% Ressourcen-Erstattung (`app/api/province.py`)
- ✅ **Notfallreserve implementiert:** Reserve an MIPS einrichten, automatische Aktivierung bei kritischem Handelskonto (`app/finance_logic.py`)
- ✅ **Provinz-Tags implementiert:** Tags für Provinzen zur Organisation (CRUD API) (`app/api/province_tags.py`, `app/models.py`)
- ✅ **Neue Tests:** 11 Unit-Tests für Cleanup, Onboarding, Wetter, EventType (`tests/test_new_features.py`)
- ✅ **Gesamt: 55 Tests bestanden** (16 ORM + 9 API Quick + 19 Core Logic + 11 New Features)

**2026-10-12 — Vorherige Verbesserungen:**
- ✅ Security: Environment-Variablen für alle Config-Werte (`app/config.py`)
- ✅ Security: CSRF-Schutz für Admin-Panel implementiert
- ✅ Performance: 39 Datenbank-Indexe hinzugefügt
- ✅ Tests: 16 ORM-Tests erstellt (100% bestanden)
- ✅ Seed-Daten: Artikel, Lebewesen, Regierungsformen vervollständigt
- ✅ Daten: SQLite FK-Constraints aktiviert (`PRAGMA foreign_keys=ON`)
- ✅ Performance: N+1 Query Pattern in Market-Endpoint behoben (joinedload)
- ✅ Security: Transaction-Rollback bei Combat-Fehlern implementiert
- ✅ Performance: Frontend JS mit `defer` optimiert

**Vorherige Versionen:**
- v1.6 — Grundlegende Spielmechaniken implementiert
- v1.5 — Admin Panel Overhaul
- v1.4 — Auth System mit JWT

---

**Ende der Dokumentation.**  
Für Fragen oder Probleme wende dich an das Projekt-Team oder erstelle ein Issue im Repository.

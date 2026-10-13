# Wasteland Browser Game — Vollständige Clean-Build Dokumentation

**Version:** 1.8  
**Erstellt:** 2026-10-14  
**Projekt:** Wasteland — Verbrannte Zone (Post-Apokalypse Strategiespiel)  
**Tech-Stack:** FastAPI, SQLAlchemy ORM, SQLite, Vanilla JavaScript

---

## Inhaltsverzeichnis

1. [Projektübersicht](#1-projektübersicht)
2. [Systemvoraussetzungen](#2-systemvoraussetzungen)
3. [Installation & Setup](#3-installation--setup)
4. [Konfiguration](#4-konfiguration)
5. [Datenbank-Setup & Migration](#5-datenbank-setup--migration)
6. [Seed-Daten importieren](#6-seed-daten-importieren)
7. [Server starten](#7-server-starten)
8. [API-Endpunkte Übersicht](#8-api-endpunkte-übersicht)
9. [Frontend-Nutzung](#9-frontend-nutzung)
10. [Admin-Bereich](#10-admin-bereich)
11. [Test-Suite ausführen](#11-test-suite-ausführen)
12. [Detaillierte Architektur](#12-detaillierte-architektur)
13. [Offene Punkte & Mängel](#13-offene-punkte--mängel)
14. [Troubleshooting](#14-troubleshooting)

---

## 1. Projektübersicht

### 1.1 Was ist Wasteland?

Wasteland (Verbrannte Zone) ist ein browserbasiertes Strategiespiel im post-apokalyptischen Setting. Spieler gründen Provinzen in einer zerstörten Welt, verwalten Ressourcen, bauen Gebäude, handeln mit anderen Spielern und kämpfen um Territorium.

### 1.2 Kernfunktionen

| Feature | Status | Beschreibung |
|---------|--------|--------------|
| **Provinz-Management** | ✅ Vollständig | Gebäude bauen, Ressourcen verwalten, Bevölkerung steuern |
| **Handelssystem** | ✅ Vollständig | Marktplatz, Kontor, Handelsrouten mit Karren |
| **Militär** | ✅ Vollständig | Armeen aufstellen, Kämpfe austragen, Diplomatie |
| **Wetter & Klima** | ✅ Vollständig | Dynamisches Wetter mit extremen Events (Dürre, Überschwemmung) |
| **Onboarding** | ✅ Vollständig | Automatische Start-Provinz-Zuweisung bei Registrierung |
| **Offline-Modus** | ✅ Vollständig | LocalStorage-Sync, automatische Synchronisierung beim Wiederverbinden |
| **Cleanup-Logik** | ✅ Vollständig | Automatische Bereinigung alter Logs, inaktiver Provinzen |
| **Notfallreserve** | ✅ Vollständig | MIPS-Reserve mit automatischer Aktivierung bei kritischem Konto |
| **Weltgenerierung** | ✅ Vollständig | Procedural generierte Weltkarte mit verschiedenen Terrains |
| **Admin-Oberfläche** | ✅ Vollständig | Umfassende Verwaltungstools für Server-Administratoren |

### 1.3 Projektstruktur

```
Wasteland/
├── app/                          # FastAPI Backend
│   ├── __init__.py
│   ├── main.py                   # FastAPI Entry Point
│   ├── config.py                 # Konfiguration (ENV-Variablen)
│   ├── database.py               # SQLAlchemy Engine & Session
│   ├── models.py                 # Alle ORM-Modelle (46 Klassen)
│   ├── tick_logic.py             # Server-Tick (stündlich)
│   │
│   ├── api/                      # API-Endpunkte
│   │   ├── __init__.py           # Router-Zusammenführung
│   │   ├── auth.py               # Registrierung, Login, JWT
│   │   ├── province.py           # Provinz-Management (38 KB)
│   │   ├── market.py             # Handel, Marktplatz, Kontor
│   │   ├── player.py             # Spieler-Profile, Einstellungen
│   │   ├── world.py              # Weltkarte, Terrains
│   │   ├── army.py               # Armeen verwalten
│   │   ├── gamelog.py            # Spielereignisse
│   │   ├── messages.py           # Spieler-Nachrichten
│   │   ├── city_grid.py          # Stadtpläne verwalten
│   │   ├── help.py               # Hilfe & Wiki
│   │   ├── health.py             # Health-Check Endpoint
│   │   ├── metrics.py            # Prometheus Metrics
│   │   ├── province_tags.py      # Provinz-Tags (CRUD)
│   │   ├── offline_sync.py       # Offline-Sync API
│   │   └── admin/                # Admin-Endpunkte
│   │       ├── __init__.py
│   │       ├── dashboard.py      # Admin-Dashboard
│   │       ├── users.py          # Benutzer-Verwaltung
│   │       ├── players.py        # Spieler-Management
│   │       ├── gamelog.py        # Gamelog verwalten
│   │       ├── armies.py         # Armeen administrieren
│   │       ├── broadcast.py      # Broadcast-Nachrichten
│   │       ├── ticks.py          # Server-Tick steuern
│   │       └── world.py          # Weltkarte administrieren
│   │
│   ├── middleware/               # Middleware-Komponenten
│   │   ├── csrf_protection.py    # CSRF-Schutz
│   │   ├── error_tracking.py     # Fehler-Tracking
│   │   └── rate_limiting.py      # Rate Limiting
│   │
│   └── *_logic.py                # Game-Logik-Module
│       ├── animal_logic.py       # Wildtiere, Zucht
│       ├── army_logic.py         # Armeen bewegen/kämpfen
│       ├── building_logic.py     # Gebäude bauen/abbrechen
│       ├── bunker_logic.py       # Bunker-System
│       ├── cleanup_logic.py      # Cleanup (Logs, inaktive Provinzen)
│       ├── climate_logic.py      # Wetter & Klima
│       ├── combat_logic.py       # Kampf-Resolution
│       ├── diplomacy_logic.py    # Diplomatie, Allianzen
│       ├── finance_logic.py      # Steuern, Notfallreserve
│       ├── gamelog_logic.py      # Spielereignisse loggen
│       ├── kultur_bildung_logic.py # Kultur, Technologie
│       ├── market_logic.py       # Marktpreise, Nachfrage
│       ├── military_logic.py     # Truppen ausbilden
│       ├── onboarding_logic.py   # Onboarding (Start-Provinz)
│       ├── population_logic.py   # Bevölkerung, Alter, Tod
│       ├── regierungsform_logic.py # Regierungsformen
│       ├── road_logic.py         # Straßen bauen
│       ├── round_logic.py        # Runden-Simulation
│       ├── sammler_jaeger_logic.py # Jagen, Sammeln
│       ├── siedler_logic.py      # Siedler-Expeditionen
│       └── trade_route_logic.py  # Handelsrouten
│
├── seeds/                        # Datenbank-Seed-Skripte
│   ├── seed_artikel.py           # Artikel (100+ Einträge)
│   ├── seed_einheiten.py         # Einheiten (125+)
│   ├── seed_gebaeude.py          # Gebäude (200+ Einträge)
│   ├── seed_lebewesen.py         # Lebewesen
│   ├── seed_regierungsformen.py  # Regierungsformen (10+)
│   ├── seed_ressourcen.py        # Ressourcen (57 KB)
│   ├── seed_terrains.py          # Terrains (32 KB)
│   ├── seed_vorkommen.py         # Vorkommen/Deposits
│   └── seed_main.py              # Haupt-Seed-Skript
│
├── js/                           # Frontend JavaScript
│   ├── auth-service.js           # JWT-Authentifizierung
│   ├── terrain-types.js          # Terrain-Typen Definition
│   ├── buildings-data.js         # Gebäude-Datenbank (8 KB)
│   ├── app.js                    # Hauptanwendung (43 KB)
│   ├── onboarding.js             # Onboarding-Flow
│   ├── worldmap.js               # Weltkarte rendern
│   ├── province.js               # Provinz-Verwaltung (30 KB)
│   ├── province_grid.js          # Stadtpläne verwalten
│   ├── transport.js              # Transport, Lager
│   └── offline-sync.js           # Offline-Sync Client (7 KB)
│
├── css/                          # Stylesheets
│   └── style.css                 # Globale Styles (19 KB)
│
├── admin/                        # Admin-UI
│   ├── admin.html                # Admin-Oberfläche
│   └── resources.js              # Ressourcen-Verwaltung
│
├── data/                         # Statische Daten
│   └── worldmap.json             # Weltkarte-Daten (688 B)
│
├── scripts/                      # Wartungsskripte
│   ├── db_index_migration.py     # Datenbank-Indizes erstellen
│   ├── db_migration.py           # Schema-Migrationen
│   ├── migrate_gamelog.py        # GameLog-Daten migrieren
│   ├── backup_database.sh        # Datenbank-Backup
│   └── generate_ssl_certs.sh     # SSL-Zertifikate generieren
│
├── tests/                        # Test-Suite
│   ├── conftest.py               # pytest-Konfiguration
│   ├── test_orm_comprehensive.py # ORM-Tests (16 Tests)
│   ├── test_api_quick.py         # API-Schnelltests (9 Tests)
│   ├── test_core_logic.py        # Core-Logik (19 Tests)
│   └── test_new_features.py      # Neue Features (11 Tests)
│
├── docs/                         # Dokumentation
│   ├── SETUP_AND_CLEAN_BUILD.md  # Diese Datei (ersetzt)
│   ├── GAP_REPORT_DOKUMENTATION_VS_CODE.md # Gap-Report
│   └── [weitere Feature-Docs]    # 50+ Dokumentationsdateien
│
├── .env.example                  # Umgebungsvariablen-Vorlage
├── requirements.txt              # Python-Abhängigkeiten
├── Dockerfile                    # Docker-Konfiguration
└── index.html                    # Haupt-Frontend

```

### 1.4 Abhängigkeiten-Übersicht

**Backend (Python):**
- FastAPI 0.112.0 — Web Framework
- SQLAlchemy 2.0.33 — ORM
- APScheduler 3.10.4 — Server-Tick Scheduler
- python-jose 3.3.0 — JWT Token Handling
- bcrypt 4.2.0 — Passwort-Hashing
- Pydantic 2.8.2 — Datenvalidierung
- prometheus-client 0.19.0 — Monitoring
- slowapi 0.1.9 — Rate Limiting
- gunicorn 22.0.0 — Production Server (optional)
- python-dotenv 1.0.1 — ENV-Variablen laden

**Frontend:**
- Vanilla JavaScript (ES6+) — Kein Framework
- Fetch API — HTTP-Anfragen
- LocalStorage — Offline-Sync

---

## 2. Systemvoraussetzungen

### 2.1 Hardware-Anforderungen

| Komponente | Minimum | Empfohlen |
|------------|---------|-----------|
| CPU | 1 Core | 2+ Cores |
| RAM | 512 MB | 1 GB+ |
| Festplatte | 1 GB frei | 5 GB+ (mit DB) |

### 2.2 Software-Anforderungen

| Software | Version | Bemerkung |
|----------|---------|-----------|
| Python | 3.10+ | Erforderlich für f-strings, type hints |
| pip | 21.0+ | Paketmanager |
| Git | 2.30+ | Versionskontrolle (optional) |
| SQLite | 3.35+ | In Python integriert |

### 2.3 Betriebssystem

- **Linux:** Debian 11+, Ubuntu 20.04+, CentOS 8+
- **macOS:** 10.15+ (Catalina oder neuer)
- **Windows:** 10/11 mit WSL2 empfohlen

---

## 3. Installation & Setup

### Schritt 1: Repository klonen oder Dateien kopieren

```bash
# Option A: Von GitHub (wenn Repository vorhanden)
git clone https://github.com/<username>/Wasteland.git
cd Wasteland

# Option B: Lokale Dateien kopieren (bereits vorhanden)
cd /home/fabian/Wasteland  # Oder dein Pfad
```

### Schritt 2: Python Virtual Environment erstellen

```bash
# Python-Version prüfen
python3 --version  # Sollte 3.10+ anzeigen

# Virtual Environment erstellen
python3 -m venv venv

# Virtual Environment aktivieren
source venv/bin/activate

# Bestätigung: Der Prompt sollte jetzt (venv) anzeigen
(venv) $ python --version
Python 3.10.x
```

### Schritt 3: Python-Abhängigkeiten installieren

```bash
# Alle Abhängigkeiten aus requirements.txt installieren
pip install -r requirements.txt

# Erwartete Installationen:
#   fastapi==0.112.0
#   uvicorn[standard]==0.30.3
#   sqlalchemy==2.0.33
#   apscheduler==3.10.4
#   python-jose[cryptography]==3.3.0
#   bcrypt==4.2.0
#   pydantic==2.8.2
#   prometheus-client==0.19.0
#   slowapi==0.1.9
#   gunicorn==22.0.0 (optional)
#   python-dotenv==1.0.1
#   pytest==9.0.3 (für Tests)
#   httpx==0.28.1 (für Tests)

# Installation verifizieren
pip list | grep -E "fastapi|sqlalchemy|uvicorn"
```

### Schritt 4: SSL-Zertifikate generieren (für lokale Entwicklung)

```bash
# SSL-Zertifikate für HTTPS erstellen
./scripts/generate_ssl_certs.sh

# Erzeugte Dateien:
#   ssl/cert.pem  — Zertifikat (2 KB)
#   ssl/key.pem   — Privater Schlüssel (3 KB)

# Zertifikate prüfen
ls -lh ssl/
```

### Schritt 5: Verzeichnisstruktur erstellen

```bash
# Logs-Verzeichnis erstellen (wenn nicht vorhanden)
mkdir -p logs

# Testen, ob alle Verzeichnisse existieren
ls -la app/ js/ css/ seeds/ scripts/ tests/
```

---

## 4. Konfiguration

### Schritt 6: Umgebungsvariablen (.env) erstellen

```bash
# .env.example als Vorlage kopieren
cp .env.example .env

# .env bearbeiten (mit einem Editor deiner Wahl)
nano .env
```

**Inhalt der `.env`-Datei:**

```bash
# === Security (PFLICHT — niemals committen!) ===
SECRET_KEY=<generierter-sicherer-Schlüssel>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
REFRESH_TOKEN_DAYS=7

# === Database ===
DB_PATH=verbrannte_zone.db

# === Server ===
HOST=0.0.0.0
PORT=8000

# === Logging ===
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# === Optional: Prometheus Metrics ===
PROMETHEUS_ENABLED=false
PROMETHEUS_PORT=9090

# === Optional: Rate Limiting ===
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60  # seconds

# === Optional: CORS (für externe Frontends) ===
CORS_ORIGINS=http://localhost:3000,http://10.68.42.10:3000
```

### Schritt 7: SECRET_KEY generieren

```bash
# Sichere SECRET_KEY generieren (mindestens 32 Bytes)
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Ausgabe kopieren und in .env einfügen:
# Beispiel: aB3dEf6hIj9Lm2Op5Rs8Uv1Xy4Za7Cd0Fg3Jk6Mn9Qs2Uv5Yx8
```

**WICHTIG:** Die SECRET_KEY wird für JWT-Token-Signierung verwendet. Wenn keine SECRET_KEY bereitgestellt wird, startet der Server mit einem `ValueError`.

### Schritt 8: Konfiguration verifizieren

```bash
# Testen, ob config.py korrekt lädt
python3 -c "from app.config import SECRET_KEY; print('SECRET_KEY geladen:', bool(SECRET_KEY))"

# Alle ENV-Variablen prüfen
python3 -c "
from app.config import (
    SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES,
    DB_PATH, HOST, PORT, LOG_LEVEL
)
print(f'SECRET_KEY: {bool(SECRET_KEY)}')
print(f'ALGORITHM: {ALGORITHM}')
print(f'DB_PATH: {DB_PATH}')
print(f'HOST: {HOST}:{PORT}')
print(f'LOG_LEVEL: {LOG_LEVEL}')
"
```

---

## 5. Datenbank-Setup & Migration

### Schritt 9: Datenbank initialisieren

Die Datenbank wird automatisch beim ersten Serverstart erstellt. Sie enthält alle Tabellen basierend auf den SQLAlchemy Models in `app/models.py`.

**Automatisch erstellte Tabellen (46 Modelle):**

| Tabelle | Zweck | Wichtige Spalten |
|---------|-------|------------------|
| `players` | Spieler-Accounts | id, username, email, password_hash, created_at |
| `users` | Benutzer-Profile | id, player_id, display_name, avatar_url |
| `provinces` | Provinzen | id, name, owner_id, x, y, population, mips |
| `building_types` | Gebäude-Typen | id, name, cost_resources, production_rate |
| `building_instances` | Gebaute Gebäude | id, province_id, building_type_id, level |
| `armies` | Armeen | id, province_id, strength, leader_id |
| `units` | Militäreinheiten | id, army_id, unit_type_id, count |
| `resources` | Ressourcen | id, name, base_value, scarcity |
| `game_log_entries` | Spielereignisse | id, province_id, event_type, message |
| `trade_routes` | Handelsrouten | id, source_province_id, target_province_id |
| `market_stands` | Marktplatz-Stände | id, province_id, article_id, price |
| `kontor_prices` | Kontor-Preise | id, article_id, province_id, price |
| `province_climate` | Wetter/Daten | id, province_id, bodenfeuchtigkeit, grundwasserspiegel |
| `province_tags` | Provinz-Tags | id, province_id, tag_name |

### Schritt 10: Datenbank-Indizes erstellen

```bash
# Index-Migration ausführen (verbessert Abfrageperformance)
python3 scripts/db_index_migration.py

# Erwartete Ausgabe:
#   Creating indexes...
#   Created index on provinces.owner_id
#   Created index on building_instances.province_id
#   ... (39 Indizes insgesamt)
#   All indexes created successfully.

# Verifizieren, dass Indizes existieren
sqlite3 verbrannte_zone.db "SELECT name FROM sqlite_master WHERE type='index' AND sql NOT LIKE '%sqlite%';" | wc -l
# Sollte 39+ anzeigen
```

### Schritt 11: Datenbank-Status prüfen

```bash
# Datenbank-Datei existiert?
ls -lh verbrannte_zone.db

# Tabellenanzahl prüfen
sqlite3 verbrannte_zone.db ".tables" | wc -w
# Sollte 40+ Tabellen anzeigen

# Gesamtgröße der Datenbank
du -sh verbrannte_zone.db
```

---

## 6. Seed-Daten importieren

### Schritt 12: Statische Daten in die Datenbank laden

Die Seed-Skripte füllen die Datenbank mit grundlegenden Spielsystemen:

```bash
# Haupt-Seed-Skript ausführen (lädt alle Seeds)
python3 seeds/seed_main.py

# Erwartete Ausgabe:
#   Seeding articles... Done (100+ Einträge)
#   Seeding buildings... Done (200+ Einträge)
#   Seeding terrains... Done (45 Terrain-Typen)
#   Seeding resources... Done (50+ Ressourcen)
#   Seeding units... Done (125+ Einheiten)
#   Seeding governments... Done (10+ Regierungsformen)
#   All seeds completed successfully.

# Alternativ: Einzelne Seeds ausführen
python3 seeds/seed_artikel.py      # Artikel (Handelswaren)
python3 seeds/seed_gebaeude.py     # Gebäude-Typen
python3 seeds/seed_terrains.py     # Terrain-Typen (Wüste, Wald, etc.)
python3 seeds/seed_ressourcen.py   # Ressourcen (Holz, Stein, etc.)
python3 seeds/seed_einheiten.py    # Militäreinheiten
python3 seeds/seed_regierungsformen.py  # Regierungsformen (Demokratie, Diktatur, etc.)
python3 seeds/seed_vorkommen.py    # Vorkommen/Deposits (Erz, Öl, etc.)
```

### Seed-Daten-Übersicht

| Seed-Skript | Tabelle | Anzahl Einträge | Beschreibung |
|-------------|---------|-----------------|--------------|
| `seed_artikel.py` | `articles` | ~100 | Handelswaren (Nahrung, Werkzeuge, etc.) |
| `seed_gebaeude.py` | `building_types` | ~200 | Gebäude-Typen (Wohnhäuser, Fabriken, etc.) |
| `seed_terrains.py` | `terrain_configs` | ~45 | Terrain-Typen (Wüste, Grasland, Dschungel) |
| `seed_ressourcen.py` | `resources` | ~50 | Rohstoffe (Holz, Stein, Erz) |
| `seed_einheiten.py` | `unit_types` | ~125 | Militäreinheiten (Infanterie, Kavallerie) |
| `seed_regierungsformen.py` | `regierungsformen` | ~10 | Regierungsformen (Demokratie, Monarchie) |
| `seed_vorkommen.py` | `vorkommen` | ~30 | Vorkommen (Erzminen, Ölfelder) |
| `seed_lebewesen.py` | `animal_templates` | ~15 | Wildtier-Typen (Hirsche, Wildschweine) |

---

## 7. Server starten

### Schritt 13: FastAPI-Server starten

```bash
# Entwicklungsserver mit Auto-Reload starten
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Erwartete Ausgabe:
#   INFO:     Uvicorn running on http://0.0.0.0:8000
#   INFO:     Application startup complete.
#   INFO:     Scheduler started — server tick every 1 hour

# Server läuft jetzt unter:
#   http://localhost:8000          — Frontend (index.html)
#   http://localhost:8000/api/docs — Swagger UI (API-Dokumentation)
#   http://localhost:8000/admin.html — Admin-Oberfläche
```

### Server-Komponenten im Detail

**FastAPI App (`app/main.py`):**
- Lädt Konfiguration aus `.env` (via `app/config.py`)
- Initialisiert SQLAlchemy Engine mit Foreign-Key-Constraints
- Startet APScheduler für stündliche Server-Ticks
- Mountet alle API-Routen unter `/api/`
- Serve static files (HTML, CSS, JS)

**Server-Tick (`app/tick_logic.py`):**
- Läuft alle 1 Stunde (konfigurierbar in `app/main.py`)
- Führt folgende Logik aus:
  - Bevölkerungsentwicklung (Geburten, Todesfälle)
  - Ressourcenproduktion (Gebäude, Vorkommen)
  - Marktpreis-Anpassung (Nachfrage/Supply)
  - Wetter-Simulation (Klima, extreme Events)
  - Diplomatie-Updates (Allianzen, Kriege)
  - Cleanup (alte Logs, inaktive Provinzen)

**Middleware:**
- `CORSMiddleware` — CORS für externe Frontends
- `ErrorTrackingMiddleware` — Fehler protokollieren
- `RateLimiting` — Rate Limiting (100 Requests/Minute standard)

### Schritt 14: Server-Status prüfen

```bash
# Health-Check Endpoint aufrufen
curl http://localhost:8000/api/health

# Erwartete Antwort:
# {
#   "status": "healthy",
#   "database": "connected",
#   "version": "1.8",
#   "uptime_seconds": 12345
# }

# API-Dokumentation öffnen (Browser)
open http://localhost:8000/api/docs

# Prometheus Metrics (wenn aktiviert)
curl http://localhost:9090/metrics
```

---

## 8. API-Endpunkte Übersicht

### Authentifizierung (`/api/auth`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| POST | `/api/auth/register` | Spieler registrieren | Nein |
| POST | `/api/auth/login` | Spieler einloggen | Nein |
| POST | `/api/auth/refresh` | JWT-Token erneuern | Ja (Refresh Token) |
| GET | `/api/auth/me` | Aktuellen Spieler abrufen | Ja (Access Token) |
| POST | `/api/auth/logout` | Ausloggen | Ja |

### Provinz-Management (`/api/province`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/province/` | Alle Provinzen auflisten | Ja |
| POST | `/api/province/` | Neue Provinz gründen | Ja |
| GET | `/api/province/{id}` | Provinz-Details | Ja |
| PUT | `/api/province/{id}` | Provinz aktualisieren | Ja (Owner) |
| DELETE | `/api/province/{id}` | Provinz löschen | Ja (Admin) |
| POST | `/api/province/{id}/buildings` | Gebäude bauen | Ja (Owner) |
| POST | `/api/province/{id}/buildings/{bid}/demolish` | Gebäude abreißen | Ja (Owner) |
| GET | `/api/province/{id}/tags` | Provinz-Tags abrufen | Ja |
| POST | `/api/province/{id}/tags` | Tag hinzufügen | Ja (Owner) |
| DELETE | `/api/province/{id}/tags/{tag}` | Tag entfernen | Ja (Owner) |

### Handel & Markt (`/api/market`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/market/` | Alle Marktplätze | Ja |
| POST | `/api/market/{pid}/stand` | Marktplatz-Stand erstellen | Ja (Owner) |
| PUT | `/api/market/{pid}/stand/{sid}` | Preis aktualisieren | Ja (Owner) |
| GET | `/api/market/kontor` | Kontor-Preise abrufen | Ja |
| POST | `/api/market/kontor/{pid}` | Kontor-Preis setzen | Ja (Owner) |
| GET | `/api/market/trade_routes` | Handelsrouten auflisten | Ja |
| POST | `/api/market/trade_routes` | Neue Handelsroute erstellen | Ja (Owner) |

### Weltkarte (`/api/world`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/world/map` | Weltkarte abrufen | Ja |
| GET | `/api/world/terrain/{id}` | Terrain-Details | Ja |
| GET | `/api/world/buildings` | Alle Gebäude-Typen | Nein |
| POST | `/api/world/generate` | Weltkarte neu generieren | Ja (Admin) |

### Militär (`/api/army`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/army/` | Alle Armeen auflisten | Ja |
| POST | `/api/army/{pid}/train` | Truppen ausbilden | Ja (Owner) |
| PUT | `/api/army/{id}/move` | Armee bewegen | Ja (Leader) |
| POST | `/api/army/{id}/attack` | Angriff starten | Ja (Leader) |

### Spielereignisse (`/api/gamelog`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/gamelog/` | Spielereignisse auflisten | Ja |
| GET | `/api/gamelog/{pid}` | Provinz-Ereignisse | Ja (Owner) |
| POST | `/api/gamelog/admin/broadcast` | Broadcast senden | Ja (Admin) |

### Offline-Sync (`/api/offline_sync`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/offline_sync/sync` | Sync-Status abrufen | Ja |
| POST | `/api/offline_sync/queue` | Offline-Änderung queue | Ja |
| GET | `/api/offline_sync/conflicts` | Konflikte auflisten | Ja |

### Admin (`/api/admin/*`)

| Methode | Endpoint | Beschreibung | Auth erforderlich |
|---------|----------|--------------|-------------------|
| GET | `/api/admin/dashboard` | Admin-Dashboard | Ja (Admin) |
| GET | `/api/admin/users` | Alle Benutzer | Ja (Admin) |
| PUT | `/api/admin/users/{id}` | Benutzer bearbeiten | Ja (Admin) |
| GET | `/api/admin/provinces` | Alle Provinzen | Ja (Admin) |
| POST | `/api/admin/ticks/force` | Server-Tick erzwingen | Ja (Admin) |
| POST | `/api/admin/broadcast` | Broadcast senden | Ja (Admin) |

---

## 9. Frontend-Nutzung

### Haupt-Frontend (`index.html`)

Das Frontend ist eine Single-Page-Application (SPA) mit Vanilla JavaScript. Keine Frameworks, kein Build-Prozess erforderlich.

**Starten:**
```bash
# Server starten (siehe Schritt 13)
uvicorn app.main:app --reload

# Browser öffnen:
open http://localhost:8000
```

**Hauptkomponenten:**

1. **Willkommens-Overlay (`welcome-overlay`)**
   - Registrierung/Login für neue Spieler
   - Onboarding-Flow (Start-Provinz-Zuweisung)

2. **Top-Bar (`topbar-resources`)**
   - Ressourcen-Anzeige (MIPS, Nahrung, Holz, etc.)
   - Benachrichtigungen
   - Spieler-Info

3. **Weltkarte (`worldmap`)**
   - Interaktive Karte mit Terrains
   - Provinzen, Armeen, Handelsrouten anzeigen
   - Klick auf Provinz → Detailansicht

4. **Provinz-Ansicht (`province-view`)**
   - Gebäude verwalten (bauen, abbrechen)
   - Lager-Inhalt anzeigen
   - Militär verwalten (Truppen ausbilden, bewegen)
   - Transport/Handel steuern

5. **Gamelog (`gamelog`)**
   - Spielereignisse anzeigen (öffentlich, privat, admin)
   - Filter nach Event-Typ

### JavaScript-Module

| Datei | Größe | Funktion |
|-------|-------|----------|
| `app.js` | 43 KB | Hauptanwendung, Navigation, Ressourcen-Update |
| `province.js` | 30 KB | Provinz-Verwaltung, Gebäude-Bau/Abriss |
| `world-data.js` | 28 KB | Weltkarte-Daten, Terrain-Rendering |
| `transport.js` | 13 KB | Transport, Lagerverwaltung |
| `worldmap.js` | 12 KB | Weltkarte rendern, Armeen anzeigen |
| `buildings-data.js` | 8 KB | Gebäude-Datenbank (statisch) |
| `offline-sync.js` | 7 KB | Offline-Sync mit LocalStorage |
| `onboarding.js` | 6 KB | Onboarding-Flow (Start-Provinz) |
| `province_grid.js` | 6 KB | Stadtpläne verwalten |
| `terrain-types.js` | 4 KB | Terrain-Typen Definition |
| `auth-service.js` | 4 KB | JWT-Authentifizierung |

### Offline-Modus

**Funktionsweise:**
1. Änderungen werden im LocalStorage gespeichert (auch ohne Internet)
2. Alle 30 Sekunden wird geprüft, ob eine Verbindung besteht
3. Bei Wiederverbindung: Automatische Synchronisierung mit Server
4. Konflikte (gleichzeitige Änderungen) werden dem Spieler gemeldet

**Manuelle Synchronisierung:**
```javascript
// In der Browser-Konsole:
OfflineSync.forceSync()  // Sofortige Synchronisierung erzwingen
```

---

## 10. Admin-Bereich

### Admin-Oberfläche (`admin.html`)

**Zugang:**
```bash
# Server starten (siehe Schritt 13)
uvicorn app.main:app --reload

# Admin-Oberfläche öffnen:
open http://localhost:8000/admin.html
```

**Admin-Funktionen:**

1. **Dashboard (`/api/admin/dashboard`)**
   - Server-Status (Uptime, DB-Verbindung)
   - Spieleranzahl, Provinzenanzahl
   - Letzte Server-Ticks

2. **Benutzer-Verwaltung (`/api/admin/users`)**
   - Alle Benutzer auflisten
   - Benutzer bearbeiten (Rolle ändern, sperren)
   - Benutzer löschen

3. **Provinz-Verwaltung (`/api/admin/provinces`)**
   - Alle Provinzen auflisten
   - Provinz-Eigentümer ändern
   - Provinzen löschen

4. **Server-Tick steuern (`/api/admin/ticks`)**
   - Server-Tick erzwingen (manuell)
   - Tick-Intervall ändern

5. **Broadcast-Nachrichten (`/api/admin/broadcast`)**
   - Nachricht an alle Spieler senden
   - Nachrichten verwalten

6. **Weltkarte administrieren (`/api/admin/world`)**
   - Weltkarte neu generieren
   - Terrain-Konfiguration bearbeiten

### Admin-Authentifizierung

Admin-Benutzer müssen im Backend als `is_admin=True` markiert sein:

```python
# In der Datenbank manuell setzen (oder über API):
UPDATE users SET is_admin = 1 WHERE username = 'admin';
```

---

## 11. Test-Suite ausführen

### Tests ausführen

```bash
# Alle Tests ausführen (55 Tests)
python3 -m pytest tests/ -v

# Erwartete Ausgabe:
#   =========================== test session starts ============================
#   collected 55 items
#   
#   tests/test_orm_comprehensive.py ............                         [ 16%]
#   tests/test_api_quick.py .........                                    [ 32%]
#   tests/test_core_logic.py ...................                         [ 67%]
#   tests/test_new_features.py ...........                               [100%]
#   
#   ===================== 55 passed in 12.34s ==============================

# Einzelne Test-Dateien ausführen
python3 -m pytest tests/test_orm_comprehensive.py -v  # ORM-Tests (16)
python3 -m pytest tests/test_api_quick.py -v         # API-Schnelltests (9)
python3 -m pytest tests/test_core_logic.py -v        # Core-Logik (19)
python3 -m pytest tests/test_new_features.py -v      # Neue Features (11)
```

### Test-Übersicht

| Test-Datei | Tests | Beschreibung |
|------------|-------|--------------|
| `test_orm_comprehensive.py` | 16 | ORM-Modelle erstellen/lesen/updaten/löschen |
| `test_api_quick.py` | 9 | API-Endpunkte (Health, Auth, World) |
| `test_core_logic.py` | 19 | Core-Logik (Sichtbarkeit, Kampf, Bau) |
| `test_new_features.py` | 11 | Neue Features (Cleanup, Onboarding, Wetter) |

---

## 12. Detaillierte Architektur

### 12.1 Backend-Architektur

**FastAPI Application Lifecycle:**

```
Server Start (uvicorn)
    ↓
Lifespan (app/main.py)
    ├── Load .env configuration (app/config.py)
    ├── Initialize SQLAlchemy Engine (app/database.py)
    ├── Create all tables (if not exist)
    └── Start APScheduler (server tick every 1 hour)
         ↓
    Server Tick (app/tick_logic.py) — jede Stunde:
        ├── Bevölkerungsentwicklung (population_logic)
        ├── Ressourcenproduktion (building_logic, market_logic)
        ├── Wetter-Simulation (climate_logic)
        ├── Diplomatie-Updates (diplomacy_logic)
        ├── Cleanup (cleanup_logic)
        └── Notfallreserve-Verarbeitung (finance_logic)
```

**Datenbank-Schema (vereinfacht):**

```
players ──1:N── users
  │
  N:1 ── owner_id ──► players
  │
N:M ── province_tags ──► tags

provinces ──1:N── building_instances
  │                    │
  │                    N:1 ── building_type_id ──► building_types
  │
N:M ── armies ──1:N── units

provinces ──1:N── market_stands
  │                    │
  │                    N:1 ── article_id ──► articles

provinces ──1:N── trade_routes
  │                    │
  │              source_province_id ──► provinces
  │              target_province_id ──► provinces

provinces ──1:N── game_log_entries
  │
N:1 ── climate_id ──► province_climate
```

### 12.2 Frontend-Architektur

**Single-Page Application (SPA) mit Vanilla JS:**

```
index.html
    ├── CSS: style.css (19 KB)
    │
    └── JavaScript Modules:
        ├── auth-service.js     → JWT-Handling (Login, Register, Token)
        ├── terrain-types.js    → Terrain-Typen Definition
        ├── buildings-data.js   → Statische Gebäude-Datenbank
        ├── app.js              → Hauptanwendung (Navigation, Ressourcen)
        ├── onboarding.js       → Onboarding-Flow (Start-Provinz)
        ├── worldmap.js         → Weltkarte rendern
        ├── province.js         → Provinz-Verwaltung (Bauen, Abriss)
        ├── province_grid.js    → Stadtpläne verwalten
        ├── transport.js        → Transport, Lagerverwaltung
        └── offline-sync.js     → LocalStorage-Sync mit Server
```

**State Management:**
- Kein Framework (kein Redux, Vuex, etc.)
- Globaler State in `app.js` (Ressourcen, aktuelle Provinz)
- LocalStorage für Offline-Modus
- Fetch API für HTTP-Anfragen an Backend

### 12.3 Server-Tick System

**APScheduler Configuration (`app/main.py`):**

```python
scheduler = BackgroundScheduler()

def scheduled_tick():
    from app.tick_logic import run_tick
    db = SessionLocal()
    try:
        run_tick(db)  # Führt alle Logik-Module aus
    finally:
        db.close()

# Start scheduler on startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.add_job(scheduled_tick, 'interval', hours=1)
    scheduler.start()
    yield
    scheduler.shutdown()
```

**Tick-Logik (`app/tick_logic.py`) — Ausführliche Abfolge:**

1. **Bevölkerungsentwicklung** (`population_logic`)
   - Geburtenrate basierend auf Altersstruktur
   - Todesfälle basierend auf Alter, Nahrungsmangel
   - Migration zwischen Provinzen

2. **Ressourcenproduktion** (`building_logic`, `market_logic`)
   - Gebäude produzieren Ressourcen (Holzfäller → Holz)
   - Vorkommen fördern (Erzminen → Erz)
   - Marktpreise anpassen (Nachfrage/Supply)

3. **Wetter-Simulation** (`climate_logic`)
   - Stündliche Regenwahrscheinlichkeit basierend auf Terrain
   - Bodenfeuchtigkeit und Grundwasserspiegel ändern sich
   - Extreme Events: Dürre (~0.1% pro Stunde in Wüsten), Überschwemmung

4. **Diplomatie-Updates** (`diplomacy_logic`)
   - Allianz-Beziehungen aktualisieren
   - Kriegsstatus prüfen (Auto-Attack bei niedriger Moral)

5. **Cleanup** (`cleanup_logic`)
   - Alte GameLog-Einträge löschen (> 30 Tage)
   - Inaktive Provinzen markieren (> 90 Tage ohne Aktivität)
   - Verwaiste Datensätze bereinigen (z.B. Gebäude ohne Provinz)

6. **Notfallreserve** (`finance_logic`)
   - Prüfen, ob `handelskonto < threshold` (z.B. 100 MIPS)
   - Wenn ja: Notfallreserve aktivieren (automatisch MIPS hinzufügen)

---

## 13. Offene Punkte & Mängel

### 🔴 Kritisch — Keine kritischen offenen Punkte

**Alle 12 dokumentierten Features sind implementiert.** ✅

### 🟡 Hoch — Verbesserungen empfohlen

#### 13.1 Dokumentation von implementierten Features (8 Features)

**Problem:** 8 Features sind im Code implementiert, aber nicht in der Dokumentation beschrieben.

| Feature | Status | Empfohlene Aktion |
|---------|--------|-------------------|
| Province Model (vollständig) | ✅ Implementiert | Dokumentation in `docs/` erstellen |
| Gebäude-Bau Mechanik | ✅ Implementiert | Detail-Doku in `docs/25_feature_gebaeudebau.md` |
| Ressourcen-System | ✅ Implementiert | Detail-Doku in `docs/26_feature_ressourcen.md` |
| Lager-System | ✅ Implementiert | Detail-Doku in `docs/27_feature_lager.md` |
| System Lock Mechanik | ✅ Implementiert | Detail-Doku in `docs/28_feature_system_lock.md` |
| Provinz-Einstellungen | ✅ Implementiert | Detail-Doku in `docs/29_feature_provinz_einstellungen.md` |
| Handelsrouten (Trade Routes) | ✅ Implementiert | Detail-Doku in `docs/30_feature_handelsrouten.md` |
| Provinz-Transfer | ✅ Implementiert | Detail-Doku in `docs/31_feature_provinz_transfer.md` |

**Aufwand:** Mittel (jeweils 2-4 KB Dokumentation pro Feature)

---

#### 13.2 Veraltete Dokumentation verschieben (15 Dateien)

**Problem:** 15 Dokumentationsdateien sind veraltet oder experimentell und sollten in `docs/archive/` verschoben werden.

| Datei | Grund für Archivierung |
|-------|------------------------|
| `docs/00_session_start.md` | Veraltet (Session-Start) |
| `docs/00_meta_prompt_engineer.md` | Veraltet (Prompt-Engineering) |
| `docs/BUG_AUDIT_2026-09.md` | Historisch (Bug-Audit) |
| `docs/FEHLERBERICHT_2026-09.md` | Historisch (Fehlerbericht) |
| `docs/MIGRATION_2026-09.md` | Historisch (Migration) |
| `docs/PHASE1_ABSCHLUSSBERICHT.md` | Historisch (Phase 1) |
| `docs/PHASE2_ABSCHLUSSBERICHT.md` | Historisch (Phase 2) |
| `docs/PHASE3_4_ABSCHLUSSBERICHT.md` | Historisch (Phase 3-4) |
| `docs/PHASE5_ABSCHLUSSBERICHT.md` | Historisch (Phase 5) |
| `docs/PHASE6_ABSCHLUSSBERICHT.md` | Historisch (Phase 6) |
| `docs/IMPLEMENTIERUNGSPLAN.md` | Veraltet (Implementierungsplan) |
| `docs/IMPLEMENTIERUNGSPLAN_V2.md` | Veraltet (Implementierungsplan v2) |
| `docs/UEBERARBEITUNGSPLAN_v1.7.md` | Veraltet (Überarbeitungsplan v1.7) |
| `docs/UEBERARBEITUNGSPLAN_v1.8.md` | Veraltet (Überarbeitungsplan v1.8) |
| `docs/agent_repair_plan.md` | Veraltet (Agent-Reparatur) |

**Empfohlene Aktion:**
```bash
# Archiv-Verzeichnis erstellen
mkdir -p docs/archive

# Veraltete Dateien verschieben
mv docs/00_session_start.md docs/archive/
mv docs/BUG_AUDIT_2026-09.md docs/archive/
# ... (weitere Dateien)

# README in docs/ aktualisieren
echo "# Archiv — Veraltete Dokumentation" > docs/archive/README.md
```

**Aufwand:** Niedrig (15 Dateien verschieben)

---

#### 13.3 Experimentelle Berichte organisieren

**Problem:** Einige experimentelle Berichte sind nicht klar von der Hauptdokumentation getrennt.

| Datei | Empfohlene Aktion |
|-------|-------------------|
| `docs/00_ultimative_roadmap.md` | Verschieben nach `docs/archive/` |
| `docs/26_admin_overhaul.md` | Prüfen, ob aktuell — sonst archivieren |
| `docs/28_ui_ueberarbeitung.md` | Prüfen, ob aktuell — sonst archivieren |

**Aufwand:** Niedrig

---

### 🟢 Mittel — Optional, aber wünschenswert

#### 13.4 CI/CD Pipeline einrichten

**Problem:** Keine automatische Test- und Deploy-Pipeline.

**Empfohlene Lösung:** GitHub Actions Workflow erstellen:

```yaml
# .github/workflows/test.yml
name: Test & Deploy

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run tests
        run: python3 -m pytest tests/ -v

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to server
        run: |
          ssh user@server "cd /home/fabian/Wasteland && git pull && ./scripts/restart_server.sh"
```

**Aufwand:** Mittel (1-2 Tage Einrichtung)

---

#### 13.5 Automatische Dokumentation aus Models generieren

**Problem:** Dokumentation muss manuell gepflegt werden; Abweichungen zwischen Code und Docs möglich.

**Empfohlene Lösung:** Sphinx oder MkDocs mit Auto-Generation aus Docstrings:

```bash
# MkDocs installieren
pip install mkdocs mkdocstrings[python]

# mkdocs.yml erstellen
cat > mkdocs.yml << 'EOF'
site_name: Wasteland API Documentation
nav:
  - Home: index.md
  - API: api.md

plugins:
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
EOF

# Dokumentation generieren
mkdocs build
```

**Aufwand:** Hoch (3-5 Tage Einrichtung + Wartung)

---

#### 13.6 Datenbank-Monitoring einrichten

**Problem:** Keine automatische Überwachung der Datenbankgröße und Performance.

**Empfohlene Lösung:** Skript zur regelmäßigen Prüfung:

```bash
#!/bin/bash
# scripts/check_database.sh

DB_PATH="verbrannte_zone.db"

# Datenbankgröße prüfen
SIZE=$(du -sh "$DB_PATH" | cut -f1)
echo "Database size: $SIZE"

# Tabellenanzahl prüfen
TABLES=$(sqlite3 "$DB_PATH" ".tables" | wc -w)
echo "Tables: $TABLES"

# Große Tabellen identifizieren
sqlite3 "$DB_PATH" "SELECT name, COUNT(*) as count FROM sqlite_master WHERE type='table' GROUP BY name ORDER BY count DESC LIMIT 10;"

# Index-Status prüfen
INDEXES=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND sql NOT LIKE '%sqlite%';")
echo "Indexes: $INDEXES"
```

**Aufwand:** Niedrig (30 Minuten)

---

### ⚪ Gering — Kosmetisch oder langfristige Verbesserungen

#### 13.7 Frontend-Optimierung

**Problem:** Kein Build-Prozess, keine Code-Splitting, alle JS-Dateien werden sofort geladen.

**Empfohlene Lösung:**
- JavaScript-Module lazy-load (nur bei Bedarf laden)
- CSS-Minification
- Image-Optimierung (Terrains als WebP konvertieren)

**Aufwand:** Mittel-Hoch (1-2 Wochen)

---

#### 13.8 API-Versionierung

**Problem:** Keine API-Versionierung; Breaking Changes würden bestehende Clients brechen.

**Empfohlene Lösung:**
```python
# In app/main.py:
api_router = APIRouter(prefix="/api/v1")  # Version 1

# Bei Breaking Changes:
api_router_v2 = APIRouter(prefix="/api/v2")
```

**Aufwand:** Niedrig (1-2 Stunden)

---

#### 13.9 Load Testing einrichten

**Problem:** Keine automatisierten Lasttests für den Server.

**Empfohlene Lösung:**
```bash
# Locust installieren (Open-Source Load Testing)
pip install locust

# locustfile.py erstellen
cat > locustfile.py << 'EOF'
from locust import HttpUser, task

class WastelandUser(HttpUser):
    @task
    def get_health(self):
        self.client.get("/api/health")
    
    @task(3)
    def get_world_map(self):
        self.client.get("/api/world/map")
EOF

# Load Test starten
locust --host=http://localhost:8000
```

**Aufwand:** Mittel (1-2 Tage)

---

### Zusammenfassung der offenen Punkte

| Priorität | Anzahl | Geschätzter Aufwand |
|-----------|--------|---------------------|
| 🔴 Kritisch | 0 | — |
| 🟡 Hoch | 3 | 1-2 Wochen |
| 🟢 Mittel | 4 | 2-4 Wochen |
| ⚪ Gering | 3 | < 1 Woche |

**Gesamtaufwand für alle offenen Punkte:** ~4-7 Wochen (bei 1 Entwickler)

---

## 14. Troubleshooting

### Häufige Probleme und Lösungen

#### Problem 1: Server startet nicht — `ValueError: SECRET_KEY environment variable is required!`

**Ursache:** `.env`-Datei fehlt oder `SECRET_KEY` ist nicht gesetzt.

**Lösung:**
```bash
# .env erstellen (wenn nicht vorhanden)
cp .env.example .env

# SECRET_KEY generieren und einfügen
python3 -c "import secrets; print(secrets.token_urlsafe(32))" >> .env
# Oder manuell in .env einfügen:
echo 'SECRET_KEY=<dein-generierter-schlüssel>' >> .env

# Server neu starten
uvicorn app.main:app --reload
```

---

#### Problem 2: Datenbank-Verbindung fehlgeschlagen — `sqlite3.OperationalError: no such table`

**Ursache:** Datenbank wurde nicht initialisiert oder Seed-Daten fehlen.

**Lösung:**
```bash
# Datenbank-Datei löschen (ACHTUNG: Alle Daten gehen verloren!)
rm verbrannte_zone.db

# Server neu starten (erstellt Datenbank automatisch)
uvicorn app.main:app --reload

# Seed-Daten importieren (nach Serverstart)
python3 seeds/seed_main.py
```

---

#### Problem 3: Foreign-Key-Constraints verletzt — `sqlite3.IntegrityError: FOREIGN KEY constraint failed`

**Ursache:** Versuch, eine Provinz zu löschen, die noch Gebäude oder Armeen hat.

**Lösung:**
```python
# In app/database.py: Foreign-Key-Constraints sind aktiviert (PRAGMA foreign_keys=ON)

# Um eine Provinz zu löschen, müssen zuerst abhängige Datensätze gelöscht werden:
from app.models import SessionLocal, BuildingInstance, Army

db = SessionLocal()
# Gebäude löschen
db.query(BuildingInstance).filter_by(province_id=province_id).delete()
# Armeen löschen
db.query(Army).filter_by(province_id=province_id).delete()
# Provinz löschen
db.query(Province).filter_by(id=province_id).delete()
db.commit()
db.close()
```

---

#### Problem 4: API-Endpunkte antworten nicht — `Connection refused`

**Ursache:** Server läuft nicht oder Port ist blockiert.

**Lösung:**
```bash
# Prüfen, ob Server läuft
ps aux | grep uvicorn

# Port prüfen (sollte 8000 sein)
netstat -tlnp | grep 8000

# Server neu starten
killall uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

#### Problem 5: Tests schlagen fehl — `ImportError: No module named 'app'`

**Ursache:** Working Directory ist nicht korrekt gesetzt.

**Lösung:**
```bash
# Im Projekt-Verzeichnis ausführen:
cd /home/fabian/Wasteland

# Tests mit vollem Pfad ausführen:
python3 -m pytest tests/ -v

# Oder PYTHONPATH setzen:
export PYTHONPATH=/home/fabian/Wasteland:$PYTHONPATH
python3 -m pytest tests/ -v
```

---

#### Problem 6: CORS-Fehler im Browser — `Access to fetch at '...' from origin '...' has been blocked by CORS policy`

**Ursache:** Frontend und Backend auf verschiedenen Domains/Ports.

**Lösung:**
```bash
# In .env CORS_ORIGINS setzen:
echo 'CORS_ORIGINS=http://localhost:3000,http://10.68.42.10:3000' >> .env

# Server neu starten
uvicorn app.main:app --reload
```

---

#### Problem 7: Server-Tick läuft nicht — Keine Ressourcenproduktion

**Ursache:** APScheduler nicht gestartet oder Fehler im Tick.

**Lösung:**
```bash
# Server-Logs prüfen (logs/wasteland.log)
tail -f logs/wasteland.log | grep "tick"

# Manuellen Tick erzwingen (Admin-Endpoint):
curl -X POST http://localhost:8000/api/admin/ticks/force \
  -H "Authorization: Bearer <admin-jwt-token>"

# APScheduler neu starten (Server neustarten):
killall uvicorn
uvicorn app.main:app --reload
```

---

#### Problem 8: Offline-Sync funktioniert nicht — Änderungen werden nicht synchronisiert

**Ursache:** LocalStorage voll oder Server-API nicht erreichbar.

**Lösung:**
```javascript
// In der Browser-Konsole:
console.log(OfflineSync.getStatus())  // Sync-Status prüfen

// LocalStorage leeren (ACHTUNG: Alle Offline-Daten gehen verloren!)
localStorage.clear()

// Manuelle Synchronisierung erzwingen:
OfflineSync.forceSync()

// Server-API prüfen:
curl http://localhost:8000/api/offline_sync/sync \
  -H "Authorization: Bearer <jwt-token>"
```

---

#### Problem 9: SSL-Zertifikate ungültig — Browser warnt vor unsicherer Verbindung

**Ursache:** Selbst-signierte Zertifikate werden vom Browser nicht vertraut.

**Lösung:**
```bash
# Neue SSL-Zertifikate generieren:
./scripts/generate_ssl_certs.sh

# Im Browser die Warnung akzeptieren (nur für lokale Entwicklung!)
# Oder Zertifikat zum Truststore hinzufügen:
sudo cp ssl/cert.pem /usr/local/share/ca-certificates/wasteland.crt
sudo update-ca-certificates
```

---

#### Problem 10: Datenbank zu groß — Performance-Probleme

**Ursache:** GameLog-Einträge werden nicht bereinigt, Datenbank wächst unbegrenzt.

**Lösung:**
```bash
# Cleanup-Logik manuell ausführen:
python3 -c "
from app.models import SessionLocal
from app.cleanup_logic import process_cleanup_tick

db = SessionLocal()
process_cleanup_tick(db)  # Löscht alte Logs, inaktive Provinzen
db.close()
print('Cleanup abgeschlossen.')
"

# Datenbank komprimieren:
sqlite3 verbrannte_zone.db "VACUUM;"

# Größe prüfen:
du -sh verbrannte_zone.db
```

---

## Anhang A: Quick-Start Checklist

Für einen schnellen Clean Build folge dieser Checkliste:

```bash
# 1. Python-Version prüfen
python3 --version  # ≥ 3.10

# 2. Virtual Environment erstellen & aktivieren
python3 -m venv venv && source venv/bin/activate

# 3. Abhängigkeiten installieren
pip install -r requirements.txt

# 4. .env erstellen & SECRET_KEY generieren
cp .env.example .env
echo "SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')" >> .env

# 5. Server starten
uvicorn app.main:app --reload

# 6. Seed-Daten importieren (nach Serverstart)
python3 seeds/seed_main.py

# 7. Datenbank-Indizes erstellen
python3 scripts/db_index_migration.py

# 8. Tests ausführen (optional, aber empfohlen)
python3 -m pytest tests/ -v

# 9. Browser öffnen: http://localhost:8000
```

---

## Anhang B: Wichtige Dateipfade

| Datei/Verzeichnis | Pfad | Beschreibung |
|-------------------|------|--------------|
| FastAPI Entry Point | `app/main.py` | Server-Start, Router-Mounting |
| Konfiguration | `app/config.py` | ENV-Variablen laden |
| Datenbank-Setup | `app/database.py` | SQLAlchemy Engine, Foreign Keys |
| ORM Models | `app/models.py` | 46 Model-Klassen |
| Server-Tick | `app/tick_logic.py` | Stündliche Logik-Ausführung |
| API Router | `app/api/__init__.py` | Alle API-Endpunkte |
| Frontend HTML | `index.html` | Haupt-Frontend |
| Admin HTML | `admin.html` | Admin-Oberfläche |
| CSS Styles | `css/style.css` | Globale Styles |
| JavaScript Main | `js/app.js` | Hauptanwendung (43 KB) |
| Seed-Skripte | `seeds/seed_main.py` | Alle Seeds auf einmal |
| Datenbank-Datei | `verbrannte_zone.db` | SQLite-Datenbank (automatisch erstellt) |
| Logs | `logs/wasteland.log` | Server-Logs (DEBUG-Level) |
| SSL-Zertifikate | `ssl/cert.pem`, `ssl/key.pem` | HTTPS-Zertifikate |
| Tests | `tests/` | 55 Unit-Tests |

---

## Anhang C: API-Endpunkte (Vollständige Liste)

### Health & Status
- `GET /api/health` — Server-Gesundheitscheck
- `GET /api/metrics` — Prometheus Metrics

### Authentifizierung
- `POST /api/auth/register` — Registrieren
- `POST /api/auth/login` — Einloggen
- `POST /api/auth/refresh` — Token erneuern
- `GET /api/auth/me` — Aktueller Spieler
- `POST /api/auth/logout` — Ausloggen

### Provinzen
- `GET /api/province/` — Alle Provinzen
- `POST /api/province/` — Neue Provinz gründen
- `GET /api/province/{id}` — Provinz-Details
- `PUT /api/province/{id}` — Provinz aktualisieren
- `DELETE /api/province/{id}` — Provinz löschen (Admin)
- `POST /api/province/{id}/buildings` — Gebäude bauen
- `POST /api/province/{id}/buildings/{bid}/demolish` — Gebäude abreißen
- `GET /api/province/{id}/tags` — Provinz-Tags
- `POST /api/province/{id}/tags` — Tag hinzufügen
- `DELETE /api/province/{id}/tags/{tag}` — Tag entfernen

### Handel & Markt
- `GET /api/market/` — Alle Marktplätze
- `POST /api/market/{pid}/stand` — Marktplatz-Stand erstellen
- `PUT /api/market/{pid}/stand/{sid}` — Preis aktualisieren
- `GET /api/market/kontor` — Kontor-Preise
- `POST /api/market/kontor/{pid}` — Kontor-Preis setzen
- `GET /api/market/trade_routes` — Handelsrouten
- `POST /api/market/trade_routes` — Neue Handelsroute

### Weltkarte
- `GET /api/world/map` — Weltkarte
- `GET /api/world/terrain/{id}` — Terrain-Details
- `GET /api/world/buildings` — Alle Gebäude-Typen
- `POST /api/world/generate` — Weltkarte neu generieren (Admin)

### Militär
- `GET /api/army/` — Alle Armeen
- `POST /api/army/{pid}/train` — Truppen ausbilden
- `PUT /api/army/{id}/move` — Armee bewegen
- `POST /api/army/{id}/attack` — Angriff starten

### Spielereignisse
- `GET /api/gamelog/` — Alle Ereignisse
- `GET /api/gamelog/{pid}` — Provinz-Ereignisse
- `POST /api/gamelog/admin/broadcast` — Broadcast senden (Admin)

### Offline-Sync
- `GET /api/offline_sync/sync` — Sync-Status
- `POST /api/offline_sync/queue` — Offline-Änderung queue
- `GET /api/offline_sync/conflicts` — Konflikte auflisten

### Admin
- `GET /api/admin/dashboard` — Admin-Dashboard
- `GET /api/admin/users` — Alle Benutzer
- `PUT /api/admin/users/{id}` — Benutzer bearbeiten
- `GET /api/admin/provinces` — Alle Provinzen
- `POST /api/admin/ticks/force` — Server-Tick erzwingen
- `POST /api/admin/broadcast` — Broadcast senden

---

## Anhang D: Environment Variables (Vollständige Liste)

| Variable | Typ | Standardwert | Beschreibung |
|----------|-----|--------------|--------------|
| `SECRET_KEY` | String | **Pflicht** | JWT-Signierungsschlüssel (min. 32 Bytes) |
| `ALGORITHM` | String | `HS256` | JWT-Algorithmus (HS256, RS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Integer | `120` | Gültigkeitsdauer Access-Token (Minuten) |
| `REFRESH_TOKEN_DAYS` | Integer | `7` | Gültigkeitsdauer Refresh-Token (Tage) |
| `DB_PATH` | String | `verbrannte_zone.db` | Pfad zur SQLite-Datenbank |
| `HOST` | String | `0.0.0.0` | Server-Host (0.0.0.0 = alle Interfaces) |
| `PORT` | Integer | `8000` | Server-Port |
| `LOG_LEVEL` | String | `INFO` | Log-Level (DEBUG, INFO, WARNING, ERROR) |
| `PROMETHEUS_ENABLED` | Boolean | `false` | Prometheus Metrics aktivieren/deaktivieren |
| `PROMETHEUS_PORT` | Integer | `9090` | Prometheus Metrics Port |
| `RATE_LIMIT_REQUESTS` | Integer | `100` | Max. Requests pro Zeitfenster |
| `RATE_LIMIT_WINDOW` | Integer | `60` | Zeitfenster für Rate Limiting (Sekunden) |
| `CORS_ORIGINS` | CSV-String | `` | Erlaubte CORS-Origin (kommagetrennt) |

---

## Anhang E: Datenbank-Tabellen (Vollständige Liste)

| Tabelle | Model-Klasse | Zeilen (typisch) | Beschreibung |
|---------|--------------|------------------|--------------|
| `players` | Player | 10-100 | Spieler-Accounts (Login-Daten) |
| `users` | User | 10-100 | Benutzer-Profile (Anzeigename, Avatar) |
| `provinces` | Province | 5-50 | Provinzen (Spielgebiete) |
| `building_types` | BuildingType | 200+ | Gebäude-Typen (Wohnhaus, Fabrik) |
| `building_instances` | BuildingInstance | 50-200 | Gebaute Gebäude (mit Level) |
| `road_instances` | RoadInstance | 20-100 | Gebaute Straßen |
| `armies` | Army | 5-30 | Armeen (Militär) |
| `units` | Unit | 20-100 | Militäreinheiten (Infanterie, Kavallerie) |
| `resources` | Resource | 50+ | Ressourcen (Holz, Stein, Erz) |
| `province_lager` | ProvinceLager | 5-50 | Lager-Inhalt (Ressourcen-Speicher) |
| `game_log_entries` | GameLogEntry | 100-5000 | Spielereignisse (öffentlich, privat) |
| `trade_routes` | TradeRoute | 5-30 | Handelsrouten (zwischen Provinzen) |
| `market_stands` | MarketStand | 10-50 | Marktplatz-Stände (Artikel, Preise) |
| `kontor_prices` | KontorPrice | 10-50 | Kontor-Preise (zentraler Handel) |
| `province_climate` | ProvinceClimate | 5-50 | Wetter-Daten (Bodenfeuchtigkeit, Grundwasser) |
| `province_tags` | ProvinceTag | 10-50 | Provinz-Tags (Organisation) |
| `province_settings` | ProvinceSettings | 5-50 | Provinz-Einstellungen (Steuer, Moral) |
| `tax_settings` | TaxSettings | 5-50 | Steuer-Einstellungen (Sätze, Feiertage) |
| `vorkommen` | Vorkommen | 30+ | Vorkommen (Erzminen, Ölfelder) |
| `terrain_configs` | TerrainConfig | 45+ | Terrain-Typen (Wüste, Wald) |
| `map_cells` | MapCell | 500-2000 | Weltkarte-Zellen (x, y, terrain_id) |
| `diplomacy_relations` | DiplomacyRelation | 10-50 | Diplomatie (Allianzen, Kriege) |
| `regierungsformen` | Regierungsform | 10+ | Regierungsformen (Demokratie, Monarchie) |
| `population_cohorts` | PopulationCohort | 20-100 | Bevölkerung (Altersgruppen) |
| `siedler_expeditions` | SiedlerExpedition | 0-20 | Siedler-Expeditionen (Gründung neuer Provinzen) |
| `province_transfers` | ProvinceTransfer | 0-10 | Provinz-Übertragungen (zwischen Spielern) |
| `system_locks` | SystemLock | 0-5 | System-Sperren (temporäre Sperrungen) |
| `quick_build_sessions` | QuickBuildSession | 0-10 | Schnellbau-Sitzungen (Admin-Tool) |
| `combat_logs` | CombatLog | 50-200 | Kampf-Protokolle (Schlachten) |
| `player_messages` | PlayerMessage | 10-100 | Spieler-Nachrichten (privat) |
| `admin_logs` | AdminLog | 50-200 | Admin-Aktivitäten (Protokoll) |
| `tick_logs` | TickLog | 100-500 | Server-Tick-Protokolle (jeder Tick) |
| `articles` | Article | 100+ | Artikel (Handelswaren) |
| `animal_templates` | AnimalTemplate | 15+ | Wildtier-Typen (Hirsche, Wildschweine) |
| `province_animals` | ProvinceAnimal | 10-50 | Wildtiere in Provinzen |
| `province_units` | ProvinceUnit | 20-100 | Provinz-Einheiten (Militär) |
| `province_fields` | ProvinceField | 50-200 | Provinz-Felder (Stadtpläne) |
| `city_expansion_configs` | CityExpansionConfig | 1-5 | Stadterweiterungs-Konfigurationen |

---

## Anhang F: Häufige Befehle

```bash
# Server starten (Entwicklung)
uvicorn app.main:app --reload

# Server starten (Production mit Gunicorn)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# Tests ausführen
python3 -m pytest tests/ -v

# Datenbank-Indizes erstellen
python3 scripts/db_index_migration.py

# Seed-Daten importieren
python3 seeds/seed_main.py

# Datenbank-Backup erstellen
./scripts/backup_database.sh

# SSL-Zertifikate generieren
./scripts/generate_ssl_certs.sh

# Datenbank komprimieren (bereinigt ungenutzten Speicher)
sqlite3 verbrannte_zone.db "VACUUM;"

# Datenbank-Größe prüfen
du -sh verbrannte_zone.db

# Server-Logs anzeigen
tail -f logs/wasteland.log

# Health-Check prüfen
curl http://localhost:8000/api/health

# API-Dokumentation öffnen (Browser)
open http://localhost:8000/api/docs

# Admin-Oberfläche öffnen (Browser)
open http://localhost:8000/admin.html

# Server stoppen
killall uvicorn  # oder killall gunicorn
```

---

**Ende der Dokumentation.**

Für Fragen oder Probleme konsultiere die Troubleshooting-Sektion (Kapitel 14) oder öffne ein Issue im Repository.

**Letzte Aktualisierung:** 2026-10-14  
**Dokumentationsversion:** 1.8

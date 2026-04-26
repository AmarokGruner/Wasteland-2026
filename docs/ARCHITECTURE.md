# Verbrannte Zone - System Architektur

## Überblick

**FastAPI Backend** + **SQLite** + **modulares Frontend**

### Tech Stack

| Layer | Technologie |
|-------|---|
| Backend | FastAPI 0.109.0 |
| ORM | SQLAlchemy 2.0 |
| Datenbank | SQLite 3 |
| Auth | JWT (python-jose) |
| Frontend | Vanilla JS (modular) |
| Scheduler | BackgroundTasks |

## Projekt-Struktur

```
app/
├── main.py              # FastAPI App, Scheduler, Static Files
├── config.py            # Konfiguration (SECRET_KEY, etc.)
├── database.py          # SQLite Connection
├── models.py            # SQLAlchemy Models
├── api/                 # API Router
│   ├── auth.py         # /auth/* (JWT)
│   ├── admin/          # /admin/*
│   │   ├── users.py    # Benutzerverwaltung
│   │   └── city_grid.py # Grid-Endpoints
│   ├── crawler.py      # /api/admin/crawler/*
│   └── world.py        # /api/world/*
├── building_logic.py    # Building-Logik
├── road_logic.py        # Straßen & AP-System
├── round_logic.py       # Produktions-Runden
└── tick_logic.py        # Hourly Tick Engine
```

## Datenbank-Modelle (Kern)

### Core Tables

| Tabelle | Zweck |
|---|---|
| `players` | Spieler-Daten |
| `provinces` | Spieler-Provinzen |
| `building_typen` | Gebäude-Definitionen |
| `ressourcen` | Rohstoffe |
| `vorkommen` | Ressourcen-Spots |
| `gebaeude_instances` | Gebaute Gebäude |
| `roads` | Straßennetz |
| `gamelog` | Welt-Ereignisse |
| `crawl_sessions` | Crawler-Sessions |
| `crawl_changes` | Pending Changes |

### Crawler-Tabellen

```sql
crawl_sessions:
  - id, started_at, completed_at, status (pending|running|completed|failed)
  - categories (JSON), dry_run, total_changes, error_message

crawl_changes:
  - id, session_id, category, action (INSERT|UPDATE|REJECT)
  - record_id, table_name, old_data_json, new_data_json
  - changed_fields JSON, approved, rejected
```

## Auth-System

### JWT Flow

```
1. Login (POST /api/auth/login)
   → Check credentials
   → Generate JWT access_token + refresh_token
   → Return token + role

2. Authenticated Request
   → Header: Authorization: Bearer <access_token>
   → JWT validate (app/api/auth.py)
   → Return user context

3. Token Refresh (POST /api/auth/refresh)
   → Header: Authorization: Bearer <refresh_token>
   → New access_token generieren
```

### Rollen

- `admin` → Volle Berechtigungen
- `player` → Spieler-spezifische Endpunkte

## Building System v3

### 15x15 Grid

```
Level 1: Start (4x4) → Level 2: 6x6 → ... → Level 8: 15x15
```

### Building-Logik

```
can_build(province_id, x, y, building_type):
  → Grid-Check (frei?)
  → Level-Check (Unlocked?)
  → Kosten-Check (MIPS genug?)
  → Konnektivität (Straße vorhanden?)

build(province_id, x, y, building_type):
  → MIPS debitieren
  → Instance erstellen
  → Produktions-Config setzen
```

## Finanzen-System (4-Konten)

```
1. Spielerkonto: Persönliche Geld
2. Betriebskonto: Gebäude-Produktion
3. Staatskonto: Steuern, Ausgaben
4. PKV-Konto: Krankenversicherung

Fluss:
  Spielerverkauf → Spielerkonto
  Steuer → Staatskonto
  Produktions-MIPS → Betriebskonto
  Krankenbehandlung → PKV-Konto
```

## Tick-System

```
Hourly Tick (app/main.py Scheduler):
  → Alle 60 Sekunden
  → production_round() für alle Provinzen
  → resource_regeneration()
  → trade_route_processing()
  → gamelog_events()

BackgroundTasks:
  → Crawler-Läufe (asynchron)
  → Long-running Tasks
```

## API-Design

### REST-Konventionen

```
GET    /api/resource          # Liste
GET    /api/resource/{id}     # Eintrag
POST   /api/resource          # Create
PUT    /api/resource/{id}     # Update
DELETE /api/resource/{id}     # Delete
```

### Crawler-API

```
POST   /api/admin/crawler/start
GET    /api/admin/crawler/status
GET    /api/admin/crawler/results
POST   /api/admin/crawler/approve/{id}
POST   /api/admin/crawler/reject/{id}
GET    /api/admin/crawler/export/csv
GET    /api/admin/crawler/export/json
```

## Security

### IMPORTANT ⚠️

```python
# app/config.py - SECRET_KEY MÜSSEN GEDREHT WERDEN!
SECRET_KEY = "your-secret-key-here"  # ⚠️ In Produktion ändern!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

### Best Practices

- JWT Tokens niemals im Logging
- SECRET_KEY in .gitignore
- HTTPS in Produktion
- Rate-Limiting aktivieren

---

**Version:** 3.5 | **Update:** 2026-04-05

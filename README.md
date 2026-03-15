# Verbrannte Zone

> Rundenbasiertes Postapo-Strategie-Browsergame

Erkunde eine verbrannte Welt, erobere Provinzen, baue Gebäude, produziere Ressourcen und handle mit Karren.

---

## Quickstart

```bash
git clone https://github.com/AmarokGruner/Wasteland.git
cd verbrannte-zone
pip install fastapi uvicorn pydantic
python seed_buildings_v5.py    # DB initialisieren (108 Gebäude + 65 Ressourcen + 20 Vorkommen)
python main.py                 # Server starten → https://localhost:8000
```

Öffne im Browser: `http://localhost:8000/login.html`

**Standard-Login (nach Init):**
```
Admin:  admin / admin
Spieler1: fabian / 123456
Spieler2: felix / 345678
```

> ⚠️ `SECRET_KEY` in `main.py` vor Produktiv-Deployment ändern!

---

## Features

### Spiel
- **Weltkarte** – 50×50 Felder, 41 Terrain-Typen, 2 Inseln
- **Provinzen** – 30×30 Grid, Besitz, Ressourcen-Lager pro Provinz
- **Ressourcen** – 65 Typen (Nahrung, Baustoffe, Genussgüter, Tiere, Waffen …)
- **Gebäude** – 108 Typen (Farm, Industrie, Wohnhaus, Küste, Forschung …) mit Level-Ausbau
- **Vorkommen** – 20 Typen (geologisch, Oberfläche, unt. Seen), terrain-abhängige Fundchance
- **Produktion** – Zeitbasiert, Terrain-Boni, Arbeiter/Wohnraum, Rohstoff-Ketten
- **Handel** – Transport per Handelskarren zwischen Provinzen

### System
- **User-System** – Login/Logout, Token-Auth, Rollen (admin/player)
- **Admin-Panel** – Verwaltung von Usern, Gebäuden, Ressourcen, Terrain, Regierungsformen u.v.m.
- **Login-Seite** – `login.html`, Token via localStorage

---

## Projektstruktur

```
verbrannte-zone/
├── main.py                    # Entry Point → ruft app/main.py
│
├── app/                       # Modularisiertes Backend (FastAPI)
│   ├── __init__.py
│   ├── main.py                # FastAPI App, Scheduler, Static Files
│   ├── config.py              # SECRET_KEY, DB_PATH, Token-Einstellungen
│   ├── database.py            # SQLite Connection Helper
│   ├── models.py              # SQLAlchemy Models (Province, Building, etc.)
│   │
│   ├── api/                   # API Endpoints (Router-basiert)
│   │   ├── __init__.py        # Exportiert api_router
│   │   ├── auth.py            # /auth/* Endpoints (Login, Logout, Token)
│   │   ├── roads.py           # Roads & Arbeitspunkte
│   │   └── admin/             # Admin-Router
│   │       ├── __init__.py
│   │       └── users.py       # /admin/users Endpoints
│   │
│   ├── building_logic.py      # Building Bau/Upgrade/Demolish Logik
│   ├── road_logic.py          # Roads & Straßennetz Logik
│   ├── round_logic.py         # Produktions-Runden-Logik
│   └── tick_logic.py          # Hourly Tick Engine
│
├── seeds/                     # Datenbank-Seed-Skripte
│   ├── seed_gebaeude.py       # 108 Gebäude
│   ├── seed_ressourcen.py     # 65 Ressourcen
│   └── ...
│
├── js/                        # Frontend (Vanilla JS)
│   ├── app.js                 # Hauptlogik + Auth-Check
│   ├── worldmap.js            # Weltkarte
│   └── ...
│
├── css/                       # Stylesheets
├── terrains/                  # Terrain-GIFs (41 Stück)
├── context/                   # AI-Context-System
│   ├── index.yaml             # Block-Index (Einstieg für Agents)
│   └── blocks/                # b-backend_*.yaml, b_admin_*.yaml ...
├── main_old.py                # Legacy (vor Modularisierung)
└── verbrannte_zone.db         # SQLite
```
verbrannte-zone/
├── main.py                    # FastAPI Backend
├── seed_buildings_v5.py       # DB-Init: 108 Gebäude + 65 Ressourcen + 20 Vorkommen
├── index.html                 # Frontend Entry (requires auth)
├── login.html                 # Login-Seite
├── admin.html                 # Admin-Panel (requires admin role)
├── resources.html             # Ressourcen-Übersicht
├── js/
│   ├── app.js                 # Hauptlogik + Auth-Check
│   ├── worldmap.js            # Weltkarte
│   ├── province.js            # Provinz-Ansicht
│   ├── transport.js           # Handelskarren
│   ├── resources.js           # Ressourcen-Ansicht
│   ├── world-data.js          # Welt-Daten
│   ├── terrain-types.js       # Terrain-Definitionen
│   └── buildings-data.js
├── css/
│   ├── style.css              # Haupt-Styles
│   └── styles.css             # Admin-Styles
├── terrains/                  # Terrain-GIFs (41 Stück)
├── context/                   # AI-Context-System
│   ├── index.yaml             # Block-Index (Einstieg für Agents)
│   ├── index.json
│   └── blocks/                # b-backend-*.yaml, b-admin-*.yaml ...
├── AGENTS.md                  # AI-Agent Onboarding
├── CONTEXT_MASTER.md          # Master-Übersicht (Schemas, Ketten, Stand)
└── verbrannte_zone.db         # SQLite (wird generiert)
```

---

## Tech Stack

| Schicht | Technologie |
|---------|-------------|
| Backend | Python 3, FastAPI, SQLite |
| Auth | SHA256-Token (localStorage), Rollen: admin/player |
| Frontend | Vanilla JS (ES6+), Canvas |
| Admin | admin.html (Standalone, Token-geschützt) |
| Styling | CSS3, CSS-Variablen |
| Context | YAML/JSON Blocks (agent-optimiert) |
| Deployment | Raspberry Pi 3B+ ready |

---

## Datenbank-Stand

| Datensatz       | Anzahl | Beschreibung |
|-----------------|--------|--------------|
| Gebäude-Typen   | 108    | Farm, Industrie, Wohnhaus, Küste, Weg, Vorgabe … |
| Ressourcen      | 65     | Nahrung, Baustoffe, Verbrauchsgüter, Tiere, Waffen … |
| Vorkommen       | 20     | Geologisch, Oberfläche, unt. Seen |
| Terrain-Typen   | 41     | Grasland, Gebirge, Eiswüste, Dschungel … |

---

## API Endpunkte (Auszug)

### Auth
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| POST | `/auth/login` | Login → Token |
| POST | `/auth/logout` | Token invalidieren |
| GET | `/auth/me` | Aktuellen User prüfen |

### Spieler & Welt
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET | `/player/{id}` | Spielerdaten |
| POST | `/player/{id}/resources/produce` | Produktionsrunde |
| GET | `/player/{id}/resources/total` | Ressourcen gesamt |
| GET/POST | `/player/{id}/provinzen` | Provinzen |
| POST | `/player/{id}/transport` | Handelskarren senden |

### Admin (role: admin)
| Methode | Pfad | Beschreibung |
|---------|------|--------------|
| GET/POST | `/admin/users` | User-Verwaltung |
| GET/PUT/POST/DELETE | `/admin/buildings` | Gebäude-Typen verwalten |
| GET/POST/PUT/DELETE | `/admin/regierungsformen` | Regierungsformen |

Vollständige Doku: `context/blocks/b-api-endpoints.yaml`

---

## DB-Tabellen

| Tabelle | Inhalt |
|---------|--------|
| `users` | Username, Passwort-Hash, Rolle, Player-ID, Token |
| `players` | Spieler, Ressourcen, Zeitstempel |
| `provinzen` | Besitz, Terrain, Koordinaten |
| `provinz_lager` | Ressourcen pro Provinz |
| `ressourcen` | 65 Typen |
| `buildings` | Platzierte Gebäude |
| `gebaeude_typen` | 108 Definitionen |
| `regierungsformen` | Regierungsformen mit Bonus/Malus |
| `roads` | Wege + Kreuzungen |
| `handelskarren_transport` | Transport-Log |
| `vorkommen` | 20 Terrain-Vorkommen mit Fundwahrscheinlichkeit |

---

## AI / Agent Onboarding

1. `AGENTS.md` lesen – Rollen & Workflow
2. `context/index.yaml` öffnen – Block-Übersicht
3. `CONTEXT_MASTER.md` – aktueller Datenstand, Schemas, Rohstoff-Ketten
4. Nur relevante Blocks laden – kein Full-Dump

---

## Admin-Panel

Das Admin-Panel (`admin.html`) verwaltet aktuell:
- Benutzer (anlegen, Rolle, Player-Zuordnung)
- Gebäude-Typen (CRUD)
- Rohstoffe, Vorkommen
- Gebäude-Felder, Terrain
- Regierungsformen
- Artikel, Einheiten-Typen, Lebewesen

**Noch nicht implementiert:**
- Spieler-Übersicht im Admin
- Passwort-Reset durch Admin
- Rollenbasierte Seitensperre im Frontend (außer Redirect)

---

## Roadmap

## Docker / Deployment

### Build the Docker image
```bash
docker build -t wasteland .
```

### Run the container (quick test)
```bash
docker run -d \
  -p 8000:8000 \
  -v "$(pwd)/verbrannte_zone.db:/app/verbrannte_zone.db" \
  -e SECRET_KEY=my_super_secret \
  --name wasteland \
  wasteland
```
- `-p 8000:8000` maps the FastAPI port.
- `-v …/verbrannte_zone.db:/app/verbrannte_zone.db` persists the SQLite DB.
- `-e SECRET_KEY=…` overrides the default secret.

### With docker‑compose (recommended for development)
```bash
docker compose up -d
```
The `docker-compose.yml` in the repository already contains the needed configuration (port mapping, DB volume, environment variable and restart policy).

### Access the API
Open your browser at `http://localhost:8000/docs` to view the Swagger UI or `http://localhost:8000/login.html` for the game UI.

### Notes
- The image uses `python:3.11‑slim`, which works on both x86_64 and ARM (Raspberry Pi).
- All Python dependencies are listed in `requirements.txt` and installed during the build.
- Adjust `SECRET_KEY` and other environment variables as needed for production.


- [x] Admin: fehlende Backend-Endpoints (Artikel, Einheiten, Lebewesen)
- [ ] Auth: JWT statt SHA256-Token
- [ ] Produktions-Logik: Arbeiter/Wohnraum vollständig binden
- [ ] Stadtfelder rendern
- [ ] Multiplayer
- [ ] Docker / Deployment-Skript

---

**License:** MIT | **Updated:** 2026-03-03 | **Version:** v5.7

# 🚀 START ANLEITUNG - Verbrannte Zone (v5.7)

> **Startdatum:** 2026-04-04  
> **Server-Port:** 8011 (Standard)  
> **Implementierungsstatus:** 95%+ ✅

---

## 📋 Schnellstart

### 1. Dependencies installieren
```bash
cd /workspace/project/Wasteland
pip install -r requirements.txt
```

### 2. Datenbank initialisieren (nur beim ersten Mal)
```bash
# Seeds ausführen (Gebäude, Ressourcen, Terrains, ...)
python seeds/seed_main.py
```

### 3. Server starten
```bash
python main.py
```

Server wird auf `http://localhost:8011` gestartet.

### 4. Im Browser öffnen
```
Spiel:     http://localhost:8011/login.html
API:       http://localhost:8011/docs
Admin:     http://localhost:8011/admin.html
Hilfe:     http://localhost:8011/help.html
```

### 5. Login
```
Admin:    admin / admin
Spieler:  fabian / 123456    oder    felix / 345678
```

> ⚠️ **Sicherheitshinweis:**  
> - Alle Passwörter sind als **SHA256-Hash** in der Datenbank gespeichert  
> - `SECRET_KEY` in `app/config.py` vor Production-Deployment ändern!

---

## 🔧 Konfiguration

### Port-Konfiguration
- **Standard-Port:** 8011
- **Alternative Ports:** 8012 (gemäß work_hosts)
- **Port 8000:** Wird vermieden (Kollisionsgefahr mit anderen Diensten)

Um den Port zu ändern:
```bash
# In main.py Zeile 15 anpassen
python main.py  # Verwendet Port 8011

# Oder mit Environment-Variable
uvicorn app.main:app --host 0.0.0.0 --port 8012
```

### Environment-Variablen
```bash
# app/config.py verwendet:
SECRET_KEY=wurzelnder_secret_key_2026  # Ändern vor Production!
DB_PATH=verbrannte_zone.db

# Environment-Variable setzen (vor Start):
export SECRET_KEY=my_secure_secret_key
```

---

## 📁 Projektstruktur

```
Wasteland/
├── main.py                    # Entry Point → Port 8011
├── app/                       # Backend (FastAPI)
│   ├── main.py                # FastAPI App + Scheduler
│   ├── config.py              # SECRET_KEY, DB_PATH
│   ├── database.py            # DB-Connections
│   ├── models.py              # SQLAlchemy Models
│   │
│   ├── api/                   # API Router
│   │   ├── auth.py            # /api/auth/*
│   │   ├── province.py        # /api/province/*
│   │   ├── market.py          # /api/market/*
│   │   ├── player.py          # /api/player/*
│   │   ├── army.py            # /api/army/*
│   │   ├── world.py           # /api/world/*
│   │   ├── gamelog.py         # /api/gamelog/*
│   │   ├── messages.py        # /api/messages/*
│   │   ├── city_grid.py       # /api/city_grid/*
│   │   ├── help.py            # /api/help/*
│   │   └── admin/             # /api/admin/* (11+ Modules)
│   │
│   ├── building_logic.py      # Gebäude-Logik
│   ├── road_logic.py          # Straßen/AP-System
│   ├── round_logic.py         # Produktions-Runden
│   ├── tick_logic.py          # Hourly Tick Engine
│   ├── finance_logic.py       # 4-Konten-System
│   ├── market_logic.py        # Marktstände
│   ├── trade_route_logic.py   # Handelskarren
│   ├── population_logic.py    # Altersstruktur
│   ├── kultur_bildung_logic.py
│   ├── regierungsform_logic.py
│   ├── military_logic.py      # Armeen
│   ├── combat_logic.py        # Kampfsystem
│   ├── diplomacy_logic.py     # Diplomatie
│   ├── animal_logic.py        # Tierzucht
│   ├── sammler_jaeger_logic.py
│   ├── bunker_logic.py
│   ├── climate_logic.py
│   ├── gamelog_logic.py
│   └── siedler_logic.py
│
├── js/                        # Frontend (Vanilla JS)
│   ├── app.js                 # Hauptlogik
│   ├── worldmap.js            # 50x50 Weltkarte
│   ├── province.js            # Provinz-Ansicht
│   ├── province_grid.js       # 15x15 Grid
│   ├── transport.js           # Handelskarren
│   ├── buildings-data.js
│   ├── auth-service.js
│   ├── terrain-types.js
│   ├── onboarding.js
│   └── ...
│
├── css/                       # Stylesheets
├── terrains/                  # 41 Terrain-GIFs
├── images/                    # Gebäude-Bilder
├── context/                   # AI-Context-System
│   ├── index.yaml             # Block-Index
│   └── blocks/                # Modulare Blocks
├── seeds/                     # Datenbank-Seed-Skripte
├── docs/                      # Feature-Dokumentationen
├── webcrawler/                # Webcrawler für Updates
│   ├── main.py
│   ├── parsers/               # 8 Parser-Module
│   └── ...
├── README.md                  # Projekt-README
├── CONTEXT_MASTER.md          # Master-Dokument
├── AGENTS.md                  # AI-Agent Onboarding
├── PROJEKT_DOKUMENTATION.md   # Umfassende Dokumentation
├── start_anleitung.md         # Diese Datei
└── verbrannte_zone.db         # SQLite Datenbank
```

---

## 📡 API Überblick

### Auth (`/api/auth/*`)
| Method | Endpoint | Beschreibung |
|---|---|---|
| POST | `/register` | Benutzer registrieren |
| POST | `/login` | Login → JWT-Token |
| POST | `/logout` | Token invalidieren |
| POST | `/refresh` | Token refreshen |
| POST | `/reset-password` | Passwort zurücksetzen |

### Spieler (`/api/player/{id}/*`)
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/resources/total` | Alle Ressourcen |
| GET | `/tech` | Tech-Level |
| GET | `/diplomacy` | Diplomatieverhältnisse |
| POST | `/diplomacy` | Diplomatie setzen |
| POST | `/regierungsform` | Regierungsform ändern |

### Provinz (`/api/province/{id}/*`)
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/fields` | City-Grid anzeigen |
| POST | `/build` | Gebäude bauen |
| POST | `/demolish/{field_id}` | Gebäude abreißen |
| GET | `/finance` | Finanzen |
| GET | `/animals` | Tiere verwalten |
| POST | `/feiertag` | Feiertag aktivieren |
| GET | `/climate` | Klima/Daten |
| GET | `/deposits` | Vorkommen anzeigen |

### Handel (`/api/market/*`)
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/stands` | Marktstände |
| POST | `/stands` | Stand erstellen |
| POST | `/kontor/prices` | Kontorpreise |
| POST | `/trade-route/create` | Handelsroute erstellen |

### Militär (`/api/army/*`)
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/player/{id}/armies` | Alle Armeen |
| POST | `/{army_id}/move` | Armee bewegen |
| POST | `/{army_id}/retreat` | Armee zurückzogen |

### Admin (`/api/admin/*`)
| Method | Endpoint | Beschreibung |
|---|---|---|
| GET | `/users` | Benutzer-Verwaltung |
| POST | `/users` | Benutzer erstellen |
| POST | `/player/{id}/ban` | Benutzer bannen |
| GET | `/dashboard` | Dashboard-Statistiken |
| GET | `/ticks/status` | Tick-Status |
| POST | `/ticks/force` | Tick erzwingen |
| POST | `/world/generate` | Welt generieren |

---

## 🐳 Docker Deployment

### Build Image
```bash
docker build -t wasteland .
```

### Run Container
```bash
docker run -d \
  -p 8011:8011 \
  -v "$(pwd)/verbrannte_zone.db:/app/verbrannte_zone.db" \
  -e SECRET_KEY=my_super_secret \
  --name wasteland \
  wasteland
```

### Docker Compose
```bash
docker compose up -d
```

### Container stoppen
```bash
docker stop wasteland
docker rm wasteland
```

---

## 🛠️ Troubleshooting

### Port 8011 belegt
```bash
# Prüfen ob Port belegt ist
lsof -i :8011

# Anderen Port verwenden
uvicorn app.main:app --host 0.0.0.0 --port 8012
```

### Database-Fehler
```bash
# Backup erstellen
cp verbrannte_zone.db verbrannte_zone.db.backup

# Neu initialisieren
rm verbrannte_zone.db
python seeds/seed_main.py
```

### Server startet nicht
```bash
# Logs prüfen
tail -f /tmp/server.log

# Dependency-Check
pip install -r requirements.txt --force-reinstall
```

---

## 📚 Weitere Dokumentationen

- **README.md** - Projekt-Übersicht
- **CONTEXT_MASTER.md** - Datenstand, Schemas
- **AGENTS.md** - AI-Agent Onboarding
- **PROJEKT_DOKUMENTATION.md** - Umfassende Dokumentation
- **docs/** - 37+ Feature-Dokumentationen
- **webcrawler/README.md** - Webcrawler-Dokumentation

---

## 📞 Support & Infos

**Admin-Zugang:**  
- Username: `admin`
- Password: `admin` (SHA256-hash in DB)

**Webcrawler:**  
`cd webcrawler && python main.py --dry-run --verbose`

**API-Spec:**  
`http://localhost:8011/openapi.json`

---

**Version:** v5.7  
**Erstellt:** 2026-04-04  
**Status:** 95%+ Implementiert ✅

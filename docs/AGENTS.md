# Verbrannte Zone - AI Agent Onboarding Guide

**Version:** 4.0 | **Last Updated:** 2026-04-05 | **Status:** 🟢 Active

---

## 🔑 Quick Start für KI-Agenten

### So startest du:

1. **Lade nur 2-3 relevante Blocks** (nie alle auf einmal!)
```yaml
# Empfohlene Start-Kombination:
- b-core-overview    # Projekt-Überblick
- b-api-endpoints    # API-Struktur
- b-crawler          # Aktuelle Integration
```

2. **Verwende `context/blocks/`** für kontextspezifische Information
3. **Aktualisiere bei Änderungen** die betroffenen Blocks + `index.yaml`

### ⚠️ WICHTIG - Token-Effizienz

- **Max 250 tokens pro Block**
- **Nur notwendige Blocks laden**
- **Nach jeder Änderung: Dokumentation aktualisieren**

---

## 📚 Dokumentations-Struktur

```
docs/
├── AGENTS.md                    ← DU BIST HIER (Onboarding)
├── README.md                    # Human-Lesbarer Projekt-Einstieg
├── MANUAL.md                    # User Manual (Admin-UI, Crawler)
├── DEVELOPER.md                 # Setup, CI/CD, Guidelines
├── ARCHITECTURE.md              # Systemdesign & Datenfluss
└── CHANGELOG.md                 # Änderungsverlauf

context/
└── blocks/                      # KI-Agent Blocks (modular)
    ├── index.yaml               # Block-Index für Loader
    ├── b-core-overview.yaml
    ├── b-auth-system.yaml
    ├── b-api-endpoints.yaml
    ├── b-crawler.yaml
    └── ...

archive/docs/                    # ⚠️ Alte Dokumentation (nicht lesen)
```

---

## 🧩 Available Blocks (Index)

| Block ID | Topic | Tokens | Last Update | sources |
|----------|-------|--------|-------------|---------|
| `b-core-overview` | Projekt-Übersicht, Architektur | 200 | 2026-04-05 | `app/main.py`, `README.md` |
| `b-auth-system` | JWT-Auth, User-Modelle, Rollen | 220 | 2026-04-05 | `app/api/auth.py`, `app/models.py` |
| `b-api-endpoints` | Alle REST-API Endpunkte | 240 | 2026-04-05 | `app/api/*.py` |
| `b-crawler` | Webcrawler-Integration | 240 | 2026-04-05 | `app/api/crawler.py` |
| `b-admin-ui` | Admin-UI Struktur & Module | 230 | 2026-04-05 | `admin.html` |
| `b-building-system` | Building-Logik, Grid, AP-System | 240 | 2026-04-05 | `app/building_logic.py` |
| `b-finance-system` | 4-Konten-System, Steuern | 210 | 2026-04-05 | `app/finance_logic.py` |
| `b-market-system` | Marktstände, Trade-Logik | 220 | 2026-04-05 | `app/market_logic.py` |

**Lade nicht mehr als 3-5 Blocks gleichzeitig!**

---

## 🗂️ Code-Struktur

```
app/
├── main.py                 # FastAPI App, Scheduler, Static Files
├── config.py               # SECRET_KEY, Token-Config
├── database.py             # SQLite Connection, get_db()
├── models.py               # SQLAlchemy Models (+ CrawlSession, CrawlChange)
│
├── api/                    # REST-API Router
│   ├── __init__.py         # Router-Registrierung
│   ├── auth.py             # /auth/* (JWT Login/Logout)
│   ├── crawler.py          # /admin/crawler/* (Webcrawler)
│   ├── messages.py         # /messages/* (Nachrichten)
│   ├── city_grid.py        # /province/{id}/fields (Building)
│   ├── admin/              # Admin-Endpoints
│   │   ├── users.py        # /admin/users
│   │   └── city_grid.py    # /admin/city-config
│
├── building_logic.py       # Building-Logik (can_build, build, upgrade)
├── road_logic.py           # Straßennetz & AP-System
├── round_logic.py          # Produktions-Runden
├── tick_logic.py           # Hourly Tick Engine
├── finance_logic.py        # 4-Konten-System
├── market_logic.py         # Markt-Logik
└── crawler_logic.py        # SyncEngine (Crawler-Datenvergleiche)

admin/
├── html/                   # Modularisierte Admin-UI (11 Module)
│   ├── dashboard.html
│   ├── crawler.html
│   ├── players.html
│   └── ...
├── js/                     # JavaScript Services
│   ├── services/
│   │   ├── crawler.js
│   │   ├── auth.js
│   │   └── ...
│   └── admin.js            # Haupt-JS

tests/                      # Test-Suite
├── test_fetcher.py
├── test_parsers.py
├── test_sync_engine.py
└── ...
```

---

## 🔄 Agent Working Guidelines

### 1. BEVOR DU ARBEITEST

```yaml
# Schritt 1: Block laden
- context/blocks/b-<topic>.yaml  (max 3-5)

# Schritt 2: Code analysieren
- Betroffene Dateien finden
- Abhängigkeiten verstehen

# Schritt 3: Plan erstellen
- Task Tracking nutzen
- User bestätigen lassen
```

### 2. WÄHREND DER ARBEIT

```python
# Code-Änderungen
- Immer auf bestehenden Code updaten (nicht duplizieren!)
- Import-Hierarchie beachten (keine cyclic deps)

# Tests schreiben
- Mindestens 1 Test pro neuer Funktion
- tests/ Ordner nutzen

# Dokumentation
- Bei Code-Änderungen: betroffenen Block finden
- updated_at Timestamp setzen
- sources aktualisieren
```

### 3. NACH DER ARBEIT

```yaml
# Pflichtaufgaben:
1. CHANGELOG.md eintragen
2. Update affected context/blocks/*
3. index.yaml aktualisieren
4. Git Commit: "feat: description"

# Optional:
5. FAIL_LOG.md wenn Fehler aufgetreten
6. User: "Dokumentation aktualisiert" bestätigen
```

---

## ⚓ Security Rules

- **SECRET_KEY** in `app/config.py` → **muss vor Prod-Deployment geändert werden!**
- JWT-Tokens mit `python-jose` verwalten
- Admin-Endpoints mit `@admin_required` dekorieren
- SQL-Injection vermeiden → SQLAlchemy ORM nutzen

---

## 🚦 Projekt-Status

| Feature | Status | Next Steps |
| --- | --- | ---------- |
| Auth System | ✅ Aktiv | - |
| Admin-UI Modularisierung | ✅ Aktiv | - |
| Webcrawler Integration | ✅ Aktiv | Scheduled Crawls |
| Building System | ✅ Aktiv | - |
| Finance System | ✅ Aktiv | - |
| Market System | ✅ Aktiv | - |

---

## 📍 Nächste Schritte (Roadmap)

1. **Scheduled Crawls** - APScheduler Integration
2. **Webhooks** - Event Notifications
3. **Bulk Actions** - Massen-Aktionen in Admin-UI
4. **Test Coverage** - Testsuite erweitern
5. **API Dokumentation** - OpenAPI/Swagger Generator

---

**Agent Checklist vor PR:**
- [ ] Code funktioniert (`python main.py` startet)
- [ ] Tests geschrieben/aktualisiert
- [ ] affected Blocks in `context/blocks/` updated
- [ ] `index.yaml` aktualisiert
- [ ] CHANGELOG.md aktualisiert
- [ ] updated_at Timestamps gesetzt

**Frage?** → `context/blocks/b-core-overview.yaml` lesen oder User fragen!

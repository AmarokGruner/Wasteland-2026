# Verbrannte Zone - Admin Interface

> **Wasteland Game Admin Dashboard** - Webcrawler-Integration, Spielerverwaltung, Weltsteuerung

---

## 🚀 Quick Start

```bash
# Server starten
python main.py

# Admin-UI öffnen
http://localhost:8011/admin.html

# Login
admin / admin
```

---

## 📁 Projektstruktur

```
Wasteland/
├── app/                    # Backend FastAPI Application
│   ├── api/               # API Router (Auth, Admin, World, Crawler)
│   ├── admin/             # Admin-Sub-Router
│   ├── models.py          # SQLAlchemy DB Models
│   ├── database.py        # SQLite Connection & Session
│   ├── config.py          # Konfiguration (SECRET_KEY, etc.)
│   ├── main.py            # FastAPI App Entry Point
│   └── ...              # Logik-Module (building, road, round, tick)
│
├── admin/                 # Admin-UI (Frontend)
│   ├── admin.html         # Haupt-Admin-Oberfläche (modular)
│   ├── js/                # JavaScript Services
│   │   └── services/      # Crawler, Player, Building Services
│   └── css/              # Admin-Styles
│
├── tests/                 # Pytest Test Suite
│   ├── test_fetcher.py
│   ├── test_parsers.py
│   ├── test_sync_engine.py
│   └── ...
│
├── context/               # Agent Context Blocks (KI-Onboarding)
│   ├── index.yaml        # Block-Index für KI-Lader
│   └── blocks/           # Modularisierte Kontext-Blocks
│
├── docs/                  # Dokumentation (neu strukturiert)
│   ├── README.md         # ← Du bist hier
│   ├── MANUAL.md         # Admin-UI Handbuch
│   ├── DEVELOPER.md      # Entwicklereinrichtung
│   ├── ARCHITECTURE.md   # Systemdesign
│   └── AGENTS.md         # KI-Agent Onboarding
│
├── archive/              # Veraltete Dokumente/Dateien
│   └── docs/             # Altes Markdown (historisch)
│
└── verbrannte_zone.db    # SQLite Datenbank
```

---

## 🔧 Kern-Features

| Feature | Status | Docs |
|---|--|--|
| Admin-UI (11 Module) | ✅ | [docs/MANUAL.md](MANUAL.md) |
| Webcrawler-Integration | ✅ | [docs/MANUAL.md#crawler](MANUAL.md) |
| Auth-System (JWT) | ✅ | [docs/ARCHITECTURE.md#auth](ARCHITECTURE.md) |
| Building System v3 | ✅ | [docs/MANUAL.md#building](MANUAL.md) |
| 4-Konten-System | ✅ | [docs/ARCHITECTURE.md#finance](ARCHITECTURE.md) |
| Handelsrouten | ✅ | [docs/MANUAL.md#trade](MANUAL.md) |

---

## 🤖 KI-Agent Onboarding

**Für KI-Agenten:** Lies zuerst [AGENTS.md](AGENTS.md) für effizientes Arbeiten.

**Quick Onboarding:**
1. `context/index.yaml` öffnen - Block-Index laden
2. Relevante Blocks auswählen (max 3-5 gleichzeitig)
3. Bei Änderungen: `updated_at` und `sources` aktualisieren
4. Nach Abschluss: `CHANGELOG.md` eintragen

---

## 📖 Wichtige Dokumente

| Dokument | Zweck | Zielgruppe |
|---|--|--|
| [MANUAL.md](MANUAL.md) | Feature-Dokumentation, API-Refs | Entwickler, Support |
| [DEVELOPER.md](DEVELOPER.md) | Setup, CI/CD, Contributing | Neue Entwickler |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Systemdesign, Datenfluss | Architekten, KI-Agenten |
| [AGENTS.md](AGENTS.md) | KI-Onboarding, Workflows | KI-Agenten |
| [CHANGELOG.md](CHANGELOG.md) | Versionshistorie | Alle |
| [FAIL_LOG.md](FAIL_LOG.md) | Fehler-Dokumentation | Entwickler |

---

## 🛠️ Nächste Schritte

**Als Entwickler:**
1. [DEVELOPER.md](DEVELOPER.md) lesen - Setup
2. `python -m pytest tests/` - Tests ausführen
3. Feature hinzufügen → CHANGELOG.md eintragen

**Als KI-Agent:**
1. [AGENTS.md](AGENTS.md) lesen - Onboarding
2. Relevante Blocks aus `context/index.yaml` laden
3. Bei Änderungen: Dokumentation aktualisieren!

**Als Admin:**
1. [MANUAL.md](MANUAL.md) lesen - Features
2. Admin-UI: `http://localhost:8011/admin.html`
3. Webcrawler im Admin-Tab nutzen

---

## 📞 Support

- **Issues:** Öffne ein Issue im GitHub Repository
- **Docs:** Fehlt etwas? Erstelle eine PR für docs/!
- **Archiv:** Historische Docs → `archive/docs/`

---

**Version:** 3.5  
**Update:** 2026-04-05  
**Maintainer:** OpenHands Agent

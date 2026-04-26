# AGENTS.md – Open Context Standard v2.3.0

## Purpose
Standardisierte Rollen und Workflows für AI-Agents (Perplexity, Copilot etc.).
Ziel: Schnelles Onboarding ohne Context-Überladung – via modulare Blocks in `context/`.

**Version:** v3.1 | **Updated:** 2026-03-16

---

## Block-Schema (YAML – mandatory fields)

```yaml
id: "b-backend-health"
type: "overview|api|code|risks|deployment|auth|admin"
domain: "backend|frontend|data|ui|security|admin"
title: "Backend Health Status"
summary: "FastAPI v2.3.0, SQLite DB, Auth-System, Admin-Panel"   # <100 tokens
details: |
  Markdown-Inhalt, Tabellen, Code-Snippets etc.
sources: ["main.py", "admin.html"]
related_blocks: ["b-api-endpoints", "b-auth-system"]
tokens_estimate: 250
created_at: "2026-03-01T21:00:00Z"
updated_at: "2026-03-01T21:00:00Z"
status: "active"
```

---

## Agent Roles

| Role | Aufgabe | Trigger |
|------|---------|---------|
| **ContextLoader** | Relevante Blocks laden (domain-basiert) | "zeig backend endpoints" |
| **BlockCreator** | Neuen Block aus Rohinhalten erstellen | "erstelle block für api-docs" |
| **Validator** | Schema-Check, Token-Limits, Konsistenz | "validiere alle blocks" |
| **Migrator** | Alte CONTEXT_vX.md → Blocks konvertieren | "migriere context v1.9" |
| **Onboarder** | 3-5 Core-Blocks als Seed-Prompt laden | "quick onboard" |
| **AuthReviewer** | Auth/Security-Blocks prüfen (Token, Hashing) | "review auth system" |
| **AdminMapper** | Admin-Panel-Endpoints + fehlende Features dokumentieren | "was fehlt im admin?" |

---

## Workflow

```
Query
  → AGENTS.md Roles auswählen
  → context/index.yaml laden
  → Passende Blocks selektieren
  → Nur diese Blocks in Context laden
  → Antwort mit Zitaten
```

### Onboarding-Sequenz (empfohlen)
1. `context/index.yaml` öffnen
2. Blocks: `b-backend-health` + `b-api-endpoints` + `b-auth-system` laden
3. Optional: `b-admin-panel` für Admin-Aufgaben
4. Optional: `b-frontend-flow` für UI-Aufgaben
5. **Nie:** alle Blocks auf einmal (Context-Overflow!)

---

## Block Index (v2.3.0)
- **Datei:** `context/index.yaml` + `context/index.json`
- **Pfad:** `context/blocks/b-<topic>.yaml`
- **Konvention:** `b-<domain>-<topic>.yaml`

### Aktuelle Blocks
**Backend:**
- b-backend-health, b-backend-architecture, b-backend-endpoints
- b-api-endpoints, b-openapi-spec

**Auth & Admin (NEU v2.3.0):**
- b-auth-system ← Login/Logout/Token/Rollen
- b-admin-panel ← Verwaltungs-UI, offene Features
- b-admin-endpoints ← /admin/* REST-Routen

**Frontend:**
- b-frontend-flow, b-frontend-endpoints
- b-frontend-ux-guidelines, b-frontend-performance
- b-ui-component-library, b-ui-interactions

**Data:**
- b-world-endpoints, b-data-models, b-merged-master

**Kolonisierung & Kommunikation (NEU v3.2):**
- b-siedler-kolonisierung ← Siedler-Expeditionen, Provincia-Transfer
- b-gamelog-system ← Gamelog, Weltereignisse, Notification-Settings
- b-player-messaging ← Direktnachrichten, Posteingang/Ausgang

**Wirtschaft & Handel (NEU v3.4):**
- b-finance-system ← 4-Konten-System, Steuern, PKV, Staatskonto
- b-market-system ← Marktstände, Bedarfsberechnung, Auto-Buy
- b-trade-logistics ← Handelsrouten, Handelskarren, Siedler (20-25 J.)
- b-coastal-features ← Häfen, See-Zugang, Entsalzungsanlagen

**Building System v3 (NEU v3.3):**
- b-admin-city-grid ← 15x15 Grid Config, Level Unlocks
- b-province-city-grid ← Player Grid View, Building/Demolish Rules
- b-city-expansion-logic ← Progressive Unlock Logic, Level 1-8

---

## Security-Hinweise für Agents
> Das aktuelle Auth-System nutzt JWT-Tokens (`python-jose`).
> `SECRET_KEY` in `app/config.py` → **muss vor Produktiv-Deployment geändert werden!**
> Block `b-auth-system` enthält alle Details + offene Punkte.

---

## Konsistenz-Regeln
- Format: YAML (lesbar) oder JSON (maschinell), UTF-8
- Alle mandatory fields müssen vorhanden sein
- `tokens_estimate` immer befüllen
- Nach jedem Update → `index.yaml` + `index.json` aktualisieren

---

## Code-Struktur für Agents (Modularisiert v3.0)

```
app/
├── main.py            → FastAPI App, Scheduler, Static Files
├── config.py          → SECRET_KEY, ALGORITHM, Token-Config (ausgelagert)
├── database.py        → SQLite Connection
├── models.py          → SQLAlchemy Models (Province, Building, RoadInstance)
│
├── api/               → API Router (NEU in v3.0)
│   ├── __init__.py    → exportiert api_router
│   ├── auth.py        → /auth/* Endpoints (JWT-basiert)
│   ├── gamelog.py     → /gamelog/* Endpoints
│   ├── messages.py    → /messages/* Endpoints
│   ├── city_grid.py   → /province/{id}/fields & /build Endpoints
│   └── admin/         → Admin-Router
│       ├── users.py   → /admin/users Endpoints
│       └── city_grid.py → /admin/city-config Endpoints
│
├── building_logic.py  → Building-Logik (can_build, build, upgrade, demolish)
├── road_logic.py      → Roads & Straßennetz (BFS-Konnektivität, AP-System)
├── round_logic.py     → Produktions-Runden (AP-Generierung, simulate_round)
└── tick_logic.py      → Hourly Tick Engine
```

### Für Agent-Relevante Dateien:
- **Auth**: `app/api/auth.py` + `app/config.py`
- **Bunker & Start**: `app/bunker_logic.py`, `app/api/world.py` (/claim)
- **Buildings**: `app/building_logic.py`, `app/models.py`
- **Roads/AP**: `app/road_logic.py` + `app/round_logic.py`
- **Finance & Market**: `app/finance_logic.py` + `app/market_logic.py`
- **Trade & Logistics**: `app/trade_route_logic.py`
- **Help & FAQ (NEU v3.5)**: `app/api/help.py`, `help.html`
- **DB**: `app/models.py`, `app/database.py`

---

## Quellen
- AGENTS.md (v2.3.0), README.md, app/main.py, app/config.py, main_old.py

**Updated: 2026-04-04 | Version: v5.7 (Vollständig Implementiert)**

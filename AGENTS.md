# AGENTS.md – Open Context Standard v2.3.0

## Purpose
Standardisierte Rollen und Workflows für AI-Agents (Perplexity, Copilot etc.).
Ziel: Schnelles Onboarding ohne Context-Überladung – via modulare Blocks in `context/`.

**Version:** v2.3.0 | **Updated:** 2026-03-01

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

---

## Security-Hinweise für Agents
> Das aktuelle Auth-System nutzt SHA256-Tokens (kein JWT).
> `SECRET_KEY` ist hardcoded → **muss vor Produktiv-Deployment geändert werden.**
> Block `b-auth-system` enthält alle Details + offene Punkte.

---

## Konsistenz-Regeln
- Format: YAML (lesbar) oder JSON (maschinell), UTF-8
- Alle mandatory fields müssen vorhanden sein
- `tokens_estimate` immer befüllen
- Nach jedem Update → `index.yaml` + `index.json` aktualisieren

---

## Quellen
- AGENTS.md (orig v2.2.0), README-5.md, main-2.py, admin.html, login.html, app.js

**Updated: 2026-03-01 | Version: v2.3.0**

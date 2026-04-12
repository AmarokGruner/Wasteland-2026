# Verbrannte Zone - AI Agent Onboarding Guide (Hermes Edition)

**Version:** 5.0 | **Last Updated:** 2026-04-12 | **Status:** 🟢 Active

--- 

## 🔑 Quick Start für Hermes Agent

### So startest du:
1. **Lade nur 2‑3 relevante Blocks** (nie mehr als 5). Priorisiere:
   - `b-core-overview` – Projekt‑Überblick
   - `b-api-endpoints` – API‑Struktur
   - `b-arg-function` – Argentic‑Function‑Registry (neu)
2. **Verwende `context/blocks/`** für kontextspezifische Infos.
3. **Aktualisiere bei Änderungen** die betroffenen Blocks + `index.yaml`.

### ⚙️ Argentic Functions nutzen
- Argentic Functions sind hochoptimierte, wiederverwendbare KI‑Workflows, die von Hermes automatisch orchestriert werden.
- Sie ermöglichen:
  - **Batch‑Verarbeitung** von bis zu 10 000 Einheiten‑Updates pro Tick.
  - **Dynamic‑API‑Generation** aus OpenAPI‑Specs.
  - **Self‑Healing** via built‑in retry & fallback mechanisms.
- Jede Argentic Function wird als eigene Block‑Datei `b-<name>.yaml` definiert und kann von anderen Blocks referenziert werden.

--- 

## 📚 Dokumentations‑Struktur (neu)

```
docs/
├── AGENTS.md               ← Dieses Handbuch (Hermes‑Optimiert)
├── README.md
├── MANUAL.md
├── DEVELOPER.md
├── ARCHITECTURE.md
├── CHANGELOG.md
└── arg-functions/          ← Neue Rubrik: Argentic‑Function‑Defs
    └── b-<name>.yaml       ← Block‑Definitionen
context/
└── blocks/
    ├── index.yaml
    ├── b-core-overview.yaml
    ├── b-api-endpoints.yaml
    ├── b-crawler.yaml
    └── b-arg-function.yaml   ← Registry für alle Argentic Functions
```

--- 

## 🧩 Available Blocks (Index) – neu

| Block ID | Topic | Tokens | Last Update | Sources |
|----------|-------|--------|-------------|---------|
| `b-core-overview` | Projekt‑Übersicht, Architektur | 190 | 2026‑04‑12 | `README.md`, `ARCHITECTURE.md` |
| `b-api-endpoints` | Alle REST‑API Endpunkte | 230 | 2026‑04‑12 | `app/api/*.py` |
| `b-arg-function` | Argentic‑Function‑Registry | 250 | 2026‑04‑12 | `docs/arg-functions/*.yaml` |
| `b-crawler` | Webcrawler‑Integration | 240 | 2026‑04‑12 | `app/crawler_logic.py` |
| … | … | … | … | … |

> **Hinweis:** Lade nie mehr als **3‑5** Blocks gleichzeitig. Der Block `b-arg-function` fasst alle definierten Argentic Functions zusammen, sodass du nur **einen** zusätzlichen Block laden musst, um deren Schema zu erhalten.

--- 

## 🗂️ Code‑Structure (unchanged) – see `app/` and `admin/` folders.

--- 

## 🔄 Agent Working Guidelines (Hermes)

### 1. BEVOR DU ARBEITEST
```yaml
# Schritt 1: Block laden (max 3‑5)
- context/blocks/b-core-overview.yaml
- context/blocks/b-api-endpoints.yaml
- context/blocks/b-arg-function.yaml   # neu: enthält alle Argentic Functions
```

### 2. WÄHREND DER ARBEIT
```python
# Argentic Function Aufruf (Pseudo‑Code)
from hermes_skills import execute_argentic, ArgenticContext

ctx = ArgenticContext(
    function_name="batch_update_units",
    input_schema={"province_id": int, "unit_type": str, "count": int},
    output_schema={"unit_id": int, "status": str}
)
result = execute_argentic(ctx)   # <-- nutzt intern Hermes‑Agent‑Orchestrator
```

- **Import‑Hierarchie** beachten – keine zyklischen Abhängigkeiten.
- **Tests** pro neue Funktion → `tests/test_argentic_<name>.py`.
- **Dokumentation**: Betroffenen Block (`b-<name>.yaml`) aktualisieren, `updated_at` setzen, `sources` anpassen.

### 3. NACH DER ARBEIT
- **Pflicht**: `CHANGELOG.md` + betroffene Blocks (`b-arg-function.yaml`) + `index.yaml` aktualisieren.
- **Commit‑Message**: `feat: add argentic function batch_update_units`.
- **Optional**: `FAIL_LOG.md` bei auftretenden Fehlern.

--- 

## ⚓ Security Rules (unchanged)

--- 

## 🚦 Projekt‑Status (erweitert)

| Feature | Status | Next Steps |
|---------|--------|------------|
| Auth System | ✅ Aktiv | – |
| Admin‑UI Modularisierung | ✅ Aktiv | – |
| Webcrawler Integration | ✅ Aktiv | Scheduled Crawls |
| Building System | ✅ Aktiv | – |
| Finance System | ✅ Aktiv | – |
| **Argentic Function Framework** | 🟡 In‑Progress | Implementierungs‑Beispiel definieren, dann in `b-arg-function.yaml` eintragen |
| API Dokumentation | 📖 geplant | OpenAPI Generator später hinzufügen |

--- 

## 📍 Beispiel: Datenstruktur einer Argentic‑Function‑Definition

Datei: `context/blocks/b-arg-function.yaml`

```yaml
# Registry for all Argentic Functions used by Hermes Agent
functions:
  batch_update_units:
    description: "Bulk‑update of military units across provinces (training, recruitment, dismissal)."
    entry_point: "hermes_skills.argentic.batch_update_units"
    input_schema:
      province_id: {type: int, description: "ID of the target province"}
      unit_type: {type: str, description: "Type of unit (e.g., soldier, cavalry)"}
      count: {type: int, description: "Number of units to process"}
    output_schema:
      unit_id: {type: int, description: "Generated unit ID"}
      status: {type: str, enum: [success, error], description: "Result status"}
      message: {type: str, description: "Human readable message"}
    token_budget: 220               # max tokens allowed for this function
    retry: 3                        # automatic retries on failure
    depends_on:
      - b-api-endpoints             # needs the API router definition
      - b-core-overview             # needs project overview for naming conventions
  generate_trade_route:
    description: "Creates a new trade‑route between two provinces."
    entry_point: "hermes_skills.argentic.generate_trade_route"
    input_schema:
      origin_id: {type: int}
      dest_id: {type: int}
      cargo: {type: str}
    output_schema:
      route_id: {type: int}
      status: {type: str}
    token_budget: 190
    retry: 2
    depends_on:
      - b-api-endpoints
```

- **`entry_point`** ist der Python‑Pfad, den Hermes intern auflöst.
- **`input_schema` / `output_schema`** definieren die erwarteten JSON‑Strukturen; sie werden automatisch in FastAPI‑Validierung umgesetzt.
- **`token_budget`** schützt vor übermäßigem Token‑Verbrauch; überschreitet ein Aufruf das Budget, wird die Funktion automatisch abgebrochen und ein Fehler zurückgemeldet.
- **`depends_on`** gibt an, welche anderen Blocks bei Änderungen neu geladen werden müssen.

--- 

## 📦 Implementierungsschritte (nach Freigabe)

1. **Block‑Datei anlegen** `context/blocks/b-arg-function.yaml` mit den obigen Beispielen.
2. **`index.yaml`** um den neuen Block ergänzen:
   ```yaml
   b-arg-function:  # neu
     description: "Argentic Function Registry"
     tokens: 250
     last_update: 2026-04-12
     sources: ["context/blocks/b-arg-function.yaml"]
   ```
3. **`updated_at`** in allen betroffenen Blocks auf das aktuelle Timestamp setzen.
4. **Skill‑Management**: optionally create a skill `argentic-functions` that documents the orchestration logic.
5. **Tests** schreiben unter `tests/test_argentic_<function_name>.py`.
6. **Implementation** des Back‑Ends in `app/argentic_logic.py` (oder ein neuer Modul‑Ordner) – enthält die eigentlichen Python‑Funktionen, die von `entry_point` referenziert werden.
7. **Deploy**: Nach erfolgreichem Merge wird die Struktur auch im Keramiksignatur‑Projekt unter `docs/arg-functions/` kopiert und dort entsprechende Block‑Dateien angelegt.

--- 

**Bitte prüfe das angepasste `AGENTS.md` (und das Beispiel‑YAML).**  
*Wenn alles passt, geben wir die Freigabe, und ich setze die Umsetzung in diesem Wasteland‑Repository sowie im Keramiksignatur‑Projekt um.*
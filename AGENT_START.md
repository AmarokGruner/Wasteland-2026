# 🎮 Wasteland - Verbrannte Zone

**Ein postapokalyptisches Browser-Strategiespiel mit FastAPI Backend und SQLite Datenbank.**

---

## 🚀 Schnellstart für KI-Agenten

Dieses Projekt kann von einem KI-Agenten komplett neu aufgesetzt und entwickelt werden. Alle notwendigen Informationen sind in diesem Repository enthalten.

### 1. Projektübersicht

| Komponente | Technologie | Beschreibung |
|------------|-------------|--------------|
| **Backend** | FastAPI (Python 3.13) | REST API mit SQLite |
| **Frontend** | Vanilla JS + HTML/CSS | Kein Framework |
| **Datenbank** | SQLite | Relationale Datenbank mit SQLAlchemy ORM |
| **Authentifizierung** | JWT Tokens | Session-basiert |
| **Deployment** | Docker / Systemd | Uvicorn ASGI Server |

### 2. Verzeichnisstruktur

```
Wasteland_neu/
├── app/                    # FastAPI Backend
│   ├── main.py            # Hauptanwendung, Router-Mounting
│   ├── config.py          # Konfiguration (PORT, HOST, SECRET_KEY)
│   ├── database.py        # SQLAlchemy Engine & Session
│   └── models.py          # Alle Datenbankmodelle (30+ Tabellen)
├── seeds/                 # Datenbank-Initialisierung
│   ├── db_config.py       # Verbindung zur Datenbank
│   ├── seed_gebaeude.py   # 209 Gebäude-Typen
│   ├── seed_ressourcen.py # 153 Ressourcen
│   └── seed_terrains.py   # 42 Terrain-Typen
├── js/                    # Frontend JavaScript (21 Module)
│   ├── app.js             # Hauptanwendung
│   ├── province.js        # Provinz-Management
│   ├── buildings-data.js  # Gebäudedaten
│   └── ...               # Weitere Module
├── admin/                 # Admin UI HTML
│   └── resources.html     # Ressourcen-Verwaltung
├── admin.html             # Haupt-Admin-Oberfläche
├── index.html             # Spieler-Oberfläche
| `docs/`                  # Vollständige Dokumentation (32 Dateien)
│   ├── 00_meta_prompt_engineer.md    # KI-Agent Konfiguration und System-Prompts
│   ├── 00_session_start.md           # Session-Start Checkliste
│   ├── 01_PROJEKTUEBERSICHT.md       # Projektbeschreibung, Tech-Stack
│   ├── 02_DATENBANK.md               # Datenbank-Schema, Migrationen
│   ├── 03_API.md                     # Alle API Endpunkte
│   ├── 04_GAMEMECHANIK.md            # Alle Spielmechaniken
│   ├── 05_ADMIN_SYSTEM.md            # Admin-Funktionen
│   ├── 06_SICHERHEIT.md              # Sicherheit & Audit
│   ├── 07_DEPLOYMENT.md              # Setup, Docker, nginx
│   ├── 08_ENTWICKLUNG.md             # Testing, Linting, CI/CD
│   ├── 09_DATENBANK_ABGLEICH.md      # Datenbank-Abgleich Original vs. models.py
│   ├── 10_ci_cd_pipeline.md          # GitHub Actions CI/CD Pipeline
│   ├── 11_monitoring_logging.md      # Monitoring, Logging & Error Tracking
│   ├── 12_backup_strategy.md         # Backup Strategy & Disaster Recovery
│   ├── sub_agent_devops_engineer.md  # DevOps Engineer Sub-Agent Definition
├── SESSION_LOG.md           # Entwicklungs-Log (wird vom Agenten befüllt)
├── .gitignore             # Ignorierte Dateien
└── requirements.txt       # Python Abhängigkeiten
```

### 3. Session Log (SESSION_LOG.md) - WICHTIG!

**DIESSES FILE MUSS VOR JEDER SESSION GELESEN UND NACH JEDER SESSION AKTUALISIERT WERDEN!**

```
SESSION_LOG.md:
├── Letzte Session (Datum, Agent, Status)
├── Erledigte Aufgaben (Checkliste)
├── Offene Aufgaben (Was fehlt?)
├── Bekannte Probleme (Fehler + Lösungen)
└── Nächste Schritte (Plan für nächste Session)
```

**Zweck:** Konsistenz zwischen verschiedenen Sessions und Agenten wahren.  
**Ohne Session Log keine konsistente Entwicklung über mehrere KI-Sessions hinweg!**

### 3. Datenbank-Schema (Kern-Tabellen)

| Tabelle | Beschreibung | Wichtige Felder |
|---------|--------------|-----------------|
| `gebaeude_typen` | 209 Gebäude-Typen | id, name, kategorie, tech_level, baukosten_mips |
| `ressourcen` | 153 Ressourcen | id, name, typ, wert |
| `vorkommen` | 24 Vorkommensarten | id, name, typ, tech, suchkosten |
| `terrain_typen` | 42 Terrain-Typen | id, name, farbe, effektivitaet |
| `provinzen` | Spieler-Provinzen | id, name, besitzer_id, mips, bevölkerung |
| `provinz_gebaeude` | Gebäude in Provinzen | provinz_id, gebaeude_typ_id, x, y, level |
| `einheiten_typen` | 63 Einheitentypen | id, name, kosten, staerke |
| `lebewesen` | 8 Tierarten | id, name, typ, aggressivitaet |
| `artikel` | 15 Artikel | id, name, typ, wert |
| `regierungsformen` | 7 Regierungsformen | id, name, bonusse |

### 4. API Endpunkte (Hauptkategorien)

```
Auth:
  POST /auth/register
  POST /auth/login
  GET  /auth/me

Provinz:
  GET    /province/
  POST   /province/
  GET    /province/{id}
  PUT    /province/{id}
  POST   /province/{id}/build           # Gebäude bauen
  POST   /province/{id}/demolish        # Gebäude abreißen
  GET    /province/{id}/buildings       # Alle Gebäude

Admin:
  GET    /admin/dashboard
  POST   /admin/gebaeude_typen          # Gebäude verwalten
  POST   /admin/ressourcen              # Ressourcen verwalten
  GET    /admin/provinzen              # Provinzen verwalten

Welt:
  GET    /world/map                    # Weltkarte
  GET    /world/terrains               # Terrains
```

### 5. Wichtige Spielmechaniken

#### Gebäude-System
- **209 verschiedene Gebäude** mit unterschiedlichen Funktionen
- Kategorien: Farm, Industrie, Bildung, Militär, Spezial
- Tech-Level erforderlich für Bau
- MIPS-Kosten + Rohstoffbedarf
- Ausbaubar (bis zu 10 Stufen) bei einigen Gebäuden
- Einmalige Gebäude (pro Provinz nur einmal)

#### Ressourcen-Management
- **153 verschiedene Ressourcen**
- Typen: Nahrung, Getränk, Baurohstoff, Luxus, etc.
- Produktion durch Gebäude
- Lagerkapazität begrenzt
- Handel zwischen Provinzen

#### Terrains & Weltkarte
- **42 Terrain-Typen** mit verschiedenen Effektivitäten
- 50x50 Weltkarte (2500 Zellen)
- Gebäude haben Terrain-Boni
- Vorkommen auf bestimmten Terrains

#### Runden-System (Ticks)
- Server Tick alle 60 Sekunden
- Berechnet: Produktion, Verbrauch, Wachstum
- Gamelog für Events
- Automatische Cleanup-Routinen

### 6. Sicherheitsvorgaben

#### Authentifizierung
- JWT Tokens mit 24h Ablauf
- Password Hashing mit bcrypt
- Rate Limiting für Login-Versuche

#### Autorisierung
- Admin-Rollen für Verwaltungsfunktionen
- Provinz-Besitzprüfung bei Aktionen
- API Token Validierung

#### Datenvalidierung
- Pydantic Models für alle Requests
- SQL-Injection Schutz durch SQLAlchemy ORM
- Input Sanitization

### 7. Entwicklungsumgebung aufsetzen

```bash
# 1. Python Virtual Environment
python3 -m venv venv
source venv/bin/activate

# 2. Abhängigkeiten installieren
pip install -r requirements.txt

# 3. Datenbank initialisieren
python seeds/seed_main.py

# 4. Server starten
uvicorn app.main:app --host 0.0.0.0 --port 8011 --reload
```

### 8. Wichtige Dateien für KI-Agenten

**Zum Starten des Projekts lesen:**
1. `docs/00_meta_prompt_engineer.md` - KI-Agent Konfiguration und System-Prompts
2. `docs/00_session_start.md` - Session-Start Checkliste
3. `AGENT_START.md` - Komplette Projektübersicht und Multi-Agenten System

**Für Feature-Entwicklung (alle 28 docs/ Dateien):**
- `docs/01_feature_einheiten.md` - Militärsystem (Einheiten & Kampf)
- `docs/03_feature_ruinen.md` - Ruinen-Mechanik
- `docs/05_feature_wege_arbeit.md` - Wege, Arbeitspunkte & Straßennetz
- `docs/07_feature_demolish.md` - Abriss-Funktion (Demolish)
- `docs/08_feature_markt_handel.md` - Marktplatz & Spieler-Handel
- `docs/09_feature_kultur_bildung.md` - Kulturpunkte, Bildung & Staatsform
- `docs/12_feature_vorkommen.md` - Bodenschätze & Vorkommen
- `docs/13_feature_regierungsformen.md` - Regierungsformen System
- `docs/18_feature_bunker.md` - Bunker-Mechanik & Startprovinz
- `docs/20_feature_kampf.md` - Belagerung & Kampfsystem
- `docs/21_feature_siedler.md` - Siedler & Kolonisierung
- `docs/24_feature_weltgenerierung.md` - Weltgenerierung & Admin-Tools
- `docs/28_ui_ueberarbeitung.md` - Spieler-UI Überarbeitung (Navigation, Menü)
- `docs/29_feature_auth_system.md` - Authentifizierung & Login-System
- `docs/30_feature_server_tick.md` - Server-Tick Engine (Cronjob)

**Für Datenbank-Änderungen:**
- `docs/02_DATENBANK.md` - Datenbank-Schema und Migrationen
- `docs/09_DATENBANK_ABGLEICH.md` - Abgleich Original vs. models.py
- `docs/27_weltkarte_db_migration.md` - Weltkarte DB-Migration
- `docs/MIGRATION_2026-09.md` - Datenbank-Migration September 2026
- `app/models.py` - Alle SQLAlchemy Modelle

**Für Infrastruktur & DevOps:**
- `docs/10_ci_cd_pipeline.md` - GitHub Actions CI/CD Pipeline
- `docs/11_monitoring_logging.md` - Monitoring, Logging & Error Tracking
- `docs/12_backup_strategy.md` - Backup Strategy & Disaster Recovery
- `docs/sub_agent_devops_engineer.md` - DevOps Engineer Sub-Agent

**Für Admin-System:**
- `docs/05_ADMIN_SYSTEM.md` - Admin-Funktionen Übersicht
- `docs/26_admin_overhaul.md` - Admin-Oberfläche Überarbeitung
- `docs/gebaeude_admin_grid.md` - Building System v3 (Admin Grid)

### 10. Testing

```bash
# Unit Tests
pytest tests/

# Integration Tests
pytest tests/integration/

# Linting
flake8 app/
mypy app/
```

### 11. Multi-Agenten Architektur - Projektleiter & Sub-Agenten

#### 🎯 Rolle des Haupt-Agenten (Projektleiter/Manager)

Der Haupt-KI-Agent übernimmt die Rolle des **Projektmanagers** und koordiniert alle Entwicklungsaktivitäten:

- **Aufgabenzerlegung:** Komplexe Aufgaben werden in kleinere, spezialisierte Arbeitspakete zerlegt
- **Sub-Agenten Zuweisung:** Jedes Arbeitspaket wird an einen spezialisierten Sub-Agenten übergeben
- **Ergebnis-Konsolidierung:** Ergebnisse mehrerer Sub-Agenten werden analysiert, verglichen und konsolidiert
- **Qualitätssicherung:** Alle Ergebnisse werden auf Konsistenz, Vollständigkeit und Korrektheit geprüft
- **Umsetzungs-Entscheidungen:** Basierend auf den Sub-Agenten-Ergebnissen wird die beste Lösung ausgewählt und umgesetzt

#### 🤖 Sub-Agenten System

Das Projekt verwendet ein **Multi-Agenten-System** mit spezialisierten Sub-Agenten. Jeder Sub-Agent hat eine klare Spezialisierung und wird über `delegate_task` mit isoliertem Kontext gestartet.

##### 📋 Liste der Sub-Agenten

**1. planning-analyst (Planungs-Analyst)**
- **Spezialisierung:** Technische Analyse und Machbarkeitsprüfung
- **Aufgaben:**
  - Analyse bestehender Codebasis für Feature-Integration
  - Identifikation von Abhängigkeiten und Konflikten
  - Technische Machbarkeitsbewertung
  - Risikobewertung und Alternative Vorschläge
- **Einsatz:** Vor jeder Feature-Entwicklung

**2. planning-architect (Planungs-Architekt)**
- **Spezialisierung:** Systemdesign und Architektur
- **Aufgaben:**
  - Entwirft Datenbank-Schema Änderungen
  - Plant API-Endpunkt Integrationen
  - Definiert Model-Relationships und Back-Populates
  - Erstellt Migrationspläne für bestehende Tabellen
- **Einsatz:** Bei Datenbank- oder API-Änderungen

**3. planning-developer (Planungs-Entwickler)**
- **Spezialisierung:** Implementierungsplanung und Code-Struktur
- **Aufgaben:**
  - Erstellt detaillierte Implementierungs-Schritte
  - Plant File-Struktur und Module-Organisation
  - Definiert Test-Szenarien und Edge-Cases
  - Erstellt Code-Beispiele für kritische Funktionen
- **Einsatz:** Vor jeder Feature-Implementierung

**4. backend-developer (Backend-Entwickler)**
- **Spezialisierung:** FastAPI Backend Entwicklung
- **Aufgaben:**
  - Implementiert API-Endpunkte (Router, Services, Schemas)
  - Erstellt Datenbank-Migrationen und Seeds
  - Implementiert Business Logic und Validierung
  - Schreibt Unit-Tests für Backend-Funktionen
- **Einsatz:** Bei allen Backend-Features

**5. frontend-developer (Frontend-Entwickler)**
- **Spezialisierung:** Vanilla JS Frontend Entwicklung
- **Aufgaben:**
  - Implementiert UI-Komponenten (HTML/CSS/JS)
  - Erstellt API-Integrationen im Frontend
  - Plant State-Management und Event-Handling
  - Implementiert Responsive Design und UX-Verbesserungen
- **Einsatz:** Bei allen UI/Feature-Entwicklungen

**6. game-mechanic (Spielmechanik-Experte)**
- **Spezialisierung:** Spielbalance und Game Design
- **Aufgaben:**
  - Berechnet MIPS-Kosten und Ressourcen-Balance
  - Definiert Tech-Level Anforderungen
  - Plant Gebäude-Interaktionen und Synergien
  - Erstellt Balance-Tabellen für neue Features
- **Einsatz:** Bei neuen Spielmechaniken oder Balance-Anpassungen

**7. security-auditor (Sicherheits-Audit)**
- **Spezialisierung:** Sicherheit und Datenschutz
- **Aufgaben:**
  - Prüft API-Endpunkte auf Sicherheitslücken
  - Validiert Input-Sanitization und SQL-Injection Schutz
  - Prüft Authentifizierung und Autorisierung
  - Erstellt Security-Checklisten für neue Features
- **Einsatz:** Vor jedem Deployment oder bei sicherheitskritischen Features

**8. documentation-writer (Dokumentations-Schreiber)**
- **Spezialisierung:** Technische Dokumentation
- **Aufgaben:**
  - Erstellt Feature-Dokumentation im Markdown-Format
  - Aktualisiert API-Dokumentation (OpenAPI/Swagger)
  - Schreibt Changelog und Release Notes
  - Erstellt Benutzerhandbücher für neue Features
- **Einsatz:** Nach jeder Feature-Implementierung

**9. testing-engineer (Test-Ingenieur)**
- **Spezialisierung:** Testautomatisierung und Qualitätssicherung
- **Aufgaben:**
  - Erstellt Unit-Tests für Backend-Funktionen
  - Schreibt Integrationstests für API-Endpunkte
  - Plant Edge-Cases und Fehler-Szenarien
  - Führt Regressionstests nach Änderungen durch
- **Einsatz:** Vor und nach jeder Feature-Implementierung

**10. database-admin (Datenbank-Administrator)**
- **Spezialisierung:** Datenbank-Design und Performance
- **Aufgaben:**
  - Erstellt und optimiert Datenbank-Schemata
  - Plant Index-Strategien für Performance
  - Erstellt Migrationsskripte und Seed-Daten
  - Prüft Daten-Integrität und Constraints
- **Einsatz:** Bei allen Datenbank-Änderungen

**11. devops-engineer (DevOps Engineer)**
- **Spezialisierung:** CI/CD, Docker, Server Administration, Monitoring
- **Aufgaben:**
  - GitHub Actions Workflows erstellen und pflegen (.github/workflows/)
  - Dockerfile und docker-compose.yml optimieren
  - Server Deployment automatisieren (SSH, Systemd)
  - Monitoring Infrastructure aufsetzen (Prometheus, Grafana, Sentry)
  - Backup Strategy implementieren und überwachen
- **Einsatz:** Bei Deployment, Server Setup, Monitoring Konfiguration

**12. qa-manager (Quality Assurance Manager)**
- **Spezialisierung:** Test-Strategie und Qualitätssicherung
- **Aufgaben:**
  - Test-Abdeckungsstrategie entwickeln (Unit, Integration, E2E)
  - Quality Gates definieren (Code Coverage, Linting Standards)
  - Accessibility und UX Testing durchführen
  - Regression Testing nach größeren Änderungen
- **Einsatz:** Vor Releases, bei großen Feature-Änderungen

**13. ui-ux-designer (UI/UX Designer)**
- **Spezialisierung:** Frontend Design und User Experience
- **Aufgaben:**
  - UI/UX Guidelines definieren (Farben, Typografie, Layout)
  - Responsive Design und Mobile-First Ansatz
  - Accessibility (WCAG 2.1) sicherstellen
  - User Flow und Navigation optimieren
- **Einsatz:** Bei UI-Überarbeitungen, neuen Features mit Frontend

**14. api-integration-specialist (API Integration Specialist)**
- **Spezialisierung:** Third-party API Integration und Webhooks
- **Aufgaben:**
  - OAuth2 / OpenID Connect Integrationen
  - Webhook Handler implementieren
  - API Rate Limiting und Retry Logic
  - External Service Error Handling
- **Einsatz:** Bei Integration externer Dienste (Payment, Email, SMS)

**15. data-analyst (Data Analyst)**
- **Spezialisierung:** Datenanalyse und Reporting
- **Aufgaben:**
  - Spielstatistiken auswerten (Nutzung, Balance)
  - Admin Reporting Dashboards erstellen
  - Player Behavior Analytics
  - Performance Monitoring und Optimierungsvorschläge
- **Einsatz:** Bei Balance-Anpassungen, Admin Reporting Features


**16. browser-frontend-developer (Browser Frontend Developer)**
- **Spezialisierung:** Vanilla JavaScript, HTML5, CSS3, Browser Features
- **Aufgaben:**
  - Vanilla JS Module entwickeln (app.js, province.js, buildings-data.js)
  - DOM Manipulation und Event Handling implementieren
  - Responsive Design und Cross-Browser Kompatibilität sicherstellen
  - Browser Storage (localStorage, sessionStorage) verwalten
  - Progressive Web App (PWA) Features implementieren
- **Einsatz:** Bei allen UI-Komponenten, responsive Design, PWA Features

**17. browser-testing-engineer (Browser Testing Engineer)**
- **Spezialisierung:** Browser-basierte E2E Tests, Cross-Browser Testing
- **Aufgaben:**
  - Playwright/Puppeteer E2E Tests schreiben (Chrome, Firefox, Safari)
  - Cross-Browser Kompatibilität testen
  - Responsive Design Testing (Mobile, Tablet, Desktop)
  - Lighthouse Audits und Core Web Vitals messen
  - Accessibility Testing (WCAG 2.1 AA) durchführen
- **Einsatz:** Vor Releases, bei UI-Änderungen, Performance-Optimierung


**18. ai-player-bot (Adaptive AI Player Bot)**
- **Spezialisierung:** Adaptive Spieler-Simulation, Reinforcement Learning, Langzeit-Testing
- **Aufgaben:**
  - Simuliert reale Spieler im Live-Browser (echte API-Endpunkte)
  - Adaptives Lernen basierend auf Spielerfolg (Q-Learning, ε-greedy)
  - Verschiedene Spielertypen simulieren (conservative, aggressive, trader, explorer)
  - Spielbalance über längere Zeiträume testen (Tage/Wochen komprimiert)
  - UX-Schwachstellen und Edge Cases unter realistischen Bedingungen erkennen
- **Einsatz:** Bei Balance-Anpassungen, Langzeit-Simulationen, UX-Optimierung

---

---


#### 🔄 Multi-Model Planning Workflow

Für **Planungsaufgaben** wird ein spezieller Workflow verwendet, der die Stärken verschiedener LLM-Modelle kombiniert:

##### Schritt 1: Parallel Planning (3 Sub-Agenten)
Der Projektleiter erstellt **drei parallele Planungsaufgaben** an drei verschiedene Planning-Sub-Agenten:

```
Planning-Analyst (Modell A) → Technische Analyse
Planning-Architect (Modell B) → Systemdesign  
Planning-Developer (Modell C) → Implementierungsplan
```

##### Schritt 2: Modell-Zuweisung (10.68.42.2:1234)
Jeder Planning-Sub-Agent verwendet ein **unterschiedliches LLM-Modell** vom lokalen Server:

| Sub-Agent | Empfohlenes Modell | Stärke |
|-----------|-------------------|--------|
| Planning-Analyst | qwen3.6-35b-a3b-holo3-qwopus-instruct-qx64-hi-mlx | Tiefe technische Analyse |
| Planning-Architect | qwen3.6-32b-a3b-instruct-qwopus-holo-fast-v1.5 | Schnelles Systemdesign |
| Planning-Developer | qwen3.6-235b-a22b-v05-qwen3coder-instruct-qwopus-holo-mlx | Code-Generierung |

##### Schritt 3: Ergebnis-Konsolidierung
Der Projektleiter analysiert alle drei Planungsergebnisse:

1. **Gemeinsamkeiten identifizieren:** Wo stimmen alle drei Modelle überein?
2. **Unterschiede analysieren:** Wo weichen die Modelle ab und warum?
3. **Stärken kombinieren:** Beste Aspekte jedes Plans auswählen
4. **Konflikte lösen:** Widersprüche durch technische Bewertung auflösen
5. **Konsolidierten Plan erstellen:** Optimaler Hybrid-Plan aus allen drei Ergebnissen

##### Schritt 4: Umsetzung
Der konsolidierte Plan wird an den zuständigen Sub-Agenten (backend-developer oder frontend-developer) zur Implementierung übergeben.

##### Beispiel: Feature "Neues Gebäude-System"

```
📋 Projektleiter erstellt 3 parallele Planungsaufgaben:

┌─────────────────────────────────────────────────────────────┐
│ Planning-Analyst (qwen3.6-35b)                              │
│ - Analyse: 209 Gebäude existieren, neue Tabelle nötig?      │
│ - Risiko: Konflikte mit bestehenden Seeds                   │
│ - Empfehlung: Erweiterung der gebaeude_typen Tabelle        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Planning-Architect (qwen3.6-32b)                            │
│ - Design: Neue Spalten in gebaeude_typen                    │
│ - Migration: ALTER TABLE + Seed-Daten                       │
│ - API: POST /admin/gebaeude_typen erweitern                │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Planning-Developer (qwen3.6-235b)                           │
│ - Implementierung: models.py patchen, seed_gebaeude.py      │
│ - Tests: pytest für neue Spalten                            │
│ - Code-Beispiel: BuildingType Model erweitern              │
└─────────────────────────────────────────────────────────────┘

📊 Konsolidierung durch Projektleiter:
✅ Alle stimmen: Erweiterung der gebaeude_typen Tabelle
✅ Architektur: ALTER TABLE + Seed-Daten
✅ Implementierung: models.py patchen, Tests schreiben

🎯 Konsolidierter Plan:
1. BuildingType Model in models.py erweitern (alle neuen Spalten)
2. Datenbank-Migration über init_tables() (SQLAlchemy-basiert)
3. Seed-Daten in seed_gebaeude.py hinzufügen
4. API-Endpunkt POST /admin/gebaeude_typen erweitern
5. Unit-Tests für neue Spalten schreiben
6. Dokumentation aktualisieren (docs/04_GAMEMECHANIK.md)
```

#### 📝 Sub-Agenten Konfiguration

Jeder Sub-Agent wird über `delegate_task` mit folgenden Parametern gestartet:

```python
# Beispiel: Planning-Analyst Task
delegate_task(
    tasks=[{
        "goal": "Analysiere die technische Machbarkeit von Feature X",
        "context": "Bestehende Codebasis, Modelle, API-Endpunkte...",
        "output_schema": {
            "type": "object",
            "properties": {
                "feasibility": {"type": "string"},  # high/medium/low
                "risks": {"type": "array", "items": {"type": "string"}},
                "recommendations": {"type": "array", "items": {"type": "string"}}
            }
        }
    }]
)
```

#### ⚠️ Wichtige Regeln für den Projektleiter

1. **IMMER Planning-Phase:** Keine Feature-Implementierung ohne vorherige parallele Planung (3 Modelle)
2. **Dokumentation pflegen:** SESSION_LOG.md nach jeder Sub-Agenten-Execution aktualisieren
3. **Qualitätssicherung:** Alle Ergebnisse auf Konsistenz prüfen bevor Umsetzung
4. **Ressourcen schonen:** Nicht alle Tasks benötigen 3 parallele Planning-Agenten (einfache Fixes können direkt umgesetzt werden)
5. **Modell-Auswahl:** Passendes Modell für jede Aufgabe wählen (siehe Tabelle oben)
6. **Ergebnis-Konsolidierung:** Mindestens 2 von 3 Planning-Agenten müssen zustimmen bevor Umsetzung

#### 🌿 Branch-Strategie für Sub-Agenten

Jeder Sub-Agent arbeitet **eigenständig in einem eigenen Git-Branch** für sein Arbeitspaket:

##### Branch-Erstellung
```bash
# Projektleiter erstellt Branch für Sub-Agent
git checkout -b feature/<feature-name>
# oder
git checkout -b fix/<bug-description>
# oder
git checkout -b refactor/<module-name>

# Beispiel:
git checkout -b feature/neues-gebaeude-system
git checkout -b fix/auth-token-expiry
git checkout -b refactor/database-migrations
```

##### Sub-Agent Arbeit im Branch
- Sub-Agent arbeitet **ausschließlich** in seinem zugewiesenen Branch
- Alle Code-Änderungen, Tests und Dokumentationen erfolgen im eigenen Branch
- Regelmäßige Commits mit aussagekräftigen Messages:
  ```bash
  git add .
  git commit -m "feat: BuildingType Model erweitert um neue Spalten"
  git push origin feature/neues-gebaeude-system
  ```

##### Testing im Branch
- Sub-Agent führt **alle Tests** im eigenen Branch durch:
  ```bash
  # Unit Tests
  pytest tests/ -v
  
  # Integration Tests (wenn applicable)
  pytest tests/integration/ -v
  
  # Linting
  flake8 app/
  mypy app/
  ```

##### Merge nach erfolgreicher Testung
- **Voraussetzung:** Alle Tests bestanden, Dokumentation aktualisiert
- Sub-Agent erstellt **Pull Request** zum master Branch:
  ```bash
  # GitHub CLI (gh) verwenden
  gh pr create \
    --base master \
    --head feature/neues-gebaeude-system \
    --title "feat: Neues Gebäude-System implementiert" \
    --body "Implementierung basierend auf konsolidiertem Planning-Plan
  
  ## Änderungen
  - BuildingType Model erweitert (17 Spalten)
  - Seed-Daten hinzugefügt (122 Gebäude)
  - API-Endpunkt POST /admin/gebaeue_typen erweitert
  
  ## Tests
  - ✅ Alle Unit Tests bestanden
  - ✅ Integrationstests erfolgreich
  - ✅ Linting ohne Fehler
  
  ## Planning-Agenten Ergebnisse
  - Planning-Analyst: Machbarkeit bestätigt (high)
  - Planning-Architect: ALTER TABLE + Seed-Daten empfohlen
  - Planning-Developer: models.py patchen, Tests schreiben"
  ```

##### Projektleiter Review & Merge
- Projektleiter prüft Pull Request auf:
  - Konsistenz mit konsolidiertem Plan
  - Vollständigkeit der Implementierung
  - Testabdeckung
  - Dokumentationsaktualisierung
- Bei Bestätigung: **Merge in master**
  ```bash
  gh pr merge <pr-number> --merge --delete-branch
  ```

##### Branch-Bereinigung
- Nach erfolgreichem Merge: Feature-Branch löschen (automatisch durch gh pr merge)
- Master Branch bleibt stabil und testbar

##### Beispiel Workflow: Neues Gebäude-Feature

```bash
# 1. Projektleiter erstellt Planning (3 parallele Agenten)
# ... Planning-Ergebnisse werden konsolidiert ...

# 2. Projektleiter erstellt Branch für backend-developer
git checkout -b feature/neues-gebaeude-system

# 3. backend-developer arbeitet im Branch
git checkout feature/neues-gebaeude-system

# 4. Implementierung
# - models.py patchen (BuildingType erweitern)
# - seed_gebaeude.py aktualisieren
# - API-Endpunkt erweitern

# 5. Testing im Branch
pytest tests/ -v
flake8 app/

# 6. Commit & Push
git add .
git commit -m "feat: BuildingType Model um 13 neue Spalten erweitert

- platz_land, platz_wasser, platz_luft
- verbrauch, produktionswert
- beschreibung, created_at, updated_at
- verbraucht_von, produziert_von
- verbrauch_hinweis, fleisch_bei_schlachtung"
git push origin feature/neues-gebaeude-system

# 7. Pull Request erstellen
gh pr create \
  --base master \
  --head feature/neues-gebaeude-system \
  --title "feat: BuildingType Model erweitert (17 Spalten)" \
  --body "Implementierung basierend auf konsolidiertem Planning-Plan"

# 8. Projektleiter prüft PR und merged
gh pr merge <pr-number> --merge --delete-branch

# 9. Zurück zu master für nächstes Feature
git checkout master
```

##### Branch-Namenskonventionen

| Typ | Pattern | Beispiel |
|-----|---------|----------|
| Feature | `feature/<name>` | `feature/handelsrouten-system` |
| Bugfix | `fix/<description>` | `fix/auth-token-expiry` |
| Refactor | `refactor/<module>` | `refactor/database-migrations` |
| Docs | `docs/<topic>` | `docs/api-documentation-update` |
| Test | `test/<scenario>` | `test/integration-api-endpoints` |

##### Ausnahmen (direkte Umsetzung ohne Branch)
- **Kleine Documentation Updates** (Typos, Formatierung)
- **Triviale Config Changes** (Port-Anpassungen, Environment Variables)
- **SESSION_LOG.md Updates** (nach jeder Sub-Agenten-Execution)

Diese können direkt auf master committet werden, ohne eigenen Branch zu erstellen.

---

### 13. Deployment

#### Docker
```bash
docker build -t wasteland .
docker run -p 8011:8011 wasteland
```

#### Systemd Service
```bash
sudo cp wasteland.service /etc/systemd/system/
sudo systemctl enable wasteland
sudo systemctl start wasteland
```

#### nginx Reverse Proxy (Port 443)
```nginx
server {
    listen 443 ssl;
    server_name wasteland.local;
    
    location / {
        proxy_pass http://127.0.0.1:8011;
    }
}
```

---

## 📚 Vollständige Dokumentation

Alle 26 Dokumentationsdateien im `docs/` Verzeichnis beschreiben:
- ✅ Datenbank-Schema und Migrationen
- ✅ API Schnittstellen (REST)
- ✅ Spielmechaniken (37 Features)
- ✅ Sicherheitskonzepte
- ✅ Admin-Oberfläche
- ✅ UI/UX Design
- ✅ Fehlerbehebung und Audit

---

## 🎯 Nächste Schritte für KI-Agenten

1. **Lies** `docs/00_meta_prompt_engineer.md` für Agenten-Konfiguration
2. **Folge** `docs/00_session_start.md` für Session-Setup
3. **Setze auf** mit `docs/COMPLETE_CLEAN_BUILD_GUIDE.md`
4. **Entwickle** Feature für Feature basierend auf `docs/XX_feature_*.md`

---

**Projektstatus:** v1.6 - Voll funktionsfähig  
**Letztes Update:** 2026-10-13  
**GitHub:** https://github.com/AmarokGruner/Wasteland-2026

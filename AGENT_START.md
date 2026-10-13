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
├── docs/                  # Vollständige Dokumentation (8 Dateien)
│   ├── 01_PROJEKTUEBERSICHT.md    # Projektbeschreibung, Tech-Stack
│   ├── 02_DATENBANK.md            # Datenbank-Schema, Migrationen
│   ├── 03_API.md                  # Alle API Endpunkte
│   ├── 04_GAMEMECHANIK.md         # Alle Spielmechaniken
│   ├── 05_ADMIN_SYSTEM.md         # Admin-Funktionen
│   ├── 06_SICHERHEIT.md           # Sicherheit & Audit
│   ├── 07_DEPLOYMENT.md           # Setup, Docker, nginx
│   └── 08_ENTWICKLUNG.md          # Testing, Linting, CI/CD
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
1. `docs/00_meta_prompt_engineer.md` - KI-Agent Konfiguration
2. `docs/00_session_start.md` - Session-Start Checkliste
3. `docs/COMPLETE_CLEAN_BUILD_GUIDE.md` - Kompletter Aufbau-Guide
4. `docs/SETUP_AND_CLEAN_BUILD.md` - Schnelleinrichtung

**Für Feature-Entwicklung:**
- `docs/01_feature_einheiten.md` - Militärsystem
- `docs/03_feature_ruinen.md` - Ruinen-Mechanik
- `docs/08_feature_markt_handel.md` - Handelssystem
- `docs/24_feature_weltgenerierung.md` - Weltkarte
- `docs/29_feature_auth_system.md` - Authentifizierung

**Für Datenbank-Änderungen:**
- `docs/27_weltkarte_db_migration.md` - Migrationen
- `app/models.py` - Alle Modelle

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

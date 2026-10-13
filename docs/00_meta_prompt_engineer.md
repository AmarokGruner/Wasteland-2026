# 🤖 KI-Agent Meta-Prompt Konfiguration

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 🎯 Agenten-Rollen und Konfiguration

### Haupt-Agent: Projektleiter/Manager

**Rolle:** Koordiniert alle Entwicklungsaktivitäten, zerlegt Aufgaben, konsolidiert Ergebnisse.

**System-Prompt:**
```
Du bist der Projektleiter für das Wasteland Browser Game (Verbrannte Zone v1.6).
Deine Aufgabe ist es, komplexe Entwicklungsaufgaben zu analysieren, in spezialisierte
Arbeitspakete zu zerlegen und diese an Sub-Agenten zu delegieren.

WICHTIGE REGELN:
1. IMMER Planning-Phase durchführen (3 parallele Planning-Agenten mit verschiedenen LLMs)
2. Ergebnisse der 3 Planning-Agenten konsolidieren (Gemeinsamkeiten + Unterschiede)
3. Nur Umsetzung wenn mindestens 2 von 3 Planning-Agenten zustimmen
4. SESSION_LOG.md nach jeder Sub-Agenten-Execution aktualisieren
5. Alle Ergebnisse auf Konsistenz, Vollständigkeit und Korrektheit prüfen

VERFÜGBARE SUB-AGENTEN:
- planning-analyst, planning-architect, planning-developer (Planning-Phase)
- backend-developer, frontend-developer (Implementierung)
- game-mechanic, security-auditor, documentation-writer, testing-engineer, database-admin (Spezialaufgaben)

ARBEITSWEISE:
- delegate_task verwenden für Sub-Agenten (isolierte Kontexte)
- Git Branches für jedes Arbeitspaket (feature/<name>, fix/<desc>)
- Pull Requests über gh CLI erstellen und mergen
```

### Sub-Agent Konfiguration

Jeder Sub-Agent erhält einen spezifischen System-Prompt basierend auf seiner Spezialisierung.

**Beispiel: backend-developer**
```
Du bist der Backend-Entwickler für Wasteland. Spezialisiert auf FastAPI, SQLAlchemy und SQLite.

AUFGABEN:
- API-Endpunkte implementieren (Router, Services, Schemas)
- Datenbank-Migrationen und Seeds erstellen
- Business Logic und Validierung implementieren
- Unit-Tests für Backend-Funktionen schreiben

RICHTLINIEN:
- Immer models.py als Single Source of Truth verwenden
- Pydantic Schemas für alle Requests/Responses
- SQLAlchemy ORM für Datenbankzugriff (keine RAW SQL)
- JWT Authentication für geschützte Endpunkte
- Error Handling mit HTTPException und custom error handlers

CODE-STIL:
- PEP 8 Konventionen
- Type Hints für alle Funktionen
- Docstrings nach Google Style
- Modularer Aufbau (Router, Service, Schema Trennung)
```

---

## 🔄 Multi-Model Planning Workflow

### Schritt 1: Parallel Planning (3 Sub-Agenten)

Der Projektleiter erstellt drei parallele Planungsaufgaben:

| Agent | LLM Modell (10.68.42.2:1234) | Fokus |
|-------|-------------------------------|-------|
| planning-analyst | qwen3.6-35b-a3b-holo3-qwopus-instruct-qx64-hi-mlx | Technische Analyse, Machbarkeit, Risiken |
| planning-architect | qwen3.6-32b-a3b-instruct-qwopus-holo-fast-v1.5 | Systemdesign, Architektur, Migrationen |
| planning-developer | qwen3.6-235b-a22b-v05-qwen3coder-instruct-qwopus-holo-mlx | Implementierungsplan, Code-Beispiele |

### Schritt 2: Ergebnis-Konsolidierung

Der Projektleiter analysiert alle drei Ergebnisse:
1. **Gemeinsamkeiten** identifizieren (wo stimmen alle zu?)
2. **Unterschiede** analysieren (warum weichen sie ab?)
3. **Stärken kombinieren** (beste Aspekte jedes Plans)
4. **Konflikte lösen** (durch technische Bewertung)
5. **Konsolidierten Plan** erstellen (Hybrid-Plan)

### Schritt 3: Umsetzung

Der konsolidierte Plan wird an den zuständigen Sub-Agenten übergeben.

---

## 📋 Agenten-Output Schema

### Planning-Analyst Output
```json
{
  "feasibility": "high|medium|low",
  "risks": ["Risiko 1", "Risiko 2"],
  "dependencies": ["Abhängigkeit 1"],
  "recommendations": ["Empfehlung 1"]
}
```

### Planning-Architect Output
```json
{
  "database_changes": ["ALTER TABLE...", "CREATE INDEX..."],
  "api_endpoints": [{"method": "POST", "path": "/api/..."}],
  "models_affected": ["Model1", "Model2"],
  "migration_steps": ["Schritt 1", "Schritt 2"]
}
```

### Planning-Developer Output
```json
{
  "implementation_steps": ["Schritt 1", "Schritt 2"],
  "files_to_modify": ["app/models.py", "seeds/seed_gebaeude.py"],
  "test_scenarios": ["Szenario 1", "Szenario 2"],
  "code_examples": [{"file": "models.py", "snippet": "..."}]
}
```

---

## ⚠️ Fehlerbehandlung für Agenten

### Häufige Fehler und Lösungen:

1. **Import-Fehler**
   - Problem: `ModuleNotFoundError`
   - Lösung: Virtual Environment aktivieren (`source venv/bin/activate`)

2. **Datenbank-Schema Inkonsistenz**
   - Problem: Model hat Spalten die DB nicht hat (oder umgekehrt)
   - Lösung: `docs/09_DATENBANK_ABGLEICH.md` konsultieren, models.py patchen

3. **Port bereits belegt**
   - Problem: `Address already in use`
   - Lösung: `lsof -i :8011` prüfen, Prozess beenden

4. **Seed-Prozess bricht ab**
   - Problem: Fehlende Spalten in DB
   - Lösung: `init_tables()` über SQLAlchemy aufrufen (nicht RAW SQL)

---

## 📚 Referenz-Dokumentation

**Essenzielle Dateien (IMMER lesen):**
- `AGENT_START.md` - Projektübersicht und Multi-Agenten System
- `SESSION_LOG.md` - Aktueller Entwicklungsstatus
- `docs/01_PROJEKTUEBERSICHT.md` - Projektbeschreibung
- `docs/02_DATENBANK.md` - Datenbank-Schema
- `docs/03_API.md` - API Endpunkte

**Feature-Dokumentation (bei Bedarf):**
- `docs/01_feature_einheiten.md` - Militärsystem
- `docs/03_feature_ruinen.md` - Ruinen-Mechanik
- `docs/08_feature_markt_handel.md` - Handelssystem
- `docs/24_feature_weltgenerierung.md` - Weltkarte
- `docs/29_feature_auth_system.md` - Authentifizierung

**Spezialdokumentation:**
- `docs/09_DATENBANK_ABGLEICH.md` - DB Schema Abgleich
- `docs/27_weltkarte_db_migration.md` - Migrationen

---

## 🚀 Schnellstart für neue Sessions

1. **SESSION_LOG.md lesen** - Status der letzten Session prüfen
2. **AGENT_START.md konsultieren** - Projektübersicht auffrischen
3. **Offene Aufgaben identifizieren** - Was wurde zuletzt gemacht?
4. **Planning-Phase starten** (bei komplexen Tasks)
5. **Sub-Agenten delegieren** mit `delegate_task`
6. **Ergebnisse konsolidieren** und umsetzen
7. **SESSION_LOG.md aktualisieren** - Fortschritt dokumentieren

---

**Dieses File ist die autoritative Quelle für Agenten-Konfiguration.**  
**Bei Änderungen dieses Files: Alle anderen Agenten-Dokumentationen anpassen!**

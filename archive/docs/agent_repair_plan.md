# AI Agent Reparaturplan - Wasteland Projekt

Dieser Plan wurde automatisiert erstellt, um Inkonsistenzen und unvollständige Implementationen im Projekt zu beheben. Er ist optimiert für die Abarbeitung durch autonome Agenten (Argentic Systems).

## 1. Audit-Ergebnisse & Fehleranalyse

### 1.1 Dokumentation & Indexierung
- **Problem**: `context/index.yaml` ist nicht synchron mit `context/index.json`. Der Block `b-bunker-system` fehlt in der YAML-Version.
- **Problem**: `CHANGELOG.md` enthält inkonsistente Daten (2026-02-22 vs 2026-03-16) und veraltete "Nächste Schritte", die bereits implementiert wurden.

### 1.2 Frontend-Backend Diskrepanz (Kritisch)
- **Problem**: Die in Phase 4 implementierten Backend-Systeme (Militär, Kampf, Diplomatie, Bunker) verfügen über keine UI-Integration in `index.html`, `js/app.js` oder `js/province.js`.
- **Details**:
    - Militär: Training/Entlassung von Einheiten nicht möglich.
    - Kampf: Armeebewegung und Kampfstatus nicht sichtbar.
    - Diplomatie: Beziehungen zu anderen Spielern nicht einsehbar/änderbar.
    - Bunker: Startprovinz-Beanspruchung (`/world/claim`) nur via API möglich.

### 1.3 Code-Qualität & Redundanz
- **Problem**: In `app/api/province.py` gibt es redundante Endpunkt-Definitionen (z.B. `@router.post("/{province_id}/deposits/search")` existiert doppelt).
- **Problem**: `admin.html` ist ein monolithisches "Monster" (>2200 Zeilen), das schwer zu warten ist und die neuen Systeme nicht abbildet.

---

## 2. Implementierungs-Schritte (Priorisiert)

### 🚀 Phase A: Dokumentation & Cleanup
1. Synchronisiere `context/index.yaml` mit `index.json`.
2. Bereinige `CHANGELOG.md` (Daten korrigieren, "Nächste Schritte" aktualisieren).
3. Entferne doppelte Endpunkte in `app/api/province.py`.

### 🛡️ Phase B: UI-Integration (Kern-Features)
1. **Militär-UI**: 
    - Neuen Tab "Militär" in der Provinzansicht (`index.html`) hinzufügen.
    - Logik in `js/province.js` zum Laden des Militär-Status und zum Auslösen von Training/Entlassung.
2. **Bunker-UI**:
    - "Bunker öffnen"-Button im Welcome-Overlay oder in der Weltkarte integrieren.
    - API-Anbindung an `/world/claim`.
3. **Diplomatie-UI**:
    - Globales Menü oder Tab für "Diplomatie" hinzufügen.
    - Liste der Mitspieler und deren Beziehungsstatus anzeigen.
4. **Kampf-UI**:
    - Armeen auf der Weltkarte (`js/worldmap.js`) visualisieren.
    - Befehlsmenü für Armeen (Bewegen, Rückzug).

### ⚙️ Phase C: Admin-Panel & Polish
1. Admin-Panel (`admin.html`) um die neuen Datenmodelle (`Army`, `DiplomacyRelation`) erweitern.
2. `SECRET_KEY` Handhabung in `app/config.py` dokumentieren oder via `.env` absichern.

---

## 3. Validierungs-Checkliste

- [ ] `context/index.yaml` enthält alle 19+ Blöcke.
- [ ] Militär-Tab in der Provinz zeigt korrekte Zahlen an.
- [ ] Einheiten-Training zieht Ressourcen/Zeit korrekt ab.
- [ ] Armeen sind auf der Karte sichtbar.
- [ ] CHANGELOG ist auf dem Stand 2026-03-16.

---
*Erstellt am: 2026-03-16 | Status: In Umsetzung*

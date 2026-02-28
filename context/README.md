Context v2.2.0 — Struktur-Guide

Ziel: Eine lean, maschinenlesbare Form des Kontextes schaffen, die Seed-/Prompt-Inputs sauber injizierbar macht und das Risiko einer Context-Überladung reduziert.

Grundprinzipien
- Jede Kontext-Information wird in Blöcken (Blocks) organisiert, mit klarer Zuordnung zu Domain und Zweck.
- Blöcke sind als eigenständige YAML-Dateien abgelegt und durch einen zentralen Index referenziert.
- Eine Version (v2.2.0) dient als Kompatibilitäts- und Migrationsmarker.
- Metadaten unterstützen Nachverfolgung (Zeitstempel, Status, Token‑Schätzung).

Dateistruktur (Beispiel)
- index.yaml: Verzeichniskarte auf alle Blöcke
- blocks/: Enthält einzelne Block-Dateien, z. B. b-backend-health.yaml
- references/: Quellverweise/Links zu Originalquellen

Beispiel-Block (MVP)
- File: blocks/b-backend-health.yaml
- File: blocks/b-api-endpoints.yaml
- File: blocks/b-risks.yaml

Stil & Semantik
- Format: YAML (lesbar) – JSON akzeptabel, wenn maschinelles Parsen benötigt.
- Felder: id, type, title, domain, summary, details, sources, related_codes, created_at, updated_at, status, tokens_estimate

Nutzung
- Neue Blöcke hinzufügen, Index aktualisieren, README dokumentieren.
- Vor dem Umstieg: validieren, dass Prompts zuverlässig nur relevante Blöcke laden.

Hinweise zur Migration
- Starte mit einem 2–3 Block MVP (Beispiele: Backend-Health, API-Endpunkte, Risiken).
- Erstelle einen kurzen Converter-Skripte (z. B. Python), der existierende Context-Abschnitte in Blöcke überführt.

Letzte Aktualisierung: 2026-02-28

Zusatz: MVP‑Blöcke (Beispiele)
- Bedeutsame Blöcke liegen unter context/v2.2.0/blocks/
- Bevorzugte Namenskonvention: b-<topic>.yaml
- Neue Blöcke: deployment-plan, frontend-workflow, api-docs

Konverter (Konzept)
- Es gibt einen kleinen Converter (Python/JS), der existierende Markdown-Kontexte in Blöcke überführt.
- Ziel ist eine einfache Migration, kein perfekter Parser in der ersten Iteration.

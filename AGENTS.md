AGENTS – Open Context Migration (v2.2.0)

Zweck
- Koordination und Dokumentation der Kontext-Migration von v2.x in eine offene, maschinenlesbare Block-Struktur.
- Sicherstellen, dass Backend- und Frontend-Komponenten konsistent abgebildet sind und Prompts zuverlässig seedbar bleiben.

Rollen (Open-Format-Namen)
- Backend-Mapper: mapped blocks for backend endpoints, architecture, data-models, security, deployment.
- Frontend-Mapper: mapped frontend endpoints, flows, UX guidelines, UI components, performance.
- Validator: prüft, dass Blöcke die Required-Keys enthalten (id, type, title, domain, summary, details, sources, created_at, updated_at, status, tokens_estimate).
- Patch-Generator: erstellt diff/patch-Dateien zum manuellen Patchen, falls kein Python-Apply genutzt wird.
- Migration-Orchestrator: koordiniert Dry-Run, Apply, Backup, Verifikation, und ggf. Rollback.

Vorgehen (empfohlen)
- 1) Dry-Run erneut prüfen: Welche Blöcke würden erstellt und welche Pfade aktualisiert? Dann freigeben.
- 2) Apply: Blöcke endgültig migrieren, Index aktualisieren, Originaldateien löschen oder archivieren.
- 3) Validierung: YAML-Block-Validierung über Validator; OpenAPI-Block-Validierung; Rippen-Quellen-Verweise prüfen.
- 4) Backup: Bundle/Zip der v2.2.0-Struktur vor weiteren Migrationen sichern.
- 5) Frontend-Phase vorbereiten: Blöcke für Frontend-Verträge ergänzen.

Dateipfade (aktuell beobachtet)
- Backend-Blöcke liegen derzeit unter context/blocks/...
- Frontend-Blöcke liegen derzeit unter context/blocks/...
- Index-Dateien: context/index.yaml, context/index.json

Hinweise zur künftigen Umstellung
- Die Open-Format-Standards: YAML oder JSON sind akzeptiert; YAML bleibt lesbar, JSON leichter maschinell zu parsen.
- Konsistenzregeln: Felder in Blöcken: id, type, title, domain, summary, details, sources, created_at, updated_at, status, tokens_estimate.
- Nach der Migration: Entferne die Zwischenebene v2.2.0 schrittweise, sobald alle Blöcke stabil integriert sind.

Quellen/Referenzen (intern)
- CONTEXT_MASTER.md, CONTEXT_DOKUMENTATION.md, BACKEND_CONTEXT.md, BACKEND_README.md (Quellen der Migration)
- Open-Format-Standards: YAML/JSON, UTF-8, ASCII-Only, keine Binary-Artefakte.

Hinweis: Diese Datei dient als organisiertes Handbuch für die Koordination; Inhalte können von Build-Prozessen gelesen werden, um Automatisierung zu unterstützen.

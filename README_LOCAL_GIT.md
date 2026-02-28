Lokale Git-Workflows fuer das Projekt (ohne Remote-Hosting)

Ziel: Saubere Versionskontrolle, Reproduzierbarkeit und einfache Backups, ganz ohne GitHub.

Setup
- repo initialisieren: already done in this Arbeitsverzeichnis.
- .gitignore ignoriert sensible Dateien (siehe .gitignore).

Grundlegender Workflow
- Branching:
  - Hauptzweig: main
  - Feature/Refactor: git checkout -b feature/<beschreibung>
- Commits:
  - Kurze, beschreibende Messages mit Fokus auf Warum statt Was
  - Beispiele: feat(context): neue MVP-Blöcke hinzugefügt
- Backups/Portabilität:
  - Bundle-Exports: git bundle create wasteland.bundle --all
  - Transport auf andere Maschine: git fetch path/to/bundle
- Versionierung/Releases:
  - Tags verwenden: git tag v2.2.0-local
  - Lokale Releases als Snapshot definieren

Nützliche Befehle
- Bundle erstellen: ./tools/export_bundle.sh
- Bundle in anderes Repo importieren: ./tools/import_bundle.sh /pfad/zum/bundle.bundle
- Lokale Checks ausführen: git status; git log --oneline -n 5

Hinweise
- Arbeite primär auf Branches; merge oder rebase nur nach Review.
- Secrets nie committen; sensitive Dateien in .gitignore belassen.
- Falls später Remote nötig wird, kannst du ein privates Git-Server-Setup (z.B. Gitea) hosten.

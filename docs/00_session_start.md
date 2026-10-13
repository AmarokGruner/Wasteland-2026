# Wastelands – Agent Session Start

## Project
Browser-based RTS game (Python 3, FastAPI, SQLite, Vanilla JS).
Codebase uses `seed_gebaeude.py` + `seed_ressourcen.py` as lookup tables.

## Tech Stack
| Layer | Tech |
|---|---|
| Backend | Python 3, FastAPI, SQLite, SQLAlchemy, Pydantic |
| Auth | SHA256-Token (localStorage), roles: admin/player |
| Frontend | Vanilla JS (ES6+), HTML Canvas |
| Admin | admin.html (standalone, token-protected) |
| Deployment | Raspberry Pi 3B+ |

## Completed Prompts (reference only – do NOT re-implement)
1. `wasteland_roundlogic_en.md` – Round spool, time credit, pro-rata prod/consumption, 48h hunger warning
2. `gebaeude_v3_admin_grid.md` – Building build/upgrade, Stadtausbau (Camp→Metropole), 13x13 admin-configurable field grid, city expansion logic

## Session Goal
Implement the feature described in the attached `feature_*.md` file for this session.
Always deliver **complete, working code**: SQLAlchemy models, Pydantic schemas, FastAPI routes, core logic.
Follow existing patterns from the completed prompts above.
Atomic DB commits. No negative resources/population. German error messages.

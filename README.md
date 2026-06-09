# Wasteland – Verbrannte Zone

A browser‑based post‑apocalyptic strategy game.
Backend is a FastAPI service (port 8011) with SQLite, Admin UI,
and a Webcrawler integration. Frontend is vanilla JavaScript.
All source lives in `./Wasteland/`.

## Repository layout
```
Wasteland/
├─ app/               # FastAPI source (auth, admin, public endpoints)
├─ js/                # Frontend JavaScript
├─ css/
├─ data/
├─ verbrannte_zone.db # SQLite DB (dev only)
└─ docs/              # Markdown docs, including Backend_API.md
```

## Development setup
```bash
cd /home/fabian/Wasteland
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload   # runs on http://localhost:8011
```

## CI / GitHub Actions
The repository contains a pre‑configured workflow that:
- Installs Python deps
- Runs `pytest tests/`
- Lints with flake8

## License
MIT © 2026, developed by FabiaN (AmarokGruner).

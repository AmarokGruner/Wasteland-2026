# Backend API – Wasteland (Verbrannte Zone)

## Overview
This document describes the public FastAPI endpoints that are currently available for the Wasteland browser game.
All routes live under **`/api/`** (except static HTML files) and are documented via the OpenAPI schema at
`https://localhost:8011/api/docs`.  

The backend is split into three logical layers:

* **Auth** – JWT‑based login, token validation and role handling.
* **Admin** – CRUD operations for game data (terrain, resources, buildings) – protected by `admin` role.
* **Public / Player** – read‑only data that the UI uses without authentication (e.g. province lists, player inventory).

## Base URL
```
http://localhost:8011/api/
```

> **Note** – In production the API is served behind nginx on port 443 (HTTPS). Use the same base path, only the scheme/port changes.

---

## 1️⃣ Authentication Service
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/login` | `POST` | Returns JWT access‑token and refresh token. Body: `{ "username": "...", "password": "..." }`. |
| `/auth/refresh` | `POST` | Refreshes an access token using a valid refresh token (sent in the body). |
| `/auth/me` | `GET` *(requires token)* | Returns current user profile (`username`, `role`). |

### Example – Login
```bash
curl -X POST http://localhost:8011/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"securepwd"}'
```

Response (200):
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "dXNlcjp3c2VyMTIz"
}
```

---

## 2️⃣ Admin Service (protected – `admin` role required)
All admin routes are prefixed with `/admin/*`.  
The FastAPI router checks the JWT via `Depends(get_current_user)` and also verifies that
`token["role"] == "admin"`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/admin/terrain` | `GET /list`, `POST /create` |
| `/admin/resource` | `GET /list`, `POST /create` |
| `/admin/building_type` | `GET /all`, `POST /create` |
| `/admin/province` | CRUD for provinces (GET, POST, PUT, DELETE) |
| `/admin/crawler/start` | `POST` – start a new Webcrawler run (optional). |

### Example – Create a New Terrain
```bash
curl -X POST http://localhost:8011/api/admin/terrain \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name":"Wüstenpfad","radius":12}'
```

Response (201):
```json
{
  "id": 47,
  "name": "Wüstenpfad",
  "radius": 12
}
```

---

## 3️⃣ Public / Player Service (no auth required)
These endpoints are used by the vanilla‑JS front‑end to display static game information.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/public/players` | `GET` – list visible player summaries |
| `/public/province/{id}` | `GET` – detailed province data (resources, troops) |
| `/public/market` | `GET /list`, `POST /buy` – market listings |
| `/public/messages` | `GET /list`, `POST /send` – in‑game chat |

### Example – Get Province Details
```bash
curl http://localhost:8011/api/public/province/42?t=cache&v=3
```

Response (200):
```json
{
  "id": 42,
  "name": "Stadt der Asche",
  "owner_id": 3,
  "resources": {"mips":120,"coins":45},
  "troops": [
    {"type":"soldier","count":12}
  ]
}
```

---

## 4️⃣ Crawler Service (admin only – optional v2.0)
If the background crawler is enabled, additional admin endpoints exist under `/admin/crawler/*`:
* `POST /crawler/start` – start a run with a set of categories.
* `GET /crawler/status` – current status (`idle`, `running`, `finished`).
* `GET /crawler/changes/{session_id}` – pending changes to review.
* **All responses are paginated** (`limit`, `offset`).

### Example – Get Crawler History
```bash
curl http://localhost:8011/api/admin/crawler/history?limit=20
```

---

## 5️⃣ Common Query‑Parameter Gotchas
FastAPI does **not** read query parameters automatically – they must be declared in the function signature.
If an endpoint returns `404 Not Found` while you are sure it exists, check that the function accepts the token as a `Query` parameter:

```python
def get_players(token: str = Query(...), db: Session = Depends(get_db)):
    ...
```

---

## 6️⃣ Error‑Handling & Status Codes
| Code | Meaning |
|------|---------|
| 200  | Success, JSON payload. |
| 401  | No / invalid JWT – use `/auth/refresh` or re‑login. |
| 403  | JWT valid but role insufficient (e.g., non‑admin trying admin route). |
| 404  | Endpoint exists but URL mismatch (common when generic `/{{entity}}/{{id}}` catches a specific route). |
| 500  | Internal server error – check `uvicorn.log` for traceback. |

---

## 7️⃣ Development Tips
* **Run the server with `uvicorn app.main:app --host 0.0.0.0 --port 8011`** (no SSL in dev).
* **Clear Python cache before a restart**:
  ```bash
  rm -rf app/__pycache__ app/api/__pycache__
  ```
* **After adding a new endpoint** remember to:
  1. Add a test in `tests/backend/test_<module>.py`.
  2. Update `docs/player-ui/Backend_API.md` (the section you are reading now).
  3. Commit with a message following the pattern:
     ```
     feat: add admin endpoint /admin/market/buy
     ```

---

## 8️⃣ Related Documentation (Obsidian Vault)
* `docs/player-ui/ui_implementation_status.md` – mapping of UI components to backend services.
* `docs/player-ui/CRAWLER_DASHBOARD_V2.md` – how the crawler UI talks to `/admin/crawler/*`.
* `docs/arg-functions/` – advanced Argentic Function orchestration (used internally for batch updates).

---

*Last updated: 2026‑06‑13 – corresponds to Wasteland v1.6, Hermes Agent 2024‑07‑15.*  
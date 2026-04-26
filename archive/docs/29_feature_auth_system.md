# Feature: Authentifizierung & Login-System

## Ziel
Sicheres und vollständiges Authentifizierungssystem für Spieler und Admins. Ersetzt simple/unsichere Logins durch JWT-basierte Authentifizierung mit Hashing, Refresh-Tokens und Passwort-Reset.

## 1. Datenbank-Anpassungen (Tabelle `users`)
- `id` (PK)
- `username` (unique, varchar)
- `email` (unique, varchar)
- `password_hash` (varchar)
- `role` (enum: 'user', 'admin', 'banned')
- `created_at` (datetime)
- `last_login` (datetime)
- `reset_token` (varchar, nullable)
- `reset_token_expires` (datetime, nullable)

## 2. Backend (FastAPI / Auth)
- **Hashing:** Nutzung von `passlib` (bcrypt) für Passwörter.
- **JWT:** Ausgabe von Access-Tokens (gültig 2h) und Refresh-Tokens (gültig 7 Tage).
- **Endpoints:**
  - `POST /auth/register`: Erstellt User + leeres Player-Profil.
  - `POST /auth/login`: Prüft Credentials, gibt `{access_token, refresh_token, player_id, role}` zurück. Aktualisiert `last_login`.
  - `POST /auth/refresh`: Nimmt Refresh-Token, gibt neuen Access-Token.
  - `POST /auth/forgot-password`: Generiert `reset_token` und loggt URL (später E-Mail).
  - `POST /auth/reset-password`: Setzt neues Passwort mit gültigem Token.
- **Middleware/Dependency:** `get_current_user(token)` prüft Signatur und Ablaufdatum.

## 3. Frontend (UI)
- **`login.html` & `register.html`**: Formulare mit Validierung (Passwortlänge, E-Mail-Format).
- **Local Storage:** Speicherung von `token`, `refresh_token`, `player_id`, `role`.
- **Fetch Wrapper (`app-2.js`)**:
  - Globaler Interceptor für alle `fetch()`-Calls: Wenn 401 (Unauthorized) zurückkommt, versuche automatisch `/auth/refresh`.
  - Schlägt Refresh fehl -> Logout und Redirect zu `login.html`.

## 4. Edge Cases & Sicherheit
- Keine Passwörter im Klartext loggen.
- Banned Users dürfen kein Token mehr generieren.
- Brute-Force-Schutz: Nach 5 falschen Versuchen Account für 15 Minuten sperren (optional, einfache Zähler-Spalte `failed_login_attempts`).

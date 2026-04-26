# Feature: Error-Handling & Offline-Modus

## Ziel
Ein Browsergame reagiert oft empfindlich auf kurze Verbindungsabbrüche. Die UI muss gracefully degraden (sanft reagieren) statt Fehler in der Konsole zu werfen oder halbfertig zu rendern.

## 1. Globaler Fetch-Wrapper (`app-2.js`)
Ersetze alle nackten `fetch()` calls durch eine zentrale Funktion `apiFetch(url, options)`.
- Implementiert Timeout (z.B. 10 Sekunden).
- Fängt `TypeError: Failed to fetch` (Netzwerkfehler) ab.
- Setzt einen globalen State `isOffline = true`.

## 2. Offline-UI State
- Wenn `isOffline == true`:
  - Topbar ändert Farbe (z.B. roter Balken: "Keine Verbindung zum Server... Verbinde neu").
  - Alle Aktions-Buttons (Bauen, Rekrutieren, Markt) erhalten das Attribut `disabled`.
  - CSS: `opacity: 0.7; cursor: not-allowed;` für Container.

## 3. Auto-Reconnect
- Der Wrapper versucht im Hintergrund alle 5 Sekunden einen Ping an `GET /health`.
- Sobald 200 OK zurückkommt -> `isOffline = false`.
- Lade die aktuelle View neu (`showView(currentView)`), um inkonsistente States zu fixen.
- Verstecke rote Offline-Leiste, schalte Buttons wieder frei.

## 4. Standardisiertes Backend-Error-Handling
- Sicherstellen, dass das Backend immer folgendes JSON-Format bei 400/500 zurückgibt:
  `{ "error": true, "code": "NOT_ENOUGH_RESOURCES", "detail": "Dir fehlen 50 Eisen" }`
- Der Wrapper fängt dies ab und wirft automatisch einen `showToast(data.detail, 'error')`. Kein manuelles Error-Handling pro Button-Klick mehr im Frontend.

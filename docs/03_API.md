# API Endpunkte & Schnittstellen

**Wasteland REST API | Version 1.6**

---

## 📡 API Übersicht

Die API folgt RESTful Prinzipien und verwendet JSON für Request/Response. Alle Endpunkte sind in `app/api/` definiert und in `app/main.py` gemountet.

### Basis-URL
```
http://localhost:8011/api/
https://your-domain.com/api/  (Production)
```

### Authentifizierung
- **Methode:** JWT Bearer Token
- **Header:** `Authorization: Bearer <token>`
- **Token-Laufzeit:** 24 Stunden
- **Refresh:** Neuanmeldung erforderlich

---

## 🔐 Authentifizierung (`/auth`)

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| `POST` | `/auth/register` | Neuen Benutzer registrieren |
| `POST` | `/auth/login` | Login und Token erhalten |
| `GET` | `/auth/me` | Aktuelles Benutzerprofil |

### Login Request
```json
{
  "username": "player1",
  "password": "secure_password"
}
```

### Login Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": 1,
  "username": "player1"
}
```

---

## 🏘️ Provinz-Management (`/province`)

| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `GET` | `/province/` | Alle Provinzen des Spielers | ✓ |
| `POST` | `/province/` | Neue Provinz gründen | ✓ |
| `GET` | `/province/{id}` | Provinz-Details | ✓ |
| `PUT` | `/province/{id}` | Provinz bearbeiten | ✓ |
| `DELETE` | `/province/{id}` | Provinz aufgeben | ✓ |

### Gebäude bauen
| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `POST` | `/province/{id}/build` | Gebäude errichten | ✓ |

**Request Body:**
```json
{
  "gebaeude_typ_id": 2,
  "x": 10,
  "y": 15
}
```

### Gebäude abreißen
| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `POST` | `/province/{id}/demolish` | Gebäude entfernen (50% Ressourcen-Rückerstattung) | ✓ |

### Gebäude-Liste
| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `GET` | `/province/{id}/buildings` | Alle Gebäude der Provinz | ✓ |

---

## 🏭 Ressourcen & Handel (`/market`)

| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `GET` | `/market/` | Verfügbare Ressourcen | ✓ |
| `POST` | `/market/trade` | Handel zwischen Provinzen | ✓ |
| `GET` | `/market/routes` | Handelsrouten | ✓ |

### Handel Request
```json
{
  "von_provinz_id": 1,
  "zu_provinz_id": 2,
  "ressource_id": 5,
  "menge": 100
}
```

---

## ⚔️ Militär & Kampf (`/army`, `/combat`)

| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `GET` | `/army/` | Eigene Einheiten | ✓ |
| `POST` | `/army/train` | Neue Einheit ausbilden | ✓ |
| `GET` | `/combat/{id}` | Kampfdetails | ✓ |

### Einheiten ausbilden
```json
{
  "province_id": 1,
  "einheit_typ_id": 1,  // Rekrut
  "anzahl": 10
}
```

---

## 🗺️ Weltkarte (`/world`)

| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `GET` | `/world/map` | Weltkarte (50x50) | ✓ |
| `GET` | `/world/terrains` | Alle Terrain-Typen | - |
| `GET` | `/world/vorkommen` | Vorkommen-Liste | - |

### Weltkarte Response
```json
{
  "width": 50,
  "height": 50,
  "cells": [
    {
      "x": 0,
      "y": 0,
      "terrain_id": 1,
      "province_id": null,
      "gebaeude_id": null
    }
  ]
}
```

---

## 👨‍💼 Admin-API (`/admin`)

**Alle Admin-Endpunkte erfordern Admin-Rechte!**

| Methode | Endpunkt | Beschreibung |
|---------|----------|--------------|
| `GET` | `/admin/dashboard` | Admin-Dashboard |
| `POST` | `/admin/gebaeude_typen` | Gebäude-Typ verwalten |
| `POST` | `/admin/ressourcen` | Ressource verwalten |
| `GET` | `/admin/provinzen` | Alle Provinzen |
| `POST` | `/admin/users` | Benutzer verwalten |
| `GET` | `/admin/gamelog` | Spiel-Logbuch |

### Gebäude-Typ erstellen
```json
{
  "name": "NeuesGebäude",
  "kategorie": "Industrie",
  "tech_level": 1000,
  "baukosten_mips": 50000,
  "produktion": "[{\"ressource\": \"Stahl\", \"menge\": 10}]"
}
```

---

## 📊 System-Endpunkte

| Methode | Endpunkt | Beschreibung | Auth |
|---------|----------|--------------|------|
| `GET` | `/health` | Health Check | - |
| `GET` | `/metrics` | Prometheus Metrics | - |

---

## 🔒 Fehlerbehandlung

### HTTP Status Codes
| Code | Bedeutung |
|------|-----------|
| 200 | Erfolg |
| 201 | Erstellt |
| 400 | Ungültige Anfrage |
| 401 | Nicht authentifiziert |
| 403 | Keine Berechtigung |
| 404 | Nicht gefunden |
| 500 | Interner Serverfehler |

### Fehler Response Format
```json
{
  "detail": "Beschreibung des Fehlers",
  "errors": [
    {
      "field": "username",
      "message": "Benutzername bereits vergeben"
    }
  ]
}
```

---

## 📝 Wichtige Hinweise

1. **Rate Limiting:** Max 60 Anfragen/Minute pro User
2. **Pagination:** Liste-Endpunkte unterstützen `?page=1&limit=50`
3. **Filterung:** Viele Endpunkte unterstützen Query-Parameter
4. **JSON:** Alle Request/Response Daten sind JSON

---

**Letzte Aktualisierung:** 2026-10-14  
**API Dokumentation:** OpenAPI Spec in `docs/openapi_spec.json`

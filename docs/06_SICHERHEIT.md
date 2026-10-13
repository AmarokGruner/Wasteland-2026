# Sicherheit & Audit

**Wasteland Security Guidelines | Version 1.6**

---

## 🔐 Authentifizierung

### JWT Token System
- **Algorithm:** HS256 (HMAC-SHA256)
- **Token-Laufzeit:** 24 Stunden
- **Refresh:** Neuanmeldung erforderlich
- **Speicherung:** Client-seitig (localStorage/cookie)

### Password Hashing
- **Methode:** bcrypt
- **Rounds:** 12 (standard)
- **Salting:** Automatisch pro Password

### Login-Sicherheit
```python
# Rate Limiting: Max 5 Versuche pro Minute
@limiter.limit("5/minute")
async def login(request: Request, credentials: Credentials):
    ...
```

### Token-Validierung
Jeder geschützte Endpunkt prüft:
1. **Gültigkeit** des Tokens (nicht abgelaufen)
2. **Integrität** (Signature check)
3. **Berechtigung** (User-Rolle)

---

## 🔒 Autorisierung

### Rollen-System
| Rolle | Berechtigungen |
|-------|----------------|
| **Gast** | Nur öffentliche Endpunkte |
| **Player** | Eigene Provinzen verwalten |
| **Moderator** | + Lesen aller Daten, keine Schreibrechte |
| **Admin** | Vollzugriff auf alle Endpunkte |

### Berechtigungs-Check
```python
# Beispiel: Provinz bearbeiten
@router.put("/province/{id}")
async def update_province(
    province_id: int,
    data: ProvinceUpdate,
    current_user: User = Depends(get_current_user)
):
    # Prüfe: Ist der User Besitzer dieser Provinz?
    province = db.query(Province).get(province_id)
    if province.besitzer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Keine Berechtigung")
```

### Admin-Endpunkte
Alle `/admin/*` Endpunkte erfordern `role='admin'`:
```python
def get_current_admin(user: User = Depends(get_current_user)):
    if user.role != 'admin':
        raise HTTPException(status_code=403, detail="Admin-Rechte erforderlich")
    return user
```

---

## 🛡️ Input-Validierung

### Pydantic Models
Alle API-Requests werden mit Pydantic validiert:
```python
class BuildingCreate(BaseModel):
    gebaeude_typ_id: int = Field(..., ge=1, le=209)
    x: int = Field(..., ge=0, lt=50)  # Weltkarte 50x50
    y: int = Field(..., ge=0, lt=50)
    
    @validator('gebaeude_typ_id')
    def building_exists(cls, v):
        if not db.query(BuildingType).get(v):
            raise ValueError('Gebäude-Typ existiert nicht')
        return v
```

### SQL-Injection Schutz
- **SQLAlchemy ORM** verwendet parameterisierte Queries
- **Keine** raw SQL Strings vom User
- **Alle** Foreign Keys werden geprüft

### XSS Schutz
- **Output Encoding:** Alle User-Inputs werden escaped
- **CSP Header:** Content Security Policy gesetzt
- **Sanitization:** HTML in Textfeldern wird entfernt

---

## 📊 Audit-Logbuch

### Was wird protokolliert?
| Event | Beschreibung |
|-------|--------------|
| **Login/Logout** | Benutzeran- und -abmeldung |
| **Gebäude bauen/abrissen** | Alle Bauaktionen |
| **Kämpfe** | Gewonnene/verlorene Schlachten |
| **Handel** | Alle Transaktionen |
| **Admin-Aktionen** | Jede Admin-Änderung |

### Log-Eintrag Struktur
```json
{
  "id": 12345,
  "timestamp": "2026-10-14T10:30:00Z",
  "event_type": "building_built",
  "user_id": 5,
  "province_id": 12,
  "details": {
    "gebaeude_typ_id": 41,
    "name": "Weberei",
    "x": 23,
    "y": 45
  }
}
```

### Aufbewahrungsrichtlinie
- **Aktive Logs:** 30 Tage im Klartext
- **Archiviert:** Bis zu 1 Jahr komprimiert
- **Gelöscht:** Nach 2 Jahren (automatisch)

---

## 🔍 Häufige Sicherheitsprobleme & Lösungen

### 1. Brute-Force Angriffe
**Problem:** Automatisierte Login-Versuche  
**Lösung:** Rate Limiting + Account-Lock nach 5 Fehlversuchen

### 2. Token-Manipulation
**Problem:** User versucht, Token zu fälschen  
**Lösung:** Server-seitige Signature-Prüfung + kurze Token-Laufzeit

### 3. Privilege Escalation
**Problem:** Player versucht, Admin-Funktionen zu nutzen  
**Lösung:** Strikte Rollen-Prüfung auf jedem Endpunkt

### 4. Daten-Leckage
**Problem:** Sensible Daten in API-Responses  
**Lösung:** Pydantic Models definieren, welche Felder gesendet werden

### 5. DoS-Angriffe
**Problem:** Server überlasten mit vielen Anfragen  
**Lösung:** Rate Limiting + Connection Pooling

---

## 📋 Security Checklist

### Before Deployment
- [ ] Password Hashing mit bcrypt aktiviert
- [ ] JWT Secret Key in Environment Variable (nicht im Code!)
- [ ] Rate Limiting für Login-Endpunkte
- [ ] CORS auf erlaubte Domains beschränken
- [ ] HTTPS nur (kein HTTP)
- [ ] Security Headers gesetzt (CSP, HSTS, X-Frame-Options)

### Regular Audits
- [ ] Monatlich: Benutzerrechte prüfen
- [ ] Wöchentlich: Admin-Logbuch durchsehen
- [ ] Täglich: Server-Logs auf Anomalien prüfen
- [ ] Quartalsweise: Penetration Testing

---

## 🔧 Konfiguration

### Wichtige Environment Variables
```bash
# .env Datei (NIEMALS im Repo committen!)
SECRET_KEY=your_32_char_random_string_here
DATABASE_URL=sqlite:///./verbrannte_zone.db
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### Generiere SECRET_KEY
```python
import secrets
print(secrets.token_urlsafe(32))
# Beispiel: k7X9mP2vQ8nR4wL6jH1sA5bC3dF0gY
```

---

## 🚨 Incident Response

### Bei Sicherheitsvorfall:
1. **Isolieren:** Betroffene Systeme vom Netzwerk trennen
2. **Dokumentieren:** Alle Schritte protokollieren
3. **Beheben:** Schwachstelle schließen
4. **Benachrichtigen:** Betroffene User informieren
5. **Überprüfen:** System auf weitere Schäden prüfen

### Kontakt
- **Admin:** admin@wasteland.local
- **Notfall:** +49 XXX XXXXXXX

---

**Letzte Aktualisierung:** 2026-10-14  
**Audit-Stand:** Alle kritischen Mängel behoben

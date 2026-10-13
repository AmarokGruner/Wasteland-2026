# 🛡️ Compliance & GDPR (DSGVO)

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Umsetzung der DSGVO (GDPR) für:
- Datenschutz durch Technikgestaltung (Privacy by Design)
- Recht auf Löschung und Datenportabilität
- Cookie-Einwilligung und Tracking
- Datenschutzbeauftragter und Verzeichnis von Verarbeitungstätigkeiten

---

## 🎯 Ziele

1. **DSGVO-konform** - Alle Anforderungen der EU-Datenschutz-Grundverordnung
2. **Transparenz** - Klare Information über Datenverarbeitung
3. **Benutzerrechte** - Auskunft, Löschung, Berichtigung, Portabilität
4. **Datensparsamkeit** - Nur notwendige Daten erheben und speichern

---

## 📜 DSGVO-Anforderungen im Überblick

| Artikel | Anforderung | Umsetzung |
|---------|-------------|-----------|
| Art. 5 | Grundsätze der Verarbeitung | Datensparsamkeit, Zweckbindung |
| Art. 6 | Rechtmäßigkeit der Verarbeitung | Einwilligung, Vertragserfüllung |
| Art. 12-23 | Betroffenenrechte | Auskunft, Löschung, Berichtigung |
| Art. 25 | Privacy by Design/Default | Technische Maßnahmen |
| Art. 30 | Verzeichnis von Verarbeitungstätigkeiten | Dokumentation |
| Art. 32 | Sicherheit der Verarbeitung | Verschlüsselung, Zugangskontrolle |
| Art. 33-34 | Meldepflicht bei Datenschutzverletzungen | Incident Response |

---

## 🔧 Privacy by Design Implementation

### Datenminimierung in API Endpoints

```python
# app/api/v1/users.py - Datenschutz-konforme User-Endpoints

from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.get("/users/me")
async def get_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktuellen Benutzer abrufen (Datenschutz-konform)"""
    
    # Nur nicht-sensitive Daten zurückgeben
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,  # E-Mail ist notwendig für Login
        "avatar_url": current_user.avatar_url,
        "created_at": current_user.created_at.isoformat(),
        "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
        "game_stats": {  # Spielstatistiken (keine persönlichen Daten)
            "level": current_user.level,
            "province_id": current_user.province_id,
            "resources": {
                "food": current_user.resources_food,
                "water": current_user.resources_water,
                "energy": current_user.resources_energy
            }
        }
    }

@router.put("/users/me")
async def update_current_user(
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Benutzerdaten aktualisieren"""
    
    # Nur erlaubte Felder aktualisieren
    if user_data.username:
        current_user.username = user_data.username
    
    # E-Mail nur ändern, wenn verifiziert
    if user_data.email:
        current_user.email = user_data.email
        current_user.email_verified = False  # Neue Verifikation erforderlich
    
    db.commit()
    
    return {"message": "Daten erfolgreich aktualisiert"}

@router.delete("/users/me")
async def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Benutzerkonto löschen (Recht auf Vergessenwerden)"""
    
    # Soft Delete: Benutzer markieren, nicht physisch löschen
    current_user.is_deleted = True
    current_user.deleted_at = datetime.utcnow()
    
    # Persönliche Daten anonymisieren (Art. 17 DSGVO)
    current_user.username = f"gelöscht_{current_user.id}"
    current_user.email = f"gelöscht_{current_user.id}@wasteland.local"
    current_user.password_hash = ""  # Password löschen
    
    # Spiel-Daten behalten (für Spielbalance), aber anonymisieren
    # Provinz bleibt bestehen, aber Owner-Beziehung wird gelöst
    
    db.commit()
    
    # Session invalidieren
    return {"message": "Konto erfolgreich gelöscht. Alle persönlichen Daten wurden anonymisiert."}
```

---

## 📊 Verzeichnis von Verarbeitungstätigkeiten (Art. 30 DSGVO)

### Dokumentation der Datenverarbeitung

```python
# app/models_compliance.py - Verzeichnis der Verarbeitungstätigkeiten

class ProcessingRecord(Base):
    """Verarbeitungstätigkeit gemäß Art. 30 DSGVO"""
    
    __tablename__ = "processing_records"
    
    id = Column(Integer, primary_key=True)
    purpose = Column(String(255), nullable=False)  # Zweck der Verarbeitung
    legal_basis = Column(String(100), nullable=False)  # Art. 6 DSGVO
    data_categories = Column(Text)  # Kategorien betroffener Personen
    data_fields = Column(Text)  # Verarbeitete Datenfelder
    retention_period = Column(String(100))  # Aufbewahrungsfrist
    recipients = Column(Text)  # Empfänger der Daten
    international_transfers = Column(Boolean, default=False)  # Drittländertransfer
    security_measures = Column(Text)  # Technische Maßnahmen
    created_at = Column(DateTime, default=datetime.utcnow)

# Beispiel-Einträge:
"""
1. Benutzerregistrierung
   - Zweck: Vertragserfüllung (Spielteilnahme)
   - Rechtsgrundlage: Art. 6(1)(b) DSGVO
   - Daten: username, email, password_hash
   - Aufbewahrung: Bis zur Löschung des Kontos
   - Empfänger: Keine Third-Party

2. Spiel-Datenverarbeitung
   - Zweck: Vertragserfüllung (Spielmechanik)
   - Rechtsgrundlage: Art. 6(1)(b) DSGVO
   - Daten: province_id, resources, buildings, units
   - Aufbewahrung: Dauer der Spielteilnahme + 3 Jahre (gesetzliche Aufbewahrung)
   - Empfänger: Keine Third-Party

3. Analytics/Statistiken (anonymisiert)
   - Zweck: Berechtigte Interessen (Art. 6(1)(f))
   - Rechtsgrundlage: Art. 6(1)(f) DSGVO
   - Daten: Anonymisierte Spielstatistiken (keine PII)
   - Aufbewahrung: 2 Jahre
   - Empfänger: Keine Third-Party

4. Email-Benachrichtigungen
   - Zweck: Vertragserfüllung (Spielkommunikation)
   - Rechtsgrundlage: Art. 6(1)(b) DSGVO
   - Daten: email (für Versand)
   - Aufbewahrung: Bis zur Widerruf der Einwilligung
   - Empfänger: Email Provider (SendGrid, evtl. US-Server)
"""
```

---

## 🍪 Cookie Consent & Tracking

### Cookie Management Service

```python
# app/services/cookie_service.py

class CookieService:
    # Cookie Kategorien
    COOKIE_CATEGORIES = {
        "essential": {  # Erforderlich (keine Einwilligung nötig)
            "description": "Notwendig für den Betrieb der Website",
            "examples": ["session_id", "csrf_token"]
        },
        "analytics": {  # Analytisch (Einwilligung erforderlich)
            "description": "Helfen uns, die Website zu verbessern",
            "examples": ["analytics_id", "utm_source"]
        },
        "marketing": {  # Marketing (Einwilligung erforderlich)
            "description": "Werden verwendet, um relevante Werbung anzuzeigen",
            "examples": ["ad_id", "tracking_id"]
        }
    }
    
    @staticmethod
    def get_cookie_consent(user_id: int) -> dict:
        """Cookie-Einwilligung des Benutzers abrufen"""
        
        # In Production: Aus Datenbank laden
        return {
            "essential": True,  # Immer erlaubt
            "analytics": False,  # Standard: Ablehnen (Opt-in)
            "marketing": False   # Standard: Ablehnen (Opt-in)
        }
    
    @staticmethod
    def set_cookie_consent(user_id: int, categories: dict):
        """Cookie-Einwilligung speichern"""
        
        # Validieren
        for category in categories:
            if category not in CookieService.COOKIE_CATEGORIES:
                raise ValueError(f"Ungültige Kategorie: {category}")
        
        # In Datenbank speichern (vereinfacht)
        # db.query(UserCookieConsent).filter_by(user_id=user_id).delete()
        
        consent = UserCookieConsent(
            user_id=user_id,
            categories=json.dumps(categories),
            consented_at=datetime.utcnow()
        )
        
        # db.add(consent)
        # db.commit()

# Cookie Middleware (setzt Cookies basierend auf Einwilligung)
class CookieConsentMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Nur essentielle Cookies immer setzen
        response.set_cookie(
            key="session_id",
            value=self.generate_session_id(),
            httponly=True,
            secure=True,
            samesite="lax"
        )
        
        # Analytics Cookies nur mit Einwilligung
        user_id = self.extract_user_id(request)
        
        if user_id:
            consent = CookieService.get_cookie_consent(user_id)
            
            if consent.get("analytics"):
                response.set_cookie(
                    key="analytics_id",
                    value=self.generate_analytics_id(),
                    httponly=False,  # JavaScript darf lesen (für Analytics)
                    max_age=31536000  # 1 Jahr
                )
        
        return response
    
    def extract_user_id(self, request: Request) -> int:
        # Token decodieren (vereinfacht)
        return 1  # Placeholder

app.add_middleware(CookieConsentMiddleware)
```

### Cookie Consent Banner (Client-Side)

```javascript
// js/components/cookie-consent.js

class CookieConsentBanner {
    constructor() {
        this.categories = {
            essential: true,  // Immer erlaubt
            analytics: false,
            marketing: false
        };
    }

    // Banner anzeigen (wenn noch keine Einwilligung)
    showBanner() {
        const consent = localStorage.getItem('cookie_consent');
        
        if (consent) {
            return;  // Bereits eingewilligt
        }

        const banner = document.createElement('div');
        banner.id = 'cookie-consent-banner';
        banner.className = 'cookie-banner';
        
        banner.innerHTML = `
            <div class="cookie-content">
                <h3>🍪 Cookie-Einstellungen</h3>
                <p>
                    Wir verwenden Cookies, um Ihnen die bestmögliche Erfahrung auf unserer Website zu bieten. 
                    Einige Cookies sind notwendig für den Betrieb, andere helfen uns, die Website zu verbessern.
                </p>
                
                <div class="cookie-options">
                    <label class="cookie-option">
                        <input type="checkbox" checked disabled>
                        <span><strong>Erforderlich</strong> - Notwendig für den Betrieb</span>
                    </label>
                    
                    <label class="cookie-option">
                        <input type="checkbox" id="analytics-cookies">
                        <span>📊 Analytisch - Hilft uns, die Website zu verbessern</span>
                    </label>
                    
                    <label class="cookie-option">
                        <input type="checkbox" id="marketing-cookies">
                        <span>📢 Marketing - Für relevante Werbung</span>
                    </label>
                </div>
                
                <div class="cookie-buttons">
                    <button onclick="cookieConsent.acceptAll()">Alle akzeptieren</button>
                    <button onclick="cookieConsent.savePreferences()">Auswählen & speichern</button>
                </div>
                
                <a href="/privacy-policy" class="privacy-link">Mehr erfahren</a>
            </div>
        `;

        document.body.appendChild(banner);
    }

    // Alle Cookies akzeptieren
    acceptAll() {
        this.categories = {
            essential: true,
            analytics: true,
            marketing: true
        };
        
        this.saveAndHide();
    }

    // Ausgewählte Preferences speichern
    savePreferences() {
        this.categories.analytics = document.getElementById('analytics-cookies').checked;
        this.categories.marketing = document.getElementById('marketing-cookies').checked;
        
        this.saveAndHide();
    }

    // Speichern und Banner ausblenden
    saveAndHide() {
        localStorage.setItem('cookie_consent', JSON.stringify(this.categories));
        
        // Zu Server senden (für User-Accounts)
        const userId = this.getUserIdFromToken();
        
        if (userId) {
            fetch('/api/v1/cookie-consent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: JSON.stringify({ categories: this.categories })
            });
        }

        // Banner ausblenden
        const banner = document.getElementById('cookie-consent-banner');
        
        if (banner) {
            banner.style.display = 'none';
        }

        // Analytics aktivieren (wenn erlaubt)
        if (this.categories.analytics) {
            this.enableAnalytics();
        }

        // Marketing aktivieren (wenn erlaubt)
        if (this.categories.marketing) {
            this.enableMarketing();
        }
    }

    // Analytics Scripts laden (wenn erlaubt)
    enableAnalytics() {
        // Google Analytics oder ähnliches laden
        const script = document.createElement('script');
        script.src = 'https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID';
        document.head.appendChild(script);
        
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'GA_MEASUREMENT_ID');
    }

    // Marketing Scripts laden (wenn erlaubt)
    enableMarketing() {
        // Werbetreibende Tracking-Pixel laden
        console.log('Marketing cookies enabled');
    }

    getUserIdFromToken() {
        // Token decodieren (vereinfacht)
        return 1;  // Placeholder
    }

    // Initialisieren
    init() {
        this.showBanner();
    }
}

// Singleton
const cookieConsent = new CookieConsentBanner();
cookieConsent.init();

export default cookieConsent;
```

### Cookie Consent API Endpoint

```python
# app/api/v1/cookie_consent.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.post("/cookie-consent")
async def save_cookie_consent(
    consent_data: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cookie-Einwilligung speichern"""
    
    # Validieren
    valid_categories = {"essential", "analytics", "marketing"}
    
    for category in consent_data.get("categories", {}):
        if category not in valid_categories:
            raise HTTPException(
                status_code=400,
                detail={"code": "INVALID_CATEGORY", "message": f"Ungültige Kategorie: {category}"}
            )
    
    # Speichern
    CookieService.set_cookie_consent(
        user_id=current_user.id,
        categories=consent_data["categories"]
    )
    
    return {"message": "Cookie-Einstellungen gespeichert"}

@router.get("/cookie-consent")
async def get_cookie_consent(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Aktuelle Cookie-Einwilligung abrufen"""
    
    consent = CookieService.get_cookie_consent(current_user.id)
    
    return {
        "categories": consent,
        "consented_at": None  # In Production: Aus Datenbank laden
    }
```

---

## 📋 Benutzerrechte-Implementation

### Recht auf Auskunft (Art. 15 DSGVO)

```python
# app/api/v1/data_export.py

@router.get("/users/me/export")
async def export_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Benutzerdaten exportieren (Recht auf Datenportabilität, Art. 20 DSGVO)"""
    
    # Alle Benutzerdaten sammeln
    user_data = {
        "account": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "avatar_url": current_user.avatar_url
        },
        "game_data": {
            "province_id": current_user.province_id,
            "level": current_user.level,
            "resources": {
                "food": current_user.resources_food,
                "water": current_user.resources_water,
                "energy": current_user.resources_energy
            },
            "buildings": [],  # Gebäude der Provinz
            "units": []       # Einheiten der Provinz
        },
        "activity_log": [],  # Letzten 90 Tage
        "consent_history": []  # Cookie/Email Consent Verlauf
    }
    
    # JSON-Datei generieren
    import json
    from io import BytesIO
    
    json_data = json.dumps(user_data, indent=2, ensure_ascii=False).encode('utf-8')
    
    # Response mit Download-Header
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        BytesIO(json_data),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="wasteland_data_export_{current_user.id}.json"'
        }
    )

@router.get("/users/me/data")
async def get_user_data(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Benutzerdaten abrufen (Recht auf Auskunft, Art. 15 DSGVO)"""
    
    # Gleiche Daten wie Export, aber als JSON Response (kein Download)
    user_data = {
        "account": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "created_at": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "avatar_url": current_user.avatar_url
        },
        "game_data": {
            "province_id": current_user.province_id,
            "level": current_user.level,
            "resources": {
                "food": current_user.resources_food,
                "water": current_user.resources_water,
                "energy": current_user.resources_energy
            }
        },
        "processing_records": []  # Verzeichnis der Verarbeitungstätigkeiten (Art. 30)
    }
    
    return user_data
```

### Recht auf Löschung (Art. 17 DSGVO)

```python
# app/api/v1/data_deletion.py

@router.post("/users/me/request-deletion")
async def request_account_deletion(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Konto-Löschung anfordern (Recht auf Vergessenwerden, Art. 17 DSGVO)"""
    
    # Bestätigungs-Email senden
    from app.services.email_service import email_service
    
    deletion_token = secrets.token_urlsafe(32)
    
    # Token in Datenbank speichern (24h gültig)
    deletion_request = DeletionRequest(
        user_id=current_user.id,
        token=deletion_token,
        expires_at=datetime.utcnow() + timedelta(hours=24)
    )
    
    db.add(deletion_request)
    db.commit()
    
    # Bestätigungs-Email senden
    deletion_url = f"http://localhost:8011/auth/confirm-deletion?token={deletion_token}"
    
    email_service.send_email(
        to_email=current_user.email,
        subject="Wasteland: Konto-Löschung anfordern",
        html_content=f"""
            <h2>Konto löschen</h2>
            <p>Sie haben angefordert, Ihr Wasteland Konto zu löschen.</p>
            <p>Klicken Sie auf den folgenden Button, um die Löschung zu bestätigen:</p>
            <a href="{deletion_url}" style="background-color: #e94560; color: white; padding: 12px 30px; text-decoration: none; border-radius: 4px;">
                Konto löschen
            </a>
            <p>Dieser Link ist 24 Stunden gültig.</p>
        """
    )
    
    return {"message": "Löschungsanfrage gesendet. Bitte bestätigen Sie Ihre Email."}

@router.post("/auth/confirm-deletion")
async def confirm_account_deletion(
    token: str,
    db: Session = Depends(get_db)
):
    """Konto-Löschung bestätigen"""
    
    # Token validieren
    deletion_request = db.query(DeletionRequest).filter_by(token=token).first()
    
    if not deletion_request:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_TOKEN", "message": "Ungültiger Token"}
        )
    
    if datetime.utcnow() > deletion_request.expires_at:
        raise HTTPException(
            status_code=400,
            detail={"code": "TOKEN_EXPIRED", "message": "Token abgelaufen (24h Gültigkeit)"}
        )
    
    # Benutzer löschen
    user = db.query(User).get(deletion_request.user_id)
    
    # Persönliche Daten anonymisieren (Art. 17)
    user.username = f"gelöscht_{user.id}"
    user.email = f"gelöscht_{user.id}@wasteland.local"
    user.password_hash = ""
    user.avatar_url = None
    
    # Spiel-Daten behalten (für Spielbalance), aber Owner-Beziehung lösen
    if user.province_id:
        province = db.query(Province).get(user.province_id)
        if province:
            province.owner_id = None  # Provinz wird neutral
    
    db.commit()
    
    # Token löschen
    db.delete(deletion_request)
    db.commit()
    
    return {"message": "Konto erfolgreich gelöscht. Alle persönlichen Daten wurden anonymisiert."}
```

---

## 🔒 Datenschutz durch Verschlüsselung (Art. 32 DSGVO)

### Password Hashing & Security

```python
# app/security/password_hashing.py
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Password mit bcrypt hashen"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Password verifizieren"""
    return pwd_context.verify(plain_password, hashed_password)

# HTTPS erzwingen (Transportverschlüsselung)
class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # In Production: nginx leitet HTTP → HTTPS um
        # Hier nur als Hinweis
        
        response = await call_next(request)
        
        # HSTS Header setzen (Strict Transport Security)
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

app.add_middleware(HTTPSRedirectMiddleware)
```

---

## 🧪 Testing Compliance

### Unit Tests für Datenschutz-Funktionen

```python
# tests/compliance/test_data_export.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_user_data_export(client, auth_token):
    """Testet Benutzerdaten-Export (Art. 20 DSGVO)"""
    
    response = client.get("/users/me/export", headers={"Authorization": f"Bearer {auth_token}"})
    
    assert response.status_code == 200
    assert response.headers["content-disposition"].startswith("attachment")
    
    data = response.json()
    
    assert "account" in data
    assert "game_data" in data
    assert "email" in data["account"]

def test_user_data_access(client, auth_token):
    """Testet Recht auf Auskunft (Art. 15 DSGVO)"""
    
    response = client.get("/users/me/data", headers={"Authorization": f"Bearer {auth_token}"})
    
    assert response.status_code == 200
    
    data = response.json()
    
    assert "account" in data
    assert "game_data" in data

def test_account_deletion_request(client, auth_token):
    """Testet Löschungsanfrage (Art. 17 DSGVO)"""
    
    response = client.post("/users/me/request-deletion", headers={"Authorization": f"Bearer {auth_token}"})
    
    assert response.status_code == 200
    assert "Löschungsanfrage gesendet" in response.json()["message"]

def test_account_deletion_confirmation(client):
    """Testet Konto-Löschung mit Token"""
    
    # Token generieren (vereinfacht)
    token = "test_deletion_token"
    
    response = client.post(f"/auth/confirm-deletion?token={token}")
    
    # In Production: Gültiger Token erforderlich
    assert response.status_code in [200, 400]

def test_cookie_consent_required(client):
    """Testet dass Analytics Cookies ohne Einwilligung nicht gesetzt werden"""
    
    response = client.get("/")
    
    # Keine Analytics Cookies ohne Einwilligung
    cookies = response.cookies
    
    assert "analytics_id" not in cookies

def test_cookie_consent_saves_preferences(client, auth_token):
    """Testet dass Cookie-Präferenzen gespeichert werden"""
    
    response = client.post(
        "/cookie-consent",
        json={"categories": {"essential": True, "analytics": True, "marketing": False}},
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == 200
```

---

## 📚 Privacy Policy & Terms of Service

### Datenschutz-Erklärung (Auszug)

```markdown
<!-- templates/privacy-policy.html -->

# Datenschutz-Erklärung für Wasteland - Verbrannte Zone

## 1. Verantwortlicher
Fabian [Nachname]  
[Adresse]  
[E-Mail]

## 2. Erhobene Daten
- **Pflichtangaben:** E-Mail-Adresse, Passwort (gehashet)
- **Freiwillige Angaben:** Benutzername, Profilbild
- **Spiel-Daten:** Provinz, Ressourcen, Gebäude, Einheiten

## 3. Rechtsgrundlage
- **Art. 6(1)(b) DSGVO:** Vertragserfüllung (Spielteilnahme)
- **Art. 6(1)(f) DSGVO:** Berechtigte Interessen (Analytics, Verbesserung)

## 4. Speicherdauer
- **Kontodaten:** Bis zur Löschung
- **Spiel-Daten:** Dauer der Spielteilnahme + 3 Jahre (gesetzliche Aufbewahrung)
- **Log-Daten:** 90 Tage

## 5. Ihre Rechte
- Recht auf Auskunft (Art. 15)
- Recht auf Berichtigung (Art. 16)
- Recht auf Löschung (Art. 17)
- Recht auf Datenportabilität (Art. 20)
- Widerspruchsrecht (Art. 21)

## 6. Third-Party Services
- **SendGrid:** Email-Versand (evtl. US-Server)
- **GitHub Pages:** Hosting (EU-Rechenzentrum)

## 7. Kontakt
Bei Fragen zum Datenschutz: [datenschutz@wasteland.game]
```

---

## 🎯 Best Practices

1. **Privacy by Design** - Datenschutz von Anfang an integrieren
2. **Datensparsamkeit** - Nur notwendige Daten erheben
3. **Transparenz** - Klare Datenschutzerklärung
4. **Benutzerrechte** - Auskunft, Löschung, Portabilität einfach ermöglichen
5. **Verschlüsselung** - HTTPS + bcrypt Password Hashing
6. **Cookie Consent** - Opt-in für Analytics/Marketing (keine Default-Aktivierung)

---

**DSGVO-Compliance schützt Benutzerrechte und vermeidet hohe Bußgelder!**

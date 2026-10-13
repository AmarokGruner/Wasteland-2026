# 📧 Email System & Notifications

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung eines Email-Systems für:
- Benachrichtigungen (Spiel-Events)
- Passwort-Reset Flow
- Email-Verifikation bei Registration
- Newsletter/Announcements

---

## 🎯 Ziele

1. **Automatisierte Benachrichtigungen** - Spieler erhalten relevante Updates
2. **Sichere Passwort-Reset** - Email-basierte Verifikation
3. **Email-Verifikation** - Spam/False Accounts verhindern
4. **Template System** - Mehrsprachige, gestaltete Emails

---

## 🏗️ Email Service Architecture

### Komponenten

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI    │────▶│  Email Queue  │────▶│ SMTP Server  │
│   Backend    │     │ (Celery/RQ)   │     │ (SendGrid,   │
│              │     │               │     │  Mailgun)    │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │ Email Template│
                    │   Engine      │
                    └──────────────┘
```

---

## 🔧 Installation & Configuration

### Dependencies

```bash
pip install sendgrid jinja2 python-dotenv celery redis
# Oder alternativ:
# pip install mailgun-python
# pip install aiosmtplib
```

### Email Configuration

```python
# app/config.py

class EmailConfig:
    # SendGrid (empfohlen für Production)
    SENDGRID_API_KEY = "SG.xxxxxxxxxxxxxxxx"
    SENDGRID_FROM_EMAIL = "noreply@wasteland.game"
    SENDGRID_FROM_NAME = "Wasteland - Verbrannte Zone"
    
    # Alternativ: Eigener SMTP Server
    SMTP_HOST = "smtp.example.com"
    SMTP_PORT = 587
    SMTP_USER = "wasteland@example.com"
    SMTP_PASSWORD = "your_smtp_password"
    SMTP_USE_TLS = True
    
    # Email Templates Verzeichnis
    TEMPLATES_DIR = "app/email/templates"

email_config = EmailConfig()
```

---

## 📝 Email Template Engine (Jinja2)

### Template Struktur

```
app/email/templates/
├── base.html              # Basis-Layout (HTML + Inline CSS)
├── verification.html      # Email-Verifikation
├── password_reset.html    # Passwort-Reset
├── notification_game.html # Spiel-Benachrichtigungen
├── announcement.html      # Ankündigungen/Newsletter
└── css/
    └── styles.css         # Email-spezifisches CSS (Inline konvertiert)
```

### Base Template (HTML + Inline CSS für Email Clients)

```html
<!-- app/email/templates/base.html -->
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #1a1a2e;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #1a1a2e;">
        <tr>
            <td align="center" style="padding: 20px;">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #16213e; border-radius: 8px; overflow: hidden;">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background-color: #0f3460; padding: 30px; text-align: center;">
                            <h1 style="color: #e94560; margin: 0; font-size: 28px;">Wasteland</h1>
                            <p style="color: #a0a0a0; margin: 5px 0 0 0; font-size: 14px;">Verbrannte Zone</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 30px; color: #ffffff;">
                            {{ content }}
                        </td>
                    </tr>
                    
                    <!-- CTA Button -->
                    {% if button_text and button_url %}
                    <tr>
                        <td style="padding: 0 30px 30px 30px; text-align: center;">
                            <a href="{{ button_url }}" 
                               style="background-color: #e94560; color: #ffffff; padding: 12px 30px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">
                                {{ button_text }}
                            </a>
                        </td>
                    </tr>
                    {% endif %}
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #0a192f; padding: 20px; text-align: center; color: #666666; font-size: 12px;">
                            <p style="margin: 0 0 10px 0;">Sie erhalten diese Email, weil Sie ein Wasteland Konto haben.</p>
                            <p style="margin: 0;">© 2026 Wasteland - Verbrannte Zone</p>
                            <p style="margin: 10px 0 0 0;">
                                <a href="{{ unsubscribe_url }}" style="color: #666666;">Abmelden</a>
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
```

### Verification Email Template

```html
<!-- app/email/templates/verification.html -->
{% extends "base.html" %}

{% block content %}
<h2 style="color: #e94560; margin-top: 0;">Email verifizieren</h2>

<p style="font-size: 16px; line-height: 1.6;">
    Willkommen bei Wasteland! Bitte verifizieren Sie Ihre Email-Adresse, um Ihr Konto zu aktivieren.
</p>

<p style="font-size: 14px; color: #a0a0a0;">
    Klicken Sie auf den folgenden Button, um Ihre Email zu verifizieren:
</p>

<p style="text-align: center; margin: 30px 0;">
    <a href="{{ verification_url }}" 
       style="background-color: #e94560; color: #ffffff; padding: 14px 40px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 16px;">
       Email verifizieren
    </a>
</p>

<p style="font-size: 12px; color: #666666;">
    Dieser Link ist 24 Stunden gültig. Wenn Sie dieses Konto nicht erstellt haben, ignorieren Sie diese Email.
</p>

{% endblock %}
```

### Password Reset Template

```html
<!-- app/email/templates/password_reset.html -->
{% extends "base.html" %}

{% block content %}
<h2 style="color: #e94560; margin-top: 0;">Passwort zurücksetzen</h2>

<p style="font-size: 16px; line-height: 1.6;">
    Jemand hat angefordert, das Passwort für Ihr Wasteland Konto zurückzusetzen.
</p>

{% if requested %}
<p style="font-size: 14px; color: #a0a0a0;">
    Klicken Sie auf den folgenden Button, um ein neues Passwort festzulegen:
</p>

<p style="text-align: center; margin: 30px 0;">
    <a href="{{ reset_url }}" 
       style="background-color: #e94560; color: #ffffff; padding: 14px 40px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold; font-size: 16px;">
       Passwort zurücksetzen
    </a>
</p>
{% else %}
<p style="font-size: 14px; color: #a0a0a0;">
    Wenn Sie kein Passwort-Reset angefordert haben, ignorieren Sie diese Email. Ihr Passwort bleibt unverändert.
</p>
{% endif %}

<p style="font-size: 12px; color: #666666;">
    Dieser Link ist 1 Stunde gültig.
</p>

{% endblock %}
```

---

## 🔧 Email Service Implementation

### SendGrid Integration

```python
# app/services/email_service.py
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from jinja2 import Environment, FileSystemLoader
import secrets
from datetime import datetime, timedelta

class EmailService:
    def __init__(self):
        self.sendgrid = SendGridAPIClient(os.getenv("SENDGRID_API_KEY"))
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@wasteland.game")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "Wasteland - Verbrannte Zone")
        
        # Jinja2 Environment für Templates
        self.jinja_env = Environment(
            loader=FileSystemLoader("app/email/templates")
        )
    
    def render_template(self, template_name: str, context: dict) -> str:
        """HTML Template rendern"""
        template = self.jinja_env.get_template(template_name)
        return template.render(**context)
    
    def send_email(self, to_email: str, subject: str, html_content: str):
        """Email über SendGrid senden"""
        message = Mail(
            from_email=self.from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )
        
        try:
            response = self.sendgrid.send(message)
            
            if response.status_code >= 200 and response.status_code < 300:
                return {"success": True, "message": "Email gesendet"}
            else:
                return {"success": False, "error": f"SendGrid Error: {response.status_code}"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def send_verification_email(self, to_email: str, user_id: int):
        """Verifikations-Email senden"""
        
        # Token generieren (24h gültig)
        token = secrets.token_urlsafe(32)
        
        # Token in Datenbank speichern (mit expiry)
        from app.models import EmailVerificationToken
        verification_token = EmailVerificationToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        # In Datenbank speichern (vereinfacht)
        # db.add(verification_token)
        # db.commit()
        
        # URL für Verifikation
        verification_url = f"http://localhost:8011/auth/verify-email?token={token}"
        
        # Template rendern
        html_content = self.render_template("verification.html", {
            "title": "Email verifizieren",
            "content": "",  # Content kommt aus Template
            "verification_url": verification_url,
            "unsubscribe_url": f"http://localhost:8011/unsubscribe?email={to_email}"
        })
        
        # Email senden
        return self.send_email(
            to_email=to_email,
            subject="Wasteland: Email verifizieren",
            html_content=html_content
        )
    
    def send_password_reset_email(self, to_email: str, user_id: int):
        """Passwort-Reset Email senden"""
        
        # Token generieren (1h gültig)
        token = secrets.token_urlsafe(32)
        
        # Token in Datenbank speichern
        from app.models import PasswordResetToken
        reset_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        
        # In Datenbank speichern (vereinfacht)
        # db.add(reset_token)
        # db.commit()
        
        # URL für Reset
        reset_url = f"http://localhost:8011/auth/reset-password?token={token}"
        
        # Template rendern
        html_content = self.render_template("password_reset.html", {
            "title": "Passwort zurücksetzen",
            "content": "",
            "reset_url": reset_url,
            "unsubscribe_url": f"http://localhost:8011/unsubscribe?email={to_email}"
        })
        
        # Email senden
        return self.send_email(
            to_email=to_email,
            subject="Wasteland: Passwort zurücksetzen",
            html_content=html_content
        )
    
    def send_game_notification(self, to_email: str, notification_data: dict):
        """Spiel-Benachrichtigung senden"""
        
        html_content = self.render_template("notification_game.html", {
            "title": "Spiel-Benachrichtigung",
            "content": notification_data.get("message"),
            "button_text": notification_data.get("button_text", "Zum Spiel"),
            "button_url": notification_data.get("button_url", "/dashboard")
        })
        
        return self.send_email(
            to_email=to_email,
            subject=f"Wasteland: {notification_data.get('title', 'Neues Event')}",
            html_content=html_content
        )

# Singleton Instance
email_service = EmailService()
```

---

## 📡 API Endpoints für Email-Funktionen

### Email Verification Endpoint

```python
# app/api/v1/auth_email_verification.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/auth/send-verification")
async def send_verification_email(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifikations-Email senden"""
    
    # Prüfen ob Email bereits verifiziert
    if current_user.email_verified:
        raise HTTPException(
            status_code=400,
            detail={"code": "EMAIL_ALREADY_VERIFIED", "message": "Email bereits verifiziert"}
        )
    
    # Email senden
    result = email_service.send_verification_email(
        to_email=current_user.email,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail={"code": "EMAIL_SEND_FAILED", "message": result["error"]}
        )
    
    return {"message": "Verifikations-Email gesendet"}

@router.get("/auth/verify-email")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Email verifizieren"""
    
    # Token suchen
    verification_token = db.query(EmailVerificationToken).filter_by(token=token).first()
    
    if not verification_token:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_TOKEN", "message": "Ungültiger Verifikationstoken"}
        )
    
    # Token abgelaufen?
    if datetime.utcnow() > verification_token.expires_at:
        raise HTTPException(
            status_code=400,
            detail={"code": "TOKEN_EXPIRED", "message": "Token abgelaufen (24h Gültigkeit)"}
        )
    
    # User verifizieren
    user = db.query(User).get(verification_token.user_id)
    user.email_verified = True
    db.commit()
    
    # Token löschen (einmalige Verwendung)
    db.delete(verification_token)
    db.commit()
    
    return {"message": "Email erfolgreich verifiziert"}

@router.post("/auth/resend-verification")
async def resend_verification_email(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Verifikations-Email erneut senden"""
    
    # Prüfen ob Email bereits verifiziert
    if current_user.email_verified:
        raise HTTPException(
            status_code=400,
            detail={"code": "EMAIL_ALREADY_VERIFIED", "message": "Email bereits verifiziert"}
        )
    
    # Rate Limiting: Max 3 Versuche pro Stunde
    last_sent = db.query(EmailVerificationToken).filter_by(
        user_id=current_user.id,
        type="verification"
    ).order_by(EmailVerificationToken.created_at.desc()).first()
    
    if last_sent and datetime.utcnow() - last_sent.created_at < timedelta(hours=1):
        remaining_minutes = 60 - int((datetime.utcnow() - last_sent.created_at).seconds / 60)
        raise HTTPException(
            status_code=429,
            detail={
                "code": "RATE_LIMITED",
                "message": f"Bitte warten Sie noch {remaining_minutes} Minuten"
            }
        )
    
    # Email erneut senden
    result = email_service.send_verification_email(
        to_email=current_user.email,
        user_id=current_user.id
    )
    
    if not result["success"]:
        raise HTTPException(
            status_code=500,
            detail={"code": "EMAIL_SEND_FAILED", "message": result["error"]}
        )
    
    return {"message": "Verifikations-Email erneut gesendet"}
```

### Password Reset Endpoints

```python
# app/api/v1/auth_password_reset.py
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter()

@router.post("/auth/forgot-password")
async def forgot_password(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    """Passwort-Reset Email senden"""
    
    # Benutzer suchen
    user = db.query(User).filter_by(email=email).first()
    
    # Security: Auch wenn User nicht existiert, erfolgreiche Message zurückgeben
    # (verhindert Email-Enumeration)
    if user:
        result = email_service.send_password_reset_email(
            to_email=user.email,
            user_id=user.id
        )
        
        if not result["success"]:
            logger.error(f"Password reset email failed for {email}: {result['error']}")
    
    # Immer gleiche Message zurückgeben (Security)
    return {"message": "Wenn ein Konto mit dieser Email existiert, wurde eine Reset-Email gesendet"}

@router.get("/auth/reset-password")
async def show_reset_password_form(
    token: str,
    request: Request
):
    """Passwort-Reset Formular anzeigen"""
    
    # Token validieren (vereinfacht - in Production: Template rendern)
    reset_token = db.query(PasswordResetToken).filter_by(token=token).first()
    
    if not reset_token or datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_OR_EXPIRED_TOKEN", "message": "Ungültiger oder abgelaufener Token"}
        )
    
    # Template rendern und zurückgeben (vereinfacht)
    return {"token": token}  # In Production: HTML Template zurückgeben

@router.post("/auth/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """Passwort zurücksetzen"""
    
    # Token validieren
    reset_token = db.query(PasswordResetToken).filter_by(token=token).first()
    
    if not reset_token:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_TOKEN", "message": "Ungültiger Token"}
        )
    
    if datetime.utcnow() > reset_token.expires_at:
        raise HTTPException(
            status_code=400,
            detail={"code": "TOKEN_EXPIRED", "message": "Token abgelaufen (1h Gültigkeit)"}
        )
    
    # Password validieren (mindestens 8 Zeichen, komplex)
    if len(new_password) < 8:
        raise HTTPException(
            status_code=400,
            detail={"code": "PASSWORD_TOO_SHORT", "message": "Passwort muss mindestens 8 Zeichen lang sein"}
        )
    
    # User finden und Password aktualisieren
    user = db.query(User).get(reset_token.user_id)
    user.password_hash = hash_password(new_password)  # bcrypt
    db.commit()
    
    # Token löschen (einmalige Verwendung)
    db.delete(reset_token)
    db.commit()
    
    return {"message": "Passwort erfolgreich zurückgesetzt"}
```

---

## 🧪 Testing Email Service

### Unit Tests

```python
# tests/services/test_email_service.py
import pytest
from app.services.email_service import EmailService

@pytest.fixture
def email_service():
    return EmailService()

def test_render_verification_template(email_service):
    """Testet Rendering der Verifikations-Email"""
    html = email_service.render_template("verification.html", {
        "title": "Email verifizieren",
        "content": "",
        "verification_url": "http://localhost:8011/auth/verify?token=abc123"
    })
    
    assert "Email verifizieren" in html
    assert "abc123" in html

def test_render_password_reset_template(email_service):
    """Testet Rendering der Passwort-Reset Email"""
    html = email_service.render_template("password_reset.html", {
        "title": "Passwort zurücksetzen",
        "content": "",
        "reset_url": "http://localhost:8011/auth/reset?token=xyz789"
    })
    
    assert "Passwort zurücksetzen" in html
    assert "xyz789" in html

def test_send_email_mock(email_service, mocker):
    """Testet Email Versand (mocked SendGrid)"""
    mock_response = mocker.Mock()
    mock_response.status_code = 202
    
    mock_sendgrid = mocker.Mock()
    mock_sendgrid.send = mocker.Mock(return_value=mock_response)
    
    email_service.sendgrid = mock_sendgrid
    
    result = email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>"
    )
    
    assert result["success"] is True

def test_send_email_failure(email_service, mocker):
    """Testet Email Versand bei Fehler"""
    mock_sendgrid = mocker.Mock()
    mock_sendgrid.send = mocker.Mock(side_effect=Exception("SMTP Error"))
    
    email_service.sendgrid = mock_sendgrid
    
    result = email_service.send_email(
        to_email="test@example.com",
        subject="Test",
        html_content="<p>Test</p>"
    )
    
    assert result["success"] is False
    assert "SMTP Error" in result["error"]
```

---

## 📊 Email Queue mit Celery (Async)

### Celery Configuration

```python
# app/tasks/email_tasks.py
from celery import Celery
import os

celery_app = Celery(
    "wasteland_email",
    broker=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://localhost:6379/0")
)

@celery_app.task(bind=True, max_retries=3)
def send_verification_email_task(self, to_email: str, user_id: int):
    """Verifikations-Email asynchron senden"""
    try:
        return email_service.send_verification_email(to_email, user_id)
    except Exception as exc:
        # Retry mit exponentiellem Backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task(bind=True, max_retries=3)
def send_password_reset_email_task(self, to_email: str, user_id: int):
    """Passwort-Reset Email asynchron senden"""
    try:
        return email_service.send_password_reset_email(to_email, user_id)
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def send_game_notification_task(to_email: str, notification_data: dict):
    """Spiel-Benachrichtigung asynchron senden"""
    return email_service.send_game_notification(to_email, notification_data)
```

### Celery Worker Starten

```bash
# Celery Worker starten (Terminal 1)
celery -A app.tasks.email_tasks worker --loglevel=info

# Celery Beat für Scheduled Tasks (Terminal 2)
celery -A app.tasks.email_tasks beat --loglevel=info
```

---

## 🎯 Best Practices

1. **Email Templates HTML + Inline CSS** - Für Email Client Kompatibilität
2. **Async Queue (Celery)** - Emails nicht im Request Thread senden
3. **Rate Limiting** - Max 3 Verifikations-Versuche pro Stunde
4. **Security: Email Enumeration verhindern** - Immer gleiche Message zurückgeben
5. **Token Expiry** - Verifikations-Tokens 24h, Reset-Tokens 1h
6. **Unsubscribe Link** - DSGVO-konform (Opt-out ermöglichen)

---

**Email System ermöglicht Benachrichtigungen, sichere Passwort-Reset und Email-Verifikation!**

# 🔐 OAuth2 & Third-party Authentication

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung von OAuth2/OpenID Connect für Social Logins (Google, GitHub, Discord) und Third-party Authentication.

---

## 🎯 Ziele

1. **Benutzerfreundlichkeit** - Kein neues Passwort merken
2. **Sicherheit** - OAuth2 Standard verwenden (kein Password Storage)
3. **Multi-Provider Support** - Google, GitHub, Discord, etc.
4. **Account Linking** - Bestehende Accounts mit Social Logins verknüpfen

---

## 🏗️ OAuth2 Flow (Authorization Code)

### Standard Flow Diagramm

```
Client → Authorization Server (Google/GitHub)
         ↓ (User autorisiert)
Client ← Authorization Code
         ↓
Client → Token Exchange (Code → Access Token)
         ↓
Client ← Access Token + Refresh Token
         ↓
Client → User Info (mit Access Token)
```

---

## 🔧 Implementation in FastAPI

### Installation

```bash
pip install authlib fastapi-oauth2 python-jose[cryptography]
```

### OAuth2 Configuration

```python
# app/config.py

class OAuth2Config:
    # Google OAuth2
    GOOGLE_CLIENT_ID = "YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET = "YOUR_GOOGLE_CLIENT_SECRET"
    GOOGLE_REDIRECT_URI = "http://localhost:8011/auth/google/callback"
    GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
    GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
    GOOGLE_USER_INFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
    
    # GitHub OAuth2
    GITHUB_CLIENT_ID = "YOUR_GITHUB_CLIENT_ID"
    GITHUB_CLIENT_SECRET = "YOUR_GITHUB_CLIENT_SECRET"
    GITHUB_REDIRECT_URI = "http://localhost:8011/auth/github/callback"
    GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
    GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
    GITHUB_USER_INFO_URL = "https://api.github.com/user"
    
    # Discord OAuth2
    DISCORD_CLIENT_ID = "YOUR_DISCORD_CLIENT_ID"
    DISCORD_CLIENT_SECRET = "YOUR_DISCORD_CLIENT_SECRET"
    DISCORD_REDIRECT_URI = "http://localhost:8011/auth/discord/callback"
    DISCORD_AUTH_URL = "https://discord.com/api/oauth2/authorize"
    DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
    DISCORD_USER_INFO_URL = "https://discord.com/api/users/@me"

oauth_config = OAuth2Config()
```

### Google OAuth2 Router

```python
# app/api/v1/auth_google.py
from fastapi import APIRouter, Depends, HTTPException, Request
from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session
import httpx

router = APIRouter()
oauth = OAuth()

# Google konfigurieren
oauth.register(
    name="google",
    client_id=oauth_config.GOOGLE_CLIENT_ID,
    client_secret=oauth_config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"}
)

@router.get("/auth/google")
async def google_login(request: Request):
    """Google Login starten"""
    redirect_uri = request.url_for("google_auth_callback")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@router.get("/auth/google/callback")
async def google_auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Google Callback verarbeiten"""
    try:
        # Token exchange
        token = await oauth.google.authorize_access_token(request)
        
        # User Info abrufen
        user_info = token.get("userinfo")
        
        if not user_info:
            raise HTTPException(
                status_code=400,
                detail={"code": "GOOGLE_USER_INFO_FAILED", "message": "Konnte Benutzerinformationen nicht abrufen"}
            )
        
        email = user_info.get("email")
        if not email:
            raise HTTPException(
                status_code=400,
                detail={"code": "NO_EMAIL", "message": "Google hat keine E-Mail freigegeben"}
            )
        
        # Benutzer in Datenbank suchen oder erstellen
        user = db.query(User).filter_by(email=email).first()
        
        if not user:
            # Neuen Benutzer erstellen
            user = User(
                email=email,
                username=user_info.get("name", email.split("@")[0]),
                profile_picture=user_info.get("picture"),
                provider="google",
                provider_user_id=user_info.get("id")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Bestehenden User aktualisieren (falls Provider geändert)
            if user.provider != "google":
                # Account Linking: Bestehenden Account mit Google verknüpfen
                user.provider = "google"
                user.provider_user_id = user_info.get("id")
                user.profile_picture = user_info.get("picture")
                db.commit()
        
        # JWT Token generieren
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "provider": "google"
            }
        }
    
    except Exception as e:
        logger.error(f"Google OAuth Error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "GOOGLE_OAUTH_ERROR", "message": "Google Login fehlgeschlagen"}
        )
```

### GitHub OAuth2 Router

```python
# app/api/v1/auth_github.py
from fastapi import APIRouter, Depends, HTTPException, Request
from authlib.integrations.starlette_client import OAuth

router = APIRouter()
oauth = OAuth()

# GitHub konfigurieren
oauth.register(
    name="github",
    client_id=oauth_config.GITHUB_CLIENT_ID,
    client_secret=oauth_config.GITHUB_CLIENT_SECRET,
    access_token_url=oauth_config.GITHUB_TOKEN_URL,
    authorize_url=oauth_config.GITHUB_AUTH_URL,
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"}
)

@router.get("/auth/github")
async def github_login(request: Request):
    """GitHub Login starten"""
    redirect_uri = request.url_for("github_auth_callback")
    return await oauth.github.authorize_redirect(request, redirect_uri)

@router.get("/auth/github/callback")
async def github_auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """GitHub Callback verarbeiten"""
    try:
        token = await oauth.github.authorize_access_token(request)
        
        # User Info abrufen
        resp = await oauth.github.get("user", token=token)
        user_info = resp.json()
        
        # Primary Email abrufen (GitHub API special case)
        email_resp = await oauth.github.get("user/emails", token=token)
        emails = email_resp.json()
        primary_email = next((e["email"] for e in emails if e.get("primary")), None)
        
        if not primary_email:
            raise HTTPException(
                status_code=400,
                detail={"code": "NO_EMAIL", "message": "GitHub hat keine E-Mail freigegeben"}
            )
        
        # Benutzer suchen oder erstellen
        user = db.query(User).filter_by(email=primary_email).first()
        
        if not user:
            user = User(
                email=primary_email,
                username=user_info.get("login"),
                profile_picture=user_info.get("avatar_url"),
                provider="github",
                provider_user_id=str(user_info.get("id"))
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # JWT Token generieren
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "provider": "github"
            }
        }
    
    except Exception as e:
        logger.error(f"GitHub OAuth Error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "GITHUB_OAUTH_ERROR", "message": "GitHub Login fehlgeschlagen"}
        )
```

### Discord OAuth2 Router

```python
# app/api/v1/auth_discord.py
from fastapi import APIRouter, Depends, HTTPException, Request

router = APIRouter()
oauth = OAuth()

# Discord konfigurieren
oauth.register(
    name="discord",
    client_id=oauth_config.DISCORD_CLIENT_ID,
    client_secret=oauth_config.DISCORD_CLIENT_SECRET,
    access_token_url=oauth_config.DISCORD_TOKEN_URL,
    authorize_url=oauth_config.DISCORD_AUTH_URL,
    api_base_url="https://discord.com/api/",
    client_kwargs={"scope": "identify email"}
)

@router.get("/auth/discord")
async def discord_login(request: Request):
    """Discord Login starten"""
    redirect_uri = request.url_for("discord_auth_callback")
    return await oauth.discord.authorize_redirect(request, redirect_uri)

@router.get("/auth/discord/callback")
async def discord_auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Discord Callback verarbeiten"""
    try:
        token = await oauth.discord.authorize_access_token(request)
        
        # User Info abrufen
        resp = await oauth.discord.get("users/@me", token=token)
        user_info = resp.json()
        
        # Email über User Object (Discord sendet Email im User Object)
        email = user_info.get("email")
        
        if not email:
            raise HTTPException(
                status_code=400,
                detail={"code": "NO_EMAIL", "message": "Discord hat keine E-Mail freigegeben"}
            )
        
        # Benutzer suchen oder erstellen
        user = db.query(User).filter_by(email=email).first()
        
        if not user:
            # Discord Username mit Discriminator (z.B. User#1234)
            username = f"{user_info.get('username')}#{user_info.get('discriminator')}"
            
            user = User(
                email=email,
                username=username,
                profile_picture=f"https://cdn.discordapp.com/avatars/{user_info.get('id')}/{user_info.get('avatar')}.png" if user_info.get("avatar") else None,
                provider="discord",
                provider_user_id=str(user_info.get("id"))
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # JWT Token generieren
        access_token = create_access_token(data={"sub": str(user.id)})
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "provider": "discord"
            }
        }
    
    except Exception as e:
        logger.error(f"Discord OAuth Error: {e}")
        raise HTTPException(
            status_code=500,
            detail={"code": "DISCORD_OAUTH_ERROR", "message": "Discord Login fehlgeschlagen"}
        )
```

---

## 📝 Client-Side Implementation (JavaScript)

### OAuth Login Button Component

```javascript
// js/components/oauth-login.js

class OAuthLogin {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Google Login starten
    async loginWithGoogle() {
        window.location.href = `${this.baseUrl}/auth/google`;
    }

    // GitHub Login starten
    async loginWithGitHub() {
        window.location.href = `${this.baseUrl}/auth/github`;
    }

    // Discord Login starten
    async loginWithDiscord() {
        window.location.href = `${this.baseUrl}/auth/discord`;
    }

    // OAuth Response vom Server verarbeiten (nach Callback)
    async handleOAuthResponse() {
        const params = new URLSearchParams(window.location.search);
        const code = params.get('code');
        
        if (code) {
            // Token exchange mit Backend
            const response = await fetch(`${this.baseUrl}/auth/token-exchange`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ code })
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Token im localStorage speichern
                localStorage.setItem('access_token', data.access_token);
                localStorage.setItem('user', JSON.stringify(data.user));
                
                // Zur Dashboard weiterleiten
                window.location.href = '/dashboard';
            } else {
                console.error('OAuth Error:', await response.json());
            }
        }
    }

    // Logout (Token invalidieren)
    async logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
    }

    // Login Status prüfen
    isAuthenticated() {
        return !!localStorage.getItem('access_token');
    }

    getCurrentUser() {
        const userStr = localStorage.getItem('user');
        return userStr ? JSON.parse(userStr) : null;
    }
}

const oauthLogin = new OAuthLogin();

export default oauthLogin;
```

### HTML Login Page

```html
<!-- templates/login.html -->
<!DOCTYPE html>
<html lang="de">
<head>
    <meta charset="UTF-8">
    <title>Wasteland - Login</title>
    <link rel="stylesheet" href="/css/login.css">
</head>
<body>
    <div class="login-container">
        <h1>Wasteland - Verbrannte Zone</h1>
        
        <!-- Email/Password Login -->
        <form id="email-login-form" class="login-form">
            <h2>Mit E-Mail anmelden</h2>
            <input type="email" name="email" placeholder="E-Mail" required>
            <input type="password" name="password" placeholder="Passwort" required>
            <button type="submit">Einloggen</button>
        </form>

        <!-- Oder Social Login -->
        <div class="divider">oder</div>

        <!-- Social Login Buttons -->
        <div class="social-login">
            <button onclick="oauthLogin.loginWithGoogle()" class="btn-google">
                <img src="/icons/google.svg" alt="Google">
                Mit Google anmelden
            </button>

            <button onclick="oauthLogin.loginWithGitHub()" class="btn-github">
                <img src="/icons/github.svg" alt="GitHub">
                Mit GitHub anmelden
            </button>

            <button onclick="oauthLogin.loginWithDiscord()" class="btn-discord">
                <img src="/icons/discord.svg" alt="Discord">
                Mit Discord anmelden
            </button>
        </div>

        <p class="register-link">
            Noch kein Konto? <a href="/register">Registrieren</a>
        </p>
    </div>

    <script src="/js/oauth-login.js"></script>
    <script>
        // OAuth Callback verarbeiten (wenn nach Redirect)
        if (new URLSearchParams(window.location.search).has('code')) {
            oauthLogin.handleOAuthResponse();
        }

        // Email Login Formular
        document.getElementById('email-login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(e.target);
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email: formData.get('email'),
                    password: formData.get('password')
                })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                window.location.href = '/dashboard';
            } else {
                alert('Login fehlgeschlagen!');
            }
        });
    </script>
</body>
</html>
```

---

## 📊 OAuth2 Scopes pro Provider

### Google Scopes
| Scope | Beschreibung | Erforderlich? |
|-------|--------------|---------------|
| `openid` | OpenID Connect (Essenziell) | ✅ Ja |
| `email` | E-Mail Adresse | ✅ Ja |
| `profile` | Profilinformationen (Name, Bild) | ✅ Ja |

### GitHub Scopes
| Scope | Beschreibung | Erforderlich? |
|-------|--------------|---------------|
| `user:email` | Primäre E-Mail Adresse | ✅ Ja |

### Discord Scopes
| Scope | Beschreibung | Erforderlich? |
|-------|--------------|---------------|
| `identify` | Benutzer-ID und Username | ✅ Ja |
| `email` | E-Mail Adresse | ✅ Ja |

---

## 🧪 Testing OAuth2

### Unit Tests für OAuth Endpoints

```python
# tests/api/test_oauth.py
import pytest
from fastapi.testclient import TestClient

@pytest.fixture
def client():
    from app.main import app
    return TestClient(app)

def test_google_login_redirect(client):
    """Testet dass Google Login zu Authorization URL weiterleitet"""
    response = client.get("/auth/google", follow_redirects=False)
    
    assert response.status_code == 307  # Temporary Redirect
    assert "accounts.google.com" in response.headers["location"]

def test_github_login_redirect(client):
    """Testet dass GitHub Login zu Authorization URL weiterleitet"""
    response = client.get("/auth/github", follow_redirects=False)
    
    assert response.status_code == 307
    assert "github.com/login/oauth/authorize" in response.headers["location"]

def test_discord_login_redirect(client):
    """Testet dass Discord Login zu Authorization URL weiterleitet"""
    response = client.get("/auth/discord", follow_redirects=False)
    
    assert response.status_code == 307
    assert "discord.com/api/oauth2/authorize" in response.headers["location"]

def test_oauth_callback_without_code(client):
    """Testet Callback ohne Authorization Code"""
    response = client.get("/auth/google/callback")
    
    # Sollte Fehler zurückgeben (kein Code)
    assert response.status_code in [400, 500]

def test_oauth_callback_with_invalid_token(client):
    """Testet Callback mit ungültigem Token"""
    # Simuliere ungültigen Token im OAuth Flow
    # In Production: Mock oauth.google.authorize_access_token
    pass
```

---

## 🔐 Security Best Practices

### 1. State Parameter (CSRF Protection)

```python
# app/api/v1/auth_google.py - Erweitert mit State Parameter

import secrets

@router.get("/auth/google")
async def google_login(request: Request):
    """Google Login mit State Parameter"""
    
    # CSRF Protection: Zufälligen State generieren
    state = secrets.token_urlsafe(32)
    
    # State im Session speichern
    request.session["oauth_state"] = state
    
    redirect_uri = request.url_for("google_auth_callback")
    
    # State zu Authorization URL hinzufügen
    auth_url = f"{oauth_config.GOOGLE_AUTH_URL}?client_id={oauth_config.GOOGLE_CLIENT_ID}&redirect_uri={redirect_uri}&response_type=code&scope=openid+email+profile&state={state}"
    
    return RedirectResponse(auth_url)

@router.get("/auth/google/callback")
async def google_auth_callback(request: Request):
    """Google Callback mit State Validation"""
    
    # State Parameter validieren (CSRF Schutz)
    provided_state = request.query_params.get("state")
    stored_state = request.session.get("oauth_state")
    
    if not provided_state or provided_state != stored_state:
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_STATE", "message": "Ungültiger State Parameter (möglicher CSRF Angriff)"}
        )
    
    # Normaler OAuth Flow...
```

### 2. Token Storage (HttpOnly Cookies)

```python
# app/middleware/token_cookie.py
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

class TokenCookieMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # JWT Token in HttpOnly Cookie setzen (statt localStorage)
        if response.status_code == 200 and "access_token" in str(response.body):
            # Token aus Response extrahieren (vereinfacht)
            token = self.extract_token_from_response(response)
            
            if token:
                response.set_cookie(
                    key="access_token",
                    value=token,
                    httponly=True,  # Nicht über JavaScript zugänglich
                    secure=True,    # Nur HTTPS
                    samesite="lax",  # CSRF Schutz
                    max_age=86400    # 24 Stunden
                )
        
        return response

app.add_middleware(TokenCookieMiddleware)
```

---

## 📚 Provider Registration (Admin Panel)

### Admin OAuth2 Provider Management

```python
# app/api/v1/admin_oauth_providers.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/admin/oauth-providers")
async def list_oauth_providers(db: Session = Depends(get_db)):
    """Listet alle konfigurierten OAuth2 Provider"""
    providers = db.query(OAuthProvider).all()
    
    return [
        {
            "id": p.id,
            "name": p.name,  # z.B. "Google", "GitHub"
            "client_id": p.client_id[:10] + "..." if p.client_id else None,  # Maskiert
            "enabled": p.enabled,
            "scopes": p.scopes.split(",") if p.scopes else []
        }
        for p in providers
    ]

@router.post("/admin/oauth-providers")
async def create_oauth_provider(
    provider_data: OAuthProviderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Neuen OAuth2 Provider konfigurieren"""
    
    provider = OAuthProvider(
        name=provider_data.name,
        client_id=provider_data.client_id,
        client_secret=provider_data.client_secret,  # Verschlüsselt speichern!
        auth_url=provider_data.auth_url,
        token_url=provider_data.token_url,
        user_info_url=provider_data.user_info_url,
        scopes=provider_data.scopes,
        enabled=True
    )
    
    db.add(provider)
    db.commit()
    
    return {"message": f"Provider '{provider_data.name}' erfolgreich konfiguriert"}
```

---

## 🎯 Best Practices

1. **State Parameter immer verwenden** - CSRF Protection
2. **Tokens in HttpOnly Cookies speichern** - XSS Schutz
3. **HTTPS erzwingen** - Secure Flag für Cookies
4. **Scopes minimal halten** - Nur notwendige Informationen anfordern
5. **Account Linking unterstützen** - Bestehende Accounts verknüpfen
6. **Fallback auf Email/Password** - Wenn OAuth fehlschlägt

---

**OAuth2 & Third-party Authentication ermöglicht benutzerfreundliches Login ohne Password-Speicherung!**

# 🌍 Internationalization (i18n) & Localization

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung von Internationalisierung (i18n) und Lokalisierung (l10n) für:
- Mehrsprachige Benutzeroberfläche
- API Response Übersetzungen
- Dynamische Sprachumschaltung

---

## 🎯 Ziele

1. **Mehrsprachige UI** - Deutsch, Englisch, Französisch, Spanisch
2. **Sprachumschaltung zur Laufzeit** - Ohne Neustart
3. **API locale Parameter** - Übersetzte Fehlermeldungen und Daten
4. **Fallback-System** - Englischer Fallback bei fehlenden Übersetzungen

---

## 🏗️ i18n Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   FastAPI    │────▶│  Translation  │────▶│  JSON Files  │
│   Backend    │     │   Service     │     │ (locales/)   │
│              │     │               │     │              │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                    ┌───────┴───────┐
                    │  Browser       │
                    │  Accept-Language│
                    └───────────────┘
```

---

## 🔧 Installation & Configuration

### Dependencies

```bash
pip install babel pytz
```

### Supported Languages

```python
# app/config.py

class I18nConfig:
    # Unterstützte Sprachen
    SUPPORTED_LANGUAGES = {
        "de": {"name": "Deutsch", "native_name": "Deutsch"},
        "en": {"name": "English", "native_name": "English"},
        "fr": {"name": "Français", "native_name": "Français"},
        "es": {"name": "Español", "native_name": "Español"},
    }
    
    # Standardsprache (Fallback)
    DEFAULT_LANGUAGE = "de"
    
    # Locale Verzeichnis
    LOCALES_DIR = "app/locales"

i18n_config = I18nConfig()
```

---

## 📁 Translation File Structure

### Verzeichnisstruktur

```
app/locales/
├── de/
│   ├── common.json          # Allgemeine Übersetzungen
│   ├── game.json            # Spiel-Begriffe
│   ├── buildings.json       # Gebäude-Übersetzungen
│   ├── resources.json       # Ressourcen-Übersetzungen
│   └── errors.json          # Fehlermeldungen
├── en/
│   ├── common.json
│   ├── game.json
│   ├── buildings.json
│   ├── resources.json
│   └── errors.json
├── fr/
│   └── ...
└── es/
    └── ...
```

### Beispiel: common.json (Deutsch)

```json
{
    "app": {
        "name": "Wasteland - Verbrannte Zone",
        "version": "1.6"
    },
    "navigation": {
        "dashboard": "Dashboard",
        "map": "Weltkarte",
        "province": "Provinz",
        "buildings": "Gebäude",
        "trade": "Handel",
        "military": "Militär",
        "research": "Forschung",
        "settings": "Einstellungen",
        "profile": "Profil",
        "logout": "Abmelden"
    },
    "buttons": {
        "save": "Speichern",
        "cancel": "Abbrechen",
        "delete": "Löschen",
        "edit": "Bearbeiten",
        "create": "Erstellen",
        "confirm": "Bestätigen",
        "close": "Schließen"
    },
    "messages": {
        "loading": "Laden...",
        "error": "Ein Fehler ist aufgetreten",
        "success": "Erfolgreich abgeschlossen",
        "no_data": "Keine Daten verfügbar"
    }
}
```

### Beispiel: game.json (Deutsch)

```json
{
    "resources": {
        "food": "Nahrung",
        "water": "Wasser",
        "energy": "Energie",
        "materials": "Materialien",
        "technology": "Technologie"
    },
    "actions": {
        "build": "Bauen",
        "upgrade": "Ausbauen",
        "train": "Ausbilden",
        "attack": "Angreifen",
        "defend": "Verteidigen",
        "trade": "Handeln"
    },
    "status": {
        "active": "Aktiv",
        "inactive": "Inaktiv",
        "under_construction": "Im Bau",
        "destroyed": "Zerstört"
    }
}
```

### Beispiel: errors.json (Deutsch)

```json
{
    "auth": {
        "invalid_credentials": "Ungültige Zugangsdaten",
        "token_expired": "Session abgelaufen, bitte erneut einloggen",
        "unauthorized": "Nicht autorisiert"
    },
    "game": {
        "insufficient_resources": "Nicht genügend Ressourcen",
        "building_cost_insufficient": "Nicht genug Materialien für Bau",
        "unit_training_failed": "Ausbildung fehlgeschlagen"
    },
    "system": {
        "not_found": "Ressource nicht gefunden",
        "validation_error": "Ungültige Eingabe",
        "server_error": "Interner Serverfehler"
    }
}
```

---

## 🔧 Translation Service Implementation

### Loader für JSON Translation Files

```python
# app/services/translation_service.py
import json
import os
from pathlib import Path

class TranslationService:
    def __init__(self, locales_dir: str = "app/locales"):
        self.locales_dir = Path(locales_dir)
        self.translations = {}
        self.load_all_translations()
    
    def load_all_translations(self):
        """Alle Übersetzungsdateien laden"""
        
        for language_dir in self.locales_dir.iterdir():
            if language_dir.is_dir():
                lang_code = language_dir.name
                
                self.translations[lang_code] = {}
                
                for json_file in language_dir.glob("*.json"):
                    file_key = json_file.stem  # z.B. "common", "game"
                    
                    with open(json_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code][file_key] = json.load(f)
    
    def get_translation(self, lang: str, key: str, fallback_lang: str = "de") -> str:
        """Übersetzung abrufen (mit Fallback)"""
        
        # Direkte Suche in angefordelter Sprache
        translation = self._lookup(lang, key)
        
        if translation:
            return translation
        
        # Fallback zu Standardsprache
        if fallback_lang != lang:
            translation = self._lookup(fallback_lang, key)
            
            if translation:
                return translation
        
        # Letzter Fallback: Key selbst zurückgeben (Debug)
        return key
    
    def _lookup(self, lang: str, key: str):
        """Schlüsselsuche in einer Sprache (dot-separated keys)"""
        
        lang_data = self.translations.get(lang, {})
        
        parts = key.split(".")
        current = lang_data
        
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        if isinstance(current, str):
            return current
        
        return None
    
    def get_available_languages(self) -> dict:
        """Verfügbare Sprachen zurückgeben"""
        from app.config import i18n_config
        
        return i18n_config.SUPPORTED_LANGUAGES

# Singleton
translation_service = TranslationService()
```

---

## 📡 API Middleware für Language Detection

### Accept-Language Header Parsing

```python
# app/middleware/language_detection.py
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

class LanguageDetectionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Sprache aus Accept-Language Header extrahieren
        accept_language = request.headers.get("accept-language", "de")
        
        # Erste Sprache priorisieren (z.B. "de-DE,de;q=0.9,en;q=0.8")
        primary_lang = accept_language.split(",")[0].strip().split("-")[0]
        
        # Unterstützte Sprache?
        from app.config import i18n_config
        
        if primary_lang in i18n_config.SUPPORTED_LANGUAGES:
            request.state.language = primary_lang
        else:
            # Fallback zu Standardsprache
            request.state.language = i18n_config.DEFAULT_LANGUAGE
        
        response = await call_next(request)
        
        # Language Header in Response setzen
        response.headers["Content-Language"] = request.state.language
        
        return response

app.add_middleware(LanguageDetectionMiddleware)
```

---

## 📝 API Endpoints für Übersetzungen

### Translation Router

```python
# app/api/v1/i18n.py
from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/i18n/languages")
async def get_languages():
    """Verfügbare Sprachen auflisten"""
    
    from app.services.translation_service import translation_service
    
    return {
        "languages": translation_service.get_available_languages()
    }

@router.get("/i18n/translations")
async def get_translations(
    request: Request,
    namespace: str = "common"
):
    """Übersetzungen für Namespace abrufen"""
    
    lang = request.state.language
    
    from app.services.translation_service import translation_service
    
    translations = translation_service.translations.get(lang, {}).get(namespace, {})
    
    return {
        "language": lang,
        "namespace": namespace,
        "translations": translations
    }

@router.get("/i18n/all")
async def get_all_translations(
    request: Request
):
    """Alle Übersetzungen für aktuelle Sprache abrufen"""
    
    lang = request.state.language
    
    from app.services.translation_service import translation_service
    
    all_translations = {}
    
    for namespace in ["common", "game", "buildings", "resources", "errors"]:
        all_translations[namespace] = translation_service.translations.get(lang, {}).get(namespace, {})
    
    return {
        "language": lang,
        "translations": all_translations
    }

@router.post("/i18n/translate")
async def translate_text(
    request: Request,
    text: str,
    target_lang: str = None
):
    """Einzelnen Text übersetzen (Fallback zu Request-Language)"""
    
    lang = target_lang or request.state.language
    
    from app.services.translation_service import translation_service
    
    # Direkte Übersetzung (wenn Key in JSON)
    translation = translation_service.get_translation(lang, text)
    
    if translation != text:  # Wurde übersetzt?
        return {
            "original": text,
            "translated": translation,
            "language": lang
        }
    else:
        # Kein Eintrag in JSON → Key zurückgeben (muss manuell übersetzt werden)
        return {
            "original": text,
            "translated": text,  # Fallback: Originaltext
            "language": lang,
            "note": "Keine Übersetzung verfügbar"
        }
```

---

## 🖥️ Client-Side i18n (JavaScript)

### Translation Manager

```javascript
// js/i18n/translation-manager.js

class TranslationManager {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
        this.currentLanguage = 'de';
        this.translations = {};
    }

    // Sprache setzen und Übersetzungen laden
    async setLanguage(lang) {
        this.currentLanguage = lang;
        
        // Übersetzungen vom Server laden
        const response = await fetch(`${this.baseUrl}/i18n/all?lang=${lang}`);
        
        if (response.ok) {
            const data = await response.json();
            this.translations = data.translations;
            
            // Sprache im localStorage speichern
            localStorage.setItem('language', lang);
            
            // UI aktualisieren
            this.updateUI();
        }
    }

    // Übersetzung abrufen (dot-separated key)
    t(key, params = {}) {
        let translation = this._lookup(this.currentLanguage, key);
        
        if (!translation) {
            // Fallback zu Englisch
            translation = this._lookup('en', key);
        }
        
        if (!translation) {
            // Letzter Fallback: Key selbst
            return key;
        }
        
        // Platzhalter ersetzen (z.B. {name})
        for (const [paramKey, paramValue] of Object.entries(params)) {
            translation = translation.replace(`{${paramKey}}`, paramValue);
        }
        
        return translation;
    }

    // Schüsselsuche in Übersetzungen
    _lookup(lang, key) {
        const langData = this.translations[lang] || {};
        const parts = key.split(".");
        let current = langData;
        
        for (const part of parts) {
            if (current && current[part] !== undefined) {
                current = current[part];
            } else {
                return null;
            }
        }
        
        return typeof current === 'string' ? current : null;
    }

    // UI aktualisieren (data-i18n Attribute)
    updateUI() {
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const translation = this.t(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                element.placeholder = translation;
            } else {
                element.textContent = translation;
            }
        });

        // Title Attribute aktualisieren
        document.querySelectorAll('[data-i18n-title]').forEach(element => {
            const key = element.getAttribute('data-i18n-title');
            element.title = this.t(key);
        });

        // Placeholder Attribute aktualisieren
        document.querySelectorAll('[data-i18n-placeholder]').forEach(element => {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = this.t(key);
        });
    }

    // Sprache aus Browser ermitteln (Accept-Language)
    detectBrowserLanguage() {
        const acceptLanguage = navigator.language || navigator.userLanguage;
        return acceptLanguage.split("-")[0]; // z.B. "de-DE" → "de"
    }

    // Initialisieren
    async init() {
        // Gespeicherte Sprache aus localStorage laden
        const savedLanguage = localStorage.getItem('language');
        
        if (savedLanguage) {
            await this.setLanguage(savedLanguage);
        } else {
            // Browser-Sprache ermitteln
            const browserLang = this.detectBrowserLanguage();
            await this.setLanguage(browserLang);
        }
    }

    // Sprachumschaltung (Dropdown)
    createLanguageSelector(containerId) {
        const container = document.getElementById(containerId);
        
        if (!container) return;

        // Verfügbare Sprachen laden
        fetch(`${this.baseUrl}/i18n/languages`)
            .then(response => response.json())
            .then(data => {
                container.innerHTML = '';
                
                Object.entries(data.languages).forEach(([code, info]) => {
                    const button = document.createElement('button');
                    button.textContent = info.native_name;
                    button.className = code === this.currentLanguage ? 'active' : '';
                    
                    button.addEventListener('click', () => {
                        this.setLanguage(code);
                    });
                    
                    container.appendChild(button);
                });
            });
    }
}

// Singleton Instance
const i18n = new TranslationManager();

export default i18n;
```

### HTML Language Selector

```html
<!-- templates/components/language-selector.html -->
<div class="language-selector" id="language-selector">
    <button onclick="i18n.setLanguage('de')" class="lang-btn active">Deutsch</button>
    <button onclick="i18n.setLanguage('en')" class="lang-btn">English</button>
    <button onclick="i18n.setLanguage('fr')" class="lang-btn">Français</button>
    <button onclick="i18n.setLanguage('es')" class="lang-btn">Español</button>
</div>

<style>
.language-selector {
    display: flex;
    gap: 8px;
    padding: 10px;
}

.lang-btn {
    padding: 6px 12px;
    border: 1px solid #0f3460;
    background-color: #16213e;
    color: #ffffff;
    border-radius: 4px;
    cursor: pointer;
}

.lang-btn.active {
    background-color: #e94560;
    border-color: #e94560;
}

.lang-btn:hover {
    background-color: #0f3460;
}
</style>
```

### Verwendung in HTML Templates

```html
<!-- templates/dashboard.html -->
<h1 data-i18n="app.name">Wasteland - Verbrannte Zone</h1>

<nav>
    <a href="/dashboard" data-i18n="navigation.dashboard">Dashboard</a>
    <a href="/map" data-i18n="navigation.map">Weltkarte</a>
    <a href="/province" data-i18n="navigation.province">Provinz</a>
    <a href="/buildings" data-i18n="navigation.buildings">Gebäude</a>
    <a href="/trade" data-i18n="navigation.trade">Handel</a>
    <a href="/military" data-i18n="navigation.military">Militär</a>
    <a href="/settings" data-i18n="navigation.settings">Einstellungen</a>
</nav>

<button data-i18n="buttons.save" onclick="saveChanges()">Speichern</button>
<button data-i18n="buttons.cancel" onclick="cancelChanges()">Abbrechen</button>

<input type="text" data-i18n-placeholder="placeholders.search" placeholder="Suche...">

<div id="language-selector"></div>

<script src="/js/i18n/translation-manager.js"></script>
<script>
    // Initialisieren
    i18n.init();
    
    // Sprachumschaltung erstellen
    i18n.createLanguageSelector('language-selector');
</script>
```

---

## 🧪 Testing i18n

### Unit Tests für Translation Service

```python
# tests/services/test_translation_service.py
import pytest
from app.services.translation_service import TranslationService

@pytest.fixture
def translation_service():
    return TranslationService("app/locales")

def test_get_translation_de(translation_service):
    """Testet deutsche Übersetzung"""
    
    translation = translation_service.get_translation("de", "app.name")
    
    assert translation == "Wasteland - Verbrannte Zone"

def test_get_translation_en(translation_service):
    """Testet englische Übersetzung"""
    
    translation = translation_service.get_translation("en", "app.name")
    
    assert translation == "Wasteland - Burned Zone"

def test_get_translation_fallback(translation_service):
    """Testet Fallback zu Standardsprache"""
    
    # Französisch existiert nicht für diesen Key → Deutsch (Default)
    translation = translation_service.get_translation("fr", "app.name")
    
    assert translation == "Wasteland - Verbrannte Zone"

def test_get_translation_missing_key(translation_service):
    """Testet fehlenden Key (gibt Key zurück)"""
    
    translation = translation_service.get_translation("de", "nonexistent.key")
    
    assert translation == "nonexistent.key"

def test_get_available_languages(translation_service):
    """Testet verfügbare Sprachen"""
    
    languages = translation_service.get_available_languages()
    
    assert "de" in languages
    assert "en" in languages
    assert "fr" in languages
    assert "es" in languages

def test_translation_with_params(translation_service):
    """Testet Übersetzung mit Platzhaltern"""
    
    # Angenommen: game.welcome = "Willkommen, {name}!"
    translation = translation_service.get_translation("de", "game.welcome", params={"name": "Fabian"})
    
    assert translation == "Willkommen, Fabian!"
```

---

## 🎯 Best Practices

1. **JSON-basierte Übersetzungen** - Einfach zu pflegen und zu versionen
2. **Dot-separated Keys** - Strukturierte Hierarchie (namespace.key)
3. **Fallback-System** - Englischer Fallback bei fehlenden Übersetzungen
4. **Client-Side Caching** - Übersetzungen im localStorage speichern
5. **data-i18n Attribute** - Deklarative Übersetzungen in HTML

---

**i18n ermöglicht mehrsprachige Benutzeroberfläche mit dynamischer Sprachumschaltung!**

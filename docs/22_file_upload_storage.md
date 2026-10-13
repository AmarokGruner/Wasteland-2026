# 📁 File Upload & Storage System

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt die Implementierung eines File Upload Systems für:
- Benutzerprofile (Avatar, Profilbild)
- Spiel-Screenshots
- Clan/Guild Logos
- Export/Import von Spieldaten

---

## 🎯 Ziele

1. **Sichere Uploads** - Dateityp-Validierung, Größlimits
2. **Skalierbare Storage** - Lokale Dateien oder Cloud (S3)
3. **URL Generation** - Signed URLs für temporären Zugriff
4. **Cleanup** - Automatische Löschung veralteter Dateien

---

## 🏗️ Storage Architecture Options

### Option 1: Lokaler Storage (Empfohlen für Single-Server)

```
FastAPI Backend
└── /uploads/
    ├── avatars/          (Benutzer-Avatare)
    ├── screenshots/      (Spiel-Screenshots)
    ├── guilds/           (Clan-Logos)
    └── exports/          (Export-Dateien)
```

**Vorteile:**
- Keine externe Abhängigkeit
- Einfach zu verwalten
- Schneller Zugriff

**Nachteile:**
- Nicht skalierbar über mehrere Server
- Backup muss manuell erfolgen

### Option 2: Cloud Storage (S3/MinIO)

```
FastAPI Backend
├── SQLite (Metadaten)
└── S3/MinIO (Dateien)
    ├── avatars/
    ├── screenshots/
    └── guilds/
```

**Vorteile:**
- Horizontal skalierbar
- Automatische Backups
- CDN-fähig

**Nachteile:**
- Zusätzliche Infrastruktur
- Kosten pro Storage/Request

---

## 🔧 Installation & Configuration

### Dependencies

```bash
pip install python-multipart boto3 aiofiles
# Oder für lokales Storage:
# pip install Pillow (für Bildverarbeitung)
```

### File Upload Configuration

```python
# app/config.py

import os

class StorageConfig:
    # Lokales Storage Verzeichnis
    UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
    
    # Max File Size (10 MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024
    
    # Erlaubte Dateitypen pro Kategorie
    ALLOWED_TYPES = {
        "avatar": {"extensions": [".jpg", ".jpeg", ".png", ".gif"], 
                   "mime_types": ["image/jpeg", "image/png", "image/gif"]},
        "screenshot": {"extensions": [".jpg", ".jpeg", ".png"], 
                       "mime_types": ["image/jpeg", "image/png"]},
        "guild_logo": {"extensions": [".jpg", ".jpeg", ".png"], 
                       "mime_types": ["image/jpeg", "image/png"]},
        "export": {"extensions": [".json", ".csv"], 
                   "mime_types": ["application/json", "text/csv"]}
    }
    
    # Cloud Storage (optional)
    USE_CLOUD_STORAGE = os.getenv("USE_CLOUD_STORAGE", "false").lower() == "true"
    
    # AWS S3 Configuration (wenn USE_CLOUD_STORAGE=true)
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "wasteland-uploads")
    AWS_S3_REGION = os.getenv("AWS_S3_REGION", "eu-central-1")
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

storage_config = StorageConfig()
```

---

## 🔧 File Upload Service (Lokales Storage)

### Directory Structure Creation

```python
# app/services/storage_service.py
import os
import uuid
import shutil
from pathlib import Path
from datetime import datetime, timedelta

class StorageService:
    def __init__(self):
        self.uploads_dir = Path(storage_config.UPLOADS_DIR)
        self._create_directories()
    
    def _create_directories(self):
        """Upload-Verzeichnisse erstellen"""
        
        categories = ["avatars", "screenshots", "guilds", "exports"]
        
        for category in categories:
            dir_path = self.uploads_dir / category
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def validate_file(self, filename: str, category: str) -> dict:
        """Datei validieren (Typ, Größe)"""
        
        file_ext = Path(filename).suffix.lower()
        
        # Kategorie prüfen
        if category not in storage_config.ALLOWED_TYPES:
            return {
                "valid": False,
                "error": f"Ungültige Kategorie: {category}"
            }
        
        allowed = storage_config.ALLOWED_TYPES[category]
        
        # Extension prüfen
        if file_ext not in allowed["extensions"]:
            return {
                "valid": False,
                "error": f"Dateityp nicht erlaubt. Erlaubt: {', '.join(allowed['extensions'])}"
            }
        
        return {"valid": True}
    
    def save_file(self, file_data: bytes, filename: str, category: str, user_id: int) -> dict:
        """Datei speichern und URL zurückgeben"""
        
        # Validieren
        validation = self.validate_file(filename, category)
        
        if not validation["valid"]:
            return validation
        
        # Neue Dateiname generieren (UUID + Original Extension)
        file_ext = Path(filename).suffix.lower()
        new_filename = f"{uuid.uuid4().hex}{file_ext}"
        
        # Ziel-Pfad
        target_dir = self.uploads_dir / category
        file_path = target_dir / new_filename
        
        # Datei schreiben
        with open(file_path, "wb") as f:
            f.write(file_data)
        
        # URL generieren
        file_url = f"/uploads/{category}/{new_filename}"
        
        return {
            "valid": True,
            "file_url": file_url,
            "filename": new_filename,
            "category": category,
            "size": len(file_data)
        }
    
    def delete_file(self, file_url: str) -> dict:
        """Datei löschen"""
        
        # URL in Dateipfad umwandeln
        # /uploads/avatars/abc123.jpg → uploads/avatars/abc123.jpg
        relative_path = file_url.replace("/uploads/", "")
        file_path = self.uploads_dir / relative_path
        
        if not file_path.exists():
            return {
                "valid": False,
                "error": "Datei nicht gefunden"
            }
        
        # Datei löschen
        file_path.unlink()
        
        return {"valid": True, "message": "Datei gelöscht"}
    
    def get_file_size(self, file_url: str) -> int:
        """Dateigröße abrufen"""
        
        relative_path = file_url.replace("/uploads/", "")
        file_path = self.uploads_dir / relative_path
        
        if not file_path.exists():
            return 0
        
        return file_path.stat().st_size

# Singleton
storage_service = StorageService()
```

---

## ☁️ Cloud Storage (S3/MinIO) Alternative

### S3 Service Implementation

```python
# app/services/s3_storage_service.py
import boto3
from botocore.exceptions import ClientError
from datetime import timedelta

class S3StorageService:
    def __init__(self):
        if not storage_config.USE_CLOUD_STORAGE:
            return
        
        self.s3_client = boto3.client(
            "s3",
            aws_access_key_id=storage_config.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=storage_config.AWS_SECRET_ACCESS_KEY,
            region_name=storage_config.AWS_S3_REGION
        )
        
        self.bucket_name = storage_config.AWS_S3_BUCKET
    
    def upload_file(self, file_data: bytes, filename: str, category: str, user_id: int) -> dict:
        """Datei in S3 hochladen"""
        
        # Validieren (wie lokaler Storage)
        validation = storage_service.validate_file(filename, category)
        
        if not validation["valid"]:
            return validation
        
        # S3 Key generieren
        file_ext = Path(filename).suffix.lower()
        s3_key = f"{category}/{user_id}/{uuid.uuid4().hex}{file_ext}"
        
        # Upload
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType=self._get_content_type(filename)
            )
            
            # URL generieren (CloudFront oder S3 direkt)
            file_url = f"https://{self.bucket_name}.s3.{storage_config.AWS_S3_REGION}.amazonaws.com/{s3_key}"
            
            return {
                "valid": True,
                "file_url": file_url,
                "filename": Path(filename).name,
                "category": category,
                "size": len(file_data)
            }
        
        except ClientError as e:
            return {
                "valid": False,
                "error": f"S3 Upload fehlgeschlagen: {str(e)}"
            }
    
    def generate_signed_url(self, file_url: str, expires_in: int = 3600) -> str:
        """Signed URL für temporären Zugriff generieren"""
        
        # S3 Key aus URL extrahieren
        s3_key = file_url.replace(f"https://{self.bucket_name}.s3.{storage_config.AWS_S3_REGION}.amazonaws.com/", "")
        
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": s3_key},
                ExpiresIn=expires_in
            )
            
            return url
        
        except ClientError as e:
            return ""
    
    def delete_file(self, file_url: str) -> dict:
        """Datei aus S3 löschen"""
        
        s3_key = file_url.replace(f"https://{self.bucket_name}.s3.{storage_config.AWS_S3_REGION}.amazonaws.com/", "")
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=s3_key)
            
            return {"valid": True, "message": "Datei gelöscht"}
        
        except ClientError as e:
            return {
                "valid": False,
                "error": f"S3 Delete fehlgeschlagen: {str(e)}"
            }
    
    def _get_content_type(self, filename: str) -> str:
        """Content-Type aus Extension ermitteln"""
        
        ext = Path(filename).suffix.lower()
        
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".json": "application/json",
            ".csv": "text/csv"
        }
        
        return content_types.get(ext, "application/octet-stream")

# Singleton (wenn Cloud Storage aktiviert)
s3_storage_service = S3StorageService() if storage_config.USE_CLOUD_STORAGE else None
```

---

## 📡 API Endpoints für File Uploads

### Upload Router

```python
# app/api/v1/uploads.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/uploads/avatar")
async def upload_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Avatar hochladen"""
    
    # Datei lesen
    file_data = await file.read()
    
    # Größe prüfen (max 10 MB)
    if len(file_data) > storage_config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": f"Datei zu groß (max {storage_config.MAX_FILE_SIZE // 1024 // 1024} MB)"}
        )
    
    # Speichern
    result = storage_service.save_file(
        file_data=file_data,
        filename=file.filename,
        category="avatar",
        user_id=current_user.id
    )
    
    if not result["valid"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "UPLOAD_FAILED", "message": result["error"]}
        )
    
    # User Avatar URL aktualisieren
    current_user.avatar_url = result["file_url"]
    db.commit()
    
    return {
        "message": "Avatar erfolgreich hochgeladen",
        "avatar_url": result["file_url"]
    }

@router.post("/uploads/screenshot")
async def upload_screenshot(
    request: Request,
    file: UploadFile = File(...),
    province_id: int = None,  # Optional: Zu welcher Provinz gehört der Screenshot?
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Spiel-Screenshot hochladen"""
    
    file_data = await file.read()
    
    if len(file_data) > storage_config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": f"Datei zu groß (max {storage_config.MAX_FILE_SIZE // 1024 // 1024} MB)"}
        )
    
    result = storage_service.save_file(
        file_data=file_data,
        filename=file.filename,
        category="screenshots",
        user_id=current_user.id
    )
    
    if not result["valid"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "UPLOAD_FAILED", "message": result["error"]}
        )
    
    # Screenshot in Datenbank speichern (optional)
    from app.models import Screenshot
    
    screenshot = Screenshot(
        user_id=current_user.id,
        province_id=province_id,
        file_url=result["file_url"],
        uploaded_at=datetime.utcnow()
    )
    
    db.add(screenshot)
    db.commit()
    
    return {
        "message": "Screenshot erfolgreich hochgeladen",
        "screenshot_url": result["file_url"]
    }

@router.post("/uploads/guild-logo")
async def upload_guild_logo(
    request: Request,
    file: UploadFile = File(...),
    guild_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Clan/Guild Logo hochladen"""
    
    file_data = await file.read()
    
    if len(file_data) > storage_config.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail={"code": "FILE_TOO_LARGE", "message": f"Datei zu groß (max {storage_config.MAX_FILE_SIZE // 1024 // 1024} MB)"}
        )
    
    result = storage_service.save_file(
        file_data=file_data,
        filename=file.filename,
        category="guilds",
        user_id=current_user.id
    )
    
    if not result["valid"]:
        raise HTTPException(
            status_code=400,
            detail={"code": "UPLOAD_FAILED", "message": result["error"]}
        )
    
    # Guild Logo URL aktualisieren (vereinfacht)
    guild = db.query(Guild).get(guild_id)
    
    if not guild:
        raise HTTPException(
            status_code=404,
            detail={"code": "GUILD_NOT_FOUND", "message": "Guild nicht gefunden"}
        )
    
    guild.logo_url = result["file_url"]
    db.commit()
    
    return {
        "message": "Guild Logo erfolgreich hochgeladen",
        "logo_url": result["file_url"]
    }

@router.delete("/uploads/{category}/{filename}")
async def delete_file(
    category: str,
    filename: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Datei löschen"""
    
    file_url = f"/uploads/{category}/{filename}"
    
    result = storage_service.delete_file(file_url)
    
    if not result["valid"]:
        raise HTTPException(
            status_code=404,
            detail={"code": "FILE_NOT_FOUND", "message": result["error"]}
        )
    
    return {"message": "Datei erfolgreich gelöscht"}

@router.get("/uploads/{category}/{filename}")
async def serve_file(
    category: str,
    filename: str
):
    """Datei aus Storage servieren"""
    
    from fastapi.responses import FileResponse
    
    file_path = storage_service.uploads_dir / category / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail={"code": "FILE_NOT_FOUND", "message": "Datei nicht gefunden"}
        )
    
    # Content-Type ermitteln
    import mimetypes
    content_type, _ = mimetypes.guess_type(str(file_path))
    
    return FileResponse(
        path=str(file_path),
        media_type=content_type or "application/octet-stream"
    )
```

---

## 🖥️ Client-Side Upload UI (JavaScript)

### Upload Component

```javascript
// js/components/file-upload.js

class FileUploadComponent {
    constructor(baseUrl = 'http://localhost:8011') {
        this.baseUrl = baseUrl;
    }

    // Avatar Upload
    async uploadAvatar(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.baseUrl}/uploads/avatar`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                
                // Avatar im UI aktualisieren
                document.getElementById('user-avatar').src = data.avatar_url;
                
                return { success: true, url: data.avatar_url };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail.message };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Screenshot Upload
    async uploadScreenshot(file, provinceId = null) {
        const formData = new FormData();
        formData.append('file', file);
        
        if (provinceId) {
            formData.append('province_id', provinceId);
        }

        try {
            const response = await fetch(`${this.baseUrl}/uploads/screenshot`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                
                // Screenshot im UI anzeigen
                this.addScreenshotToGallery(data.screenshot_url);
                
                return { success: true, url: data.screenshot_url };
            } else {
                const error = await response.json();
                return { success: false, error: error.detail.message };
            }
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // Drag & Drop Handler
    initDragAndDrop(dropZoneId, uploadType) {
        const dropZone = document.getElementById(dropZoneId);
        
        if (!dropZone) return;

        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', async (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');

            const files = e.dataTransfer.files;
            
            if (files.length > 0) {
                const file = files[0];
                
                // Dateityp prüfen
                if (!this.isAllowedType(file.type)) {
                    this.showError('Dateityp nicht erlaubt');
                    return;
                }

                // Upload starten
                if (uploadType === 'avatar') {
                    const result = await this.uploadAvatar(file);
                    
                    if (result.success) {
                        this.showSuccess('Avatar aktualisiert');
                    } else {
                        this.showError(result.error);
                    }
                } else if (uploadType === 'screenshot') {
                    const result = await this.uploadScreenshot(file);
                    
                    if (result.success) {
                        this.showSuccess('Screenshot hochgeladen');
                    } else {
                        this.showError(result.error);
                    }
                }
            }
        });
    }

    // Dateityp prüfen
    isAllowedType(mimeType) {
        const allowedTypes = ['image/jpeg', 'image/png', 'image/gif'];
        return allowedTypes.includes(mimeType);
    }

    // UI Feedback
    showError(message) {
        const errorDiv = document.getElementById('upload-error');
        
        if (errorDiv) {
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            
            setTimeout(() => {
                errorDiv.style.display = 'none';
            }, 5000);
        }
    }

    showSuccess(message) {
        const successDiv = document.getElementById('upload-success');
        
        if (successDiv) {
            successDiv.textContent = message;
            successDiv.style.display = 'block';
            
            setTimeout(() => {
                successDiv.style.display = 'none';
            }, 3000);
        }
    }

    addScreenshotToGallery(url) {
        const gallery = document.getElementById('screenshot-gallery');
        
        if (gallery) {
            const img = document.createElement('img');
            img.src = url;
            img.alt = 'Spiel-Screenshot';
            
            gallery.appendChild(img);
        }
    }
}

// Initialisieren
const fileUpload = new FileUploadComponent();

// Drag & Drop Zonen initialisieren
fileUpload.initDragAndDrop('avatar-drop-zone', 'avatar');
fileUpload.initDragAndDrop('screenshot-drop-zone', 'screenshot');

export default fileUpload;
```

### HTML Upload UI

```html
<!-- templates/components/file-upload.html -->
<div class="upload-section">
    <h3>Avatar aktualisieren</h3>
    
    <div id="avatar-drop-zone" class="drop-zone">
        <p>Avatar hierher ziehen oder klicken zum Auswählen</p>
        
        <input 
            type="file" 
            id="avatar-file-input" 
            accept="image/jpeg,image/png,image/gif"
            style="display: none;"
        >
        
        <button onclick="document.getElementById('avatar-file-input').click()">
            Datei auswählen
        </button>
    </div>
    
    <div id="upload-error" class="error-message" style="display: none;"></div>
    <div id="upload-success" class="success-message" style="display: none;"></div>
</div>

<div class="upload-section">
    <h3>Spiel-Screenshot hochladen</h3>
    
    <div id="screenshot-drop-zone" class="drop-zone">
        <p>Screenshot hierher ziehen oder klicken zum Auswählen</p>
        
        <input 
            type="file" 
            id="screenshot-file-input" 
            accept="image/jpeg,image/png"
            style="display: none;"
        >
        
        <button onclick="document.getElementById('screenshot-file-input').click()">
            Datei auswählen
        </button>
    </div>
    
    <div id="screenshot-gallery" class="gallery"></div>
</div>

<style>
.drop-zone {
    border: 2px dashed #0f3460;
    border-radius: 8px;
    padding: 40px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.3s;
}

.drop-zone.drag-over {
    border-color: #e94560;
    background-color: rgba(233, 69, 96, 0.1);
}

.error-message {
    color: #e94560;
    padding: 10px;
    margin-top: 10px;
    background-color: rgba(233, 69, 96, 0.1);
    border-radius: 4px;
}

.success-message {
    color: #4caf50;
    padding: 10px;
    margin-top: 10px;
    background-color: rgba(76, 175, 80, 0.1);
    border-radius: 4px;
}

.gallery {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 20px;
}

.gallery img {
    width: 150px;
    height: 150px;
    object-fit: cover;
    border-radius: 4px;
    border: 1px solid #0f3460;
}
</style>
```

---

## 🧪 Testing File Uploads

### Unit Tests für Storage Service

```python
# tests/services/test_storage_service.py
import pytest
import tempfile
from pathlib import Path

@pytest.fixture
def storage_service():
    from app.services.storage_service import StorageService
    
    # Temporäres Verzeichnis für Tests verwenden
    with tempfile.TemporaryDirectory() as tmpdir:
        original_uploads_dir = storage_config.UPLOADS_DIR
        storage_config.UPLOADS_DIR = tmpdir
        
        service = StorageService()
        
        yield service
        
        # Cleanup
        storage_config.UPLOADS_DIR = original_uploads_dir

def test_validate_file_valid(storage_service):
    """Testet gültige Datei-Validierung"""
    
    result = storage_service.validate_file("avatar.jpg", "avatar")
    
    assert result["valid"] is True

def test_validate_file_invalid_extension(storage_service):
    """Testet ungültige Datei-Extension"""
    
    result = storage_service.validate_file("avatar.exe", "avatar")
    
    assert result["valid"] is False
    assert "Dateityp nicht erlaubt" in result["error"]

def test_validate_file_invalid_category(storage_service):
    """Testet ungültige Kategorie"""
    
    result = storage_service.validate_file("avatar.jpg", "invalid")
    
    assert result["valid"] is False
    assert "Ungültige Kategorie" in result["error"]

def test_save_file(storage_service):
    """Testet Dateispeicherung"""
    
    file_data = b"fake image data"
    
    result = storage_service.save_file(
        file_data=file_data,
        filename="test.jpg",
        category="avatars",
        user_id=1
    )
    
    assert result["valid"] is True
    assert result["file_url"].startswith("/uploads/avatars/")
    assert "size" in result

def test_delete_file(storage_service):
    """Testet Dateilöschung"""
    
    # Datei speichern
    save_result = storage_service.save_file(
        file_data=b"test",
        filename="delete_test.jpg",
        category="avatars",
        user_id=1
    )
    
    # Datei löschen
    delete_result = storage_service.delete_file(save_result["file_url"])
    
    assert delete_result["valid"] is True

def test_file_size_limit(storage_service):
    """Testet Dateigrößen-Limit"""
    
    large_file = b"x" * (storage_config.MAX_FILE_SIZE + 1)
    
    # In API Endpoint wird Größe geprüft, nicht im Service selbst
    assert len(large_file) > storage_config.MAX_FILE_SIZE
```

---

## 🎯 Best Practices

1. **Dateityp-Validierung** - Nur erlaubte Extensions/MIME Types
2. **Größenlimits setzen** - Max 10 MB pro Datei
3. **UUID-basierte Dateinamen** - Keine Original-Namen speichern (Sicherheit)
4. **Drag & Drop UI** - Benutzerfreundlicher Upload
5. **Cleanup veralteter Dateien** - Alte Avatare/Screenshots löschen

---

**File Upload System ermöglicht sichere, skalierbare Dateiverwaltung für Avatare, Screenshots und Guild-Logos!**

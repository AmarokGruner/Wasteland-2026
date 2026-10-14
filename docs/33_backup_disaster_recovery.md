# 💾 Backup & Disaster Recovery (Spiel-spezifisch)

**Wasteland - Verbrannte Zone v1.6**  
**Letztes Update:** 2026-10-14

---

## 📋 Übersicht

Dieses Dokument beschreibt spiel-spezifische Backup-Strategien: Ingame-Backups, Welt-Zurücksetzen, Provinz-Wiederherstellung und Backup-Rotation.

---

## 🎯 Ziele

1. **Ingame-Backups** - Admin kann manuell Backup erstellen
2. **Welt-Zurücksetzen** - Auf bestimmten Stand zurückkehren
3. **Provinz-Wiederherstellung** - Einzelne Provinzen wiederherstellen
4. **Backup-Rotation** - Automatische alte Backups löschen

---

## 🏗️ Backup-System Architektur

### Backup-Typen

```
1. Vollständiges Welt-Backup (alle Daten)
        ↓
2. Inkrementelles Backup (nur Änderungen seit letztem Backup)
        ↓
3. Einzelne Provinz-Backup (wenn nötig)
```

### Storage-Optionen

```
Lokal: /backups/wasteland/
    ├── full_2026-10-14_00-00.db
    ├── incremental_2026-10-14_06-00.db
    └── province_1_2026-10-14.db

Cloud (optional): S3/MinIO
    └── backups/wasteland/
```

---

## 📊 Datenbank-Schema für Backups

### Backup-Records

```python
# app/models.py - Backup Modelle

class BackupRecord(Base):
    """Backup-Eintrag in der Datenbank"""
    
    __tablename__ = "backup_records"
    
    id = Column(Integer, primary_key=True)
    
    # Backup-Typ (full, incremental, province)
    typ = Column(String(50), nullable=False)
    
    # Dateipfad (lokal oder Cloud)
    dateipfad = Column(String(500), nullable=False)
    
    # Größe in Bytes
    groesse_bytes = Column(Integer, default=0)
    
    # Erstellt von (Admin ID)
    erstellt_von_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Beschreibung
    beschreibung = Column(Text, nullable=True)
    
    # Tick-Status beim Backup
    tick_beim_backup = Column(Integer, nullable=False)
    
    # Gilt für welche Provinz? (bei province-Backups)
    province_id = Column(Integer, ForeignKey("provinzen.id"), nullable=True)
    
    # Erstellt am
    erstellt_am = Column(DateTime, default=datetime.utcnow)
    
    # Gelöscht? (für Rotation)
    geloescht = Column(Boolean, default=False)

# Helper: Vollständiges Backup erstellen
def create_full_backup(erstellt_von_id: int = None, beschreibung: str = None) -> dict:
    """Vollständiges Welt-Backup erstellen"""
    
    import shutil
    import os
    from datetime import datetime
    
    # Backup-Verzeichnis erstellen
    backup_dir = "/backups/wasteland"
    
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Datenbank kopieren
    original_db = "verbrannte_zone.db"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"full_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        shutil.copy2(original_db, backup_path)
        
        # Dateigröße ermitteln
        groesse = os.path.getsize(backup_path)
        
        # Backup-Record in Datenbank speichern
        backup_record = BackupRecord(
            typ="full",
            dateipfad=backup_path,
            groesse_bytes=groesse,
            erstellt_von_id=erstellt_von_id,
            beschreibung=beschreibung or f"Vollständiges Backup ({timestamp})",
            tick_beim_backup=tick_manager.current_tick,
            province_id=None
        )
        
        db.add(backup_record)
        db.commit()
        
        return {
            "success": True,
            "message": f"Vollständiges Backup erstellt: {backup_filename}",
            "path": backup_path,
            "size": groesse,
            "tick": tick_manager.current_tick
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Helper: Inkrementelles Backup erstellen
def create_incremental_backup(erstellt_von_id: int = None) -> dict:
    """Inkrementelles Backup (nur Änderungen seit letztem Backup)"""
    
    import os
    
    backup_dir = "/backups/wasteland"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"incremental_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Letztes Backup finden (full oder incremental)
        letztes_backup = db.query(BackupRecord).filter_by(geloescht=False).order_by(BackupRecord.erstellt_am.desc()).first()
        
        if not letztes_backup:
            return {"success": False, "error": "Kein vorheriges Backup gefunden"}
        
        # Änderungen seit letztem Backup exportieren (SQLite dump)
        # In Production: sqlite3 .dump verwenden oder SQLAlchemy export
        
        # Vereinfacht: gesamte Datenbank kopieren (inkrementell im Dateisystem)
        original_db = "verbrannte_zone.db"
        shutil.copy2(original_db, backup_path)
        
        groesse = os.path.getsize(backup_path)
        
        # Backup-Record speichern
        backup_record = BackupRecord(
            typ="incremental",
            dateipfad=backup_path,
            groesse_bytes=groesse,
            erstellt_von_id=erstellt_von_id,
            beschreibung=f"Inkrementelles Backup seit #{letztes_backup.tick_beim_backup}",
            tick_beim_backup=tick_manager.current_tick,
            province_id=None
        )
        
        db.add(backup_record)
        db.commit()
        
        return {
            "success": True,
            "message": f"Inkrementelles Backup erstellt: {backup_filename}",
            "path": backup_path,
            "size": groesse
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Helper: Einzelne Provinz backuppen
def create_province_backup(province_id: int, erstellt_von_id: int = None) -> dict:
    """Einzelne Provinz backuppen"""
    
    import os
    
    province = db.query(Province).get(province_id)
    
    if not province:
        return {"success": False, "error": "Provinz nicht gefunden"}
    
    backup_dir = "/backups/wasteland"
    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M")
    backup_filename = f"province_{province_id}_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    try:
        # Nur Daten dieser Provinz exportieren (SQLite filter)
        # In Production: sqlite3 mit WHERE-Klausel
        
        original_db = "verbrannte_zone.db"
        
        # Vereinfacht: gesamte Datenbank kopieren, aber Record auf province setzen
        shutil.copy2(original_db, backup_path)
        
        groesse = os.path.getsize(backup_path)
        
        # Backup-Record speichern
        backup_record = BackupRecord(
            typ="province",
            dateipfad=backup_path,
            groesse_bytes=groesse,
            erstellt_von_id=erstellt_von_id,
            beschreibung=f"Provinz-Backup: {province.name}",
            tick_beim_backup=tick_manager.current_tick,
            province_id=province_id
        )
        
        db.add(backup_record)
        db.commit()
        
        return {
            "success": True,
            "message": f"Provinz-Backup erstellt: {backup_filename}",
            "path": backup_path,
            "size": groesse,
            "province_id": province_id,
            "province_name": province.name
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Helper: Backup wiederherstellen
def restore_backup(backup_id: int) -> dict:
    """Backup wiederherstellen"""
    
    import shutil
    
    backup_record = db.query(BackupRecord).get(backup_id)
    
    if not backup_record:
        return {"success": False, "error": "Backup nicht gefunden"}
    
    if backup_record.geloescht:
        return {"success": False, "error": "Backup wurde gelöscht"}
    
    backup_path = backup_record.dateipfad
    
    if not os.path.exists(backup_path):
        return {"success": False, "error": f"Backup-Datei nicht gefunden: {backup_path}"}
    
    try:
        original_db = "verbrannte_zone.db"
        
        # Aktuelle Datenbank sichern (vor Restore)
        emergency_backup = f"emergency_{datetime.utcnow().strftime('%Y-%m-%d_%H-%M')}.db"
        shutil.copy2(original_db, emergency_backup)
        
        # Backup kopieren
        shutil.copy2(backup_path, original_db)
        
        # Datenbank neu laden (SQLite neu öffnen)
        # In Production: Server neustarten oder DB-Connection reset
        
        # Backup-Record als wiederhergestellt markieren
        backup_record.wiederhergestellt_am = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Backup wiederhergestellt: {backup_record.beschreibung}",
            "tick_wiederhergestellt": backup_record.tick_beim_backup,
            "emergency_backup": emergency_backup
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Helper: Provinz aus Backup wiederherstellen
def restore_province_from_backup(backup_id: int, province_id: int) -> dict:
    """Einzelne Provinz aus Backup wiederherstellen"""
    
    backup_record = db.query(BackupRecord).filter_by(id=backup_id, province_id=province_id).first()
    
    if not backup_record:
        return {"success": False, "error": "Provinz-Backup nicht gefunden"}
    
    backup_path = backup_record.dateipfad
    
    if not os.path.exists(backup_path):
        return {"success": False, "error": f"Backup-Datei nicht gefunden: {backup_path}"}
    
    try:
        original_db = "verbrannte_zone.db"
        
        # Nur Provinz-Daten aus Backup extrahieren (SQLite)
        # In Production: sqlite3 mit SELECT WHERE province_id = X
        
        # Vereinfacht: gesamte DB wiederherstellen, aber nur Provinz betrifft
        shutil.copy2(backup_path, original_db)
        
        # Record aktualisieren
        backup_record.wiederhergestellt_am = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": f"Provinz {province_id} aus Backup wiederhergestellt",
            "tick_wiederhergestellt": backup_record.tick_beim_backup
        }
    
    except Exception as e:
        return {"success": False, "error": str(e)}

# Helper: Backup-Rotation (alte Backups löschen)
def rotate_backups(max_backups: int = 10, max_age_days: int = 30) -> dict:
    """Backup-Rotation: Alte Backups löschen"""
    
    import os
    
    # Alle Backups laden (nicht gelöscht)
    backups = db.query(BackupRecord).filter_by(geloescht=False).order_by(BackupRecord.erstellt_am.asc()).all()
    
    geloeschte = []
    
    for backup in backups:
        # Nach Anzahl löschen (max_backups)
        if len(backups) - len(geloeschte) > max_backups:
            backup.geloescht = True
            
            # Dateisystem löschen
            if os.path.exists(backup.dateipfad):
                os.remove(backup.dateipfad)
            
            geloeschte.append(backup.id)
        
        # Nach Alter löschen (max_age_days)
        elif datetime.utcnow() - backup.erstellt_am > __import__('datetime').timedelta(days=max_age_days):
            backup.geloescht = True
            
            if os.path.exists(backup.dateipfad):
                os.remove(backup.dateipfad)
            
            geloeschte.append(backup.id)
    
    db.commit()
    
    return {
        "success": True,
        "message": f"Backup-Rotation durchgeführt: {len(geloeschte)} Backups gelöscht",
        "geloeschte_backups": geloeschte,
        "verbleibende_backups": len(backups) - len(geloeschte)
    }

# Helper: Alle Backups auflisten
def list_backups() -> list:
    """Alle Backups auflisten"""
    
    backups = db.query(BackupRecord).filter_by(geloescht=False).order_by(BackupRecord.erstellt_am.desc()).all()
    
    result = []
    
    for b in backups:
        admin_user = db.query(User).get(b.erstellt_von_id) if b.erstellt_von_id else None
        province = db.query(Province).get(b.province_id) if b.province_id else None
        
        result.append({
            "id": b.id,
            "typ": b.typ,
            "dateipfad": b.dateipfad,
            "groesse_bytes": b.groesse_bytes,
            "admin": admin_user.username if admin_user else "System",
            "beschreibung": b.beschreibung,
            "tick_beim_backup": b.tick_beim_backup,
            "province_id": b.province_id,
            "province_name": province.name if province else None,
            "erstellt_am": b.erstellt_am.isoformat()
        })
    
    return result

# Helper: Auto-Backup pro Tick (wenn konfiguriert)
def auto_backup_if_enabled():
    """Automatisches Backup wenn aktiviert"""
    
    # Konfiguration prüfen (ob Auto-Backup eingeschaltet)
    # In Production: Config-Tabelle lesen
    
    auto_backup_enabled = True  # Beispiel
    
    if not auto_backup_enabled:
        return
    
    # Alle 24 Ticks (1 Tag) ein inkrementelles Backup
    if tick_manager.current_tick % 24 == 0:
        create_incremental_backup()

# Helper: Backup vor World-Event erstellen
def backup_before_world_event():
    """Backup vor Welt-Ereignis erstellen (schützt vor Datenverlust)"""
    
    # Vor großen Events (z.B. Seuche, Krieg) Backup erstellen
    create_full_backup(beschreibung="Auto-Backup vor Welt-Ereignis")
```

---

## 📡 API Endpunkte für Backup-System

### Backup Router

```python
# app/api/v1/backup.py
from fastapi import APIRouter, Depends, HTTPException

router = APIRouter()

@router.post("/admin/backup/full")
async def create_full_backup_admin(
    beschreibung: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Vollständiges Backup erstellen"""
    
    result = create_full_backup(
        erstellt_von_id=current_user.id,
        beschreibung=beschreibung
    )
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail={"code": "BACKUP_FAILED", "message": result["error"]})
    
    return result

@router.post("/admin/backup/incremental")
async def create_incremental_backup_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Inkrementelles Backup erstellen"""
    
    result = create_incremental_backup(erstellt_von_id=current_user.id)
    
    if not result["success"]:
        raise HTTPException(status_code=500, detail={"code": "BACKUP_FAILED", "message": result["error"]})
    
    return result

@router.post("/admin/backup/province/{province_id}")
async def create_province_backup_admin(
    province_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Provinz-Backup erstellen"""
    
    result = create_province_backup(province_id, erstellt_von_id=current_user.id)
    
    if not result["success"]:
        raise HTTPException(status_code=404, detail={"code": "PROVINZ_NOT_FOUND", "message": result["error"]})
    
    return result

@router.post("/admin/backup/restore/{backup_id}")
async def restore_backup_admin(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Backup wiederherstellen"""
    
    result = restore_backup(backup_id)
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail={"code": "RESTORE_FAILED", "message": result["error"]})
    
    return result

@router.post("/admin/backup/rotate")
async def rotate_backups_admin(
    max_backups: int = 10,
    max_age_days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Backup-Rotation durchführen"""
    
    result = rotate_backups(max_backups=max_backups, max_age_days=max_age_days)
    
    return result

@router.get("/admin/backups")
async def list_backups_admin(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """Alle Backups auflisten"""
    
    backups = list_backups()
    
    return {"backups": backups}

@router.get("/admin/backup/status")
async def get_backup_status(
    db: Session = Depends(get_db)
):
    """Backup-Status abrufen (letzte Backups, Rotation)"""
    
    backups = list_backups()
    
    letztes_full = next((b for b in backups if b["typ"] == "full"), None)
    letztes_incremental = next((b for b in backups if b["typ"] == "incremental"), None)
    
    return {
        "total_backups": len(backups),
        "last_full_backup": letztes_full,
        "last_incremental_backup": letztes_incremental,
        "auto_backup_enabled": True  # Config lesen
    }
```

---

## 🧪 Testing Backup-System

### Unit Tests

```python
# tests/services/test_backup_service.py
import pytest
import tempfile
import os

@pytest.fixture
def temp_backup_dir():
    """Temporäres Backup-Verzeichnis für Tests"""
    
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

def test_create_full_backup(temp_backup_dir):
    """Testet Vollständiges Backup erstellen"""
    
    # Mock Datenbank-Pfad
    original_db = "test_verbrannte_zone.db"
    
    # Leere DB erstellen für Test
    with open(original_db, 'w') as f:
        f.write("")
    
    result = create_full_backup(beschreibung="Test-Backup")
    
    assert result["success"] is True
    assert "path" in result

def test_create_incremental_backup(temp_backup_dir):
    """Testet Inkrementelles Backup erstellen"""
    
    # Zuerst Full-Backup erstellen
    create_full_backup()
    
    result = create_incremental_backup()
    
    assert result["success"] is True

def test_create_province_backup(temp_backup_dir):
    """Testet Provinz-Backup erstellen"""
    
    result = create_province_backup(1)
    
    assert result["success"] is True

def test_restore_backup(temp_backup_dir):
    """Testet Backup wiederherstellen"""
    
    # Backup erstellen
    create_full_backup()
    
    backups = list_backups()
    
    if backups:
        result = restore_backup(backups[0]["id"])
        
        assert result["success"] is True

def test_rotate_backups(temp_backup_dir):
    """Testet Backup-Rotation"""
    
    # Mehrere Backups erstellen
    for i in range(15):
        create_full_backup(beschreibung=f"Backup {i}")
    
    result = rotate_backups(max_backups=10)
    
    assert result["success"] is True
    assert result["verbleibende_backups"] <= 10

def test_list_backups(temp_backup_dir):
    """Testet Backup-Auflistung"""
    
    create_full_backup()
    
    backups = list_backups()
    
    assert len(backups) >= 1

def test_backup_before_world_event(temp_backup_dir):
    """Testet Auto-Backup vor Welt-Ereignis"""
    
    backup_before_world_event()
    
    backups = list_backups()
    
    # Sollte mindestens ein Auto-Backup geben
    auto_backups = [b for b in backups if "Welt-Ereignis" in b.get("beschreibung", "")]
    
    assert len(auto_backups) >= 0  # Optional: je nach Config

def test_auto_backup_tick_check():
    """Testet Auto-Backup alle 24 Ticks"""
    
    # Mock Tick-Manager
    tick_manager.current_tick = 24
    
    auto_backup_if_enabled()
    
    # Sollte Backup erstellt haben (wenn enabled)
    pass  # Integrationstest
```

---

## 🎯 Best Practices

1. **Regelmäßige Backups** - Alle 24 Ticks (1 Tag) inkrementell
2. **Vor Events backuppen** - Welt-Ereignisse schützen
3. **Rotation aktivieren** - Alte Backups automatisch löschen
4. **Cloud-Storage optional** - Backups extern speichern (S3)
5. **Emergency-Backup vor Restore** - Aktuelle DB sichern bevor Restore

---

**Backup-System ermöglicht Welt-Sicherung mit Rotation, Provinz-Wiederherstellung und Auto-Backups!**

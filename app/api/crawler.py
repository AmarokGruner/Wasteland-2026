"""
Webcrawler Admin API

Endpoints for:
- Starting crawler runs manually
- Viewing crawl results and pending changes
- Approving/rejecting changes before DB sync
"""

import json
import logging
import threading
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from functools import lru_cache

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Security
from fastapi.security import HTTPBearer
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.models import get_db, User
from app.models import BuildingType, Resource, Vorkommen, TerrainType, AnimalTemplate, Article, UnitType, Regierungsform, CrawlSession, CrawlChange

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/crawler", tags=["Webcrawler"])

# ─── Admin Authorization Helper ───────────────────────────────────────────────

def require_admin(current_user: User = Depends(lambda: None)):
    """
    Dependency fÃ¼r Admin-Rolle-Validierung
    TODO: Mit echter Auth-Integration verbinden
    """
    # TemporÃ¤re LÃ¶sung: Immer True fÃ¼r Entwicklung
    # In Produktion: Token-Validierung und User-Rolle prÃ¼fen
    return True



# ─── Pydantic Models ─────────────────────────────────────────────

class CategoryResponse(BaseModel):
    name: str
    display_name: str
    table_name: str


class CrawlStartRequest(BaseModel):
    categories: Optional[List[str]] = None
    dry_run: bool = False
    verbose: bool = False


class CrawlStatusResponse(BaseModel):
    running: bool = False
    current_category: Optional[str] = None
    progress: Dict[str, Dict[str, Any]] = {}
    last_run: Optional[datetime] = None
    error: Optional[str] = None


class PendingChange(BaseModel):
    id: int
    category: str
    action: str  # 'INSERT', 'UPDATE', or 'REJECT'
    old_data: Optional[Dict[str, Any]] = None
    new_data: Dict[str, Any]
    changed_fields: List[str] = []
    detected_at: datetime


class CrawlResult(BaseModel):
    id: int
    category: str
    action: str
    record_id: int
    new_data: Dict[str, Any]
    changed_fields: List[str]
    approved: bool = False
    created_at: datetime


# ─── Global State ─────────────────────────────────────────────

# In-memory state for current crawl session
_crawl_state = {
    "running": False,
    "current_category": None,
    "progress": {},
    "last_run": None,
    "error": None,
    "results": []  # List of PendingChange objects
}

# Thread lock for state updates
_state_lock = threading.Lock()


# ─── Helper Functions ─────────────────────────────────────────────

def get_crawler_dir() -> Path:
    """Get the webcrawler directory path"""
    return Path(__file__).parent.parent.parent / "webcrawler"


def get_db_model_for_category(category: str):
    """Map category to DB model class"""
    mapping = {
        "gebaeude": BuildingType,
        "rohstoffe": Resource,
        "vorkommen": Vorkommen,
        "terrains": TerrainType,
        "lebewesen": AnimalTemplate,
        "artikel": Article,
        "einheiten": UnitType,
        "regierungen": Regierungsform
    }
    return mapping.get(category)


def get_table_name_for_category(category: str) -> str:
    """Map category to DB table name"""
    mapping = {
        "gebaeude": "gebaeude_typen",
        "rohstoffe": "ressourcen",
        "vorkommen": "vorkommen",
        "terrains": "terrain_typen",
        "lebewesen": "tier_vorlagen",
        "artikel": "artikel",
        "einheiten": "einheiten_typen",
        "regierungen": "regierungsformen"
    }
    return mapping.get(category, category)


def run_crawler(db: Session, categories: List[str] = None, dry_run: bool = False, verbose: bool = False):
    """Run the crawler in a background thread und speichert Ergebnisse in DB"""
    global _crawl_state

    crawler_dir = get_crawler_dir()
    cmd = [sys.executable, str(crawler_dir / "main.py")]

    if categories:
        cmd.extend(["--category"] + categories)
    if dry_run:
        cmd.append("--dry-run")
    if verbose:
        cmd.append("--verbose")

    # Startzeitts für Session
    started_at = datetime.now()
    session = None
    
    try:
        # Crawler-Session erstellen
        session = CrawlSession(
            status="running",
            categories=json.dumps(categories or []),
            dry_run=dry_run
        )
        db.add(session)
        db.commit()
        db.refresh(session)

        with _state_lock:
            _crawl_state["session_id"] = session.id
            _crawl_state["running"] = True
            _crawl_state["last_run"] = started_at
            _crawl_state["error"] = None
            _crawl_state["results"] = []

        # Crawler ausführen
        result = subprocess.run(
            cmd,
            cwd=crawler_dir,
            capture_output=True,
            text=True,
            timeout=300
        )

        changes_saved = 0
        output = result.stdout + result.stderr

        # Parse INSERT/UPDATE aus Output
        for line in output.split('\n'):
            if 'INSERT' in line or 'UPDATE' in line:
                parts = line.split()
                if len(parts) >= 4:
                    action = parts[0]
                    table = parts[1]
                    record_id_str = parts[3].split('=')[1] if '=' in parts[3] else '0'
                    
                    try:
                        record_id = int(record_id_str)
                    except ValueError:
                        record_id = 0

                    category = next((k for k, v in {
                        "gebaeude_typen": "gebaeude",
                        "ressourcen": "rohstoffe",
                        "vorkommen": "vorkommen",
                        "terrain_typen": "terrains",
                        "tier_vorlagen": "lebewesen",
                        "artikel": "artikel",
                        "einheiten_typen": "einheiten",
                        "regierungsformen": "regierungen"
                    }.items() if v == table or k == table), None)

                    if category:
                        # Dummy-Daten - echte Daten müssten vom Crawler kommen
                        new_data = {
                            "scraped_from": "webcrawler",
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        change = CrawlChange(
                            session_id=session.id,
                            category=category,
                            action=action,
                            record_id=record_id,
                            table_name=table,
                            new_data_json=json.dumps(new_data)
                        )
                        db.add(change)
                        changes_saved += 1
        
        db.commit()

        # Session abschließen
        session.status = "completed"
        session.completed_at = datetime.now()
        session.total_changes = changes_saved
        db.commit()

        with _state_lock:
            _crawl_state["running"] = False
            _crawl_state["total_changes"] = changes_saved
            
    except subprocess.TimeoutExpired:
        with _state_lock:
            _crawl_state["error"] = "Crawler timeout nach 5 Minuten"
        if session:
            session.status = "failed"
            session.error_message = "Timeout"
            db.commit()
    except Exception as e:
        logger.error(f"Crawler error: {e}")
        with _state_lock:
            _crawl_state["error"] = str(e)
        if session:
            session.status = "failed"
            session.error_message = str(e)
            db.commit()
    finally:
        if db:
            db.close()


# ─── API Endpoints ─────────────────────────────────────────────

@router.get("/categories")
async def get_supported_categories():
    """Get list of supported categories"""
    categories = [
        {"name": "gebaeude", "display_name": "Gebäude", "table_name": "gebaeude_typen"},
        {"name": "rohstoffe", "display_name": "Rohstoffe", "table_name": "ressourcen"},
        {"name": "vorkommen", "display_name": "Rohstoff-Vorkommen", "table_name": "vorkommen"},
        {"name": "terrains", "display_name": "Terrains", "table_name": "terrain_typen"},
        {"name": "lebewesen", "display_name": "Lebewesen", "table_name": "tier_vorlagen"},
        {"name": "artikel", "display_name": "Artikel/Items", "table_name": "artikel"},
        {"name": "einheiten", "display_name": "Einheiten", "table_name": "einheiten_typen"},
        {"name": "regierungen", "display_name": "Regierungsformen", "table_name": "regierungsformen"},
    ]
    return {"categories": categories}


@router.post("/start")
async def start_crawl(
    request: CrawlStartRequest,
    background_tasks: BackgroundTasks
):
    """Start a new crawl run"""
    global _crawl_state

    with _state_lock:
        if _crawl_state["running"]:
            raise HTTPException(status_code=409, detail="Crawl already running")

    # Start crawler in background thread
    background_tasks.add_task(
        run_crawler, db,
        request.categories,
        request.dry_run,
        request.verbose
    )

    return {"status": "started", "message": "Crawler starting in background"}


@router.get("/status")
async def get_crawl_status():
    """Get current crawl status"""
    with _state_lock:
        return {
            "running": _crawl_state["running"],
            "current_category": _crawl_state["current_category"],
            "progress": _crawl_state["progress"],
            "last_run": _crawl_state["last_run"],
            "error": _crawl_state["error"]
        }


@router.get("/pending")
async def get_pending_changes():
    """Get pending changes from last crawl"""
    with _state_lock:
        if not _crawl_state["results"]:
            return {"pending": []}
        
        # Convert to list of dicts for JSON serialization
        pending = []
        for result in _crawl_state["results"]:
            if isinstance(result, dict):
                pending.append({
                    "id": len(pending) + 1,
                    "category": result.get("category"),
                    "action": result.get("action"),
                    "record_id": result.get("record_id"),
                    "table": result.get("table"),
                    "detected_at": result.get("detected_at")
                })
            else:
                pending.append(result)
        
        return {"pending": pending, "total": len(pending)}


@router.post("/approve/{item_id}")
async def approve_change(item_id: int, db: Session = Depends(get_db)):
    """Approve a pending change and sync to database"""
    with _state_lock:
        result = next((r for r in _crawl_state["results"] if r.get("id") == item_id), None)
        if not result:
            raise HTTPException(status_code=404, detail="Change not found")

    # Perform sync (this would require actual DB access)
    # For now, return success
    return {"status": "approved", "message": f"Change {item_id} approved"}


@router.post("/reject/{item_id}")
async def reject_change(item_id: int):
    """Reject a pending change"""
    with _state_lock:
        result = next((r for r in _crawl_state["results"] if r.get("id") == item_id), None)
        if not result:
            raise HTTPException(status_code=404, detail="Change not found")
        
        # Remove from pending
        _crawl_state["results"] = [r for r in _crawl_state["results"] if r.get("id") != item_id]

    return {"status": "rejected", "message": f"Change {item_id} rejected"}


@router.post("/sync-all")
async def sync_all_pending(db: Session = Depends(get_db)):
    """Sync all pending changes to database"""
    with _state_lock:
        pending = _crawl_state["results"].copy()
        _crawl_state["results"] = []

    # Process each pending change
    synced = 0
    errors = []
    
    for item in pending:
        try:
            # Here we would sync each item to DB
            # This is a placeholder
            synced += 1
        except Exception as e:
            errors.append(str(e))

    return {
        "status": "completed",
        "synced": synced,
        "errors": errors
    }


@router.get("/history")
async def get_crawl_history(limit: int = 50):
    """Get crawl history"""
    # This would query a database table for crawl history
    # For now, return empty
    return {
        "history": []
    }


@router.delete("/results")
async def clear_results():
    """Clear all pending results"""
    with _state_lock:
        _crawl_state["results"] = []
    return {"status": "cleared", "message": "All pending results cleared"}

# ─── Export Endpoints ──────────────────────────────────────────────────────

@router.get("/export/csv")
async def export_pending_csv():
    """Export pending changes as CSV"""
    db = next(get_db())
    
    try:
        # Get pending changes for last completed session
        sessions = db.query(CrawlSession)            .filter(CrawlSession.status == "completed")            .order_by(CrawlSession.completed_at.desc())            .first()
        
        if not sessions:
            return {"csv": "", "message": "Keine abgeschlossenen Sessions gefunden"}
        
        changes = db.query(CrawlChange).filter(
            CrawlChange.session_id == sessions.id,
            ~CrawlChange.approved,
            ~CrawlChange.rejected
        ).all()
        
        if not changes:
            return {"csv": "", "message": "Keine ausstehenden Änderungen"}
        
        import csv
        import io
        import json
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow(["ID", "Session", "Kategorie", "Aktion", "Record_ID", "Tabelle", "Geänderte_Felder", "Erstellt"])
        
        for change in changes:
            writer.writerow([
                change.id,
                sessions.id,
                change.category,
                change.action,
                change.record_id,
                change.table_name,
                change.changed_fields,
                change.detected_at.isoformat() if change.detected_at else ""
            ])
        
        csv_content = output.getvalue()
        output.close()
        
        return {"csv": csv_content, "count": len(changes), "session_id": sessions.id}
    
    except Exception as e:
        logger.error(f"Export CSV error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/export/json")
async def export_pending_json():
    """Export pending changes as JSON"""
    db = next(get_db())
    
    try:
        sessions = db.query(CrawlSession)            .filter(CrawlSession.status == "completed")            .order_by(CrawlSession.completed_at.desc())            .first()
        
        if not sessions:
            return {"changes": [], "message": "Keine abgeschlossenen Sessions gefunden"}
        
        changes = db.query(CrawlChange).filter(
            CrawlChange.session_id == sessions.id,
            ~CrawlChange.approved,
            ~CrawlChange.rejected
        ).all()
        
        if not changes:
            return {"changes": [], "count": 0}
        
        result = {
            "session_id": sessions.id,
            "exported_at": datetime.now().isoformat(),
            "total": len(changes),
            "changes": []
        }
        
        for change in changes:
            result["changes"].append({
                "id": change.id,
                "category": change.category,
                "action": change.action,
                "record_id": change.record_id,
                "table_name": change.table_name,
                "old_data": change.old_data,
                "new_data": change.new_data,
                "changed_fields": change.changed_fields_list,
                "detected_at": change.detected_at.isoformat() if change.detected_at else None
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Export JSON error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


@router.get("/export/category/{category}")
async def export_by_category(category: str):
    """Export pending changes filtered by category"""
    db = next(get_db())
    
    try:
        changes = db.query(CrawlChange).filter(
            CrawlChange.category == category,
            ~CrawlChange.approved,
            ~CrawlChange.rejected
        ).all()
        
        return {
            "category": category,
            "count": len(changes),
            "changes": [
                {
                    "id": c.id,
                    "action": c.action,
                    "record_id": c.record_id,
                    "new_data": c.new_data
                }
                for c in changes
            ]
        }
    
    except Exception as e:
        logger.error(f"Export by category error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()


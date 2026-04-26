"""
Tests for the Sync Engine Module

Tests database synchronization logic (INSERT/UPDATE/SKIP).
"""

import pytest
from pathlib import Path

# Import the sync engine module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.sync_engine import SyncEngine, create_sync_engine
from app.models import BuildingType, Resource


class TestSyncEngine:
    """Tests for the SyncEngine class"""
    
    def test_create_sync_engine(self, db_session):
        """Test creating a sync engine instance"""
        engine = SyncEngine(db_session)
        
        assert engine is not None
        assert engine.session is db_session
    
    def test_create_sync_engine_via_factory(self, db_session):
        """Test creating a sync engine via factory function"""
        engine = create_sync_engine(db_session)
        
        assert engine is not None
        assert isinstance(engine, SyncEngine)


class TestSyncRecord:
    """Tests for the sync_record method"""
    
    def test_sync_insert_new_record(self, db_session):
        """Test inserting a new record"""
        engine = SyncEngine(db_session)
        
        # Prepare test data (new building)
        data = {
            "id": 999,
            "name": "Test Building",
            "kategorie": "Test",
        }
        
        # Sync the record (should INSERT)
        action, record_id = engine.sync_record(BuildingType, data, pk_field='id')
        
        assert action == 'INSERT'
        assert record_id == 999
    
    def test_sync_update_changed_record(self, db_session):
        """Test updating a changed record"""
        engine = SyncEngine(db_session)
        
        # First, insert a record
        initial_data = {
            "id": 1000,
            "name": "Original Name",
            "kategorie": "Original",
        }
        
        engine.sync_record(BuildingType, initial_data, pk_field='id')
        db_session.commit()
        
        # Now update with changed data
        updated_data = {
            "id": 1000,
            "name": "Updated Name",  # Changed
            "kategorie": "Original",
        }
        
        action, record_id = engine.sync_record(BuildingType, updated_data, pk_field='id')
        
        assert action == 'UPDATE'
        assert record_id == 1000
    
    def test_sync_skip_unchanged_record(self, db_session):
        """Test skipping an unchanged record"""
        engine = SyncEngine(db_session)
        
        # First, insert a record
        initial_data = {
            "id": 1001,
            "name": "Test Building",
            "kategorie": "Test",
        }
        
        engine.sync_record(BuildingType, initial_data, pk_field='id')
        db_session.commit()
        
        # Sync again with same data (should SKIP)
        action, record_id = engine.sync_record(BuildingType, initial_data, pk_field='id')
        
        assert action == 'SKIP'
        assert record_id == 1001
    
    def test_sync_record_without_id(self, db_session):
        """Test syncing a record without ID (should error)"""
        engine = SyncEngine(db_session)
        
        # Prepare data without ID
        data = {
            "name": "Test Building",
            "kategorie": "Test",
        }
        
        action, record_id = engine.sync_record(BuildingType, data, pk_field='id')
        
        assert action == 'ERROR'
        assert record_id is None


class TestCommitRollback:
    """Tests for transaction management"""
    
    def test_commit_transaction(self, db_session):
        """Test committing a transaction"""
        engine = SyncEngine(db_session)
        
        # Insert a record
        data = {
            "id": 2000,
            "name": "Test Building",
            "kategorie": "Test",
        }
        
        engine.sync_record(BuildingType, data, pk_field='id')
        
        # Commit (should not raise)
        engine.commit()
        
        # Verify record was saved
        result = db_session.query(BuildingType).filter_by(id=2000).first()
        assert result is not None
        assert result.name == "Test Building"
    
    def test_rollback_transaction(self, db_session):
        """Test rolling back a transaction"""
        engine = SyncEngine(db_session)
        
        # Insert a record but don't commit
        data = {
            "id": 2001,
            "name": "Rollback Test",
            "kategorie": "Test",
        }
        
        engine.sync_record(BuildingType, data, pk_field='id')
        
        # Rollback (should not raise)
        engine.rollback()
        
        # Verify record was NOT saved
        result = db_session.query(BuildingType).filter_by(id=2001).first()
        assert result is None


class TestSyncStatistics:
    """Tests for sync statistics tracking"""
    
    def test_sync_multiple_records(self, db_session):
        """Test syncing multiple records and tracking statistics"""
        engine = SyncEngine(db_session)
        
        # Insert multiple records
        records = [
            {"id": 3000, "name": "Building A", "kategorie": "Test"},
            {"id": 3001, "name": "Building B", "kategorie": "Test"},
            {"id": 3002, "name": "Building C", "kategorie": "Test"},
        ]
        
        stats = {"inserted": 0, "updated": 0, "skipped": 0}
        
        for record in records:
            action, _ = engine.sync_record(BuildingType, record, pk_field='id')
            
            if action == 'INSERT':
                stats["inserted"] += 1
            elif action == 'UPDATE':
                stats["updated"] += 1
            elif action == 'SKIP':
                stats["skipped"] += 1
        
        assert stats["inserted"] == 3
        assert stats["updated"] == 0
        assert stats["skipped"] == 0
        
        # Commit and sync again (should all be SKIP)
        db_session.commit()
        
        stats = {"inserted": 0, "updated": 0, "skipped": 0}
        
        for record in records:
            action, _ = engine.sync_record(BuildingType, record, pk_field='id')
            
            if action == 'INSERT':
                stats["inserted"] += 1
            elif action == 'UPDATE':
                stats["updated"] += 1
            elif action == 'SKIP':
                stats["skipped"] += 1
        
        assert stats["inserted"] == 0
        assert stats["updated"] == 0
        assert stats["skipped"] == 3

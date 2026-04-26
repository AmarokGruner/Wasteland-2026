"""
Database Sync Engine

Handles:
- Synchronizing scraped data with database
- INSERT/UPDATE/SKIP logic
- Transaction management
"""

import logging
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class SyncEngine:
    """Handles synchronization of scraped data with database"""
    
    def __init__(self, db_session: Session):
        self.session = db_session
    
    def sync_record(
        self,
        table_class: Any,
        data: Dict[str, Any],
        pk_field: str = "id"
    ) -> Tuple[str, Optional[int]]:
        """
        Synchronize a single record with the database.
        
        Args:
            table_class: SQLAlchemy model class for the table
            data: Dict with scraped data (must include primary key)
            pk_field: Name of the primary key field (default: 'id')
            
        Returns:
            Tuple of (action, record_id) where action is 'INSERT', 'UPDATE', or 'SKIP'
        """
        record_id = data.get(pk_field)
        
        if record_id is None:
            logger.warning(f"No primary key '{pk_field}' found in data")
            return ('ERROR', None)
        
        try:
            # 1. Check if record exists
            existing = self.session.query(table_class).filter_by(**{pk_field: record_id}).first()
            
            if not existing:
                # 2. INSERT new record
                logger.info(f"INSERT {table_class.__tablename__} id={record_id}")
                
                # Remove any fields that don't exist in the model
                valid_data = self._filter_valid_fields(table_class, data)
                
                new_record = table_class(**valid_data)
                self.session.add(new_record)
                
                return ('INSERT', record_id)
            
            # 3. Check for changes (UPDATE if changed)
            has_changes = False
            
            for key, value in data.items():
                if not hasattr(existing, key):
                    continue  # Skip unknown fields
                
                current_value = getattr(existing, key)
                
                if current_value != value:
                    logger.debug(f"Field '{key}' changed: {current_value} → {value}")
                    setattr(existing, key, value)
                    has_changes = True
            
            if has_changes:
                logger.info(f"UPDATE {table_class.__tablename__} id={record_id}")
                return ('UPDATE', record_id)
            
            # 4. SKIP (no changes)
            logger.debug(f"SKIP {table_class.__tablename__} id={record_id} (no changes)")
            return ('SKIP', record_id)
            
        except SQLAlchemyError as e:
            logger.error(f"Database error syncing {table_class.__tablename__} id={record_id}: {e}")
            self.session.rollback()
            return ('ERROR', record_id)
        except Exception as e:
            logger.error(f"Unexpected error syncing {table_class.__tablename__} id={record_id}: {e}")
            return ('ERROR', record_id)
    
    def _filter_valid_fields(self, table_class: Any, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out fields that don't exist in the model"""
        valid_fields = {column.name for column in table_class.__table__.columns}
        return {k: v for k, v in data.items() if k in valid_fields}
    
    def commit(self):
        """Commit the current transaction"""
        try:
            self.session.commit()
            logger.info("Transaction committed")
        except SQLAlchemyError as e:
            logger.error(f"Commit failed: {e}")
            self.session.rollback()
            raise
    
    def rollback(self):
        """Rollback the current transaction"""
        self.session.rollback()


def create_sync_engine(db_session: Session) -> SyncEngine:
    """Factory function to create a sync engine instance"""
    return SyncEngine(db_session)

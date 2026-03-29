"""
Database Connection Module

Handles:
- Database connection setup
- Session management
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Manages database connection and session"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        
        # Convert Windows path to forward slashes for SQLAlchemy
        db_path_normalized = str(db_path).replace("\\", "/")
        
        # Create engine
        self.engine = create_engine(
            f"sqlite:///{db_path_normalized}",
            connect_args={"check_same_thread": False},
            echo=False  # Set to True for SQL query logging
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        logger.info(f"Database connection established: {db_path}")
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                # Try to read from a table (if exists)
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                logger.info(f"Database has {len(tables)} tables: {', '.join(tables[:5])}...")
                return True
        except SQLAlchemyError as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_table_names(self) -> list:
        """Get list of all table names in the database"""
        try:
            inspector = inspect(self.engine)
            return inspector.get_table_names()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get table names: {e}")
            return []


def create_connection(db_path: str) -> DatabaseConnection:
    """Factory function to create a database connection"""
    return DatabaseConnection(db_path)

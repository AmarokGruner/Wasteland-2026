import os
import sys

# Add the current directory to sys.path to find the 'app' package
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine
from app.models import Base
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_tables():
    logger.info("Starting database table initialization...")
    try:
        # This will create all tables defined in models.py that don't exist yet
        Base.metadata.create_all(bind=engine)
        logger.info("Successfully initialized/updated database tables.")
    except Exception as e:
        logger.error(f"Error initializing tables: {e}")

if __name__ == "__main__":
    init_tables()

#!/usr/bin/env python3
"""
Webcrawler Main Entry Point

Usage:
    python main.py [--category CATEGORY] [--dry-run] [--verbose]
    
Examples:
    python main.py                          # Sync all categories
    python main.py --category gebaeude      # Sync only buildings
    python main.py --dry-run                # Preview changes without writing to DB
    python main.py --verbose                # Show detailed logs
"""

import argparse
import logging
import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add parent directory to path for imports
WEBCCRAWLER_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = WEBCCRAWLER_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

from webcrawler.config import (
    get_credentials,
    DB_PATH,
    BASE_URL,
    LOGIN_URL,
    LIST_URLS,
    DETAIL_URLS,
    REQUEST_DELAY,
    MAX_RETRIES,
    CACHE_DIR,
    LOGS_DIR,
    PARSER_MODULES,
    DB_MODELS,
)
from webcrawler.scraper.fetcher import create_session
from webcrawler.db.connection import create_connection


def setup_logging(verbose: bool = False, logs_dir: Path = None):
    """Configure logging for the application"""
    level = logging.DEBUG if verbose else logging.INFO
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # File handler (if logs_dir provided)
    handlers = [console_handler]
    if logs_dir:
        log_file = logs_dir / f"webcrawler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=level,
        handlers=handlers,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Webcrawler for v3.verbranntezone.ch",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Sync all categories
  python main.py --category gebaeude      # Sync only buildings
  python main.py --dry-run                # Preview changes without DB write
        """
    )
    
    parser.add_argument(
        '--category', '-c',
        type=str,
        nargs='+',
        choices=list(LIST_URLS.keys()),
        help="Categories to sync (default: all)"
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help="Preview changes without writing to database"
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Show detailed logging"
    )
    
    parser.add_argument(
        '--download-images', '-i',
        action='store_true',
        help="Download images for buildings, terrains, units, etc."
    )
    
    return parser.parse_args()


def import_parser_module(module_path: str, parser_func: str, list_func: str):
    """Dynamically import a parser module"""
    try:
        module = __import__(module_path, fromlist=[parser_func, list_func])
        
        parse_fn = getattr(module, parser_func)
        list_fn = getattr(module, list_func)
        
        return parse_fn, list_fn
        
    except ImportError as e:
        logging.error(f"Failed to import parser module {module_path}: {e}")
        return None, None


def fetch_and_parse_list(session, category: str, list_url: str) -> List[Dict[str, Any]]:
    """Fetch a list page and extract all item IDs"""
    logger = logging.getLogger(__name__)
    
    # Fetch the list page
    html = session.fetch(list_url)
    
    if not html:
        logger.error(f"Failed to fetch list page for {category}")
        return []
    
    # Save raw HTML to cache (for debugging)
    cache_file = CACHE_DIR / f"{category}_list.html"
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Get parser functions for this category
    module_path, parse_func, list_func = PARSER_MODULES[category]
    parse_fn, list_fn = import_parser_module(module_path, parse_func, list_func)
    
    if not list_fn:
        logger.error(f"No list parser found for {category}")
        return []
    
    # Parse the list and extract IDs
    items = list_fn(html)
    
    logger.info(f"Extracted {len(items)} {category} from list")
    return items


def fetch_and_parse_detail(session, category: str, item_id: int, detail_url: str) -> Dict[str, Any]:
    """Fetch a detail page and parse the data"""
    logger = logging.getLogger(__name__)
    
    # Fetch the detail page
    html = session.fetch(detail_url)
    
    if not html:
        logger.warning(f"Failed to fetch detail page for {category} id={item_id}")
        return {}
    
    # Save raw HTML to cache (for debugging)
    cache_file = CACHE_DIR / f"{category}_{item_id}.html"
    with open(cache_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    # Get parser functions for this category
    module_path, parse_func, list_func = PARSER_MODULES[category]
    parse_fn, _ = import_parser_module(module_path, parse_func, list_func)
    
    if not parse_fn:
        logger.error(f"No detail parser found for {category}")
        return {}
    
    # Parse the detail page
    data = parse_fn(html, item_id)
    
    logger.debug(f"Parsed {category} id={item_id}: {data.get('name', 'Unknown')}")
    return data


def sync_data(db_session, category: str, items: List[Dict[str, Any]], dry_run: bool = False) -> Dict[str, int]:
    """Synchronize scraped data with database"""
    logger = logging.getLogger(__name__)
    
    # Get DB model for this category
    module_path, model_name = DB_MODELS[category]
    
    try:
        # Import the model class
        module = __import__(module_path, fromlist=[model_name])
        model_class = getattr(module, model_name)
        
    except ImportError as e:
        logger.error(f"Failed to import DB model {model_name}: {e}")
        return {"error": 1}
    
    # Import sync engine
    from webcrawler.db.sync_engine import SyncEngine, create_sync_engine
    
    sync_engine = create_sync_engine(db_session)
    
    # Track statistics
    stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
    
    # Process each item
    for item in items:
        item_id = item.get('id')
        
        if not item_id:
            logger.warning(f"Item in {category} has no ID, skipping")
            stats["errors"] += 1
            continue
        
        # Sync the record
        action, _ = sync_engine.sync_record(model_class, item, pk_field='id')
        
        if action == 'INSERT':
            stats["inserted"] += 1
        elif action == 'UPDATE':
            stats["updated"] += 1
        elif action == 'SKIP':
            stats["skipped"] += 1
        else:
            stats["errors"] += 1
    
    # Commit the transaction (if not dry run)
    if not dry_run:
        try:
            sync_engine.commit()
            logger.info(f"Committed {category} sync: {stats['inserted']} inserted, {stats['updated']} updated, {stats['skipped']} skipped")
        except Exception as e:
            logger.error(f"Failed to commit {category} sync: {e}")
            stats["errors"] += len(items)
    else:
        logger.info(f"[DRY RUN] Would sync {category}: {stats['inserted']} inserted, {stats['updated']} updated, {stats['skipped']} skipped")
    
    return stats


def process_category(session, category: str, db_session, dry_run: bool = False, download_images: bool = False) -> Dict[str, int]:
    """Process a single category (fetch list, fetch details, sync)"""
    logger = logging.getLogger(__name__)
    
    logger.info(f"Processing category: {category}")
    
    # Get URLs for this category
    list_url = LIST_URLS[category]
    
    # Fetch and parse the list page
    items = fetch_and_parse_list(session, category, list_url)
    
    if not items:
        logger.warning(f"No items found for {category}, skipping")
        return {"inserted": 0, "updated": 0, "skipped": 0, "errors": 1}
    
    # Fetch and parse detail pages for each item
    parsed_items = []
    
    for item in items:
        item_id = item.get('id')
        
        if not item_id:
            continue
        
        # Build detail URL
        detail_url = DETAIL_URLS[category].format(id=item_id)
        
        # Fetch and parse the detail page
        data = fetch_and_parse_detail(session, category, item_id, detail_url)
        
        if data:
            parsed_items.append(data)
        
        # Respect rate limiting
        time.sleep(REQUEST_DELAY)
    
    logger.info(f"Fetched {len(parsed_items)} detail pages for {category}")
    
    # Sync with database
    stats = sync_data(db_session, category, parsed_items, dry_run)
    
    # Download images if requested
    if download_images and not dry_run and parsed_items:
        try:
            from webcrawler.scraper.image_downloader import download_category_images
            
            # Map category to image download folder name
            category_image_map = {
                'gebaeude': 'buildings',
                'terrains': 'terrains',
                'einheiten': 'units',
                'artikel': 'articles',
                'vorkommen': 'deposits',
                'regierungen': 'governments',
                'rohstoffe': 'resources',
                'lebewesen': 'animals',
            }
            
            image_category = category_image_map.get(category, category)
            image_stats = download_category_images(parsed_items, image_category)
            logger.info(f"Image download complete: {image_stats}")
        except Exception as e:
            logger.error(f"Error downloading images: {e}")
    
    return stats


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Setup logging
    setup_logging(verbose=args.verbose, logs_dir=LOGS_DIR)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("Webcrawler started")
    logger.info(f"Target: {BASE_URL}")
    logger.info(f"Dry run: {args.dry_run}")
    
    # Load configuration
    credentials = get_credentials()
    
    logger.info(f"Username: {credentials['username']}")
    
    # Determine categories to process
    if args.category:
        categories = args.category
    else:
        categories = list(LIST_URLS.keys())
    
    logger.info(f"Categories: {', '.join(categories)}")
    logger.info(f"Download images: {args.download_images}")
    
    # Create session and login
    logger.info("Creating web scraper session...")
    session = create_session(
        credentials['username'],
        credentials['password'],
        BASE_URL
    )
    
    # Attempt login
    logger.info(f"Attempting login to {LOGIN_URL}...")
    login_success = session.login(LOGIN_URL)
    
    if not login_success:
        logger.error("Login failed! Aborting.")
        session.close()
        return
    
    logger.info("Login successful!")
    
    # Create database connection
    logger.info(f"Connecting to database: {DB_PATH}...")
    
    if not DB_PATH.exists():
        logger.error(f"Database file not found: {DB_PATH}")
        session.close()
        return
    
    db_connection = create_connection(str(DB_PATH))
    
    # Test database connection
    if not db_connection.test_connection():
        logger.error("Database connection test failed! Aborting.")
        session.close()
        return
    
    logger.info("Database connection established!")
    
    # Get database session for syncing
    db_session = db_connection.get_session()
    
    try:
        # Process each category
        total_stats = {"inserted": 0, "updated": 0, "skipped": 0, "errors": 0}
        
        for category in categories:
            logger.info("-" * 40)
            
            # Process the category
            stats = process_category(session, category, db_session, args.dry_run, args.download_images)
            
            # Accumulate statistics
            for key, value in stats.items():
                total_stats[key] = total_stats.get(key, 0) + value
            
            # Small delay between categories
            time.sleep(REQUEST_DELAY * 2)
        
        # Final summary
        logger.info("=" * 60)
        logger.info("Webcrawl completed!")
        logger.info(f"Total: {total_stats['inserted']} inserted, {total_stats['updated']} updated, {total_stats['skipped']} skipped, {total_stats['errors']} errors")
        
    except Exception as e:
        logger.error(f"Error during webcrawl: {e}")
        
    finally:
        # Clean up resources
        db_session.close()
        session.close()
    
    logger.info("Resources cleaned up, exiting.")


if __name__ == "__main__":
    main()

"""
Image Downloader Module

Downloads images from the website and saves them locally.
"""

import logging
import requests
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

BASE_URL = 'https://v3.verbranntezone.ch'


def get_image_download_dir() -> Path:
    """Get or create the image download directory"""
    download_dir = Path(__file__).parent.parent / 'images'
    return download_dir


def download_image(url: str, category: str, item_id: int, item_name: str = None) -> Optional[Path]:
    """
    Download a single image and save it locally.
    
    Args:
        url: Full URL to the image
        category: Category name (e.g., 'buildings', 'terrains')
        item_id: Database ID of the item
        item_name: Optional name (used as fallback if URL doesn't have filename)
        
    Returns:
        Path to the downloaded file, or None if failed
    """
    if not url or not url.strip():
        return None
    
    # Create category subdirectory
    download_dir = get_image_download_dir() / category
    download_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract original filename from URL (e.g., g1_0r.png, t1a.gif)
    original_filename = Path(url).name
    if not original_filename or '.' not in original_filename:
        # Fallback to descriptive name
        if item_name:
            safe_name = item_name.replace(' ', '_').replace('/', '_')[:50]
            original_filename = f"{item_id}_{safe_name}.png"
        else:
            original_filename = f"{item_id}.png"
    
    # Create filename with ID prefix: [ID]_[original_name]
    filename = f"{item_id}_{original_filename}"
    filepath = download_dir / filename
    
    # Download the image
    try:
        response = requests.get(url, timeout=30, stream=True)
        if response.status_code == 200:
            filepath.write_bytes(response.content)
            logger.debug(f"Downloaded image: {filepath}")
            return filepath
        else:
            logger.warning(f"Failed to download {url}: HTTP {response.status_code}")
    except Exception as e:
        logger.warning(f"Error downloading {url}: {e}")
    
    return None


def download_category_images(items: list, category: str, image_field: str = 'bild_url') -> Dict[str, int]:
    """
    Download all images for a category.
    
    Args:
        items: List of parsed items with image URLs
        category: Category name for subdirectory
        image_field: Field name containing the image URL
        
    Returns:
        Dict with download statistics
    """
    stats = {'success': 0, 'failed': 0, 'skipped': 0}
    
    for item in items:
        item_id = item.get('id')
        item_name = item.get('name', '')
        image_url = item.get(image_field)
        
        if not image_url:
            stats['skipped'] += 1
            continue
        
        # Build full URL
        if image_url.startswith('http'):
            full_url = image_url
        else:
            full_url = BASE_URL + image_url
        
        # Download with descriptive name
        result = download_image(full_url, category, item_id, item_name)
        
        if result:
            stats['success'] += 1
        else:
            stats['failed'] += 1
    
    logger.info(f"Downloaded {category} images: {stats['success']} success, {stats['failed']} failed, {stats['skipped']} skipped")
    return stats


def download_item_images(item: Dict[str, Any], category: str) -> Dict[str, Path]:
    """
    Download all images for a single item.
    
    Args:
        item: Parsed item with image URLs
        category: Category name for subdirectory
        
    Returns:
        Dict mapping field names to downloaded file paths
    """
    downloaded = {}
    item_id = item.get('id')
    
    # Define image fields to check
    image_fields = [
        ('bild_url', 'bild'),
        ('icon_url', 'icon'),
        ('bild', 'bild'),
        ('icon', 'icon'),
    ]
    
    for field_name, prefix in image_fields:
        url = item.get(field_name)
        
        if not url:
            continue
        
        # Build full URL
        if url.startswith('http'):
            full_url = url
        else:
            full_url = BASE_URL + url
        
        # Download
        result = download_image(full_url, category, item_id, prefix)
        
        if result:
            downloaded[field_name] = result
    
    return downloaded

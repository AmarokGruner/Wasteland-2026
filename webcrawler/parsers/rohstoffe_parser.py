"""
Resources Parser Module

Parses resource detail pages from rohstoffvorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_rohstoffe(html: str, id: int) -> Dict[str, Any]:
    """
    Parse a resource detail page and extract structured data.
    
    Args:
        html: HTML content of the resource detail page
        id: Resource ID (for reference)
        
    Returns:
        Dict with extracted resource data mapped to DB fields
    """
    soup = BeautifulSoup(html, 'lxml')
    result = {"id": id}
    
    # Extract title from <div class='title'>
    title_div = soup.find('div', class_='title')
    if title_div:
        title_text = title_div.get_text(strip=True)
        # Format: "Bauholz (ID: 67)" or "Bauholz <i>(ID: 67)</i>"
        import re
        match = re.match(r'^(.+?)(?:\s*<i>)?\s*\(ID:\s*\d+\)', title_text)
        if match:
            result["name"] = match.group(1).strip()
        else:
            result["name"] = title_text
    
    # Try to find the main table with resource details
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                
                # Map German keys to DB fields
                mapped = _map_key_to_field(key, value)
                
                if mapped:
                    result.update(mapped)
    
    # Also check for div-based layouts
    detail_divs = soup.find_all('div', class_=lambda x: x and ('detail' in x.lower() or 'info' in x.lower()))
    
    for div in detail_divs:
        label = div.find('span', class_='label') or div.find('strong')
        value_elem = div.find('span', class_='value') or div
        
        if label and value_elem:
            key = label.get_text(strip=True)
            value = value_elem.get_text(strip=True)
            
            mapped = _map_key_to_field(key, value)
            
            if mapped:
                result.update(mapped)
    
    logger.debug(f"Parsed resource id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Direct string mappings
    if key_lower == "typ":
        return {"typ": value}
    
    # Numeric fields
    if key_lower == "produktionswert":
        return {"wert": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    # Transport space fields (not directly mapped to DB, store as info)
    if "platzverbrauch" in key_lower:
        return {"transport_info": value}
    
    # Building references (producing/consuming)
    if "folgende gebäude produzieren" in key_lower:
        return {"producing_buildings": value}
    
    if "folgende gebäude verbrauchen" in key_lower:
        return {"consuming_buildings": value}
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    # Verbrauch info
    if "verbrauch" in key_lower:
        return {"verbrauch_info": value}
    
    return None


def parse_rohstoffe_list(html: str) -> list:
    """
    Parse the resource list page and extract all resource IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each resource
    """
    soup = BeautifulSoup(html, 'lxml')
    resources = []
    
    # Look for table with resource list
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        
        # Skip header row
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            
            if len(cells) >= 2:
                # Try to extract ID from link or first column
                id_cell = cells[0]
                link = id_cell.find('a', href=True)
                
                if link:
                    # Extract ID from href (e.g., "rohstoffvorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        resource_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        resources.append({
                            "id": resource_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(resources)} resources in list")
    return resources

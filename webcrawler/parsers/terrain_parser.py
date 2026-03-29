"""
Terrain Parser Module

Parses terrain detail pages from terrainvorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_terrain(html: str, id: int) -> Dict[str, Any]:
    """
    Parse a terrain detail page and extract structured data.
    
    Args:
        html: HTML content of the terrain detail page
        id: Terrain ID (for reference)
        
    Returns:
        Dict with extracted terrain data mapped to DB fields
    """
    soup = BeautifulSoup(html, 'lxml')
    result = {"id": id}
    
    # Extract title from <div class='title'>
    # Format: "Grasland <i>(ID: 1)</i>"
    title_div = soup.find('div', class_='title')
    if title_div:
        title_text = title_div.get_text(strip=True)
        import re
        match = re.match(r'^(.+?)(?:\s*<i>)?\s*\(ID:\s*\d+\)', title_text)
        if match:
            result["name"] = match.group(1).strip()
        else:
            result["name"] = title_text
    
    # Extract map image
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                img = cells[1].find('img')
                if img and 'src' in img.attrs:
                    if 'Kartenbild' in key:
                        result["bild_url"] = img['src']
    
    # Try to find the main table with terrain details
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
    
    logger.debug(f"Parsed terrain id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Direct string mappings
    if key_lower == "name" or key_lower == "typ":
        return {"name": value}
    
    # Start territory
    if "startgebiet" in key_lower:
        return {"startgebiet": 1 if "JA" in value.upper() else 0}
    
    # Playable terrain (yes/no)
    if "spielbar" in key_lower or "bespielbar" in key_lower:
        return {"playable": 1 if "JA" in value.upper() else 0}
    
    # Color (for map rendering)
    if "farbe" in key_lower or "color" in key_lower:
        return {"color": value}
    
    # Icon (for UI)
    if "icon" in key_lower or "symbol" in key_lower:
        return {"icon": value}
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    # Rain probability and amount (for terrain_configs)
    if "regenwarscheinlichkeit" in key_lower:
        return {"regen_pct": int(value.replace("%", "")) if value else 30}
    
    if "regenmenge" in key_lower:
        return {"rain_amount": int(value) if value.isdigit() else 0}
    
    # Moisture (for province climate)
    if "feuchtigkeit" in key_lower or "bodenfeuchte" in key_lower:
        return {"average_moisture": float(value.replace(",", ".")) if value else 50.0}
    
    # Groundwater (for terrain_configs)
    if "grundwasser" in key_lower:
        return {"grundwasserspiegel": float(value.replace(",", ".")) if value else 50.0}
    
    # Next terrain (for terrain succession)
    if "nächstes terrain" in key_lower or "folge-terrain" in key_lower:
        return {"next_terrain_id": value}  # May need to extract ID
    
    # Yields (holz, stein, eisen)
    if "holz" in key_lower and "ertrag" in key_lower:
        return {"holz_yield": float(value.replace("%", "")) / 100 if value else 1.0}
    if "stein" in key_lower and "ertrag" in key_lower:
        return {"stein_yield": float(value.replace("%", "")) / 100 if value else 1.0}
    if "eisen" in key_lower and "ertrag" in key_lower:
        return {"eisen_yield": float(value.replace("%", "")) / 100 if value else 1.0}
    
    return None


def parse_terrain_list(html: str) -> list:
    """
    Parse the terrain list page and extract all terrain IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each terrain
    """
    soup = BeautifulSoup(html, 'lxml')
    terrains = []
    
    # Look for table with terrain list
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
                    # Extract ID from href (e.g., "terrainvorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        terrain_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        terrains.append({
                            "id": terrain_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(terrains)} terrains in list")
    return terrains

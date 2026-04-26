"""
Einheiten (Units/Military) Parser Module

Parses unit detail pages from einheitenvorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_einheiten(html: str, id: int) -> Dict[str, Any]:
    """
    Parse a unit detail page and extract structured data.
    
    Args:
        html: HTML content of the unit detail page
        id: Unit ID (for reference)
        
    Returns:
        Dict with extracted unit data mapped to DB fields
    """
    soup = BeautifulSoup(html, 'lxml')
    result = {"id": id}
    
    # Extract title from <div class='title'>
    # Format: "Name <i>(ID: 1)</i>"
    title_div = soup.find('div', class_='title')
    if title_div:
        title_text = title_div.get_text(strip=True)
        import re
        match = re.match(r'^(.+?)(?:\s*<i>)?\s*\(ID:\s*\d+\)', title_text)
        if match:
            result["name"] = match.group(1).strip()
        else:
            result["name"] = title_text
    
    # Extract unit image if present
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                img = cells[1].find('img')
                if img and 'src' in img.attrs:
                    if 'bild' in key.lower() or 'symbol' in key.lower():
                        result["bild_url"] = img['src']
    
    # Try to find the main table with unit details
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
    
    logger.debug(f"Parsed einheit id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Direct string mappings
    if key_lower == "name" or key_lower == "bezeichnung":
        return {"name": value}
    
    # Species (for species-specific units)
    if "spezies" in key_lower:
        return {"spezies": value}
    
    # Unit class (infantry, cavalry, etc.)
    if "einheitenklasse" in key_lower or "klasse" in key_lower:
        return {"einheitenklasse": value}
    
    # Category (military, civilian, etc.)
    if "kategorie" in key_lower:
        return {"kategorie": value}
    
    # Cost fields
    if "kosten in mips" in key_lower or "mips_kosten" in key_lower:
        return {"kosten_mips": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    if "kosten in münzen" in key_lower or "münzkosten" in key_lower:
        return {"kosten_muenzen": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    # Movement speed (march speed)
    if "zugsgeschwindigkeit" in key_lower or "geschwindigkeit" in key_lower:
        return {"zugsgeschwindigkeit": float(value.replace(",", ".")) if value else 1.0}
    
    # Transport capacity (how much the unit can carry)
    if "transportkapazität" in key_lower or "transportkapazitaet" in key_lower:
        return {"transport_kapazitaet": int(value) if value.isdigit() else 1}
    
    # Unit size (how much space it takes in transport)
    if "einheitengröße" in key_lower or "einheitengroesse" in key_lower:
        return {"einheitengroesse": int(value) if value.isdigit() else 1}
    
    # Module (for modular units)
    if "module" in key_lower or "modul" in key_lower:
        return {"module": value}  # JSON string
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    # Combat stats (if present)
    if "angriffswert" in key_lower or "stärke" in key_lower:
        return {"combat_stats": value}  # JSON string
    
    if "verteidigungswert" in key_lower:
        return {"defense_stats": value}  # JSON string
    
    return None


def parse_einheiten_list(html: str) -> list:
    """
    Parse the einheiten list page and extract all unit IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each unit
    """
    soup = BeautifulSoup(html, 'lxml')
    einheiten = []
    
    # Look for table with unit list
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
                    # Extract ID from href (e.g., "einheitenvorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        einheit_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        einheiten.append({
                            "id": einheit_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(einheiten)} einheiten in list")
    return einheiten

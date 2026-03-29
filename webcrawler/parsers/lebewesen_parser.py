"""
Lebewesen (Animals/Creatures) Parser Module

Parses animal detail pages from tiervorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_lebewesen(html: str, id: int) -> Dict[str, Any]:
    """
    Parse an animal detail page and extract structured data.
    
    Args:
        html: HTML content of the animal detail page
        id: Animal ID (for reference)
        
    Returns:
        Dict with extracted animal data mapped to DB fields
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
    
    # Extract animal image if present
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
    
    # Try to find the main table with animal details
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
    
    logger.debug(f"Parsed lebewesen id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Direct string mappings
    if key_lower == "name" or key_lower == "typ":
        return {"name": value}
    
    # Species/type of animal
    if "spezies" in key_lower or "tierart" in key_lower:
        return {"species": value}
    
    # Category (wild/domestic)
    if "kategorie" in key_lower:
        return {"category": value}
    
    # Feed requirements
    if "futter" in key_lower or "nahrung" in key_lower:
        return {"feed_info": value}
    
    # Feed amount per day
    if "futterbedarf" in key_lower or "futtermenge" in key_lower:
        return {"feed_amount": float(value.replace(",", ".")) if value else 1.0}
    
    # Breeding output (what the animal produces)
    if "zuchtprodukt" in key_lower or "zuchtergebnis" in key_lower:
        return {"breed_output": value}
    
    # Breeding rate
    if "zuchtrate" in key_lower or "vermehrungsrate" in key_lower:
        return {"breed_rate": float(value.replace(",", ".")) if value else 0.1}
    
    # Diet type (herbivore/carnivore)
    if "pflanzenfresser" in key_lower:
        return {"is_pflanzenfresser": 1 if "JA" in value.upper() else 0}
    
    if "fleischfresser" in key_lower:
        return {"is_pflanzenfresser": 0 if "JA" in value.upper() else 1}
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    # Habitat info
    if "lebensraum" in key_lower or "habitat" in key_lower:
        return {"habitat": value}
    
    # Capture chance (for wild animals)
    if "fangchance" in key_lower:
        return {"capture_chance": float(value.replace(",", ".")) if value else 0.0}
    
    return None


def parse_lebewesen_list(html: str) -> list:
    """
    Parse the lebewesen list page and extract all animal IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each animal
    """
    soup = BeautifulSoup(html, 'lxml')
    lebewesen = []
    
    # Look for table with animal list
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
                    # Extract ID from href (e.g., "tiervorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        lebewesen_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        lebewesen.append({
                            "id": lebewesen_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(lebewesen)} lebewesen in list")
    return lebewesen

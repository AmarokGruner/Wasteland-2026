"""
Artikel (Articles/Items) Parser Module

Parses article detail pages from artikelvorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_artikel(html: str, id: int) -> Dict[str, Any]:
    """
    Parse an article detail page and extract structured data.
    
    Args:
        html: HTML content of the article detail page
        id: Article ID (for reference)
        
    Returns:
        Dict with extracted article data mapped to DB fields
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
    
    # Extract article image if present
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
    
    # Try to find the main table with article details
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
    
    logger.debug(f"Parsed artikel id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Direct string mappings
    if key_lower == "name" or key_lower == "bezeichnung":
        return {"name": value}
    
    # Category
    if key_lower == "kategorie":
        return {"kategorie": value}
    
    # Cost fields
    if "preis in mips" in key_lower or "mips_kosten" in key_lower:
        return {"preis_mips": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    if "preis in münzen" in key_lower or "münzkosten" in key_lower:
        return {"preis_muenzen": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    # Species (for species-specific items)
    if "spezies" in key_lower:
        return {"spezies": value}
    
    # Unit text (description of the unit)
    if "einheitentext" in key_lower or "einheitenbeschreibung" in key_lower:
        return {"einheittext": value}
    
    # Module type (for modular items)
    if "modultyp" in key_lower:
        return {"modultyp": value}
    
    # Affiliation (what this belongs to)
    if "zugehörig" in key_lower or "zugehoerig" in key_lower:
        return {"zugehoerig": value}
    
    # Building type (if article is building-related)
    if "bautyp" in key_lower:
        return {"bautyp": value}
    
    # Production points
    if "produktionspunkte" in key_lower or "produktionspunkte" in key_lower:
        return {"produktionspunkte": int(value) if value.isdigit() else 0}
    
    # Raw material requirements
    if "rohstoffbedarf" in key_lower:
        return {"rohstoffbedarf": value}  # JSON string
    
    # Module size
    if "modulgröße" in key_lower or "modulgroesse" in key_lower:
        return {"modulgroesse": int(value) if value.isdigit() else 0}
    
    # Effects on unit values
    if "auswirkung" in key_lower and "einheitenwerte" in key_lower:
        return {"auswirkung_einheitenwerte": value}  # JSON string
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    # Transport capacity (for trade items)
    if "transportkapazität" in key_lower or "transportkapazitaet" in key_lower:
        return {"transportkapazitaet": value}  # JSON string
    
    # Space requirements
    if "platzbedarf" in key_lower:
        return {"platzbedarf": value}  # JSON string
    
    return None


def parse_artikel_list(html: str) -> list:
    """
    Parse the artikel list page and extract all article IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each article
    """
    soup = BeautifulSoup(html, 'lxml')
    artikel = []
    
    # Look for table with article list
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
                    # Extract ID from href (e.g., "artikelvorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        artikel_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        artikel.append({
                            "id": artikel_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(artikel)} artikel in list")
    return artikel

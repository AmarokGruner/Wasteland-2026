"""
Vorkommen (Resource Deposits) Parser Module

Parses vorkommen detail pages from vorkommenvorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_vorkommen(html: str, id: int) -> Dict[str, Any]:
    """
    Parse a vorkommen detail page and extract structured data.
    
    Args:
        html: HTML content of the vorkommen detail page
        id: Vorkommen ID (for reference)
        
    Returns:
        Dict with extracted vorkommen data mapped to DB fields
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
    
    # Extract vorkommen image if present
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
    
    # Try to find the main table with vorkommen details
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
    
    logger.debug(f"Parsed vorkommen id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Direct string mappings
    if key_lower == "typ":
        return {"typ": value}
    
    # Numeric fields
    if key_lower == "techlevel":
        return {"tech": int(value) if value.isdigit() else 0}
    
    if key_lower == "suchkosten":
        return {"suchkosten": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    # Find probability (complex - usually a table or list of terrains)
    if "findwahrscheinlichkeit" in key_lower or "fundchance" in key_lower:
        return {"findwahrscheinlichkeit": value}  # Store as string/JSON
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    # Terrain references (terrains where this deposit can be found)
    if "terrain" in key_lower:
        return {"terrain_info": value}
    
    return None


def parse_vorkommen_list(html: str) -> list:
    """
    Parse the vorkommen list page and extract all vorkommen IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each vorkommen
    """
    soup = BeautifulSoup(html, 'lxml')
    vorkommen = []
    
    # Look for table with vorkommen list
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
                    # Extract ID from href (e.g., "vorkommenvorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        vorkommen_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        vorkommen.append({
                            "id": vorkommen_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(vorkommen)} vorkommen in list")
    return vorkommen

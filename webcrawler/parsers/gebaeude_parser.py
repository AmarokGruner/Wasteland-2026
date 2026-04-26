"""
Gebäude Parser Module

Parses building detail pages from gebaeudevorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_gebaeude(html: str, id: int) -> Dict[str, Any]:
    """
    Parse a building detail page and extract structured data.
    
    Args:
        html: HTML content of the building detail page
        id: Building ID (for reference)
        
    Returns:
        Dict with extracted building data mapped to DB fields
    """
    soup = BeautifulSoup(html, 'lxml')
    result = {"id": id}
    
    # Extract title from <div class='title'>
    # Format: "Bunker <i>(ID: 1)</i>"
    title_div = soup.find('div', class_='title')
    if title_div:
        title_text = title_div.get_text(strip=True)
        import re
        match = re.match(r'^(.+?)(?:\s*<i>)?\s*\(ID:\s*\d+\)', title_text)
        if match:
            result["name"] = match.group(1).strip()
        else:
            result["name"] = title_text
    
    # Extract images/logos
    # Gebäudesymbol (icon/symbol) and Gebäudebild (building image)
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                key = cells[0].get_text(strip=True)
                img = cells[1].find('img')
                if img and 'src' in img.attrs:
                    src = img['src']
                    # More precise matching - check exact strings
                    if 'Gebäudesymbol' in key or 'symbol' in key.lower():
                        if 'icon_url' not in result:
                            result["icon_url"] = src
                    elif 'Gebäudebild' in key or 'bild' in key.lower():
                        if 'bild_url' not in result:
                            result["bild_url"] = src
    
    # Try to find the main table with building details
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
    
    logger.debug(f"Parsed building id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    # Direct mappings
    mappings = {
        "name": ("name", value),
        "kategorie": ("kategorie", value),
        "bautyp": ("bautyp",),
        "ausbaubar": ("ausbaubar", 1 if "JA" in value.upper() else 0),
        "unique(einmalig)": ("unique_gebaeude", 1 if "JA" in value.upper() else 0),
        "nur an küste": ("nur_kueste", 1 if "JA" in value.upper() else 0),
        "ist feld": ("ist_feld", 1 if "JA" in value.upper() else 0),
        "benötigtes techlevel": ("tech_level", int(value) if value.isdigit() else 0),
        "baukosten in mips": ("baukosten_mips", int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0),
        "arbeiter": ("arbeiter", int(value) if value.isdigit() else 0),
        "wohnraum": ("wohnraum", int(value) if value.isdigit() else 0),
        "lagerraumkapazität": ("lagerkapazitaet", int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0),
        "beschreibung": ("beschreibung", value),
    }
    
    # Check for exact match
    key_lower = key.lower()
    
    if key_lower in mappings:
        field_info = mappings[key_lower]
        
        if len(field_info) == 2:
            # Simple string field
            return {field_info[0]: value}
        elif len(field_info) == 3:
            # Field with transformation
            field_name = field_info[0]
            
            if field_name == "ausbaubar":
                return {"ausbaubar": 1 if "JA" in value.upper() else 0}
            elif field_name == "unique_gebaeude":
                return {"unique_gebaeude": 1 if "JA" in value.upper() else 0}
            elif field_name == "nur_kueste":
                return {"nur_kueste": 1 if "JA" in value.upper() else 0}
            elif field_name == "ist_feld":
                return {"ist_feld": 1 if "JA" in value.upper() else 0}
            elif field_name == "tech_level":
                return {"tech_level": int(value) if value.isdigit() else 0}
            elif field_name == "baukosten_mips":
                return {"baukosten_mips": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
            elif field_name == "arbeiter":
                return {"arbeiter": int(value) if value.isdigit() else 0}
            elif field_name == "wohnraum":
                return {"wohnraum": int(value) if value.isdigit() else 0}
            elif field_name == "lagerkapazitaet":
                return {"lagerkapazitaet": int(value.replace(",", "")) if value.replace(",", "").isdigit() else 0}
    
    # Special handling for complex fields (JSON)
    if "effektivität bei terrain" in key_lower:
        # This would need special parsing of the terrain effectiveness table
        return {"terrain_effektivitaet": value}  # Store as string for now
    
    if "rohstoffbedarf bau" in key_lower:
        return {"rohstoffbedarf_bau": value}  # Will be parsed as JSON later
    
    if "rohstoffproduktion im betrieb" in key_lower:
        return {"produktion": value}  # Will be parsed as JSON later
    
    if "gebäudespezifische eigenschaften" in key_lower:
        return {"spezial_eigenschaften": value}  # Will be parsed as JSON later
    
    if "energiebedarf" in key_lower:
        # Add to spezial_eigenschaften or separate field
        return {"energiebedarf": value}
    
    return None


def parse_gebaeude_list(html: str) -> list:
    """
    Parse the building list page and extract all building IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each building
    """
    soup = BeautifulSoup(html, 'lxml')
    buildings = []
    
    # Look for table with building list
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
                    # Extract ID from href (e.g., "gebaeudevorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        building_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        buildings.append({
                            "id": building_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(buildings)} buildings in list")
    return buildings

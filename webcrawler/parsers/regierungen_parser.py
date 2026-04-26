"""
Regierungsformen (Government Forms) Parser Module

Parses government detail pages from regierungvorschau.php?id={id}
"""

import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def parse_regierung(html: str, id: int) -> Dict[str, Any]:
    """
    Parse a government detail page and extract structured data.
    
    Args:
        html: HTML content of the government detail page
        id: Government ID (for reference)
        
    Returns:
        Dict with extracted government data mapped to DB fields
    """
    soup = BeautifulSoup(html, 'lxml')
    result = {"id": id}
    
    # Extract title from <div class='title'>
    # Format: "Stamm <i>(ID: 1)</i>"
    title_div = soup.find('div', class_='title')
    if title_div:
        title_text = title_div.get_text(strip=True)
        import re
        match = re.match(r'^(.+?)(?:\s*<i>)?\s*\(ID:\s*\d+\)', title_text)
        if match:
            result["name"] = match.group(1).strip()
        else:
            result["name"] = title_text
    
    # Try to find the main table with government details
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
    
    logger.debug(f"Parsed regierung id={id}: {result.get('name', 'Unknown')}")
    return result


def _map_key_to_field(key: str, value: str) -> Optional[Dict[str, Any]]:
    """Map German UI labels to database fields"""
    
    key_lower = key.lower()
    
    # Helper to extract percentage from value like "(100%)" or "normal (100%)"
    def extract_percent(val: str) -> float:
        if not val:
            return 1.0
        # Look for percentage in parentheses
        import re
        match = re.search(r'\((\d+)%\)', val)
        if match:
            return int(match.group(1)) / 100.0
        # Try direct percentage
        match = re.search(r'(\d+)%', val)
        if match:
            return int(match.group(1)) / 100.0
        return 1.0
    
    # Helper to safely convert to float
    def safe_float(val: str) -> float:
        if not val:
            return 1.0
        # Try to extract number from string
        import re
        match = re.search(r'(\d+(?:[.,]\d+)?)', val.replace(',', '.'))
        if match:
            return float(match.group(1))
        return 1.0
    
    # Direct string mappings
    if key_lower == "name" or key_lower == "bezeichnung":
        return {"name": value}
    
    # Government form type (e.g., "Demokratie", "Diktatur")
    if "formtyp" in key_lower or "regierungsform" in key_lower:
        return {"formtyp": value}
    
    # Tech level requirement
    if "techlevel" in key_lower or "benötigtes techlevel" in key_lower or "verfügbar ab techlevel" in key_lower:
        return {"techlevel": int(value) if value.isdigit() else 0}
    
    # Required government seat level
    if "ausbauwert regierungssitz" in key_lower or "regierungssitz" in key_lower:
        return {"ausbauwert_regierungssitz": int(value) if value.isdigit() else 0}
    
    # Cultural spread (Kulturverbreitung) - value has "(100%)" format
    if "kulturverbreitung" in key_lower:
        return {"kulturverbreitung": extract_percent(value)}
    
    # Base morale (Grundmoral) - value has "(50 Moralmittelwert)" format
    if "grundmoral" in key_lower:
        return {"grundmoral": 50}  # Default value
    
    # Research progress bonus (Forschungsfortschritt) - value has "(100%)" format
    if "forschungsfortschritt" in key_lower or "forschung" in key_lower:
        return {"forschungsfortschritt": extract_percent(value)}
    
    # Productivity bonus (Produktivität)
    if "produktivitaet" in key_lower or "produktivit" in key_lower:
        return {"produktivitaet": extract_percent(value)}
    
    # Growth bonus (Wachstum)
    if "wachstum" in key_lower:
        return {"wachstum": extract_percent(value)}
    
    # Finance bonus (Finanzen)
    if "finanzen" in key_lower:
        return {"finanzen": extract_percent(value)}
    
    # Security bonus (Sicherheit)
    if "sicherheit" in key_lower or "innere sicherheit" in key_lower:
        return {"sicherheit": extract_percent(value)}
    
    # Morale penalty for foreign armies (Moralmalus Armee außen)
    if "moralmalus" in key_lower and "armee" in key_lower:
        return {"moralmalus_armee_aussen": safe_float(value)}
    
    # Distance penalty (Entfernungsmalus)
    if "entfernungsmalus" in key_lower:
        return {"entfernungsmalus": extract_percent(value)}
    
    # Food requirements (Lebensmittelbedarf)
    if "lebensmittelbedarf" in key_lower:
        return {"lebensmittelbedarf": extract_percent(value)}
    
    # Consumer goods requirements (Verbrauchsgutbedarf)
    if "verbrauchsgutbedarf" in key_lower:
        return {"lebensmittelbedarf": extract_percent(value)}  # Note: Website uses same field
    
    # Strike tendency (Streikbereitschaft)
    if "streikbereitschaft" in key_lower:
        return {"streikbereitschaft": extract_percent(value)}
    
    # Emigration tendency (Auswanderbereitschaft)
    if "auswanderbereitschaft" in key_lower:
        return {"auswanderbereitschaft": extract_percent(value)}
    
    # Militia bonus (Milizen)
    if "milizen" in key_lower:
        return {"milizen": extract_percent(value)}
    
    # Foreign culture loss (Fremdkultur-Verlust)
    if "fremdkultur" in key_lower:
        return {"fremdkultur_verlust": int(value) if value.isdigit() else 0}
    
    # Uprising tendency (Aufstand)
    if "aufstand" in key_lower:
        return {"aufstand": 1 if "JA" in value.upper() else 0}
    
    # War possibility (Krieg möglich)
    if "krieg" in key_lower and "möglich" in key_lower:
        return {"krieg_moeglich": 1 if "JA" in value.upper() else 0}
    
    # Province count before penalty (Provinzanzahl bis Malus)
    if "prov" in key_lower and "malus" in key_lower:
        return {"provinzanzahl_bis_malus": int(value) if value.isdigit() else 2}
    
    # Penalty description (Malus-Beschreibung)
    if "malus" in key_lower and "beschreibung" in key_lower:
        return {"malus_beschreibung": value}
    
    # Bonuses (JSON string)
    if "boni" in key_lower:
        return {"boni": value}  # JSON string
    
    # Requirements (JSON string)
    if "voraussetzungen" in key_lower:
        return {"voraussetzungen": value}  # JSON string
    
    # Description
    if key_lower == "beschreibung":
        return {"beschreibung": value}
    
    return None


def parse_regierung_list(html: str) -> list:
    """
    Parse the regierung list page and extract all government IDs.
    
    Args:
        html: HTML content of the list page
        
    Returns:
        List of dicts with 'id' and basic info for each government
    """
    soup = BeautifulSoup(html, 'lxml')
    regierungen = []
    
    # Look for table with government list
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
                    # Extract ID from href (e.g., "regierungvorschau.php?id=123")
                    href = link['href']
                    
                    # Parse ID from URL
                    import re
                    match = re.search(r'id=(\d+)', href)
                    
                    if match:
                        regierung_id = int(match.group(1))
                        name = link.get_text(strip=True) or cells[1].get_text(strip=True)
                        
                        regierungen.append({
                            "id": regierung_id,
                            "name": name,
                            "href": href
                        })
    
    logger.info(f"Found {len(regierungen)} regierungen in list")
    return regierungen

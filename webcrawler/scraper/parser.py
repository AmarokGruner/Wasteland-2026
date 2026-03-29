"""
HTML Parser Module

Handles:
- Parsing HTML pages with BeautifulSoup
- Extracting structured data from tables and forms
"""

import logging
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


class HTMLParser:
    """Generic HTML parser with common extraction methods"""
    
    def __init__(self, html: str):
        self.html = html
        self.soup = BeautifulSoup(html, 'lxml')
    
    def extract_title(self) -> Optional[str]:
        """Extract page title from <div class='title'>, <h1> or <title> tag"""
        # Try <div class='title'> first (real website format)
        title_div = self.soup.find('div', class_='title')
        if title_div:
            return title_div.get_text(strip=True)
        
        # Try <h1> next
        h1 = self.soup.find('h1')
        if h1:
            return h1.get_text(strip=True)
        
        # Fallback to <title> tag
        title = self.soup.find('title')
        if title:
            return title.get_text(strip=True)
        
        return None
    
    def extract_table_data(self, table_selector: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract data from HTML table.
        
        Args:
            table_selector: CSS selector for the table (optional)
            
        Returns:
            List of dicts with column headers as keys and cell values
        """
        # Find the table
        if table_selector:
            table = self.soup.select_one(table_selector)
        else:
            # Try common patterns
            table = (
                self.soup.find('table', {'class': 'details'}) or
                self.soup.find('table', {'class': 'data'}) or
                self.soup.find('table', {'id': 'content'}) or
                self.soup.find('table')
            )
        
        if not table:
            logger.warning("No table found in HTML")
            return []
        
        # Extract rows
        rows = table.find_all('tr')
        if not rows:
            return []
        
        # Check if first row is header
        headers = self._extract_headers(rows[0])
        
        # Extract data rows
        data = []
        for row in rows[1:]:
            cells = row.find_all(['td', 'th'])
            if headers and len(cells) == len(headers):
                row_data = {headers[i]: self._clean_cell(cell) for i, cell in enumerate(cells)}
                data.append(row_data)
            elif len(cells) >= 2:
                # Key-value pattern (common in detail pages)
                key = self._clean_cell(cells[0])
                value = self._clean_cell(cells[1]) if len(cells) > 1 else ""
                data.append({key: value})
        
        return data
    
    def extract_key_value_pairs(self, container_selector: Optional[str] = None) -> Dict[str, str]:
        """
        Extract key-value pairs from a container (div, table, etc.)
        
        Args:
            container_selector: CSS selector for the container (optional)
            
        Returns:
            Dict with keys and values as strings
        """
        result = {}
        
        if container_selector:
            container = self.soup.select_one(container_selector)
            if not container:
                logger.warning(f"Container not found: {container_selector}")
                return result
        else:
            container = self.soup
        
        # Try table-based key-value extraction
        tables = container.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = self._clean_cell(cells[0])
                    value = self._clean_cell(cells[1])
                    result[key] = value
        
        # Try definition list (dl, dt, dd) pattern
        dl_lists = container.find_all('dl')
        for dl in dl_lists:
            dts = dl.find_all('dt')
            dds = dl.find_all('dd')
            for i, dt in enumerate(dts):
                if i < len(dds):
                    key = self._clean_cell(dt)
                    value = self._clean_cell(dds[i])
                    result[key] = value
        
        return result
    
    def _extract_headers(self, header_row: Tag) -> List[str]:
        """Extract column headers from a table row"""
        cells = header_row.find_all(['th', 'td'])
        return [self._clean_cell(cell) for cell in cells]
    
    def _clean_cell(self, cell: Tag) -> str:
        """Clean and normalize cell content"""
        # Remove script and style tags
        for tag in cell.find_all(['script', 'style']):
            tag.decompose()
        
        # Get text and normalize whitespace
        text = cell.get_text(separator=' ', strip=True)
        
        # Remove extra whitespace
        return ' '.join(text.split())
    
    def extract_links(self, pattern: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Extract links from the page.
        
        Args:
            pattern: Optional substring to filter links (e.g., "vorschau.php")
            
        Returns:
            List of dicts with 'text' and 'href' keys
        """
        links = self.soup.find_all('a', href=True)
        result = []
        
        for link in links:
            href = link['href']
            text = link.get_text(strip=True)
            
            # Apply filter if pattern provided
            if pattern and pattern not in href:
                continue
            
            result.append({'text': text, 'href': href})
        
        return result
    
    def find_element_by_class(self, class_name: str) -> Optional[Tag]:
        """Find first element with given CSS class"""
        return self.soup.find(class_=class_name)
    
    def find_element_by_id(self, element_id: str) -> Optional[Tag]:
        """Find element by ID"""
        return self.soup.find(id=element_id)


def parse_html(html: str) -> HTMLParser:
    """Factory function to create a parser instance"""
    return HTMLParser(html)

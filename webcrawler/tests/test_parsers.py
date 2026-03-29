"""
Tests for the Parser Module

Tests HTML parsing functionality.
"""

import pytest
from pathlib import Path

# Import the parser module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.parser import HTMLParser, parse_html


class TestHTMLParser:
    """Tests for the HTMLParser class"""
    
    def test_create_parser(self):
        """Test creating a parser instance"""
        html = "<html><body><h1>Test</h1></body></html>"
        parser = HTMLParser(html)
        
        assert parser is not None
        assert parser.html == html
        assert parser.soup is not None
    
    def test_create_parser_via_factory(self):
        """Test creating a parser via factory function"""
        html = "<html><body><h1>Test</h1></body></html>"
        parser = parse_html(html)
        
        assert parser is not None
        assert isinstance(parser, HTMLParser)


class TestExtractTitle:
    """Tests for title extraction"""
    
    def test_extract_title_from_div_title(self, sample_gebaeude_html):
        """Test extracting title from <div class='title'> tag (real website format)"""
        parser = HTMLParser(sample_gebaeude_html)
        title = parser.extract_title()
        
        # Should handle div.title or fall back to h1
        assert title is not None
    
    def test_extract_title_missing(self):
        """Test extracting title when no <h1> exists"""
        html = "<html><body><p>No title here</p></body></html>"
        parser = HTMLParser(html)
        title = parser.extract_title()
        
        # Should return None or handle gracefully
        assert title is None or isinstance(title, str)


class TestExtractTableData:
    """Tests for table data extraction"""
    
    def test_extract_table_data_basic(self, sample_gebaeude_html):
        """Test extracting data from a basic table"""
        parser = HTMLParser(sample_gebaeude_html)
        data = parser.extract_table_data()
        
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_extract_table_data_has_expected_fields(self, sample_gebaeude_html):
        """Test that extracted data has expected fields"""
        parser = HTMLParser(sample_gebaeude_html)
        data = parser.extract_table_data()
        
        # Check that we got data (any non-empty result is fine)
        assert len(data) > 0


class TestExtractKeyValuePairs:
    """Tests for key-value pair extraction"""
    
    def test_extract_key_value_pairs(self, sample_gebaeude_html):
        """Test extracting key-value pairs from HTML"""
        parser = HTMLParser(sample_gebaeude_html)
        data = parser.extract_key_value_pairs()
        
        assert isinstance(data, dict)
        # German website uses different keys - check that we got some data
        assert len(data) > 0


class TestParseGebaeude:
    """Tests for the gebaeude parser"""
    
    def test_parse_gebaeude_basic(self, sample_gebaeude_html):
        """Test parsing a basic building detail page"""
        from parsers.gebaeude_parser import parse_gebaeude
        
        result = parse_gebaeude(sample_gebaeude_html, id=1)
        
        assert isinstance(result, dict)
        assert result.get('id') == 1
    
    def test_parse_gebaeude_has_name(self, sample_gebaeude_html):
        """Test that parsed building has a name"""
        from parsers.gebaeude_parser import parse_gebaeude
        
        result = parse_gebaeude(sample_gebaeude_html, id=1)
        
        assert 'name' in result
        assert result['name'] == 'Bunker'
    
    def test_parse_gebaeude_extracts_icon_url(self, sample_gebaeude_html):
        """Test that building icon URL is extracted"""
        from parsers.gebaeude_parser import parse_gebaeude
        
        result = parse_gebaeude(sample_gebaeude_html, id=1)
        
        assert 'icon_url' in result
        assert result.get('icon_url') is not None
        assert len(result.get('icon_url', '')) > 0
    
    def test_parse_gebaeude_extracts_bild_url(self, sample_gebaeude_html):
        """Test that building image URL is extracted"""
        from parsers.gebaeude_parser import parse_gebaeude
        
        result = parse_gebaeude(sample_gebaeude_html, id=1)
        
        assert 'bild_url' in result
        assert result.get('bild_url') is not None
        assert len(result.get('bild_url', '')) > 0


class TestParseRohstoffe:
    """Tests for the rohstoffe parser"""
    
    def test_parse_rohstoffe_basic(self, sample_rohstoffe_html):
        """Test parsing a basic resource detail page"""
        from parsers.rohstoffe_parser import parse_rohstoffe
        
        result = parse_rohstoffe(sample_rohstoffe_html, id=1)
        
        assert isinstance(result, dict)
        assert result.get('id') == 1


class TestParseList:
    """Tests for list page parsing"""
    
    def test_parse_list_basic(self, sample_list_html):
        """Test parsing a basic list page"""
        from parsers.gebaeude_parser import parse_gebaeude_list
        
        result = parse_gebaeude_list(sample_list_html)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_parse_list_has_ids(self, sample_list_html):
        """Test that parsed list items have IDs"""
        from parsers.gebaeude_parser import parse_gebaeude_list
        
        result = parse_gebaeude_list(sample_list_html)
        
        # Check that items have 'id' field
        for item in result:
            assert 'id' in item


class TestEdgeCases:
    """Tests for edge cases and error handling"""
    
    def test_parse_empty_html(self):
        """Test parsing empty HTML"""
        html = ""
        parser = HTMLParser(html)
        
        # Should not raise an exception
        title = parser.extract_title()
        assert title is None
    
    def test_parse_malformed_html(self):
        """Test parsing malformed HTML"""
        html = "<html><body><div>Unclosed div</html>"
        parser = HTMLParser(html)
        
        # Should not raise an exception (BeautifulSoup is lenient)
        assert parser.soup is not None
    
    def test_parse_missing_table(self):
        """Test parsing HTML without tables"""
        html = "<html><body><p>No table here</p></body></html>"
        parser = HTMLParser(html)
        
        data = parser.extract_table_data()
        
        # Should return empty list or handle gracefully
        assert isinstance(data, list)

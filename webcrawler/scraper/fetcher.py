"""
HTTP Fetcher Module

Handles:
- Session management with cookies
- Login to the website
- Fetching pages with retry logic
"""

import time
import logging
from typing import Optional, Dict
from requests import Session
from requests.exceptions import RequestException, Timeout, HTTPError

logger = logging.getLogger(__name__)


class WebScraperSession:
    """Custom session with login and retry logic"""
    
    def __init__(self, username: str, password: str, base_url: str):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.session = Session()
        self.is_logged_in = False
        
    def login(self, login_url: str) -> bool:
        """
        Attempt to log in to the website.
        
        Args:
            login_url: URL of the login page/form
            
        Returns:
            bool: True if login successful, False otherwise
        """
        logger.info(f"Attempting login with username: {self.username}")
        
        try:
            # First, get the login page to extract any CSRF tokens
            response = self.session.get(login_url, timeout=10)
            response.raise_for_status()
            
            # Try to find CSRF token in the form (if present)
            csrf_token = self._extract_csrf_token(response.text)
            
            # Prepare login data with correct field names for v3.verbranntezone.ch
            login_data = {
                "nick": self.username,
                "passwort": self.password,
            }
            
            # Add CSRF token if found
            if csrf_token:
                login_data["csrf_token"] = csrf_token
                logger.debug("CSRF token found and included in login request")
            
            # Submit login form
            response = self.session.post(
                login_url,
                data=login_data,
                timeout=10,
                allow_redirects=True
            )
            
            # Check if login was successful
            # Common patterns: redirect to dashboard, success message, no error message
            if response.status_code == 200 or response.status_code == 302:
                self.is_logged_in = True
                logger.info("Login successful")
                return True
            
            # Check for error messages in response
            if self._contains_login_error(response.text):
                logger.error("Login failed: Invalid credentials or login error")
                return False
            
            # Fallback: assume success if we get a valid response
            logger.warning("Login status unclear, assuming success")
            self.is_logged_in = True
            return True
            
        except Timeout:
            logger.error("Login request timed out")
            return False
        except RequestException as e:
            logger.error(f"Login request failed: {e}")
            return False
    
    def _extract_csrf_token(self, html: str) -> Optional[str]:
        """Extract CSRF token from HTML form"""
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Look for common CSRF token field names
            token_field_names = ["csrf_token", "csrf", "_token", "authenticity_token"]
            
            for field_name in token_field_names:
                token_input = soup.find('input', {'name': field_name})
                if token_input and token_input.get('value'):
                    return token_input['value']
            
            # Also check for meta tags (some frameworks use this)
            meta_token = soup.find('meta', {'name': 'csrf-token'})
            if meta_token and meta_token.get('content'):
                return meta_token['content']
            
            return None
            
        except Exception as e:
            logger.debug(f"Failed to extract CSRF token: {e}")
            return None
    
    def _contains_login_error(self, html: str) -> bool:
        """Check if HTML contains common login error messages"""
        error_patterns = [
            "invalid credentials",
            "wrong password",
            "user not found",
            "login failed",
            "authentication error",
            "falscher benutzername",
            "falsches passwort",
            "anmeldung fehlgeschlagen"
        ]
        
        html_lower = html.lower()
        return any(pattern in html_lower for pattern in error_patterns)
    
    def fetch(self, url: str, max_retries: int = 3, delay: float = 1.0) -> Optional[str]:
        """
        Fetch a URL with retry logic.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            delay: Base delay between retries (seconds)
            
        Returns:
            str: HTML content if successful, None otherwise
        """
        for attempt in range(max_retries):
            try:
                logger.debug(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                return response.text
                
            except Timeout:
                logger.warning(f"Timeout fetching {url}, retrying in {delay ** (attempt + 1):.1f}s")
                time.sleep(delay ** (attempt + 1))  # Exponential backoff
                
            except HTTPError as e:
                if e.response.status_code == 403:
                    logger.error(f"Access denied (403) for {url}")
                    return None
                elif e.response.status_code == 404:
                    logger.warning(f"Page not found (404): {url}")
                    return None
                elif e.response.status_code >= 500:
                    logger.warning(f"Server error ({e.response.status_code}), retrying")
                    time.sleep(delay ** (attempt + 1))
                else:
                    logger.error(f"HTTP error {e.response.status_code} for {url}")
                    return None
                    
            except RequestException as e:
                logger.error(f"Request failed: {e}")
                if attempt == max_retries - 1:
                    return None
                time.sleep(delay ** (attempt + 1))
        
        logger.error(f"Failed to fetch {url} after {max_retries} attempts")
        return None
    
    def close(self):
        """Close the session"""
        self.session.close()


def create_session(username: str, password: str, base_url: str) -> WebScraperSession:
    """Factory function to create a configured session"""
    return WebScraperSession(username, password, base_url)

"""
Azure DevOps REST API client with robust error handling and retry logic.

This module provides a production-ready HTTP client for interacting with
Azure DevOps REST APIs, including automatic retries, timeout handling,
and proper error propagation.

Research Note: The client is designed to be extensible for future ML-based
error classification and adaptive retry strategies.
"""
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import Optional, Dict, Any
from src.ado.auth import build_auth_header
from src.config.settings import settings


class ADOClient:
    """
    Reusable Azure DevOps API client with PAT authentication, retry logic,
    and comprehensive error handling.
    
    Features:
    - Automatic retry on transient failures (5xx, network errors)
    - Configurable timeouts
    - Session-based connection pooling
    - Proper authentication header management
    """
    
    # Retry configuration: 3 attempts with exponential backoff
    MAX_RETRIES = 3
    BACKOFF_FACTOR = 0.5
    TIMEOUT = 30  # seconds
    
    def __init__(self, org: Optional[str] = None, project: Optional[str] = None, pat: Optional[str] = None):
        """
        Initialize ADO client.
        
        Args:
            org: Azure DevOps organization (defaults to settings.ado_org)
            project: Azure DevOps project (defaults to settings.ado_project)
            pat: Personal Access Token (defaults to settings.ado_pat)
        """
        self.org = org or settings.ado_org
        self.project = project or settings.ado_project
        self.pat = pat or settings.ado_pat
        
        self.base_url = f"https://dev.azure.com/{self.org}/{self.project}"
        self.session = self._create_session()
    
    def _create_session(self) -> requests.Session:
        """
        Create a requests Session with retry strategy and authentication.
        
        Returns:
            Configured requests.Session instance
        """
        session = requests.Session()
        
        # Configure retry strategy for transient failures
        retry_strategy = Retry(
            total=self.MAX_RETRIES,
            backoff_factor=self.BACKOFF_FACTOR,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST", "PATCH", "PUT", "DELETE"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set authentication and default headers
        session.headers.update({
            "Authorization": build_auth_header(self.pat),
            "Content-Type": "application/json",
            "Accept": "application/json"
        })
        
        return session
    
    def _url(self, path: str) -> str:
        """
        Build full URL from API path.
        
        Args:
            path: API endpoint path (e.g., "_apis/wit/workitems")
            
        Returns:
            Full URL including base URL
        """
        # Handle both absolute and relative paths
        if path.startswith("https://"):
            return path
        return f"{self.base_url.rstrip('/')}/{path.lstrip('/')}"
    
    def get(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Execute GET request with retry and timeout.
        
        Args:
            path: API endpoint path
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: For HTTP error responses
            requests.Timeout: For timeout errors
            requests.RequestException: For other request errors
        """
        url = self._url(path)
        try:
            response = self.session.get(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RetryError as e:
            raise requests.exceptions.RequestException(
                f"Max retries exceeded for GET {url}: {e}"
            ) from e
    
    def post(self, path: str, json: Optional[Dict[str, Any] | list] = None, 
             params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Execute POST request with retry and timeout.
        
        Args:
            path: API endpoint path
            json: JSON payload (dict or list)
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: For HTTP error responses
            requests.Timeout: For timeout errors
            requests.RequestException: For other request errors
        """
        url = self._url(path)
        try:
            # ADO requires application/json-patch+json for JSON Patch operations (when json is a list)
            headers = {}
            if json is not None and isinstance(json, list):
                headers['Content-Type'] = 'application/json-patch+json'
            
            response = self.session.post(url, json=json, params=params, headers=headers, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RetryError as e:
            raise requests.exceptions.RequestException(
                f"Max retries exceeded for POST {url}: {e}"
            ) from e
    
    def patch(self, path: str, json: list, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Execute PATCH request with retry and timeout.
        
        PATCH requests in ADO use JSON Patch format (RFC 6902).
        
        Args:
            path: API endpoint path
            json: JSON Patch document (list of operations)
            params: Optional query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: For HTTP error responses
            requests.Timeout: For timeout errors
            requests.RequestException: For other request errors
        """
        url = self._url(path)
        # ADO requires specific content type for PATCH operations
        headers = {"Content-Type": "application/json-patch+json"}
        try:
            response = self.session.patch(url, json=json, headers=headers, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RetryError as e:
            raise requests.exceptions.RequestException(
                f"Max retries exceeded for PATCH {url}: {e}"
            ) from e
    
    def put(self, path: str, json: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Execute PUT request with retry and timeout.
        
        Args:
            path: API endpoint path
            json: JSON payload
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: For HTTP error responses
            requests.Timeout: For timeout errors
            requests.RequestException: For other request errors
        """
        url = self._url(path)
        try:
            response = self.session.put(url, json=json, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RetryError as e:
            raise requests.exceptions.RequestException(
                f"Max retries exceeded for PUT {url}: {e}"
            ) from e
    
    def delete(self, path: str, params: Optional[Dict[str, Any]] = None) -> requests.Response:
        """
        Execute DELETE request with retry and timeout.
        
        Args:
            path: API endpoint path
            params: Query parameters
            
        Returns:
            Response object
            
        Raises:
            requests.HTTPError: For HTTP error responses
            requests.Timeout: For timeout errors
            requests.RequestException: For other request errors
        """
        url = self._url(path)
        try:
            response = self.session.delete(url, params=params, timeout=self.TIMEOUT)
            response.raise_for_status()
            return response
        except requests.exceptions.RetryError as e:
            raise requests.exceptions.RequestException(
                f"Max retries exceeded for DELETE {url}: {e}"
            ) from e


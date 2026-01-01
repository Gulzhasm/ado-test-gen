"""
Authentication utilities for Azure DevOps API.

This module handles PAT (Personal Access Token) authentication by
constructing the proper Authorization header format required by ADO REST APIs.
"""
import base64


def build_auth_header(pat: str) -> str:
    """
    Builds a Base64-encoded Authorization header for Azure DevOps PAT authentication.
    
    ADO requires Basic authentication with PAT where:
    - Username is empty string
    - Password is the PAT token
    - Format: Authorization: Basic <base64(:PAT)>
    
    Args:
        pat: Personal Access Token string
        
    Returns:
        Authorization header value (e.g., "Basic <encoded_token>")
        
    Example:
        >>> build_auth_header("abc123")
        'Basic OmFiYzEyMw=='
    """
    # ADO PAT format: base64(":" + PAT)
    token = f":{pat}".encode("utf-8")
    encoded_token = base64.b64encode(token).decode("utf-8")
    return f"Basic {encoded_token}"


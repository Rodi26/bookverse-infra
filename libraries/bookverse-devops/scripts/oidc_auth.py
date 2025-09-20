#!/usr/bin/env python3
"""
OIDC Authentication Utility for BookVerse Services

This module provides utilities for OIDC token exchange with JFrog, 
implementing proper OIDC authentication for JFrog access.

Usage:
    from oidc_auth import get_jfrog_token
    
    token = get_jfrog_token()
    # Use token for JFrog API calls
"""

import json
import os
import urllib.request
import urllib.parse
from typing import Optional, Dict, Any


def get_github_oidc_token(audience: str) -> Optional[str]:
    """
    Get GitHub OIDC ID token using GitHub Actions environment variables.
    
    Args:
        audience: The audience for the OIDC token (typically JFrog URL)
        
    Returns:
        GitHub OIDC ID token or None if not available
    """
    request_url = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL")
    request_token = os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN")
    
    if not request_url or not request_token:
        return None
    
    try:
        url = f"{request_url}&audience={urllib.parse.quote(audience)}"
        req = urllib.request.Request(url, headers={
            "Authorization": f"Bearer {request_token}"
        })
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("value")
    except Exception:
        return None


def exchange_oidc_for_jfrog_token(
    github_token: str, 
    jfrog_url: str, 
    provider_name: str,
    project_key: Optional[str] = None
) -> Optional[str]:
    """
    Exchange GitHub OIDC token for JFrog access token.
    
    Args:
        github_token: GitHub OIDC ID token
        jfrog_url: JFrog platform URL
        provider_name: OIDC provider name (e.g., bookverse-web-github)
        project_key: Optional project key for additional context
        
    Returns:
        JFrog access token or None if exchange fails
    """
    try:
        payload = {
            "grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
            "subject_token_type": "urn:ietf:params:oauth:token-type:id_token",
            "subject_token": github_token,
            "provider_name": provider_name
        }
        
        if project_key:
            payload["project_key"] = project_key
        
        # Add GitHub Actions context if available
        if os.environ.get("GITHUB_JOB"):
            payload.update({
                "job_id": os.environ.get("GITHUB_JOB", ""),
                "run_id": os.environ.get("GITHUB_RUN_ID", ""),
                "repo": f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}",
                "revision": os.environ.get("GITHUB_SHA", ""),
                "branch": os.environ.get("GITHUB_REF_NAME", "")
            })
        
        url = f"{jfrog_url.rstrip('/')}/access/api/v1/oidc/token"
        data = json.dumps(payload).encode("utf-8")
        
        req = urllib.request.Request(
            url, 
            data=data, 
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as resp:
            response_data = json.loads(resp.read().decode("utf-8"))
            return response_data.get("access_token")
    except Exception:
        return None


def get_jfrog_token(
    jfrog_url: Optional[str] = None,
    provider_name: Optional[str] = None,
    project_key: Optional[str] = None,
    fallback_env_var: Optional[str] = None
) -> Optional[str]:
    """
    Get JFrog access token using OIDC authentication with fallback to environment variable.
    
    This function implements the OIDC authentication flow:
    1. Try to get token from JF_OIDC_TOKEN environment variable
    2. Try OIDC token exchange if in GitHub Actions environment
    3. Fall back to custom environment variable if specified
    
    Args:
        jfrog_url: JFrog platform URL (defaults to JFROG_URL env var)
        provider_name: OIDC provider name (auto-detected from repository if not provided)
        project_key: Project key (defaults to PROJECT_KEY env var)
        fallback_env_var: Environment variable to use as fallback (optional)
        
    Returns:
        JFrog access token or None if not available
    """
    # First, try the standard OIDC token environment variable
    token = os.environ.get("JF_OIDC_TOKEN", "").strip()
    if token:
        return token
    
    # Try OIDC token exchange if we're in GitHub Actions
    if os.environ.get("ACTIONS_ID_TOKEN_REQUEST_URL") and os.environ.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN"):
        jfrog_url = jfrog_url or os.environ.get("JFROG_URL", "").strip()
        if not jfrog_url:
            # Try alternative environment variable names
            jfrog_url = os.environ.get("APPTRUST_BASE_URL", "").strip()
            if jfrog_url and "/apptrust/api/v1" in jfrog_url:
                # Extract base URL from AppTrust API URL
                jfrog_url = jfrog_url.replace("/apptrust/api/v1", "")
        
        if jfrog_url:
            # Auto-detect provider name from repository if not provided
            if not provider_name:
                repo_name = os.environ.get("GITHUB_REPOSITORY", "").split("/")[-1]
                if repo_name.startswith("bookverse-"):
                    service_name = repo_name.replace("bookverse-", "")
                    provider_name = f"bookverse-{service_name}-github"
            
            if provider_name:
                github_token = get_github_oidc_token(jfrog_url)
                if github_token:
                    project_key = project_key or os.environ.get("PROJECT_KEY", "bookverse")
                    token = exchange_oidc_for_jfrog_token(
                        github_token, jfrog_url, provider_name, project_key
                    )
                    if token:
                        return token
    
    # Fall back to custom environment variable if specified
    if fallback_env_var:
        return os.environ.get(fallback_env_var, "").strip() or None
    
    return None


def get_apptrust_base_url() -> Optional[str]:
    """
    Get AppTrust base URL from environment variables.
    
    Returns:
        AppTrust base URL or None if not available
    """
    # Try the standard AppTrust base URL first
    base_url = os.environ.get("APPTRUST_BASE_URL", "").strip()
    if base_url:
        return base_url
    
    # Try to construct from JFrog URL
    jfrog_url = os.environ.get("JFROG_URL", "").strip()
    if jfrog_url:
        return f"{jfrog_url.rstrip('/')}/apptrust/api/v1"
    
    return None


def setup_environment_variables():
    """
    Set up environment variables for OIDC authentication.
    
    This function ensures that JF_OIDC_TOKEN is available for OIDC authentication.
    """
    token = get_jfrog_token()
    if token:
        os.environ["JF_OIDC_TOKEN"] = token
        # Token is now available as JF_OIDC_TOKEN


if __name__ == "__main__":
    # Command-line usage for testing
    import sys
    
    token = get_jfrog_token()
    if token:
        print(f"Successfully obtained JFrog token: {token[:10]}...")
        sys.exit(0)
    else:
        print("Failed to obtain JFrog token", file=sys.stderr)
        sys.exit(1)

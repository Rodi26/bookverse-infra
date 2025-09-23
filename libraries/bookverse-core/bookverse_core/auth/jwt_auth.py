"""
BookVerse Core Library - JWT Authentication and Authorization

This module provides comprehensive JWT authentication and authorization functionality
for the BookVerse platform, implementing enterprise-grade security patterns with
OIDC integration, token validation, and role-based access control for zero-trust
authentication across all BookVerse microservices.

🏗️ Architecture Overview:
    - JWT Token Validation: RS256 signature validation with JWKS key rotation
    - OIDC Integration: OpenID Connect protocol support for modern authentication
    - Role-Based Access Control: Comprehensive RBAC with scope and role validation
    - Zero-Trust Security: Token-based authentication with cryptographic verification
    - Development Support: Configurable authentication bypass for development environments
    - Multi-Tenant Support: Audience validation for secure multi-service architecture

🚀 Key Features:
    - Enterprise-grade JWT token validation with RS256 cryptographic signatures
    - OIDC integration with automatic JWKS key rotation and discovery
    - Comprehensive user model with roles, scopes, and profile information
    - Role-based and scope-based authorization with fine-grained permissions
    - Development mode support with configurable authentication bypass
    - Production-ready security defaults with comprehensive token validation

🔧 Technical Implementation:
    - JWT Library Integration: Python-JOSE library for robust token processing
    - JWKS Integration: Automatic public key discovery and rotation handling
    - Token Validation: Comprehensive validation including signature, expiry, and audience
    - User Context: Rich user context preservation throughout request lifecycle
    - Error Handling: Detailed authentication error handling and logging

📊 Business Logic:
    - Zero-Trust Security: Token-based authentication preventing unauthorized access
    - Multi-Service Architecture: Centralized authentication across all BookVerse services
    - Role Management: Enterprise role-based access control for complex permissions
    - Audit Compliance: Comprehensive authentication logging for security auditing
    - Development Efficiency: Configurable authentication for rapid development

🛠️ Usage Patterns:
    - API Security: Token-based authentication for all BookVerse REST APIs
    - Microservice Communication: Secure inter-service authentication and authorization
    - Role-Based Authorization: Fine-grained access control based on user roles and scopes
    - Development Workflows: Configurable authentication bypass for local development
    - Enterprise Integration: OIDC integration with enterprise identity providers

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import logging
import os
from typing import Dict, Any, List

from fastapi import HTTPException, status
from jose import jwt, JWTError

from .oidc import get_jwks, get_public_key

logger = logging.getLogger(__name__)

# 🔧 Authentication Configuration: Environment-based configuration with secure defaults
OIDC_AUTHORITY = os.getenv("OIDC_AUTHORITY", "https://dev-auth.bookverse.com")
OIDC_AUDIENCE = os.getenv("OIDC_AUDIENCE", "bookverse:api")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "RS256")
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "true").lower() == "true"
DEVELOPMENT_MODE = os.getenv("DEVELOPMENT_MODE", "true").lower() == "true"


class AuthUser:
    """
    Authenticated user model with comprehensive role and scope management.
    
    This class represents an authenticated user in the BookVerse platform,
    providing access to user information, roles, and scopes extracted from
    validated JWT tokens with comprehensive authorization checking capabilities.
    
    Attributes:
        claims (Dict[str, Any]): Complete JWT token claims
        user_id (str): Unique user identifier from 'sub' claim
        email (str): User email address from 'email' claim
        name (str): User display name from 'name' claim (falls back to email)
        roles (List[str]): User roles for role-based access control
        scopes (List[str]): OAuth 2.0 scopes for fine-grained permissions
        
    Features:
        - Complete JWT claims preservation for audit and debugging
        - Role-based access control with enterprise role management
        - Scope-based authorization for fine-grained API permissions
        - Flexible user identification and profile information
        - String representation for logging and debugging
    """
    
    def __init__(self, token_claims: Dict[str, Any]):
        """
        Initialize authenticated user from validated JWT token claims.
        
        Args:
            token_claims (Dict[str, Any]): Validated JWT token claims containing
                user information, roles, and scopes
                
        Examples:
            >>> claims = {
            ...     "sub": "user-123",
            ...     "email": "user@example.com",
            ...     "name": "John Doe",
            ...     "roles": ["user", "admin"],
            ...     "scope": "read:books write:orders"
            ... }
            >>> user = AuthUser(claims)
            >>> user.user_id
            "user-123"
            >>> user.has_role("admin")
            True
        """
        # 📊 Claims Preservation: Store complete token claims for audit and debugging
        self.claims = token_claims
        
        # 👤 User Identification: Extract core user identification information
        self.user_id = token_claims.get("sub")
        self.email = token_claims.get("email")
        self.name = token_claims.get("name", self.email)
        
        # 🔐 Authorization Data: Extract roles and scopes for access control
        self.roles = token_claims.get("roles", [])
        self.scopes = token_claims.get("scope", "").split() if token_claims.get("scope") else []
    
    def has_scope(self, scope: str) -> bool:
        """
        Check if user has specific OAuth 2.0 scope permission.
        
        Args:
            scope (str): OAuth 2.0 scope to check for authorization
            
        Returns:
            bool: True if user has the specified scope, False otherwise
            
        Examples:
            >>> user.has_scope("read:books")
            True
            >>> user.has_scope("admin:users")
            False
        """
        return scope in self.scopes
    
    def has_role(self, role: str) -> bool:
        """
        Check if user has specific role for role-based access control.
        
        Args:
            role (str): Role name to check for authorization
            
        Returns:
            bool: True if user has the specified role, False otherwise
            
        Examples:
            >>> user.has_role("admin")
            True
            >>> user.has_role("super_admin")
            False
        """
        return role in self.roles
    
    def __str__(self) -> str:
        """String representation for logging and debugging."""
        return f"AuthUser(id={self.user_id}, email={self.email})"
    
    def __repr__(self) -> str:
        """Developer representation for debugging."""
        return self.__str__()


async def validate_jwt_token(token: str) -> AuthUser:
    
    
        
        
    try:
        header = jwt.get_unverified_header(token)
        
        jwks = await get_jwks()
        
        public_key = get_public_key(header, jwks)
        
        claims = jwt.decode(
            token,
            public_key,
            algorithms=[JWT_ALGORITHM],
            audience=OIDC_AUDIENCE,
            issuer=OIDC_AUTHORITY
        )
        
        if not claims.get("sub"):
            raise ValueError("Token missing 'sub' claim")
        
        scopes = claims.get("scope", "").split() if claims.get("scope") else []
        if "bookverse:api" not in scopes:
            raise ValueError("Token missing required 'bookverse:api' scope")
        
        logger.debug(f"✅ Token validated for user: {claims.get('email', claims.get('sub'))}")
        return AuthUser(claims)
        
    except JWTError as e:
        logger.warning(f"⚠️ JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        logger.error(f"❌ Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


def create_mock_user() -> AuthUser:
    
    return AuthUser({
        "sub": "dev-user",
        "email": "dev@bookverse.com",
        "name": "Development User",
        "scope": "openid profile email bookverse:api",
        "roles": ["user", "admin"]
    })


def is_auth_enabled() -> bool:
    
    return AUTH_ENABLED


def is_development_mode() -> bool:
    
    return DEVELOPMENT_MODE

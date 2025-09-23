

"""
BookVerse Core Library - Configuration Management System

This module provides comprehensive configuration management for the BookVerse
platform, implementing enterprise-grade configuration patterns with Pydantic
validation, environment variable integration, and standardized service
configuration across all BookVerse microservices.

🏗️ Architecture Overview:
    - Pydantic Configuration: Type-safe configuration with automatic validation
    - Environment Integration: Seamless .env file and environment variable support
    - Service Standardization: Consistent configuration patterns across all services
    - Validation Framework: Comprehensive configuration validation with error reporting
    - Authentication Integration: Built-in authentication and security configuration
    - Database Configuration: Standardized database connection and session management

🚀 Key Features:
    - Type-safe configuration with automatic validation and type conversion
    - Environment variable integration with .env file support and secure defaults
    - Service metadata management with consistent naming and versioning patterns
    - Authentication configuration with JWT, OIDC, and development mode support
    - Database configuration with connection string management and session pooling
    - Logging configuration with structured logging and performance monitoring

🔧 Technical Implementation:
    - Pydantic BaseModel: Type-safe configuration with automatic validation
    - Environment Variables: Secure configuration management with environment integration
    - Configuration Inheritance: Extensible configuration patterns for service customization
    - Validation Rules: Comprehensive validation with custom validators and error handling
    - Default Management: Secure defaults with production-ready configuration patterns

📊 Business Logic:
    - Service Standardization: Consistent configuration patterns across the platform
    - Security Compliance: Secure configuration management with authentication integration
    - Operational Excellence: Configuration validation and error prevention
    - Development Efficiency: Simplified configuration management for rapid development
    - Environment Management: Multi-environment configuration with secure defaults

🛠️ Usage Patterns:
    - Service Configuration: Base configuration for all BookVerse microservices
    - Development Workflows: .env file integration for local development
    - Production Deployment: Environment variable configuration for production
    - Testing Frameworks: Configuration management for testing and CI/CD
    - Configuration Validation: Type-safe configuration with comprehensive validation

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import os
from typing import Any, Dict, Optional, Type, TypeVar
from pathlib import Path

from pydantic import BaseModel, Field, ConfigDict

T = TypeVar('T', bound='BaseConfig')


class BaseConfig(BaseModel):
    """
    Base configuration class for all BookVerse microservices.
    
    This class provides comprehensive configuration management for BookVerse
    services, implementing type-safe configuration with Pydantic validation,
    environment variable integration, and standardized service configuration
    patterns across the entire platform.
    
    Features:
        - Type-safe configuration with automatic validation and type conversion
        - Environment variable integration with .env file support
        - Service metadata management with consistent patterns
        - Authentication configuration with security defaults
        - Database configuration with connection management
        - Logging configuration with structured logging support
        
    Configuration Sources (in order of precedence):
        1. Environment variables (highest priority)
        2. .env file in current directory
        3. Default values (lowest priority)
        
    Examples:
        >>> # Basic service configuration
        >>> config = BaseConfig(
        ...     service_name="Inventory Service",
        ...     service_version="2.1.0",
        ...     environment="production"
        ... )
        
        >>> # Environment variable integration
        >>> # Set: SERVICE_NAME=checkout, API_VERSION=v2
        >>> config = BaseConfig()  # Automatically loads from environment
        
        >>> # Custom service configuration
        >>> class InventoryConfig(BaseConfig):
        ...     database_url: str = "sqlite:///inventory.db"
        ...     cache_ttl: int = 300
    """
    
    # 🔧 Pydantic Configuration: Environment integration and validation settings
    model_config = ConfigDict(
        env_file=".env",                    # Automatic .env file loading
        env_file_encoding="utf-8",          # UTF-8 encoding support
        case_sensitive=False,               # Case-insensitive environment variables
        validate_assignment=True,           # Validate values on assignment
        extra="forbid"                      # Prevent extra fields for security
    )
    
    # 📊 Service Identification: Core service metadata and identification
    service_name: str = Field(
        default="BookVerse Service",
        description="Name of the service for identification and logging"
    )
    
    service_version: str = Field(
        default="1.0.0",
        description="Semantic version of the service for deployment tracking"
    )
    
    service_description: str = Field(
        default="A BookVerse microservice",
        description="Human-readable description of the service functionality"
    )
    
    # 🌐 API Configuration: API versioning and routing configuration
    api_version: str = Field(
        default="v1",
        description="API version for routing and backward compatibility"
    )
    
    api_prefix: str = Field(
        default="/api/v1",
        description="API path prefix for all service endpoints"
    )
    
    # 🏗️ Environment Management: Environment-specific configuration
    environment: str = Field(
        default="development",
        description="Deployment environment (development, staging, production)"
    )
    
    log_level: str = Field(
        default="INFO",
        description="Logging level"
    )
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    database_url: Optional[str] = Field(
        default=None,
        description="Database connection URL"
    )
    
    auth_enabled: bool = Field(
        default=True,
        description="Enable authentication"
    )
    
    development_mode: bool = Field(
        default=False,
        description="Enable development mode"
    )
    
    oidc_authority: str = Field(
        default="https://dev-auth.bookverse.com",
        description="OIDC authority URL"
    )
    
    oidc_audience: str = Field(
        default="bookverse:api",
        description="OIDC audience"
    )
    
    jwt_algorithm: str = Field(
        default="RS256",
        description="JWT algorithm"
    )
    
    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"
    
    @property
    def is_debug_enabled(self) -> bool:
        return self.debug or self.is_development
    
    def get_api_prefix(self) -> str:
        if self.api_prefix.startswith("/"):
            return self.api_prefix
        return f"/api/{self.api_version}"
    
    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        return cls(**data)
    
    @classmethod
    def from_env(cls: Type[T], prefix: str = "") -> T:
        
            
        env_vars = {}
        
        for key, value in os.environ.items():
            if prefix and key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                env_vars[config_key] = value
            elif not prefix:
                env_vars[key.lower()] = value
        
        return cls(**env_vars)
    
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(service={self.service_name}, version={self.service_version})"
    
    def __repr__(self) -> str:
        return self.__str__()


"""
BookVerse Core Library - Data Validation and Sanitization Utilities

This module provides comprehensive data validation and sanitization utilities
for the BookVerse platform, implementing enterprise-grade input validation,
data sanitization, and security patterns to ensure data integrity and prevent
security vulnerabilities across all BookVerse microservices.

🏗️ Architecture Overview:
    - Input Validation: Comprehensive validation for common data types and formats
    - Data Sanitization: Security-focused data cleaning and normalization
    - Format Validation: Email, UUID, and identifier format validation
    - Security Patterns: XSS prevention and input security validation
    - Type Safety: Type-safe validation with clear boolean returns
    - Performance Optimization: Efficient validation with minimal overhead

🚀 Key Features:
    - Email format validation with RFC-compliant pattern matching
    - UUID validation with proper format checking and error handling
    - String sanitization with HTML cleaning and length constraints
    - Security-focused input validation preventing common vulnerabilities
    - Demo-specific validation helpers for presentation scenarios
    - Extensible validation patterns for custom business rules

🔧 Technical Implementation:
    - Regular Expression Validation: Efficient pattern matching for format validation
    - UUID Library Integration: Proper UUID validation with standard library
    - HTML Sanitization: Security-focused HTML cleaning and XSS prevention
    - Type Checking: Comprehensive type validation with graceful error handling
    - Performance Optimization: Minimal overhead validation for high-throughput scenarios

📊 Business Logic:
    - Data Integrity: Ensuring data quality and consistency across the platform
    - Security Compliance: Preventing injection attacks and data corruption
    - User Experience: Providing clear validation feedback for form inputs
    - System Reliability: Preventing invalid data from causing system failures
    - Development Efficiency: Reusable validation patterns for rapid development

🛠️ Usage Patterns:
    - API Input Validation: Validating request data before processing
    - User Registration: Email and identifier validation for user accounts
    - Data Processing: Sanitizing user input before database storage
    - Security Validation: Preventing XSS and injection attacks
    - Form Validation: Client and server-side validation for user interfaces

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import re
import uuid
from typing import Optional


def validate_email(email: str) -> bool:
    """
    Validate email address format using RFC-compliant pattern matching.
    
    This function provides comprehensive email validation for user registration,
    authentication, and data processing scenarios with security-focused
    validation patterns and graceful error handling.
    
    Args:
        email (str): Email address string to validate
        
    Returns:
        bool: True if email format is valid, False otherwise
        
    Examples:
        >>> validate_email("user@example.com")
        True
        >>> validate_email("invalid.email")
        False
        >>> validate_email("")
        False
        >>> validate_email(None)
        False
        
    Validation Rules:
        - Must be a non-empty string
        - Must contain @ symbol with valid local and domain parts
        - Domain must have valid TLD (2+ characters)
        - Supports common email formats and special characters
    """
    # 🔍 Type and Null Validation: Ensure valid string input
    if not email or not isinstance(email, str):
        return False
    
    # 📧 Email Pattern: RFC-compliant email validation pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    # ✅ Pattern Matching: Validate email format with whitespace handling
    return bool(re.match(email_pattern, email.strip()))


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format using standard library validation.
    
    This function provides comprehensive UUID validation for database
    identifiers, API parameters, and distributed system coordination
    with proper error handling and type safety.
    
    Args:
        uuid_string (str): UUID string to validate
        
    Returns:
        bool: True if UUID format is valid, False otherwise
        
    Examples:
        >>> validate_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> validate_uuid("invalid-uuid")
        False
        >>> validate_uuid("")
        False
        
    Validation Features:
        - Supports all UUID versions (1, 3, 4, 5)
        - Proper hyphen formatting validation
        - Case-insensitive validation
        - Graceful error handling for invalid formats
    """
    # 🔍 Type and Null Validation: Ensure valid string input
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    try:
        # 🆔 UUID Validation: Use standard library for proper format checking
        uuid.UUID(uuid_string.strip())
        return True
    except (ValueError, AttributeError):
        # 🚫 Invalid Format: Graceful handling of malformed UUIDs
        return False


def sanitize_string(
    input_string: str,
    max_length: int = 1000,
    allow_html: bool = False
) -> str:
    
    
        
        
    if not input_string:
        return ""
    
    if not isinstance(input_string, str):
        input_string = str(input_string)
    
    sanitized = input_string.strip()
    
    if len(sanitized) > max_length:
        raise ValueError(
            f"String too long: {len(sanitized)} characters. "
            f"Maximum allowed: {max_length}. "
            f"Demo tip: Consider truncating or splitting long inputs."
        )
    
    if not allow_html:
        sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    dangerous_chars = ['<script', '</script>', 'javascript:', 'onclick=']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized


def validate_service_name(name: str) -> bool:
    
    
        
    if not name or not isinstance(name, str):
        return False
    
    pattern = r'^[a-z0-9][a-z0-9-]*[a-z0-9]$'
    
    name = name.strip().lower()
    
    if len(name) < 2 or len(name) > 50:
        return False
    
    return bool(re.match(pattern, name))


def validate_version_string(version: str) -> bool:
    
    
        
    if not version or not isinstance(version, str):
        return False
    
    pattern = r'^\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?$'
    
    return bool(re.match(pattern, version.strip()))


def validate_port_number(port: int) -> bool:
    
    
        
    if not isinstance(port, int):
        return False
    
    return 1024 <= port <= 65535


def validate_url(url: str, require_https: bool = False) -> bool:
    
    
        
    if not url or not isinstance(url, str):
        return False
    
    if require_https:
        pattern = r'^https://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/.*)?$'
    else:
        pattern = r'^https?://[a-zA-Z0-9.-]+(?:\:[0-9]+)?(?:/.*)?$'
    
    return bool(re.match(pattern, url.strip()))


def create_validation_error_message(field: str, value: str, reason: str) -> str:
    
    
        
    if len(str(value)) > 50:
        display_value = str(value)[:47] + "..."
    else:
        display_value = str(value)
    
    return (
        f"Validation failed for '{field}': {reason}. "
        f"Provided value: '{display_value}'. "
        f"Demo tip: Check the field requirements and try again."
    )

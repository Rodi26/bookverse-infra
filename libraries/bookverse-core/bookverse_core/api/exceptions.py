"""
BookVerse Core Library - API Exception Management

This module provides comprehensive exception handling for the BookVerse platform,
implementing standardized HTTP exception patterns, structured error responses,
and centralized error management with sophisticated logging and context tracking
for enterprise-grade API error handling and debugging.

🏗️ Architecture Overview:
    - Standardized Exceptions: Consistent HTTP exception patterns across all services
    - Structured Error Responses: Rich error context with debugging information
    - Centralized Logging: Comprehensive error logging with configurable levels
    - Context Tracking: Request and user context preservation for debugging
    - Service Integration: Upstream service error handling and propagation
    - Business Logic Mapping: Domain-specific error types and mappings

🚀 Key Features:
    - Comprehensive HTTP status code coverage with business logic mapping
    - Rich error context with request tracking and debugging information
    - Standardized error codes for consistent client-side error handling
    - Configurable logging levels for different error severity levels
    - Service exception mapping for upstream error propagation
    - Idempotency conflict detection and specialized handling

🔧 Technical Implementation:
    - FastAPI Integration: Native integration with FastAPI exception handling
    - Structured Logging: JSON-compatible error logging with full context
    - Exception Hierarchy: Inheritance-based exception design for extensibility
    - Context Preservation: Request and user context tracking through error flow
    - Error Categorization: Business logic error categorization and mapping

📊 Business Logic:
    - API Reliability: Consistent error handling improving API reliability
    - Debug Efficiency: Rich context enabling rapid debugging and resolution
    - Client Integration: Standardized error codes enabling robust client handling
    - Monitoring Integration: Structured logging enabling comprehensive monitoring
    - User Experience: Clear error messages improving developer experience

🛠️ Usage Patterns:
    - API Development: Standardized error handling across all BookVerse services
    - Service Integration: Upstream service error handling and propagation
    - Error Monitoring: Comprehensive error tracking and alerting integration
    - Client Development: Standardized error response handling in client applications
    - Debugging Support: Rich context and logging for rapid issue resolution

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status

logger = logging.getLogger(__name__)


class BookVerseHTTPException(HTTPException):
    """
    Enhanced HTTP exception with structured error context and logging.
    
    This class extends FastAPI's HTTPException to provide rich error context,
    structured logging, and standardized error codes for comprehensive error
    handling across the BookVerse platform with enterprise-grade debugging
    and monitoring capabilities.
    
    Attributes:
        error_code (Optional[str]): Standardized error code for client handling
        context (Dict[str, Any]): Additional error context for debugging
        
    Features:
        - Automatic structured logging with configurable levels
        - Rich error context preservation for debugging
        - Standardized error codes for consistent client handling
        - Request tracking and correlation support
        - Integration with monitoring and alerting systems
    """
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        log_level: str = "warning"
    ):
        """
        Initialize enhanced HTTP exception with context and logging.
        
        Args:
            status_code (int): HTTP status code for the response
            detail (str): Human-readable error message
            error_code (Optional[str]): Standardized error code for client handling
            context (Optional[Dict[str, Any]]): Additional context for debugging
            log_level (str): Logging level - "error", "warning", or "info"
            
        Examples:
            >>> raise BookVerseHTTPException(
            ...     status_code=404,
            ...     detail="Book not found",
            ...     error_code="book_not_found",
            ...     context={"book_id": "123"},
            ...     log_level="info"
            ... )
        """
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code
        self.context = context or {}
        
        # 📊 Structured Logging: Create comprehensive log message with context
        log_message = f"HTTP {status_code}: {detail}"
        if error_code:
            log_message += f" (code: {error_code})"
        if context:
            log_message += f" - Context: {context}"
        
        # 🔧 Configurable Logging: Log at appropriate level based on severity
        if log_level == "error":
            logger.error(log_message)
        elif log_level == "warning":
            logger.warning(log_message)
        else:
            logger.info(log_message)



def raise_validation_error(
    message: str,
    field: Optional[str] = None,
    value: Optional[Any] = None
) -> None:
    
    
        
    context = {}
    if field:
        context["field"] = field
    if value is not None:
        context["value"] = str(value)
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message,
        error_code="validation_error",
        context=context,
        log_level="info"
    )


def raise_not_found_error(
    resource_type: str,
    resource_id: Union[str, int],
    message: Optional[str] = None
) -> None:
    
    
        
    detail = message or f"{resource_type.title()} not found"
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=detail,
        error_code="not_found",
        context={
            "resource_type": resource_type,
            "resource_id": str(resource_id)
        },
        log_level="info"
    )


def raise_conflict_error(
    message: str,
    conflict_type: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    
    
        
    error_code = f"{conflict_type}_conflict" if conflict_type else "conflict"
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=message,
        error_code=error_code,
        context=context or {},
        log_level="warning"
    )


def raise_idempotency_conflict(
    idempotency_key: str,
    message: Optional[str] = None
) -> None:
    
    
        
    detail = message or "Idempotency key conflict - request hash mismatch"
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=detail,
        error_code="idempotency_conflict",
        context={"idempotency_key": idempotency_key},
        log_level="warning"
    )


def raise_insufficient_stock_error(
    book_id: str,
    requested: int,
    available: int
) -> None:
    
    
        
    raise BookVerseHTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"Insufficient stock for book {book_id}",
        error_code="insufficient_stock",
        context={
            "book_id": book_id,
            "requested": requested,
            "available": available
        },
        log_level="info"
    )



def raise_upstream_error(
    service_name: str,
    error: Exception,
    message: Optional[str] = None
) -> None:
    
    
        
    detail = message or f"Upstream service error: {service_name}"
    
    logger.error(
        f"Upstream service '{service_name}' error: {error}",
        exc_info=True
    )
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=detail,
        error_code="upstream_error",
        context={
            "service": service_name,
            "error_type": type(error).__name__
        },
        log_level="error"
    )


def raise_internal_error(
    message: str,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
) -> None:
    
    
        
    if error:
        logger.error(f"Internal server error: {message} - {error}", exc_info=True)
    else:
        logger.error(f"Internal server error: {message}")
    
    raise BookVerseHTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Internal server error",
        error_code="internal_error",
        context=context or {},
        log_level="error"
    )



def handle_service_exception(
    error: Exception,
    service_name: str = "unknown",
    operation: str = "operation"
) -> None:
    """
    Centralized service exception handler with intelligent error mapping.
    
    This function provides sophisticated exception mapping and handling for
    service operations, converting Python exceptions to appropriate HTTP
    exceptions with proper context and error codes for consistent error
    handling across the BookVerse platform.
    
    Args:
        error (Exception): The original exception to handle and map
        service_name (str): Name of the service where the error occurred
        operation (str): Description of the operation that failed
        
    Raises:
        BookVerseHTTPException: Appropriate HTTP exception based on error type
        
    Exception Mapping:
        - ValueError: Mapped to validation errors or business logic conflicts
        - FileNotFoundError: Mapped to HTTP 404 not found errors
        - PermissionError: Mapped to HTTP 403 forbidden errors
        - ConnectionError: Mapped to HTTP 502 upstream service errors
        - Other exceptions: Mapped to HTTP 500 internal server errors
        
    Examples:
        >>> try:
        ...     service_operation()
        ... except Exception as e:
        ...     handle_service_exception(e, "inventory", "get_book")
        
        >>> # In service methods
        >>> try:
        ...     result = external_api_call()
        ... except requests.ConnectionError as e:
        ...     handle_service_exception(e, "external_api", "fetch_data")
        
    Business Logic Detection:
        - Idempotency conflicts: Detected by message prefix and mapped to conflict
        - Stock conflicts: Detected by message prefix and mapped to stock conflict
        - Not found errors: Detected by message content and mapped to 404 errors
        - Validation errors: Default mapping for ValueError exceptions
    """
    # 🔍 ValueError Analysis: Intelligent mapping based on error message content
    if isinstance(error, ValueError):
        detail = str(error)
        
        # 🔄 Idempotency Conflict: Special handling for idempotency key conflicts
        if detail.startswith("idempotency_conflict"):
            raise_conflict_error(detail, "idempotency")
        # 📦 Stock Conflict: Special handling for inventory stock conflicts
        elif detail.startswith("insufficient_stock"):
            raise_conflict_error(detail, "stock")
        # 🔍 Not Found: Detection of not found scenarios in error messages
        elif "not found" in detail.lower():
            parts = detail.split()
            resource_id = parts[-1] if parts else "unknown"
            raise_not_found_error("resource", resource_id, detail)
        # ✅ Validation Error: Default mapping for ValueError exceptions
        else:
            raise_validation_error(detail)
    
    # 📁 File System Errors: Direct mapping to HTTP not found
    elif isinstance(error, FileNotFoundError):
        raise_not_found_error("file", str(error.filename or "unknown"))
    
    # 🔒 Permission Errors: Direct mapping to HTTP forbidden
    elif isinstance(error, PermissionError):
        raise BookVerseHTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied",
            error_code="permission_denied",
            context={"operation": operation}
        )
    
    # 🌐 Connection Errors: Upstream service error handling
    elif isinstance(error, ConnectionError):
        raise_upstream_error(service_name, error)
    
    # ❌ Unexpected Errors: Catch-all for unknown exception types
    else:
        raise_internal_error(
            f"Unexpected error in {operation}",
            error,
            {"service": service_name, "operation": operation}
        )


def create_error_context(
    request_id: Optional[str] = None,
    user_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    
    
        
    context = {}
    
    if request_id:
        context["request_id"] = request_id
    if user_id:
        context["user_id"] = user_id
    
    context.update(kwargs)
    return context


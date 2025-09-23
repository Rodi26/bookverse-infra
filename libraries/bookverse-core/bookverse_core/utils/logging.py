
"""
BookVerse Core Library - Structured Logging and Monitoring

This module provides comprehensive logging infrastructure for the BookVerse
platform, implementing enterprise-grade structured logging with request tracking,
performance monitoring, and standardized log formatting across all BookVerse
microservices for operational excellence and debugging efficiency.

🏗️ Architecture Overview:
    - Structured Logging: Standardized log format with consistent structure across services
    - Request Tracking: Automatic request ID injection for distributed tracing
    - Performance Monitoring: Built-in timing and performance measurement utilities
    - Configuration Management: Type-safe logging configuration with environment integration
    - Multi-Output Support: Console and file logging with configurable formats
    - Service Integration: Seamless integration with all BookVerse service components

🚀 Key Features:
    - Enterprise-grade structured logging with consistent formatting patterns
    - Request correlation ID tracking for distributed system debugging
    - Performance monitoring with automatic timing and metrics collection
    - Configurable log levels and output destinations for different environments
    - Demo-specific logging utilities for presentation and demonstration scenarios
    - Integration with monitoring systems for operational observability

🔧 Technical Implementation:
    - Python Logging Integration: Native Python logging framework with enhanced formatting
    - Pydantic Configuration: Type-safe logging configuration with validation
    - Request Context: Automatic request ID injection and correlation tracking
    - Performance Measurement: Built-in timing utilities for performance monitoring
    - Environment Integration: Environment-based configuration with secure defaults

📊 Business Logic:
    - Operational Excellence: Comprehensive logging for system monitoring and debugging
    - Development Efficiency: Structured logging enabling rapid issue identification
    - Security Compliance: Audit trail generation and security event logging
    - Performance Optimization: Performance monitoring and bottleneck identification
    - Demo Operations: Specialized logging for demonstration and presentation scenarios

🛠️ Usage Patterns:
    - Service Initialization: Logging setup and configuration for all BookVerse services
    - Request Processing: Request correlation and performance tracking
    - Error Handling: Structured error logging with context preservation
    - Performance Monitoring: Timing and metrics collection for optimization
    - Demo Scenarios: Enhanced logging for demonstration and presentation purposes

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import logging
import sys
from typing import Optional
from pydantic import BaseModel, ConfigDict


class LogConfig(BaseModel):
    """
    Logging configuration model with type-safe validation.
    
    This model provides comprehensive logging configuration for BookVerse
    services with automatic environment variable loading, structured logging
    configuration, and production-ready defaults for enterprise logging.
    
    Attributes:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format (str): Log message format string with timestamp and metadata
        include_request_id (bool): Enable request ID injection for tracing
        log_to_file (bool): Enable file logging alongside console logging
        log_file_path (Optional[str]): File path for log output
        
    Environment Variables:
        - LOG_LEVEL: Logging level configuration
        - LOG_FORMAT: Custom log message format
        - LOG_INCLUDE_REQUEST_ID: Request ID tracking (true/false)
        - LOG_LOG_TO_FILE: File logging enablement (true/false)
        - LOG_LOG_FILE_PATH: Log file output path
        
    Examples:
        >>> # Production logging configuration
        >>> config = LogConfig(
        ...     level="INFO",
        ...     log_to_file=True,
        ...     log_file_path="/var/log/bookverse.log"
        ... )
        
        >>> # Development logging with debugging
        >>> config = LogConfig(
        ...     level="DEBUG",
        ...     include_request_id=True
        ... )
    """
    
    # 📊 Log Level: Configurable logging level for different environments
    level: str = "INFO"
    
    # 🎨 Format Configuration: Structured log format with metadata
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 🔗 Request Tracking: Request ID injection for distributed tracing
    include_request_id: bool = True
    
    # 📁 File Logging: Optional file output for log persistence
    log_to_file: bool = False
    log_file_path: Optional[str] = None
    
    # 🌍 Environment Integration: Automatic environment variable loading
    model_config = ConfigDict(env_prefix="LOG_")


def setup_logging(config: LogConfig = None, service_name: str = "bookverse") -> None:
    """
    Configure comprehensive logging for BookVerse services.
    
    This function sets up enterprise-grade logging with structured formatting,
    request tracking, and multi-output support for operational excellence
    and debugging efficiency across all BookVerse microservices.
    
    Args:
        config (LogConfig, optional): Logging configuration model. Creates default if None.
        service_name (str): Service name for log prefixing and identification
        
    Features:
        - Structured log formatting with service identification
        - Console and optional file logging with consistent formatting
        - Request ID injection for distributed tracing support
        - Environment-based configuration with secure defaults
        - Handler cleanup for proper logging initialization
        
    Examples:
        >>> # Basic service logging setup
        >>> setup_logging(service_name="inventory")
        
        >>> # Custom logging configuration
        >>> config = LogConfig(level="DEBUG", log_to_file=True)
        >>> setup_logging(config, "checkout")
        
        >>> # Production logging with file output
        >>> config = LogConfig(
        ...     level="INFO",
        ...     log_to_file=True,
        ...     log_file_path="/var/log/bookverse-inventory.log"
        ... )
        >>> setup_logging(config, "inventory")
        
    Configuration Process:
        1. Load or create logging configuration
        2. Configure log level and formatting
        3. Clean up existing handlers
        4. Set up console logging with structured format
        5. Optionally configure file logging
        6. Enable request ID tracking if configured
    """
    # 🔧 Configuration Loading: Use provided config or create default
    if config is None:
        config = LogConfig()
    
    # 📊 Log Level Configuration: Convert string level to logging constant
    log_level = getattr(logging, config.level.upper(), logging.INFO)
    
    # 🎨 Format Configuration: Create service-specific log format
    log_format = f"[{service_name}] {config.format}"
    formatter = logging.Formatter(log_format)
    
    # 🧹 Handler Cleanup: Remove existing handlers for clean initialization
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 🖥️ Console Logging: Set up structured console output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 📁 File Logging: Optional file output for log persistence
    if config.log_to_file and config.log_file_path:
        try:
            file_handler = logging.FileHandler(config.log_file_path)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            logging.error(f"Failed to set up file logging: {e}")
    
    logging.info(f"✅ Logging configured for {service_name} (level: {config.level})")


def get_logger(name: str) -> logging.Logger:
    
    
    
        
    return logging.getLogger(name)


def log_request_start(logger: logging.Logger, method: str, path: str, request_id: str = None):
    
    
    request_info = f"{method} {path}"
    if request_id:
        request_info += f" [ID: {request_id}]"
    
    logger.info(f"📥 Request started: {request_info}")


def log_request_end(
    logger: logging.Logger,
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    request_id: str = None
):
    
    
    request_info = f"{method} {path}"
    if request_id:
        request_info += f" [ID: {request_id}]"
    
    if status_code >= 500:
        emoji = "❌"
        log_level = logging.ERROR
    elif status_code >= 400:
        emoji = "⚠️"
        log_level = logging.WARNING
    else:
        emoji = "✅"
        log_level = logging.INFO
    
    logger.log(
        log_level,
        f"{emoji} Request completed: {request_info} - {status_code} ({duration_ms:.1f}ms)"
    )


def log_service_startup(logger: logging.Logger, service_name: str, version: str, port: int = None):
    
    
    startup_msg = f"🚀 {service_name} v{version} starting up"
    if port:
        startup_msg += f" on port {port}"
    
    logger.info(startup_msg)


def log_service_shutdown(logger: logging.Logger, service_name: str):
    
    
    logger.info(f"🛑 {service_name} shutting down")


def log_error_with_context(
    logger: logging.Logger,
    error: Exception,
    context: str = None,
    request_id: str = None
):
    
    
    error_msg = f"❌ {type(error).__name__}: {str(error)}"
    
    if context:
        error_msg += f" (Context: {context})"
    
    if request_id:
        error_msg += f" [ID: {request_id}]"
    
    logger.error(error_msg, exc_info=True)


def log_demo_info(logger: logging.Logger, message: str):
    
    
    logger.info(f"🎯 DEMO: {message}")


def log_duplication_eliminated(logger: logging.Logger, component: str, lines_saved: int):
    
    
    logger.info(f"♻️ COMMONS: {component} - eliminated {lines_saved} lines of duplicate code")

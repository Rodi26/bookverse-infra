"""
BookVerse Core Library - Database Session Management

This module provides comprehensive database session management for the BookVerse
platform, implementing enterprise-grade SQLAlchemy integration with connection
pooling, session lifecycle management, and transactional patterns for reliable
database operations across all BookVerse microservices.

🏗️ Architecture Overview:
    - Session Factory Pattern: Centralized session creation and management
    - Connection Pooling: Efficient database connection management with pooling
    - Transactional Patterns: Context manager patterns for safe transaction handling
    - Configuration Management: Type-safe database configuration with validation
    - Lifecycle Management: Proper session cleanup and resource management
    - Error Handling: Comprehensive error handling with automatic rollback

🚀 Key Features:
    - SQLAlchemy integration with enterprise-grade session management
    - Connection pooling for optimal database performance and resource utilization
    - Context manager patterns for safe transactional operations
    - Type-safe database configuration with Pydantic validation
    - Automatic session cleanup and proper resource management
    - Comprehensive error handling with transaction rollback

🔧 Technical Implementation:
    - SQLAlchemy Engine: Database engine creation with connection pooling
    - Session Factory: Centralized session creation with proper configuration
    - Context Managers: Safe transaction handling with automatic cleanup
    - Configuration Model: Type-safe database configuration with validation
    - Resource Management: Proper connection and session lifecycle management

📊 Business Logic:
    - Data Consistency: Transactional patterns ensuring data integrity
    - Performance Optimization: Connection pooling for efficient resource utilization
    - Operational Reliability: Proper error handling and resource cleanup
    - Scalability Support: Connection pooling for high-concurrency applications
    - Development Efficiency: Simplified database access patterns

🛠️ Usage Patterns:
    - Microservice Integration: Database session management for all services
    - Transactional Operations: Safe database operations with automatic rollback
    - Connection Management: Efficient database connection pooling and lifecycle
    - Development Workflows: Simplified database access for rapid development
    - Production Deployment: Enterprise-grade database session management

Authors: BookVerse Platform Team
Version: 1.0.0
"""

import logging
from typing import Generator, Optional
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """
    Database configuration model with type-safe validation.
    
    This model provides comprehensive database configuration for BookVerse
    services with automatic environment variable loading, connection pooling
    configuration, and production-ready defaults for SQLAlchemy integration.
    
    Attributes:
        database_url (str): Database connection URL (required)
        echo (bool): Enable SQLAlchemy query logging for debugging
        pool_size (int): Number of connections to maintain in the pool
        max_overflow (int): Maximum number of connections beyond pool_size
        
    Environment Variables:
        - DB_DATABASE_URL: Database connection URL
        - DB_ECHO: Enable query logging (true/false)
        - DB_POOL_SIZE: Connection pool size (integer)
        - DB_MAX_OVERFLOW: Maximum overflow connections (integer)
        
    Examples:
        >>> # Production configuration
        >>> config = DatabaseConfig(
        ...     database_url="postgresql://user:pass@host:5432/bookverse",
        ...     pool_size=10,
        ...     max_overflow=20
        ... )
        
        >>> # Development configuration with logging
        >>> config = DatabaseConfig(
        ...     database_url="sqlite:///bookverse.db",
        ...     echo=True
        ... )
    """
    
    # 🗄️ Database Connection: Required database connection configuration
    database_url: str
    
    # 🔧 SQLAlchemy Configuration: Query logging and debugging support
    echo: bool = False
    
    # 📊 Connection Pooling: Performance optimization with connection management
    pool_size: int = 5
    max_overflow: int = 10
    
    # 🌍 Environment Integration: Automatic environment variable loading
    model_config = ConfigDict(env_prefix="DB_")


# 🏗️ Global State: Module-level engine and session factory management
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def create_database_engine(config: DatabaseConfig) -> Engine:
    """
    Create and configure SQLAlchemy database engine with connection pooling.
    
    This function creates a singleton database engine with production-ready
    connection pooling configuration, ensuring efficient database resource
    utilization across the application lifecycle.
    
    Args:
        config (DatabaseConfig): Database configuration with connection and pooling settings
        
    Returns:
        Engine: Configured SQLAlchemy engine with connection pooling
        
    Examples:
        >>> config = DatabaseConfig(database_url="sqlite:///app.db")
        >>> engine = create_database_engine(config)
        >>> # Engine is cached for subsequent calls
        
    Features:
        - Singleton pattern for efficient resource utilization
        - Connection pooling with configurable pool size and overflow
        - Query logging support for development and debugging
        - Production-ready configuration with optimal defaults
    """
    # 🔄 Singleton Pattern: Ensure single engine instance for resource efficiency
    global _engine
    
    if _engine is None:
        # 🏗️ Engine Creation: Configure SQLAlchemy engine with pooling settings
        _engine = create_engine(
            config.database_url,
            echo=config.echo,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
        )
        logger.info(f"✅ Database engine created: {config.database_url}")
    
    return _engine


def create_session_factory(engine: Engine) -> sessionmaker:
    
        
    global _session_factory
    
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=engine,
            autocommit=False,
            autoflush=False,
        )
        logger.info("✅ Database session factory created")
    
    return _session_factory


def get_database_session(config: DatabaseConfig) -> Generator[Session, None, None]:
    
    
    
        
    engine = create_database_engine(config)
    session_factory = create_session_factory(engine)
    
    session = session_factory()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Database session error: {e}")
        raise
    finally:
        session.close()


@contextmanager
def database_session_context(config: DatabaseConfig) -> Generator[Session, None, None]:
    
    
    
        
    engine = create_database_engine(config)
    session_factory = create_session_factory(engine)
    session = session_factory()
    
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Database context error: {e}")
        raise
    finally:
        session.close()


def create_tables(config: DatabaseConfig, base_class):
    
    
    try:
        engine = create_database_engine(config)
        base_class.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def test_database_connection(config: DatabaseConfig) -> bool:
    
    
        
    try:
        engine = create_database_engine(config)
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("✅ Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        return False


def reset_database_globals():
    
    global _engine, _session_factory
    
    if _engine:
        _engine.dispose()
        _engine = None
    
    _session_factory = None
    logger.info("🔄 Database globals reset")

"""
Database Connection Management
===============================

PostgreSQL connection and session management for Phase 2.

Author: PromptOps Team
Date: 2026-04-30
Phase: 2 - Database Persistence
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from contextlib import contextmanager
import os
import logging
from typing import Generator

logger = logging.getLogger(__name__)

# Database URL from environment variable
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'postgresql://promptops:promptops_dev_password@localhost:5432/promptops'
)

# Create engine
# Use NullPool for development to avoid connection issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,
    echo=False,  # Set to True for SQL query logging
    future=True
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    future=True
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.

    Usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.

    Usage:
        with get_db_context() as db:
            users = db.query(User).all()

    Yields:
        Database session
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.

    Call this on application startup if tables don't exist.
    """
    from database.models import Base

    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def check_connection() -> bool:
    """
    Test database connection.

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


# Test connection on import
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("=" * 60)
    print("  Database Connection Test")
    print("=" * 60)
    print(f"\nDatabase URL: {DATABASE_URL.replace(DATABASE_URL.split(':')[2].split('@')[0], '***')}")

    if check_connection():
        print("\n✅ Connection successful!")

        # Try creating tables
        print("\nCreating tables...")
        init_db()

        # Test session
        print("\nTesting session...")
        with get_db_context() as db:
            from database.models import User

            # Count users
            user_count = db.query(User).count()
            print(f"   Users in database: {user_count}")

        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
    else:
        print("\n❌ Connection failed!")
        print("\nTroubleshooting:")
        print("1. Check if PostgreSQL is running:")
        print("   docker ps | grep postgres")
        print("2. Check DATABASE_URL in .env file")
        print("3. Verify PostgreSQL credentials")
        print("=" * 60)

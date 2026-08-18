from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os

# Database URL - using SQLite for development (can be switched to PostgreSQL in production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mcp_platform.db")

# For PostgreSQL, use: postgresql://user:password@localhost/mcp_platform
# Make sure to install psycopg2-binary: pip install psycopg2-binary

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
else:
    engine = create_engine(DATABASE_URL)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.

    Usage in FastAPI:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    Run this once on application startup.
    """
    from server.database.models import Base
    Base.metadata.create_all(bind=engine)

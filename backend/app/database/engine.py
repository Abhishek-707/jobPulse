from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Create database engine using psycopg v3
# Convert postgresql:// to postgresql+psycopg:// to use the new driver
database_url = settings.DATABASE_URL
if "postgresql://" in database_url:
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://")

engine = create_engine(
    database_url,
    echo=settings.ENVIRONMENT == "development",
    pool_size=10,
    max_overflow=20,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

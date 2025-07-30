import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

load_dotenv()

# Get DB connection from env; required for authentication and CRUD
DB_URL = os.environ.get("DATABASE_URL")  # Should be set as an env variable

if not DB_URL:
    raise RuntimeError("DATABASE_URL not set in environment variables.")

engine = create_async_engine(DB_URL, echo=False, future=True)
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)
Base = declarative_base()


# PUBLIC_INTERFACE
async def get_db():
    """Dependency for getting DB session per-request (FastAPI style)."""
    async with async_session() as session:
        yield session


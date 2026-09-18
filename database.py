from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import settings

DATABASE_URL = settings.DATABASE_URL

# Create the async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging in development
    future=True
)

# Create the async session factory
async_session = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_db_session():
    """
    Dependency for getting an async DB session.
    Yields the session and ensures it is closed after use.
    """
    async with async_session() as session:
        yield session

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from app.db.session import Base, get_db
from fastapi import FastAPI
from httpx import AsyncClient

# Create an in-memory SQLite database for testing
test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False, future=True)
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
async def initialize_db():
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Drop tables after tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session(initialize_db):
    async with TestSessionLocal() as session:
        yield session

@pytest.fixture
async def app_override(db_session) -> FastAPI:
    from app.main import app

    # Override get_db dependency
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    return app

@pytest.fixture
async def async_client(app_override) -> AsyncClient:
    async with AsyncClient(app=app_override, base_url="http://test") as client:
        yield client
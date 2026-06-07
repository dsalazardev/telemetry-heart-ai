import asyncio
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.main import app
from app.dependencies import get_db
from app.core.security import hash_password, create_access_token
from app.models.usuario import Usuario

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(engine_test, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with engine_test.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def sample_user(db_session):
    user = Usuario(
        documento="123456",
        nombres="Juan",
        apellidos="Pérez",
        correo="juan@test.com",
        password=hash_password("clave123"),
        telefono="3001234567",
        tipo="medico",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture
async def auth_headers(sample_user):
    token = create_access_token(data={"sub": str(sample_user.id), "tipo": sample_user.tipo})
    return {"Authorization": f"Bearer {token}"}

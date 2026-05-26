import importlib
import fnmatch
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.api.dependencies import get_db
from app.core.clients import redis as redis_client
from app.core.database.session import Base
from app.main import app

importlib.import_module("app.domains.user.models.company")

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class FakeRedis:
    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._expires_at: dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        expires_at = self._expires_at.get(key)
        if expires_at is None or expires_at > time.time():
            return False
        self._values.pop(key, None)
        self._expires_at.pop(key, None)
        return True

    def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        return self._values.get(key)

    def setex(self, key: str, ttl: int, value: str) -> None:
        self._values[key] = value
        self._expires_at[key] = time.time() + ttl

    def delete(self, *keys: str) -> None:
        for key in keys:
            self._values.pop(key, None)
            self._expires_at.pop(key, None)

    def scan_iter(self, pattern: str):
        for key in list(self._values):
            if not self._is_expired(key) and fnmatch.fnmatch(key, pattern):
                yield key

    def exists(self, key: str) -> int:
        return int(self.get(key) is not None)

    def incr(self, key: str) -> int:
        value = int(self.get(key) or 0) + 1
        self._values[key] = str(value)
        return value

    def expire(self, key: str, seconds: int) -> None:
        if key in self._values:
            self._expires_at[key] = time.time() + seconds

    def ttl(self, key: str) -> int:
        if self._is_expired(key) or key not in self._values:
            return -2
        expires_at = self._expires_at.get(key)
        if expires_at is None:
            return -1
        return max(0, int(expires_at - time.time()))

    def ping(self) -> bool:
        return True


@pytest.fixture(scope="session", autouse=True)
def create_tables():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(autouse=True)
def fake_redis():
    redis_client._client = FakeRedis()
    yield
    redis_client._client = None


@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

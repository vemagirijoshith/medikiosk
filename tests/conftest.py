import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.intake import _conversations
from app.db.database import Base, get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    _conversations.clear()
    with TestClient(app) as test_client:
        yield test_client, TestingSessionLocal
    _conversations.clear()
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def synthetic_patient(client):
    test_client, _ = client
    response = test_client.post(
        "/patients/",
        json={
            "name": "Synthetic Test Patient",
            "age": 40,
            "gender": "unknown",
            "language": "en",
        },
    )
    assert response.status_code == 201
    return response.json()
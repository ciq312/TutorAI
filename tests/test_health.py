from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_when_database_unavailable():
    settings = Settings(database_url="postgresql+asyncpg://invalid:invalid@127.0.0.1:1/unavailable")
    with TestClient(create_app(settings)) as client:
        response = client.get("/health")
        assert response.status_code == 503
        assert response.json() == {"status": "unavailable", "database": "unavailable"}

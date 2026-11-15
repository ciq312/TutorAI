import asyncio
import os
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def database_url():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to a separate PostgreSQL database named tutor_test*")
    settings = Settings(database_url=url)
    if not (make_url(settings.database_url).database or "").startswith("tutor_test"):
        pytest.fail("Tests only allow databases whose names start with tutor_test")
    env = {**os.environ, "DATABASE_URL": settings.database_url}
    for args in (("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head"), ("check",)):
        subprocess.run([sys.executable, "-m", "alembic", *args], cwd=ROOT, env=env, check=True)
    return settings.database_url


@pytest.fixture
def client(database_url):
    async def clear():
        engine = create_async_engine(database_url)
        try:
            async with engine.begin() as connection:
                await connection.execute(text("TRUNCATE students CASCADE"))
        finally:
            await engine.dispose()

    asyncio.run(clear())
    with TestClient(create_app(Settings(database_url=database_url))) as client:
        yield client
    asyncio.run(clear())

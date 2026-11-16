import asyncio
import os
import secrets
import subprocess
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer

from app.core.config import Settings
from app.main import create_app

ROOT = Path(__file__).resolve().parents[1]


def apply_migrations(url: str):
    env = {**os.environ, "DATABASE_URL": url}
    for args in (("upgrade", "head"), ("downgrade", "base"), ("upgrade", "head"), ("check",)):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args], cwd=ROOT, env=env,
            capture_output=True, text=True,
        )
        if result.returncode:
            output = f"{result.stdout}\n{result.stderr}"
            password = make_url(url).password
            if password:
                output = output.replace(password, "***")
            pytest.fail(f"alembic {' '.join(args)} failed:\n{output}", pytrace=False)


@pytest.fixture(scope="session")
def database_url():
    # Always use a disposable database, never DATABASE_URL or TEST_DATABASE_URL.
    # The host port is assigned by Docker, so local PostgreSQL can keep port 5432.
    with PostgresContainer(
        "pgvector/pgvector:pg17", username="tutor_test", password=secrets.token_hex(16),
        dbname="tutor_test",
    ) as postgres:
        database_url = postgres.get_connection_url(driver="asyncpg")
        apply_migrations(database_url)
        yield database_url


@pytest.fixture
def client(database_url):
    async def clear():
        engine = create_async_engine(database_url)
        try:
            async with engine.begin() as connection:
                await connection.execute(text("TRUNCATE students, integration_state, calendar_events, knowledge_documents CASCADE"))
        finally:
            await engine.dispose()

    asyncio.run(clear())
    with TestClient(create_app(Settings(database_url=database_url, gemini_api_key=""))) as client:
        yield client
    asyncio.run(clear())

import asyncio
import logging

import httpx
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import router
from app.api.integrations import router as integrations_router
from app.api.knowledge import router as knowledge_router
from app.rag.embeddings import build_provider
from app.rag.llm import build_llm
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.getLogger('httpx').setLevel(logging.WARNING)
        logging.getLogger('httpcore').setLevel(logging.WARNING)
        config = settings or get_settings()
        app.title = config.app_name
        engine = create_async_engine(
            config.database_url, pool_pre_ping=True,
            connect_args={"timeout": 5, "command_timeout": 5},
        )
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
        app.state.settings = config
        async with (
            httpx.AsyncClient(timeout=config.embedding_timeout) as http_client,
            httpx.AsyncClient(timeout=config.llm_timeout) as llm_client,
            httpx.AsyncClient(timeout=30) as integration_client,
        ):
            app.state.llm_provider = build_llm(config, llm_client)
            app.state.embedding_provider = build_provider(config, http_client)
            app.state.integration_client = integration_client
            try:
                yield
            finally:
                await engine.dispose()

    app = FastAPI(
        title=settings.app_name if settings else "Tutor RAG",
        description="Ученики, контакты и история занятий репетитора",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(router)
    app.include_router(integrations_router)
    app.include_router(knowledge_router)

    @app.get("/", tags=["System"])
    async def root():
        return {"name": app.title, "version": app.version, "docs": "/docs"}

    @app.get("/health", tags=["System"], responses={503: {"description": "Database unavailable"}})
    async def health():
        try:
            async with asyncio.timeout(5):
                async with app.state.session_factory() as session:
                    await session.execute(text("SELECT 1"))
        except (SQLAlchemyError, OSError, TimeoutError):
            return JSONResponse(status_code=503, content={"status": "unavailable", "database": "unavailable"})
        return {"status": "ok", "database": "ok"}

    return app


app = create_app()

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.api.routes import router
from app.core.config import Settings, get_settings


def create_app(settings: Settings | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config = settings or get_settings()
        app.title = config.app_name
        engine = create_async_engine(
            config.database_url, pool_pre_ping=True,
            connect_args={"timeout": 5, "command_timeout": 5},
        )
        app.state.session_factory = async_sessionmaker(engine, expire_on_commit=False)
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

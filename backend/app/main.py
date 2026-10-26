from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errors import register_error_handlers
from app.api.routes.files import router as files_router
from app.core.config import Settings, get_settings
from app.db.session import create_engine, create_session_factory, init_db
from app.services.storage import LocalFileStorage


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = create_engine(settings.database_url)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        await init_db(engine)
        yield
        await engine.dispose()

    app = FastAPI(title="m3wory.site API", lifespan=lifespan)
    app.state.settings = settings
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.storage = LocalFileStorage(settings.upload_dir)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(app)
    app.include_router(files_router, prefix="/api")
    return app

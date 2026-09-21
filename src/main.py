from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.infrastructure.config.settings import Settings
from src.infrastructure.di.containers import Container
from src.infrastructure.logging.config import setup_logging
from src.infrastructure.persistence.sqlalchemy.database import init_sqlite_schema
from src.presentation.api.exception_handlers import register_exception_handlers
from src.presentation.api.middlewares.logging_middleware import LoggingMiddleware
from src.presentation.api.middlewares.request_id_middleware import RequestIDMiddleware
from src.presentation.api.v1.router import router as v1_router
from src.presentation.api.v1 import dependencies as v1_dependencies
from src.presentation.api.v1.routers import auth, me, sessions


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = Settings()
    setup_logging(
        level=settings.logging.level,
        service_name=settings.app.name,
        service_version=settings.app.version,
        log_path=settings.logging.path,
    )

    container = Container()
    container.config.from_pydantic(settings)

    container.wire(modules=[auth, me, sessions, v1_dependencies])
    app.container = container

    if settings.db.type == "sqlite":
        engine = container.engine()
        await init_sqlite_schema(engine)

    yield


app = FastAPI(lifespan=lifespan)
register_exception_handlers(app)
app.add_middleware(LoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.include_router(v1_router)

"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router
from src.config import get_settings
from src.database.database import (
    create_engine,
    create_session_factory,
    set_engine,
    set_session_factory,
)
from src.logging_config import setup_logging
from src.middleware.logging_middleware import LoggingMiddleware
from src.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage SQLAlchemy engine lifecycle.

    Initializes the database engine and session factory on startup
    and disposes the engine on shutdown.
    The database URL is read from DATABASE_URL environment variable.
    """
    # Initialize logging
    setup_logging()

    engine = create_engine()
    set_engine(engine)

    session_factory = create_session_factory(engine)
    set_session_factory(session_factory)

    yield

    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title="VC Audit Tool",
        description="Portfolio valuation tool with audit trail",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # Add logging middleware (first)
    app.add_middleware(LoggingMiddleware)

    # Add rate limiting middleware (only in production)
    if settings.environment == "production":
        app.add_middleware(RateLimitMiddleware)

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api")

    return app


# Create app instance for uvicorn
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
    )

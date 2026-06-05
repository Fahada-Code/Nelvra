import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import engine
from .exceptions import NelvraException, nelvra_exception_handler
from .models.base import Base
from .routers import alerts, analytics, auth, billing, events, export, projects, prompts, teams

logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # In production, run `alembic upgrade head` before starting.
    # In development, create tables automatically for convenience.
    if settings.environment == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables verified")
    yield
    await engine.dispose()


app = FastAPI(
    title="Nelvra API",
    version="1.0.0",
    description="LLM observability platform API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(NelvraException, nelvra_exception_handler)  # type: ignore[arg-type]

app.include_router(events.router, prefix="/v1")
app.include_router(projects.router, prefix="/v1")
app.include_router(analytics.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(alerts.router, prefix="/v1")
app.include_router(prompts.router, prefix="/v1")
app.include_router(billing.router, prefix="/v1")
app.include_router(teams.router, prefix="/v1")
app.include_router(export.router, prefix="/v1")


@app.get("/health", tags=["system"])
async def health() -> dict:
    return {"status": "ok", "version": "1.0.0"}

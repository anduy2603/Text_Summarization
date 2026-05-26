import asyncio
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.summarize import router as summarize_router
from app.core.config import settings
from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


def _try_preload_phobert() -> None:
    try:
        from app.services.summarization.phobert_extractive import _get_phobert_runtime
        _get_phobert_runtime()
        logger.info("PhoBERT runtime pre-warmed successfully.")
    except Exception as exc:
        logger.warning("PhoBERT pre-warm skipped (will load on first request): %s", exc)


def _try_preload_vit5() -> None:
    try:
        from app.services.summarization.vit5_abstractive import _get_vit5_runtime
        _get_vit5_runtime()
        logger.info("ViT5 runtime pre-warmed successfully.")
    except Exception as exc:
        logger.warning("ViT5 pre-warm skipped (will load on first request): %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    logger.info("Starting backend service: %s v%s", settings.app_name, settings.app_version)
    if settings.preload_models:
        loop = asyncio.get_event_loop()
        loop.run_in_executor(None, _try_preload_phobert)
        loop.run_in_executor(None, _try_preload_vit5)
    yield
    logger.info("Backend service shutting down.")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Vietnamese multi-format text summarization backend.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5173",
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1", tags=["health"])
app.include_router(summarize_router, prefix="/api/v1", tags=["summarize"])

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.summarize import router as summarize_router
from app.core.config import settings
from app.core.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Vietnamese multi-format text summarization backend skeleton.",
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


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Starting backend service: %s v%s", settings.app_name, settings.app_version)

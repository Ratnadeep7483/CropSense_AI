"""
CropSense AI — FastAPI Backend Application.

Entry point for the backend server.  Configures CORS, registers
routes, loads ML models at startup, and exposes health/status
endpoints.

Run with:
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from urllib.parse import urlsplit

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import crop, fertilizer, soil, weather, yield_prediction
from app.services.crop_service import crop_service
from app.services.fertilizer_service import fertilizer_service
from app.services.soil_service import soil_service
from app.services.yield_prediction_service import yield_prediction_service

# ── Logging ──────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ── Lifespan (startup / shutdown) ────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Load ML models once when the application starts."""
    logger.info("Loading ML models …")
    crop_service.load_model()
    fertilizer_service.load_model()
    soil_service.load_model()
    yield_prediction_service.load_model()
    logger.info("Model loading complete.")
    yield
    logger.info("Shutting down CropSense AI backend.")


# ── Application ──────────────────────────────────────────────────
app = FastAPI(
    title="CropSense AI API",
    description="Backend API for CropSense AI agricultural recommendation system.",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ─────────────────────────────────────────────────────────
_DEFAULT_ALLOWED_ORIGINS: tuple[str, ...] = (
    "http://localhost:5173",
    "http://127.0.0.1:5173",
)


def _get_allowed_origins() -> list[str]:
    configured_origins = os.getenv("CORS_ORIGINS")
    if configured_origins is None:
        return list(_DEFAULT_ALLOWED_ORIGINS)

    origins = [
        origin.strip().rstrip("/")
        for origin in configured_origins.split(",")
        if origin.strip()
    ]
    if not origins or "*" in origins:
        raise ValueError(
            "CORS_ORIGINS must contain one or more explicit browser origins."
        )
    for origin in origins:
        parsed = urlsplit(origin)
        try:
            parsed.port
        except ValueError as exc:
            raise ValueError(f"Invalid browser origin in CORS_ORIGINS: {origin}") from exc
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.username
            or parsed.password
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(f"Invalid browser origin in CORS_ORIGINS: {origin}")
    return origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routes ───────────────────────────────────────────────────────
app.include_router(crop.router)
app.include_router(fertilizer.router)
app.include_router(soil.router)
app.include_router(weather.router)
app.include_router(yield_prediction.router)


# ── Health / Status ──────────────────────────────────────────────
@app.get(
    "/health",
    tags=["Health"],
    summary="Health check",
    description="Returns the overall health status of the backend.",
)
async def health_check() -> dict:
    return {"status": "healthy"}


@app.get(
    "/api/model-status",
    tags=["Health"],
    summary="ML model status",
    description=(
        "Reports whether each ML model and its preprocessing "
        "artifacts are loaded and ready for inference."
    ),
)
async def model_status() -> dict:
    return {
        "crop_model": {
            "loaded": crop_service.is_loaded,
            "error": crop_service.load_error,
        },
        "fertilizer_model": {
            "loaded": fertilizer_service.is_loaded,
            "error": fertilizer_service.load_error,
        },
        "fertilizer_preprocessor": {
            "loaded": fertilizer_service.preprocessor_loaded,
        },
        "fertilizer_label_encoder": {
            "loaded": fertilizer_service.label_encoder_loaded,
        },
        "soil_model": {
            "loaded": soil_service.is_loaded,
            "error": soil_service.load_error,
        },
        "yield_model": {
            "loaded": yield_prediction_service.is_loaded,
            "error": (
                None
                if yield_prediction_service.is_loaded
                else "Model is not available. Check server logs."
            ),
        },
    }

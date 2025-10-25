from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette_exporter import PrometheusMiddleware, handle_metrics

from .config import settings
from .routers import backtest, data, health, live, scalp_card, signals, stream, swings

app = FastAPI(
    title="SOLUSDT Swing Detection API",
    version="1.0.0",
    description="Real-time trading signal detection with two-stage methodology",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# Prometheus metrics middleware
app.add_middleware(PrometheusMiddleware, app_name="extrema")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# Metrics endpoint
app.add_route("/metrics", handle_metrics)

# API Routes - all prefixed with /api
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(swings.router, prefix="/api/swings", tags=["swings"])
app.include_router(signals.router, prefix="/api/signals", tags=["signals"])
app.include_router(backtest.router, prefix="/api/backtest", tags=["backtest"])
app.include_router(live.router, prefix="/api/live", tags=["live-monitoring"])
app.include_router(stream.router, prefix="/api/stream", tags=["microstructure"])
app.include_router(scalp_card.router, prefix="/api/scalp", tags=["scalp-cards"])
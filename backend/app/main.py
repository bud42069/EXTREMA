from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import backtest, data, health, live, signals, swings

app = FastAPI(
    title="SOLUSDT Swing Detection API",
    version="1.0.0",
    description="Real-time trading signal detection with two-stage methodology",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

# API Routes
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(swings.router, prefix="/swings", tags=["swings"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
app.include_router(live.router, prefix="/live", tags=["live-monitoring"])
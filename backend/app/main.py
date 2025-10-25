from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import backtest, data, health, signals, swings

app = FastAPI(title="EXTREMA API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.CORS_ORIGINS == "*" else settings.CORS_ORIGINS.split(","),
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(swings.router, prefix="/swings", tags=["swings"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
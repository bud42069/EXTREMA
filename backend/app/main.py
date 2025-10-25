from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routers import health, data, swings, signals, backtest

app = FastAPI(title="EXTREMA API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True
)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(swings.router, prefix="/swings", tags=["swings"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])
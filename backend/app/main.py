"""
FastAPI Main Application
SOLUSDT Swing Capture System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

from app.routers import health, data, swings, signals, backtest

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="EXTREMA API",
    description="Two-Stage Swing Detection System for SOLUSDT",
    version="2.0.0"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(swings.router, prefix="/swings", tags=["swings"])
app.include_router(signals.router, prefix="/signals", tags=["signals"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])


@app.on_event("startup")
async def startup_event():
    """Initialize system on startup."""
    print("🚀 EXTREMA API Starting...")
    print(f"   Symbol: {os.getenv('SYMBOL', 'SOLUSDT')}")
    print(f"   Timeframe: {os.getenv('TIMEFRAME', '5m')}")
    print("✅ System Ready")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("👋 EXTREMA API Shutting Down...")

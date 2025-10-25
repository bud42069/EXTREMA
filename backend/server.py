from fastapi import FastAPI, APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import json
import io

# Import our trading modules
from indicators import add_all_indicators
from extrema_detection import detect_local_extrema, label_extrema_with_swings
from signal_detection import TwoStageDetector
from backtesting import BacktestEngine


ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")


# Define Models
class StatusCheck(BaseModel):
    model_config = ConfigDict(extra="ignore")  # Ignore MongoDB's _id field
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

# Add your routes to the router instead of directly to app
@api_router.get("/")
async def root():
    return {"message": "Hello World"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.model_dump()
    status_obj = StatusCheck(**status_dict)
    
    # Convert to dict and serialize datetime to ISO string for MongoDB
    doc = status_obj.model_dump()
    doc['timestamp'] = doc['timestamp'].isoformat()
    
    _ = await db.status_checks.insert_one(doc)
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    # Exclude MongoDB's _id field from the query results
    status_checks = await db.status_checks.find({}, {"_id": 0}).to_list(1000)
    
    # Convert ISO string timestamps back to datetime objects
    for check in status_checks:
        if isinstance(check['timestamp'], str):
            check['timestamp'] = datetime.fromisoformat(check['timestamp'])
    
    return status_checks


# ============= Trading Analysis Endpoints =============

class AnalysisRequest(BaseModel):
    """Request model for analysis configuration."""
    atr_threshold: float = 0.6
    vol_z_threshold: float = 0.5
    bb_width_threshold: float = 0.005
    confirmation_window: int = 6
    atr_multiplier: float = 0.5
    volume_multiplier: float = 1.5


class BacktestRequest(BaseModel):
    """Request model for backtest configuration."""
    analysis_id: str
    initial_capital: float = 10000.0
    risk_per_trade: float = 0.02
    tp1_r: float = 1.0
    tp2_r: float = 2.0
    tp3_r: float = 3.5
    tp1_scale: float = 0.5
    tp2_scale: float = 0.3


@api_router.post("/upload-data")
async def upload_csv_data(file: UploadFile = File(...)):
    """
    Upload and parse CSV data file.
    Stores the raw data in MongoDB for analysis.
    """
    try:
        # Read CSV content
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate required columns
        required_cols = ['time', 'open', 'high', 'low', 'close', 'Volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing_cols}")
        
        # Convert to records for MongoDB
        data_records = df.to_dict('records')
        
        # Store in MongoDB
        dataset_id = str(uuid.uuid4())
        dataset_doc = {
            'id': dataset_id,
            'filename': file.filename,
            'uploaded_at': datetime.now(timezone.utc).isoformat(),
            'total_bars': len(df),
            'start_time': int(df['time'].iloc[0]),
            'end_time': int(df['time'].iloc[-1]),
            'data': data_records
        }
        
        await db.datasets.insert_one(dataset_doc)
        
        return JSONResponse({
            'success': True,
            'dataset_id': dataset_id,
            'total_bars': len(df),
            'start_time': int(df['time'].iloc[0]),
            'end_time': int(df['time'].iloc[-1])
        })
    
    except Exception as e:
        logger.error(f"Error uploading data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/analyze")
async def analyze_data(dataset_id: str, config: AnalysisRequest):
    """
    Run complete analysis on uploaded dataset.
    Calculates indicators, detects extrema, finds candidates, confirms signals.
    """
    try:
        # Fetch dataset
        dataset = await db.datasets.find_one({'id': dataset_id}, {'_id': 0})
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Convert to DataFrame
        df = pd.DataFrame(dataset['data'])
        
        # Add indicators
        logger.info("Calculating indicators...")
        df = add_all_indicators(df)
        
        # Detect local extrema
        logger.info("Detecting local extrema...")
        minima_mask, maxima_mask = detect_local_extrema(df, window=12)
        
        total_minima = minima_mask.sum()
        total_maxima = maxima_mask.sum()
        
        # Label extrema with future swings (for analysis)
        logger.info("Labeling extrema with swings...")
        minima_labeled, maxima_labeled = label_extrema_with_swings(
            df, minima_mask, maxima_mask, 
            swing_threshold=10.0, 
            lookahead_bars=288
        )
        
        # Two-stage detection
        logger.info("Running two-stage detection...")
        detector = TwoStageDetector(
            atr_threshold=config.atr_threshold,
            vol_z_threshold=config.vol_z_threshold,
            bb_width_threshold=config.bb_width_threshold,
            confirmation_window=config.confirmation_window,
            atr_multiplier=config.atr_multiplier,
            volume_multiplier=config.volume_multiplier
        )
        
        detection_results = detector.detect_signals(df, minima_mask, maxima_mask)
        
        # Prepare results
        analysis_id = str(uuid.uuid4())
        analysis_doc = {
            'id': analysis_id,
            'dataset_id': dataset_id,
            'analyzed_at': datetime.now(timezone.utc).isoformat(),
            'config': config.model_dump(),
            'total_bars': len(df),
            'total_minima': int(total_minima),
            'total_maxima': int(total_maxima),
            'total_candidates': detection_results['total_candidates'],
            'total_confirmed': detection_results['total_confirmed'],
            'long_candidates': detection_results['long_candidates'].to_dict('records') if not detection_results['long_candidates'].empty else [],
            'short_candidates': detection_results['short_candidates'].to_dict('records') if not detection_results['short_candidates'].empty else [],
            'confirmed_longs': detection_results['confirmed_longs'].to_dict('records') if not detection_results['confirmed_longs'].empty else [],
            'confirmed_shorts': detection_results['confirmed_shorts'].to_dict('records') if not detection_results['confirmed_shorts'].empty else [],
            'extrema_analysis': {
                'minima_with_swings': int(minima_labeled['swing_occurred'].sum()) if not minima_labeled.empty else 0,
                'maxima_with_swings': int(maxima_labeled['swing_occurred'].sum()) if not maxima_labeled.empty else 0,
                'avg_swing_pct': float(pd.concat([minima_labeled[minima_labeled['swing_occurred']], 
                                                   maxima_labeled[maxima_labeled['swing_occurred']]
                                                  ])['pct_move'].mean()) if len(minima_labeled) > 0 or len(maxima_labeled) > 0 else 0
            }
        }
        
        await db.analyses.insert_one(analysis_doc)
        
        # Return summary
        return JSONResponse({
            'success': True,
            'analysis_id': analysis_id,
            'summary': {
                'total_bars': len(df),
                'total_extrema': int(total_minima + total_maxima),
                'total_candidates': detection_results['total_candidates'],
                'total_confirmed_signals': detection_results['total_confirmed'],
                'long_signals': len(detection_results['confirmed_longs']),
                'short_signals': len(detection_results['confirmed_shorts']),
                'extrema_with_swings': analysis_doc['extrema_analysis']
            }
        })
    
    except Exception as e:
        logger.error(f"Error analyzing data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/analysis/{analysis_id}")
async def get_analysis(analysis_id: str):
    """Get analysis results by ID."""
    try:
        analysis = await db.analyses.find_one({'id': analysis_id}, {'_id': 0})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return JSONResponse(analysis)
    
    except Exception as e:
        logger.error(f"Error fetching analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/backtest")
async def run_backtest(config: BacktestRequest):
    """
    Run backtest on analyzed signals.
    """
    try:
        # Fetch analysis
        analysis = await db.analyses.find_one({'id': config.analysis_id}, {'_id': 0})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        # Fetch dataset
        dataset = await db.datasets.find_one({'id': analysis['dataset_id']}, {'_id': 0})
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Convert to DataFrame
        df = pd.DataFrame(dataset['data'])
        df = add_all_indicators(df)
        
        # Get confirmed signals
        confirmed_signals = analysis['confirmed_longs'] + analysis['confirmed_shorts']
        
        if not confirmed_signals:
            raise HTTPException(status_code=400, detail="No confirmed signals to backtest")
        
        # Run backtest
        logger.info(f"Running backtest with {len(confirmed_signals)} signals...")
        engine = BacktestEngine(
            initial_capital=config.initial_capital,
            risk_per_trade=config.risk_per_trade,
            tp1_r=config.tp1_r,
            tp2_r=config.tp2_r,
            tp3_r=config.tp3_r,
            tp1_scale=config.tp1_scale,
            tp2_scale=config.tp2_scale
        )
        
        backtest_stats = engine.run_backtest(df, confirmed_signals)
        trades_df = engine.get_trades_df()
        
        # Store backtest results
        backtest_id = str(uuid.uuid4())
        backtest_doc = {
            'id': backtest_id,
            'analysis_id': config.analysis_id,
            'dataset_id': analysis['dataset_id'],
            'backtested_at': datetime.now(timezone.utc).isoformat(),
            'config': config.model_dump(),
            'statistics': backtest_stats,
            'trades': trades_df.to_dict('records') if not trades_df.empty else []
        }
        
        await db.backtests.insert_one(backtest_doc)
        
        return JSONResponse({
            'success': True,
            'backtest_id': backtest_id,
            'statistics': backtest_stats,
            'total_trades': len(trades_df)
        })
    
    except Exception as e:
        logger.error(f"Error running backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/backtest/{backtest_id}")
async def get_backtest(backtest_id: str):
    """Get backtest results by ID."""
    try:
        backtest = await db.backtests.find_one({'id': backtest_id}, {'_id': 0})
        if not backtest:
            raise HTTPException(status_code=404, detail="Backtest not found")
        
        return JSONResponse(backtest)
    
    except Exception as e:
        logger.error(f"Error fetching backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/datasets")
async def list_datasets():
    """List all uploaded datasets."""
    try:
        datasets = await db.datasets.find({}, {'_id': 0, 'data': 0}).to_list(100)
        return JSONResponse({'datasets': datasets})
    
    except Exception as e:
        logger.error(f"Error listing datasets: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/chart-data/{dataset_id}")
async def get_chart_data(dataset_id: str, start: Optional[int] = None, limit: int = 500):
    """
    Get chart data for visualization.
    Returns OHLCV data with indicators for charting.
    """
    try:
        # Fetch dataset
        dataset = await db.datasets.find_one({'id': dataset_id}, {'_id': 0})
        if not dataset:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        # Convert to DataFrame and add indicators
        df = pd.DataFrame(dataset['data'])
        df = add_all_indicators(df)
        
        # Apply start and limit
        if start is not None:
            df = df[df.index >= start]
        df = df.head(limit)
        
        # Convert NaN to None for JSON
        df = df.replace({np.nan: None})
        
        return JSONResponse({
            'data': df.to_dict('records'),
            'total_bars': len(df)
        })
    
    except Exception as e:
        logger.error(f"Error fetching chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
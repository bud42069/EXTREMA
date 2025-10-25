# SOLUSDT Swing Capture System

Two-stage swing detection system for capturing ≥10% moves in SOLUSDT on 5-minute timeframe.

## Architecture

```
Data Ingestor → Extrema & Swing Detector → Signal Engine (Two-Stage) → Backtester → UI
```

## Quick Start

### Backend API

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
yarn install
yarn start
```

## API Endpoints

### Health Check
```bash
GET /health
```

### Data Upload
```bash
POST /data/upload
Content-Type: multipart/form-data
Body: CSV file with columns: time,open,high,low,close,Volume
```

**CSV Requirements:**
- `time`: Unix timestamp (seconds)
- `open`, `high`, `low`, `close`: Price values (float)
- `Volume`: Trading volume (float)

### Latest Signal
```bash
GET /signals/latest?atr_min=0.6&volz_min=1.0&bbw_min=0.005
```

**Response:**
```json
{
  "side": "long",
  "extremum_index": 1234,
  "confirm_index": 1238,
  "entry": 195.50,
  "sl": 192.30,
  "tp1": 198.70,
  "tp2": 201.90,
  "tp3": 207.30,
  "trail_atr_mult": 0.5
}
```

### Run Backtest
```bash
POST /backtest/run
Content-Type: application/json
Body:
{
  "atr_min": 0.6,
  "volz_min": 1.0,
  "bbw_min": 0.005,
  "breakout_atr_mult": 0.5,
  "vol_mult": 1.5,
  "confirm_window": 6
}
```

**Response:**
```json
{
  "summary": {
    "trades": 98,
    "wins": 61,
    "losses": 37,
    "win_rate": 62.24,
    "avg_R": 0.42,
    "pnl_R": 41.16,
    "max_dd_R": -3.50
  },
  "ledger": [...]
}
```

### Swing Analysis
```bash
GET /swings
```

Returns count of potential ≥10% swings in loaded data (for analysis only).

## Signal Detection Methodology

### Stage 1: Candidate Detection (at Local Extrema)

**Extrema Detection:**
- Window: ±12 bars (~1 hour on 5m chart)
- Local minimum for long candidates
- Local maximum for short candidates

**Candidate Thresholds (ALL required):**
- **ATR14 ≥ 0.6** - Volatility expansion
- **Volume Z-Score ≥ 0.5** (prefer ≥1.0) - Volume spike
- **BB Width ≥ 0.005** - Band expansion

### Stage 2: Micro Confirmation

**Confirmation Window:** 6 bars (30 minutes)

**Requirements (BOTH must be met):**
1. **Breakout Close:**
   - Long: Close > `local_high + (0.5 × ATR5)`
   - Short: Close < `local_low - (0.5 × ATR5)`

2. **Volume Confirmation:**
   - Breakout bar volume ≥ `1.5× median_volume_50`

### Trade Execution

**Entry:** Breakout confirmation price

**Stop Loss:**
- Long: `local_low - (0.9 × ATR5)`
- Short: `local_high + (0.9 × ATR5)`

**Take Profit Ladder:**
- TP1 (1.0R): 50% position → move SL to BE
- TP2 (2.0R): 30% position
- TP3 (3.0R): 20% position → trail with 0.5×ATR5

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# Exchange API
MEXC_API_KEY=your_key_here
MEXC_SECRET_KEY=your_secret_here

# On-Chain Data
HELIUS_API_KEY=your_key_here

# Trading
SYMBOL=SOLUSDT
TIMEFRAME=5m

# Thresholds
ATR_THRESHOLD=0.6
VOL_Z_THRESHOLD=0.5
BB_WIDTH_THRESHOLD=0.005
```

## Testing

```bash
# Unit tests
pytest tests/ -v

# Test with sample data
curl -X POST http://localhost:8000/data/upload \
  -F "file=@data/MEXC_SOLUSDT_5m.csv"

curl http://localhost:8000/signals/latest

curl -X POST http://localhost:8000/backtest/run \
  -H "Content-Type: application/json" \
  -d '{"atr_min":0.6,"volz_min":1.0,"bbw_min":0.005}'
```

## Documentation

- **AGENTS.md** - Complete system playbook with agent roles, thresholds, and execution protocols
- **API Docs** - http://localhost:8000/docs (auto-generated Swagger)

## Expected Performance

Based on historical analysis (21,484 bars):
- **Capture Rate:** 80-85% of ≥10% swings
- **Win Rate:** 60-65%
- **Average Gain:** 15-30% per signal
- **Hold Time:** ~22 hours median
- **Profit Factor:** > 1.5

## Development

### Structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app
│   ├── routers/          # API endpoints
│   ├── services/         # Business logic
│   ├── models/           # Pydantic schemas
│   └── utils/            # Helper functions
```

### Adding Features

1. New indicators → `app/services/indicators.py`
2. New API endpoints → `app/routers/`
3. New business logic → `app/services/`

## License

MIT

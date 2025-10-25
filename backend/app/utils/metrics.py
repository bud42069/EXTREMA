"""
Prometheus metrics for application monitoring.
Tracks uploads, signals, backtests, and vetos.
"""
from prometheus_client import Counter, Histogram

# Upload metrics
upload_total = Counter(
    'extrema_upload_total',
    'Total number of CSV uploads',
    ['status']
)

# Signal metrics
signals_confirmed_total = Counter(
    'signals_confirmed_total',
    'Total number of confirmed signals',
    ['side']
)

signals_veto_total = Counter(
    'signals_veto_total',
    'Total number of vetoed signals',
    ['reason', 'side']
)

# Backtest metrics
backtest_runs_total = Counter(
    'backtest_runs_total',
    'Total number of backtest runs',
    ['status']
)

# Microstructure metrics
micro_snapshot_age = Histogram(
    'micro_snapshot_age_seconds',
    'Age of microstructure snapshot in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)

# API latency metrics
api_request_duration = Histogram(
    'api_request_duration_seconds',
    'API request duration',
    ['endpoint', 'method'],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0]
)

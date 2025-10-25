import io, pandas as pd
from fastapi.testclient import TestClient
from app.main import app

def make_series(n=120):
    # rising then break, enough for indicators to compute
    import numpy as np
    t = list(range(n))
    base = 100 + np.cumsum(np.random.normal(0, 0.05, size=n))
    df = pd.DataFrame({
        "time": t,
        "open": base,
        "high": base + 0.2,
        "low":  base - 0.2,
        "close": base + np.sin(np.linspace(0,3.14,n))*0.3,
        "Volume": 100 + (np.random.rand(n)*40)
    })
    return df

def test_latest_signal_endpoint_ok():
    c = TestClient(app)
    df = make_series()
    buf = io.BytesIO(df.to_csv(index=False).encode())
    assert c.post("/data/upload", files={"file": ("s.csv", buf, "text/csv")}).status_code == 200
    r = c.get("/signals/latest")
    assert r.status_code == 200
    # either a signal dict or a message
    js = r.json()
    assert isinstance(js, dict)
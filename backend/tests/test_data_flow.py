import io, pandas as pd
from fastapi.testclient import TestClient
from app.main import app

CSV = pd.DataFrame({
    "time":[1,2,3,4,5,6,7,8,9,10],
    "open":[10,10,10,10,10,10,10,10,10,10],
    "high":[11,11,11,11,11,11,11,11,11,11],
    "low":[9,9,9,9,9,9,9,9,9,9],
    "close":[10,10.1,10.2,10.1,10.0,9.8,9.7,9.9,10.2,10.4],
    "Volume":[100,120,140,110,90,150,160,130,200,220],
})

def test_upload_and_swings():
    c = TestClient(app)
    buf = io.BytesIO(CSV.to_csv(index=False).encode())
    r = c.post("/data/upload", files={"file": ("tiny.csv", buf, "text/csv")})
    assert r.status_code == 200
    meta = r.json()
    assert meta["rows"] == 10
    r2 = c.get("/swings/")
    assert r2.status_code == 200
    assert "rows" in r2.json()
import requests, json, os

BASE = os.getenv("BASE", "http://localhost:8000")
print("Health:", requests.get(f"{BASE}/health/").json())

# Upload sample (expects ./sample.csv beside this script)
sample_csv = os.path.join(os.path.dirname(__file__), "sample.csv")
if os.path.exists(sample_csv):
    with open(sample_csv,"rb") as f:
        r = requests.post(f"{BASE}/data/upload", files={"file": ("sample.csv", f, "text/csv")})
    print("Upload:", r.status_code, r.text[:120])

    print("Swings:", requests.get(f"{BASE}/swings/").json())
    print("Signal:", requests.get(f"{BASE}/signals/latest").json())
    bt = requests.post(f"{BASE}/backtest/run", json={
        "atr_min":0.6, "volz_min":1.0, "bbw_min":0.005,
        "breakout_atr_mult":0.5, "vol_mult":1.5, "confirm_window":6
    }).json()
    print("Backtest summary:", bt.get("summary"))
else:
    print(f"Sample CSV not found at {sample_csv}")
    print("Using backend/data.csv if available...")
    backend_csv = "/app/backend/data.csv"
    if os.path.exists(backend_csv):
        with open(backend_csv,"rb") as f:
            r = requests.post(f"{BASE}/data/upload", files={"file": ("data.csv", f, "text/csv")})
        print("Upload:", r.status_code, r.text[:120])
        print("Swings:", requests.get(f"{BASE}/swings/").json())
        print("Signal:", requests.get(f"{BASE}/signals/latest").json())
    else:
        print("No CSV found for testing")

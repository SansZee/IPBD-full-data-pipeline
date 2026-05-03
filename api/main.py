from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import json
import os
import io

app = FastAPI(
    title="IPBD Energy Data API",
    description="API Gateway for ASEAN energy data pipeline",
    version="1.0.0"
)

DATA_DIR = "/home/portolas/kuliah/ipbd/IPBD-full-data-pipeline/scraper/data"

FILES = {
    "coal_production": "eia_coal_production.json",
    "electricity_imports": "eia_electricity_imports.json",
    "asean_bbm": "cnbc_asean_bbm_prices.json",
    "oil_prices": "oil_prices.json",
}

def load_json(filename: str) -> dict:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail=f"Data file not found: {filename}")
    with open(filepath, "r") as f:
        return json.load(f)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/topics")
def list_topics():
    return {"topics": list(FILES.keys())}

@app.get("/api/coal-production")
def get_coal_production():
    return load_json(FILES["coal_production"])

@app.get("/api/electricity-imports")
def get_electricity_imports():
    return load_json(FILES["electricity_imports"])

@app.get("/api/asean-bbm")
def get_asean_bbm():
    return load_json(FILES["asean_bbm"])

@app.get("/api/oil-prices")
def get_oil_prices():
    return load_json(FILES["oil_prices"])

@app.get("/api/oil-prices/current")
def get_oil_prices_current():
    data = load_json(FILES["oil_prices"])
    return {"scraped_at": data["scraped_at"], "source": data["source"], "current_prices": data["current_prices"]}

@app.get("/api/oil-prices/historical")
def get_oil_prices_historical():
    data = load_json(FILES["oil_prices"])
    return {"scraped_at": data["scraped_at"], "source": data["source"], "historical": data["historical"]}

@app.get("/api/coal-production/stream")
def stream_coal_production():
    data = load_json(FILES["coal_production"])
    return StreamingResponse(io.BytesIO(json.dumps(data).encode()), media_type="application/json")

@app.get("/api/electricity-imports/stream")
def stream_electricity_imports():
    data = load_json(FILES["electricity_imports"])
    return StreamingResponse(io.BytesIO(json.dumps(data).encode()), media_type="application/json")

@app.get("/api/asean-bbm/stream")
def stream_asean_bbm():
    data = load_json(FILES["asean_bbm"])
    return StreamingResponse(io.BytesIO(json.dumps(data).encode()), media_type="application/json")

@app.get("/api/oil-prices/stream")
def stream_oil_prices():
    data = load_json(FILES["oil_prices"])
    return StreamingResponse(io.BytesIO(json.dumps(data).encode()), media_type="application/json")

@app.get("/api/all")
def get_all_data():
    result = {}
    for key, filename in FILES.items():
        try:
            result[key] = load_json(filename)
        except HTTPException:
            result[key] = None
    return result

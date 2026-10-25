from __future__ import annotations
from typing import Dict, Any, List
import asyncio
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Mahlabahlasele", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_STATE: Dict[str, Any] = {
    "status": "stopped",
    "started_at": None,
    "config": {
        "api_name": "",
        "api_key": "",
        "api_secret": "",
        "risk_percent": 1.0,
        "drawdown_limit": 15.0
    },
    "metrics": {
        "pnl": 0.0,
        "win_rate": 0.0
    },
    "last_signal": "WAITING FOR DATA...",
    "circuit_breaker": {
        "is_open": False,
        "reason": None
    },
    "reward_weights": {
        "trend_following": 0.5,
        "mean_reversion": 0.5,
        "risk_tolerance": 0.5
    },
    "trade_log": []
}

def log_event(action: str, pnl: float = 0.0):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {"time": timestamp, "action": action, "pnl": pnl}
    BOT_STATE["trade_log"].append(entry)
    if len(BOT_STATE["trade_log"]) > 50:
        BOT_STATE["trade_log"].pop(0)

class ConfigUpdate(BaseModel):
    api_name: str | None = None
    api_key: str | None = None
    api_secret: str | None = None
    risk_percent: float | None = None
    drawdown_limit: float | None = None

@app.get("/status")
async def get_status():
    return BOT_STATE

@app.post("/api/config")
async def update_config(config: ConfigUpdate):
    for key, value in config.model_dump(exclude_unset=True).items():
        BOT_STATE["config"][key] = value
    log_event("Config Updated")
    return {"status": "success", "config": BOT_STATE["config"]}

@app.post("/api/start")
async def start_engine():
    if not BOT_STATE["config"]["api_key"] or not BOT_STATE["config"]["api_secret"]:
        raise HTTPException(status_code=400, detail="API credentials missing.")
    BOT_STATE["status"] = "running"
    BOT_STATE["started_at"] = datetime.now().isoformat()
    BOT_STATE["last_signal"] = "SCANNING MARKET..."
    log_event("Engine Started")
    return {"status": "running", "message": "Mahlabahlasele bot started"}

@app.post("/api/stop")
async def stop_engine():
    BOT_STATE["status"] = "stopped"
    BOT_STATE["last_signal"] = "STOPPED"
    log_event("Engine Stopped")
    return {"status": "stopped", "message": "Mahlabahlasele bot stopped"}

@app.

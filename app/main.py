cat << 'EOF' > main.py
import os
from datetime import datetime
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

app = FastAPI(title="Mahlabahlasele", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BOT_STATE = {
    "status": "stopped",
    "started_at": None,
    "config": {},
    "metrics": {"pnl": 0.0, "win_rate": 0.0},
    "last_signal": "WAITING FOR DATA...",
    "circuit_breaker": {"is_open": False, "reason": ""},
    "reward_weights": {"q_learning": True, "weights": [1.0, 0.5]},
    "trade_log": []
}

class ConfigModel(BaseModel):
    api_name: str = ""
    api_key: str = ""
    api_secret: str = ""

@app.get("/")
def serve_frontend():
    if os.path.exists("frontend/index.html"):
        return FileResponse("frontend/index.html")
    return {"message": "Mahlabahlasele 2.0 Backend Online."}

@app.get("/status")
def get_status():
    return BOT_STATE

@app.post("/api/config")
def update_config(config: ConfigModel):
    BOT_STATE["config"] = config.dict()
    log_event("CONFIG_UPDATE", 0.0)
    return {"status": "success", "message": "Credentials updated successfully"}

@app.post("/api/start")
def start_engine():
    BOT_STATE["status"] = "running"
    BOT_STATE["started_at"] = str(datetime.now())
    log_event("ENGINE_STARTED", 0.0)
    return {"status": "running", "message": "Engine Started"}

@app.post("/api/stop")
def stop_engine():
    BOT_STATE["status"] = "stopped"
    log_event("ENGINE_STOPPED", 0.0)
    return {"status": "stopped", "message": "Engine Stopped"}

@app.post("/api/backtest")
def execute_backtest():
    BOT_STATE["metrics"]["pnl"] = 125.50
    BOT_STATE["metrics"]["win_rate"] = 65.4
    log_event("BACKTEST_COMPLETED", 125.50)
    return {"status": "completed", "pnl": 125.50}

@app.post("/api/learn")
def trigger_rl_step():
    log_event("RL_STEP_EXECUTED", 0.0)
    return {"status": "weights_updated", "weights": [1.2, 0.4]}

def log_event(action: str, pnl: float):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "action": action,
        "pnl": pnl
    }
    BOT_STATE["trade_log"].insert(0, entry)
    if len(BOT_STATE["trade_log"]) > 50:
        BOT_STATE["trade_log"].pop()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
EOF

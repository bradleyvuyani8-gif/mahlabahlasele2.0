from __future__ import annotations

import asyncio
import json
import math
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


ROOT_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = ROOT_DIR / "frontend"

app = FastAPI(
    title="Mahlabahlasele",
    description="AI-powered algorithmic trading system for Termux",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# Models
# -----------------------------

class ConfigUpdate(BaseModel):
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    symbol: Optional[str] = None
    interval: Optional[str] = None
    trade_mode: Optional[str] = None
    risk_percent: Optional[float] = None
    drawdown_limit: Optional[float] = None
    max_positions: Optional[int] = None
    reward_alpha: Optional[float] = None
    reward_beta: Optional[float] = None
    reward_gamma: Optional[float] = None


class Candle(BaseModel):
    timestamp: Optional[str] = None
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0


class SignalRequest(BaseModel):
    symbol: str = "BTC/USDT"
    interval: str = "1h"
    candles: List[Candle] = Field(default_factory=list)


class TradeDecision(BaseModel):
    action: str
    confidence: float
    reason: str
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    lot_size: Optional[float] = None


# -----------------------------
# Utilities
# -----------------------------

def now_iso() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def sma(values: List[float], period: int = 14) -> float:
    if not values:
        return 0.0
    if len(values) < period:
        return sum(values) / len(values)
    return sum(values[-period:]) / period


def rsi(values: List[float], period: int = 14) -> float:
    if len(values) < period + 1:
        return 50.0
    gains: List[float] = []
    losses: List[float] = []
    for i in range(1, len(values)):
        delta = values[i] - values[i - 1]
        gains.append(max(delta, 0))
        losses.append(max(-delta, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def atr(highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> float:
    if len(closes) < 2:
        return 0.0
    trs: List[float] = []
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        trs.append(tr)
    if not trs:
        return 0.0
    if len(trs) < period:
        return sum(trs) / len(trs)
    return sum(trs[-period:]) / period


def reward_function(pnl: float, confidence: float, drawdown: float, volatility: float) -> float:
    pnl_score = clamp(pnl / 100.0, -10.0, 10.0)
    confidence_score = clamp(confidence, 0.0, 1.0)
    drawdown_penalty = clamp(drawdown / 100.0, 0.0, 2.0)
    volatility_penalty = clamp(volatility / 100.0, 0.0, 2.0)

    reward = (
        0.6 * pnl_score
        + 0.4 * confidence_score
        - 0.2 * drawdown_penalty
        - 0.1 * volatility_penalty
    )
    return reward


# -----------------------------
# Bot state
# -----------------------------

BOT_STATE: Dict[str, Any] = {
    "status": "idle",
    "started_at": None,
    "last_signal": None,
    "trade_log": [],
    "reward_weights": {
        "trend_following": 0.5,
        "mean_reversion": 0.5,
        "risk_tolerance": 0.5,
    },
    "metrics": {
        "pnl": 0.0,
        "confidence": 0.0,
        "drawdown": 0.0,
        "volatility": 0.0,
        "reward": 0.0,
        "win_rate": 0.0,
    },
    "config": {
        "api_key": os.getenv("API_KEY", ""),
        "api_secret": os.getenv("API_SECRET", ""),
        "symbol": os.getenv("DEFAULT_SYMBOL", "BTC/USDT"),
        "interval": os.getenv("DEFAULT_INTERVAL", "1h"),
        "trade_mode": os.getenv("TRADING_MODE", "paper"),
        "risk_percent": float(os.getenv("RISK_PERCENT", "1.0")),
        "drawdown_limit": float(os.getenv("DRAWDOWN_LIMIT", "15.0")),
        "max_positions": int(os.getenv("MAX_POSITIONS", "3")),
        "reward_alpha": float(os.getenv("REWARD_ALPHA", "0.6")),
        "reward_beta": float(os.getenv("REWARD_BETA", "0.4")),
        "reward_gamma": float(os.getenv("REWARD_GAMMA", "0.2")),
    },
}


def update_strategy_weights(reward_value: float) -> None:
    weights = BOT_STATE["reward_weights"]
    if reward_value > 0:
        weights["trend_following"] = clamp(weights["trend_following"] + 0.05, 0.0, 1.0)
        weights["mean_reversion"] = clamp(weights["mean_reversion"] + 0.03, 0.0, 1.0)
    elif reward_value < 0:
        weights["trend_following"] = clamp(weights["trend_following"] - 0.04, 0.0, 1.0)
        weights["mean_reversion"] = clamp(weights["mean_reversion"] + 0.04, 0.0, 1.0)
    weights["risk_tolerance"] = clamp(weights["risk_tolerance"] + (0.01 if reward_value > 0 else -0.01), 0.0, 1.0)


# -----------------------------
# Market analysis
# -----------------------------

def analyze_market(candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not candles:
        return {
            "trend": 0.0,
            "momentum": 0.0,
            "volatility": 0.0,
            "rsi": 50.0,
            "confidence": 0.1,
            "market_state": "neutral",
            "price": 0.0,
        }

    closes = [safe_float(c.get("close"), 0.0) for c in candles]
    highs = [safe_float(c.get("high"), 0.0) for c in candles]
    lows = [safe_float(c.get("low"), 0.0) for c in candles]

    fast_sma = sma(closes, 7)
    slow_sma = sma(closes, 21)
    current_rsi = rsi(closes, 14)
    vol = atr(highs, lows, closes, 14)
    price = closes[-1]

    trend = (fast_sma - slow_sma) / max(slow_sma, 1e-9)
    momentum = (fast_sma - slow_sma) / max(abs(slow_sma), 1e-9) * 100.0
    volatility = (vol / max(price, 1e-9)) * 100.0
    confidence = clamp(abs(trend) * 12.0 + abs(momentum) / 100.0, 0.1, 0.95)

    if current_rsi > 70:
        market_state = "overbought"
    elif current_rsi < 30:
        market_state = "oversold"
    else:
        market_state = "neutral"

    return {
        "trend": trend,
        "momentum": momentum,
        "volatility": volatility,
        "rsi": current_rsi,
        "confidence": confidence,
        "market_state": market_state,
        "price": price,
    }


def generate_signal_from_market(markets: Dict[str, Any]) -> Dict[str, Any]:
    weights = BOT_STATE["reward_weights"]
    trend_bias = weights.get("trend_following", 0.5)
    mean_rev_bias = weights.get("mean_reversion", 0.5)

    trend = markets["trend"]
    momentum = markets["momentum"]
    rsi = markets["rsi"]
    state = markets["market_state"]
    confidence = markets["confidence"]

    action = "hold"
    reason = "No strong edge"

    if state == "oversold" and rsi < 30:
        action = "buy"
        reason = f"Mean reversion trigger: RSI {rsi:.1f} and oversold condition"
    elif state == "overbought" and rsi > 70:
        action = "sell"
        reason = f"Mean reversion trigger: RSI {rsi:.1f} and overbought condition"
    elif trend > 0.01 and momentum > 0:
        action = "buy"
        reason = f"Trend-following trigger with trend {trend:.4f}, bias {trend_bias:.2f}"
    elif trend < -0.01 and momentum < 0:
        action = "sell"
        reason = f"Trend-following trigger with trend {trend:.4f}, bias {trend_bias:.2f}"
    else:
        action = "hold"

    strength = clamp((0.4 + trend_bias * 0.4 + mean_rev_bias * 0.2) * confidence, 0.0, 1.0)

    return {
        "action": action,
        "confidence": round(strength, 4),
        "reason": reason,
    }


def risk_plan_for_signal(signal: Dict[str, Any], market: Dict[str, Any]) -> Dict[str, Any]:
    price = market["price"]
    volatility = market["volatility"]
    if price <= 0 or signal["action"] == "hold":
        return {
            "action": "hold",
            "stop_loss": None,
            "take_profit": None,
            "lot_size": 0.0,
            "risk_amount": 0.0,
        }

    atr_buffer = max((volatility / 100.0) * price, 0.01)
    risk_amount = 1000.0 * (BOT_STATE["config"]["risk_percent"] / 100.0)

    if signal["action"] == "buy":
        stop_loss = price - atr_buffer
        take_profit = price + (atr_buffer * 2.0)
    else:
        stop_loss = price + atr_buffer
        take_profit = price - (atr_buffer * 2.0)

    lot_size = max(0.01, risk_amount / max(atr_buffer, 1e-9) / 1000.0)

    return {
        "action": signal["action"],
        "stop_loss": round(stop_loss, 6),
        "take_profit": round(take_profit, 6),
        "lot_size": round(lot_size, 6),
        "risk_amount": round(risk_amount, 2),
    }


# -----------------------------
# Routes
# -----------------------------

@app.get("/")
async def root():
    if FRONTEND_DIR.exists():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(index_file)
    return {"message": "Mahlabahlasele API is running"}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "Mahlabahlasele",
        "time": now_iso(),
        "mode": BOT_STATE["config"]["trade_mode"],
    }


@app.get("/api/status")
async def status():
    return {
        "status": BOT_STATE["status"],
        "started_at": BOT_STATE["started_at"],
        "last_signal": BOT_STATE["last_signal"],
        "reward_weights": BOT_STATE["reward_weights"],
        "metrics": BOT_STATE["metrics"],
        "config": BOT_STATE["config"],
    }


@app.get("/api/config")
async def get_config():
    return BOT_STATE["config"]


@app.post("/api/config")
async def update_config(payload: ConfigUpdate):
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        if value is not None:
            BOT_STATE["config"][key] = value
    return BOT_STATE["config"]


@app.post("/api/signal")
async def signal_endpoint(payload: SignalRequest):
    candle_dicts = [c.model_dump() for c in payload.candles]
    market = analyze_market(candle_dicts)
    signal = generate_signal_from_market(market)
    risk = risk_plan_for_signal(signal, market)

    decision = {
        "symbol": payload.symbol,
        "interval": payload.interval,
        "market": market,
        "signal": signal,
        "risk": risk,
        "time": now_iso(),
    }

    BOT_STATE["last_signal"] = decision
    return decision


@app.post("/api/backtest")
async def backtest_endpoint(payload: SignalRequest):
    candle_dicts = [c.model_dump() for c in payload.candles]
    if len(candle_dicts) < 20:
        raise HTTPException(status_code=400, detail="Need at least 20 candles for backtesting")

    total_profit = 0.0
    wins = 0
    trades = 0

    for i in range(10, len(candle_dicts) - 1):
        segment = candle_dicts[max(0, i - 30): i + 1]
        market = analyze_market(segment)
        signal = generate_signal_from_market(market)

        if signal["action"] == "hold":
            continue

        entry = float(segment[-1]["close"])
        exit_price = float(candle_dicts[i + 1]["close"])

        if signal["action"] == "buy":
            pnl = ((exit_price - entry) / entry) * 100.0
        elif signal["action"] == "sell":
            pnl = ((entry - exit_price) / entry) * 100.0
        else:
            pnl = 0.0

        total_profit += pnl
        trades += 1
        if pnl > 0:
            wins += 1

    win_rate = (wins / trades * 100.0) if trades else 0.0

    return {
        "symbol": payload.symbol,
        "interval": payload.interval,
        "trades": trades,
        "net_profit_percent": round(total_profit, 4),
        "win_rate": round(win_rate, 2),
        "time": now_iso(),
    }


@app.post("/api/learn")
async def learn_endpoint(payload: Dict[str, Any]):
    pnl = safe_float(payload.get("pnl"), 0.0)
    confidence = safe_float(payload.get("confidence"), 0.0)
    drawdown = safe_float(payload.get("drawdown"), 0.0)
    volatility = safe_float(payload.get("volatility"), 0.0)

    reward_value = reward_function(pnl, confidence, drawdown, volatility)
    update_strategy_weights(reward_value)

    BOT_STATE["metrics"]["pnl"] = pnl
    BOT_STATE["metrics"]["confidence"] = confidence
    BOT_STATE["metrics"]["drawdown"] = drawdown
    BOT_STATE["metrics"]["volatility"] = volatility
    BOT_STATE["metrics"]["reward"] = reward_value

    BOT_STATE["trade_log"].append({
        "time": now_iso(),
        "pnl": pnl,
        "reward": reward_value,
        "confidence": confidence,
        "drawdown": drawdown,
        "volatility": volatility,
    })
    BOT_STATE["trade_log"] = BOT_STATE["trade_log"][-100:]

    return {
        "reward": round(reward_value, 4),
        "weights": BOT_STATE["reward_weights"],
        "message": "Learning update applied",
    }


@app.post("/api/start")
async def start_bot():
    BOT_STATE["status"] = "running"
    BOT_STATE["started_at"] = now_iso()
    return {"status": "running", "message": "Mahlabahlasele bot started"}


@app.post("/api/stop")
async def stop_bot():
    BOT_STATE["status"] = "stopped"
    return {"status": "stopped", "message": "Mahlabahlasele bot stopped"}


# -----------------------------
# Web terminal
# -----------------------------

@app.websocket("/ws/terminal")
async def terminal_socket(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            command = data.strip()
            if not command:
                continue

            try:
                proc = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                )
                output, _ = proc.communicate(timeout=30)
                await websocket.send_text(output or f"Command executed: {command}\n")
            except Exception as exc:
                await websocket.send_text(f"Error: {str(exc)}\n")
    except WebSocketDisconnect:
        pass


# -----------------------------
# Serve frontend files
# -----------------------------

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/terminal")
    async def terminal_page():
        terminal_file = FRONTEND_DIR / "terminal.html"
        if terminal_file.exists():
            return FileResponse(terminal_file)
        return {"message": "terminal.html missing"}

    @app.get("/dashboard")
    async def dashboard_page():
        dashboard_file = FRONTEND_DIR / "index.html"
        if dashboard_file.exists():
            return FileResponse(dashboard_file)
        return {"message": "index.html missing"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
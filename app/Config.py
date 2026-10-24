from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

@dataclass
class Settings:
    app_name: str = "Mahlabahlasele"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    exchange_name: str = "binance"
    api_key: str = ""
    api_secret: str = ""
    trading_mode: str = "paper"
    account_balance: float = 1000.0
    risk_percent: float = 1.0
    max_positions: int = 3
    drawdown_limit: float = 15.0
    circuit_breaker_enabled: bool = True

    default_symbol: str = "BTC/USDT"
    default_interval: str = "1h"
    reward_alpha: float = 0.6
    reward_beta: float = 0.4
    reward_gamma: float = 0.2

    portfolio_history: list = field(default_factory=list)

    @classmethod
    def load(cls) -> "Settings":
        return cls(
            app_name=os.getenv("APP_NAME", "Mahlabahlasele"),
            app_host=os.getenv("APP_HOST", "0.0.0.0"),
            app_port=int(os.getenv("APP_PORT", "8000")),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            exchange_name=os.getenv("EXCHANGE_NAME", "binance"),
            api_key=os.getenv("API_KEY", ""),
            api_secret=os.getenv("API_SECRET", ""),
            trading_mode=os.getenv("TRADING_MODE", "paper"),
            account_balance=float(os.getenv("ACCOUNT_BALANCE", "1000.0")),
            risk_percent=float(os.getenv("RISK_PERCENT", "1.0")),
            max_positions=int(os.getenv("MAX_POSITIONS", "3")),
            drawdown_limit=float(os.getenv("DRAWDOWN_LIMIT", "15.0")),
            circuit_breaker_enabled=os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true",
            default_symbol=os.getenv("DEFAULT_SYMBOL", "BTC/USDT"),
            default_interval=os.getenv("DEFAULT_INTERVAL", "1h"),
            reward_alpha=float(os.getenv("REWARD_ALPHA", "0.6")),
            reward_beta=float(os.getenv("REWARD_BETA", "0.4")),
            reward_gamma=float(os.getenv("REWARD_GAMMA", "0.2")),
        )

settings = Settings.load()

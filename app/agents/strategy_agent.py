from __future__ import annotations
from typing import Dict, List

class StrategyAgent:
    def __init__(self):
        self.name = "StrategyAgent"

    def make_signal(self, market_analysis: dict) -> dict:
        rsi = float(market_analysis.get('rsi', 50.0))
        trend = float(market_analysis.get('trend', 0.0))

        action = "hold"
        confidence = 0.0

        if rsi < 30.0 and trend >= 0:
            action = "buy"
            confidence = 0.8
        elif rsi > 70.0 and trend <= 0:
            action = "sell"
            confidence = 0.8

        return {
            "action": action,
            "confidence": confidence,
            "stop_loss": float(market_analysis.get('price', 0.0)) * 0.98,
            "take_profit": float(market_analysis.get('price', 0.0)) * 1.04
        }


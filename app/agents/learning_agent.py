from __future__ import annotations
from typing import Dict, Any

class LearningAgent:
    def __init__(self):
        self.name = "LearningAgent"
        self.performance_history = []

    def score_trade(self, signal: dict, pnl: float) -> dict:
        confidence = float(signal.get("confidence", 0.0))
        strength = float(signal.get("strength", 0.0))
        
        score = (pnl / 100.0) * 10 + confidence * 2 + strength
        
        self.performance_history.append({
            "score": float(score),
            "pnl": float(pnl),
            "confidence": confidence
        })
        
        # Keep memory bounded
        if len(self.performance_history) > 1000:
            self.performance_history.pop(0)

        return {"score": float(score), "updated": True}


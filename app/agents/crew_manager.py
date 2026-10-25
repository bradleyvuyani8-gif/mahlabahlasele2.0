from __future__ import annotations
from typing import Any, Dict, List

try:
    from crewai import Agent, Crew, Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False
    Agent = None
    Crew = None
    Task = None

from app.agents.learning_agent import LearningAgent
from app.agents.market_analyst import MarketAnalystAgent
from app.agents.strategy_agent import StrategyAgent

class CrewManager:
    def __init__(self, account_balance: float = 1000.0):
        self.market_agent = MarketAnalystAgent()
        self.strategy_agent = StrategyAgent()
        self.learning_agent = LearningAgent()
        self.account_balance = float(account_balance)

    def run_cycle(self, candles: list[dict]) -> dict:
        market_analysis = self.market_agent.analyze(candles)
        signal = self.strategy_agent.make_signal(market_analysis)

        decision = {
            "market_analysis": market_analysis,
            "signal": signal,
            "account_balance": self.account_balance
        }
        return decision


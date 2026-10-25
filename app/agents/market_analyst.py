from __future__ import annotations
from typing import Dict, List
import pandas as pd

def backtest_strategy(df: pd.DataFrame, initial_balance: float = 1000.0) -> dict:
    if df.empty or 'close' not in df.columns:
        return {"error": "Invalid or empty dataframe provided"}

    balance = initial_balance
    peak = initial_balance
    max_drawdown = 0.0
    wins = 0
    losses = 0
    profits = []
    trades = 0

    for i in range(len(df) - 2):
        entry_price = float(df.iloc[i]['close'])
        exit_price = float(df.iloc[i + 2]['close'])
        
        # Simple long execution simulation placeholder
        pnl = exit_price - entry_price
        pct_return = (pnl / entry_price) * 100 if entry_price > 0 else 0.0
        
        balance += pnl
        profits.append(pnl)
        trades += 1

        if balance > peak:
            peak = balance
        
        if peak > 0:
            drawdown = ((peak - balance) / peak) * 100
            if drawdown > max_drawdown:
                max_drawdown = drawdown

        if pnl > 0:
            wins += 1
        else:
            losses += 1

    win_rate = (wins / trades * 100) if trades > 0 else 0.0
    net_profit = balance - initial_balance

    return {
        "net_profit": net_profit,
        "win_rate": win_rate,
        "trades": trades,
        "max_drawdown": max_drawdown
    }


import pandas as pd
from .technical import indicators, rsi_signal

def rsi_backtest(df: pd.DataFrame, initial_cash: float = 10_000) -> dict:
    if initial_cash <= 0:
        raise ValueError("initial_cash must be positive")
    data = indicators(df).dropna(subset=["RSI14"])
    cash = float(initial_cash)
    shares = 0.0
    trades = 0
    for _, row in data.iterrows():
        price = float(row["Close"])
        signal = rsi_signal(row)
        if signal == "BUY" and shares == 0 and price > 0:
            shares = cash / price
            cash = 0.0
            trades += 1
        elif signal == "SELL" and shares > 0:
            cash = shares * price
            shares = 0.0
            trades += 1
    final_equity = cash + shares * float(data["Close"].iloc[-1])
    return {"initial_cash": initial_cash, "final_equity": final_equity, "return_pct": (final_equity / initial_cash - 1) * 100, "trades": trades}

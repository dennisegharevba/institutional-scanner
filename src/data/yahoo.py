"""Sync yfinance fetcher + technical analysis suite."""
from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st
from src.core.config import MARKETS


@st.cache_data(ttl=900, show_spinner=False)
def fetch_ohlcv(symbol: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    meta = MARKETS.get(symbol)
    if not meta:
        return pd.DataFrame()
    try:
        df = yf.download(meta["yahoo"], period=period, interval=interval,
                         auto_adjust=True, progress=False)
        if df.empty:
            return df
        df.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in df.columns]
        if "adj close" in df.columns:
            df = df.rename(columns={"adj close": "close"})
        df = df[["open", "high", "low", "close", "volume"]].dropna()
        return df
    except Exception:
        return pd.DataFrame()


def enrich(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or len(df) < 5:
        return df
    c, h, l = df["close"], df["high"], df["low"]
    for p in (9, 20, 50, 100, 200):
        df[f"ma_{p}"] = c.rolling(p).mean()
    pc = c.shift(1)
    tr = pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    df["atr_14"] = tr.rolling(14).mean()
    delta = c.diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    df["rsi_14"] = 100 - (100 / (1 + gain / loss.replace(0, np.nan)))
    ema12 = c.ewm(span=12, adjust=False).mean()
    ema26 = c.ewm(span=26, adjust=False).mean()
    df["macd"]        = ema12 - ema26
    df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
    df["macd_hist"]   = df["macd"] - df["macd_signal"]
    ma20 = c.rolling(20).mean(); std20 = c.rolling(20).std()
    df["bb_upper"] = ma20 + 2 * std20
    df["bb_lower"] = ma20 - 2 * std20
    df["bb_pct"]   = (c - df["bb_lower"]) / (df["bb_upper"] - df["bb_lower"])
    return df


def score_technical(df: pd.DataFrame) -> dict:
    if df.empty or len(df) < 50:
        return {"total": 50.0, "bias": "neutral", "components": {}}
    last = df.iloc[-1]
    c    = last["close"]
    scores = {}
    ma_bulls = sum(1 for p in (20, 50, 100, 200)
                   if not pd.isna(last.get(f"ma_{p}", float("nan"))) and c > last[f"ma_{p}"])
    scores["ma_alignment"] = ma_bulls / 4 * 100
    rsi = last.get("rsi_14")
    scores["rsi"] = 65 if (rsi and 40 <= rsi <= 70) else 35
    hist = last.get("macd_hist")
    scores["macd"] = 70 if (hist and hist > 0) else 30
    bb = last.get("bb_pct")
    scores["bb"] = 75 if (bb and bb < 0.35) else (30 if (bb and bb > 0.75) else 50)
    hh = (df["high"].rolling(5).max() > df["high"].shift(1).rolling(5).max()).tail(10).sum()
    scores["structure"] = min(100, float(hh) * 15)
    total = sum(scores.values()) / len(scores)
    bias  = "bullish" if total >= 60 else ("bearish" if total <= 40 else "neutral")
    return {"total": round(total, 1), "bias": bias, "components": scores,
            "price": float(last.get("close", 0) or 0),
            "atr":   float(last.get("atr_14", 0) or 0),
            "rsi":   float(rsi or 0),
            "ma_50": float(last.get("ma_50", 0) or 0),
            "ma_200":float(last.get("ma_200", 0) or 0)}


@st.cache_data(ttl=900, show_spinner=False)
def fetch_and_score(symbol: str) -> dict:
    df   = fetch_ohlcv(symbol)
    df   = enrich(df)
    tech = score_technical(df)
    tech["symbol"] = symbol
    return tech

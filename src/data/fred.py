"""Sync FRED fetcher — uses requests + st.cache_data instead of httpx + Redis."""
from __future__ import annotations
from typing import Optional
import requests
import pandas as pd
import streamlit as st
from tenacity import retry, stop_after_attempt, wait_exponential
from src.core.config import get_settings

settings = get_settings()
FRED_BASE = "https://api.stlouisfed.org/fred/series/observations"


@st.cache_data(ttl=3600 * 4, show_spinner=False)
def fetch_series(series_id: str, limit: int = 400) -> pd.Series:
    """Fetch a FRED series, cached for 4 hours."""
    if not settings.fred_api_key:
        return pd.Series(dtype=float, name=series_id)
    try:
        resp = requests.get(FRED_BASE, params={
            "series_id": series_id, "api_key": settings.fred_api_key,
            "file_type": "json", "sort_order": "desc", "limit": str(limit),
        }, timeout=15)
        resp.raise_for_status()
        obs = resp.json().get("observations", [])
        records = {
            o["date"]: float(o["value"])
            for o in obs if o.get("value") not in (".", "", None)
        }
        s = pd.Series(records, dtype=float, name=series_id).sort_index()
        s.index = pd.to_datetime(s.index)
        return s
    except Exception:
        return pd.Series(dtype=float, name=series_id)


def fetch_multiple(series_ids: list[str], limit: int = 400) -> dict[str, pd.Series]:
    return {sid: fetch_series(sid, limit) for sid in series_ids}


# ── Transform helpers (identical to FastAPI version) ─────────────────────────

def yoy(s: pd.Series) -> Optional[float]:
    if s is None or s.empty: return None
    v = s.iloc[-1]
    ya = s.asof(s.index[-1] - pd.DateOffset(years=1))
    if pd.isna(ya) or ya == 0: return None
    return float((v / ya - 1) * 100)

def mom(s: pd.Series) -> Optional[float]:
    if s is None or s.empty: return None
    v = s.iloc[-1]
    ma = s.asof(s.index[-1] - pd.DateOffset(months=1))
    if pd.isna(ma) or ma == 0: return None
    return float((v / ma - 1) * 100)

def latest(s: pd.Series, n: int = 0) -> Optional[float]:
    if s is None or s.empty or len(s) <= n: return None
    return float(s.iloc[-1 - n])

def chg(s: pd.Series, periods: int = 1) -> Optional[float]:
    if s is None or s.empty or len(s) < periods + 1: return None
    return float(s.iloc[-1] - s.iloc[-1 - periods])

def gdp_annualized(s: pd.Series, n: int = 0) -> Optional[float]:
    if s is None or s.empty or len(s) < n + 2: return None
    a, b = s.iloc[-1 - n], s.iloc[-2 - n]
    if b == 0: return None
    return float(((a / b) ** 4 - 1) * 100)

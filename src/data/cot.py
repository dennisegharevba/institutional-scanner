"""Sync CFTC COT downloader + COT Index calculator."""
from __future__ import annotations
import io, zipfile
from datetime import datetime
from typing import Optional
import pandas as pd
import requests
import streamlit as st
from src.core.config import MARKETS

CFTC_BASE = "https://www.cftc.gov/files/dea/history"
COLS = {
    "Report_Date_as_YYYY-MM-DD":  "report_date",
    "CFTC_Contract_Market_Code":  "cot_code",
    "Comm_Positions_Long_All":    "comm_long",
    "Comm_Positions_Short_All":   "comm_short",
    "NonComm_Positions_Long_All": "spec_long",
    "NonComm_Positions_Short_All":"spec_short",
    "Open_Interest_All":          "open_interest",
}


@st.cache_data(ttl=3600 * 24, show_spinner=False)
def fetch_cot_raw(year: int) -> Optional[pd.DataFrame]:
    url = f"{CFTC_BASE}/fut_fin_xls_{year}.zip"
    try:
        resp = requests.get(url, timeout=60)
        resp.raise_for_status()
        z = zipfile.ZipFile(io.BytesIO(resp.content))
        csv_name = [n for n in z.namelist() if n.endswith((".txt", ".csv"))][0]
        df = pd.read_csv(z.open(csv_name), low_memory=False)
        keep = [c for c in COLS if c in df.columns]
        df = df[keep].rename(columns=COLS)
        for col in [c for c in df.columns if c not in ("report_date", "cot_code")]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df["report_date"] = pd.to_datetime(df["report_date"], errors="coerce")
        return df.dropna(subset=["report_date", "cot_code"])
    except Exception:
        return None


@st.cache_data(ttl=3600 * 6, show_spinner=False)
def get_latest_cot(symbol: str) -> Optional[dict]:
    meta = MARKETS.get(symbol)
    cot_code = meta.get("cot_code") if meta else None
    if not cot_code:
        return None
    yr = datetime.now().year
    raw = fetch_cot_raw(yr) or fetch_cot_raw(yr - 1)
    if raw is None:
        return None
    subset = raw[raw["cot_code"].astype(str).str.strip() == str(cot_code).strip()]
    if subset.empty:
        return None
    subset = subset.sort_values("report_date").copy()
    subset["comm_net"] = subset["comm_long"] - subset["comm_short"]
    subset["spec_net"] = subset["spec_long"] - subset["spec_short"]
    roll = subset["comm_net"].rolling(156, min_periods=26)
    rng  = (roll.max() - roll.min()).replace(0, float("nan"))
    subset["cot_index"]    = ((subset["comm_net"] - roll.min()) / rng * 100).round(1)
    subset["net_change_wk"]= subset["comm_net"].diff()
    last = subset.iloc[-1]
    idx  = float(last.get("cot_index") or 50)
    bias = "bullish" if idx >= 70 else ("bearish" if idx <= 30 else "neutral")
    return {
        "symbol": symbol, "report_date": str(last["report_date"].date()),
        "commercials_net": float(last.get("comm_net") or 0),
        "large_specs_net": float(last.get("spec_net") or 0),
        "open_interest":   float(last.get("open_interest") or 0),
        "cot_index":       round(idx, 1),
        "net_change_wk":   float(last.get("net_change_wk") or 0),
        "institutional_bias": bias,
        "bias_score": round(idx, 1),
    }

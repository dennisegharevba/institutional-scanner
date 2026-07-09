"""
Central config — reads from st.secrets on Streamlit Cloud,
falls back to environment variables / .env for local dev.
"""
from __future__ import annotations
import os
from functools import lru_cache

try:
    import streamlit as st
    def _get(key: str, default: str = "") -> str:
        try:
            return st.secrets[key]
        except Exception:
            return os.environ.get(key, default)
except ImportError:
    def _get(key: str, default: str = "") -> str:
        return os.environ.get(key, default)


class Settings:
    anthropic_api_key:  str = _get("ANTHROPIC_API_KEY")
    openai_api_key:     str = _get("OPENAI_API_KEY")
    ai_provider:        str = _get("AI_PROVIDER", "anthropic")
    fred_api_key:       str = _get("FRED_API_KEY")
    telegram_bot_token: str = _get("TELEGRAM_BOT_TOKEN")
    telegram_chat_id:   str = _get("TELEGRAM_CHAT_ID")
    telegram_admin_ids: str = _get("TELEGRAM_ADMIN_IDS")
    signal_threshold:   int = int(_get("SIGNAL_THRESHOLD", "65"))
    scan_ttl_minutes:   int = int(_get("SCAN_TTL_MINUTES", "15"))
    database_url:       str = "sqlite:///scanner.db"

    @property
    def admin_ids_list(self) -> list[int]:
        if not self.telegram_admin_ids:
            return []
        return [int(x.strip()) for x in self.telegram_admin_ids.split(",") if x.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


# ── Market catalogue ──────────────────────────────────────────────────────────

MARKETS: dict[str, dict] = {
    "GC":    {"name": "Gold",        "class": "commodity", "yahoo": "GC=F",    "cot_code": "088691"},
    "SI":    {"name": "Silver",      "class": "commodity", "yahoo": "SI=F",    "cot_code": "084691"},
    "PL":    {"name": "Platinum",    "class": "commodity", "yahoo": "PL=F",    "cot_code": "076651"},
    "CL":    {"name": "WTI Crude",   "class": "energy",    "yahoo": "CL=F",    "cot_code": "067651"},
    "NG":    {"name": "Nat Gas",     "class": "energy",    "yahoo": "NG=F",    "cot_code": "023651"},
    "HG":    {"name": "Copper",      "class": "commodity", "yahoo": "HG=F",    "cot_code": "085692"},
    "ES":    {"name": "S&P 500",     "class": "equity",    "yahoo": "ES=F",    "cot_code": "13874A"},
    "NQ":    {"name": "Nasdaq 100",  "class": "equity",    "yahoo": "NQ=F",    "cot_code": "209742"},
    "YM":    {"name": "Dow Jones",   "class": "equity",    "yahoo": "YM=F",    "cot_code": "124603"},
    "RTY":   {"name": "Russell 2000","class": "equity",    "yahoo": "RTY=F",   "cot_code": "239742"},
    "EURUSD":{"name": "EUR/USD",     "class": "forex",     "yahoo": "EURUSD=X","cot_code": "099741"},
    "GBPUSD":{"name": "GBP/USD",     "class": "forex",     "yahoo": "GBPUSD=X","cot_code": "096742"},
    "USDJPY":{"name": "USD/JPY",     "class": "forex",     "yahoo": "USDJPY=X","cot_code": "097741"},
    "USDCHF":{"name": "USD/CHF",     "class": "forex",     "yahoo": "USDCHF=X","cot_code": "092741"},
    "AUDUSD":{"name": "AUD/USD",     "class": "forex",     "yahoo": "AUDUSD=X","cot_code": "232741"},
    "USDCAD":{"name": "USD/CAD",     "class": "forex",     "yahoo": "USDCAD=X","cot_code": "090741"},
    "BTC":   {"name": "Bitcoin",     "class": "crypto",    "yahoo": "BTC-USD", "cot_code": None},
    "ETH":   {"name": "Ethereum",    "class": "crypto",    "yahoo": "ETH-USD", "cot_code": None},
}

# ── Central bank catalogue ────────────────────────────────────────────────────

CENTRAL_BANKS: dict[str, dict] = {
    "FED": {"name": "Federal Reserve",          "currency": "USD"},
    "ECB": {"name": "European Central Bank",    "currency": "EUR"},
    "BOJ": {"name": "Bank of Japan",             "currency": "JPY"},
    "BOE": {"name": "Bank of England",           "currency": "GBP"},
    "BOC": {"name": "Bank of Canada",            "currency": "CAD"},
    "RBA": {"name": "Reserve Bank of Australia", "currency": "AUD"},
    "SNB": {"name": "Swiss National Bank",       "currency": "CHF"},
    "PBOC":{"name": "People's Bank of China",    "currency": "CNY"},
}

FRED_SERIES = {
    "cpi":          "CPIAUCSL",   "core_cpi":    "CPILFESL",
    "pce":          "PCEPI",      "core_pce":    "PCEPILFE",
    "ppi":          "PPIACO",
    "nfp":          "PAYEMS",     "unemployment":"UNRATE",
    "participation":"CIVPART",    "jobless_init":"ICSA",
    "jobless_cont": "CCSA",       "jolts_open":  "JTSJOL",
    "ahe":          "CES0500000003",
    "gdp":          "GDPC1",
    "y2":           "DGS2",       "y5":          "DGS5",
    "y10":          "DGS10",      "y30":         "DGS30",
    "tips_10y":     "DFII10",     "breakeven_10y":"T10YIE",
    "fed_upper":    "DFEDTARU",   "fed_lower":   "DFEDTARL",
    "vix":          "VIXCLS",     "nfci":        "NFCI",
}

MODULE_WEIGHTS = {
    "technical": 20, "macro": 20, "cot": 15,
    "central_bank": 15, "inflation": 10,
    "labour": 10, "sentiment": 5, "seasonality": 5,
}

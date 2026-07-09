"""
All macro analysis modules — sync versions for Streamlit.
Inflation · Labour · Bond · Sentiment
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
import streamlit as st
from src.core.config import FRED_SERIES
from src.data.fred import chg, fetch_multiple, gdp_annualized, latest, mom, yoy


# ═══════════════════════════════════════════════════════════════════════════
# INFLATION
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class InflationSnapshot:
    cpi_yoy:        Optional[float] = None
    cpi_mom:        Optional[float] = None
    core_cpi_yoy:   Optional[float] = None
    core_cpi_mom:   Optional[float] = None
    pce_yoy:        Optional[float] = None
    core_pce_yoy:   Optional[float] = None
    core_pce_mom:   Optional[float] = None
    ppi_yoy:        Optional[float] = None
    breakeven_10y:  Optional[float] = None
    real_yield_10y: Optional[float] = None
    breakeven_chg_20d:   Optional[float] = None
    real_yield_chg_20d:  Optional[float] = None
    ahe_yoy:        Optional[float] = None
    bias:           str   = "neutral"
    inflation_score:float = 50.0
    risk_label:     str   = "on-target"
    summary:        str   = ""
    drivers:        list  = field(default_factory=list)


@st.cache_data(ttl=3600, show_spinner=False)
def run_inflation() -> InflationSnapshot:
    ids = [FRED_SERIES["cpi"], FRED_SERIES["core_cpi"], FRED_SERIES["pce"],
           FRED_SERIES["core_pce"], FRED_SERIES["ppi"], FRED_SERIES["ahe"],
           FRED_SERIES["breakeven_10y"], FRED_SERIES["tips_10y"]]
    d = fetch_multiple(ids, limit=800)
    snap = InflationSnapshot(
        cpi_yoy=yoy(d[FRED_SERIES["cpi"]]), cpi_mom=mom(d[FRED_SERIES["cpi"]]),
        core_cpi_yoy=yoy(d[FRED_SERIES["core_cpi"]]), core_cpi_mom=mom(d[FRED_SERIES["core_cpi"]]),
        pce_yoy=yoy(d[FRED_SERIES["pce"]]), core_pce_yoy=yoy(d[FRED_SERIES["core_pce"]]),
        core_pce_mom=mom(d[FRED_SERIES["core_pce"]]), ppi_yoy=yoy(d[FRED_SERIES["ppi"]]),
        breakeven_10y=latest(d[FRED_SERIES["breakeven_10y"]]),
        real_yield_10y=latest(d[FRED_SERIES["tips_10y"]]),
        breakeven_chg_20d=chg(d[FRED_SERIES["breakeven_10y"]], 20),
        real_yield_chg_20d=chg(d[FRED_SERIES["tips_10y"]], 20),
        ahe_yoy=yoy(d[FRED_SERIES["ahe"]]),
    )
    return _score_inflation(snap)


def _score_inflation(snap: InflationSnapshot) -> InflationSnapshot:
    votes, drivers = [], []
    def _v(label, val, hot, cool):
        if val is None: return
        if val > hot:   votes.append(1);  drivers.append(f"{label} {val:.1f}% — above target")
        elif val < cool:votes.append(-1); drivers.append(f"{label} {val:.1f}% — below target")
        else:           votes.append(0);  drivers.append(f"{label} {val:.1f}% — near target")
    _v("Core PCE YoY",snap.core_pce_yoy, 3.0, 1.5); _v("Core PCE YoY",snap.core_pce_yoy,3.0,1.5)
    _v("Core CPI YoY",snap.core_cpi_yoy, 3.5, 1.5); _v("Core CPI YoY",snap.core_cpi_yoy,3.5,1.5)
    _v("Headline CPI",snap.cpi_yoy, 4.0, 1.0)
    _v("PPI YoY",     snap.ppi_yoy, 4.0, 0.0)
    _v("AHE YoY",     snap.ahe_yoy, 4.0, 2.0)
    if not votes:
        snap.summary = "Inflation data loading."; snap.drivers = drivers; return snap
    hot = sum(1 for v in votes if v == 1)
    cool= sum(1 for v in votes if v == -1)
    score = max(0, min(100, 50 + (hot - cool) / len(votes) * 40))
    snap.inflation_score = round(score, 1)
    snap.bias      = "hawkish" if score >= 60 else ("dovish" if score <= 40 else "neutral")
    snap.risk_label= "sticky-high" if score >= 68 else ("rising" if score >= 55 else ("falling" if score <= 40 else "on-target"))
    snap.drivers   = drivers
    snap.summary   = f"Core PCE {snap.core_pce_yoy:.1f}% YoY — {snap.risk_label}. Bias: {snap.bias.upper()}." if snap.core_pce_yoy else "Loading."
    return snap


# ═══════════════════════════════════════════════════════════════════════════
# LABOUR
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class LabourSnapshot:
    nfp_change_k:      Optional[float] = None
    unemployment_rate: Optional[float] = None
    participation_rate:Optional[float] = None
    jobless_claims:    Optional[float] = None
    jolts_openings_m:  Optional[float] = None
    ahe_yoy:           Optional[float] = None
    bias:              str   = "neutral"
    labour_score:      float = 50.0
    summary:           str   = ""
    drivers:           list  = field(default_factory=list)


@st.cache_data(ttl=3600, show_spinner=False)
def run_labour() -> LabourSnapshot:
    ids = [FRED_SERIES["nfp"], FRED_SERIES["unemployment"], FRED_SERIES["participation"],
           FRED_SERIES["jobless_init"], FRED_SERIES["jolts_open"], FRED_SERIES["ahe"]]
    d = fetch_multiple(ids, limit=600)
    jolts_raw = latest(d[FRED_SERIES["jolts_open"]])
    snap = LabourSnapshot(
        nfp_change_k=chg(d[FRED_SERIES["nfp"]], 1),
        unemployment_rate=latest(d[FRED_SERIES["unemployment"]]),
        participation_rate=latest(d[FRED_SERIES["participation"]]),
        jobless_claims=latest(d[FRED_SERIES["jobless_init"]]),
        jolts_openings_m=jolts_raw / 1000 if jolts_raw else None,
        ahe_yoy=yoy(d[FRED_SERIES["ahe"]]),
    )
    return _score_labour(snap)


def _score_labour(snap: LabourSnapshot) -> LabourSnapshot:
    votes, drivers = [], []
    if snap.nfp_change_k is not None:
        v = 2 if snap.nfp_change_k > 200 else (1 if snap.nfp_change_k > 100 else (-2 if snap.nfp_change_k < 0 else 0))
        votes.append(v); drivers.append(f"NFP {snap.nfp_change_k:+.0f}k")
    if snap.unemployment_rate is not None:
        v = 2 if snap.unemployment_rate < 4.0 else (1 if snap.unemployment_rate < 4.5 else (-1 if snap.unemployment_rate < 5.5 else -2))
        votes.append(v); drivers.append(f"Unemployment {snap.unemployment_rate:.1f}%")
    if snap.jobless_claims is not None:
        v = 1 if snap.jobless_claims < 220_000 else (-1 if snap.jobless_claims > 280_000 else 0)
        votes.append(v); drivers.append(f"Claims {snap.jobless_claims/1000:.0f}k")
    if snap.jolts_openings_m is not None:
        v = 1 if snap.jolts_openings_m > 8.0 else (-1 if snap.jolts_openings_m < 5.5 else 0)
        votes.append(v); drivers.append(f"JOLTS {snap.jolts_openings_m:.1f}M")
    if not votes:
        snap.summary = "Labour data loading."; snap.drivers = drivers; return snap
    score = max(0, min(100, sum(votes) / (len(votes) * 2) * 50 + 50))
    snap.labour_score = round(score, 1)
    snap.bias    = "strong" if score >= 70 else ("weakening" if score < 45 else ("weak" if score < 35 else "neutral"))
    snap.drivers = drivers
    snap.summary = f"NFP {snap.nfp_change_k:+.0f}k, unemployment {snap.unemployment_rate:.1f}%, claims {(snap.jobless_claims or 0)/1000:.0f}k. {snap.bias.upper()}." if snap.nfp_change_k else "Loading."
    return snap


# ═══════════════════════════════════════════════════════════════════════════
# BOND MARKET
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class BondSnapshot:
    y2:  Optional[float] = None; y5:  Optional[float] = None
    y10: Optional[float] = None; y30: Optional[float] = None
    real_yield_10y: Optional[float] = None
    breakeven_10y:  Optional[float] = None
    fed_funds_upper:Optional[float] = None
    fed_funds_lower:Optional[float] = None
    curve_2s10s:    Optional[float] = None
    curve_inverted: bool = False
    y10_chg:        Optional[float] = None
    y2_chg:         Optional[float] = None
    real_chg:       Optional[float] = None
    breakeven_chg:  Optional[float] = None
    regime:  str   = "Unknown"
    bias:    str   = "neutral"
    bond_score: float = 50.0
    summary: str   = ""
    drivers: list  = field(default_factory=list)


@st.cache_data(ttl=3600, show_spinner=False)
def run_bond() -> BondSnapshot:
    ids = [FRED_SERIES["y2"], FRED_SERIES["y5"], FRED_SERIES["y10"], FRED_SERIES["y30"],
           FRED_SERIES["tips_10y"], FRED_SERIES["breakeven_10y"],
           FRED_SERIES["fed_upper"], FRED_SERIES["fed_lower"]]
    d = fetch_multiple(ids, limit=300)
    snap = BondSnapshot(
        y2=latest(d[FRED_SERIES["y2"]]),     y5=latest(d[FRED_SERIES["y5"]]),
        y10=latest(d[FRED_SERIES["y10"]]),   y30=latest(d[FRED_SERIES["y30"]]),
        real_yield_10y=latest(d[FRED_SERIES["tips_10y"]]),
        breakeven_10y=latest(d[FRED_SERIES["breakeven_10y"]]),
        fed_funds_upper=latest(d[FRED_SERIES["fed_upper"]]),
        fed_funds_lower=latest(d[FRED_SERIES["fed_lower"]]),
        y10_chg=chg(d[FRED_SERIES["y10"]], 20),
        y2_chg=chg(d[FRED_SERIES["y2"]], 20),
        real_chg=chg(d[FRED_SERIES["tips_10y"]], 20),
        breakeven_chg=chg(d[FRED_SERIES["breakeven_10y"]], 20),
    )
    if snap.y2 and snap.y10:
        snap.curve_2s10s = round(snap.y10 - snap.y2, 3)
        snap.curve_inverted = snap.curve_2s10s < 0
    return _score_bond(_classify_regime(snap))


def _classify_regime(s: BondSnapshot) -> BondSnapshot:
    rr = s.real_yield_10y or 0; rr_up = (s.real_chg or 0) > 0.05
    be_up = (s.breakeven_chg or 0) * 100 > 8
    if (s.curve_2s10s or 0) < -0.2: s.regime = "Recession Risk"
    elif rr > 2.0 and rr_up:        s.regime = "Higher For Longer"
    elif be_up and rr > 0:           s.regime = "Stagflation"
    elif rr < 0:                     s.regime = "Liquidity Expansion"
    elif (s.breakeven_10y or 3) < 2.0: s.regime = "Disinflation"
    else:                            s.regime = "Risk-On Growth"
    return s


def _score_bond(s: BondSnapshot) -> BondSnapshot:
    votes, drivers = [], []
    if s.curve_2s10s is not None:
        if s.curve_inverted: votes.append(-2); drivers.append(f"Curve inverted {s.curve_2s10s:+.2f}pp")
        elif s.curve_2s10s > 0.5: votes.append(1); drivers.append(f"Curve steep {s.curve_2s10s:+.2f}pp")
    if s.real_yield_10y is not None:
        if s.real_yield_10y > 2.0:   votes.append(-2); drivers.append(f"Real yield {s.real_yield_10y:.2f}% — highly restrictive")
        elif s.real_yield_10y > 0.5: votes.append(-1); drivers.append(f"Real yield {s.real_yield_10y:.2f}% — restrictive")
        elif s.real_yield_10y < 0:   votes.append(2);  drivers.append(f"Real yield {s.real_yield_10y:.2f}% — accommodative")
    if (s.y10_chg or 0) > 0.2:  votes.append(-1); drivers.append(f"10Y rising +{s.y10_chg:.2f}%")
    elif (s.y10_chg or 0) < -0.2: votes.append(1); drivers.append(f"10Y falling {s.y10_chg:.2f}%")
    if not votes:
        s.bond_score = 50; s.bias = "neutral"; s.drivers = drivers; return s
    score = max(0, min(100, sum(float(v) for v in votes) / (len(votes) * 2) * 40 + 50))
    s.bond_score = round(score, 1)
    s.bias    = "bullish" if score >= 60 else ("bearish" if score <= 40 else "neutral")
    s.drivers = drivers
    s.summary = f"Regime: {s.regime}. 10Y {s.y10:.2f}% / 2Y {s.y2:.2f}% (curve {s.curve_2s10s:+.2f}pp), real yield {s.real_yield_10y:.2f}%." if s.y10 and s.y2 else "Loading."
    return s


# ═══════════════════════════════════════════════════════════════════════════
# SENTIMENT
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SentimentSnapshot:
    vix:               Optional[float] = None
    fear_greed_score:  Optional[float] = None
    fear_greed_label:  str = "Neutral"
    put_call_ratio:    Optional[float] = None
    nfci:              Optional[float] = None
    overall_score:     float = 50.0
    regime:            str = "neutral"
    risk_appetite:     str = "neutral"
    summary:           str = ""
    drivers:           list = field(default_factory=list)


@st.cache_data(ttl=1800, show_spinner=False)
def run_sentiment() -> SentimentSnapshot:
    import requests
    vix_s  = fetch_multiple([FRED_SERIES["vix"], FRED_SERIES["nfci"]], limit=30)
    vix    = latest(vix_s[FRED_SERIES["vix"]])
    nfci   = latest(vix_s[FRED_SERIES["nfci"]])
    fg     = None
    try:
        r = requests.get("https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
                         timeout=8, headers={"User-Agent": "Mozilla/5.0"})
        fg = float(r.json().get("fear_and_greed", {}).get("score") or 50)
    except Exception:
        pass
    snap = SentimentSnapshot(vix=vix, nfci=nfci, fear_greed_score=fg)
    if fg is not None:
        if fg <= 25:   snap.fear_greed_label = "Extreme Fear"
        elif fg <= 45: snap.fear_greed_label = "Fear"
        elif fg <= 55: snap.fear_greed_label = "Neutral"
        elif fg <= 75: snap.fear_greed_label = "Greed"
        else:          snap.fear_greed_label = "Extreme Greed"
    return _score_sentiment(snap)


def _score_sentiment(s: SentimentSnapshot) -> SentimentSnapshot:
    votes, drivers = [], []
    if s.vix:
        v = 2 if s.vix < 14 else (1 if s.vix < 20 else (-1 if s.vix < 28 else -2))
        votes.append(v); drivers.append(f"VIX {s.vix:.1f}")
    if s.fear_greed_score:
        votes.append((s.fear_greed_score / 50 - 1) * 2)
        drivers.append(f"Fear & Greed {s.fear_greed_label} ({s.fear_greed_score:.0f})")
    if s.nfci:
        if s.nfci < -0.5: votes.append(2); drivers.append(f"NFCI {s.nfci:.2f} loose")
        elif s.nfci > 0.5: votes.append(-2); drivers.append(f"NFCI {s.nfci:.2f} tight")
    if not votes:
        s.summary = "Sentiment data loading."; s.drivers = drivers; return s
    score = max(0, min(100, (sum(float(v) for v in votes) / len(votes) / 2 + 1) / 2 * 100))
    s.overall_score = round(score, 1)
    if score <= 20:    s.regime, s.risk_appetite = "extreme-fear",  "risk-off"
    elif score <= 40:  s.regime, s.risk_appetite = "fear",          "risk-off"
    elif score <= 60:  s.regime, s.risk_appetite = "neutral",       "neutral"
    elif score <= 80:  s.regime, s.risk_appetite = "greed",         "risk-on"
    else:              s.regime, s.risk_appetite = "extreme-greed",  "risk-on"
    s.drivers = drivers
    s.summary = f"Sentiment: {s.regime.upper().replace('-',' ')} ({score:.0f}/100). VIX {s.vix:.1f}. {s.fear_greed_label}." if s.vix else f"Sentiment: {s.regime.upper()} ({score:.0f}/100)."
    return s

"""
Institutional Scanner — Main Dashboard
Fully defensively coded: all optional values guarded against None.
"""
import streamlit as st
from datetime import datetime, timezone

from src.core.config import get_settings
from src.core.database import create_tables
from src.ui.helpers import (
    BEAR, BLUE, BULL, DIM, GOLD, NEUTRAL, PURPLE,
    inject_css, live_dot, regime_banner, section_header, signal_card,
)

st.set_page_config(
    page_title="Institutional Scanner",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# Ensure DB tables exist on every cold start
try:
    create_tables()
except Exception:
    pass

settings = get_settings()

# ── Helper: safe format ───────────────────────────────────────────────────────
def _f(val, fmt=".1f", suffix="", fallback="N/A"):
    """Format val with fmt, return fallback if val is None."""
    if val is None:
        return fallback
    try:
        return f"{val:{fmt}}{suffix}"
    except Exception:
        return fallback

# ── Load data FIRST so sidebar can reference it ───────────────────────────────
inflation = labour = bond = sentiment = None
signals   = []
load_err  = None

with st.spinner("Loading market intelligence..."):
    try:
        from src.modules.modules import run_inflation, run_labour, run_bond, run_sentiment
        from src.modules.scanner import run_scan
        inflation = run_inflation()
        labour    = run_labour()
        bond      = run_bond()
        sentiment = run_sentiment()
        signals   = run_scan()
    except Exception as e:
        load_err = str(e)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""<div style="padding:0.5rem 0 1rem">
    <div style="font-size:1.3rem;font-weight:900;color:#f4b942">🏛️ Institutional</div>
    <div style="font-size:0.8rem;color:{DIM}">Scanner Pro · AI Edition</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    fred_ok = bool(settings.fred_api_key)
    ai_ok   = bool(settings.anthropic_api_key or settings.openai_api_key)
    tg_ok   = bool(settings.telegram_bot_token)
    st.markdown(f"""
    <div style="font-size:11px;line-height:2;color:{DIM}">
    {'✅' if fred_ok else '❌'} FRED API {'connected' if fred_ok else '— add key in secrets'}<br>
    {'✅' if ai_ok   else '❌'} AI provider {'ready' if ai_ok else '— add key in secrets'}<br>
    {'✅' if tg_ok   else '⚪'} Telegram {'active' if tg_ok else 'not configured'}<br>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if not fred_ok or not ai_ok:
        st.warning("Add API keys in ⚙️ Settings to enable live data.", icon="⚠️")

    if st.button("🔄 Refresh All Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown("""<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem">
    <span style="font-size:1.6rem;font-weight:900;color:#e8e8f0">Institutional Scanner</span>
    </div>""", unsafe_allow_html=True)
    live_dot()
    st.markdown(f"<span style='font-size:0.8rem;color:{DIM}'>Live macro + institutional intelligence dashboard</span>",
                unsafe_allow_html=True)
with col_status:
    st.markdown(f"""<div style="text-align:right;font-size:11px;color:{DIM};margin-top:8px">
    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>""", unsafe_allow_html=True)

if load_err:
    st.error(f"Data load error: {load_err}")

st.markdown("---")

# ── AI Macro Summary ──────────────────────────────────────────────────────────
if bond and inflation and settings.anthropic_api_key:
    try:
        from src.ai.analyst import generate_macro_summary
        ai = generate_macro_summary({
            "bond_regime":    bond.regime,
            "10Y_yield":      bond.y10,
            "real_yield_10y": bond.real_yield_10y,
            "curve_2s10s":    bond.curve_2s10s,
            "core_pce_yoy":   inflation.core_pce_yoy,
            "nfp_change_k":   labour.nfp_change_k   if labour    else None,
            "unemployment":   labour.unemployment_rate if labour  else None,
            "vix":            sentiment.vix           if sentiment else None,
        })
    except Exception:
        ai = {}

    if ai.get("one_sentence_summary"):
        regime_banner(ai.get("regime", bond.regime), ai["one_sentence_summary"])
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"<div style='font-size:11px;color:{DIM};font-weight:700;text-transform:uppercase;margin-bottom:4px'>Top Risks</div>",
                        unsafe_allow_html=True)
            for r in ai.get("top_risks", []):
                st.markdown(f"<span style='font-size:11px;color:{BEAR}'>⚠ {r}</span><br>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"<div style='font-size:11px;color:{DIM};font-weight:700;text-transform:uppercase;margin-bottom:4px'>Opportunities</div>",
                        unsafe_allow_html=True)
            for o in ai.get("top_opportunities", []):
                st.markdown(f"<span style='font-size:11px;color:{BULL}'>✦ {o}</span><br>", unsafe_allow_html=True)
        with r3:
            pref = ai.get("portfolio_preference", "—")
            risk = ai.get("risk_appetite", "neutral")
            st.markdown(f"""<div style='font-size:11px;color:{DIM};font-weight:700;text-transform:uppercase;margin-bottom:4px'>Portfolio Stance</div>
            <div style='font-size:1.1rem;font-weight:900;color:{GOLD}'>{pref.upper()}</div>
            <div style='font-size:11px;color:{DIM}'>{risk.upper()} environment</div>""", unsafe_allow_html=True)
    elif bond:
        regime_banner(bond.regime, bond.summary)
elif bond:
    regime_banner(bond.regime, bond.summary)

st.markdown("---")

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
high_conf = [s for s in signals if s.get("confidence") == "high"]
longs     = [s for s in signals if s.get("direction") == "long"]
shorts    = [s for s in signals if s.get("direction") == "short"]

k1.metric("Active Signals",  len(signals))
k2.metric("High Confidence", len(high_conf))
k3.metric("Long Signals",    len(longs))
k4.metric("Short Signals",   len(shorts))
k5.metric("10Y Yield",       _f(bond.y10 if bond else None, ".2f", "%"),
          _f(bond.y10_chg if bond else None, "+.2f", "pp", None))
k6.metric("VIX",             _f(sentiment.vix if sentiment else None, ".1f"))

st.markdown("---")

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    section_header("Active Trade Signals", "📡")
    if not signals:
        st.info(
            "No signals above the probability threshold right now. "
            "Scanner refreshes every 15 minutes — click **Refresh** in the sidebar to force a new scan.",
            icon="🔍",
        )
    else:
        for sig in signals:
            signal_card(sig)

with right:
    # Sentiment gauge
    if sentiment:
        section_header("Market Sentiment", "🧭")
        score     = sentiment.overall_score or 50
        color     = BULL if score >= 60 else (BEAR if score <= 40 else GOLD)
        vix_str   = _f(sentiment.vix, ".1f")
        risk_str  = sentiment.risk_appetite.replace("-", " ").upper() if sentiment.risk_appetite else "—"
        label_str = sentiment.fear_greed_label or "N/A"
        st.markdown(f"""<div style="background:#111118;border:1px solid #1e1e2e;border-radius:10px;
        padding:1rem;margin-bottom:1rem;text-align:center">
        <div style="font-size:2.5rem;font-weight:900;color:{color}">{score:.0f}</div>
        <div style="font-size:0.9rem;font-weight:700;color:{color};margin-bottom:8px">{label_str}</div>
        <div style="font-size:11px;color:{DIM}">VIX {vix_str} · {risk_str}</div>
        </div>""", unsafe_allow_html=True)

    # Bond yields strip
    if bond:
        section_header("Bond Market", "📈")
        st.metric("2Y Yield",   _f(bond.y2,  ".2f", "%"),
                  _f(bond.y2_chg,  "+.2f", "pp", None))
        st.metric("10Y Yield",  _f(bond.y10, ".2f", "%"),
                  _f(bond.y10_chg, "+.2f", "pp", None))
        st.metric("Real Yield", _f(bond.real_yield_10y, ".2f", "%"))
        curve_str = _f(bond.curve_2s10s, "+.2f", "pp") if bond.curve_2s10s is not None else "N/A"
        st.metric("2s10s",      curve_str)
        if bond.summary:
            st.caption(bond.summary)

    # Inflation strip
    if inflation:
        section_header("Inflation", "🔥")
        st.metric("Core PCE YoY",  _f(inflation.core_pce_yoy,  ".1f", "%"))
        st.metric("Core CPI YoY",  _f(inflation.core_cpi_yoy,  ".1f", "%"))
        st.metric("10Y Breakeven", _f(inflation.breakeven_10y, ".2f", "%"))
        bias_col = BEAR if inflation.bias == "hawkish" else (BULL if inflation.bias == "dovish" else NEUTRAL)
        st.markdown(
            f"<span style='font-size:11px;color:{bias_col};font-weight:700'>"
            f"{inflation.bias.upper()} · {inflation.risk_label}</span>",
            unsafe_allow_html=True,
        )

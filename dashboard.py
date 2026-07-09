"""
Institutional Scanner — Main Dashboard
Overview: AI summary, active signals, bond market, sentiment, currency strength.
"""
import streamlit as st
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
create_tables()           # idempotent — creates SQLite tables if not exist
settings = get_settings()

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
   vix_str = f"{sentiment.vix:.1f}" if sentiment.vix is not None else "—"
risk_str = sentiment.risk_appetite.replace('-', ' ').upper() if sentiment.risk_appetite else "—"
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

# ── Header ─────────────────────────────────────────────────────────────────────
col_title, col_status = st.columns([3, 1])
with col_title:
    st.markdown(f"""<div style="display:flex;align-items:center;gap:10px;margin-bottom:0.5rem">
    <span style="font-size:1.6rem;font-weight:900;color:#e8e8f0">Institutional Scanner</span>
    </div>""", unsafe_allow_html=True)
    live_dot()
    st.markdown(f"<span style='font-size:0.8rem;color:{DIM}'>Live macro + institutional intelligence dashboard</span>", unsafe_allow_html=True)
with col_status:
    from datetime import datetime, timezone
    st.markdown(f"""<div style="text-align:right;font-size:11px;color:{DIM};margin-top:8px">
    {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}</div>""", unsafe_allow_html=True)

st.markdown("---")

# ── Load data (cached) ────────────────────────────────────────────────────────
with st.spinner("Loading market intelligence..."):
    try:
        from src.modules.modules import run_inflation, run_labour, run_bond, run_sentiment
        from src.modules.scanner import run_scan
        inflation  = run_inflation()
        labour     = run_labour()
        bond       = run_bond()
        sentiment  = run_sentiment()
        signals    = run_scan()
        load_err   = None
    except Exception as e:
        inflation = labour = bond = sentiment = None
        signals   = []
        load_err  = str(e)

if load_err:
    st.error(f"Data load error: {load_err}")

# ── AI Macro Summary ──────────────────────────────────────────────────────────
if bond and inflation and settings.anthropic_api_key:
    with st.spinner("Generating AI macro assessment..."):
        try:
            from src.ai.analyst import generate_macro_summary
            ai = generate_macro_summary({
                "bond_regime":   bond.regime,
                "10Y_yield":     bond.y10,
                "real_yield_10y":bond.real_yield_10y,
                "curve_2s10s":   bond.curve_2s10s,
                "core_pce_yoy":  inflation.core_pce_yoy,
                "nfp_change_k":  labour.nfp_change_k if labour else None,
                "unemployment":  labour.unemployment_rate if labour else None,
                "vix":           sentiment.vix if sentiment else None,
            })
        except Exception:
            ai = {}

    if ai.get("one_sentence_summary"):
        regime_label = ai.get("regime", bond.regime)
        regime_banner(regime_label, ai["one_sentence_summary"])
        r1, r2, r3 = st.columns(3)
        with r1:
            st.markdown(f"<div style='font-size:11px;color:{DIM};font-weight:700;text-transform:uppercase;margin-bottom:4px'>Top Risks</div>", unsafe_allow_html=True)
            for r in ai.get("top_risks", []):
                st.markdown(f"<span style='font-size:11px;color:{BEAR}'>⚠ {r}</span><br>", unsafe_allow_html=True)
        with r2:
            st.markdown(f"<div style='font-size:11px;color:{DIM};font-weight:700;text-transform:uppercase;margin-bottom:4px'>Opportunities</div>", unsafe_allow_html=True)
            for o in ai.get("top_opportunities", []):
                st.markdown(f"<span style='font-size:11px;color:{BULL}'>✦ {o}</span><br>", unsafe_allow_html=True)
        with r3:
            pref = ai.get("portfolio_preference","—")
            risk = ai.get("risk_appetite","neutral")
            st.markdown(f"""<div style='font-size:11px;color:{DIM};font-weight:700;text-transform:uppercase;margin-bottom:4px'>Portfolio Stance</div>
            <div style='font-size:1.1rem;font-weight:900;color:{GOLD}'>{pref.upper()}</div>
            <div style='font-size:11px;color:{DIM}'>{risk.upper()} environment</div>""", unsafe_allow_html=True)
elif bond:
    regime_banner(bond.regime, bond.summary)

st.markdown("---")

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5, k6 = st.columns(6)
high_conf = [s for s in signals if s["confidence"] == "high"]
longs     = [s for s in signals if s["direction"] == "long"]
shorts    = [s for s in signals if s["direction"] == "short"]

k1.metric("Active Signals",   len(signals))
k2.metric("High Confidence",  len(high_conf))
k3.metric("Long Signals",     len(longs))
k4.metric("Short Signals",    len(shorts))
k5.metric("10Y Yield",        f"{bond.y10:.2f}%" if bond and bond.y10 else "—",
          f"{bond.y10_chg:+.2f}pp" if bond and bond.y10_chg else None)
k6.metric("VIX",              f"{sentiment.vix:.1f}" if sentiment and sentiment.vix else "—")

st.markdown("---")

# ── Two-column layout ─────────────────────────────────────────────────────────
left, right = st.columns([2, 1])

with left:
    section_header("Active Trade Signals", "📡")
    if not signals:
        st.info("No signals above the probability threshold right now. Scanner refreshes every 15 minutes — click **Refresh** in the sidebar to force a new scan.", icon="🔍")
    else:
        for sig in signals:
            signal_card(sig)

with right:
    # Sentiment gauge
    if sentiment:
        section_header("Market Sentiment", "🧭")
        score = sentiment.overall_score
        color = BULL if score >= 60 else (BEAR if score <= 40 else GOLD)
        st.markdown(f"""<div style="background:#111118;border:1px solid #1e1e2e;border-radius:10px;
        padding:1rem;margin-bottom:1rem;text-align:center">
        <div style="font-size:2.5rem;font-weight:900;color:{color}">{score:.0f}</div>
        <div style="font-size:0.9rem;font-weight:700;color:{color};margin-bottom:8px">{sentiment.fear_greed_label}</div>
        <div style="font-size:11px;color:{DIM}">VIX {sentiment.vix:.1f} · {sentiment.risk_appetite.replace('-',' ').upper()}</div>
        </div>""", unsafe_allow_html=True)

    # Bond yields strip
    if bond:
        section_header("Bond Market", "📈")
        for label, val, delta, col in [
            ("2Y Yield",   f"{bond.y2:.2f}%"  if bond.y2  else "—", f"{bond.y2_chg:+.2f}pp"   if bond.y2_chg  else None, BEAR if (bond.y2_chg or 0) > 0 else BULL),
            ("10Y Yield",  f"{bond.y10:.2f}%" if bond.y10 else "—", f"{bond.y10_chg:+.2f}pp"  if bond.y10_chg else None, BEAR if (bond.y10_chg or 0) > 0 else BULL),
            ("Real Yield", f"{bond.real_yield_10y:.2f}%" if bond.real_yield_10y else "—", None, GOLD),
            ("2s10s",      f"{bond.curve_2s10s:+.2f}pp" if bond.curve_2s10s is not None else "—", None, BEAR if bond.curve_inverted else BULL),
        ]:
            st.metric(label, val, delta)
        if bond.summary:
            st.caption(bond.summary)

    # Inflation strip
    if inflation:
        section_header("Inflation", "🔥")
        st.metric("Core PCE YoY",  f"{inflation.core_pce_yoy:.1f}%"  if inflation.core_pce_yoy  else "—")
        st.metric("Core CPI YoY",  f"{inflation.core_cpi_yoy:.1f}%"  if inflation.core_cpi_yoy  else "—")
        st.metric("10Y Breakeven", f"{inflation.breakeven_10y:.2f}%"  if inflation.breakeven_10y else "—")
        bias_col = BEAR if inflation.bias == "hawkish" else (BULL if inflation.bias == "dovish" else NEUTRAL)
        st.markdown(f"<span style='font-size:11px;color:{bias_col};font-weight:700'>{inflation.bias.upper()} · {inflation.risk_label}</span>", unsafe_allow_html=True)

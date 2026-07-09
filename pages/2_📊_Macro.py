"""Macro Dashboard — Inflation, Labour, Bond, Sentiment, Central Banks."""
import streamlit as st
from src.ui.helpers import (
    BEAR, BLUE, BULL, DIM, GOLD, NEUTRAL, PURPLE,
    inject_css, progress_bar, regime_banner, section_header,
)
from src.modules.modules import run_inflation, run_labour, run_bond, run_sentiment

st.set_page_config(page_title="Macro · Institutional", page_icon="📊", layout="wide")
inject_css()
st.title("📊 Macro Dashboard")
st.caption("Real-time economic data via FRED API — refreshed every hour.")

if st.button("🔄 Refresh Macro Data"):
    st.cache_data.clear(); st.rerun()

with st.spinner("Loading macro modules..."):
    inflation = run_inflation()
    labour    = run_labour()
    bond      = run_bond()
    sentiment = run_sentiment()

# ── Bond regime banner ────────────────────────────────────────────────────────
regime_banner(bond.regime, bond.summary)

# ── Bond yields ───────────────────────────────────────────────────────────────
section_header("Bond Market", "📈")
bc1, bc2, bc3, bc4, bc5, bc6 = st.columns(6)
for col, (label, val, delta) in zip(
    [bc1, bc2, bc3, bc4, bc5, bc6],
    [
        ("2Y Yield",    f"{bond.y2:.2f}%"   if bond.y2   else "—", f"{bond.y2_chg:+.2f}pp"   if bond.y2_chg   else None),
        ("10Y Yield",   f"{bond.y10:.2f}%"  if bond.y10  else "—", f"{bond.y10_chg:+.2f}pp"  if bond.y10_chg  else None),
        ("30Y Yield",   f"{bond.y30:.2f}%"  if bond.y30  else "—", None),
        ("Real Yield",  f"{bond.real_yield_10y:.2f}%" if bond.real_yield_10y else "—", f"{bond.real_chg:+.2f}pp" if bond.real_chg else None),
        ("Breakeven",   f"{bond.breakeven_10y:.2f}%" if bond.breakeven_10y else "—", None),
        ("2s10s Curve", f"{bond.curve_2s10s:+.2f}pp" if bond.curve_2s10s is not None else "—", None),
    ]
):
    col.metric(label, val, delta)

fed_str = f"{bond.fed_funds_lower:.2f}–{bond.fed_funds_upper:.2f}%" if bond.fed_funds_lower and bond.fed_funds_upper else "N/A"
st.markdown(f"**Fed Funds Target:** `{fed_str}` &nbsp;|&nbsp; Curve: {'🔴 INVERTED' if bond.curve_inverted else '🟢 Normal'}", unsafe_allow_html=True)
if bond.drivers:
    with st.expander("Bond drivers"):
        for d in bond.drivers: st.markdown(f"- {d}")

st.markdown("---")

# ── Two-column: Inflation + Labour ────────────────────────────────────────────
left, right = st.columns(2)

with left:
    section_header("Inflation", "🔥")
    bias_col = BEAR if inflation.bias=="hawkish" else (BULL if inflation.bias=="dovish" else NEUTRAL)
    st.markdown(f"<span style='font-size:1rem;font-weight:900;color:{bias_col}'>{inflation.bias.upper()} · Score {inflation.inflation_score:.0f}/100</span>", unsafe_allow_html=True)
    progress_bar(inflation.inflation_score, color=bias_col)
    st.markdown("<br>", unsafe_allow_html=True)
    data = [
        ("CPI YoY",       inflation.cpi_yoy,       "%"),
        ("CPI MoM",       inflation.cpi_mom,        "%"),
        ("Core CPI YoY",  inflation.core_cpi_yoy,   "%"),
        ("Core CPI MoM",  inflation.core_cpi_mom,   "%"),
        ("PCE YoY",       inflation.pce_yoy,        "%"),
        ("Core PCE YoY",  inflation.core_pce_yoy,   "%"),
        ("Core PCE MoM",  inflation.core_pce_mom,   "%"),
        ("PPI YoY",       inflation.ppi_yoy,        "%"),
        ("AHE YoY",       inflation.ahe_yoy,        "%"),
        ("10Y Breakeven", inflation.breakeven_10y,   "%"),
        ("10Y Real Yield",inflation.real_yield_10y,  "%"),
    ]
    for label, val, unit in data:
        v = f"{val:.2f}{unit}" if val is not None else "N/A"
        col_str = BEAR if (val or 0) > 3.5 else (BULL if (val or 0) < 2 else NEUTRAL)
        st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:4px 0;
        border-bottom:1px solid #1e1e2e;font-size:12px">
        <span style="color:{DIM}">{label}</span>
        <span style="font-weight:700;color:{col_str}">{v}</span></div>""", unsafe_allow_html=True)
    if inflation.summary:
        st.caption(inflation.summary)

with right:
    section_header("Labour Market", "💼")
    lab_colors = {"strong": BULL, "neutral": NEUTRAL, "weakening": GOLD, "weak": BEAR}
    lab_col = lab_colors.get(labour.bias, NEUTRAL)
    st.markdown(f"<span style='font-size:1rem;font-weight:900;color:{lab_col}'>{labour.bias.upper()} · Score {labour.labour_score:.0f}/100</span>", unsafe_allow_html=True)
    progress_bar(labour.labour_score, color=lab_col)
    st.markdown("<br>", unsafe_allow_html=True)
    data = [
        ("NFP Change",       f"{labour.nfp_change_k:+.0f}k" if labour.nfp_change_k is not None else "N/A",
         BULL if (labour.nfp_change_k or 0) > 150 else BEAR),
        ("Unemployment",     f"{labour.unemployment_rate:.1f}%" if labour.unemployment_rate else "N/A",
         BULL if (labour.unemployment_rate or 5) < 4.5 else BEAR),
        ("Participation",    f"{labour.participation_rate:.1f}%" if labour.participation_rate else "N/A", NEUTRAL),
        ("Initial Claims",   f"{labour.jobless_claims/1000:.0f}k" if labour.jobless_claims else "N/A",
         BULL if (labour.jobless_claims or 300000) < 220000 else BEAR),
        ("JOLTS Openings",   f"{labour.jolts_openings_m:.1f}M" if labour.jolts_openings_m else "N/A",
         BULL if (labour.jolts_openings_m or 0) > 8 else NEUTRAL),
        ("AHE YoY",          f"{labour.ahe_yoy:.1f}%" if labour.ahe_yoy else "N/A", NEUTRAL),
    ]
    for label, val, col in data:
        st.markdown(f"""<div style="display:flex;justify-content:space-between;padding:4px 0;
        border-bottom:1px solid #1e1e2e;font-size:12px">
        <span style="color:{DIM}">{label}</span>
        <span style="font-weight:700;color:{col}">{val}</span></div>""", unsafe_allow_html=True)
    if labour.summary:
        st.caption(labour.summary)

st.markdown("---")

# ── Sentiment ─────────────────────────────────────────────────────────────────
section_header("Market Sentiment", "🧭")
sc1, sc2, sc3, sc4 = st.columns(4)
sent_col = BULL if sentiment.overall_score >= 60 else (BEAR if sentiment.overall_score <= 40 else GOLD)
sc1.metric("Overall Score",    f"{sentiment.overall_score:.0f}/100")
sc2.metric("Fear & Greed",     sentiment.fear_greed_label, f"{sentiment.fear_greed_score:.0f}/100" if sentiment.fear_greed_score else None)
sc3.metric("VIX",              f"{sentiment.vix:.1f}" if sentiment.vix else "N/A")
sc4.metric("Risk Appetite",    sentiment.risk_appetite.replace("-"," ").upper())
progress_bar(sentiment.overall_score, "Overall Sentiment Score", color=sent_col)
if sentiment.summary:
    st.caption(sentiment.summary)

st.markdown("---")

# ── ISM Manual Entry ──────────────────────────────────────────────────────────
section_header("ISM PMI (Manual Entry)", "📋")
st.caption("ISM data is not on FRED — enter the latest prints after each release (1st & 3rd business day of the month).")
from src.core.database import get_db, IsmRelease
from sqlalchemy import select as sa_select

db  = get_db()
row = db.execute(sa_select(IsmRelease).order_by(IsmRelease.entered_at.desc()).limit(1)).scalar_one_or_none()
db.close()
default_mfg = float(row.manufacturing_pmi) if row and row.manufacturing_pmi else 50.0
default_svc = float(row.services_pmi)      if row and row.services_pmi      else 50.0

ic1, ic2, ic3, ic4 = st.columns([2, 2, 3, 1])
with ic1: new_mfg = st.number_input("Manufacturing PMI", 0.0, 100.0, default_mfg, 0.1)
with ic2: new_svc = st.number_input("Services PMI",      0.0, 100.0, default_svc, 0.1)
with ic3: period  = st.text_input("Period", placeholder="e.g. June 2026")
with ic4:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Save", use_container_width=True):
        db2 = get_db()
        db2.add(IsmRelease(manufacturing_pmi=new_mfg, services_pmi=new_svc,
                           period_label=period or None))
        db2.commit(); db2.close()
        st.cache_data.clear()
        st.success(f"ISM saved — Mfg {new_mfg:.1f} / Svc {new_svc:.1f}", icon="✅")

if row:
    st.caption(f"Currently using: Manufacturing {default_mfg:.1f}, Services {default_svc:.1f} ({row.period_label or 'no period label'})")

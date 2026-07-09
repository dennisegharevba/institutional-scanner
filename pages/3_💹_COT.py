"""COT — Commitments of Traders institutional positioning."""
import streamlit as st
import plotly.graph_objects as go
from src.core.config import MARKETS
from src.data.cot import get_latest_cot, fetch_cot_raw
from src.ui.helpers import BEAR, BULL, DIM, GOLD, NEUTRAL, inject_css, progress_bar, section_header

st.set_page_config(page_title="COT · Institutional", page_icon="💹", layout="wide")
inject_css()
st.title("💹 Commitments of Traders")
st.caption("CFTC weekly COT data — COT Index = current net position vs 3-year range (0–100).")

if st.button("🔄 Refresh COT Data"):
    st.cache_data.clear(); st.rerun()

# ── Market selector ───────────────────────────────────────────────────────────
classes = sorted(set(m["class"] for m in MARKETS.values()))
flt_class = st.selectbox("Filter by asset class", ["All"] + classes)

markets_with_cot = {sym: m for sym, m in MARKETS.items() if m.get("cot_code")}
if flt_class != "All":
    markets_with_cot = {sym: m for sym, m in markets_with_cot.items() if m["class"] == flt_class.lower()}

# ── Load all COT data ─────────────────────────────────────────────────────────
with st.spinner("Downloading CFTC COT data..."):
    cot_data = {}
    for sym in markets_with_cot:
        d = get_latest_cot(sym)
        if d:
            cot_data[sym] = d

if not cot_data:
    st.warning("No COT data available. CFTC may be updating — try again shortly.", icon="⚠️")
    st.stop()

# ── Summary table ─────────────────────────────────────────────────────────────
section_header("Positioning Summary", "📊")
import pandas as pd
rows = []
for sym, d in cot_data.items():
    rows.append({
        "Symbol":         sym,
        "Market":         MARKETS[sym]["name"],
        "COT Index":      d["cot_index"],
        "Comm Net":       int(d["commercials_net"]),
        "Spec Net":       int(d["large_specs_net"]),
        "Net Chg (wk)":   int(d["net_change_wk"]),
        "Open Interest":  int(d["open_interest"]),
        "Bias":           d["institutional_bias"].upper(),
        "Report Date":    d["report_date"],
    })
df = pd.DataFrame(rows).sort_values("COT Index", ascending=False)

def _color_cot(val):
    if isinstance(val, (int, float)):
        if val >= 70: return "color: #00d2a8; font-weight: 700"
        if val <= 30: return "color: #ff4b6e; font-weight: 700"
    return ""

def _color_bias(val):
    if val == "BULLISH": return "color: #00d2a8; font-weight: 700"
    if val == "BEARISH": return "color: #ff4b6e; font-weight: 700"
    return f"color: {NEUTRAL}"

styled = df.style.applymap(_color_cot, subset=["COT Index"]).applymap(_color_bias, subset=["Bias"])
st.dataframe(styled, use_container_width=True, hide_index=True)

st.markdown("---")

# ── Individual market deep-dive ───────────────────────────────────────────────
section_header("Market Detail", "🔍")
sym_choice = st.selectbox("Select market", list(cot_data.keys()),
                          format_func=lambda s: f"{MARKETS[s]['name']} ({s})")

if sym_choice and sym_choice in cot_data:
    d   = cot_data[sym_choice]
    idx = d["cot_index"]
    bias_col = BULL if d["institutional_bias"] == "bullish" else (BEAR if d["institutional_bias"] == "bearish" else NEUTRAL)

    dc1, dc2, dc3 = st.columns(3)
    dc1.metric("COT Index",      f"{idx:.1f} / 100")
    dc2.metric("Commercials Net", f"{d['commercials_net']:,.0f}")
    dc3.metric("Large Specs Net", f"{d['large_specs_net']:,.0f}")

    st.markdown(f"<div style='margin:8px 0'></div>", unsafe_allow_html=True)
    progress_bar(idx, f"COT Index ({d['institutional_bias'].upper()})", color=bias_col)

    dc4, dc5 = st.columns(2)
    dc4.metric("Net Change (week)", f"{d['net_change_wk']:+,.0f}")
    dc5.metric("Open Interest",     f"{d['open_interest']:,.0f}")
    st.caption(f"Report date: {d['report_date']}")

    # Historical chart
    from datetime import datetime
    yr = datetime.now().year
    raw = fetch_cot_raw(yr) or fetch_cot_raw(yr - 1)
    if raw is not None and MARKETS[sym_choice].get("cot_code"):
        cot_code = MARKETS[sym_choice]["cot_code"]
        subset = raw[raw["cot_code"].astype(str).str.strip() == str(cot_code).strip()].copy()
        if not subset.empty:
            subset = subset.sort_values("report_date")
            subset["comm_net"] = subset.get("comm_long", 0) - subset.get("comm_short", 0)
            subset["spec_net"] = subset.get("spec_long", 0) - subset.get("spec_short", 0)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=subset["report_date"], y=subset["comm_net"],
                                  name="Commercials Net", marker_color=BULL, opacity=0.7))
            fig.add_trace(go.Bar(x=subset["report_date"], y=subset["spec_net"],
                                  name="Large Specs Net", marker_color=BEAR, opacity=0.7))
            fig.update_layout(
                title=f"{MARKETS[sym_choice]['name']} — COT Net Positions",
                barmode="group", height=350,
                paper_bgcolor="#0a0a0f", plot_bgcolor="#111118",
                font=dict(color="#8888aa", size=11),
                legend=dict(bgcolor="#111118"),
            )
            st.plotly_chart(fig, use_container_width=True)

    # AI interpretation
    if st.button("🧠 Get AI Interpretation"):
        from src.ai.analyst import interpret_cot
        with st.spinner("Asking AI..."):
            try:
                from src.ai.analyst import ask
                text = f"""Interpret COT data for {MARKETS[sym_choice]['name']}:
COT Index: {idx:.0f}/100, Commercials Net: {d['commercials_net']:,.0f},
Large Specs Net: {d['large_specs_net']:,.0f}, Weekly Change: {d['net_change_wk']:+,.0f}
Write 2-3 sentences about what this positioning implies for price direction."""
                from src.ai.provider import ask as _ask
                interp = _ask(text, max_tokens=200)
                st.info(interp, icon="🧠")
            except Exception as e:
                st.error(f"AI unavailable: {e}")

"""Signal History + Performance Analytics."""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from src.core.database import Signal, get_db
from src.ui.helpers import BEAR, BLUE, BULL, DIM, GOLD, NEUTRAL, inject_css, section_header
from sqlalchemy import select as sa_select

st.set_page_config(page_title="History · Institutional", page_icon="📋", layout="wide")
inject_css()
st.title("📋 Signal History & Analytics")

db = get_db()
rows = db.execute(sa_select(Signal).order_by(Signal.created_at.desc()).limit(200)).scalars().all()
db.close()

if not rows:
    st.info("No signals recorded yet. Run the scanner to generate signals.", icon="ℹ️")
    st.stop()

# ── Build DataFrame ────────────────────────────────────────────────────────────
data = [{
    "ID":        s.id,
    "Symbol":    s.symbol,
    "Market":    s.market_name,
    "Direction": s.direction.upper(),
    "Prob %":    s.probability,
    "Conf":      s.confidence,
    "Entry":     s.entry_price,
    "SL":        s.stop_loss,
    "TP1":       s.take_profit_1,
    "RR":        s.risk_reward,
    "Status":    s.status,
    "Outcome":   s.outcome_label or "—",
    "Date":      s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "—",
} for s in rows]
df = pd.DataFrame(data)

# ── Analytics ─────────────────────────────────────────────────────────────────
closed = [s for s in rows if s.status in ("hit_tp1","hit_tp2","stopped")]
wins   = [s for s in closed if (s.outcome_label or "") in ("win","partial_win")]
losses = [s for s in closed if (s.outcome_label or "") == "loss"]

section_header("Performance Summary", "📈")
ac1, ac2, ac3, ac4, ac5 = st.columns(5)
ac1.metric("Total Signals",  len(rows))
ac2.metric("Closed",         len(closed))
ac3.metric("Win Rate",       f"{len(wins)/max(len(closed),1)*100:.0f}%" if closed else "—")
ac4.metric("Avg RR",         f"1:{sum(s.outcome_rr or 0 for s in wins)/max(len(wins),1):.1f}" if wins else "—")
ac5.metric("Active",         sum(1 for s in rows if s.status == "active"))

# Direction breakdown
st.markdown("---")
longs  = [s for s in rows if s.direction == "long"]
shorts = [s for s in rows if s.direction == "short"]
dc1, dc2, dc3, dc4 = st.columns(4)
dc1.metric("Long Signals",   len(longs))
dc2.metric("Short Signals",  len(shorts))
dc3.metric("High Confidence",sum(1 for s in rows if s.confidence == "high"))
dc4.metric("Best Market",    max(set(s.symbol for s in wins), key=lambda m: sum(1 for s in wins if s.symbol == m), default="—") if wins else "—")

# ── Chart: signals per market ──────────────────────────────────────────────────
st.markdown("---")
section_header("Signals by Market", "📊")
from collections import Counter
sym_counts = Counter(s.symbol for s in rows)
fig = go.Figure(go.Bar(
    x=list(sym_counts.keys()), y=list(sym_counts.values()),
    marker_color=GOLD, marker_line_color="#0a0a0f", marker_line_width=1,
))
fig.update_layout(
    height=280, paper_bgcolor="#0a0a0f", plot_bgcolor="#111118",
    font=dict(color="#8888aa", size=11), margin=dict(t=10, b=40),
    xaxis=dict(gridcolor="#1e1e2e"), yaxis=dict(gridcolor="#1e1e2e"),
)
st.plotly_chart(fig, use_container_width=True)

# ── Full table ─────────────────────────────────────────────────────────────────
st.markdown("---")
section_header("All Signals", "📋")

flt_sym  = st.multiselect("Filter by symbol", options=df["Symbol"].unique().tolist())
flt_dir  = st.selectbox("Direction", ["All","LONG","SHORT"], key="hist_dir")
flt_stat = st.selectbox("Status",    ["All","active","hit_tp1","hit_tp2","stopped","expired"], key="hist_stat")

view = df.copy()
if flt_sym:  view = view[view["Symbol"].isin(flt_sym)]
if flt_dir  != "All": view = view[view["Direction"] == flt_dir]
if flt_stat != "All": view = view[view["Status"]    == flt_stat]

def _color_dir(val):
    if val == "LONG":  return f"color: {BULL}; font-weight: 700"
    if val == "SHORT": return f"color: {BEAR}; font-weight: 700"
    return ""

def _color_outcome(val):
    if val == "win":    return f"color: {BULL}; font-weight: 700"
    if val == "loss":   return f"color: {BEAR}; font-weight: 700"
    return f"color: {NEUTRAL}"

styled = (view.style
          .applymap(_color_dir,     subset=["Direction"])
          .applymap(_color_outcome, subset=["Outcome"]))
st.dataframe(styled, use_container_width=True, hide_index=True)

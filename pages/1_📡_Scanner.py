"""Scanner page — all active signals with module scores and AI reasoning."""
import streamlit as st
from src.core.config import MARKETS
from src.ui.helpers import BEAR, BLUE, BULL, DIM, GOLD, NEUTRAL, inject_css, section_header, signal_card
from src.modules.scanner import run_scan

st.set_page_config(page_title="Scanner · Institutional", page_icon="📡", layout="wide")
inject_css()
st.title("📡 Trade Scanner")
st.caption("Only fires when Technical + Macro + COT + Sentiment all agree above the threshold.")

col_f1, col_f2, col_f3, col_scan = st.columns([2, 2, 2, 1])
with col_f1:
    classes   = ["All"] + sorted(set(m["class"] for m in MARKETS.values()))
    flt_class = st.selectbox("Asset Class", classes, key="sc_class")
with col_f2:
    flt_dir   = st.selectbox("Direction", ["All","Long","Short"], key="sc_dir")
with col_f3:
    flt_conf  = st.selectbox("Confidence", ["All","High","Medium","Low"], key="sc_conf")
with col_scan:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔄 Rescan", use_container_width=True):
        st.cache_data.clear(); st.rerun()

with st.spinner("Running scanner..."):
    signals = run_scan()

# Apply filters
filtered = signals
if flt_class != "All":
    filtered = [s for s in filtered if MARKETS.get(s["symbol"],{}).get("class","") == flt_class.lower()]
if flt_dir  != "All":
    filtered = [s for s in filtered if s["direction"] == flt_dir.lower()]
if flt_conf != "All":
    filtered = [s for s in filtered if s["confidence"] == flt_conf.lower()]

st.markdown("---")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Signals",    len(signals))
c2.metric("Filtered Signals", len(filtered))
c3.metric("High Confidence",  sum(1 for s in signals if s["confidence"]=="high"))
c4.metric("Long / Short",     f"{sum(1 for s in signals if s['direction']=='long')} / {sum(1 for s in signals if s['direction']=='short')}")
st.markdown("---")

if not filtered:
    st.info("No signals match your filters right now.", icon="🔍")
else:
    for sig in filtered:
        signal_card(sig)

        # Telegram send button
        if st.button(f"📨 Send to Telegram — {sig['symbol']}", key=f"tg_{sig['symbol']}", use_container_width=False):
            from src.telegram.bot import send_signal_alert
            ok = send_signal_alert(sig)
            st.success("Alert sent!" if ok else "Telegram not configured. Add BOT_TOKEN in secrets.", icon="✅" if ok else "⚠️")

"""Shared Streamlit UI helpers — Bloomberg dark theme."""
from __future__ import annotations
import streamlit as st

# ── Colour palette ────────────────────────────────────────────────────────────
BULL    = "#00d2a8"
BEAR    = "#ff4b6e"
GOLD    = "#f4b942"
BLUE    = "#4a9eff"
PURPLE  = "#9b59ff"
NEUTRAL = "#888899"
BG_CARD = "#111118"
BG_ELEV = "#16161f"
BORDER  = "#1e1e2e"
DIM     = "#8888aa"

REGIME_COLORS = {
    "Risk-On Growth":    BULL,  "Disinflation":       BULL,
    "Liquidity Expansion": BULL,"Higher For Longer":  GOLD,
    "Stagflation":       BEAR,  "Recession Risk":     BEAR,
}
CB_TONE_COLORS = {
    "very-hawkish": BEAR, "hawkish": "#ff8fa3",
    "neutral": NEUTRAL, "dovish": BLUE, "very-dovish": "#a8d8ff",
}


def inject_css():
    st.markdown("""<style>
    div[data-testid="stMetricValue"]  { font-size:1.6rem !important; font-weight:800 !important; }
    div[data-testid="stMetricLabel"]  { font-size:0.72rem !important; color:#8888aa !important; letter-spacing:0.06em; text-transform:uppercase; }
    div[data-testid="stMetricDelta"]  { font-size:0.78rem !important; }
    .block-container { padding-top:1.2rem !important; padding-bottom:1rem !important; }
    section[data-testid="stSidebar"] > div { background:#0d0d14 !important; }
    .stTabs [data-baseweb="tab"]      { font-size:0.8rem; font-weight:600; letter-spacing:0.04em; }
    div[data-testid="stExpander"]     { border:1px solid #1e1e2e !important; border-radius:8px; }
    [data-testid="stDataFrame"] table { background:#111118 !important; }
    </style>""", unsafe_allow_html=True)


def card(content_fn, border_color: str = BORDER):
    """Render content inside a styled dark card."""
    st.markdown(f"""<div style="background:{BG_CARD};border:1px solid {border_color};
    border-radius:10px;padding:1rem 1.25rem;margin-bottom:0.5rem">""", unsafe_allow_html=True)
    content_fn()
    st.markdown("</div>", unsafe_allow_html=True)


def section_header(label: str, icon: str = ""):
    st.markdown(f"""<div style="font-size:11px;font-weight:700;letter-spacing:0.1em;
    text-transform:uppercase;color:{DIM};margin-bottom:0.6rem;display:flex;align-items:center;gap:6px">
    <span>{icon}</span>{label}</div>""", unsafe_allow_html=True)


def bias_pill(label: str, color: str = NEUTRAL):
    bg = color + "22"
    st.markdown(f"""<span style="display:inline-flex;align-items:center;padding:2px 10px;
    border-radius:99px;font-size:10px;font-weight:800;letter-spacing:0.05em;
    text-transform:uppercase;background:{bg};color:{color}">{label}</span>""",
    unsafe_allow_html=True)


def regime_banner(regime: str, rationale: str = ""):
    color = REGIME_COLORS.get(regime, NEUTRAL)
    st.markdown(f"""<div style="background:{color}18;border:1px solid {color};border-radius:10px;
    padding:0.9rem 1.2rem;margin-bottom:1rem">
    <span style="font-size:1.2rem;font-weight:900;color:{color}">{regime}</span>
    {"<div style='margin-top:6px;font-size:0.85rem;color:#c8c8d8'>"+rationale+"</div>" if rationale else ""}
    </div>""", unsafe_allow_html=True)


def kpi_row(items: list[tuple]):
    """items = [(label, value, delta, color), ...]"""
    cols = st.columns(len(items))
    for col, (label, value, delta, color) in zip(cols, items):
        with col:
            st.metric(label=label, value=value, delta=delta)
            if color:
                st.markdown(f"<style>div[data-testid='stMetricValue']{{color:{color}}}</style>",
                            unsafe_allow_html=True)


def signal_card(sig: dict):
    is_long  = sig["direction"] == "long"
    color    = BULL if is_long else BEAR
    conf_col = {"high": BULL, "medium": GOLD, "low": NEUTRAL}.get(sig["confidence"], NEUTRAL)
    scores   = sig.get("module_scores", {})
    bars     = "".join(
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:3px'>"
        f"<span style='font-size:10px;color:{DIM};width:90px;flex-shrink:0'>{m.replace('_',' ').title()}</span>"
        f"<div style='flex:1;height:4px;background:{BORDER};border-radius:99px'>"
        f"<div style='width:{min(float(s),100):.0f}%;height:100%;background:"
        f"{'#00d2a8' if float(s)>=60 else ('#ff4b6e' if float(s)<=40 else '#f4b942')};"
        f"border-radius:99px'></div></div>"
        f"<span style='font-size:10px;color:{DIM};width:24px;text-align:right'>{float(s):.0f}</span>"
        f"</div>"
        for m, s in scores.items()
    )
    exp_str = sig.get("expires_at","")
    cd_str  = ""
    if exp_str:
        try:
            from datetime import datetime, timezone
            exp = datetime.fromisoformat(exp_str.replace("Z","+00:00"))
            if exp.tzinfo is None: exp = exp.replace(tzinfo=timezone.utc)
            secs = max(0, int((exp - datetime.now(timezone.utc)).total_seconds()))
            h, rem = divmod(secs, 3600); m2, s2 = divmod(rem, 60)
            cd_str = f"{h}h {m2:02d}m {s2:02d}s"
        except Exception:
            pass

    st.markdown(f"""
<div style="background:{BG_CARD};border:1px solid {BORDER};border-left:4px solid {color};
border-radius:10px;padding:1rem 1.2rem;margin-bottom:0.75rem;
box-shadow:0 0 14px {color}22">
  <div style="display:flex;justify-content:space-between;align-items:flex-start">
    <div>
      <span style="font-size:1.1rem;font-weight:900;color:#e8e8f0">{sig['market_name']}</span>
      <span style="color:{DIM};font-size:0.8rem;margin-left:6px">({sig['symbol']})</span>
      <span style="display:inline-flex;margin-left:8px;padding:2px 10px;border-radius:99px;
      font-size:10px;font-weight:800;background:{color}22;color:{color}">
      {'▲ LONG' if is_long else '▼ SHORT'}</span>
    </div>
    <div style="text-align:right">
      <div style="font-size:1.5rem;font-weight:900;color:{conf_col};line-height:1">
        {sig['probability']:.0f}%</div>
      <div style="font-size:10px;font-weight:700;color:{conf_col};text-transform:uppercase">
        {sig['confidence']}</div>
    </div>
  </div>
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:10px">
    {"".join(f"<div style='background:{BG_ELEV};border-radius:6px;padding:6px 8px'>"
             f"<div style='font-size:9px;color:{DIM};margin-bottom:2px'>{lbl}</div>"
             f"<div style='font-family:monospace;font-size:0.82rem;font-weight:700;color:{vc}'>{val}</div>"
             f"</div>"
             for lbl,val,vc in [
                 ("Entry",   f"{sig['entry_price']:.4f}",   "#e8e8f0"),
                 ("Stop",    f"{sig['stop_loss']:.4f}",     BEAR),
                 ("TP1",     f"{sig['take_profit_1']:.4f}", BULL),
                 ("TP2",     f"{sig['take_profit_2']:.4f}", BULL),
             ])}
  </div>
  <div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:8px;font-size:11px;color:{DIM}">
    <span>RR: <b style="color:{GOLD}">1:{sig['risk_reward']:.1f}</b></span>
    <span style="margin-left:auto;color:{GOLD};font-family:monospace">⏱ {cd_str}</span>
  </div>
  <div style="margin-top:10px">{bars}</div>
  {"<div style='margin-top:8px;padding:8px 10px;background:"+BG_ELEV+";border-radius:6px;"
   "border-left:2px solid "+PURPLE+";font-size:11px;color:"+DIM+";line-height:1.6'>"
   "<span style='color:"+PURPLE+";font-size:10px;font-weight:700'>🧠 AI REASONING&nbsp;</span>"
   +sig['ai_reasoning']+"</div>" if sig.get('ai_reasoning') else ""}
</div>""", unsafe_allow_html=True)


def progress_bar(score: float, label: str = "", color: str = GOLD):
    pct = min(max(float(score), 0), 100)
    st.markdown(f"""<div style="margin-bottom:6px">
    {"<div style='font-size:10px;color:"+DIM+";margin-bottom:2px'>"+label+"</div>" if label else ""}
    <div style="display:flex;align-items:center;gap:8px">
      <div style="flex:1;height:5px;background:{BORDER};border-radius:99px">
        <div style="width:{pct:.0f}%;height:100%;background:{color};border-radius:99px"></div>
      </div>
      <span style="font-size:11px;color:{color};font-weight:700;width:28px;text-align:right">
        {pct:.0f}</span>
    </div></div>""", unsafe_allow_html=True)


def live_dot():
    st.markdown("""<span style="display:inline-block;width:8px;height:8px;border-radius:50%;
    background:#00d2a8;animation:pulse 2s infinite;margin-right:6px"></span>
    <style>@keyframes pulse{0%,100%{opacity:1}50%{opacity:.3}}</style>""",
    unsafe_allow_html=True)

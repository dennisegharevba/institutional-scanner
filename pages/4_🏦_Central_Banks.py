"""
Central Banks page — AI tone classification + manual statement entry.
"""
import streamlit as st
from src.core.config import CENTRAL_BANKS
from src.core.database import CentralBankStatement, get_db
from src.ui.helpers import (
    BEAR, BLUE, BULL, DIM, GOLD, NEUTRAL, PURPLE,
    CB_TONE_COLORS, inject_css, section_header, progress_bar,
)
from sqlalchemy import select as sa_select

st.set_page_config(page_title="Central Banks · Institutional", page_icon="🏦", layout="wide")
inject_css()
st.title("🏦 Central Banks")
st.caption("AI classifies every statement as Very Hawkish → Very Dovish with reasoning.")

# ── Load latest tone for each CB ──────────────────────────────────────────────
section_header("Current Stance by Bank", "📊")
db = get_db()
cols = st.columns(4)
banks_list = list(CENTRAL_BANKS.items())

for i, (code, meta) in enumerate(banks_list):
    row = db.execute(
        sa_select(CentralBankStatement)
        .where(CentralBankStatement.bank_code == code)
        .order_by(CentralBankStatement.event_date.desc()).limit(1)
    ).scalar_one_or_none()

    with cols[i % 4]:
        tone  = row.tone      if row else "neutral"
        score = row.tone_score if row else 0.0
        color = CB_TONE_COLORS.get(tone, NEUTRAL)
        label = {"very-hawkish":"🦅 Very Hawkish","hawkish":"🔺 Hawkish",
                 "neutral":"⚖️ Neutral","dovish":"🔻 Dovish","very-dovish":"🕊️ Very Dovish"}.get(tone, tone)
        st.markdown(f"""<div style="background:#111118;border:1px solid #1e1e2e;border-radius:8px;
        padding:0.75rem;margin-bottom:0.5rem">
        <div style="font-size:10px;color:{DIM};font-weight:700">{code} · {meta['currency']}</div>
        <div style="font-size:0.85rem;font-weight:700;color:{color};margin:4px 0">{label}</div>
        <div style="font-size:10px;color:{DIM}">{meta['name']}</div>
        {"<div style='font-size:10px;color:"+DIM+";margin-top:4px'>"+row.event_date+"</div>" if row else ""}
        </div>""", unsafe_allow_html=True)

db.close()

st.markdown("---")

# ── Add new statement for AI classification ───────────────────────────────────
section_header("Classify New Statement", "🧠")
st.caption("Paste any central bank text (press conference, minutes, speech) — AI will classify the tone.")

sf1, sf2, sf3 = st.columns([2, 2, 2])
with sf1: bank_code  = st.selectbox("Central Bank", list(CENTRAL_BANKS.keys()))
with sf2: event_type = st.selectbox("Event Type", ["decision","speech","minutes","presser","statement"])
with sf3: event_date = st.date_input("Date")

headline  = st.text_input("Headline / Title")
full_text = st.text_area("Paste full text (optional — used for better classification)", height=150)

if st.button("🧠 Classify with AI", use_container_width=True):
    if not headline:
        st.error("Please enter at least a headline.")
    elif not (st.session_state.get("_ai_ok") or True):
        st.error("AI not configured.")
    else:
        with st.spinner("Classifying..."):
            try:
                from src.ai.analyst import classify_cb_tone
                bank_name = CENTRAL_BANKS[bank_code]["name"]
                result    = classify_cb_tone(bank_name, event_type, str(event_date),
                                             f"{headline}\n\n{full_text}")
                color = CB_TONE_COLORS.get(result["tone"], NEUTRAL)
                st.markdown(f"""<div style="background:#111118;border:1px solid {color};
                border-radius:8px;padding:1rem;margin:0.5rem 0">
                <div style="font-size:1.1rem;font-weight:900;color:{color}">
                  Tone: {result['tone'].upper().replace('-',' ')} (Score: {result['tone_score']:+.1f})</div>
                <div style="font-size:0.85rem;color:{DIM};margin-top:6px">{result['reasoning']}</div>
                </div>""", unsafe_allow_html=True)

                # Save to DB
                db2 = get_db()
                db2.add(CentralBankStatement(
                    bank_code=bank_code, event_type=event_type,
                    event_date=str(event_date), headline=headline,
                    full_text=full_text[:5000] if full_text else None,
                    tone=result["tone"], tone_score=result["tone_score"],
                    rate_decision=result["rate_decision"], ai_reasoning=result["reasoning"],
                ))
                db2.commit(); db2.close()
                st.success("Saved to database.", icon="✅")
            except Exception as e:
                st.error(f"Classification failed: {e}")

st.markdown("---")

# ── Statement history ──────────────────────────────────────────────────────────
section_header("Statement History", "📋")
import pandas as pd
db3 = get_db()
rows = db3.execute(
    sa_select(CentralBankStatement).order_by(CentralBankStatement.event_date.desc()).limit(50)
).scalars().all()
db3.close()

if rows:
    df = pd.DataFrame([{
        "Bank": r.bank_code, "Date": r.event_date, "Event": r.event_type,
        "Tone": r.tone, "Score": r.tone_score, "Decision": r.rate_decision,
        "Headline": r.headline[:80] + "..." if r.headline and len(r.headline) > 80 else r.headline,
    } for r in rows])
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No statements classified yet. Use the form above to add one.", icon="ℹ️")

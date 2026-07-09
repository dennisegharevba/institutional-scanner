"""Probability engine + master scanner — sync, Streamlit-compatible."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import streamlit as st
from src.core.config import MARKETS, MODULE_WEIGHTS, get_settings

settings = get_settings()
THRESHOLD = settings.signal_threshold


@dataclass
class ProbabilityResult:
    symbol:         str
    direction:      str
    probability:    float
    confidence:     str
    risk_rating:    str
    module_scores:  dict = field(default_factory=dict)
    meets_threshold:bool = False
    breakdown:      list = field(default_factory=list)


def compute(symbol, technical_score, technical_bias, inflation_score, inflation_bias,
            labour_score, labour_bias, bond_score, bond_bias, cot_score, cot_bias,
            cb_score, cb_bias, sentiment_score, sentiment_bias,
            seasonality_score=50.0, seasonality_bias="neutral",
            direction_override=None) -> ProbabilityResult:

    if direction_override:
        direction = direction_override
    elif technical_bias in ("bullish","bearish"):
        direction = "long" if technical_bias == "bullish" else "short"
    elif bond_bias != "neutral":
        direction = "long" if bond_bias == "bullish" else "short"
    else:
        direction = "long"

    def orient(score, bias):
        return score if direction == "long" else 100 - score

    macro_avg = (inflation_score + bond_score + labour_score) / 3
    raw = {
        "technical":    orient(technical_score,  technical_bias),
        "macro":        orient(macro_avg,         ""),
        "cot":          orient(cot_score,         cot_bias),
        "central_bank": orient(cb_score,          cb_bias),
        "inflation":    orient(inflation_score,   inflation_bias),
        "labour":       orient(labour_score,      labour_bias),
        "sentiment":    orient(sentiment_score,   sentiment_bias),
        "seasonality":  orient(seasonality_score, seasonality_bias),
    }
    tw = sum(MODULE_WEIGHTS.values())
    prob = sum(raw[m] * (MODULE_WEIGHTS.get(m, 0) / tw) for m in raw)
    prob = max(0.0, min(100.0, prob))
    conf = "high" if prob >= 80 else ("medium" if prob >= THRESHOLD else "low")
    agree = sum(1 for s in raw.values() if s >= 55) / len(raw)
    risk  = "low" if agree >= 0.8 else ("medium" if agree >= 0.6 else ("high" if agree >= 0.4 else "very-high"))
    return ProbabilityResult(
        symbol=symbol, direction=direction, probability=round(prob, 1),
        confidence=conf, risk_rating=risk, module_scores=raw,
        meets_threshold=prob >= THRESHOLD,
        breakdown=[f"{m.replace('_',' ').title()}: {raw[m]:.0f}/100 (weight {MODULE_WEIGHTS.get(m,0)}%)" for m in raw],
    )


def compute_risk_levels(entry, direction, atr, sl_mult=1.5, rr1=2.0, rr2=3.5):
    if not atr or atr <= 0:
        return {}
    sl_d = atr * sl_mult
    if direction == "long":
        return {"entry_price": round(entry,5), "stop_loss": round(entry-sl_d,5),
                "take_profit_1": round(entry+sl_d*rr1,5), "take_profit_2": round(entry+sl_d*rr2,5),
                "risk_reward": round(rr1,2)}
    return {"entry_price": round(entry,5), "stop_loss": round(entry+sl_d,5),
            "take_profit_1": round(entry-sl_d*rr1,5), "take_profit_2": round(entry-sl_d*rr2,5),
            "risk_reward": round(rr1,2)}


# ── Master scanner ────────────────────────────────────────────────────────────

@st.cache_data(ttl=settings.scan_ttl_minutes * 60, show_spinner=False)
def run_scan() -> list[dict]:
    """Run the full scanner. Cached for scan_ttl_minutes."""
    from src.modules.modules import (
        run_inflation, run_labour, run_bond, run_sentiment,
    )
    from src.data.yahoo import fetch_and_score
    from src.data.cot   import get_latest_cot
    from src.ai.analyst  import generate_signal_narrative

    inflation = run_inflation()
    labour    = run_labour()
    bond      = run_bond()
    sentiment = run_sentiment()
    cb_score  = 50.0   # neutral default (updated when CB data is saved)

    signals = []
    for symbol in MARKETS:
        try:
            tech = fetch_and_score(symbol)
            if not tech or tech.get("total", 0) == 0:
                continue
            cot  = get_latest_cot(symbol)
            cot_score = cot["bias_score"]    if cot else 50.0
            cot_bias  = cot["institutional_bias"] if cot else "neutral"

            prob = compute(
                symbol=symbol,
                technical_score=tech["total"],  technical_bias=tech["bias"],
                inflation_score=inflation.inflation_score, inflation_bias=inflation.bias,
                labour_score=labour.labour_score,     labour_bias=labour.bias,
                bond_score=bond.bond_score,           bond_bias=bond.bias,
                cot_score=cot_score,                  cot_bias=cot_bias,
                cb_score=cb_score,                    cb_bias="neutral",
                sentiment_score=sentiment.overall_score, sentiment_bias=sentiment.risk_appetite,
            )
            if not prob.meets_threshold:
                continue

            levels = compute_risk_levels(tech["price"], prob.direction, tech["atr"])
            if not levels:
                continue

            key_data = {
                "Price": f"{tech['price']:.4f}", "ATR(14)": f"{tech['atr']:.4f}",
                "RSI(14)": f"{tech['rsi']:.1f}",
                "COT Index": f"{cot['cot_index']:.0f}/100" if cot else "N/A",
                "Core PCE": f"{inflation.core_pce_yoy:.1f}%" if inflation.core_pce_yoy else "N/A",
                "Bond Regime": bond.regime, "VIX": f"{sentiment.vix:.1f}" if sentiment.vix else "N/A",
            }
            try:
                reasoning = generate_signal_narrative(
                    symbol=symbol, market_name=MARKETS[symbol]["name"],
                    direction=prob.direction, probability=prob.probability,
                    module_scores=prob.module_scores, key_data=key_data,
                )
            except Exception:
                reasoning = f"Scanner is {prob.direction} on {MARKETS[symbol]['name']} with {prob.probability:.0f}% probability."

            expires = datetime.utcnow() + timedelta(hours=96)
            signal = {
                "symbol": symbol, "market_name": MARKETS[symbol]["name"],
                "direction": prob.direction, "probability": prob.probability,
                "confidence": prob.confidence, "risk_rating": prob.risk_rating,
                "entry_price": levels["entry_price"], "stop_loss": levels["stop_loss"],
                "take_profit_1": levels["take_profit_1"], "take_profit_2": levels["take_profit_2"],
                "risk_reward": levels["risk_reward"], "atr_value": round(tech["atr"], 5),
                "module_scores": prob.module_scores,
                "technical_bias": tech["bias"],
                "macro_bias": "bullish" if (inflation.inflation_score + bond.bond_score) / 2 > 55 else "bearish",
                "cot_bias": cot_bias, "ai_reasoning": reasoning,
                "expires_at": expires.isoformat(),
                "countdown_secs": int((expires - datetime.utcnow()).total_seconds()),
                "created_at": datetime.utcnow().isoformat(),
            }
            signals.append(signal)
        except Exception:
            continue

    return signals

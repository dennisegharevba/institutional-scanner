"""All AI domain analysis functions — sync."""
from __future__ import annotations
from src.ai.provider import ask, parse_json

SYSTEM = """You are a senior institutional macro strategist with 20+ years experience.
Respond with precision and brevity. Return ONLY valid JSON when requested — no markdown, no preamble."""


def generate_signal_narrative(symbol, market_name, direction, probability, module_scores, key_data) -> str:
    scores_text = "\n".join(f"  {m.replace('_',' ').title()}: {s:.0f}/100" for m, s in module_scores.items())
    data_text   = "\n".join(f"  {k}: {v}" for k, v in key_data.items())
    prompt = f"""Generate a professional trade signal narrative.

Market: {market_name} ({symbol}) | Direction: {direction.upper()} | Probability: {probability:.0f}%

Module Scores:
{scores_text}

Key Data:
{data_text}

Write ONE paragraph (max 75 words) starting with:
"The scanner is {direction} on {market_name} because..."
Be specific. Use the actual data. Sound like a Goldman Sachs research note.
Return ONLY the paragraph — no JSON, no preamble."""
    return ask(prompt, system=SYSTEM, max_tokens=200)


def classify_cb_tone(bank_name, event_type, event_date, text) -> dict:
    prompt = f"""Classify this central bank communication:
Bank: {bank_name} | Event: {event_type} | Date: {event_date}
Content: {text[:2500]}

Return ONLY valid JSON:
{{"tone":"<very-hawkish|hawkish|neutral|dovish|very-dovish>","tone_score":<-2.0 to +2.0>,
"rate_decision":"<hike|hold|cut|none>","reasoning":"<2 sentences>"}}"""
    raw = ask(prompt, system=SYSTEM, max_tokens=400, expect_json=True)
    r   = parse_json(raw)
    return {"tone": r.get("tone","neutral"), "tone_score": float(r.get("tone_score",0)),
            "rate_decision": r.get("rate_decision","hold"), "reasoning": r.get("reasoning","")}


def analyze_news_item(headline, body="") -> dict:
    prompt = f"""Analyze this financial news for market impact:
Headline: {headline}
Body: {body[:1000] if body else "N/A"}

Return ONLY valid JSON:
{{"sentiment":"<positive|negative|neutral>","sentiment_score":<-1.0 to +1.0>,
"affected_markets":["GC","ES",...],
"immediate_impact":"<brief>","confidence_score":<0-1>,
"duration_label":"<intraday|1-3 days|1 week>","reasoning":"<1-2 sentences>"}}"""
    raw = ask(prompt, system=SYSTEM, max_tokens=400, expect_json=True)
    r   = parse_json(raw)
    return {"sentiment": r.get("sentiment","neutral"),
            "sentiment_score": float(r.get("sentiment_score",0)),
            "affected_markets": r.get("affected_markets",[]),
            "immediate_impact": r.get("immediate_impact",""),
            "confidence_score": float(r.get("confidence_score",0.5)),
            "duration_label": r.get("duration_label","intraday"),
            "reasoning": r.get("reasoning","")}


def generate_macro_summary(macro_data: dict) -> dict:
    data_text = "\n".join(f"  {k}: {v}" for k, v in macro_data.items() if v is not None)
    prompt = f"""Analyze the macro environment:
{data_text}

Return ONLY valid JSON:
{{"regime":"<Risk-On Growth|Disinflation|Recession Risk|Higher For Longer|Stagflation|Liquidity Expansion>",
"risk_appetite":"<risk-on|neutral|risk-off>","fed_bias":"<hawkish|neutral|dovish>",
"top_risks":["risk1","risk2","risk3"],"top_opportunities":["opp1","opp2","opp3"],
"one_sentence_summary":"<concise>","portfolio_preference":"<risk-assets|defensive|precious-metals|cash|mixed>"}}"""
    raw = ask(prompt, system=SYSTEM, max_tokens=500, expect_json=True)
    return parse_json(raw)

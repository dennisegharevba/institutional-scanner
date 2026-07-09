"""Sync AI provider — Claude primary, OpenAI fallback."""
from __future__ import annotations
import json, re
from src.core.config import get_settings

settings = get_settings()


def ask(prompt: str, system: str = "", max_tokens: int = 1000, expect_json: bool = False) -> str:
    providers = _order()
    last_err  = None
    for p in providers:
        try:
            text = _call(p, system, prompt, max_tokens)
            return _clean_json(text) if expect_json else text
        except Exception as e:
            last_err = e
    return f"AI unavailable: {last_err}"


def _order() -> list[str]:
    preferred = settings.ai_provider
    all_p = ["anthropic", "openai"]
    available = []
    if settings.anthropic_api_key: available.append("anthropic")
    if settings.openai_api_key:    available.append("openai")
    order = [preferred] + [p for p in all_p if p != preferred]
    return [p for p in order if p in available] or ["anthropic"]


def _call(provider: str, system: str, prompt: str, max_tokens: int) -> str:
    if provider == "anthropic":
        import anthropic
        client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        msg = client.messages.create(
            model="claude-sonnet-4-6", max_tokens=max_tokens,
            system=system or "You are an institutional macro strategist.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text
    elif provider == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.chat.completions.create(
            model="gpt-4o", max_tokens=max_tokens,
            messages=[
                {"role": "system", "content": system or "You are an institutional macro strategist."},
                {"role": "user",   "content": prompt},
            ],
        )
        return resp.choices[0].message.content
    raise ValueError(f"Unknown provider: {provider}")


def _clean_json(text: str) -> str:
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    return re.sub(r"\s*```$", "", text).strip()


def parse_json(text: str) -> dict:
    try:
        return json.loads(_clean_json(text))
    except Exception:
        m = re.search(r"\{.*\}", text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except Exception:
                pass
    return {}

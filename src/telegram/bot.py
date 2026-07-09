"""Telegram bot — sync, uses requests."""
from __future__ import annotations
from datetime import datetime, timezone
import requests
from src.core.config import get_settings

settings = get_settings()

DIR_EMOJI  = {"long": "🟢 LONG", "short": "🔴 SHORT"}
CONF_EMOJI = {"high": "🔥", "medium": "⚡", "low": "💡"}


def send_signal_alert(signal: dict) -> bool:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        return False
    text = _fmt_signal(signal)
    return _send(settings.telegram_chat_id, text)


def _send(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    try:
        url  = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        resp = requests.post(url, json={"chat_id": chat_id, "text": text,
                                        "parse_mode": parse_mode,
                                        "disable_web_page_preview": True}, timeout=15)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def _fmt_signal(sig: dict) -> str:
    d = sig["direction"]; prob = sig["probability"]; conf = sig["confidence"]
    scores = sig.get("module_scores", {})
    scores_html = "".join(
        f"  {m.replace('_',' ').title():<14} {_bar(float(s))} {s:.0f}/100\n"
        for m, s in scores.items()
    )
    exp = sig.get("expires_at","")
    cd  = ""
    if exp:
        try:
            dt = datetime.fromisoformat(exp.replace("Z","+00:00"))
            if dt.tzinfo is None: dt = dt.replace(tzinfo=timezone.utc)
            secs = int((dt - datetime.now(timezone.utc)).total_seconds())
            if secs > 0:
                h, m = divmod(secs // 60, 60)
                cd = f"{h}h {m}m"
        except Exception:
            pass
    return (
        f"╔══════════════════════════════╗\n"
        f"║  🏛️  <b>INSTITUTIONAL SCANNER</b>  ║\n"
        f"╚══════════════════════════════╝\n\n"
        f"<b>{DIR_EMOJI.get(d,d.upper())} — {sig['market_name']} ({sig['symbol']})</b>\n\n"
        f"📊 <b>Probability:</b> <b>{prob:.0f}%</b>  {CONF_EMOJI.get(conf,'')} {conf.upper()}\n"
        f"⏰ <b>Expires in:</b> {cd or 'N/A'}\n\n"
        f"──────── TRADE LEVELS ────────\n"
        f"🎯 <b>Entry:</b>         <code>{sig['entry_price']:.5f}</code>\n"
        f"🛑 <b>Stop Loss:</b>     <code>{sig['stop_loss']:.5f}</code>\n"
        f"✅ <b>Take Profit 1:</b>  <code>{sig['take_profit_1']:.5f}</code>\n"
        f"🏆 <b>Take Profit 2:</b>  <code>{sig['take_profit_2']:.5f}</code>\n"
        f"⚖️  <b>Risk/Reward:</b>   <code>1:{sig['risk_reward']:.1f}</code>\n\n"
        f"──────── BIAS ────────────────\n"
        f"{'🟢' if sig.get('technical_bias')=='bullish' else '🔴'} <b>Technical:</b>    {sig.get('technical_bias','—').title()}\n"
        f"{'🟢' if sig.get('macro_bias')=='bullish' else '🔴'} <b>Macro:</b>        {sig.get('macro_bias','—').title()}\n"
        f"{'🟢' if sig.get('cot_bias')=='bullish' else '🔴'} <b>Institutional:</b> {sig.get('cot_bias','—').title()}\n\n"
        f"──────── MODULE SCORES ───────\n<pre>{scores_html}</pre>\n"
        f"──────── AI REASONING ────────\n"
        f"<i>{sig.get('ai_reasoning','')}</i>\n\n"
        f"──────────────────────────────\n"
        f"🕐 {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"⚠️  <i>Not financial advice. DYOR.</i>"
    )


def _bar(score: float, w: int = 8) -> str:
    f = round(score / 100 * w)
    return "▓" * f + "░" * (w - f)

"""Settings page — API keys, Telegram test, system status."""
import streamlit as st
from src.core.config import get_settings
from src.ui.helpers import BEAR, BULL, DIM, GOLD, inject_css, section_header

st.set_page_config(page_title="Settings · Institutional", page_icon="⚙️", layout="wide")
inject_css()
st.title("⚙️ Settings")

settings = get_settings()

# ── System status ─────────────────────────────────────────────────────────────
section_header("System Status", "✅")
checks = [
    ("FRED API",           bool(settings.fred_api_key),           "Add FRED_API_KEY to Streamlit secrets"),
    ("Anthropic / Claude", bool(settings.anthropic_api_key),      "Add ANTHROPIC_API_KEY to secrets"),
    ("OpenAI (fallback)",  bool(settings.openai_api_key),         "Optional — add OPENAI_API_KEY"),
    ("Telegram Bot",       bool(settings.telegram_bot_token),     "Optional — add TELEGRAM_BOT_TOKEN"),
    ("Telegram Chat ID",   bool(settings.telegram_chat_id),       "Optional — add TELEGRAM_CHAT_ID"),
]
for label, ok, note in checks:
    col1, col2 = st.columns([3, 4])
    col1.markdown(f"{'✅' if ok else '❌'} **{label}**")
    col2.markdown(f"<span style='font-size:11px;color:{BULL if ok else BEAR}'>"
                  f"{'Configured' if ok else note}</span>", unsafe_allow_html=True)

st.markdown("---")

# ── How to add secrets ────────────────────────────────────────────────────────
section_header("How to Add API Keys", "🔑")
st.markdown("""
**On Streamlit Cloud:**
1. Open your app → click **⋮ (three dots)** top-right → **Settings**
2. Click **Secrets** in the left panel
3. Paste your keys in TOML format:

```toml
ANTHROPIC_API_KEY   = "sk-ant-xxxxxxxxx"
FRED_API_KEY        = "your_fred_key"
TELEGRAM_BOT_TOKEN  = "123456:ABC-xyz"
TELEGRAM_CHAT_ID    = "-1001234567890"
```

4. Click **Save** — the app restarts automatically.

**Running locally:**
Create `.streamlit/secrets.toml` in the project folder with the same format above.
""")

st.markdown("---")

# ── Telegram test ─────────────────────────────────────────────────────────────
section_header("Test Telegram Alert", "📨")
if not settings.telegram_bot_token:
    st.info("Configure Telegram credentials above first.", icon="ℹ️")
else:
    if st.button("📨 Send Test Message"):
        from src.telegram.bot import _send
        ok = _send(settings.telegram_chat_id,
                   "🏛️ <b>Institutional Scanner</b> — test message. Connection is working! ✅")
        st.success("Test message sent!" if ok else "Failed — check your BOT_TOKEN and CHAT_ID.",
                   icon="✅" if ok else "❌")

st.markdown("---")

# ── Scanner config ─────────────────────────────────────────────────────────────
section_header("Scanner Configuration", "🎛️")
st.markdown(f"""
| Setting | Value |
|---|---|
| Signal threshold | {settings.signal_threshold}% |
| Scan cache TTL  | {settings.scan_ttl_minutes} minutes |
| AI provider     | {settings.ai_provider} |
| Database        | SQLite (local file — scanner.db) |

To change these, add them to your Streamlit secrets:
```toml
SIGNAL_THRESHOLD   = 65     # minimum probability to emit a signal
SCAN_TTL_MINUTES   = 15     # how long scan results are cached
AI_PROVIDER        = "anthropic"
```
""")

st.markdown("---")

# ── Clear cache ────────────────────────────────────────────────────────────────
section_header("Cache Management", "🗑️")
st.caption("Cached data refreshes automatically based on TTL. Use the buttons below to force a refresh.")
c1, c2 = st.columns(2)
with c1:
    if st.button("🗑️ Clear All Caches", use_container_width=True):
        st.cache_data.clear()
        st.success("All caches cleared — data will reload on next visit.", icon="✅")
with c2:
    if st.button("🏛️ Re-create DB Tables", use_container_width=True):
        from src.core.database import create_tables
        create_tables()
        st.success("Database tables verified/created.", icon="✅")

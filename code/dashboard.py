# dashboard.py

import streamlit as st
import json
import time
from pathlib import Path

# ──────────────────── CONFIG ────────────────────
DASHBOARD_PATH = Path(__file__).parent / "dashboard_state.json"
POLL_INTERVAL = 1.5  # seconds between dashboard refreshes
# ─────────────────────────────────────────────────

st.set_page_config(
    page_title="Infinite AI Deep Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔮 Infinite AI Deep Dashboard")

# Create containers for “top stats” so we can update them easily each loop:
stats_col1, stats_col2, stats_col3, stats_col4, stats_col5, stats_col6 = st.columns(6)

# Section for showing historical outputs in a scrollable area:
st.subheader("📚 All Outputs So Far")
outputs_area = st.empty()

# Section for “Current Generation Details”:
st.subheader("🛠 Current Generation Details")
gen_col1, gen_col2, gen_col3 = st.columns(3)
system_prompt_area = st.empty()
in_tok_area = st.empty()
out_tok_area = st.empty()

# Section for showing LTM summaries (pulls from memory each iteration):
st.subheader("📜 Fetched LTM Summaries")
ltm_summaries_area = st.empty()

# Helper to format a runtime in seconds → “D d H h M m S s”
def format_runtime(seconds: float) -> str:
    secs = int(seconds)
    days, secs = divmod(secs, 86400)
    hours, secs = divmod(secs, 3600)
    mins, secs = divmod(secs, 60)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if mins or hours or days:
        parts.append(f"{mins}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


while True:
    try:
        with open(DASHBOARD_PATH, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        st.sidebar.warning("Waiting for `dashboard_state.json` to appear …")
        time.sleep(1)
        st.experimental_rerun()
    except json.JSONDecodeError:
        st.sidebar.error("`dashboard_state.json` is malformed. Retrying …")
        time.sleep(1)
        st.experimental_rerun()

    # ──────────────────────────────────────────────────────────────────
    # 1) Update Top‐Level Stats (6 columns)
    # ──────────────────────────────────────────────────────────────────
    stats_col1.metric("Iteration", data.get("iteration", "N/A"))
    stats_col2.metric("STM Tokens", data.get("stm_tokens", "N/A"))
    stats_col3.metric("Cost (last)", f"${data.get('cost', 0):.5f}")
    stats_col4.metric("Total Cost", f"${data.get('total_cost', 0):.5f}")
    stats_col5.metric("Total Input Tokens", data.get("total_input_tokens", "N/A"))
    stats_col6.metric("Total Output Tokens", data.get("total_output_tokens", "N/A"))

    # ──────────────────────────────────────────────────────────────────
    # 2) Display Total Runtime in dynamic D d H h M m S s format
    # ──────────────────────────────────────────────────────────────────
    total_runtime_secs = data.get("total_runtime_seconds", 0.0)
    formatted_runtime = format_runtime(float(total_runtime_secs))
    st.write(f"⏳ **Total Runtime:** {formatted_runtime}")

    st.markdown("---")

    # ──────────────────────────────────────────────────────────────────
    # 3) “All Outputs So Far” as a scrollable text area
    # ──────────────────────────────────────────────────────────────────
    all_outputs = data.get("all_outputs", [])
    # Combine them with a separator for readability:
    combined_text = "\n\n---\n\n".join(all_outputs)
    outputs_area.text_area(
        label="Scroll through every LLM output (newest at bottom)",
        value=combined_text,
        height=300,
        disabled=True,
    )

    st.markdown("---")

    # ──────────────────────────────────────────────────────────────────
    # 4) Current Generation Details:
    #    • System Prompt
    #    • Input Tokens (current) & Output Tokens (current)
    # ──────────────────────────────────────────────────────────────────
    gen_col1.subheader("🔧 System Prompt")
    gen_col1.code(data.get("system_prompt", "_no prompt_"), language="markdown")

    gen_col2.subheader("🔢 Input Tokens (Curr)")
    gen_col2.write(data.get("input_tokens_current", "N/A"))

    gen_col3.subheader("🔢 Output Tokens (Curr)")
    gen_col3.write(data.get("output_tokens_current", "N/A"))

    st.markdown("---")

    # ──────────────────────────────────────────────────────────────────
    # 5) Fetched LTM Summaries
    # ──────────────────────────────────────────────────────────────────
    fetched = data.get("fetched_ltm_summaries", [])
    if fetched:
        ltm_summaries_area.write("\n".join(f"- {s}" for s in fetched))
    else:
        ltm_summaries_area.write("_No LTM fetched this iteration._")

    # ──────────────────────────────────────────────────────────────────
    # 6) Pause & return control to Streamlit for auto‐refresh
    # ──────────────────────────────────────────────────────────────────
    time.sleep(POLL_INTERVAL)
    st.experimental_rerun()

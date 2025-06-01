"""
Streamlit dashboard for “Infinite-GPT”
———————————————
• Fixed Prev/Next/JUMP controls (work every click)
• Reads real per-page metadata if present in dashboard_state.json
• Writes a short JS log to browser console on every page change
"""

from __future__ import annotations
import json, time, html, json as _json
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as st_html
from streamlit_autorefresh import st_autorefresh   # pip install streamlit-autorefresh

# ───────────── CONFIG ─────────────
DASHBOARD_PATH = Path(__file__).parent / "dashboard_state.json"
REFRESH_SEC    = 1.5
BOX_HEIGHT_PX  = 560
HEADER_PX      = 40
# ──────────────────────────────────

st.set_page_config("Infinite-GPT dashboard", layout="wide")
st.title("🔮 Infinite AI Deep Dashboard")

# ---------- helpers ----------
def fmt_runtime(sec: int | float) -> str:
    sec = int(sec)
    d, sec = divmod(sec, 86_400)
    h, sec = divmod(sec, 3_600)
    m, s   = divmod(sec, 60)
    return " ".join(
        f"{n}{u}" for n, u in ((d,"d"), (h,"h"), (m,"m"), (s,"s")) if n or u == "s"
    )

def js_log(msg: str):
    """Emit a one-liner to the browser console."""
    st_html(f"<script>console.log({_json.dumps(msg)});</script>", height=0)

# ---------- initialise session ----------
if "page" not in st.session_state:
    st.session_state.page = 1

# ---------- autorefresh ----------
st_autorefresh(interval=REFRESH_SEC*1000, key="autorefresh")

# ---------- load JSON ----------
try:
    state_raw = DASHBOARD_PATH.read_text()
    state     = json.loads(state_raw) if state_raw.strip() else {}
except FileNotFoundError:
    st.info("Waiting for dashboard_state.json …")
    st.stop()
except json.JSONDecodeError:
    st.error("dashboard_state.json is malformed – fix or delete it.")
    st.stop()

# ---------- pull arrays ----------
outputs = state.get("all_outputs", [])
total_pages = len(outputs)
if total_pages == 0:
    st.info("*No outputs yet…*")
    st.stop()

# first choice: history arrays already saved by main.py
hist_keys = ("iteration_history",
             "system_prompt_history",
             "output_tokens_history",
             "max_tokens_history")

if all(k in state for k in hist_keys):
    (iter_hist, prompt_hist,
     out_tok_hist, max_tok_hist) = (state[k] for k in hist_keys)
else:
    # fallback – repeat “latest” values for older pages
    latest_iter   = state.get("iteration")
    latest_prompt = state.get("system_prompt", "")
    latest_outtok = state.get("output_tokens_current")
    latest_maxtok = state.get("max_tokens_current")
    repeat = lambda v: [v]*total_pages
    iter_hist, prompt_hist, out_tok_hist, max_tok_hist = map(
        repeat, (latest_iter, latest_prompt, latest_outtok, latest_maxtok)
    )

# ensure we never step outside bounds
st.session_state.page = max(1, min(st.session_state.page, total_pages))
idx = st.session_state.page - 1

# ---------- top metrics ----------
cols = st.columns(6)
for col, (lbl, val) in zip(
        cols,
        (("Iteration",            state.get("iteration")),
         ("STM Tokens",           state.get("stm_tokens")),
         ("Cost (last)",         f"${state.get('cost',0):.5f}"),
         ("Total Cost",          f"${state.get('total_cost',0):.5f}"),
         ("Total Input Tokens",   state.get("total_input_tokens")),
         ("Total Output Tokens",  state.get("total_output_tokens")))):
    col.metric(lbl, val if val is not None else "—")
st.write(f"⏳ **Total Runtime:** {fmt_runtime(state.get('total_runtime_seconds',0))}")

# ---------- per-page box ----------
iteration   = iter_hist[idx]
prompt_txt  = prompt_hist[idx]
out_tokens  = out_tok_hist[idx]
max_tokens  = max_tok_hist[idx]

prompt_html = html.escape(prompt_txt)
body_html   = html.escape(outputs[idx])

scroll_h = BOX_HEIGHT_PX - HEADER_PX
st_html(f"""
<div style='background:#f9f9f9;border:1px solid #ddd;border-radius:6px;
            width:100%;height:{BOX_HEIGHT_PX}px;overflow:hidden'>
  <div style='height:{HEADER_PX}px;line-height:{HEADER_PX}px;padding:0 16px;
              border-bottom:1px solid #ccc;font-family:Arial;font-size:14px;
              color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis'>
    <strong>Iteration:</strong> {iteration} &nbsp;|&nbsp;
    <strong>Prompt:</strong> <code style='font-size:13px'>{prompt_html}</code> &nbsp;|&nbsp;
    <strong>Tokens:</strong> {out_tokens or "N/A"}{' / '+str(max_tokens) if max_tokens else ''}
  </div>
  <div style='height:{scroll_h}px;padding:12px 16px;font-family:Menlo,Consolas,
              "Courier New",monospace;font-size:15px;line-height:1.5;color:#1d1d1d;
              background:#fff;overflow-y:auto;white-space:pre-wrap;word-break:break-word'>
    {body_html}
  </div>
</div>""", height=BOX_HEIGHT_PX+8)

# ---------- callbacks ----------
def _prev():
    if st.session_state.page > 1:
        st.session_state.page -= 1
        js_log(f"◀ prev → page {st.session_state.page}")

def _next():
    if st.session_state.page < total_pages:
        st.session_state.page += 1
        js_log(f"next ▶ → page {st.session_state.page}")

# ---------- nav bar ----------
n1, n2, n3, n4 = st.columns([1,2,1,2])
with n1:
    st.button("◀ Previous",   disabled=(idx==0),          on_click=_prev, key="prev")
with n2:
    st.markdown(f"**Page {st.session_state.page} of {total_pages}**")
with n3:
    st.button("Next ▶",       disabled=(idx==total_pages-1), on_click=_next, key="next")
with n4:
    choice = st.selectbox("Jump", list(range(1, total_pages+1)), index=idx, key="jump")
    if choice != st.session_state.page:
        st.session_state.page = choice
        js_log(f"jump → page {choice}")

st.divider()

# ---------- current generation ----------
st.subheader("🛠 Current Generation Details")
cg1, cg2, cg3 = st.columns(3)
cg1.code(state.get("system_prompt", "_no prompt_"), language="markdown")
cg2.metric("Input Tokens (Curr)",  state.get("input_tokens_current", "—"))
cg3.metric("Output Tokens (Curr)", state.get("output_tokens_current", "—"))

st.divider()

# ---------- LTM summaries ----------
st.subheader("📜 Fetched LTM Summaries")
if state.get("fetched_ltm_summaries"):
    st.markdown("\n\n".join(f"**{i+1}.** {s.strip()}"
                            for i, s in enumerate(state["fetched_ltm_summaries"])))

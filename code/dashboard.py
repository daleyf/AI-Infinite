"""dashboard.py – robust version
This Streamlit dashboard tracks an "Infinite-GPT" loop.
• Fixed-height history pane with per-page metadata.
• Stable Prev / Next buttons & Jump dropdown (they work on every click).
• Maintains its **own copy** of metadata arrays in `st.session_state` so even
  if the JSON file only stores the *latest* iteration, older pages still
  remember their prompt / token counts.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import streamlit as st
from streamlit.components.v1 import html as st_html

# ─────────────── CONFIG ────────────────
DASHBOARD_PATH  = Path(__file__).parent / "dashboard_state.json"
REFRESH_SEC     = 1.5
BOX_HEIGHT_PX   = 560
HEADER_PX       = 40
# ───────────────────────────────────────

st.set_page_config("Infinite AI Deep Dashboard", layout="wide")
st.title("🔮 Infinite AI Deep Dashboard")

# ─────────── helpers ───────────

def fmt_runtime(sec: int | float) -> str:
    sec = int(sec)
    d, sec = divmod(sec, 86_400)
    h, sec = divmod(sec, 3_600)
    m, s   = divmod(sec, 60)
    parts = []
    if d: parts.append(f"{d}d")
    if h or d: parts.append(f"{h}h")
    if m or h or d: parts.append(f"{m}m")
    parts.append(f"{s}s")
    return " ".join(parts)

# ─────────── session-state init ───────────

def _init_array(name: str):
    if name not in st.session_state:
        st.session_state[name] = []

for key in ("page", "iter_hist", "prompt_hist", "out_tok_hist", "max_tok_hist"):
    if key == "page":
        st.session_state.setdefault(key, 1)
    else:
        _init_array(key)

# callbacks

def prev_page():
    if st.session_state.page > 1:
        st.session_state.page -= 1

def next_page(total_pages: int):
    if st.session_state.page < total_pages:
        st.session_state.page += 1

def jump_to(page: int):
    st.session_state.page = page

# ─────────── main loop ───────────
while True:
    # 1️⃣ read JSON safely ----------------------
    try:
        state = json.loads(DASHBOARD_PATH.read_text())
    except FileNotFoundError:
        st.info("Waiting for dashboard_state.json …")
        time.sleep(1); st.experimental_rerun()
    except json.JSONDecodeError:
        st.warning("State file malformed – retrying …")
        time.sleep(1); st.experimental_rerun()

    # 2️⃣ pull arrays & ensure we cache metadata ----
    outputs = state.get("all_outputs", [])
    latest_iter   = state.get("iteration")
    latest_prompt = state.get("system_prompt", "")
    latest_outtok = state.get("output_tokens_current")
    latest_maxtok = state.get("max_tokens_current")

    # append metadata for any unseen outputs
    while len(st.session_state.iter_hist) < len(outputs):
        st.session_state.iter_hist.append(latest_iter)
        st.session_state.prompt_hist.append(latest_prompt)
        st.session_state.out_tok_hist.append(latest_outtok)
        st.session_state.max_tok_hist.append(latest_maxtok)

    total_pages = len(outputs)
    if total_pages == 0:
        st.info("*No outputs yet…*")
        time.sleep(REFRESH_SEC); st.experimental_rerun()

    # keep page within bounds
    st.session_state.page = max(1, min(st.session_state.page, total_pages))
    idx = st.session_state.page - 1

    # 3️⃣ top stats --------------------------------
    cols = st.columns(6)
    stats = [
        ("Iteration",             state.get("iteration")),
        ("STM Tokens",            state.get("stm_tokens")),
        ("Cost (last)",          f"${state.get('cost',0):.5f}"),
        ("Total Cost",           f"${state.get('total_cost',0):.5f}"),
        ("Total Input Tokens",    state.get("total_input_tokens")),
        ("Total Output Tokens",   state.get("total_output_tokens")),
    ]
    for col, (label, val) in zip(cols, stats):
        col.metric(label, val if val is not None else "—")
    st.write(f"⏳ **Total Runtime:** {fmt_runtime(state.get('total_runtime_seconds',0))}")

    # 4️⃣ per-page metadata & content -----------
    iteration   = st.session_state.iter_hist[idx]
    prompt_txt  = st.session_state.prompt_hist[idx]
    out_tokens  = st.session_state.out_tok_hist[idx]
    max_tokens  = st.session_state.max_tok_hist[idx]

    prompt_html = prompt_txt.replace("<", "&lt;").replace(">", "&gt;")
    body_html   = outputs[idx].replace("<", "&lt;").replace(">", "&gt;")

    scroll_h = BOX_HEIGHT_PX - HEADER_PX
    box_html = f"""
    <div style='background:#f9f9f9;border:1px solid #ddd;border-radius:6px;width:100%;height:{BOX_HEIGHT_PX}px;overflow:hidden;'>
      <div style='height:{HEADER_PX}px;line-height:{HEADER_PX}px;padding:0 16px;border-bottom:1px solid #ccc;font-family:Arial,sans-serif;font-size:14px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>
        <strong>Iteration:</strong> {iteration} &nbsp;|&nbsp;
        <strong>Prompt:</strong> <code style="font-size:13px;">{prompt_html}</code> &nbsp;|&nbsp;
        <strong>Tokens:</strong> {out_tokens if out_tokens is not None else 'N/A'}{(' / '+str(max_tokens)) if max_tokens is not None else ''}
      </div>
      <div style='height:{scroll_h}px;padding:12px 16px;font-family:Menlo,Consolas,"Courier New",monospace;font-size:16px;line-height:1.5;color:#1d1d1d;background:#fff;overflow-y:auto;white-space:pre-wrap;word-break:break-word;'>
        {body_html}
      </div>
    </div>"""
    st_html(box_html, height=BOX_HEIGHT_PX+8, scrolling=False)

    # 5️⃣ navigation row ---------------------------
    n1, n2, n3, n4 = st.columns([1,2,1,2])
    with n1:
        st.button("◀ Previous", key="prev", disabled=(idx==0), on_click=prev_page)
    with n2:
        st.markdown(f"**Page {st.session_state.page} of {total_pages}**")
    with n3:
        st.button("Next ▶", key="next", disabled=(idx==total_pages-1), on_click=next_page, args=(total_pages,))
    with n4:
        sel = st.selectbox("Jump", list(range(1,total_pages+1)), index=idx, key="jump")
        if sel != st.session_state.page:
            jump_to(sel)

    st.markdown("---")

    # 6️⃣ current generation details --------------
    st.subheader("🛠 Current Generation Details")
    cg1, cg2, cg3 = st.columns(3)
    cg1.code(state.get("system_prompt", "_no prompt_"), language="markdown")
    cg2.metric("Input Tokens (Curr)",  state.get("input_tokens_current", "—"))
    cg3.metric("Output Tokens (Curr)", state.get("output_tokens_current", "—"))

    st.markdown("---")

    # 7️⃣ LTM summaries ---------------------------
    st.subheader("📜 Fetched LTM Summaries")
    ltm = state.get("fetched_ltm_summaries", [])
    if ltm:
        st.markdown("\n\n".join(f"**{i+1}.**  {s.strip()}" for i, s in enumerate(ltm)))

    # 8️⃣ auto-refresh ----------------------------
    time.sleep(REFRESH_SEC)
    st.experimental_rerun()
    # 1️⃣ Load state file --------------------------------------------------
    try:
        state = json.loads(DASHBOARD_PATH.read_text())
    except FileNotFoundError:
        st.info("Waiting for dashboard_state.json …")
        time.sleep(1); st.experimental_rerun()
    except json.JSONDecodeError:
        st.warning("State file malformed — retrying …")
        time.sleep(1); st.experimental_rerun()

    # 2️⃣ Top metrics ------------------------------------------------------
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    metrics = [
        ("Iteration",             state.get("iteration")),
        ("STM Tokens",            state.get("stm_tokens")),
        ("Cost (last)",          f"${state.get('cost',0):.5f}"),
        ("Total Cost",           f"${state.get('total_cost',0):.5f}"),
        ("Total Input Tokens",    state.get("total_input_tokens")),
        ("Total Output Tokens",   state.get("total_output_tokens")),
    ]
    for col, (lbl, val) in zip((c1,c2,c3,c4,c5,c6), metrics):
        col.metric(lbl, val if val is not None else "—")
    st.write(f"⏳ **Total Runtime:** {fmt_runtime(state.get('total_runtime_seconds',0))}")

    # 3️⃣ Histories --------------------------------------------------------
    outputs      = state.get("all_outputs", [])
    iter_hist    = state.get("iteration_history", [])
    prompt_hist  = state.get("system_prompt_history", [])
    out_tok_hist = state.get("output_tokens_history", [])
    max_tok_hist = state.get("max_tokens_history", [])

    total_pages = len(outputs)
    if total_pages == 0:
        st.info("*No outputs yet…*")
        time.sleep(REFRESH_SEC); st.experimental_rerun()

    # ensure current page in range
    st.session_state.page = max(1, min(st.session_state.page, total_pages))
    idx = st.session_state.page - 1  # zero‑based index

    # page‑specific metadata (fallback to latest)
    def h(lst, fallback):
        return lst[idx] if idx < len(lst) else fallback

    iteration   = h(iter_hist,   state.get("iteration"))
    prompt_txt  = h(prompt_hist, state.get("system_prompt", ""))
    out_tokens  = h(out_tok_hist,state.get("output_tokens_current"))
    max_tokens  = h(max_tok_hist,state.get("max_tokens_current"))

    prompt_html = prompt_txt.replace("<", "&lt;").replace(">", "&gt;")
    body_html   = outputs[idx].replace("<", "&lt;").replace(">", "&gt;")

    scroll_h = BOX_HEIGHT_PX - HEADER_PX
    box_html = f"""
    <div style='background:#f9f9f9;border:1px solid #ddd;border-radius:6px;width:100%;height:{BOX_HEIGHT_PX}px;overflow:hidden;'>
      <div style='height:{HEADER_PX}px;line-height:{HEADER_PX}px;padding:0 16px;border-bottom:1px solid #ccc;font-family:Arial,sans-serif;font-size:14px;color:#333;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>
        <strong>Iteration:</strong> {iteration} &nbsp;|&nbsp;
        <strong>Prompt:</strong> <code style="font-size:13px;">{prompt_html}</code> &nbsp;|&nbsp;
        <strong>Tokens:</strong> {out_tokens if out_tokens is not None else 'N/A'}{(' / '+str(max_tokens)) if max_tokens is not None else ''}
      </div>
      <div style='height:{scroll_h}px;padding:12px 16px;font-family:Menlo,Consolas,"Courier New",monospace;font-size:16px;line-height:1.5;color:#1d1d1d;background:#fff;overflow-y:auto;white-space:pre-wrap;word-break:break-word;'>
        {body_html}
      </div>
    </div>"""

    st_html(box_html, height=BOX_HEIGHT_PX + 8, scrolling=False)

    # 4️⃣ Navigation row ---------------------------------------------------
    n1, n2, n3, n4 = st.columns([1,2,1,2])
    with n1:
        st.button("◀ Previous", key="prev_btn", disabled=(idx==0), on_click=prev_page)
    with n2:
        st.markdown(f"**Page {st.session_state.page} of {total_pages}**")
    with n3:
        st.button("Next ▶", key="next_btn", disabled=(idx==total_pages-1), on_click=next_page, args=(total_pages,))
    with n4:
        sel = st.selectbox("Jump", list(range(1,total_pages+1)), index=idx, key="jump")
        if sel != st.session_state.page:
            jump_to(sel)

    st.markdown("---")

    # 5️⃣ Current Generation Details --------------------------------------
    st.subheader("🛠 Current Generation Details")
    cur_cols = st.columns(3)
    cur_cols[0].code(state.get("system_prompt", "_no prompt_"), language="markdown")
    cur_cols[1].metric("Input Tokens (Curr)",  state.get("input_tokens_current", "—"))
    cur_cols[2].metric("Output Tokens (Curr)", state.get("output_tokens_current", "—"))

    st.markdown("---")

    # 6️⃣ Fetched LTM Summaries -------------------------------------------
    st.subheader("📜 Fetched LTM Summaries")
    ltm = state.get("fetched_ltm_summaries", [])
    if ltm:
        st.markdown("\n\n".join(f"**{i+1}.**  {s.strip()}" for i,s in enumerate(ltm)))

    # 7️⃣ Auto‑refresh ------------------------------------------------------
    time.sleep(REFRESH_SEC)
    st.experimental_rerun()

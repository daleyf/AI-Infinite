"""
main.py

Infinite loop that:
  1. Builds context via MemoryManager
  2. Calls OpenAI’s `o4-mini-high` to get next tokens
  3. Adds generated text to STM via MemoryManager
  4. Logs output to disk
  5. Sleeps briefly, then repeats
"""
# ==============================================================================
# ==============================================================================
from openai import OpenAI
client = OpenAI()
import time
from config import (
    OPENAI_API_KEY,
    INFINITE_MODEL,
    SUMMARIZE_THRESHOLD_TOKENS,
    API_CALL_SLEEP_SEC,
    INITIAL_PROMPT, 
    RAND_POOL,
    CONTINUOUS_PROMPT_POOL,
)
import random
from memory_manager import MemoryManager
from logger import log_text
import tiktoken
import sys
# ==============================================================================
# 1) init OpenAI & memory manager
# ==============================================================================
OpenAI.api_key = OPENAI_API_KEY
memory = MemoryManager()
memory.add_to_STM(INITIAL_PROMPT)
# ==============================================================================
# ==============================================================================

# ==============================================================================
# dashboard
# ==============================================================================
import json
from pathlib import Path
DASHBOARD_PATH = Path(__file__).parent / "dashboard_state.json"


def update_dashboard_state(entry):
    if DASHBOARD_PATH.exists():
        try:
            data = json.loads(DASHBOARD_PATH.read_text())
            history = data.get("all_outputs", [])
        except Exception:
            history = []
    else:
        history = []

    history.append(entry)
    with open(DASHBOARD_PATH, "w") as f:
        json.dump({"all_outputs": history}, f, indent=2)


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
# ==============================================================================
# ==============================================================================


# ==============================================================================
# ==============================================================================
def generate_next_chunk(context: str, max_tokens: int = 512, temperature: float = 0.9) -> str:
    """
    Generates the next chunk of tokens using OpenAI's Chat API (v1.0+).
    """
    response = client.chat.completions.create(
        model=INFINITE_MODEL,
        messages=[{"role": "user", "content": context}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    content = response.choices[0].message.content
    usage = response.usage  # contains input/output token counts
    return content, usage.prompt_tokens, usage.completion_tokens
# ==============================================================================
# ==============================================================================
def main_loop():
    total_start = time.time()
    """
    1. Build the current context (LTM summaries + STM_buffer)
    2. Generate the next chunk from GPT
    3. Add generated text to STM
    4. Log it
    5. Sleep a bit to respect rate limits
    6. Repeat forever
    """
    # token tracking
    TOTAL_INPUT_TOKENS = 0
    TOTAL_OUTPUT_TOKENS = 0

    # Pricing per million tokens for gpt-4.1-nano
    INPUT_COST = 0.10 / 1_000_000
    OUTPUT_COST = 0.40 / 1_000_000
    iteration = 0

    # If the dashboard file already exists from a prior run, remove it so we start fresh:
    if DASHBOARD_PATH.exists():
        DASHBOARD_PATH.unlink()

    while True:
        iter_start = time.time()

        iteration += 1
        print(f"[Iteration {iteration}]")
        if random.randint(1, 2) == 1:
            system_msg = random.choice(RAND_POOL)
            # print('\n\n****\nRandom prompt triggered:', system_msg)
            # print('****') 
        else:
            system_msg = random.choice(CONTINUOUS_PROMPT_POOL)
            # print('\n\n****\nSystem prompt:', system_msg)
            # print('****') 
           

            
      
        if iteration % 2 == 0:
            # print("📜 Top memories in LTM:")
            summaries = memory.retrieve_relevant_LTM("find something random/ unexpected from ltm", top_k=3)
            for i, summary in enumerate(summaries):
                snippet = summary.strip().replace("\n", " ")[:200]
                # print(f"  {i+1}. {snippet}...")



        # 1) Build context with system prompt BEFORE generating
        context = memory.build_context(user_prompt=system_msg)

        # 2) Generate the next chunk
        max_tokens = random.choices(
                    [128, 512, 1_024, 2_048, 32_000],
            weights=[0.5, 0.3,  0.15,  0.04,  0.01],  
            k=1
        )[0]
        # print('🧠 Max tokens allowed for next output:', max_tokens)
        context_tokens = (
            context + 
            f"\n(Note: You may use up to {max_tokens} tokens for this response. Use them all)"
        )

        # ==============================================================================
        # generation here
        # ==============================================================================
        next_text, input_tokens, output_tokens = generate_next_chunk(context_tokens + "in this iteration", max_tokens)
        # ==============================================================================

        TOTAL_INPUT_TOKENS += input_tokens
        TOTAL_OUTPUT_TOKENS += output_tokens

        # 3) Add it to STM (this allows memory compression and context chaining)
        memory.add_to_STM(next_text)

        # 4) Log to disk so we can inspect afterward
        log_text(next_text)  

        cost = (TOTAL_INPUT_TOKENS * INPUT_COST) + (TOTAL_OUTPUT_TOKENS * OUTPUT_COST)
        if cost >= 1.00:
            print(f"💸 Reached cost cap of $1.00. Stopping. Total tokens: {TOTAL_INPUT_TOKENS + TOTAL_OUTPUT_TOKENS}")
            break
        
        iteration_time = time.time() - iter_start
        total_runtime = time.time() - total_start






        # ==============================================================================
        # dashboard and logging
        # ==============================================================================
        stm_tokens = memory.STM_token_count

        # Fetch the top-3 LTM summaries (each iteration, to display in dashboard)
        fetched_ltm = memory.retrieve_relevant_LTM(
            "find something random/ unexpected from ltm", top_k=3
        )
        # ─────────────────────────────────────────────────────────────────
        # j) Build the state dict exactly matching the tracked variables
        # ─────────────────────────────────────────────────────────────────
        iteration_metadata = {
            "id": iteration,
            "text": next_text,
            "prompt": system_msg,
            "tokens": {
                "in": input_tokens,
                "out": output_tokens
            },
            "runtime_seconds": round(time.time() - iter_start, 2),
            "total_runtime_seconds": round(time.time() - total_start, 2),
            "cost": round(cost, 5)
        }

        update_dashboard_state(iteration_metadata)
        time.sleep(API_CALL_SLEEP_SEC)
        # print(f"[Iteration {iteration}] ✅ {len(next_text.split())} words | STM: {TOTAL_OUTPUT_TOKENS % SUMMARIZE_THRESHOLD_TOKENS} / {SUMMARIZE_THRESHOLD_TOKENS} | 💰 Est. cost: ${cost:.4f}")
        # print('input tokens:', input_tokens, 'total', TOTAL_INPUT_TOKENS)
        # print('output tokens:', output_tokens, 'total', TOTAL_OUTPUT_TOKENS)
        # print(f"⏱️ Iteration time: {iteration_time} sec")
        # print(f"⏳ Total runtime: {total_runtime} sec")
        # print("-")
        # print("-")
        # print("-")
        # print("=" * 40)
# ==============================================================================
# ==============================================================================
if __name__ == "__main__":
    try:
        print("🚀 Infinite GPT loop started. Press Ctrl+C to stop.")
        main_loop()
    except KeyboardInterrupt:
        print("\n⏹️  Keyboard interrupt received. Saving vector store...")
        print("👋 Goodbye!")

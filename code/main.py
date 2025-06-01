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
    DEFAULT_CONTINOUS_PROMPT,
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
# ==============================================================================
# 2) prompt
# ==============================================================================
memory.add_to_STM(INITIAL_PROMPT)
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

    while True:
        start = time.time()

        iteration += 1
        if random.randint(1, 2) == 1:
            system_msg = random.choice(RAND_POOL)
            print('\n\n****\nRandom prompt triggered:', system_msg)
            print('****')
        else:
            system_msg = DEFAULT_CONTINOUS_PROMPT

            
      
        if iteration % 2 == 0:
            print("📜 Top memories in LTM:")
            summaries = memory.retrieve_relevant_LTM("find something random/ unexpected from ltm", top_k=3)
            for i, summary in enumerate(summaries):
                snippet = summary.strip().replace("\n", " ")[:200]
                print(f"  {i+1}. {snippet}...")



        # 1) Build context with system prompt BEFORE generating
        context = memory.build_context(user_prompt=system_msg)

        # 2) Generate the next chunk
        max_tokens = random.choices(
                    [128, 512, 1_024, 2_048, 32_000],
            weights=[0.5, 0.3,  0.15,  0.04,  0.01],  
            k=1
        )[0]
        print('🧠 Max tokens allowed for next output:', max_tokens)
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
        print(f"[Iteration {iteration}] ✅ {len(next_text.split())} words | STM: {TOTAL_OUTPUT_TOKENS % SUMMARIZE_THRESHOLD_TOKENS} / {SUMMARIZE_THRESHOLD_TOKENS} | 💰 Est. cost: ${cost:.4f}")
        print('input tokens:', input_tokens, 'total', TOTAL_INPUT_TOKENS)
        print('output tokens:', output_tokens, 'total', TOTAL_OUTPUT_TOKENS)
        end = time.time()
        print(f"⏱️ Iteration time: {end - start:.2f} sec")
        total_end = time.time()  # ← End total timer
        duration = total_end - total_start
        mins, secs = divmod(duration, 60)
        print(f"⏳ Total runtime: {int(mins)} min {int(secs)} sec")
        print("-")
        print("-")
        print("-")
        print("=" * 40)
        # 5) Sleep to avoid hitting rate limits
        time.sleep(API_CALL_SLEEP_SEC)
# ==============================================================================
# ==============================================================================
if __name__ == "__main__":
    try:
        print("🚀 Infinite GPT loop started. Press Ctrl+C to stop.")
        total_start = time.time()  # ← Start total timer
        main_loop()
    except KeyboardInterrupt:
        print("\n⏹️  Keyboard interrupt received. Saving vector store...")
        print("👋 Goodbye!")

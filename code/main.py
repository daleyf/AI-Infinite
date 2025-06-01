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
    API_CALL_SLEEP_SEC
)
import random
from memory_manager import MemoryManager
from logger import log_text
import tiktoken
# ==============================================================================
# 1) init OpenAI & memory manager
# ==============================================================================
OpenAI.api_key = OPENAI_API_KEY
memory = MemoryManager()
# ==============================================================================
# 2) prompt
# ==============================================================================
INITIAL_PROMPT = "Hi, you are artificial general intelligence. You are prompted continously and with recursivley become AGI."
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
    prompt_pool = [
        "Disagree with your last idea.",
        "Play devil's advocate to what you just wrote.",
        "Ask yourself a hard question and try to answer it.",
        "Shift to a different domain: biology, psychology, ethics.",
        "Describe a fictional world where AGI already exists.",
        "Write a memory or a dream of an AGI being trained."
    ]

    while True:
        iteration += 1
        if random.randint(1, 5) == 1:
            system_msg = random.choice(prompt_pool)
        else:
            system_msg = (
                "Continue your train of thought from the last message. "
                "Do not repeat ideas exactly. Build forward. Ask new questions, propose ideas, or simulate thought."
            )

        # 1) Build context with system prompt BEFORE generating
        context = memory.build_context(user_prompt=system_msg)

        # 2) Generate the next chunk
        next_text, input_tokens, output_tokens = generate_next_chunk(context)
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
        print(f"[{iteration}] ✅ {len(next_text.split())} words | 💰 Est. cost: ${cost:.4f}")
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
        main_loop()
    except KeyboardInterrupt:
        print("\n⏹️  Keyboard interrupt received. Saving vector store...")
        print("👋 Goodbye!")

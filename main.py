"""
main.py

Infinite loop that:
  1. Builds context via MemoryManager
  2. Calls OpenAI’s `o4-mini-high` to get next tokens
  3. Adds generated text to STM via MemoryManager
  4. Logs output to disk
  5. Sleeps briefly, then repeats
"""

import openai
import time
from config import (
    OPENAI_API_KEY,
    LLM_MODEL,
    API_CALL_SLEEP_SEC
)
from memory_manager import MemoryManager
from logger import log_text

# ------------------------------------------------------------------------------
# 1) Initialize OpenAI client & memory manager
# ------------------------------------------------------------------------------
openai.api_key = OPENAI_API_KEY
memory = MemoryManager()

# ------------------------------------------------------------------------------
# 2) Starting prompt
# ------------------------------------------------------------------------------
INITIAL_PROMPT = "Hi, you are artificial general intelligence."

# Add the initial prompt to STM right away:
memory.add_to_STM(INITIAL_PROMPT)

def generate_next_chunk(context: str, max_tokens: int = 512, temperature: float = 0.9) -> str:
    """
    generate_next_chunk(context, max_tokens, temperature) -> str

    Call the LLM to predict the next `max_tokens` tokens given `context`.
    Returns the raw text generated (without role prefixes).
    """
    response = openai.ChatCompletion.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": context}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content

def main_loop():
    """
    main_loop() -> None

    1. Build the current context (LTM summaries + STM_buffer)
    2. Generate the next chunk from GPT
    3. Add generated text to STM
    4. Log it
    5. Sleep a bit to respect rate limits
    6. Repeat forever
    """
    iteration = 0
    while True:
        iteration += 1
        # 1) Build the context for this iteration
        context = memory.build_context(user_prompt=None)

        # 2) Generate the next chunk
        next_text = generate_next_chunk(context)

        # 3) Add generated text to STM (this may trigger summarization if STM is too big)
        memory.add_to_STM(next_text)

        # 4) Log to disk so we can inspect afterward
        log_text(next_text)

        print(f"[Iteration {iteration}] Generated {len(next_text)} characters, {len(next_text.split())} words.")

        # 5) Sleep to avoid hitting rate limits
        time.sleep(API_CALL_SLEEP_SEC)

if __name__ == "__main__":
    try:
        print("🚀 Starting infinite GPT loop. Press Ctrl+C to stop.")
        main_loop()
    except KeyboardInterrupt:
        print("\n⏹️  Stopping loop. Persisting vector store to disk...")
        # If using Chroma, do:
        from vector_store import persist_vector_store
        persist_vector_store()
        print("✅ Vector store saved. Goodbye!")

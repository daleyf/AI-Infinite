"""
config.py

All tunable hyperparameters and paths for the Infinite-LLM-Loop project.
"""

import os
from dotenv import load_dotenv

# If a .env file is present, load it:
load_dotenv()

# ------------------------------------------------------------------------------
# 1) OPENAI CONFIGURATION
# ------------------------------------------------------------------------------
# (Best practice: store your API key in the environment, not in code)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment.")

# Model to use for generation and summarization:
LLM_MODEL = "o4-mini-high"

# ------------------------------------------------------------------------------
# 2) TOKEN COUNTERS FOR MEMORY MANAGEMENT
# ------------------------------------------------------------------------------
# How many tokens can our LLM context window hold?
# (Adjust based on the model’s max tokens; o4-mini-high supports ~64k, but we will be conservative.)
CONTEXT_WINDOW_TOKENS = 32_000

# When STM (short-term memory) exceeds this number of tokens, trigger summarization:
SUMMARIZE_THRESHOLD_TOKENS = 12_000

# Group size to summarize at once (we’ll summarize old STM in chunks of this size):
MEMORY_CHUNK_TOKENS = 8_000

# ------------------------------------------------------------------------------
# 3) CHROMA VECTOR STORE CONFIGURATION
# ------------------------------------------------------------------------------
# Where on disk should Chroma store embeddings?
# If not specified, defaults to "./chromadb_data"
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chromadb_data")

# ------------------------------------------------------------------------------
# 4) LOGGING & OUTPUT PATHS
# ------------------------------------------------------------------------------
# Where to store continuous logs of GPT’s “stream”:
LOG_DIR = "./logs"
STREAM_LOG_FILE = os.path.join(LOG_DIR, "stream.txt")

# ------------------------------------------------------------------------------
# 5) OTHER SETTINGS
# ------------------------------------------------------------------------------
# How often (in seconds) to pause between API calls?
# You might want a small sleep to avoid rate limits or to control cost.
API_CALL_SLEEP_SEC = 0.5

# ------------------------------------------------------------------------------
# 6) SAFETY & BEST PRACTICES
# ------------------------------------------------------------------------------
# If you need to override for testing or have multiple agents, load from env.
# Always keep your API key private. Do NOT push it to version control!

"""
config.py

All tunable hyperparameters and paths for the Infinite-LLM-Loop project.
"""

import os
from dotenv import load_dotenv

# If a .env file is present, load it:
load_dotenv()

# ==============================================================================
# 1) OPENAI 
# ==============================================================================
# key stuff
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", None)
if not OPENAI_API_KEY:
    raise ValueError("Missing OPENAI_API_KEY in environment.")

# models
INFINITE_MODEL = "gpt-4.1-nano"
SUMMARY_MODEL = "gpt-4.1-nano"
# ==============================================================================
# ==============================================================================


# ==============================================================================
# 2) TOKEN COUNTERS FOR MEMORY MANAGEMENT
# ==============================================================================
# How many tokens can our LLM context window hold?
CONTEXT_WINDOW_TOKENS = 32_000

# stm
SUMMARIZE_THRESHOLD_TOKENS = 1_100
# much much summaries to hold from the og size in stm
MEMORY_CHUNK_TOKENS = SUMMARIZE_THRESHOLD_TOKENS // 2
# ==============================================================================
# ==============================================================================


# ==============================================================================
# 3) CHROMA VECTOR STORE CONFIGURATION
# ==============================================================================
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chromadb_data")
# ==============================================================================
# ==============================================================================


# ==============================================================================
# 4) LOGGING & OUTPUT PATHS
# ==============================================================================
LOG_DIR = "./logs"
STREAM_LOG_FILE = os.path.join(LOG_DIR, "stream.txt")
# ==============================================================================
# ==============================================================================


# ==============================================================================
# 5) OTHER SETTINGS
# ==============================================================================
API_CALL_SLEEP_SEC = 0.01
# ==============================================================================
# ==============================================================================

# ==============================================================================
# prompts
# ==============================================================================
INITIAL_PROMPT = (
    "You are an AI strategist tasked with helping Daley Fraser, a 21-year-old Google SWE intern, figure out how to get rich. "
    "Daley is ambitious, technically sharp, and torn between pursuing a high-paying job in big tech or building a startup. "
    "Your job is to explore actionable, scalable paths to wealth that align with his skills, values, and long-term goals."
)

RAND_POOL = [
    "You are STUCK in the same loop. THINK OUTSIDE THE BOX ON THIS ONE",
    "What are 3 overlooked ways to get rich in tech?",
    "Act as a startup mentor. What would you advise Daley to build?",
    "What would Naval Ravikant say to someone like Daley Fraser?",
    "Play devil’s advocate: why might working at OpenAI or Google not make Daley rich?",
    "How could Daley use AI to build a passive income engine?",
    "Compare: big tech career vs. lean startup vs. content empire.",
    "Daley has 5 years. What's the fastest, non-scammy way to $10M?",
    "Which tech niches are most likely to explode by 2027?",
    "What would a no-regret move be for someone in Daley’s shoes?",
    "What underappreciated skills compound wealth the fastest?",
    "Assume Daley fails twice. How does he still win in the end?",
    "What role could publishing research or building tools play?",
    "Could Daley get rich without being a founder or influencer?",
    "Which successful people have a similar background to Daley?",
    "If Daley went all-in on a startup, what should he build?"
]

DEFAULT_CONTINOUS_PROMPT = (
    "Continue generating ideas, frameworks, or insights for how Daley Fraser — a 21-year-old Google SWE intern — can become financially free. "
    "He is deciding between big tech, startups, and building solo products. He values impact, autonomy, and long-term leverage. "
    "Expand on the previous idea or pivot to something new. Be practical but bold. Use real-world reasoning and reference successful paths."
)

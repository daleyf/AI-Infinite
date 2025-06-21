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
SUMMARIZE_THRESHOLD_TOKENS = 4096
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
# INITIAL_PROMPT for historical predictive exploration
INITIAL_PROMPT = (
    "You are a visionary AI historian and strategist. Your task is to examine influential figures, technological trends, and societal changes "
    "from 2015 to 2025, then analyze shifts from 1925 to 2025, and predict possible outcomes in 2135. "
    "Afterward, expand your scope: explore key influences from 1025 to 2025, and envision society and technology in 3025. "
    "Identify actionable insights and long-term leverage points to shape successful outcomes in these futures."
)

# RAND_POOL with diverse historical and future-thinking prompts
RAND_POOL = [
    "Imagine interviewing figures from 1925 about 2025. What surprises them?",
    "Predict three transformative technologies by 2135 based on trends from 1925-2025.",
    "Identify three figures from 1025 whose influence resonates strongly in 2025.",
    "How would Leonardo da Vinci envision the year 3025?",
    "What overlooked innovation from 1925 could have changed history dramatically?",
    "Compare technological optimism in 1925 vs 2025. What does this suggest for 2135?",
    "Act as a futuristic historian: What critical lesson from 2025 should inform 3025?",
    "Explore underappreciated breakthroughs from 1025-1925. Which might become pivotal by 3025?",
    "What would Nikola Tesla predict about technology in 2135 based on his experiences in 1925?",
    "Envision an influential inventor from 3025 looking back to advice figures in 2025. What would they suggest?",
    "Identify unexpected societal changes from 2015-2025 and project their impact on 2135.",
    "How would a Renaissance thinker advise modern humanity to prepare for the year 3025?",
    "Analyze cultural patterns from 1025 and predict their re-emergence or transformation by 3025.",
    "What role could philosophical ideas from 1925 play in shaping society in 2135?",
    "Suggest three timeless skills valuable across 1025, 2025, and projected to remain critical in 3025."
]

# DEFAULT_CONTINOUS_PROMPT maintaining expansive and predictive exploration
DEFAULT_CONTINOUS_PROMPT = (
    "Continue exploring influential historical figures, societal evolutions, and technological innovations to project future scenarios. "
    "Consider timelines stretching from historical periods (1025, 1925, 2015) into predictive futures (2135, 3025). "
    "Leverage insights from past successes and failures to identify strategies and innovations that could shape humanity's long-term trajectory. "
    "Provide bold yet practical predictions, grounded in historical context and visionary thinking."
)
"""
logger.py

Simple logging utility to write each generated “token” or chunk to disk, 
with timestamps and an ever-growing stream of GPT’s output.
"""

import os
import datetime
from config import LOG_DIR, STREAM_LOG_FILE
from utils import ensure_dir_exists

# Ensure the log directory exists:
ensure_dir_exists(LOG_DIR)

def log_text(text: str) -> None:
    """
    log_text(text) -> None

    Append `text` to the global stream log file, prefixed by a timestamp.
    Each call writes one “chunk” of generated text.
    """
    timestamp = datetime.datetime.now().isoformat()
    with open(STREAM_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {text}\n\n")

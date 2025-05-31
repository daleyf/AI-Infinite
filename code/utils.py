"""
utils.py

Helper functions, especially for token counting using tiktoken.
"""

import tiktoken
from config import LLM_MODEL

# ------------------------------------------------------------------------------
# 1) Load the tiktoken encoding for our chosen model
# ------------------------------------------------------------------------------
try:
    ENCODER = tiktoken.encoding_for_model(LLM_MODEL)
except KeyError:
    # If the model name isn’t recognized, fall back to a default, e.g., "gpt-3.5-turbo"
    ENCODER = tiktoken.get_encoding("cl100k_base")

def count_tokens(text: str) -> int:
    """
    count_tokens(text) -> int

    Count how many tokens `text` uses for the chosen LLM model.

    Example:
        >>> count_tokens("Hello, world!")
        3
    """
    return len(ENCODER.encode(text))

def chunk_text_by_tokens(text: str, max_tokens: int) -> list[str]:
    """
    chunk_text_by_tokens(text, max_tokens) -> List of text shards

    Split `text` into chunks, each no more than `max_tokens` tokens when encoded.
    This helps when you need to summarize or embed text in parts.
    """
    tokens = ENCODER.encode(text)
    chunks = []
    start = 0
    while start < len(tokens):
        end = min(start + max_tokens, len(tokens))
        piece_tokens = tokens[start:end]
        chunks.append(ENCODER.decode(piece_tokens))
        start = end
    return chunks

def ensure_dir_exists(path: str) -> None:
    """
    ensure_dir_exists(path) -> None

    Create the directory `path` if it doesn't already exist.
    """
    import os
    if not os.path.isdir(path):
        os.makedirs(path, exist_ok=True)

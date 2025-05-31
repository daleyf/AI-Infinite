"""
memory_manager.py

Handles separation of Short-Term Memory (STM) vs. Long-Term Memory (LTM), summarization,
and retrieval so that the never-ending GPT loop remains coherent over time.
"""

import time
import uuid
import openai
from typing import List
from config import (
    CONTEXT_WINDOW_TOKENS,
    SUMMARIZE_THRESHOLD_TOKENS,
    MEMORY_CHUNK_TOKENS,
    OPENAI_API_KEY
)
from utils import count_tokens
from summarizer import summarize_text
from vector_store import add_memory_chunk, query_similar_memory

# Initialize OpenAI
openai.api_key = OPENAI_API_KEY

class MemoryManager:
    """
    MemoryManager orchestrates:
      - a short-term buffer (STM_buffer: List[str])
      - periodically summarizing old STM into LTM
      - querying LTM for relevant memory given a “query”
    """

    def __init__(self):
        # STM will store recent lines of generated text (each element is a string)
        self.STM_buffer: List[str] = []
        # Track token count of STM
        self.STM_token_count = 0

        # We keep a chronological list of summaries in LTM—embedding is stored via Chroma.
        # Optionally, keep metadata if desired.
        self.LTM_index = []  # list of (chunk_id, summary_text)

    def add_to_STM(self, text: str) -> None:
        """
        add_to_STM(text) -> None

        Add newly generated text into the short-term buffer and update token count.
        If STM exceeds SUMMARIZE_THRESHOLD_TOKENS, “compress” the oldest chunk into LTM.
        """
        tokens = count_tokens(text)
        self.STM_buffer.append(text)
        self.STM_token_count += tokens

        # If we exceed our STM threshold, compress oldest chunk(s)
        if self.STM_token_count > SUMMARIZE_THRESHOLD_TOKENS:
            self._compress_oldest()

    def _compress_oldest(self) -> None:
        """
        _compress_oldest() -> None

        When STM becomes too large, pop off roughly MEMORY_CHUNK_TOKENS worth of tokens
        from the *start* of STM_buffer, summarize that chunk, store it in LTM, and delete them from STM.
        """
        # 1) Gather text until we have ~MEMORY_CHUNK_TOKENS tokens
        collected_text = ""
        collected_tokens = 0
        pieces_to_remove = 0

        for idx, piece in enumerate(self.STM_buffer):
            piece_tokens = count_tokens(piece)
            if collected_tokens + piece_tokens > MEMORY_CHUNK_TOKENS:
                break
            collected_text += piece + "\n"
            collected_tokens += piece_tokens
            pieces_to_remove += 1

        if pieces_to_remove == 0:
            # In case a single piece exceeds MEMORY_CHUNK_TOKENS (rare),
            # just summarize that one piece.
            collected_text = self.STM_buffer[0]
            collected_tokens = count_tokens(collected_text)
            pieces_to_remove = 1

        # 2) Create a summary
        summary = summarize_text(collected_text)

        # 3) Create a unique chunk ID (e.g., timestamp + uuid)
        chunk_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        # 4) Add summary to LTM (Chroma) via embedding
        add_memory_chunk(chunk_id, summary)
        self.LTM_index.append((chunk_id, summary))

        # 5) Remove those pieces from STM_buffer and adjust token count
        for _ in range(pieces_to_remove):
            removed = self.STM_buffer.pop(0)
            self.STM_token_count -= count_tokens(removed)

    def retrieve_relevant_LTM(self, query_text: str, top_k: int = 3) -> List[str]:
        """
        retrieve_relevant_LTM(query_text, top_k) -> List of summary_text

        Looks up similar memory chunks in LTM based on `query_text`,
        returns their summary_texts so we can inject them into context.
        """
        if not self.LTM_index:
            return []

        results = query_similar_memory(query_text, top_k=top_k)
        return [r["document"] for r in results]

    def build_context(self, user_prompt: str = None) -> str:
        """
        build_context(user_prompt=None) -> str

        Compose:
          1. A small prompt (optional) reminding the LLM who it is.
          2. The top K relevant LTM summaries for semantic recall.
          3. The entire STM_buffer (last few thousand tokens).

        Always ensure total tokens <= CONTEXT_WINDOW_TOKENS by truncation if needed.
        """
        # 1) Start with a “system prompt” or user prompt if provided:
        context_parts = []
        if user_prompt:
            context_parts.append(user_prompt)

        # 2) Retrieve relevant LTM based on the last few lines in STM_buffer
        #    We can join last N pieces to form a “query.” Simpler: query using the most recent piece.
        if self.STM_buffer:
            query = self.STM_buffer[-1]
            relevant_summaries = self.retrieve_relevant_LTM(query, top_k=3)
            context_parts.extend(relevant_summaries)

        # 3) Append the entire STM_buffer (chronological)
        context_parts.extend(self.STM_buffer)

        # 4) Join and ensure we don’t exceed CONTEXT_WINDOW_TOKENS
        full_context = "\n".join(context_parts)
        # If it’s too large, we can truncate from the front until it fits:
        while count_tokens(full_context) > CONTEXT_WINDOW_TOKENS:
            # Drop the earliest element in STM_buffer, rebuild:
            if self.STM_buffer:
                dropped = self.STM_buffer.pop(0)
                self.STM_token_count -= count_tokens(dropped)
                context_parts = []
                if user_prompt:
                    context_parts.append(user_prompt)
                if self.STM_buffer:
                    new_query = self.STM_buffer[-1]
                    new_relevant = self.retrieve_relevant_LTM(new_query, top_k=3)
                    context_parts.extend(new_relevant)
                context_parts.extend(self.STM_buffer)
                full_context = "\n".join(context_parts)
            else:
                # If STM is empty but still too big, force a final truncate on full_context string
                tokens = full_context.split()  # crude: split on whitespace
                truncated = " ".join(tokens[-CONTEXT_WINDOW_TOKENS:])
                full_context = truncated
                break

        return full_context

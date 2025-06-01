"""
memory_manager.py

Handles separation of Short-Term Memory (STM) vs. Long-Term Memory (LTM), summarization,
and retrieval so that the never-ending GPT loop remains coherent over time.
"""

import time
import uuid
from openai import OpenAI
from typing import List
from config import (
    CONTEXT_WINDOW_TOKENS,
    SUMMARIZE_THRESHOLD_TOKENS,
    MEMORY_CHUNK_TOKENS,
    OPENAI_API_KEY
)
from utils import count_tokens
from summarizer import summarize_text
from vector_store import add_to_vector_store as add_memory_chunk
from vector_store import retrieve_similar_memories as query_similar_memory


# Initialize OpenAI
OpenAI.api_key = OPENAI_API_KEY

class MemoryManager:
    """
      - a short-term buffer (STM_buffer: List[str])
      - periodically summarizing old STM into LTM
      - querying LTM for relevant memory given a “query”
    """
    # ==============================================================================
    # ==============================================================================
    def __init__(self):
        self.STM_buffer: List[str] = []  # stores current chats
        self.STM_token_count = 0
        self.LTM_index = []  # list of (chunk_id, summary_text)
    # ==============================================================================
    # ==============================================================================
    def add_to_STM(self, text: str) -> None:
        """
        add_to_STM(text) -> None

        Add newly generated text into the short-term buffer and update token count.
        If STM exceeds SUMMARIZE_THRESHOLD_TOKENS, “compress” the oldest chunk into LTM.
        """
        tokens = count_tokens(text)
        self.STM_buffer.append(text)
        self.STM_token_count += tokens

        # exceed STM threshold, move STM --> summarize into LT
        if self.STM_token_count > SUMMARIZE_THRESHOLD_TOKENS:
            print('\n\n****\nSTM token reached, moving to LTM\n****\n\n')
            self._compress_oldest()
    # ==============================================================================
    # ==============================================================================
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
        summary = summarize_text(collected_text)  # imported function from summarizer.py

        # 3) Create a unique chunk ID (e.g., timestamp + uuid)
        chunk_id = f"{int(time.time())}_{uuid.uuid4().hex[:8]}"
        # 4) Add summary to LTM (Chroma) via embedding
        add_memory_chunk(text=summary, metadata={"chunk_id": chunk_id})
        self.LTM_index.append((chunk_id, summary))

        # 5) Remove those pieces from STM_buffer and adjust token count
        for _ in range(pieces_to_remove):
            removed = self.STM_buffer.pop(0)
            self.STM_token_count -= count_tokens(removed)
    # ==============================================================================
    # ==============================================================================
    def retrieve_relevant_LTM(self, query_text: str, top_k: int = 3):
        results = query_similar_memory(query_text, k=top_k)
        return results["documents"][0]  # returns a list of top-k document texts
    # ==============================================================================
    # ==============================================================================
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

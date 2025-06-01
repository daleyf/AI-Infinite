"""
summarizer.py

Functions to compress large text into a concise “memory chunk” using GPT.
"""

from openai import OpenAI
client = OpenAI()
from config import SUMMARY_MODEL, OPENAI_API_KEY
from utils import count_tokens, chunk_text_by_tokens

# Initialize the OpenAI client
OpenAI.api_key = OPENAI_API_KEY

def summarize_text(text: str, max_tokens: int = 512) -> str:
    """
    summarize_text(text, max_tokens) -> str

    Summarize `text` into a short, cohesive paragraph that captures the gist.
    - We break `text` into smaller chunks if it exceeds the model’s input limit.
    - Then we summarize each chunk and combine.

    Args:
      text: Original long text to compress.
      max_tokens: The maximum length of the summary output.

    Returns:
      A string that is the approximate summary of `text`.
    """

    # ==============================================================================
    # PART 1: small enough to just summarize directly
    # ==============================================================================
    if count_tokens(text) < 6_000:  # choose a threshold comfortably under the model’s input limit
        prompt = f"Please provide a concise summary (1–2 paragraphs) of the following text:\n\n{text}"
        response = client.chat.completions.create(
            model=SUMMARY_MODEL,  # or whatever summarization model you're using
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content.strip()

    # ==============================================================================
    # PART 2: break into sub-chunks, summarize each, then concatenate and re-summarize:
    # ==============================================================================
    chunks = chunk_text_by_tokens(text, max_tokens=4_000)
    partial_summaries = []
    for i, c in enumerate(chunks):
        prompt_chunk = (
            f"Chunk {i+1}/{len(chunks)}: "
            "Summarize the following text into 1 paragraph:\n\n" + c
        )
        resp = client.chat.completions.create(
            model=SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt_chunk}],
            temperature=0.3,
            max_tokens=max_tokens // len(chunks)
        )
        partial_summaries.append(resp.choices[0].message.content.strip())

    # Combine partial summaries into one final summary
    combined = "\n\n".join(partial_summaries)
    final_prompt = (
        "The following are partial summaries of a longer document. "
        "Please combine them into a single, concise summary:\n\n" + combined
    )
    final_resp = client.chat.completions.create(
        model=SUMMARY_MODEL,
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.3,
        max_tokens=max_tokens
    )
    return final_resp.choices[0].message.content.strip()

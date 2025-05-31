# AI-Infinite

> A “infinite” LLM loop that never stops.  
> Continuously generates tokens from an initial prompt, while managing both short-term and long-term memory.

---

## Overview

This project demonstrates how to:
1. Continuously feed LLM its own output (a never-ending “self-completion” loop).
2. Keep only the last X tokens in-⁠RAM to respect LLM’s context window.
3. Compress older text into “long-term memory” via summarization and store embeddings in a local Chroma DB.
4. Retrieve relevant memory as needed to keep the loop coherent over time.

---

## Quick Start

1. Clone this repo
2. Init OpenAI env in terminal:
```export OPENAI_API_KEY= "YOUR_API_KEY"```
3. Run main.py


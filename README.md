# AI-Infinite

> A “dreaming” GPT loop that never stops.  
> Continuously generates tokens from an initial AGI prompt, while managing both short-term and long-term memory.

---

## 📋 Overview

This project demonstrates how to:
1. **Continuously feed GPT** its own output (a never-ending “self-completion” loop).
2. **Keep only the last X tokens** in-⁠RAM to respect GPT’s context window.
3. **Compress older text** into “long-term memory” via summarization and store embeddings in a local Chroma DB.
4. **Retrieve relevant memory** as needed to keep the loop coherent over time.

---

## 🚀 Quick Start

1. **Clone or download** this repo:

   ```bash
   git clone https://github.com/your-username/infinite_llm_loop.git
   cd infinite_llm_loop


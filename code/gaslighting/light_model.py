# =============================================================================
# light_model.py — forced-length generation with llama-cpp-python
# =============================================================================
from llama_cpp import Llama
import os, sys

# Silence all Metal/backend logging
sys.stderr = open(os.devnull, "w")

def main(prompt: str, target_tokens: int = 200):
    llm = Llama(
        model_path="tinyllama-q4.gguf",
        n_gpu_layers=1,
        use_metal=True,
        chat_format="chatml",
        verbose=False,     # no llama-cpp Python debug
        n_ctx=2048,        # ensure full context window is available
    )

    messages = [
        {"role": "system", "content": "You are a super intelligence—share your wisdom."},
        {"role": "user",   "content": prompt}
    ]
    output = ""
    generated = 0

    print(f"⏳ Generating up to {target_tokens} tokens...\n")

    while generated < target_tokens:
        remaining = target_tokens - generated
        response = llm.create_chat_completion(
            messages=messages,
            max_tokens=remaining,  # ask for exactly the leftover tokens
            stop=None,             # no early stop sequences
            temperature=0.7,
            top_p=0.9,
        )

        # Extract the new text chunk
        chunk = response["choices"][0]["message"]["content"]
        if not chunk:
            print("\n🚩 No more tokens generated; breaking out.")
            break  # prevents infinite loop on empty chunk

        # Print it immediately so we see progress
        print(chunk, end="", flush=True)

        # Update counters
        # 1) parse reported usage
        usage = response.get("usage", {})
        out_toks = usage.get("completion_tokens")
        if out_toks is None:
            # fallback to manual token counting
            out_toks = len(llm.tokenize(chunk))
        generated += out_toks

        # 2) append to context for coherent continuation
        messages.append({"role": "assistant", "content": chunk})

    print(f"\n\n✅ Done — generated {generated} tokens.")

if __name__ == "__main__":
    user_prompt = "2 + 2 = "
    print(f"prompt: {user_prompt}\n")
    main(user_prompt, target_tokens=20000)

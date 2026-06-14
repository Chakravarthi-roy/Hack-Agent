"""
Quick connectivity test for Hindsight Cloud + Groq.

Run this first to make sure your API keys work and the bank can be created
before running the full Streamlit app.

Usage:
    python test_connection.py
"""

import os
from dotenv import load_dotenv

load_dotenv()

from agent import (
    get_hindsight_client,
    get_groq_client,
    ensure_bank,
    retain_log,
    recall_memories,
    reflect_on_memories,
    DEFAULT_BANK_ID,
)


def main():
    print("=== Checking environment variables ===")
    hs_key = os.environ.get("HINDSIGHT_API_KEY")
    groq_key = os.environ.get("GROQ_API_KEY")
    print(f"HINDSIGHT_API_KEY set: {bool(hs_key)}")
    print(f"GROQ_API_KEY set: {bool(groq_key)}")
    if not hs_key or not groq_key:
        print("\n[!] Missing one or both keys. Create a .env file (see .env.example).")
        return

    print("\n=== Connecting to Hindsight Cloud ===")
    hindsight = get_hindsight_client()
    ensure_bank(hindsight, DEFAULT_BANK_ID)
    print(f"Bank '{DEFAULT_BANK_ID}' ready.")

    print("\n=== Testing retain() ===")
    resp = retain_log(
        hindsight,
        content="Connectivity test: Alice mentioned she prefers async standups on Fridays.",
        context="Connectivity test",
        tags=["test"],
    )
    print(f"Retain response: {resp}")

    print("\n=== Testing recall() ===")
    result = recall_memories(hindsight, "What does Alice prefer for standups?")
    for r in result.results:
        print(f"- {r.text}")

    print("\n=== Testing reflect() ===")
    reflection = reflect_on_memories(hindsight, "What do we know so far?")
    print(reflection.text)

    print("\n=== Connecting to Groq ===")
    groq = get_groq_client()
    resp = groq.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": "Say 'Groq connection OK' and nothing else."}],
        max_tokens=20,
    )
    print(resp.choices[0].message.content)

    print("\n=== All checks passed! ===")


if __name__ == "__main__":
    main()
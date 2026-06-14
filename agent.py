"""
Core agent logic: wraps Hindsight (memory) and Groq (LLM reasoning).

Design:
- One Hindsight bank per "product" (bank_id = e.g. "pm-fintrack").
- retain() is called whenever the PM logs a note (standup, stakeholder call, feedback).
- recall() is used for direct factual lookups ("what did Priya ask for?").
- reflect() is used for synthesis questions ("what risks should I flag this week?").
- Groq LLM is used to (a) classify whether a question needs recall vs reflect,
  and (b) produce the final user-facing answer using the memory context Hindsight returns.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from hindsight_client import Hindsight
from groq import Groq


HINDSIGHT_BASE_URL = "https://api.hindsight.vectorize.io"
DEFAULT_BANK_ID = "pm-fintrack-demo"
GROQ_MODEL = "openai/gpt-oss-120b"

# hindsight_client's sync methods internally call loop.run_until_complete().
# In environments that already have a running/cached event loop (e.g. Streamlit),
# this raises "Timeout context manager should be used inside a task". Running each
# Hindsight call in its own thread gives it a fresh event loop and avoids the clash.
_executor = ThreadPoolExecutor(max_workers=4)


def _run_isolated(fn, *args, **kwargs):
    """Run a sync hindsight_client call in a separate thread with its own event loop."""
    future = _executor.submit(fn, *args, **kwargs)
    return future.result()


def get_hindsight_client() -> Hindsight:
    api_key = os.environ.get("HINDSIGHT_API_KEY")
    return Hindsight(base_url=HINDSIGHT_BASE_URL, api_key=api_key)


def get_groq_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=api_key)


def ensure_bank(client: Hindsight, bank_id: str = DEFAULT_BANK_ID):
    """Create the memory bank if it doesn't exist yet (idempotent-ish)."""
    try:
        _run_isolated(
            client.create_bank,
            bank_id=bank_id,
            name="FinTrack PM Memory",
            mission=(
                "Track product decisions, risks, stakeholder requests, and user "
                "feedback for the FinTrack product so the PM can recall context "
                "and spot recurring issues over time."
            ),
            background=(
                "FinTrack is a personal budgeting app. The user of this bank is "
                "the Product Manager. Key people: Marcus (Engineering Lead), "
                "Lena (Designer), Priya (Head of Product, stakeholder), David "
                "(Sales VP, stakeholder)."
            ),
        )
    except Exception:
        # Bank likely already exists - safe to ignore for demo purposes
        pass


def retain_log(client: Hindsight, content: str, context: str, tags: list[str],
                timestamp=None, bank_id: str = DEFAULT_BANK_ID):
    return _run_isolated(
        client.retain,
        bank_id=bank_id,
        content=content,
        context=context,
        tags=tags,
        timestamp=timestamp,
    )


def recall_memories(client: Hindsight, query: str, bank_id: str = DEFAULT_BANK_ID, max_tokens=2048):
    return _run_isolated(client.recall, bank_id=bank_id, query=query, max_tokens=max_tokens)


def reflect_on_memories(client: Hindsight, query: str, bank_id: str = DEFAULT_BANK_ID):
    return _run_isolated(client.reflect, bank_id=bank_id, query=query, budget="mid")


def classify_query(groq_client: Groq, question: str) -> str:
    """
    Use Groq to decide whether a question needs:
    - 'recall' : a direct factual lookup ("what did X say", "when did Y happen")
    - 'reflect': synthesis/reasoning across multiple memories ("what risks should I flag",
                  "what patterns have come up", "what should I prioritize")
    """
    prompt = (
        "Classify the following Product Manager question into exactly one word: "
        "'recall' or 'reflect'.\n\n"
        "'recall' = the question asks for a specific fact, event, or past statement "
        "(who said what, when something happened, status of a specific item).\n"
        "'reflect' = the question asks for synthesis, patterns, risks, recommendations, "
        "or reasoning across multiple pieces of information.\n\n"
        f"Question: {question}\n\n"
        "Answer with only one word: recall or reflect."
    )
    resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=10,
    )
    answer = resp.choices[0].message.content.strip().lower()
    return "reflect" if "reflect" in answer else "recall"


def answer_question(hindsight_client: Hindsight, groq_client: Groq, question: str,
                     bank_id: str = DEFAULT_BANK_ID):
    """
    Full pipeline: classify -> hindsight recall/reflect -> Groq final answer.
    Returns (mode_used, memory_context_text, final_answer_text)
    """
    mode = classify_query(groq_client, question)

    if mode == "reflect":
        result = reflect_on_memories(hindsight_client, question, bank_id=bank_id)
        memory_context = result.text if hasattr(result, "text") else str(result)
        # Reflect already produces a reasoned answer - lightly polish with Groq
        final_prompt = (
            "You are an AI assistant helping a Product Manager. Hindsight's memory "
            "system has already reasoned over past notes and produced this answer:\n\n"
            f"{memory_context}\n\n"
            f"Original question: {question}\n\n"
            "Present this to the PM in a clear, concise way (use bullet points if "
            "listing multiple items). Do not invent new facts beyond what's given."
        )
    else:
        result = recall_memories(hindsight_client, question, bank_id=bank_id)
        memory_context = "\n".join(f"- {r.text}" for r in result.results) if hasattr(result, "results") else str(result)
        final_prompt = (
            "You are an AI assistant helping a Product Manager. Here are relevant "
            "memories retrieved from past notes:\n\n"
            f"{memory_context}\n\n"
            f"Question: {question}\n\n"
            "Answer the question directly using only the information above. If the "
            "memories don't contain a clear answer, say so."
        )

    final_resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": final_prompt}],
        temperature=0.3,
        max_tokens=512,
    )
    final_answer = final_resp.choices[0].message.content.strip()

    return mode, memory_context, final_answer
"""
Core agent logic: wraps Hindsight (memory) and Groq (LLM reasoning).

retain() stores PM notes. recall() and reflect() are exposed to Groq as
tools - the LLM decides per question which to call (one, both, or repeated).
"""

import os
import json
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


# ---------------------------------------------------------------------------
# Tool definitions exposed to Groq - the LLM decides per question whether to
# call recall, reflect, both, or repeat either, rather than a fixed rule.
# ---------------------------------------------------------------------------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": (
                "Search the memory bank for specific facts, statements, or events. "
                "Use this to find concrete details: who said what, when something "
                "happened, the status of a specific item, a specific decision or "
                "request. Returns raw memory snippets, each as a separate fact."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "A focused search query describing what fact(s) to find.",
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "reflect",
            "description": (
                "Ask the memory system to reason over everything it knows and produce "
                "a synthesized answer. Use this for questions that require connecting "
                "multiple memories over time: spotting patterns, recurring issues, "
                "risks, trends, or recommendations. This does its own retrieval AND "
                "reasoning - it can be used on its own or after recall() to add a "
                "layer of synthesis on top of specific facts."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The synthesis/reasoning question to pose to the memory system.",
                    }
                },
                "required": ["query"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are an AI Project Manager assistant for FinTrack, a budgeting app. "
    "You have access to a long-term memory system (Hindsight) via two tools:\n\n"
    "- recall(query): retrieves specific facts/memories matching a query.\n"
    "- reflect(query): performs reasoning over memories to produce synthesized "
    "insights (patterns, risks, recommendations).\n\n"
    "For each user question, decide which tool(s) to use - you may call recall, "
    "reflect, both, or call a tool multiple times with different queries if needed. "
    "Use recall when the question asks for a specific fact or status. Use reflect "
    "when the question asks you to synthesize, spot patterns, or recommend something. "
    "For questions that benefit from both (e.g. 'what risks should I flag' may need "
    "reflect for synthesis, but recall to ground specific dates/names), feel free to "
    "call both.\n\n"
    "Once you have enough information, answer the PM's question directly and "
    "concisely, using only information returned by the tools. If the tools don't "
    "have relevant information, say so honestly. Use bullet points for lists."
)


def _execute_tool_call(hindsight_client: Hindsight, name: str, args: dict, bank_id: str):
    """Execute a single tool call against Hindsight and return a text result."""
    query = args.get("query", "")
    if name == "recall":
        result = recall_memories(hindsight_client, query, bank_id=bank_id)
        if hasattr(result, "results") and result.results:
            return "\n".join(f"- {r.text}" for r in result.results)
        return "No relevant memories found."
    elif name == "reflect":
        result = reflect_on_memories(hindsight_client, query, bank_id=bank_id)
        text = result.text if hasattr(result, "text") else str(result)
        return text or "No insights generated."
    else:
        return f"Unknown tool: {name}"


def answer_question(hindsight_client: Hindsight, groq_client: Groq, question: str,
                     bank_id: str = DEFAULT_BANK_ID, max_iterations: int = 4,
                     on_tool_call=None):
    """
    Agentic loop: Groq decides which Hindsight tools to call, then answers.

    on_tool_call: optional callback(tool_name, args, result) for UI progress.
    Returns (tool_trace, final_answer) - tool_trace logs every memory op used.
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": question},
    ]
    tool_trace = []

    for _ in range(max_iterations):
        resp = groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.2,
            max_tokens=1024,
        )
        msg = resp.choices[0].message

        if not msg.tool_calls:
            # No more tools needed - this is the final answer
            final_answer = (msg.content or "").strip()
            return tool_trace, final_answer

        # Append the assistant's tool-call message, then execute each tool call
        messages.append({
            "role": "assistant",
            "content": msg.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ],
        })

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments)
            except (json.JSONDecodeError, TypeError):
                args = {}

            result_text = _execute_tool_call(hindsight_client, tc.function.name, args, bank_id)
            tool_trace.append({
                "tool": tc.function.name,
                "args": args,
                "result": result_text,
            })
            if on_tool_call is not None:
                on_tool_call(tc.function.name, args, result_text)
            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result_text,
            })

    # Hit max_iterations without a final answer - force one final completion without tools
    resp = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        temperature=0.2,
        max_tokens=1024,
    )
    final_answer = (resp.choices[0].message.content or "").strip()
    return tool_trace, final_answer
"""
FinTrack PM Memory Agent - Streamlit App

A demo agent for a Product Manager that:
- Logs daily notes (standups, stakeholder calls, user feedback) into Hindsight
- Answers questions using Hindsight recall (facts) and reflect (synthesis)
- Visualizes the memory timeline so "memory" is visibly the star of the demo

Run:
    streamlit run app.py
"""

import os
from datetime import datetime
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

from agent import (
    get_hindsight_client,
    get_groq_client,
    ensure_bank,
    retain_log,
    answer_question,
    DEFAULT_BANK_ID,
)
from seed_data import seed
from data.seed_logs import LOGS


# ---------------------------------------------------------------------------
# Page config + light custom styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="FinTrack PM Memory Agent",
    page_icon="🧭",
    layout="wide",
)

CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #F7F6F3;
    }
    h1, h2, h3 {
        font-family: 'Georgia', serif;
        color: #1F2A24;
    }
    .memory-card {
        background-color: #FFFFFF;
        border: 1px solid #E3E0D8;
        border-left: 4px solid #6B8F71;
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.6rem;
    }
    .memory-meta {
        color: #8A8478;
        font-size: 0.78rem;
        margin-bottom: 0.25rem;
        letter-spacing: 0.02em;
        text-transform: uppercase;
    }
    .tag-pill {
        display: inline-block;
        background-color: #EFEDE6;
        color: #5A5448;
        border-radius: 999px;
        padding: 0.1rem 0.6rem;
        margin-right: 0.3rem;
        font-size: 0.72rem;
    }
    .mode-badge-recall {
        background-color: #DCE8E0;
        color: #2F4A3A;
        border-radius: 4px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .mode-badge-reflect {
        background-color: #F0E2D0;
        color: #6E4A23;
        border-radius: 4px;
        padding: 0.15rem 0.5rem;
        font-size: 0.75rem;
        font-weight: 600;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Session state init
# ---------------------------------------------------------------------------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # list of dicts: {question, mode, memory_context, answer}

if "logged_entries" not in st.session_state:
    st.session_state.logged_entries = []  # entries logged this session (for timeline display)


# ---------------------------------------------------------------------------
# Sidebar - setup / status
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🧭 FinTrack PM Agent")
    st.caption("AI Project Manager with persistent memory, powered by Hindsight + Groq.")

    hs_key_set = bool(os.environ.get("HINDSIGHT_API_KEY"))
    groq_key_set = bool(os.environ.get("GROQ_API_KEY"))

    st.markdown("**API Keys**")
    st.write(f"{'✅' if hs_key_set else '❌'} Hindsight API key")
    st.write(f"{'✅' if groq_key_set else '❌'} Groq API key")

    if not (hs_key_set and groq_key_set):
        st.error("Set HINDSIGHT_API_KEY and GROQ_API_KEY in your .env file.")
        st.stop()

    st.divider()
    st.markdown("**Memory Bank**")
    st.code(DEFAULT_BANK_ID, language=None)

    if st.button("🌱 Seed demo data (4 weeks of logs)", use_container_width=True):
        with st.spinner("Seeding Hindsight bank with synthetic PM history..."):
            seed(DEFAULT_BANK_ID, verbose=False)
        st.success(f"Seeded {len(LOGS)} memories!")

    st.caption(
        "Seeding loads ~4 weeks of synthetic standups, stakeholder calls, and "
        "user feedback for FinTrack (a budgeting app). This gives the agent "
        "history to recall and reflect on."
    )

    st.divider()
    st.markdown("**About this demo**")
    st.caption(
        "Persona: You are the PM for FinTrack. Team: Marcus (Eng Lead), "
        "Lena (Designer). Stakeholders: Priya (Head of Product), David (Sales VP)."
    )


# ---------------------------------------------------------------------------
# Init clients
# ---------------------------------------------------------------------------
@st.cache_resource
def init_clients():
    hindsight = get_hindsight_client()
    ensure_bank(hindsight, DEFAULT_BANK_ID)
    groq = get_groq_client()
    return hindsight, groq

hindsight_client, groq_client = init_clients()


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("FinTrack — AI Project Manager")
st.caption(
    "Logs your product notes into long-term memory, then answers questions by "
    "recalling facts or reflecting across weeks of history."
)

tab_log, tab_ask, tab_timeline = st.tabs(["📝 Log a Note", "💬 Ask the Agent", "🧠 Memory Timeline"])


# ---------------------------------------------------------------------------
# TAB 1: Log a note
# ---------------------------------------------------------------------------
with tab_log:
    st.subheader("Log today's notes")
    st.caption(
        "Paste in standup notes, a stakeholder call summary, or user feedback. "
        "This gets stored in Hindsight so the agent can recall or reflect on it later."
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        log_context = st.selectbox(
            "Source",
            [
                "Daily standup - Engineering",
                "Stakeholder call - Priya",
                "Stakeholder call - David",
                "User research synthesis",
                "Design review",
                "Other / custom",
            ],
        )
        if log_context == "Other / custom":
            log_context = st.text_input("Custom source label", value="Note")

    with col2:
        tag_options = [
            "standup", "engineering", "design", "stakeholder", "priya", "david",
            "search-redesign", "export-feature", "onboarding", "notifications",
            "user-feedback", "blocker", "risk", "request", "planning", "sales",
        ]
        selected_tags = st.multiselect("Tags", tag_options, default=[])

    log_content = st.text_area(
        "Note content",
        height=150,
        placeholder=(
            "e.g. Marcus flagged that the export feature will need design input "
            "from Lena before engineering can start..."
        ),
    )

    if st.button("💾 Save to memory", type="primary"):
        if not log_content.strip():
            st.warning("Write something before saving.")
        else:
            with st.spinner("Storing in Hindsight (retain)..."):
                retain_log(
                    hindsight_client,
                    content=log_content.strip(),
                    context=log_context,
                    tags=selected_tags,
                    timestamp=datetime.now(),
                )
            st.session_state.logged_entries.append({
                "content": log_content.strip(),
                "context": log_context,
                "tags": selected_tags,
                "timestamp": datetime.now().isoformat(),
            })
            st.success("Saved to memory.")


# ---------------------------------------------------------------------------
# TAB 2: Ask the agent
# ---------------------------------------------------------------------------
with tab_ask:
    st.subheader("Ask about your product")
    st.caption(
        "Try a factual recall question (\"What did Priya ask for?\") or a "
        "synthesis question (\"What risks should I flag this week?\")."
    )

    example_questions = [
        "What did Priya ask for?",
        "What's the status of the export feature?",
        "What risks should I flag in tomorrow's exec review?",
        "What have we learned about onboarding from user feedback?",
        "Has the API rate limit issue come up before?",
    ]

    cols = st.columns(len(example_questions))
    clicked_example = None
    for i, q in enumerate(example_questions):
        if cols[i].button(q, key=f"ex_{i}", use_container_width=True):
            clicked_example = q

    question = st.text_input(
        "Your question",
        value=clicked_example or "",
        key="question_input",
        placeholder="Ask the agent anything about FinTrack's history...",
    )

    if st.button("Ask", type="primary") and question.strip():
        thinking_placeholder = st.empty()
        live_steps = []

        def _show_progress(tool_name, args, result):
            icon = "🧩" if tool_name == "reflect" else "🔍"
            label = "Reflecting" if tool_name == "reflect" else "Recalling"
            query_preview = args.get("query", "")
            live_steps.append(f"{icon} {label}: _{query_preview}_")
            thinking_placeholder.markdown("\n\n".join(live_steps))

        with st.spinner("Agent is thinking..."):
            tool_trace, answer = answer_question(
                hindsight_client, groq_client, question.strip(),
                on_tool_call=_show_progress,
            )
        thinking_placeholder.empty()
        st.session_state.chat_history.insert(0, {
            "question": question.strip(),
            "tool_trace": tool_trace,
            "answer": answer,
        })

    st.divider()

    for entry in st.session_state.chat_history:
        st.markdown(f"**Q: {entry['question']}**")

        # Show a badge for each tool call the agent actually made, in order
        badges_html = ""
        for call in entry["tool_trace"]:
            if call["tool"] == "reflect":
                badges_html += '<span class="mode-badge-reflect">REFLECT (synthesis)</span> '
            else:
                badges_html += '<span class="mode-badge-recall">RECALL (fact lookup)</span> '
        if badges_html:
            st.markdown(badges_html, unsafe_allow_html=True)
        else:
            st.caption("No memory operations were used for this answer.")

        st.markdown(entry["answer"])

        with st.expander(f"🔍 Show agent's memory operations ({len(entry['tool_trace'])})"):
            if not entry["tool_trace"]:
                st.text("The agent answered without querying memory.")
            for i, call in enumerate(entry["tool_trace"], 1):
                st.markdown(f"**{i}. `{call['tool']}`** — query: _{call['args'].get('query', '')}_")
                st.text(call["result"])
                if i < len(entry["tool_trace"]):
                    st.markdown("---")

        st.divider()


# ---------------------------------------------------------------------------
# TAB 3: Memory timeline (this session's logs)
# ---------------------------------------------------------------------------
with tab_timeline:
    st.subheader("What's in memory (this session)")
    st.caption(
        "Entries you've logged in this session. The full history (including the "
        "seeded 4 weeks) lives in Hindsight and is what powers recall/reflect above."
    )

    if not st.session_state.logged_entries:
        st.info("Nothing logged yet this session. Use the 'Log a Note' tab, or seed demo data from the sidebar.")
    else:
        for entry in reversed(st.session_state.logged_entries):
            tags_html = "".join(f'<span class="tag-pill">{t}</span>' for t in entry["tags"])
            st.markdown(
                f"""
                <div class="memory-card">
                    <div class="memory-meta">{entry['context']} &middot; {entry['timestamp'][:16]}</div>
                    <div>{entry['content']}</div>
                    <div style="margin-top:0.5rem;">{tags_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.divider()
    st.markdown("**Seeded demo history (4 weeks)**")
    st.caption("This is the synthetic dataset loaded via 'Seed demo data' in the sidebar.")
    for log in LOGS:
        tags_html = "".join(f'<span class="tag-pill">{t}</span>' for t in log["tags"])
        st.markdown(
            f"""
            <div class="memory-card">
                <div class="memory-meta">Week {log['week']} &middot; {log['context']} &middot; {log['timestamp'][:10]}</div>
                <div>{log['content']}</div>
                <div style="margin-top:0.5rem;">{tags_html}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
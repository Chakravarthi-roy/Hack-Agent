# FinTrack PM Memory Agent

An AI Project/Product Manager assistant with **persistent memory powered by
[Hindsight](https://hindsight.vectorize.io)** and reasoning powered by **Groq**.

## The idea

A PM logs notes after standups, stakeholder calls, and user research sessions.
These get stored in Hindsight's memory layer. Later, the PM can ask:

- **Factual recall**: "What did Priya ask for?" → Hindsight `recall`
- **Synthesis / reasoning**: "What risks should I flag in tomorrow's exec review?" → Hindsight `reflect`

Hindsight connects the dots across weeks of scattered notes — e.g. the same
API rate-limit blocker mentioned in week 1, week 2, and week 4 gets surfaced
as a recurring risk worth escalating, even though no single note says "this
is recurring."

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

(If you hit an "externally managed environment" error, add `--break-system-packages`.)

### 2. Add your API keys

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

```
HINDSIGHT_API_KEY=your-hindsight-cloud-api-key
GROQ_API_KEY=your-groq-api-key
```

- Hindsight Cloud key: sign up at https://ui.hindsight.vectorize.io
- Groq key: https://console.groq.com

### 3. Test connectivity

```bash
python test_connection.py
```

This should print `=== All checks passed! ===` at the end. If it fails,
check that both keys are set correctly in `.env`.

### 4. Seed the demo data (4 weeks of synthetic PM logs)

```bash
python seed_data.py
```

This loads ~16 synthetic notes (standups, stakeholder calls, design reviews,
user research) for a fictional product called **FinTrack** (a budgeting app)
into a Hindsight memory bank. You can also do this from the app sidebar.

### 5. Run the app

```bash
streamlit run app.py
```

## Demo script (suggested)

1. **Seed data** from the sidebar (4 weeks of history loads instantly).
2. Go to **Ask the Agent** tab, try:
   - *"What did Priya ask for?"* → shows `RECALL` mode, pulls the exact
     stakeholder request from week 1/3.
   - *"What's the status of the export feature?"* → recall across multiple
     entries (request → scoping → status).
   - *"What risks should I flag in tomorrow's exec review?"* → shows
     `REFLECT` mode — Hindsight synthesizes the recurring API rate-limit
     issue across 3 separate weeks into one flagged risk, something no
     single note states directly.
3. Go to **Log a Note** tab, add a new note (e.g. a new standup update),
   then immediately ask a follow-up question that references it — showing
   memory updates live.
4. **Memory Timeline** tab shows everything that's been retained, making the
   memory layer visible and tangible for judges.

## Project structure

```
.
├── app.py              # Streamlit UI (3 tabs: Log, Ask, Timeline)
├── agent.py            # Hindsight + Groq wrapper logic
├── seed_data.py         # Loads synthetic logs into Hindsight
├── test_connection.py  # Connectivity check for both APIs
├── data/
│   └── seed_logs.py     # Synthetic 4-week dataset for FinTrack
├── requirements.txt
└── .env.example
```

## Why Hindsight is central here

- **retain**: every PM note (standup, call, feedback) is stored with tags
  and timestamps.
- **recall**: factual questions are answered by retrieving the specific
  relevant memories.
- **reflect**: synthesis questions trigger Hindsight's reasoning over
  multiple memories — this is where the "agent gets smarter over time"
  story is most visible. The recurring API rate-limit blocker (mentioned
  in weeks 1, 2, and 4) is never explicitly labeled as "recurring" in any
  single note — only by connecting memories across time does the pattern
  emerge.
# FinTrack PM Agent

A small AI Project Manager assistant built around [Hindsight](https://hindsight.vectorize.io) for long-term memory and Groq for reasoning.

The idea: a PM logs notes after standups, stakeholder calls, and user research. Those notes go into Hindsight. Later, the PM can just ask questions - the agent decides on its own whether it needs to pull up a specific fact, reason across everything it knows, or both.

## Why this is interesting

Most "AI assistant" demos are stateless - every conversation starts from zero. This one isn't. After a few weeks of logs, you can ask things like:

- "What did Priya ask for?" - pulls the exact request from memory.
- "What's the status of the export feature?" - pieces together the request, the scoping, and where things stand now, from notes logged on different days.
- "What risks should I flag in tomorrow's exec review?" - this is the fun one. The same API rate-limit issue gets mentioned across three separate weeks, never explicitly flagged as "recurring" in any single note. The agent connects those dots and surfaces it as a risk on its own.

That last one is really the whole point of using Hindsight here - it's not just storage, it's the thing that turns scattered notes into something useful weeks later.

## How it's built

- `agent.py` - Hindsight + Groq glue. `recall` and `reflect` are exposed to Groq as tools, and the model decides per question what it actually needs.
- `app.py` - Streamlit UI with three tabs: log a note, ask the agent, and a memory timeline view.
- `data/seed_logs.py` - ~4 weeks of synthetic logs for a fictional product (FinTrack, a budgeting app) and team, so the agent has history to work with out of the box.
- `seed_data.py` / `test_connection.py` - helper scripts for loading the seed data and checking your API keys work.

This is scoped to one PM, one product, one small team - on purpose. The goal was to get the memory mechanic working well for a single clear workflow rather than spreading thin across a generic multi-user tool.

## Running it

```bash
pip install -r requirements.txt
```

If pip complains about an "externally managed environment," add `--break-system-packages`.

Copy `.env.example` to `.env` and add your keys:

```
HINDSIGHT_API_KEY=...
GROQ_API_KEY=...
```

(Hindsight Cloud: https://ui.hindsight.vectorize.io, Groq: https://console.groq.com)

Then check the connection works:

```bash
python test_connection.py
```

Load the synthetic 4-week dataset (or just click "Seed demo data" in the app sidebar):

```bash
python seed_data.py
```

And run the app:

```bash
streamlit run app.py
```

## Trying it out

Once seeded, head to the "Ask the Agent" tab and try the example questions, or write your own. Worth trying a few different angles:

- A direct factual question ("what did David say about the export feature?")
- A "what should I worry about" question - this is where reflect kicks in and you'll see it pull together things from multiple weeks.
- Something that's genuinely not in the data ("who's the CEO of FinTrack?") - it should just say it doesn't know, rather than making something up.

You can also log a new note yourself and ask about it right after - it's already part of memory by the time you ask.

The "memory operations" expander under each answer shows exactly what the agent searched for and what came back, so it's not a black box.
"""
Synthetic PM log data for FinTrack product.
Spans ~4 weeks. Designed so:
- "API rate limit" blocker on Search Redesign recurs in weeks 1, 2, and 4 (reflect demo).
- Priya (stakeholder) makes a request in week 1, references it again in week 3.
- Onboarding feedback theme builds across weeks 2-4.
- Each entry has: content, context, tags, timestamp (ISO), week label.
"""

from datetime import datetime, timedelta

# Anchor date - "today" in the demo is roughly 4 weeks after week 1 day 1
BASE_DATE = datetime(2026, 5, 11)  # a Monday

def d(week_offset_days):
    return (BASE_DATE + timedelta(days=week_offset_days)).strftime("%Y-%m-%dT09:00:00")

LOGS = [
    # ---------- WEEK 1 ----------
    {
        "week": 1,
        "content": (
            "Standup notes: Marcus (eng lead) flagged that the Search Redesign work is "
            "blocked by the third-party transaction API's rate limits. We're hitting "
            "429 errors during load testing. He estimates this could slip the timeline "
            "by about a week if not resolved."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "search-redesign", "blocker", "risk"],
        "timestamp": d(0),
    },
    {
        "week": 1,
        "content": (
            "Call with Priya (Head of Product): she wants the CSV export feature "
            "prioritized for Q3 because two enterprise clients specifically asked for "
            "it during renewal conversations. She said it's a 'must-have for the Q3 "
            "roadmap review' and wants a status update before the review."
        ),
        "context": "Stakeholder call - Priya",
        "tags": ["stakeholder", "priya", "export-feature", "request"],
        "timestamp": d(1),
    },
    {
        "week": 1,
        "content": (
            "User interview synthesis (3 sessions this week): two of three users got "
            "confused at onboarding step 3, where we ask them to link a bank account "
            "before showing any value. One user said 'I wasn't sure why I needed to "
            "do this yet.' Lena (designer) thinks we should show a preview/demo "
            "dashboard before asking for account linking."
        ),
        "context": "User research synthesis",
        "tags": ["user-feedback", "onboarding", "design"],
        "timestamp": d(2),
    },
    {
        "week": 1,
        "content": (
            "Standup notes: Marcus says the team worked around the API rate limit "
            "issue for now using request batching, but it's a temporary fix. He "
            "thinks we'll hit the same wall again once we add the budgeting alerts "
            "feature, which will make even more API calls."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "search-redesign", "blocker", "risk"],
        "timestamp": d(3),
    },

    # ---------- WEEK 2 ----------
    {
        "week": 2,
        "content": (
            "Standup notes: Search Redesign is back on track after the batching "
            "workaround. Marcus says it should ship by end of next week. He also "
            "mentioned the notifications feature (budgeting alerts) is in early "
            "design and will likely need the same transaction API at higher volume."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "search-redesign", "notifications"],
        "timestamp": d(7),
    },
    {
        "week": 2,
        "content": (
            "Design review with Lena: she presented a new onboarding flow where users "
            "see a sample dashboard with demo data BEFORE linking their real bank "
            "account. This directly addresses the confusion at step 3 we heard about "
            "last week. She wants feedback by Friday."
        ),
        "context": "Design review",
        "tags": ["design", "onboarding", "user-feedback"],
        "timestamp": d(8),
    },
    {
        "week": 2,
        "content": (
            "Another user interview (2 sessions): one user dropped off entirely at "
            "the bank-linking step in onboarding and never came back. This is the "
            "second time this week we've heard onboarding step 3 is a drop-off point."
        ),
        "context": "User research synthesis",
        "tags": ["user-feedback", "onboarding", "risk"],
        "timestamp": d(9),
    },
    {
        "week": 2,
        "content": (
            "Quick sync with David (Sales VP): he mentioned that during a demo to a "
            "prospect this week, the prospect asked specifically about exporting "
            "transaction data to Excel for their accountant. David says this comes "
            "up 'pretty often' in sales calls."
        ),
        "context": "Stakeholder call - David",
        "tags": ["stakeholder", "david", "export-feature", "sales"],
        "timestamp": d(10),
    },

    # ---------- WEEK 3 ----------
    {
        "week": 3,
        "content": (
            "Standup notes: Search Redesign shipped to staging. QA found a minor "
            "issue with sort order on large transaction lists but otherwise looks "
            "good. Targeting production release early next week."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "search-redesign"],
        "timestamp": d(14),
    },
    {
        "week": 3,
        "content": (
            "Follow-up call with Priya: she asked for the status on the export "
            "feature ahead of the Q3 roadmap review next week. I let her know it's "
            "not started yet - design work hasn't begun. She seemed concerned and "
            "asked if we could at least scope it before the review."
        ),
        "context": "Stakeholder call - Priya",
        "tags": ["stakeholder", "priya", "export-feature", "request", "risk"],
        "timestamp": d(15),
    },
    {
        "week": 3,
        "content": (
            "Design review: Lena's new onboarding flow (sample dashboard before bank "
            "linking) tested well with 4 of 5 users in a quick usability test. "
            "Recommend moving this into the sprint. Engineering estimates 1 week of "
            "work."
        ),
        "context": "Design review",
        "tags": ["design", "onboarding", "user-feedback"],
        "timestamp": d(16),
    },
    {
        "week": 3,
        "content": (
            "Standup notes: Marcus started early design discussions for the "
            "notifications/budgeting alerts feature. He's already flagging that "
            "this feature will significantly increase calls to the transaction API "
            "and wants to revisit the rate-limit issue before committing to a "
            "timeline, since the batching workaround from a couple weeks ago was "
            "only ever meant to be temporary."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "notifications", "blocker", "risk", "search-redesign"],
        "timestamp": d(17),
    },

    # ---------- WEEK 4 ----------
    {
        "week": 4,
        "content": (
            "Search Redesign shipped to production successfully. Sort order bug from "
            "QA was fixed before release. No issues reported so far."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "search-redesign"],
        "timestamp": d(21),
    },
    {
        "week": 4,
        "content": (
            "Scoping session for export feature: rough scope is CSV and Excel export "
            "for transaction history, filterable by date range and category. "
            "Engineering estimates 1.5-2 weeks. Sharing this scope with Priya before "
            "the roadmap review tomorrow."
        ),
        "context": "Planning - Export feature",
        "tags": ["export-feature", "planning", "priya"],
        "timestamp": d(22),
    },
    {
        "week": 4,
        "content": (
            "Standup notes: Marcus raised the transaction API rate limit issue again "
            "- this is the third time it's come up. He's now recommending we "
            "formally request a higher rate limit tier from the API provider before "
            "starting notifications work, rather than relying on more workarounds. "
            "He wants this flagged as a dependency risk for the notifications "
            "feature in the roadmap."
        ),
        "context": "Daily standup - Engineering",
        "tags": ["standup", "engineering", "notifications", "blocker", "risk", "search-redesign"],
        "timestamp": d(23),
    },
    {
        "week": 4,
        "content": (
            "Onboarding redesign (sample dashboard before account linking) completed "
            "development and is in QA. Lena confirmed it matches the tested design "
            "from the usability sessions. Targeting release next week, which should "
            "directly address the drop-off issue we've tracked since week 1."
        ),
        "context": "Design review",
        "tags": ["design", "onboarding", "user-feedback"],
        "timestamp": d(24),
    },
]


if __name__ == "__main__":
    print(f"Total log entries: {len(LOGS)}")
    for log in LOGS:
        print(f"Week {log['week']} | {log['timestamp']} | {log['context']}")
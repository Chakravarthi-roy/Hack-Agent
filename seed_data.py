"""
Seed the Hindsight bank with the synthetic PM logs (data/seed_logs.py).

Simulates 4 weeks of PM notes so the demo has history to recall/reflect on.
Run once before the demo, or via the "Seed demo data" button in the sidebar.

Usage:
    python seed_data.py
"""

from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from agent import get_hindsight_client, ensure_bank, retain_log, DEFAULT_BANK_ID
from data.seed_logs import LOGS


def seed(bank_id: str = DEFAULT_BANK_ID, verbose: bool = True):
    client = get_hindsight_client()
    ensure_bank(client, bank_id)

    for i, log in enumerate(LOGS, 1):
        ts = datetime.fromisoformat(log["timestamp"])
        retain_log(
            client,
            content=log["content"],
            context=log["context"],
            tags=log["tags"],
            timestamp=ts,
            bank_id=bank_id,
        )
        if verbose:
            print(f"[{i}/{len(LOGS)}] Retained (week {log['week']}): {log['context']}")

    if verbose:
        print(f"\nDone. Seeded {len(LOGS)} memories into bank '{bank_id}'.")


if __name__ == "__main__":
    seed()
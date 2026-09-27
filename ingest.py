"""
Load incident data into Hindsight as memories (the "retain" step).

This is what gives your agent its long-term memory. Run this once after you
have data, and again any time you add more incidents.

Usage:
    python ingest.py
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from hindsight_client import Hindsight

load_dotenv()

client = Hindsight(
    base_url=os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"),
    api_key=os.environ["HINDSIGHT_API_KEY"],
)
BANK_ID = os.environ.get("HINDSIGHT_BANK_ID", "incident-response-demo")


def load_incidents() -> list[dict]:
    generated = Path(__file__).parent / "data" / "incidents.json"
    sample = Path(__file__).parent / "data" / "sample_incidents.json"

    incidents = []
    if sample.exists():
        incidents += json.loads(sample.read_text())
    if generated.exists():
        incidents += json.loads(generated.read_text())
    return incidents


def main():
    incidents = load_incidents()
    if not incidents:
        print("No incident data found in data/. Run generate_data.py first, "
              "or make sure data/sample_incidents.json exists.")
        return

    for inc in incidents:
        content = (
            f"Incident {inc['id']} in {inc['service']}.\n"
            f"Error: {inc['error_signature']}\n"
            f"Symptoms: {inc['symptoms']}\n"
            f"Root cause: {inc['root_cause']}\n"
            f"Resolution: {inc['resolution_steps']}\n"
            f"Resolved in {inc['resolution_time_minutes']} minutes."
        )
        client.retain(
            bank_id=BANK_ID,
            content=content,
            context="past incident postmortem",
            timestamp=inc.get("timestamp"),
            metadata={"service": inc["service"], "incident_id": inc["id"]},
        )
        print(f"Retained {inc['id']} ({inc['service']})")

    print(f"\nDone. {len(incidents)} incidents loaded into bank '{BANK_ID}'.")
    print(f"View them at: https://ui.hindsight.vectorize.io/banks/{BANK_ID}?view=documents")


if __name__ == "__main__":
    main()

"""
Generate additional synthetic incident data using Groq's LLM.

You already have 5 sample incidents in data/sample_incidents.json to get started.
Run this script to generate more -> data/incidents.json.

Generates in two smaller batches instead of one big request, since asking for
15 at once can get cut off mid-response (truncated JSON) on some models.

Usage:
    python generate_data.py
"""
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1",
)
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

BATCH_SIZE = 8
NUM_BATCHES = 2

PROMPT_TEMPLATE = """Generate exactly {n} realistic software engineering production incidents as a JSON array.
Each incident must be an object with exactly these fields:
- "id": short string like "INC-{start}"
- "service": name of a microservice (e.g. "payments-api", "auth-service", "checkout-worker")
- "error_signature": the exact error message / stack trace snippet an on-call engineer would see in logs (1-3 lines)
- "symptoms": short description of what users/systems experienced
- "root_cause": the underlying technical root cause, written like a real postmortem
- "resolution_steps": numbered steps taken to fix it, as a single string
- "resolution_time_minutes": integer, how long it took to resolve
- "timestamp": ISO 8601 datetime sometime in the last 6 months

Vary the root causes across: {themes}

Return ONLY the raw JSON array. No markdown fences, no commentary, no explanation, no trailing text after the closing bracket. Keep each field concise so the full response stays well under the token limit.
"""

THEMES = [
    "connection pool exhaustion, memory leaks, bad deploys, rate limit misconfiguration",
    "expired certificates, race conditions, N+1 queries, cache stampedes, DNS failures, disk space exhaustion",
]


def generate_batch(n: int, start: int, themes: str) -> list[dict]:
    prompt = PROMPT_TEMPLATE.format(n=n, start=start, themes=themes)
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=4000,
    )
    raw = resp.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        debug_path = Path(__file__).parent / "data" / f"debug_raw_batch_{start}.txt"
        debug_path.write_text(raw)
        print(f"Could not parse batch starting at {start}: {e}")
        print(f"Raw response saved to {debug_path} for inspection.")
        return []


def main():
    all_incidents = []
    for i in range(NUM_BATCHES):
        start = 101 + i * BATCH_SIZE
        print(f"Requesting batch {i + 1}/{NUM_BATCHES} ({BATCH_SIZE} incidents)...")
        batch = generate_batch(BATCH_SIZE, start, THEMES[i % len(THEMES)])
        print(f"  -> got {len(batch)} incidents")
        all_incidents.extend(batch)

    if not all_incidents:
        print("\nNo incidents were generated successfully. Check the debug files "
              "in data/ for what the model actually returned.")
        return

    out_path = Path(__file__).parent / "data" / "incidents.json"
    out_path.write_text(json.dumps(all_incidents, indent=2))
    print(f"\nGenerated {len(all_incidents)} incidents total -> {out_path}")


if __name__ == "__main__":
    main()
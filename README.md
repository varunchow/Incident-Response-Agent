# Incident Response Agent (built with Hindsight)

An on-call assistant that remembers every past incident, its root cause, and
what fixed it — then uses that memory to brief you on a new incident in
seconds instead of you digging through old postmortems.

**Memory story:** without memory, this is just a generic LLM guessing at
fixes. With Hindsight, it recalls the closest matching past incident and
tells you exactly what worked (or didn't) last time — and every resolved
incident makes the next recall smarter.

## How it works

1. **Retain** — past incident postmortems are loaded into Hindsight as memories (`ingest.py`)
2. **Recall** — when a new incident comes in, the agent searches memory for similar past incidents (`agent.py: handle_incident`)
3. **(Retain again)** — once resolved, the outcome is written back to memory, so next time this pattern is recalled, the agent already knows what worked (`agent.py: resolve_incident`)
4. **Reflect** (optional, bonus) — `agent.py: reflect_on_service` asks Hindsight to synthesize a higher-level pattern across many incidents for one service — good for a "here's what the agent has learned" demo moment

## Setup

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the env template and fill in your real keys
cp .env.example .env
# then edit .env with your GROQ_API_KEY and HINDSIGHT_API_KEY
```

## Run it

```bash
# Step 1: (optional) generate 15 more synthetic incidents beyond the 5 sample ones
python generate_data.py

# Step 2: load incident data into Hindsight memory
python ingest.py

# Step 3: start the server
uvicorn app:app --reload --port 8000
```

Open **http://localhost:8000** in your browser.

## Demo script (for judges)

1. Submit an incident similar to one in `data/sample_incidents.json`
   (the textarea is pre-filled with one — a Postgres connection pool exhaustion).
2. Point out that the agent found a matching past incident and cited the
   *exact* root cause and fix from memory — not a generic guess.
3. Click "Mark Resolved" with a slightly different resolution note.
4. Submit a *similar* incident again — show that the response now also
   references the most recent resolution, proving the agent is learning,
   not just doing static lookup.
5. (Bonus) Call `POST /api/reflect` with `{"service": "payments-api"}` to
   show Hindsight synthesizing a cross-incident pattern, e.g. "this service
   has had 3 connection-related incidents in 4 months."

## Files

| File | Purpose |
|---|---|
| `generate_data.py` | Uses Groq to generate realistic synthetic incidents |
| `data/sample_incidents.json` | 5 hand-written incidents, guaranteed to work even with no LLM calls |
| `ingest.py` | Loads incident data into Hindsight (retain) |
| `agent.py` | Core recall + LLM response + retain-outcome logic |
| `app.py` | FastAPI backend |
| `static/index.html` | Demo UI |

## Next steps to strengthen this for judging

- Add more incident categories (rate limits, expired certs, cache stampedes — see `generate_data.py`'s prompt for ideas)
- Show a "confidence" score based on how closely the recalled memory matches
- Add a simple dashboard listing all incidents ever retained, grouped by service
- Record your demo video showing the "before/after" — same incident, better answer the second time

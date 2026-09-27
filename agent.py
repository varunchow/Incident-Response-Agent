import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from hindsight_client import Hindsight

load_dotenv()

groq = AsyncOpenAI(api_key=os.environ["GROQ_API_KEY"], base_url="https://api.groq.com/openai/v1")
MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

memory = Hindsight(
    base_url=os.environ.get("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io"),
    api_key=os.environ["HINDSIGHT_API_KEY"],
)
BANK_ID = os.environ.get("HINDSIGHT_BANK_ID", "incident-response-demo")


async def handle_incident(description: str) -> dict:
    recalled = await memory.arecall(bank_id=BANK_ID, query=description)
    memory_texts = [r.text for r in recalled.results][:5]

    if memory_texts:
        memory_block = "\n\n".join(f"- {m}" for m in memory_texts)
        system_prompt = (
            "You are an incident response assistant with access to memories of past "
            "incidents at this company. Use them to give a fast, specific, actionable "
            "response. If a past incident closely matches, say so explicitly and reference "
            "exactly what worked (or didn't) last time. Be concise: this is for an engineer "
            "during a live incident, not a report."
        )
        user_prompt = (
            f"New incident:\n{description}\n\n"
            f"Relevant memories from past incidents:\n{memory_block}\n\n"
            "What is likely happening, and what should the on-call engineer try first?"
        )
    else:
        system_prompt = (
            "You are an incident response assistant. No matching past incidents were found "
            "in memory. Give a best-effort general debugging response and clearly note that "
            "this looks like a new type of incident with no prior history."
        )
        user_prompt = f"New incident:\n{description}\n\nWhat should the on-call engineer try first?"

    resp = await groq.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
    )

    return {
        "response": resp.choices[0].message.content,
        "matched_memories": memory_texts,
        "had_memory_match": bool(memory_texts),
    }


async def resolve_incident(description: str, resolution: str, worked: bool) -> None:
    content = (
        f"Incident: {description}\n"
        f"Resolution attempted: {resolution}\n"
        f"Outcome: {'This resolved the issue.' if worked else 'This did NOT resolve the issue.'}"
    )
    await memory.aretain(
        bank_id=BANK_ID,
        content=content,
        context="incident resolution outcome",
    )


async def reflect_on_service(service: str) -> str:
    result = await memory.areflect(
        bank_id=BANK_ID,
        query=f"What patterns or recurring issues have we seen with {service}?",
    )
    return result.text
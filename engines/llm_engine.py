import os
import requests

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")

SYSTEM_PROMPT = (
    "You are GeoCopilot, a concise travel copilot. "
    "Write practical, short, step-by-step trip suggestions. "
    "Keep it under ~8 bullet points. Avoid fluff."
)

def _gen(prompt: str) -> str:
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
        timeout=120
    )
    r.raise_for_status()
    return r.json().get("response", "").strip()

def chat_recommendation(location: dict, user_prompt: str) -> str:
    lat = location["lat"]; lon = location["lon"]
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Task: Suggest a short trip plan near lat={lat}, lon={lon}.\n"
        f"User prompt: {user_prompt}\n"
        "Requirements:\n"
        "- 2–4 stops max\n"
        "- Distances/time rough estimates are fine\n"
        "- Output as bullet list + 2-sentence overview at top\n"
        "- English only\n"
    )
    return _gen(prompt)

def route_recommendation(start: dict, end: dict, user_prompt: str) -> str:
    s = f"({start['lat']},{start['lon']})"
    e = f"({end['lat']},{end['lon']})"
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"Task: Suggest a simple trip from A{s} to B{e}.\n"
        f"User prompt: {user_prompt}\n"
        "Constraints:\n"
        "- Assume driving; give a high-level sequence (no exact turns)\n"
        "- 2–3 optional stops en route (coffee/viewpoints/etc.)\n"
        "- Output: brief overview + numbered steps + optional stops\n"
        "- English only\n"
    )
    return _gen(prompt)

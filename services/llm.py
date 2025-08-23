import os, json, requests
from typing import Protocol, Dict, Optional

class LLMService(Protocol):
    def summarize(self, system_prompt: str, facts: Dict) -> str: ...

class OllamaLLMService:
    def __init__(self, *, base_url: Optional[str] = None, model: Optional[str] = None):
        # Read defaults from env when not provided
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model    = model    or os.getenv("LLM_MODEL", "llama3.1:8b")

    def summarize(self, system_prompt: str, facts: Dict) -> str:
        prompt = (
            f"{system_prompt}\n\n"
            "Consider ONLY the JSON facts and write a concise, fluent summary in English. "
            "Use 1–2 short paragraphs and bullet tips if relevant. No JSON in the output.\n\n"
            f"FACTS = {json.dumps(facts, ensure_ascii=False)}"
        )
        r = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        text = (r.json() or {}).get("response", "").strip()
        return text or "No summary."

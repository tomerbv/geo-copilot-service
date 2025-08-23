from typing import Protocol, Dict
import json, requests

class LLMService(Protocol):
    def summarize(self, system_prompt: str, facts: Dict) -> str: ...

class OllamaLLMService:
    def __init__(self, base_url: str, model: str):
        self.base_url, self.model = base_url, model

    def summarize(self, system_prompt: str, facts: Dict) -> str:
        prompt = (
            f"{system_prompt}\n\n"
            "Consider ONLY the JSON facts and write a concise, fluent summary in English. "
            "Use 1–2 short paragraphs and bullet tips if relevant. No JSON in the output.\n\n"
            f"FACTS = {json.dumps(facts, ensure_ascii=False)}"
        )
        r = requests.post(f"{self.base_url}/api/generate",
                          json={"model": self.model, "prompt": prompt, "stream": False},
                          timeout=120)
        r.raise_for_status()
        text = (r.json() or {}).get("response", "").strip()
        return text or "No summary."

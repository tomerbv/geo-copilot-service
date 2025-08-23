import os
import requests
from typing import Protocol, Optional

class LLMService(Protocol):
    def generate(self, prompt: str) -> str: ...

class OllamaLLMService:
    """
    Thin LLM client: send a prompt, get back text. No prompt assembly here.
    """
    def __init__(self, *, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.model    = model    or os.getenv("LLM_MODEL", "llama3.1:8b")

    def generate(self, prompt: str) -> str:
        r = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False},
            timeout=120,
        )
        r.raise_for_status()
        return (r.json() or {}).get("response", "").strip() or "No output."

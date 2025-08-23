from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Dict
import json
from services.llm import LLMService

class BaseGeoCopilotEngine(ABC):
    """
    Abstract base for all engines:
    - owns prompt_rules: List[str]
    - assembles the final prompt from rules + FACTS
    - requires subclasses to implement `run(...)`
    """

    def __init__(self, llm: LLMService, *, prompt_rules: List[str]):
        self._llm = llm
        self.prompt_rules = list(prompt_rules)

    def build_prompt(self, facts: Dict, user_prompt: str) -> str:
        user_prompt = (user_prompt or "").strip()
        rules_block = "\n".join(f"- {r}" for r in self.prompt_rules)
        user_block = f"USER REQUEST:\n{user_prompt}\n\n" if user_prompt else ""
        return (
            "Follow ALL these rules:\n"
            f"{rules_block}\n\n"
            f"{user_block}"
            "FACTS (machine-provided, authoritative):\n"
            f"{json.dumps(facts, ensure_ascii=False)}\n\n"
            "Write the final answer now."
        )

    def _generate(self, facts: Dict, user_prompt: str) -> str:
        return self._llm.generate(self.build_prompt(facts, user_prompt))

    @abstractmethod
    def run(self, *args, **kwargs) -> str:
        raise NotImplementedError

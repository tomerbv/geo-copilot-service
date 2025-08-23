from typing import List, Dict, Protocol
import json
from services.llm import LLMService

class BaseGeoCopilotEngine:
    """
    Shared engine base:
    - holds prompt_rules: List[str]
    - builds the final LLM prompt from rules + caller-provided FACTS
    """

    def __init__(self, llm: LLMService, *, prompt_rules: List[str] | None = None):
        self._llm = llm
        # Core, shared “identity + guardrails” rules for GeoCopilot
        default_rules: List[str] = [
            "You are GeoCopilot, a helpful geo/travel assistant.",
            "English only.",
            "Be concise and practical.",
            "Prefer 1–2 short paragraphs; add bullet tips if helpful.",
            "Do not include raw JSON in the output.",
            "Avoid suggesting gas stations or infrastructure unless asked.",
            "Rely only on the provided facts; do not hallucinate places or distances.",
        ]
        # Engines may pass extra rules; keep order: shared first, then engine‑specific
        self.prompt_rules: List[str] = default_rules + (prompt_rules or [])

    # Engines call this to convert rules + facts into a single prompt string
    def build_prompt(self, facts: Dict) -> str:
        rules_block = "\n".join(f"- {r}" for r in self.prompt_rules)
        # We keep the JSON in a FACTS section but tell the model (via rules) not to emit JSON
        prompt = (
            "Follow ALL these rules:\n"
            f"{rules_block}\n\n"
            "FACTS (machine-provided, authoritative):\n"
            f"{json.dumps(facts, ensure_ascii=False)}\n\n"
            "Write the final answer now."
        )
        return prompt

    def _generate(self, facts: Dict) -> str:
        prompt = self.build_prompt(facts)
        return self._llm.generate(prompt)

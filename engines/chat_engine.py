from typing import Tuple, Dict
from services.llm import LLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI
from engines.abstract_engine import BaseGeoCopilotEngine

LatLon = Tuple[float, float]

class ChatEngine(BaseGeoCopilotEngine):
    def __init__(
        self,
        geocoder: NominatimGeocoder,
        poi: OverpassPOI,
        llm: LLMService,
        *,
        prompt_rules: list[str] | None = None,
    ):
        # Engine‑specific rules layered on top of base rules
        engine_rules = [
            "You receive a verified location and a small list of nearby POIs.",
            "If the user did not specify a search radius, assume 3000 meters.",
            "Summarize the area, notable POIs, and give a few practical tips.",
        ]
        super().__init__(llm, prompt_rules=(prompt_rules or []) + engine_rules)
        self._geocoder = geocoder
        self._poi = poi

    def _build_facts(self, loc: LatLon, user_prompt: str) -> Dict:
        lat, lon = loc
        return {
            "location": self._geocoder.reverse(lat, lon),
            "pois": self._poi.around(lat, lon, 30),
            "user_prompt": user_prompt,
        }

    def run(self, loc: LatLon, user_prompt: str) -> str:
        facts = self._build_facts(loc, user_prompt)
        return self._generate(facts)

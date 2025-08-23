from typing import Tuple, Dict
from services.llm import LLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI
from engines.abstract_engine import BaseGeoCopilotEngine
from config.config_loader import combined_rules, default_user_prompt

LatLon = Tuple[float, float]

class ChatEngine(BaseGeoCopilotEngine):
    def __init__(self, geocoder: NominatimGeocoder, poi: OverpassPOI, llm: LLMService):
        super().__init__(llm, prompt_rules=combined_rules("chat"))
        self._geocoder = geocoder
        self._poi = poi

    def _build_facts(self, loc: LatLon) -> Dict:
        lat, lon = loc
        return {
            "location": self._geocoder.reverse(lat, lon),
            "pois": self._poi.around(lat, lon, 30),
        }

    def run(self, loc: LatLon, user_prompt: str) -> str:
        if not user_prompt or not user_prompt.strip():
            user_prompt = default_user_prompt("chat")
        facts = self._build_facts(loc)
        return self._generate(facts, user_prompt)

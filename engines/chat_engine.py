from typing import Tuple, Dict, Optional
from services.llm import OllamaLLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI

LatLon = Tuple[float, float]

class ChatEngine:
    def __init__(
        self,
        geocoder: NominatimGeocoder,
        poi: OverpassPOI,
        llm: OllamaLLMService,
        *,
        system_prompt: Optional[str] = None,
    ):
        self._geocoder = geocoder
        self._poi = poi
        self._llm = llm
        self.system_prompt = system_prompt or (
            "You are GeoCopilot. You receive a verified location and nearby POIs. "
            "Write a compact, helpful summary and a few practical tips. English only."
        )

    def _build_facts(self, loc: LatLon, radius_m: int, user_prompt: str) -> Dict:
        lat, lon = loc
        return {
            "location": self._geocoder.reverse(lat, lon),
            "radius_m": radius_m,
            "pois": self._poi.around(lat, lon, radius_m, 30),
            "user_prompt": user_prompt,
        }

    def run(self, loc: LatLon, radius_m: int, user_prompt: str) -> str:
        facts = self._build_facts(loc, radius_m, user_prompt)
        return self._llm.summarize(self.system_prompt, facts)

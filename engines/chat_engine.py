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
            "You are GeoCopilot, a travel agent that provides traveling tips and planning services. "
            "You receive a verified location and nearby POIs. "
            "If no search radius was specified by the user the default search value is 3000 meters. "
            "Write a compact, helpful summary and a few practical tips. English only."
        )

    def _build_facts(self, loc: LatLon, user_prompt: str) -> Dict:
        lat, lon = loc
        return {
            "location": self._geocoder.reverse(lat, lon),
            "pois": self._poi.around(lat, lon, 30),
            "user_prompt": user_prompt,
        }

    def run(self, loc: LatLon, user_prompt: str) -> str:
        facts = self._build_facts(loc, user_prompt)
        return self._llm.summarize(self.system_prompt, facts)

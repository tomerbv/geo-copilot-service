import os
from typing import Tuple, Dict, Optional
from services.llm import OllamaLLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI

LatLon = Tuple[float, float]

class ChatEngine:
    def __init__(
        self,
        *,
        system_prompt: Optional[str] = None,
        ollama_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        nominatim_url: Optional[str] = None,
        overpass_url: Optional[str] = None,
        http_user_agent: Optional[str] = None,
    ):
        self.system_prompt = system_prompt or (
            "You are GeoCopilot. You receive a verified location and nearby POIs. "
            "Write a compact, helpful summary and a few practical tips. English only."
        )
        ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        llm_model  = llm_model  or os.getenv("LLM_MODEL", "llama3.1:8b")
        nominatim_url = nominatim_url or os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
        overpass_url  = overpass_url  or os.getenv("OVERPASS_URL",  "https://overpass-api.de/api/interpreter")
        http_user_agent = http_user_agent or os.getenv("HTTP_USER_AGENT", "geo-copilot/1.0 (contact: you@example.com)")
        headers = {"User-Agent": http_user_agent}

        self._llm = OllamaLLMService(ollama_url, llm_model)
        self._geocoder = NominatimGeocoder(nominatim_url, headers)
        self._poi = OverpassPOI(overpass_url)

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

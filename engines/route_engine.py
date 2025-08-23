import os
from typing import Tuple, Dict, List, Optional
from services.llm import OllamaLLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI
from services.routing import OSRMRouting, ORSRouting

LatLon = Tuple[float, float]

class RouteEngine:
    def __init__(
        self,
        *,
        system_prompt: Optional[str] = None,
        router_preference: Optional[str] = None,
        ollama_url: Optional[str] = None,
        llm_model: Optional[str] = None,
        nominatim_url: Optional[str] = None,
        overpass_url: Optional[str] = None,
        ors_api_key: Optional[str] = None,
        http_user_agent: Optional[str] = None,
    ):
        self.system_prompt = system_prompt or (
            "You are GeoCopilot. You receive a computed route with names and nearby POIs. "
            "Summarize the drive (distance/time/provider), notable via areas/POIs, and a few tips. English only."
        )
        ollama_url = ollama_url or os.getenv("OLLAMA_URL", "http://localhost:11434")
        llm_model  = llm_model  or os.getenv("LLM_MODEL", "llama3.1:8b")
        nominatim_url = nominatim_url or os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
        overpass_url  = overpass_url  or os.getenv("OVERPASS_URL",  "https://overpass-api.de/api/interpreter")
        http_user_agent = http_user_agent or os.getenv("HTTP_USER_AGENT", "geo-copilot/1.0 (contact: you@example.com)")
        ors_api_key = ors_api_key or os.getenv("ORS_API_KEY", "")
        router_pref = (router_preference or os.getenv("ROUTER", "osrm")).lower()
        headers = {"User-Agent": http_user_agent}

        self._llm = OllamaLLMService(ollama_url, llm_model)
        self._geocoder = NominatimGeocoder(nominatim_url, headers)
        self._poi = OverpassPOI(overpass_url)
        self._router = ORSRouting(ors_api_key) if router_pref == "ors" else OSRMRouting()

    @staticmethod
    def _bbox(points: List[LatLon]):
        lats = [p[0] for p in points]; lons = [p[1] for p in points]
        return min(lats), min(lons), max(lats), max(lons)

    def _via_list(self, points: List[LatLon]) -> List[str]:
        idxs = [0, max(1, len(points)//3), max(2, 2*len(points)//3), len(points)-1]
        seen, via = set(), []
        for i in idxs:
            lat, lon = points[i]
            rg = self._geocoder.reverse(lat, lon)
            city = rg.get("city") or rg.get("state") or rg.get("country")
            if city and city not in seen:
                via.append(city); seen.add(city)
        return via

    def _build_facts(self, start: LatLon, end: LatLon, user_prompt: str) -> Dict:
        s_rg = self._geocoder.reverse(*start)
        e_rg = self._geocoder.reverse(*end)
        route = self._router.route(start, end)
        if not route:
            return {"error": "no_route"}

        min_lat, min_lon, max_lat, max_lon = self._bbox(route["points"])
        pad = 0.05
        pois = self._poi.in_bbox(min_lat - pad, min_lon - pad, max_lat + pad, max_lon + pad, 40)

        return {
            "start": s_rg,
            "end": e_rg,
            "distance_m": route["distance_m"],
            "duration_s": route["duration_s"],
            "provider": route["provider"],
            "via_summary": self._via_list(route["points"]),
            "pois": pois,
            "user_prompt": user_prompt,
        }

    def run(self, start: LatLon, end: LatLon, user_prompt: str) -> str:
        facts = self._build_facts(start, end, user_prompt)
        if facts.get("error") == "no_route":
            return "No drivable route was found between the selected points."
        return self._llm.summarize(self.system_prompt, facts)

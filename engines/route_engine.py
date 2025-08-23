from typing import Tuple, Dict, List, Optional
from services.llm import LLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI
from services.routing import OSRMRouting, ORSRouting
from engines.abstract_engine import BaseGeoCopilotEngine

LatLon = Tuple[float, float]

class RouteEngine(BaseGeoCopilotEngine):
    def __init__(
        self,
        geocoder: NominatimGeocoder,
        poi: OverpassPOI,
        router: OSRMRouting | ORSRouting,
        llm: LLMService,
        *,
        prompt_rules: list[str] | None = None,
    ):
        engine_rules = [
            "You receive a computed driving route with via places and nearby POIs.",
            "Summarize total distance/time and which provider was used.",
            "Mention a few notable via areas/POIs and add practical driving tips.",
        ]
        super().__init__(llm, prompt_rules=(prompt_rules or []) + engine_rules)
        self._geocoder = geocoder
        self._poi = poi
        self._router = router

    def _bbox(self, points: List[LatLon]):
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
        return self._generate(facts)

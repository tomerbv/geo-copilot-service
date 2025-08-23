import os
from typing import Optional
from services.llm import OllamaLLMService
from services.geocoding import NominatimGeocoder
from services.pois import OverpassPOI
from services.routing import OSRMRouting, ORSRouting
from engines.chat_engine import ChatEngine
from engines.route_engine import RouteEngine

class EngineManager:
    """
    Initializes shared services once, then constructs ChatEngine and RouteEngine
    with those instances. Use: manager.chat.run(...), manager.route.run(...).
    """
    def __init__(self, *, router_preference: Optional[str] = None):
        # Shared services (each service reads its own env defaults)
        self.llm = OllamaLLMService()
        self.geocoder = NominatimGeocoder()
        self.poi = OverpassPOI()

        router_pref = (router_preference or os.getenv("ROUTER", "osrm")).lower()
        if router_pref == "ors":
            self.router = ORSRouting()
            if self.router.api_key == "":
                # Fallback to OSRM if ORS key missing
                self.router = OSRMRouting()
        else:
            self.router = OSRMRouting()

        self.chat = ChatEngine(self.geocoder, self.poi, self.llm)
        self.route = RouteEngine(self.geocoder, self.poi, self.router, self.llm)

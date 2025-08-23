from config.config_loader import get_flag
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
    def __init__(self):
        use_ors = bool(int(get_flag("USE_ORS", 0)))
        self.llm = OllamaLLMService()
        self.geocoder = NominatimGeocoder()
        self.poi = OverpassPOI()
        self.router = ORSRouting() if use_ors else OSRMRouting()

        self.chat = ChatEngine(geocoder=self.geocoder, poi=self.poi, llm=self.llm)
        self.route = RouteEngine(geocoder=self.geocoder, poi=self.poi, router=self.router, llm=self.llm)

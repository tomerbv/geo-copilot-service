import os, requests
from typing import List, Dict, Optional

class OverpassPOI:
    def __init__(self, *, url: Optional[str] = None, radius_m: Optional[int] = None):
        self.url = url or os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
        self.radius_m = radius_m or os.getenv("POI_RADIUS_METERS", 3000)

    def around(self, lat: float, lon: float, limit: int) -> List[Dict]:
        q = f"""
        [out:json][timeout:25];
        (
          node["tourism"~"attraction|viewpoint|museum"](around:{self.radius_m},{lat},{lon});
          node["amenity"~"fuel|restaurant|cafe"](around:{self.radius_m},{lat},{lon});
          node["natural"~"beach|peak|spring"](around:{self.radius_m},{lat},{lon});
        );
        out center {limit};
        """
        r = requests.post(self.url, data=q, timeout=30)
        if r.status_code != 200: return []
        out = []
        for e in r.json().get("elements", []):
            if e.get("type") != "node": continue
            tags = e.get("tags", {})
            out.append({"lat": e.get("lat"), "lon": e.get("lon"), "name": tags.get("name"), "tags": tags})
        return out[:limit]

    def in_bbox(self, min_lat, min_lon, max_lat, max_lon, limit: int) -> List[Dict]:
        q = f"""
        [out:json][timeout:25];
        (
          node["tourism"~"attraction|viewpoint|museum"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["amenity"~"fuel|restaurant|cafe"]({min_lat},{min_lon},{max_lat},{max_lon});
          node["natural"~"beach|peak|spring"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center {limit};
        """
        r = requests.post(self.url, data=q, timeout=30)
        if r.status_code != 200: return []
        out = []
        for e in r.json().get("elements", []):
            if e.get("type") != "node": continue
            tags = e.get("tags", {})
            out.append({"lat": e.get("lat"), "lon": e.get("lon"), "name": tags.get("name"), "tags": tags})
        return out[:limit]

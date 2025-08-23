from typing import List, Dict
import requests

class OverpassPOI:
    def __init__(self, url: str):
        self.url = url

    def around(self, lat: float, lon: float, radius_m: int, limit: int) -> List[Dict]:
        q = f"""
        [out:json][timeout:25];
        (
          node["tourism"~"attraction|viewpoint|museum"](around:{radius_m},{lat},{lon});
          node["amenity"~"fuel|restaurant|cafe"](around:{radius_m},{lat},{lon});
          node["natural"~"beach|peak|spring"](around:{radius_m},{lat},{lon});
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

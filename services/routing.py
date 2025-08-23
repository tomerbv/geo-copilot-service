import os, requests, polyline
from typing import Optional, Tuple, Dict, List

LatLon = Tuple[float, float]

class OSRMRouting:
    def route(self, start: LatLon, end: LatLon) -> Optional[Dict]:
        (slat, slon), (elat, elon) = start, end
        url = f"https://router.project-osrm.org/route/v1/driving/{slon},{slat};{elon},{elat}?overview=full&geometries=polyline&steps=false"
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        j = r.json()
        if not j.get("routes"): return None
        rt = j["routes"][0]
        pts = polyline.decode(rt["geometry"])
        return {"distance_m": float(rt["distance"]), "duration_s": float(rt["duration"]), "points": pts, "provider": "osrm"}

class ORSRouting:
    def __init__(self, *, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ORS_API_KEY", "")
    def route(self, start: LatLon, end: LatLon) -> Optional[Dict]:
        if not self.api_key: return None
        body = {"coordinates": [[start[1], start[0]], [end[1], end[0]]]}
        r = requests.post("https://api.openrouteservice.org/v2/directions/driving-car",
                          json=body, headers={"Authorization": self.api_key}, timeout=30)
        r.raise_for_status()
        j = r.json()
        feat = j["features"][0]
        coords = feat["geometry"]["coordinates"]   # [[lon,lat], ...]
        seg = feat["properties"]["segments"][0]
        pts = [(lat, lon) for lon, lat in coords]
        return {"distance_m": float(seg["distance"]), "duration_s": float(seg["duration"]), "points": pts, "provider": "ors"}

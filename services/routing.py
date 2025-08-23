import os, requests, polyline
from typing import Optional, Tuple, Dict, List, Protocol

LatLon = Tuple[float, float]

class RoutingService(Protocol):
    def route(self, start: LatLon, end: LatLon) -> Optional[Dict]: ...

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
        if not self.api_key:
            return None

        body = {
            "coordinates": [[start[1], start[0]], [end[1], end[0]]],
            "instructions": False  # we don't need step-by-step; keeps response small
        }

        url = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"
        r = requests.post(url, json=body, headers={"Authorization": self.api_key}, timeout=30)
        r.raise_for_status()
        j = r.json()

        feat = j["features"][0]
        props = feat.get("properties", {})
        geom = feat.get("geometry", {}) or {}
        coords = geom.get("coordinates", [])  # [[lon, lat], ...]

        # Prefer segments[0] if present; otherwise fallback to summary
        segs = props.get("segments")
        if segs and isinstance(segs, list) and segs:
            dist = float(segs[0].get("distance", 0.0))
            dur = float(segs[0].get("duration", 0.0))
        else:
            summ = props.get("summary", {}) or {}
            dist = float(summ.get("distance", 0.0))
            dur = float(summ.get("duration", 0.0))

        # Convert to (lat, lon) tuples
        pts: List[LatLon] = [(lat, lon) for lon, lat in coords]

        return {
            "distance_m": dist,
            "duration_s": dur,
            "points": pts,
            "provider": "ors",
        }

import os
import json
import requests
import polyline as _polyline

# ---------- Config ----------
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LLM_MODEL  = os.getenv("LLM_MODEL", "llama3.1:8b")

ROUTER     = os.getenv("ROUTER", "osrm").lower()   # "osrm" | "ors"
ORS_API_KEY = os.getenv("ORS_API_KEY", "")

NOMINATIM_URL = os.getenv("NOMINATIM_URL", "https://nominatim.openstreetmap.org")
OVERPASS_URL  = os.getenv("OVERPASS_URL",  "https://overpass-api.de/api/interpreter")
HTTP_UA       = os.getenv("HTTP_USER_AGENT", "geo-copilot/1.0 (contact: you@example.com)")

HEADERS = {"User-Agent": HTTP_UA}

# ---------- LLM prompts ----------
SYSTEM_ROUTE = (
    "You are GeoCopilot. You receive verified routing facts and POIs.\n"
    "Do NOT invent coordinates, distances, or times. If data is missing, say so.\n"
    "Return STRICT JSON with keys: summary, highlights, practical, border_notes.\n"
    "English only."
)

SYSTEM_POINT = (
    "You are GeoCopilot. You receive a verified location and nearby POIs.\n"
    "Return STRICT JSON with keys: summary, highlights, practical, border_notes.\n"
    "English only."
)

def _ollama_generate(system_prompt: str, facts: dict) -> dict:
    """Call Ollama and return a parsed JSON object; fall back to a minimal structure."""
    prompt = (
        f"{system_prompt}\n\n"
        "Use only the provided JSON FACTS.\n"
        "- summary: 1–2 sentences.\n"
        "- highlights: list of {name, why, approx_km_from_start?}.\n"
        "- practical: list of short tips.\n"
        "- border_notes: null or short string.\n\n"
        f"FACTS = {json.dumps(facts, ensure_ascii=False)}\n\n"
        "Return ONLY the JSON object."
    )
    r = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": LLM_MODEL, "prompt": prompt, "stream": False},
        timeout=120,
    )
    r.raise_for_status()
    txt = r.json().get("response", "").strip()
    try:
        return json.loads(txt)
    except Exception:
        # Best-effort fallback
        return {"summary": (txt[:400] or "No summary."), "highlights": [], "practical": [], "border_notes": None}

def _as_text(narr: dict) -> str:
    """Convert the structured narrative to a single string for the client."""
    parts = []
    if narr.get("summary"):
        parts.append(narr["summary"].strip())

    hl = narr.get("highlights") or []
    if hl:
        parts.append("\nHighlights:")
        for h in hl[:6]:
            name = (h.get("name") or "Point of interest").strip()
            why = (h.get("why") or "").strip()
            km  = h.get("approx_km_from_start")
            tail = f" (~{km} km from start)" if isinstance(km, (int, float)) else ""
            bullet = f"• {name}: {why}{tail}".strip().rstrip(":")
            parts.append(bullet)

    pr = narr.get("practical") or []
    if pr:
        parts.append("\nPractical tips:")
        for tip in pr[:6]:
            parts.append(f"• {tip}")

    bn = narr.get("border_notes")
    if bn:
        parts.append(f"\nBorder notes: {bn}")

    return "\n".join(parts).strip()

# ---------- HTTP helpers ----------
def _get(url: str, **kwargs):
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    return requests.get(url, headers=headers, timeout=kwargs.pop("timeout", 20), **kwargs)

def _post(url: str, **kwargs):
    headers = {**HEADERS, **kwargs.pop("headers", {})}
    return requests.post(url, headers=headers, timeout=kwargs.pop("timeout", 30), **kwargs)

# ---------- Geocoding ----------
def reverse_geocode(lat: float, lon: float) -> dict:
    r = _get(f"{NOMINATIM_URL}/reverse", params={"lat": lat, "lon": lon, "format": "jsonv2"})
    r.raise_for_status()
    j = r.json()
    addr = j.get("address", {})
    return {
        "display_name": j.get("display_name"),
        "road": addr.get("road"),
        "city": addr.get("city") or addr.get("town") or addr.get("village"),
        "state": addr.get("state"),
        "country": addr.get("country"),
        "country_code": addr.get("country_code"),
        "lat": float(j.get("lat", lat)),
        "lon": float(j.get("lon", lon)),
    }

# ---------- Routing ----------
OSRM_ROUTE = "https://router.project-osrm.org/route/v1/driving/{},{};{},{}?overview=full&geometries=polyline&steps=false"

def _route_osrm(a: dict, b: dict) -> dict | None:
    url = OSRM_ROUTE.format(a["lon"], a["lat"], b["lon"], b["lat"])
    r = _get(url)
    r.raise_for_status()
    j = r.json()
    if not j.get("routes"):
        return None
    rt = j["routes"][0]
    pts = _polyline.decode(rt["geometry"])  # [(lat, lon), ...]
    return {"distance_m": float(rt["distance"]), "duration_s": float(rt["duration"]), "points": pts, "provider": "osrm"}

def _route_ors(a: dict, b: dict) -> dict | None:
    if not ORS_API_KEY:
        return None
    body = {"coordinates": [[a["lon"], a["lat"]], [b["lon"], b["lat"]]]}
    r = _post("https://api.openrouteservice.org/v2/directions/driving-car",
              json=body, headers={"Authorization": ORS_API_KEY})
    r.raise_for_status()
    j = r.json()
    feat = j["features"][0]
    coords = feat["geometry"]["coordinates"]   # [[lon,lat], ...]
    seg = feat["properties"]["segments"][0]
    pts = [(lat, lon) for lon, lat in coords]
    return {"distance_m": float(seg["distance"]), "duration_s": float(seg["duration"]), "points": pts, "provider": "ors"}

# ---------- POIs ----------
def _bbox(points):
    lats = [p[0] for p in points]; lons = [p[1] for p in points]
    return min(lats), min(lons), max(lats), max(lons)

def _pois_bbox(min_lat, min_lon, max_lat, max_lon, limit=40):
    q = f"""
    [out:json][timeout:25];
    (
      node["tourism"~"attraction|viewpoint|museum"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["amenity"~"fuel|restaurant|cafe"]({min_lat},{min_lon},{max_lat},{max_lon});
      node["natural"~"beach|peak|spring"]({min_lat},{min_lon},{max_lat},{max_lon});
    );
    out center {limit};
    """
    r = _post(OVERPASS_URL, data=q)
    if r.status_code != 200:
        return []
    els = r.json().get("elements", [])
    out = []
    for e in els:
        if e.get("type") != "node": continue
        tags = e.get("tags", {})
        out.append({"lat": e.get("lat"), "lon": e.get("lon"), "name": tags.get("name"), "tags": tags})
    return out[:limit]

def _pois_around(lat: float, lon: float, radius_m=3000, limit=30):
    q = f"""
    [out:json][timeout:25];
    (
      node["tourism"~"attraction|viewpoint|museum"](around:{radius_m},{lat},{lon});
      node["amenity"~"fuel|restaurant|cafe"](around:{radius_m},{lat},{lon});
      node["natural"~"beach|peak|spring"](around:{radius_m},{lat},{lon});
    );
    out center {limit};
    """
    r = _post(OVERPASS_URL, data=q)
    if r.status_code != 200:
        return []
    els = r.json().get("elements", [])
    out = []
    for e in els:
        if e.get("type") != "node": continue
        tags = e.get("tags", {})
        out.append({"lat": e.get("lat"), "lon": e.get("lon"), "name": tags.get("name"), "tags": tags})
    return out[:limit]

# ---------- Public API used by app.py ----------
def chat_recommendation(location: dict, user_prompt: str, radius_m: int = 3000) -> str:
    """Single-point: reverse geocode + nearby POIs → LLM JSON → text."""
    lat, lon = location["lat"], location["lon"]
    loc = reverse_geocode(lat, lon)
    pois = _pois_around(lat, lon, radius_m=radius_m, limit=30)
    facts = {
        "location": loc,
        "radius_m": radius_m,
        "pois": pois,
        "user_prompt": user_prompt
    }
    narr = _ollama_generate(SYSTEM_POINT, facts)
    return _as_text(narr)

def route_recommendation(start: dict, end: dict, user_prompt: str) -> str:
    """A→B: route + names + POIs → LLM JSON → text."""
    start_rg = reverse_geocode(start["lat"], start["lon"])
    end_rg   = reverse_geocode(end["lat"],   end["lon"])

    route = _route_ors(start, end) or _route_osrm(start, end)
    if not route:
        return "No drivable route was found between the selected points."

    # Build a loose corridor bbox for POIs
    min_lat, min_lon, max_lat, max_lon = _bbox(route["points"])
    pad = 0.05
    pois = _pois_bbox(min_lat - pad, min_lon - pad, max_lat + pad, max_lon + pad, limit=40)

    # Lite via summary: sample a few points and reverse geocode them
    idxs = [0, max(1, len(route["points"])//3), max(2, 2*len(route["points"])//3), len(route["points"]) - 1]
    via = []
    seen = set()
    for i in idxs:
        lat, lon = route["points"][i]
        rg = reverse_geocode(lat, lon)
        city = rg.get("city") or rg.get("state") or rg.get("country")
        if city and city not in seen:
            via.append(city); seen.add(city)

    facts = {
        "start": start_rg,
        "end": end_rg,
        "distance_m": route["distance_m"],
        "duration_s": route["duration_s"],
        "via_summary": via,
        "pois": pois,
        "user_prompt": user_prompt,
    }
    narr = _ollama_generate(SYSTEM_ROUTE, facts)
    return _as_text(narr)

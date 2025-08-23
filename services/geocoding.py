from typing import Dict
import requests

class NominatimGeocoder:

    def __init__(self, base_url: str, headers: Dict[str, str]):
        self.base_url, self.headers = base_url, headers

    def reverse(self, lat: float, lon: float) -> Dict:
        r = requests.get(f"{self.base_url}/reverse",
                         params={"lat": lat, "lon": lon, "format": "jsonv2"},
                         headers=self.headers, timeout=20)
        r.raise_for_status()
        j = r.json(); addr = j.get("address", {})
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

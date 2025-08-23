from __future__ import annotations
import json, os
from typing import Dict, List, Any

def _load_config() -> Dict[str, Any]:
    # Path: CONFIG_FILE env or default to config/config.json
    path = os.getenv("CONFIG_FILE") or os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(path):
        return {"USE_ORS": 0, "prompts": {"base": [], "chat": [], "route": []}}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # minimal normalization
        prompts = data.get("prompts", {})
        return {
            "USE_ORS": data.get("USE_ORS", 0),
            "prompts": {
                "base": list(prompts.get("base", [])),
                "chat": list(prompts.get("chat", [])),
                "route": list(prompts.get("route", [])),
            },
        }
    except Exception:
        return {"USE_ORS": 0, "prompts": {"base": [], "chat": [], "route": []}}

_CFG = _load_config()

def get_flag(name: str, default: Any = None) -> Any:
    """Read a config flag, allowing ENV override if present."""
    # ENV takes precedence if set explicitly
    if name in os.environ:
        v = os.getenv(name)
        if v is None:
            return default
        # try int/bool parsing for convenience
        if v.isdigit():
            return int(v)
        if v.lower() in {"true", "false"}:
            return v.lower() == "true"
        return v
    return _CFG.get(name, default)

def base_rules() -> List[str]:
    return list(_CFG["prompts"]["base"])

def engine_rules(name: str) -> List[str]:
    return list(_CFG["prompts"].get(name, []))

def combined_rules(name: str) -> List[str]:
    rules = base_rules() + engine_rules(name)
    return rules

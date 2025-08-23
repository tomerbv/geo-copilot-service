from __future__ import annotations
import json, os
from typing import Dict, List, Any

def _load_config() -> Dict[str, Any]:
    path = os.getenv("CONFIG_FILE") or os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(path):
        return {
            "USE_ORS": False,
            "prompts": {"base": [], "chat": [], "route": []},
            "default_user_prompts": {"chat": "", "route": ""}
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        prompts = data.get("prompts", {})
        return {
            "USE_ORS": bool(data.get("USE_ORS", False)),
            "prompts": {
                "base": list(prompts.get("base", [])),
                "chat": list(prompts.get("chat", [])),
                "route": list(prompts.get("route", [])),
            },
            "default_user_prompts": dict(data.get("default_user_prompts", {})),
        }
    except Exception:
        return {
            "USE_ORS": False,
            "prompts": {"base": [], "chat": [], "route": []},
            "default_user_prompts": {"chat": "", "route": ""}
        }

_CFG = _load_config()

def get_flag(name: str, default: Any = None) -> Any:
    if name in os.environ:
        v = os.getenv(name)
        if v is None:
            return default
        if v.lower() in {"true", "1", "yes"}:
            return True
        if v.lower() in {"false", "0", "no"}:
            return False
        return v
    return _CFG.get(name, default)

def base_rules() -> List[str]:
    return list(_CFG["prompts"]["base"])

def engine_rules(name: str) -> List[str]:
    return list(_CFG["prompts"].get(name, []))

def combined_rules(name: str) -> List[str]:
    """Merge base rules with engine-specific rules."""
    return base_rules() + engine_rules(name)

def default_user_prompt(engine_name: str) -> str:
    return _CFG["default_user_prompts"].get(engine_name, "")

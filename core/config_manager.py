import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime


CONFIG_DIR = Path.home() / ".warroom"
CONFIG_FILE = CONFIG_DIR / "config.json"
PROJECTS_FILE = CONFIG_DIR / "projects.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

DEFAULTS = {
    "output_format": "rich",
    "default_port": 8080,
    "editor": "",
    "max_recent_projects": 10,
    "max_history": 100,
}


def _ensure_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_json(path: Path, data: Any):
    _ensure_dir()
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def get_config() -> dict:
    cfg = {**DEFAULTS, **_load_json(CONFIG_FILE)}
    return cfg


def set_config(key: str, value: Any) -> dict:
    cfg = _load_json(CONFIG_FILE)
    cfg[key] = value
    _save_json(CONFIG_FILE, cfg)
    return {key: value}


def get_projects() -> List[dict]:
    data = _load_json(PROJECTS_FILE)
    return data.get("projects", [])


def add_project(name: str, path: str, description: str = "") -> dict:
    projects = get_projects()
    existing = next((p for p in projects if p["name"] == name), None)
    if existing:
        existing["path"] = path
        existing["description"] = description
        existing["updated_at"] = datetime.now().isoformat()
    else:
        projects.append({
            "name": name,
            "path": path,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        })
    max_proj = get_config().get("max_recent_projects", 10)
    _save_json(PROJECTS_FILE, {"projects": projects[-max_proj:]})
    return projects


def remove_project(name: str) -> bool:
    projects = get_projects()
    filtered = [p for p in projects if p["name"] != name]
    if len(filtered) == len(projects):
        return False
    _save_json(PROJECTS_FILE, {"projects": filtered})
    return True


def add_history(cmd: str):
    hist = _load_json(HISTORY_FILE)
    entries = hist.get("history", [])
    if not entries or entries[-1] != cmd:
        entries.append(cmd)
    max_h = get_config().get("max_history", 100)
    _save_json(HISTORY_FILE, {"history": entries[-max_h:]})

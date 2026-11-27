"""Read-only standard Antigravity path discovery across Windows, macOS, and Linux."""

from __future__ import annotations

import os
import platform
from pathlib import Path
from typing import Mapping


def detect_antigravity_paths(
    system: str | None = None,
    home: Path | None = None,
    env: Mapping[str, str] | None = None,
) -> dict[str, dict[str, object]]:
    """Return standard Antigravity IDE, CLI, and skill paths with existence flags."""
    sys_name = system or platform.system()
    user_home = home or Path.home()
    env_map = env if env is not None else os.environ

    if sys_name == "Windows":
        appdata = Path(env_map.get("APPDATA") or (user_home / "AppData" / "Roaming"))
        ide_settings = appdata / "Antigravity" / "User" / "settings.json"
        app_dir = appdata / "Antigravity"
    elif sys_name == "Darwin":
        app_dir = user_home / "Library" / "Application Support" / "Antigravity"
        ide_settings = app_dir / "User" / "settings.json"
    else:
        xdg_cfg = Path(env_map.get("XDG_CONFIG_HOME") or (user_home / ".config"))
        app_dir = xdg_cfg / "Antigravity"
        ide_settings = app_dir / "User" / "settings.json"

    candidates = {
        "ideAppDir": app_dir,
        "ideSettings": ide_settings,
        "cliSettings": user_home / ".gemini" / "antigravity-cli" / "settings.json",
        "globalSkillsDir": user_home / ".gemini" / "antigravity" / "skills",
        "agentsSkillsDir": user_home / ".agents" / "skills",
    }
    return {
        key: {"path": str(path), "exists": path.exists()}
        for key, path in candidates.items()
    }

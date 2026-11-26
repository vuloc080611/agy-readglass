"""Schema and hygiene validator for Clearframe presets and theme packs."""

from __future__ import annotations

import re
from typing import Any

REQUIRED_FIELDS: dict[str, type | tuple[type, ...]] = {
    "concept": str,
    "primary": str,
    "secondary": str,
    "glow": str,
    "secondaryGlow": str,
    "overlayRgb": (str, list),
    "textColor": str,
    "uiTextColor": str,
    "uiMutedColor": str,
    "bg": str,
    "frameBg": str,
    "borderColor": str,
    "innerBorder": str,
    "sidebarBg": str,
    "sidebarHoverBg": str,
    "sidebarEnhanceText": bool,
    "aiCardBg": str,
    "aiCardBorder": str,
    "headerBg": str,
    "headerBorder": str,
    "unifiedGlass": bool,
    "btnBg": str,
    "inputGlassBg": str,
    "inputCardBg": str,
    "modalBg": str,
    "modalHeaderBg": str,
    "cardBg": str,
    "cardSelectedBg": str,
    "pureBg": str,
    "wallpaper": str,
    "clearBackdrop": bool,
    "isOrnament": bool,
    "isLight": bool,
    "pillBg": str,
    "pillTextColor": str,
    "pillBorder": str,
    "pillHoverBg": str,
}

ORNAMENT_FIELDS: dict[str, type | tuple[type, ...]] = {
    "sticker": str,
    "stickerW": (int, float),
    "stickerH": (int, float),
    "stickerTop": (int, float),
    "stickerRight": (int, float),
}

_FORBIDDEN_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"backdrop-filter", re.IGNORECASE), "CSS backdrop-filter is forbidden in Clearframe presets"),
    (re.compile(r"\bWLOP\b", re.IGNORECASE), "Third-party WLOP asset reference is forbidden"),
    (re.compile(r"[A-Za-z]:\\Users\\", re.IGNORECASE), "Absolute Windows user path is forbidden"),
    (re.compile(r"/(?:Users|home)/[^/\s\"']+", re.IGNORECASE), "Absolute Unix home path is forbidden"),
]


def validate_preset_schema(name: str, preset: Any, check_forbidden: bool = True) -> list[str]:
    """Validate required fields, types, and forbidden patterns in one preset object."""
    issues: list[str] = []
    if not isinstance(preset, dict):
        return [f"Preset {name!r} must be a JSON object"]

    for field, expected_type in REQUIRED_FIELDS.items():
        if field not in preset:
            issues.append(f"Missing required field: {field}")
        elif not isinstance(preset[field], expected_type):
            issues.append(f"Field {field} has wrong type: {type(preset[field]).__name__}")

    if preset.get("isOrnament") is True:
        for field, expected_type in ORNAMENT_FIELDS.items():
            if field not in preset:
                issues.append(f"Ornament theme missing field: {field}")
            elif not isinstance(preset[field], expected_type):
                issues.append(f"Ornament field {field} has wrong type: {type(preset[field]).__name__}")

    if preset.get("clearBackdrop") is False:
        issues.append("clearBackdrop must be true for Clearframe presets")

    if check_forbidden:
        for key, value in preset.items():
            if isinstance(value, str):
                for pat, msg in _FORBIDDEN_PATTERNS:
                    if pat.search(value):
                        issues.append(f"Field {key}: {msg}")

    return issues


def validate_themes_collection(data: Any) -> list[str]:
    """Validate a complete themes.json structure (flat map with Deep Ink optional check)."""
    if not isinstance(data, dict) or not data:
        return ["themes.json must be a non-empty JSON object keyed by theme name"]
    issues: list[str] = []
    for name, preset in data.items():
        for err in validate_preset_schema(name, preset):
            issues.append(f"[{name}] {err}")
    return issues

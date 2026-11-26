"""Generate matching VS Code / Antigravity IDE workbench.colorCustomizations from a Clearframe preset."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
for _cand in (str(_HERE), str(_REPO_ROOT / "src")):
    if _cand not in sys.path:
        sys.path.insert(0, _cand)

try:
    from contrast_lib import (  # type: ignore[import-not-found]
        blend_over,
        contrast_ratio,
        extract_color_stops,
        hex_to_rgb,
        oklch_to_srgb,
        parse_overlay_rgb,
        rgb_to_hex,
        srgb_to_oklch,
    )
except ImportError:
    from clearframe_core.contrast_lib import (
        blend_over,
        contrast_ratio,
        extract_color_stops,
        hex_to_rgb,
        oklch_to_srgb,
        parse_overlay_rgb,
        rgb_to_hex,
        srgb_to_oklch,
    )


def _solid_hex(css_val: str, overlay: tuple[float, float, float]) -> str:
    stops = extract_color_stops(css_val)
    return rgb_to_hex(blend_over(stops[0], overlay))


def _visible_scrollbar_hex(editor_bg_hex: str, ink_hex: str, min_ratio: float = 3.0) -> tuple[str, str, str]:
    """Compute WCAG 1.4.11 visible scrollbar slider tokens (>= 3:1 on hover, crisp idle)."""
    bg = hex_to_rgb(editor_bg_hex)
    ink = hex_to_rgb(ink_hex)
    for alpha in (0.34, 0.42, 0.50, 0.58):
        blended = blend_over((ink[0], ink[1], ink[2], alpha), bg)
        if contrast_ratio(blended, bg) >= min_ratio:
            idle_hex = f"{ink_hex}{round(alpha * 255):02x}"
            hover_hex = f"{ink_hex}{round(min(0.85, alpha + 0.18) * 255):02x}"
            active_hex = f"{ink_hex}{round(min(0.95, alpha + 0.30) * 255):02x}"
            return idle_hex, hover_hex, active_hex
    return f"{ink_hex}66", f"{ink_hex}99", f"{ink_hex}cc"


def build_ide_customizations(
    preset: dict[str, Any],
    cvd_safe: bool = False,
    scope_theme: str | None = None,
) -> dict[str, Any]:
    """Build workbench.colorCustomizations JSON mapped from a Clearframe preset."""
    is_light = bool(preset.get("isLight", False))
    overlay = parse_overlay_rgb(preset["overlayRgb"])

    editor_bg = _solid_hex(preset["aiCardBg"], overlay)
    sidebar_bg = _solid_hex(preset["sidebarBg"], overlay)
    header_bg = _solid_hex(preset["headerBg"], overlay)
    modal_bg = _solid_hex(preset["modalBg"], overlay)
    tab_active = _solid_hex(preset["btnBg"], overlay)
    sel_bg = _solid_hex(preset["cardSelectedBg"], overlay)
    fg = rgb_to_hex(hex_to_rgb(preset["uiTextColor"]))
    muted = rgb_to_hex(hex_to_rgb(preset.get("uiMutedColor") or fg))
    primary = rgb_to_hex(hex_to_rgb(preset["primary"]))

    L_bg, C_bg, h_bg = srgb_to_oklch(hex_to_rgb(editor_bg))
    border_l = L_bg - 0.14 if is_light else L_bg + 0.14
    border_hex = rgb_to_hex(oklch_to_srgb(border_l, min(C_bg, 0.025), h_bg))

    sb_idle, sb_hover, sb_active = _visible_scrollbar_hex(editor_bg, fg, min_ratio=3.0)

    if cvd_safe:
        # Blue (inserted) vs Amber/Orange (removed): safe for Deuteranopia & Protanopia
        ins_bg = "#3b82f62e"
        del_bg = "#e08b3a30"
    else:
        ins_bg = "#3ecf8e26" if not is_light else "#1f6b4524"
        del_bg = "#d96b6b28" if not is_light else "#b83b3b24"

    colors: dict[str, str] = {
        "focusBorder": primary,
        "contrastBorder": border_hex,
        "editor.background": editor_bg,
        "editor.foreground": fg,
        "editor.lineHighlightBackground": sel_bg if is_light else modal_bg,
        "editor.selectionBackground": f"{primary}38",
        "editorCursor.foreground": primary,
        "sideBar.background": sidebar_bg,
        "sideBar.foreground": fg,
        "sideBarTitle.foreground": fg,
        "sideBar.border": border_hex,
        "activityBar.background": header_bg,
        "activityBar.foreground": fg,
        "activityBar.inactiveForeground": muted,
        "editorGroupHeader.tabsBackground": header_bg,
        "tab.activeBackground": tab_active,
        "tab.activeForeground": fg,
        "tab.activeBorderTop": primary,
        "tab.inactiveBackground": header_bg,
        "tab.inactiveForeground": muted,
        "tab.border": border_hex,
        "statusBar.background": header_bg,
        "statusBar.foreground": fg,
        "statusBar.border": border_hex,
        "panel.background": sidebar_bg,
        "panel.border": border_hex,
        "terminal.background": editor_bg,
        "terminal.foreground": fg,
        "scrollbarSlider.background": sb_idle,
        "scrollbarSlider.hoverBackground": sb_hover,
        "scrollbarSlider.activeBackground": sb_active,
        "diffEditor.insertedTextBackground": ins_bg,
        "diffEditor.removedTextBackground": del_bg,
        "diffEditor.border": border_hex,
    }

    if scope_theme:
        return {"workbench.colorCustomizations": {f"[{scope_theme}]": colors}}
    return {
        "workbench.colorCustomizations": colors,
        "editor.lineHeight": 1.6,
    }


def _load_single_preset(preset_name: str | None, file_path: Path | None) -> tuple[str, dict[str, Any]]:
    target = file_path or (_REPO_ROOT / "themes" / "themes.json")
    raw = json.loads(target.read_text(encoding="utf-8"))
    if "name" in raw and "bg" in raw:
        return raw["name"], {k: v for k, v in raw.items() if k != "name"}
    presets = raw["presets"] if ("presets" in raw and isinstance(raw["presets"], dict)) else raw
    if preset_name:
        if preset_name not in presets:
            raise KeyError(f"Preset {preset_name!r} not found in {target}")
        return preset_name, presets[preset_name]
    first = next(iter(presets))
    return first, presets[first]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export matching Antigravity IDE / VS Code colorCustomizations")
    parser.add_argument("--preset", default=None, help="Preset name in themes/themes.json (default: first)")
    parser.add_argument("--file", type=Path, default=None, help="Path to pack.json or themes.json")
    parser.add_argument("--cvd-safe", action="store_true", help="Use Blue/Amber diff highlights for CVD")
    parser.add_argument("--scope", default=None, help="Optional VS Code theme scope name, e.g. 'Default Dark Modern'")
    parser.add_argument("--apply", type=Path, default=None, help="Safely merge into target settings.json (with .bak)")
    args = parser.parse_args(argv)

    try:
        name, body = _load_single_preset(args.preset, args.file)
    except (OSError, KeyError, json.JSONDecodeError) as exc:
        print(f"Error loading preset: {exc}", file=sys.stderr)
        return 1

    payload = build_ide_customizations(body, cvd_safe=args.cvd_safe, scope_theme=args.scope)

    if args.apply:
        if args.apply.exists():
            try:
                existing = json.loads(args.apply.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                print(
                    f"Refusing to overwrite {args.apply}: file contains comments or invalid JSON ({exc}). "
                    "Paste the generated block manually.",
                    file=sys.stderr,
                )
                return 1
            bak = args.apply.with_suffix(args.apply.suffix + ".bak")
            shutil.copy2(args.apply, bak)
            print(f"Backup created: {bak}")
        else:
            existing = {}

        existing_wc = existing.get("workbench.colorCustomizations", {})
        if not isinstance(existing_wc, dict):
            existing_wc = {}
        existing_wc.update(payload["workbench.colorCustomizations"])
        existing["workbench.colorCustomizations"] = existing_wc
        args.apply.parent.mkdir(parents=True, exist_ok=True)
        args.apply.write_text(json.dumps(existing, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"Applied Clearframe IDE sync ({name}) into {args.apply}")
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

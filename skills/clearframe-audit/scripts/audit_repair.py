"""Audit and minimally repair any existing agy-theme themes.json or pack file.

Preserves user's wallpaper, accent colors, and aesthetic while elevating failing
contrast surfaces, muted inks, glow glare, or unsafe wallpaper opacities to WCAG AA/AAA.
"""

from __future__ import annotations

import argparse
import copy
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
        audit_preset,
        clamp,
        contrast_ratio,
        evaluate_surface_stops,
        extract_alpha,
        extract_color_stops,
        hex_to_rgb,
        oklch_to_srgb,
        parse_overlay_rgb,
        relative_luminance,
        rgb_to_hex,
        srgb_to_oklch,
    )
except ImportError:
    from clearframe_core.contrast_lib import (
        audit_preset,
        clamp,
        contrast_ratio,
        evaluate_surface_stops,
        extract_alpha,
        extract_color_stops,
        hex_to_rgb,
        oklch_to_srgb,
        parse_overlay_rgb,
        relative_luminance,
        rgb_to_hex,
        srgb_to_oklch,
    )


def _format_rgba(r: float, g: float, b: float, a: float) -> str:
    return f"rgba({round(r)}, {round(g)}, {round(b)}, {clamp(a, 0.0, 1.0):.2f})"


def _bump_surface_alpha(css_value: str, min_alpha: float) -> str:
    stops = extract_color_stops(css_value)
    if len(stops) == 1 and "gradient" not in css_value.lower():
        r, g, b, a = stops[0]
        return _format_rgba(r, g, b, max(a, min_alpha))
    # Replace rgba stops inline if gradient
    r, g, b, a = stops[0]
    return _format_rgba(r, g, b, max(a, min_alpha))


def _step_surface_contrast(
    preset: dict[str, Any],
    field: str,
    fg_rgb: tuple[float, float, float],
    overlay: tuple[float, float, float],
    target_ratio: float,
    is_light: bool,
) -> list[str]:
    changes: list[str] = []
    if field not in preset:
        return changes

    val = preset[field]
    ratio, _, _ = evaluate_surface_stops(fg_rgb, val, overlay)
    if ratio >= target_ratio:
        return changes

    stops = extract_color_stops(val)
    if len(stops) == 1 and "gradient" not in val.lower():
        r, g, b, a = stops[0]
        # First step opacity upward cleanly
        cur_a = a
        while cur_a < 0.98:
            cur_a = min(0.98, cur_a + 0.04)
            candidate = _format_rgba(r, g, b, cur_a)
            new_r, _, _ = evaluate_surface_stops(fg_rgb, candidate, overlay)
            if new_r >= target_ratio:
                preset[field] = candidate
                changes.append(f"{field}: opacity {a:.2f} -> {cur_a:.2f}")
                return changes
        # If still failing at alpha=0.98, shift surface lightness toward dark/light anchor
        L, C, h = srgb_to_oklch((r, g, b))
        for _ in range(14):
            L = clamp(L + (0.05 if is_light else -0.05), 0.12 if not is_light else 0.85, 0.99)
            nr, ng, nb = oklch_to_srgb(L, min(C, 0.05), h)
            candidate = _format_rgba(nr, ng, nb, 0.96)
            new_r, _, _ = evaluate_surface_stops(fg_rgb, candidate, overlay)
            if new_r >= target_ratio:
                preset[field] = candidate
                changes.append(f"{field}: adjusted surface tone & opacity -> 0.96")
                return changes

    # Gradient / fallback: darken or lighten base card cleanly
    fallback_rgb = (255.0, 252.0, 246.0) if is_light else (16.0, 18.0, 22.0)
    preset[field] = _format_rgba(fallback_rgb[0], fallback_rgb[1], fallback_rgb[2], 0.96)
    changes.append(f"{field}: stabilized gradient to readable solid glass")
    return changes


def repair_preset(name: str, raw_preset: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Return a minimally repaired copy of preset and human-readable list of fixes."""
    p = copy.deepcopy(raw_preset)
    changes: list[str] = []
    is_light = bool(p.get("isLight", False))

    if "overlayRgb" not in p:
        p["overlayRgb"] = "244, 241, 234" if is_light else "12, 14, 18"
        changes.append("Added missing overlayRgb")
    overlay = parse_overlay_rgb(p["overlayRgb"])

    # Fill minimal schema defaults if inspecting an older upstream themes.json
    default_ink = "#1c1915" if is_light else "#ebe7df"
    if "textColor" not in p:
        p["textColor"] = default_ink
        changes.append(f"Set missing textColor -> {default_ink}")
    if "uiTextColor" not in p:
        p["uiTextColor"] = p["textColor"]
        changes.append(f"Set missing uiTextColor -> {p['uiTextColor']}")

    # Ensure primary ink luminance meets dark/light requirement
    t_rgb = hex_to_rgb(p["textColor"])
    ui_rgb = hex_to_rgb(p["uiTextColor"])
    if (not is_light and relative_luminance(t_rgb) < 0.70) or (is_light and relative_luminance(t_rgb) > 0.18):
        p["textColor"] = default_ink
        t_rgb = hex_to_rgb(default_ink)
        changes.append(f"Adjusted textColor -> {default_ink} for luminance gate")
    if (not is_light and relative_luminance(ui_rgb) < 0.70) or (is_light and relative_luminance(ui_rgb) > 0.18):
        p["uiTextColor"] = default_ink
        ui_rgb = hex_to_rgb(default_ink)
        changes.append(f"Adjusted uiTextColor -> {default_ink} for luminance gate")

    # Clamp glow alpha <= 0.18
    for g_field in ("glow", "secondaryGlow"):
        if g_field in p:
            alpha = extract_alpha(p[g_field])
            if alpha > 0.18:
                r, g, b, _ = extract_color_stops(p[g_field])[0]
                p[g_field] = _format_rgba(r, g, b, 0.16)
                changes.append(f"{g_field}: clamped alpha {alpha:.2f} -> 0.16")

    # Enforce wallpaper safeguards
    if str(p.get("wallpaper", "") or "").strip():
        if p.get("sidebarEnhanceText") is not True:
            p["sidebarEnhanceText"] = True
            changes.append("Wallpaper detected: enabled sidebarEnhanceText=true")
        if "sidebarBg" in p and extract_alpha(p["sidebarBg"]) < 0.82:
            p["sidebarBg"] = _bump_surface_alpha(p["sidebarBg"], 0.84)
            changes.append("Wallpaper detected: raised sidebarBg alpha >= 0.84")
        if "aiCardBg" in p and extract_alpha(p["aiCardBg"]) < 0.84:
            p["aiCardBg"] = _bump_surface_alpha(p["aiCardBg"], 0.86)
            changes.append("Wallpaper detected: raised aiCardBg alpha >= 0.86")

    # Repair surfaces below AA / AAA
    for field in ("sidebarBg", "aiCardBg", "headerBg", "btnBg", "inputGlassBg", "cardBg", "cardSelectedBg"):
        if field in p:
            changes.extend(_step_surface_contrast(p, field, ui_rgb, overlay, 4.5, is_light))

    for field in ("modalBg", "modalHeaderBg"):
        if field in p:
            changes.extend(_step_surface_contrast(p, field, ui_rgb, overlay, 7.0, is_light))

    for field in ("bg", "inputCardBg"):
        if field in p:
            changes.extend(_step_surface_contrast(p, field, t_rgb, overlay, 4.5, is_light))

    if "pillBg" in p:
        pill_ink = hex_to_rgb(p.get("pillTextColor") or p["uiTextColor"])
        r_pill, _, _ = evaluate_surface_stops(pill_ink, p["pillBg"], overlay)
        if r_pill < 4.5:
            p["pillTextColor"] = p["uiTextColor"]
            changes.extend(_step_surface_contrast(p, "pillBg", ui_rgb, overlay, 4.5, is_light))
            changes.append(f"pillTextColor aligned to {p['uiTextColor']}")

    # Repair uiMutedColor if present and below 4.5
    if p.get("uiMutedColor") and "aiCardBg" in p and "sidebarBg" in p:
        mu_rgb = hex_to_rgb(p["uiMutedColor"])
        _, _, ai_blend = evaluate_surface_stops(ui_rgb, p["aiCardBg"], overlay)
        _, _, sb_blend = evaluate_surface_stops(ui_rgb, p["sidebarBg"], overlay)
        if contrast_ratio(mu_rgb, ai_blend) < 4.5 or contrast_ratio(mu_rgb, sb_blend) < 4.5:
            L, C, h = srgb_to_oklch(mu_rgb)
            for _ in range(15):
                L = clamp(L + (-0.04 if is_light else 0.04), 0.18 if is_light else 0.55, 0.90)
                cand = oklch_to_srgb(L, min(C, 0.025), h)
                if contrast_ratio(cand, ai_blend) >= 4.7 and contrast_ratio(cand, sb_blend) >= 4.7:
                    p["uiMutedColor"] = rgb_to_hex(cand)
                    changes.append(f"uiMutedColor adjusted -> {p['uiMutedColor']}")
                    break

    return p, changes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit and minimally repair an existing themes.json")
    parser.add_argument("--input", required=True, type=Path, help="Input themes.json or pack.json")
    parser.add_argument("--output", type=Path, default=None, help="Output path (default: dry-run or --in-place)")
    parser.add_argument("--in-place", action="store_true", help="Backup original to .bak and overwrite input")
    parser.add_argument("--fix", action="store_true", help="Write repaired JSON (required if --in-place)")
    args = parser.parse_args(argv)

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    is_single_pack = "name" in raw and "bg" in raw
    is_mod_v2 = "presets" in raw and isinstance(raw["presets"], dict)

    if is_single_pack:
        presets = {raw["name"]: {k: v for k, v in raw.items() if k != "name"}}
    elif is_mod_v2:
        presets = raw["presets"]
    else:
        presets = raw

    repaired_map: dict[str, dict[str, Any]] = {}
    for name, body in presets.items():
        before = audit_preset(name, body)
        fixed_body, changes = repair_preset(name, body)
        after = audit_preset(name, fixed_body)
        repaired_map[name] = fixed_body
        print(f"=== {name} ===")
        print(
            f"  Before: pass={before['passed']} | sidebar={before['metrics'].get('sidebarBgRatio')} | "
            f"aiCard={before['metrics'].get('aiCardBgRatio')} | modal={before['metrics'].get('modalBgRatio')}"
        )
        print(
            f"  After : pass={after['passed']} | sidebar={after['metrics'].get('sidebarBgRatio')} | "
            f"aiCard={after['metrics'].get('aiCardBgRatio')} | modal={after['metrics'].get('modalBgRatio')}"
        )
        for ch in changes or ["No changes needed"]:
            print(f"  - {ch}")

    if args.output or (args.in_place and args.fix):
        if is_single_pack:
            out_obj = {"name": raw["name"], **repaired_map[raw["name"]]}
        elif is_mod_v2:
            out_obj = {**raw, "presets": repaired_map}
        else:
            out_obj = repaired_map

        out_path = args.output or args.input
        if args.in_place and args.input.exists():
            bak_path = args.input.with_suffix(args.input.suffix + ".bak")
            shutil.copy2(args.input, bak_path)
            print(f"Backup written: {bak_path}")
        out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print(f"Repaired file written: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Deterministic OKLCH Clearframe theme scaffolder with auto-tuning contrast loop."""

from __future__ import annotations

import argparse
import json
import re
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
        hex_to_rgb,
        oklch_to_srgb,
        parse_overlay_rgb,
        rgb_to_hex,
        srgb_to_oklch,
    )
except ImportError:
    from clearframe_core.contrast_lib import (
        audit_preset,
        clamp,
        hex_to_rgb,
        oklch_to_srgb,
        parse_overlay_rgb,
        rgb_to_hex,
        srgb_to_oklch,
    )


def _slugify(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.strip().lower()).strip("-")
    return slug or "custom-theme"


def _clamp_accent_oklch(hex_color: str, mode: str) -> tuple[str, tuple[float, float, float]]:
    """Preserve hue while clamping neon chroma and ensuring usable accent lightness."""
    L, C, h = srgb_to_oklch(hex_to_rgb(hex_color))
    safe_c = min(C, 0.145)
    safe_l = clamp(L, 0.42, 0.56) if mode == "light" else clamp(L, 0.64, 0.78)
    rgb = oklch_to_srgb(safe_l, safe_c, h)
    return rgb_to_hex(rgb), rgb


def _rgba_str(rgb: tuple[float, float, float], alpha: float) -> str:
    return f"rgba({round(rgb[0])}, {round(rgb[1])}, {round(rgb[2])}, {alpha:.2f})"


def scaffold_preset(
    name: str,
    primary: str,
    secondary: str,
    mode: str = "dark",
    concept: str | None = None,
    overlay_rgb: str | None = None,
    wallpaper: str = "",
    ornament: bool = False,
) -> dict[str, Any]:
    """Generate a full, contrast-verified Clearframe preset dictionary using OKLCH."""
    is_light = mode == "light"
    pri_hex, pri_rgb = _clamp_accent_oklch(primary, mode)
    sec_hex, sec_rgb = _clamp_accent_oklch(secondary, mode)
    _, _, pri_h = srgb_to_oklch(pri_rgb)
    _, _, sec_h = srgb_to_oklch(sec_rgb)

    if is_light:
        ink_l = 0.21
        text_hex = rgb_to_hex(oklch_to_srgb(ink_l, 0.014, pri_h))
        muted_hex = rgb_to_hex(oklch_to_srgb(0.45, 0.018, pri_h))
        base_ov = parse_overlay_rgb(overlay_rgb) if overlay_rgb else oklch_to_srgb(0.955, 0.012, pri_h)
        surface_bg1 = oklch_to_srgb(0.990, 0.008, pri_h)
        surface_bg2 = oklch_to_srgb(0.952, 0.014, sec_h)
        sidebar_rgb = oklch_to_srgb(0.955, 0.012, pri_h)
        ai_rgb = oklch_to_srgb(0.988, 0.008, sec_h)
        modal_rgb = oklch_to_srgb(0.990, 0.006, pri_h)
        modal_hdr_rgb = oklch_to_srgb(0.955, 0.010, pri_h)
        sel_rgb = oklch_to_srgb(0.925, 0.025, pri_h)
        sb_alpha = 0.88 if not wallpaper else 0.90
        ai_alpha = 0.94
        pure_bg = f"linear-gradient(180deg, {rgb_to_hex(surface_bg1)} 0%, {rgb_to_hex(surface_bg2)} 100%)"
        border_col = _rgba_str(pri_rgb, 0.30)
        inner_border = f"1px solid {_rgba_str(hex_to_rgb(text_hex), 0.08)}"
        ai_border = _rgba_str(hex_to_rgb(text_hex), 0.10)
        pill_border = _rgba_str(hex_to_rgb(text_hex), 0.14)
    else:
        ink_l = 0.92
        text_hex = rgb_to_hex(oklch_to_srgb(ink_l, 0.012, pri_h))
        muted_hex = rgb_to_hex(oklch_to_srgb(0.79, 0.016, sec_h))
        base_ov = parse_overlay_rgb(overlay_rgb) if overlay_rgb else oklch_to_srgb(0.165, 0.012, pri_h)
        surface_bg1 = oklch_to_srgb(0.225, 0.018, pri_h)
        surface_bg2 = oklch_to_srgb(0.185, 0.014, sec_h)
        sidebar_rgb = oklch_to_srgb(0.175, 0.012, pri_h)
        ai_rgb = oklch_to_srgb(0.188, 0.014, sec_h)
        modal_rgb = oklch_to_srgb(0.185, 0.010, pri_h)
        modal_hdr_rgb = oklch_to_srgb(0.210, 0.012, pri_h)
        sel_rgb = oklch_to_srgb(0.295, 0.035, pri_h)
        sb_alpha = 0.84 if not wallpaper else 0.88
        ai_alpha = 0.93 if not wallpaper else 0.94
        pure_bg = (
            f"radial-gradient(1100px 560px at 50% 100%, {_rgba_str(pri_rgb, 0.08)}, transparent 55%), "
            f"{rgb_to_hex(base_ov)}"
        )
        border_col = _rgba_str(pri_rgb, 0.30)
        inner_border = f"1px solid {_rgba_str(hex_to_rgb(text_hex), 0.08)}"
        ai_border = _rgba_str(sec_rgb, 0.18)
        pill_border = _rgba_str(hex_to_rgb(text_hex), 0.12)

    ov_str = f"{round(base_ov[0])}, {round(base_ov[1])}, {round(base_ov[2])}"
    concept_text = concept or f"{'Light paper' if is_light else 'Work session'} • {pri_hex} & {sec_hex} • AA"
    if "• AA" not in concept_text:
        concept_text = f"{concept_text} • AA"

    bg_grad = f"linear-gradient(145deg, {_rgba_str(surface_bg1, 0.94)} 0%, {_rgba_str(surface_bg2, 0.94)} 100%)"

    preset: dict[str, Any] = {
        "name": name,
        "concept": concept_text,
        "primary": pri_hex,
        "secondary": sec_hex,
        "glow": _rgba_str(pri_rgb, 0.12),
        "secondaryGlow": _rgba_str(sec_rgb, 0.09),
        "overlayRgb": ov_str,
        "textColor": text_hex,
        "uiTextColor": text_hex,
        "uiMutedColor": muted_hex,
        "bg": bg_grad,
        "frameBg": f"linear-gradient(135deg, {_rgba_str(pri_rgb, 0.45)} 0%, {_rgba_str(sec_rgb, 0.25)} 100%)",
        "borderColor": border_col,
        "innerBorder": inner_border,
        "sidebarBg": _rgba_str(sidebar_rgb, sb_alpha),
        "sidebarHoverBg": _rgba_str(pri_rgb, 0.12),
        "sidebarEnhanceText": bool(wallpaper),
        "aiCardBg": _rgba_str(ai_rgb, ai_alpha),
        "aiCardBorder": ai_border,
        "headerBg": _rgba_str(sidebar_rgb, min(0.96, sb_alpha + 0.02)),
        "headerBorder": inner_border.replace("1px solid ", ""),
        "unifiedGlass": False,
        "btnBg": _rgba_str(surface_bg1, 0.92),
        "inputGlassBg": _rgba_str(ai_rgb, 0.92),
        "inputCardBg": bg_grad,
        "modalBg": _rgba_str(modal_rgb, 0.98),
        "modalHeaderBg": _rgba_str(modal_hdr_rgb, 0.98),
        "cardBg": _rgba_str(ai_rgb, 0.94),
        "cardSelectedBg": _rgba_str(sel_rgb, 0.96),
        "pureBg": pure_bg,
        "wallpaper": wallpaper,
        "clearBackdrop": True,
        "isOrnament": ornament,
        "isLight": is_light,
        "pillBg": _rgba_str(surface_bg1, 0.92),
        "pillTextColor": text_hex,
        "pillBorder": pill_border,
        "pillHoverBg": _rgba_str(pri_rgb, 0.14),
    }

    if ornament:
        preset.update(
            {
                "sticker": "assets/lantern-mark.svg",
                "stickerW": 28,
                "stickerH": 36,
                "stickerTop": -8,
                "stickerRight": 16,
                "cornerSvg": "",
            }
        )

    # Auto-tune loop if anything fails contrast (e.g. bright custom overlayRgb)
    for _step in range(10):
        res = audit_preset(name, preset)
        if res["passed"]:
            break
        sb_alpha = min(0.98, sb_alpha + 0.03)
        ai_alpha = min(0.98, ai_alpha + 0.03)
        preset["sidebarBg"] = _rgba_str(sidebar_rgb, sb_alpha)
        preset["aiCardBg"] = _rgba_str(ai_rgb, ai_alpha)
        preset["headerBg"] = _rgba_str(sidebar_rgb, min(0.98, sb_alpha + 0.02))
        if any("textColor" in e or "contrast" in e for e in res["errors"]):
            fallback_ink = "#1c1915" if is_light else "#ebe7df"
            preset["textColor"] = fallback_ink
            preset["uiTextColor"] = fallback_ink
            preset["pillTextColor"] = fallback_ink

    return preset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scaffold a contrast-verified Clearframe theme preset")
    parser.add_argument("--name", required=True, help="Display name of the theme")
    parser.add_argument("--primary", required=True, help="Primary accent hex color (e.g. #e0a45a)")
    parser.add_argument("--secondary", default="#8aa0b4", help="Secondary accent hex color")
    parser.add_argument("--mode", choices=("dark", "light"), default="dark")
    parser.add_argument("--concept", default=None, help="Short session description")
    parser.add_argument("--overlay-rgb", default=None, help="Background scrim RGB (e.g. '12, 16, 20')")
    parser.add_argument("--wallpaper", default="", help="Optional wallpaper path or empty string")
    parser.add_argument("--ornament", action="store_true", help="Attach minimal lantern-mark SVG")
    parser.add_argument("--output", type=Path, default=None, help="Write pack JSON to this path")
    args = parser.parse_args(argv)

    preset = scaffold_preset(
        name=args.name,
        primary=args.primary,
        secondary=args.secondary,
        mode=args.mode,
        concept=args.concept,
        overlay_rgb=args.overlay_rgb,
        wallpaper=args.wallpaper,
        ornament=args.ornament,
    )
    audit = audit_preset(args.name, preset)
    rendered = json.dumps(preset, indent=2, ensure_ascii=False) + "\n"

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8", newline="\n")
        print(f"Wrote {args.output} (passed={audit['passed']}, sidebar={audit['metrics'].get('sidebarBgRatio')}, ai={audit['metrics'].get('aiCardBgRatio')})")
    else:
        print(rendered)

    return 0 if audit["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

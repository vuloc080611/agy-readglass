"""Render crisp SVG palette swatches for README directly from themes/themes.json."""

from __future__ import annotations

import argparse
import html
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clearframe_core.contrast_lib import (  # noqa: E402
    audit_preset,
    blend_over,
    extract_color_stops,
    parse_overlay_rgb,
    rgb_to_hex,
)


def _blended_hex(css_val: str, overlay: tuple[float, float, float]) -> str:
    stops = extract_color_stops(css_val)
    return rgb_to_hex(blend_over(stops[0], overlay))


def render_swatches_svg(themes_dir: Path) -> str:
    manifest = json.loads((themes_dir / "manifest.json").read_text(encoding="utf-8"))
    themes = json.loads((themes_dir / "themes.json").read_text(encoding="utf-8"))

    cols = 2
    card_w = 430
    card_h = 192
    gap_x = 20
    gap_y = 18
    pad = 20
    rows = (len(manifest["presets"]) + cols - 1) // cols
    total_w = pad * 2 + cols * card_w + (cols - 1) * gap_x
    total_h = pad * 2 + rows * card_h + (rows - 1) * gap_y + 34

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {total_w} {total_h}" '
        f'width="{total_w}" height="{total_h}" font-family="ui-sans-serif, system-ui, -apple-system, Segoe UI, sans-serif">',
        f'  <rect width="{total_w}" height="{total_h}" rx="14" fill="#0b0d11"/>',
        '  <text x="20" y="28" fill="#cbd5e1" font-size="13" font-weight="600">'
        "Clearframe Presets — Auto-rendered Swatches &amp; Live WCAG/APCA Scores</text>",
    ]

    for idx, meta in enumerate(manifest["presets"]):
        name = meta["name"]
        body: dict[str, Any] = themes[name]
        audit = audit_preset(name, body)
        m = audit["metrics"]
        ov = parse_overlay_rgb(body["overlayRgb"])

        col = idx % cols
        row = idx // cols
        x = pad + col * (card_w + gap_x)
        y = 44 + row * (card_h + gap_y)

        canvas_hex = rgb_to_hex(ov)
        sb_hex = _blended_hex(body["sidebarBg"], ov)
        ai_hex = _blended_hex(body["aiCardBg"], ov)
        bg_hex = _blended_hex(body["bg"], ov)
        pill_hex = _blended_hex(body["pillBg"], ov)
        ui_ink = body["uiTextColor"]
        muted_ink = body["uiMutedColor"]
        bubble_ink = body["textColor"]
        pri = body["primary"]
        sec = body["secondary"]
        bdr_hex = _blended_hex(body["borderColor"], ov)
        ai_bdr_hex = _blended_hex(body["aiCardBorder"], ov)

        title = html.escape(name)
        session = html.escape(meta["session"])
        badge = f"AI {m['aiCardBgRatio']:.1f}:1 | Lc {m['aiCardBgApca']:+.0f}"

        parts.extend(
            [
                f'  <g transform="translate({x}, {y})">',
                f'    <rect width="{card_w}" height="{card_h}" rx="12" fill="{canvas_hex}" stroke="{bdr_hex}" stroke-width="1.2"/>',
                # Simulated sidebar strip
                f'    <rect x="8" y="8" width="96" height="{card_h - 16}" rx="8" fill="{sb_hex}" stroke="{ai_bdr_hex}" stroke-width="1"/>',
                f'    <circle cx="22" cy="24" r="5" fill="{pri}"/>',
                f'    <circle cx="36" cy="24" r="5" fill="{sec}"/>',
                f'    <text x="18" y="48" fill="{ui_ink}" font-size="11.5" font-weight="700">{title}</text>',
                f'    <text x="18" y="64" fill="{muted_ink}" font-size="9.5">{html.escape(meta["mode"].upper())}</text>',
                f'    <rect x="18" y="78" width="76" height="8" rx="4" fill="{ui_ink}" fill-opacity="0.22"/>',
                f'    <rect x="18" y="94" width="60" height="7" rx="3.5" fill="{muted_ink}" fill-opacity="0.35"/>',
                f'    <rect x="18" y="108" width="68" height="7" rx="3.5" fill="{muted_ink}" fill-opacity="0.28"/>',
                f'    <rect x="18" y="152" width="76" height="22" rx="6" fill="{pill_hex}" stroke="{ai_bdr_hex}"/>',
                f'    <text x="26" y="166" fill="{body["pillTextColor"]}" font-size="9" font-weight="600">SB {m["sidebarBgRatio"]:.1f}:1</text>',
                # User bubble
                f'    <rect x="116" y="12" width="302" height="44" rx="8" fill="{bg_hex}" stroke="{bdr_hex}" stroke-width="1"/>',
                f'    <text x="128" y="30" fill="{bubble_ink}" font-size="11" font-weight="600">{session}</text>',
                f'    <text x="128" y="45" fill="{muted_ink}" font-size="9.5">User bubble {m["bgRatio"]:.1f}:1 • {pri} / {sec}</text>',
                # AI Card
                f'    <rect x="116" y="64" width="302" height="116" rx="8" fill="{ai_hex}" stroke="{ai_bdr_hex}" stroke-width="1"/>',
                f'    <text x="128" y="84" fill="{ui_ink}" font-size="11.5" font-weight="600">AI Card: readable body &amp; code</text>',
                f'    <text x="128" y="102" fill="{muted_ink}" font-size="10">Muted label ({m["muted_aiCardBgRatio"]:.1f}:1) • Modal {m["modalBgRatio"]:.1f}:1 AAA</text>',
                f'    <rect x="128" y="114" width="276" height="26" rx="6" fill="{canvas_hex}" stroke="{ai_bdr_hex}"/>',
                f'    <text x="138" y="131" fill="{ui_ink}" font-size="10" font-family="ui-monospace, Consolas, monospace">def check(ink, glass): return aa_pass</text>',
                f'    <rect x="128" y="148" width="144" height="22" rx="11" fill="{pill_hex}" stroke="{bdr_hex}"/>',
                f'    <text x="140" y="163" fill="{body["pillTextColor"]}" font-size="10" font-weight="600">{html.escape(badge)}</text>',
                "  </g>",
            ]
        )

    parts.append("</svg>\n")
    return "\n".join(parts)


def sync_studio_html(themes_dir: Path, studio_path: Path, check_only: bool = False) -> bool:
    """Sync INITIAL_PRESETS inside docs/index.html with themes/themes.json."""
    if not studio_path.exists():
        return True
    themes = json.loads((themes_dir / "themes.json").read_text(encoding="utf-8"))
    start_marker = "/* CLEARFRAME_PRESETS_START */"
    end_marker = "/* CLEARFRAME_PRESETS_END */"
    content = studio_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if start_marker not in content or end_marker not in content:
        raise ValueError(f"Missing preset markers in {studio_path}")

    before = content.split(start_marker, 1)[0]
    after = content.split(end_marker, 1)[1]
    injected = f"{start_marker}\n    const INITIAL_PRESETS = {json.dumps(themes, indent=2, ensure_ascii=False)};\n    {end_marker}"
    updated = before + injected + after
    if check_only:
        return content == updated
    studio_path.write_text(updated, encoding="utf-8", newline="\n")
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render docs/assets/swatches.svg and sync docs/index.html")
    parser.add_argument("--themes-dir", type=Path, default=ROOT / "themes")
    parser.add_argument("--output", type=Path, default=ROOT / "docs" / "assets" / "swatches.svg")
    parser.add_argument("--studio", type=Path, default=ROOT / "docs" / "index.html")
    parser.add_argument("--check", action="store_true", help="Exit 1 if SVG or Studio HTML is out of sync")
    args = parser.parse_args(argv)

    svg = render_swatches_svg(args.themes_dir)
    if args.check:
        if not args.output.exists():
            print(f"FAIL: missing {args.output}", file=sys.stderr)
            return 1
        cur = args.output.read_text(encoding="utf-8").replace("\r\n", "\n")
        if cur != svg:
            print(f"FAIL: {args.output} is out of sync; run tools/render_swatches.py", file=sys.stderr)
            return 1
        if not sync_studio_html(args.themes_dir, args.studio, check_only=True):
            print(f"FAIL: {args.studio} presets out of sync; run tools/render_swatches.py", file=sys.stderr)
            return 1
        print(f"OK: {args.output} and {args.studio} match themes.json")
        return 0

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg, encoding="utf-8", newline="\n")
    sync_studio_html(args.themes_dir, args.studio, check_only=False)
    print(f"Wrote {args.output} and synced {args.studio}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

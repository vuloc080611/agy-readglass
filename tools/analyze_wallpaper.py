"""Analyze wallpaper sidebar & chat luminance zones without Pillow."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
for _cand in (str(_HERE), str(_REPO_ROOT / "src")):
    if _cand not in sys.path:
        sys.path.insert(0, _cand)

try:
    from wallpaper_probe import analyze_wallpaper  # type: ignore[import-not-found]
except ImportError:
    from clearframe_core.wallpaper_probe import analyze_wallpaper


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze wallpaper luminance zones for Clearframe")
    parser.add_argument("image", type=Path, help="Path to wallpaper (PNG, BMP, PPM, or JPG on Win)")
    parser.add_argument("--mode", choices=("dark", "light"), default="dark")
    parser.add_argument("--no-os-fallback", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    if not args.image.exists():
        print(f"Image not found: {args.image}", file=sys.stderr)
        return 1

    try:
        report = analyze_wallpaper(args.image, mode=args.mode, allow_os_fallback=not args.no_os_fallback)
    except ValueError as exc:
        print(f"Error analyzing wallpaper: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Image grid: {report['widthSamples']}x{report['heightSamples']} ({args.mode} mode)")
        print(f"Sidebar Zone (left 22%) P90 RGB : {report['sidebarZone']['p90Rgb']}")
        print(f"Chat Zone   (right 78%) P90 RGB : {report['chatZone']['p90Rgb']}")
        print(f"Recommended overlayRgb          : {report['recommendedOverlayRgb']}")
        print(f"Recommended sidebarBg min alpha : {report['recommendedSidebarAlpha']:.2f}")
        print(f"Recommended aiCardBg  min alpha : {report['recommendedAiCardAlpha']:.2f}")
        print(f"sidebarEnhanceText              : {report['sidebarEnhanceText']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

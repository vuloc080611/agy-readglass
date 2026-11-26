"""Compile themes/packs/*.json into themes/themes.json using themes/manifest.json order."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def build_themes_payload(themes_dir: Path, fmt: str = "agy-theme") -> dict[str, Any]:
    """Read manifest.json and packs/*.json and assemble ordered themes.json payload."""
    manifest = json.loads((themes_dir / "manifest.json").read_text(encoding="utf-8"))
    ordered_presets: dict[str, dict[str, Any]] = {}

    for entry in manifest["presets"]:
        pack_path = themes_dir / "packs" / f"{entry['slug']}.json"
        pack = json.loads(pack_path.read_text(encoding="utf-8"))
        display_name = pack.get("name") or entry["name"]
        body = {k: v for k, v in pack.items() if k != "name"}
        ordered_presets[display_name] = body

    if fmt == "mod-v2":
        default_name = manifest["presets"][0]["name"]
        return {"defaultTheme": default_name, "presets": ordered_presets}
    return ordered_presets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sync Clearframe packs into themes/themes.json")
    parser.add_argument("--themes-dir", type=Path, default=ROOT / "themes")
    parser.add_argument("--format", choices=("agy-theme", "mod-v2"), default="agy-theme")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--check", action="store_true", help="Exit 1 if themes.json is out of sync")
    args = parser.parse_args(argv)

    payload = build_themes_payload(args.themes_dir, fmt=args.format)
    rendered = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    out_path = args.output or (args.themes_dir / "themes.json")

    if args.check:
        if not out_path.exists():
            print(f"FAIL: missing {out_path}", file=sys.stderr)
            return 1
        current = out_path.read_text(encoding="utf-8").replace("\r\n", "\n")
        if current != rendered:
            print(f"FAIL: {out_path} is out of sync with packs/*.json. Run tools/sync_packs.py", file=sys.stderr)
            return 1
        print(f"OK: {out_path} matches packs/*.json ({len(payload)} presets)")
        return 0

    out_path.write_text(rendered, encoding="utf-8", newline="\n")
    print(f"Wrote {out_path} ({len(payload)} presets, format={args.format})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

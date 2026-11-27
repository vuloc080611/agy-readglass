"""Select and promote a Clearframe preset by work-session shift or local clock time.

Designed to run on demand or via /schedule / OS scheduler without any background daemon.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent

SHIFT_MAP: dict[str, str] = {
    "morning": "Mekong Morning",
    "deep": "Deep Ink",
    "review": "Review Split",
    "night": "Lantern Hour",
    "screenshot": "Screenshot Clean",
    "mint": "Delta Mint",
}


def resolve_preset_for_time(hour: int, minute: int) -> str:
    """Resolve preset name from local time using Clearframe circadian schedule windows."""
    total_mins = hour * 60 + minute
    if 6 * 60 + 30 <= total_mins < 17 * 60 + 30:
        return "Mekong Morning"
    if 17 * 60 + 30 <= total_mins < 21 * 60 + 30:
        return "Deep Ink"
    return "Lantern Hour"


def _parse_hhmm(raw: str) -> tuple[int, int]:
    parts = raw.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Expected HH:MM time format, got {raw!r}")
    hour = int(parts[0])
    minute = int(parts[1])
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        raise ValueError(f"Time out of range: {raw!r}")
    return hour, minute


def promote_preset(target_path: Path, preset_name: str, dry_run: bool = False) -> dict[str, Any]:
    """Promote preset_name to default position in flat agy-theme or mod-v2 JSON."""
    raw = json.loads(target_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{target_path} must contain a non-empty JSON object")

    is_mod_v2 = "presets" in raw and isinstance(raw["presets"], dict)
    if is_mod_v2:
        presets = raw["presets"]
        if preset_name not in presets:
            raise KeyError(f"Preset {preset_name!r} not found in {target_path}")
        previous = raw.get("defaultTheme")
        updated = {**raw, "defaultTheme": preset_name}
    else:
        if preset_name not in raw:
            raise KeyError(f"Preset {preset_name!r} not found in {target_path}")
        previous = next(iter(raw))
        updated = {preset_name: raw[preset_name]}
        for key, val in raw.items():
            if key != preset_name:
                updated[key] = val

    if not dry_run and previous != preset_name:
        bak = target_path.with_suffix(target_path.suffix + ".bak")
        shutil.copy2(target_path, bak)
        target_path.write_text(json.dumps(updated, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    return {
        "target": str(target_path),
        "previousDefault": previous,
        "selectedPreset": preset_name,
        "changed": previous != preset_name,
        "dryRun": dry_run,
        "format": "mod-v2" if is_mod_v2 else "agy-theme",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Switch default Clearframe preset by work shift or clock time")
    parser.add_argument(
        "--shift",
        choices=tuple(SHIFT_MAP.keys()),
        default=None,
        help="Explicit work shift (overrides --time)",
    )
    parser.add_argument("--time", default=None, help="Clock time in HH:MM (default: current local time)")
    parser.add_argument(
        "--target",
        type=Path,
        default=_REPO_ROOT / "themes" / "themes.json",
        help="Target themes.json to update",
    )
    parser.add_argument("--dry-run", action="store_true", help="Report selection without modifying file")
    parser.add_argument("--json", action="store_true", help="Output JSON status")
    args = parser.parse_args(argv)

    try:
        if args.shift:
            chosen = SHIFT_MAP[args.shift]
        else:
            if args.time:
                h, m = _parse_hhmm(args.time)
            else:
                now = dt.datetime.now()
                h, m = now.hour, now.minute
            chosen = resolve_preset_for_time(h, m)

        if not args.target.exists():
            raise FileNotFoundError(f"Target file not found: {args.target}")

        result = promote_preset(args.target, chosen, dry_run=args.dry_run)
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}) if args.json else f"Shift failed: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        mode = "DRY-RUN" if args.dry_run else "UPDATED"
        print(
            f"[{mode}] Default preset: {result['previousDefault']!r} -> {result['selectedPreset']!r} "
            f"({result['target']})"
        )
        if not args.dry_run and result["changed"]:
            print("If using agy-theme externally, run `agy-theme build` to apply.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

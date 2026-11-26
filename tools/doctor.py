"""Non-destructive diagnostic doctor for Clearframe + agy-theme setup."""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
for _cand in (str(_HERE), str(_REPO_ROOT / "src")):
    if _cand not in sys.path:
        sys.path.insert(0, _cand)

from clearframe_core.contrast_lib import audit_preset  # noqa: E402
from clearframe_core.schema_validator import validate_themes_collection  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clearframe environment and theme diagnostic check")
    parser.add_argument("--themes", type=Path, default=_REPO_ROOT / "themes" / "themes.json")
    args = parser.parse_args(argv)

    print(f"Python  : {platform.python_version()} ({platform.system()})")
    print(f"agy-theme CLI in PATH: {'yes -> ' + str(shutil.which('agy-theme')) if shutil.which('agy-theme') else 'not found (install from chinhzz108/antigravity-custom-theme-rust if needed)'}")
    print(f"Themes file: {args.themes}")

    if not args.themes.exists():
        print("FAIL: themes file missing", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.themes.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: invalid JSON: {exc}", file=sys.stderr)
        return 1

    presets = data["presets"] if ("presets" in data and isinstance(data["presets"], dict)) else data
    schema_issues = validate_themes_collection(presets)
    if schema_issues:
        for issue in schema_issues:
            print(f"[SCHEMA FAIL] {issue}", file=sys.stderr)
        return 1

    first_key = next(iter(presets))
    failed = 0
    for name, body in presets.items():
        res = audit_preset(name, body)
        if not res["passed"]:
            failed += 1
            print(f"[CONTRAST FAIL] {name}: {res['errors']}", file=sys.stderr)

    print(f"Presets validated: {len(presets)} (default first entry: {first_key!r}, failures: {failed})")
    print("Runtime checklist for Antigravity:")
    print("  1. Ensure Antigravity shortcut launches with `--remote-debugging-port=0` (when using agy-theme).")
    print("  2. Quit Antigravity completely from system tray before relaunching after `agy-theme build`.")
    print("  3. Safe rollback: restore `themes.json.bak` or remove the CDP theme loader without touching app.asar.")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

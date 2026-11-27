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
from clearframe_core.env_paths import detect_antigravity_paths  # noqa: E402
from clearframe_core.schema_validator import validate_themes_collection  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clearframe environment and theme diagnostic check")
    parser.add_argument("--themes", type=Path, default=_REPO_ROOT / "themes" / "themes.json")
    parser.add_argument("--json", action="store_true", help="Output structured diagnostic report")
    args = parser.parse_args(argv)

    agy_bin = shutil.which("agy-theme")
    detected = detect_antigravity_paths()

    if not args.themes.exists():
        msg = f"Themes file missing: {args.themes}"
        print(json.dumps({"passed": False, "error": msg}) if args.json else f"FAIL: {msg}", file=sys.stderr)
        return 1

    try:
        data = json.loads(args.themes.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        msg = f"Invalid JSON: {exc}"
        print(json.dumps({"passed": False, "error": msg}) if args.json else f"FAIL: {msg}", file=sys.stderr)
        return 1

    presets = data["presets"] if ("presets" in data and isinstance(data["presets"], dict)) else data
    schema_issues = validate_themes_collection(presets)

    first_key = next(iter(presets)) if presets else None
    failed = 0
    contrast_errors: list[str] = []
    for name, body in presets.items():
        res = audit_preset(name, body)
        if not res["passed"]:
            failed += 1
            contrast_errors.append(f"{name}: {res['errors']}")

    passed = len(schema_issues) == 0 and failed == 0

    if args.json:
        print(
            json.dumps(
                {
                    "passed": passed,
                    "python": platform.python_version(),
                    "os": platform.system(),
                    "agyThemeCli": agy_bin,
                    "themesFile": str(args.themes),
                    "defaultPreset": first_key,
                    "presetCount": len(presets),
                    "schemaIssues": schema_issues,
                    "contrastFailures": contrast_errors,
                    "detectedPaths": detected,
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 0 if passed else 1

    print(f"Python  : {platform.python_version()} ({platform.system()})")
    print(
        f"agy-theme CLI in PATH: {'yes -> ' + agy_bin if agy_bin else 'not found (install from chinhzz108/antigravity-custom-theme-rust if needed)'}"
    )
    print(f"Themes file: {args.themes}")
    print("Detected Antigravity paths (read-only):")
    for label, info in detected.items():
        mark = "FOUND" if info["exists"] else "absent"
        print(f"  - {label:<16} [{mark:>6}] {info['path']}")

    for issue in schema_issues:
        print(f"[SCHEMA FAIL] {issue}", file=sys.stderr)
    for err in contrast_errors:
        print(f"[CONTRAST FAIL] {err}", file=sys.stderr)

    print(f"Presets validated: {len(presets)} (default first entry: {first_key!r}, failures: {failed})")
    print("Runtime checklist for Antigravity:")
    print("  1. Ensure Antigravity shortcut launches with `--remote-debugging-port=0` (when using agy-theme).")
    print("  2. Quit Antigravity completely from system tray before relaunching after `agy-theme build`.")
    print("  3. Safe rollback: restore `themes.json.bak` or remove the CDP theme loader without touching app.asar.")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

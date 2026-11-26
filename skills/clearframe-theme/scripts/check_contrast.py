"""Clearframe contrast, schema, APCA, and pack-sync gate CLI.

Exit code 0 if all themes pass WCAG AA/AAA, schema, and hygiene rules; 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_REPO_ROOT = _HERE.parent
for _cand in (str(_HERE), str(_REPO_ROOT / "src")):
    if _cand not in sys.path:
        sys.path.insert(0, _cand)

try:
    from contrast_lib import audit_preset  # type: ignore[import-not-found]
    from schema_validator import validate_preset_schema  # type: ignore[import-not-found]
except ImportError:
    from clearframe_core.contrast_lib import audit_preset
    from clearframe_core.schema_validator import validate_preset_schema


def _load_presets_from_file(path: Path) -> dict[str, dict[str, Any]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"{path} must contain a non-empty JSON object")

    # Single pack file case (contains "name" and preset properties)
    if "name" in raw and isinstance(raw["name"], str) and "bg" in raw:
        return {raw["name"]: {k: v for k, v in raw.items() if k != "name"}}

    # mod-v2 envelope case
    if "presets" in raw and isinstance(raw["presets"], dict):
        return raw["presets"]

    # Standard agy-theme flat object keyed by preset name
    return raw


def _check_pack_sync(themes_dir: Path, themes_data: dict[str, dict[str, Any]]) -> list[str]:
    issues: list[str] = []
    manifest_path = themes_dir / "manifest.json"
    packs_dir = themes_dir / "packs"
    if not manifest_path.exists() or not packs_dir.exists():
        return issues

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_keys = []
    for entry in manifest.get("presets", []):
        slug = entry["slug"]
        pack_file = packs_dir / f"{slug}.json"
        if not pack_file.exists():
            issues.append(f"Missing pack file: {pack_file}")
            continue
        pack = json.loads(pack_file.read_text(encoding="utf-8"))
        name = pack.get("name") or entry["name"]
        expected_keys.append(name)
        pack_body = {k: v for k, v in pack.items() if k != "name"}
        if name not in themes_data:
            issues.append(f"themes.json missing preset {name!r} from {pack_file.name}")
        elif themes_data[name] != pack_body:
            issues.append(f"themes.json entry {name!r} differs from {pack_file.name}; run tools/sync_packs.py")

    if list(themes_data.keys()) != expected_keys:
        issues.append(
            f"Preset order mismatch: expected {expected_keys}, got {list(themes_data.keys())}"
        )
    return issues


def _format_table(results: list[dict[str, Any]], show_apca: bool) -> str:
    if show_apca:
        header = (
            f"{'Preset':<18} {'Sidebar':>9} {'AI Card':>9} {'Modal':>8} {'Bubble':>8} "
            f"{'Muted':>8} {'Glow':>6} {'APCA(AI)':>9} {'Status':>7}"
        )
    else:
        header = (
            f"{'Preset':<18} {'Sidebar':>9} {'AI Card':>9} {'Modal':>8} {'Bubble':>8} "
            f"{'Muted':>8} {'Glow':>6} {'Status':>7}"
        )
    lines = [header, "-" * len(header)]
    for res in results:
        m = res.get("metrics", {})
        sb = f"{m.get('sidebarBgRatio', 0):.2f}" if "sidebarBgRatio" in m else "ERR"
        ai = f"{m.get('aiCardBgRatio', 0):.2f}" if "aiCardBgRatio" in m else "ERR"
        md = f"{m.get('modalBgRatio', 0):.2f}" if "modalBgRatio" in m else "ERR"
        bg = f"{m.get('bgRatio', 0):.2f}" if "bgRatio" in m else "ERR"
        mu = f"{m.get('muted_aiCardBgRatio', 0):.2f}" if "muted_aiCardBgRatio" in m else "-"
        gl = f"{m.get('glowAlpha', 0):.2f}" if "glowAlpha" in m else "ERR"
        status = "PASS" if res["passed"] else "FAIL"
        if res["passed"] and res["warnings"]:
            status = "PASS*"
        if show_apca:
            apca_ai = f"{m.get('aiCardBgApca', 0):+.1f}" if "aiCardBgApca" in m else "-"
            lines.append(
                f"{res['name']:<18} {sb:>9} {ai:>9} {md:>8} {bg:>8} {mu:>8} {gl:>6} {apca_ai:>9} {status:>7}"
            )
        else:
            lines.append(f"{res['name']:<18} {sb:>9} {ai:>9} {md:>8} {bg:>8} {mu:>8} {gl:>6} {status:>7}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Clearframe contrast, APCA, schema, and sync gate")
    default_themes = _REPO_ROOT / "themes" / "themes.json"
    parser.add_argument("path", nargs="?", type=Path, default=None, help="Optional themes.json or pack.json path")
    parser.add_argument("--file", type=Path, default=None, help="Themes or pack JSON file to audit")
    parser.add_argument("--json", action="store_true", help="Output structured JSON report")
    parser.add_argument("--apca", action="store_true", help="Include APCA Lc telemetry column")
    parser.add_argument("--strict-ergo", action="store_true", help="Treat ergonomic warnings as failures")
    parser.add_argument("--no-sync-check", action="store_true", help="Skip manifest/packs sync verification")
    args = parser.parse_args(argv)

    target = args.file or args.path or default_themes
    if not target.exists():
        msg = f"File not found: {target}"
        print(json.dumps({"passed": False, "error": msg}) if args.json else msg, file=sys.stderr)
        return 1

    try:
        presets = _load_presets_from_file(target)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        msg = f"Failed to parse {target}: {exc}"
        print(json.dumps({"passed": False, "error": msg}) if args.json else msg, file=sys.stderr)
        return 1

    sync_issues: list[str] = []
    if not args.no_sync_check and target.name == "themes.json":
        sync_issues = _check_pack_sync(target.parent, presets)

    results: list[dict[str, Any]] = []
    all_ok = len(sync_issues) == 0

    for name, preset in presets.items():
        schema_errors = validate_preset_schema(name, preset)
        audit = audit_preset(name, preset, strict_ergo=args.strict_ergo)
        audit["errors"] = schema_errors + audit["errors"]
        if args.strict_ergo and audit["warnings"]:
            audit["errors"].extend([f"ergo: {w}" for w in audit["warnings"]])
        audit["passed"] = len(audit["errors"]) == 0
        if not audit["passed"]:
            all_ok = False
        results.append(audit)

    if args.json:
        payload = {
            "file": str(target),
            "passed": all_ok,
            "syncIssues": sync_issues,
            "presets": results,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_format_table(results, show_apca=args.apca))
        for res in results:
            for err in res["errors"]:
                print(f"[FAIL] {res['name']}: {err}", file=sys.stderr)
            for warn in res["warnings"]:
                print(f"[WARN] {res['name']}: {warn}")
        for issue in sync_issues:
            print(f"[SYNC FAIL] {issue}", file=sys.stderr)

    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

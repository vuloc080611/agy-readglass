"""Safely install or merge a Clearframe pack JSON into a target agy-theme themes.json."""

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
    from contrast_lib import audit_preset  # type: ignore[import-not-found]
except ImportError:
    from clearframe_core.contrast_lib import audit_preset


def install_pack(
    pack_path: Path,
    target_path: Path,
    set_default: bool = False,
    dry_run: bool = False,
) -> tuple[str, dict[str, Any]]:
    """Merge pack JSON into target themes.json, creating .bak backup if target exists."""
    pack = json.loads(pack_path.read_text(encoding="utf-8"))
    if "name" not in pack or not isinstance(pack["name"], str):
        raise ValueError(f"{pack_path} is missing top-level 'name' field")

    name = pack["name"]
    body = {k: v for k, v in pack.items() if k != "name"}

    audit = audit_preset(name, body)
    if not audit["passed"]:
        raise ValueError(f"Pack {name!r} failed contrast gate: {audit['errors']}")

    if target_path.exists():
        existing = json.loads(target_path.read_text(encoding="utf-8"))
        if not isinstance(existing, dict):
            raise ValueError(f"{target_path} must contain a JSON object")
    else:
        existing = {}

    is_mod_v2 = "presets" in existing and isinstance(existing["presets"], dict)
    if is_mod_v2:
        presets = dict(existing["presets"])
        presets[name] = body
        out_obj = {**existing, "presets": presets}
        if set_default:
            out_obj["defaultTheme"] = name
    else:
        if set_default:
            out_obj = {name: body}
            for k, v in existing.items():
                if k != name:
                    out_obj[k] = v
        else:
            out_obj = dict(existing)
            out_obj[name] = body

    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists():
            bak = target_path.with_suffix(target_path.suffix + ".bak")
            shutil.copy2(target_path, bak)
        target_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    return name, audit


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install a Clearframe pack into an agy-theme themes.json")
    parser.add_argument("--pack", required=True, type=Path, help="Path to themes/packs/<slug>.json")
    parser.add_argument("--target", required=True, type=Path, help="Path to target agy-theme themes.json")
    parser.add_argument("--set-default", action="store_true", help="Place preset first (or set defaultTheme)")
    parser.add_argument("--dry-run", action="store_true", help="Validate merge without writing files")
    args = parser.parse_args(argv)

    try:
        name, audit = install_pack(args.pack, args.target, set_default=args.set_default, dry_run=args.dry_run)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Install failed: {exc}", file=sys.stderr)
        return 1

    action = "Validated (dry-run)" if args.dry_run else "Installed"
    print(f"{action}: {name!r} -> {args.target} (default={args.set_default})")
    print(f"Contrast sidebar={audit['metrics'].get('sidebarBgRatio')}, aiCard={audit['metrics'].get('aiCardBgRatio')}, modal={audit['metrics'].get('modalBgRatio')}")
    if not args.dry_run:
        print("Next step in your agy-theme engine folder: run `agy-theme build`, then restart Antigravity completely.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Bundle core modules, tools, and references into standalone skill directories.

Ensures single source of truth in src/, tools/, and references/ while guaranteeing each
skill folder under skills/ works standalone when installed via `npx skills add`.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SKILL_BUNDLES: dict[str, dict[str, list[tuple[Path, str]]]] = {
    "clearframe-theme": {
        "scripts": [
            (ROOT / "src" / "clearframe_core" / "contrast_lib.py", "contrast_lib.py"),
            (ROOT / "src" / "clearframe_core" / "schema_validator.py", "schema_validator.py"),
            (ROOT / "src" / "clearframe_core" / "wallpaper_probe.py", "wallpaper_probe.py"),
            (ROOT / "tools" / "check_contrast.py", "check_contrast.py"),
            (ROOT / "tools" / "scaffold_theme.py", "scaffold_theme.py"),
            (ROOT / "tools" / "analyze_wallpaper.py", "analyze_wallpaper.py"),
            (ROOT / "tools" / "install_pack.py", "install_pack.py"),
        ],
        "references": [
            (ROOT / "references" / "contrast.md", "contrast.md"),
            (ROOT / "references" / "theme-schema.md", "theme-schema.md"),
            (ROOT / "references" / "theme-schema.json", "theme-schema.json"),
        ],
    },
    "clearframe-audit": {
        "scripts": [
            (ROOT / "src" / "clearframe_core" / "contrast_lib.py", "contrast_lib.py"),
            (ROOT / "src" / "clearframe_core" / "schema_validator.py", "schema_validator.py"),
            (ROOT / "tools" / "check_contrast.py", "check_contrast.py"),
            (ROOT / "tools" / "audit_repair.py", "audit_repair.py"),
        ],
        "references": [
            (ROOT / "references" / "contrast.md", "contrast.md"),
        ],
    },
    "clearframe-ide-sync": {
        "scripts": [
            (ROOT / "src" / "clearframe_core" / "contrast_lib.py", "contrast_lib.py"),
            (ROOT / "tools" / "export_ide_sync.py", "export_ide_sync.py"),
        ],
        "references": [
            (ROOT / "references" / "ide-tokens.md", "ide-tokens.md"),
        ],
    },
}


def sync_or_check(check_only: bool = False) -> list[str]:
    mismatches: list[str] = []
    for skill_name, sections in SKILL_BUNDLES.items():
        skill_dir = ROOT / "skills" / skill_name
        for subdir, mappings in sections.items():
            target_dir = skill_dir / subdir
            if not check_only:
                target_dir.mkdir(parents=True, exist_ok=True)
            for src_path, dest_name in mappings:
                dest_path = target_dir / dest_name
                src_bytes = src_path.read_bytes().replace(b"\r\n", b"\n")
                if check_only:
                    if not dest_path.exists():
                        mismatches.append(f"Missing bundled file: {dest_path}")
                    elif dest_path.read_bytes().replace(b"\r\n", b"\n") != src_bytes:
                        mismatches.append(f"Out of sync: {dest_path} != {src_path}")
                else:
                    dest_path.write_bytes(src_bytes)
    return mismatches


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bundle core scripts and references into skills/*")
    parser.add_argument("--check", action="store_true", help="Verify bundled files match canonical sources")
    args = parser.parse_args(argv)

    mismatches = sync_or_check(check_only=args.check)
    if args.check:
        if mismatches:
            for item in mismatches:
                print(f"[BUNDLE MISMATCH] {item}", file=sys.stderr)
            return 1
        print("OK: All skill bundles match canonical sources.")
        return 0

    print(f"Bundled {len(SKILL_BUNDLES)} standalone skills under {ROOT / 'skills'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

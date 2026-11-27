"""Tests verifying skill frontmatter validity, bundle sync, and isolated standalone execution."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from bundle_skills import SKILL_BUNDLES, sync_or_check  # noqa: E402


class TestSkillBundles(unittest.TestCase):
    def test_bundle_in_sync(self) -> None:
        mismatches = sync_or_check(check_only=True)
        self.assertEqual(mismatches, [], f"Run tools/bundle_skills.py: {mismatches}")

    def test_skill_frontmatter_and_names(self) -> None:
        for skill_name in SKILL_BUNDLES:
            skill_md = ROOT / "skills" / skill_name / "SKILL.md"
            self.assertTrue(skill_md.exists(), f"Missing {skill_md}")
            text = skill_md.read_text(encoding="utf-8")
            m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
            self.assertIsNotNone(m, f"Missing YAML frontmatter in {skill_md}")
            fm = m.group(1)
            self.assertIsNotNone(
                re.search(rf"^name:\s*{re.escape(skill_name)}\s*$", fm, re.MULTILINE),
                f"name must match folder name {skill_name}",
            )
            self.assertIn("description:", fm)
            self.assertLessEqual(len(text.splitlines()), 140, f"{skill_name} SKILL.md should stay lean")

    def test_isolated_skill_runs_outside_repo(self) -> None:
        """Simulate `npx skills add` copying only one skill folder to an external directory."""
        with tempfile.TemporaryDirectory() as tmp:
            isolated_skill = Path(tmp) / "clearframe-theme"
            shutil.copytree(ROOT / "skills" / "clearframe-theme", isolated_skill)

            # Run scaffold_theme.py and check_contrast.py inside the isolated folder
            out_pack = Path(tmp) / "sunset.json"
            proc1 = subprocess.run(
                [
                    sys.executable,
                    str(isolated_skill / "scripts" / "scaffold_theme.py"),
                    "--name",
                    "Sunset Focus",
                    "--primary",
                    "#d9825b",
                    "--secondary",
                    "#6d9dc5",
                    "--output",
                    str(out_pack),
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc1.returncode, 0, proc1.stderr)
            self.assertTrue(out_pack.exists())

            proc2 = subprocess.run(
                [
                    sys.executable,
                    str(isolated_skill / "scripts" / "check_contrast.py"),
                    "--apca",
                    "--json",
                    "--file",
                    str(out_pack),
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc2.returncode, 0, proc2.stderr)
            report = json.loads(proc2.stdout)
            self.assertTrue(report["passed"])

            # Verify clearframe-audit runs standalone outside repo
            isolated_audit = Path(tmp) / "clearframe-audit"
            shutil.copytree(ROOT / "skills" / "clearframe-audit", isolated_audit)
            proc3 = subprocess.run(
                [
                    sys.executable,
                    str(isolated_audit / "scripts" / "audit_repair.py"),
                    "--input",
                    str(out_pack),
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc3.returncode, 0, proc3.stderr)

            # Verify clearframe-ide-sync runs standalone outside repo
            isolated_ide = Path(tmp) / "clearframe-ide-sync"
            shutil.copytree(ROOT / "skills" / "clearframe-ide-sync", isolated_ide)
            proc4 = subprocess.run(
                [
                    sys.executable,
                    str(isolated_ide / "scripts" / "export_ide_sync.py"),
                    "--file",
                    str(out_pack),
                    "--cvd-safe",
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc4.returncode, 0, proc4.stderr)
            self.assertIn("workbench.colorCustomizations", proc4.stdout)

            # Verify --detect-settings and isolated shift_preset.py
            proc5 = subprocess.run(
                [sys.executable, str(isolated_ide / "scripts" / "export_ide_sync.py"), "--detect-settings"],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc5.returncode, 0, proc5.stderr)
            self.assertIn("ideSettings:", proc5.stdout)

            themes_copy = Path(tmp) / "themes.json"
            themes_copy.write_text((ROOT / "themes" / "themes.json").read_text(encoding="utf-8"), encoding="utf-8")
            proc6 = subprocess.run(
                [
                    sys.executable,
                    str(isolated_skill / "scripts" / "shift_preset.py"),
                    "--shift",
                    "night",
                    "--target",
                    str(themes_copy),
                ],
                cwd=tmp,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(proc6.returncode, 0, proc6.stderr)
            self.assertEqual(list(json.loads(themes_copy.read_text(encoding="utf-8")).keys())[0], "Lantern Hour")


if __name__ == "__main__":
    unittest.main()

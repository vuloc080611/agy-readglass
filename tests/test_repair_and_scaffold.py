"""Tests for Clearframe preset integrity, pack sync, OKLCH scaffolder, repair, and IDE sync."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "tools"))

from audit_repair import repair_preset  # noqa: E402
from clearframe_core.contrast_lib import audit_preset  # noqa: E402
from clearframe_core.schema_validator import validate_themes_collection  # noqa: E402
from export_ide_sync import build_ide_customizations  # noqa: E402
from install_pack import install_pack  # noqa: E402
from scaffold_theme import scaffold_preset  # noqa: E402
from sync_packs import build_themes_payload  # noqa: E402


class TestPresetsAndTools(unittest.TestCase):
    def test_repo_themes_pass_strict_and_sync(self) -> None:
        themes_path = ROOT / "themes" / "themes.json"
        data = json.loads(themes_path.read_text(encoding="utf-8"))
        self.assertEqual(list(data.keys())[0], "Deep Ink")
        self.assertEqual(len(data), 6)
        self.assertEqual(validate_themes_collection(data), [])
        expected = build_themes_payload(ROOT / "themes", fmt="agy-theme")
        self.assertEqual(data, expected)
        for name, body in data.items():
            res = audit_preset(name, body, strict_ergo=True)
            self.assertTrue(res["passed"], f"{name} failed errors: {res['errors']}")
            self.assertEqual(res["warnings"], [], f"{name} had warnings: {res['warnings']}")

    def test_scaffold_clamps_neon_and_passes(self) -> None:
        preset = scaffold_preset(
            name="Neon Rescue",
            primary="#ff00ff",
            secondary="#00ffff",
            mode="dark",
            wallpaper="assets/sample.png",
        )
        body = {k: v for k, v in preset.items() if k != "name"}
        res = audit_preset("Neon Rescue", body)
        self.assertTrue(res["passed"], res["errors"])
        self.assertTrue(body["sidebarEnhanceText"])
        self.assertLessEqual(res["metrics"]["glowAlpha"], 0.18)

    def test_audit_repair_rescues_broken_wallpaper_theme(self) -> None:
        broken = {
            "concept": "Anime glass",
            "primary": "#00f0ff",
            "secondary": "#ff2bd6",
            "glow": "rgba(0, 240, 255, 0.55)",
            "secondaryGlow": "rgba(255, 43, 214, 0.45)",
            "overlayRgb": "200, 205, 220",
            "textColor": "#8f94a0",
            "uiTextColor": "#9aa0ac",
            "uiMutedColor": "#585c66",
            "bg": "rgba(20, 24, 30, 0.40)",
            "sidebarBg": "rgba(18, 22, 28, 0.35)",
            "sidebarEnhanceText": False,
            "aiCardBg": "rgba(20, 22, 26, 0.40)",
            "headerBg": "rgba(20, 22, 26, 0.45)",
            "btnBg": "rgba(25, 28, 34, 0.45)",
            "inputGlassBg": "rgba(25, 28, 34, 0.45)",
            "inputCardBg": "rgba(20, 24, 30, 0.40)",
            "modalBg": "rgba(22, 24, 28, 0.50)",
            "modalHeaderBg": "rgba(25, 27, 32, 0.50)",
            "cardBg": "rgba(24, 26, 30, 0.45)",
            "cardSelectedBg": "rgba(35, 45, 55, 0.55)",
            "pillBg": "rgba(24, 26, 30, 0.45)",
            "pillTextColor": "#9aa0ac",
            "wallpaper": "user/my-bg.jpg",
        }
        repaired, changes = repair_preset("Broken Theme", broken)
        self.assertTrue(len(changes) > 0)
        # Wallpaper preserved
        self.assertEqual(repaired["wallpaper"], "user/my-bg.jpg")
        res = audit_preset("Broken Theme", repaired)
        self.assertTrue(res["passed"], f"Repaired theme still failing: {res['errors']}")

    def test_install_pack_backup_and_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "themes.json"
            target.write_text(json.dumps({"Existing": {"x": 1}}), encoding="utf-8")
            name, _audit = install_pack(ROOT / "themes" / "packs" / "review-split.json", target, set_default=True)
            self.assertEqual(name, "Review Split")
            self.assertTrue((Path(tmp) / "themes.json.bak").exists())
            updated = json.loads(target.read_text(encoding="utf-8"))
            self.assertEqual(list(updated.keys())[0], "Review Split")
            self.assertIn("Existing", updated)

    def test_ide_sync_cvd_diff_and_scrollbar(self) -> None:
        pack = json.loads((ROOT / "themes" / "packs" / "deep-ink.json").read_text(encoding="utf-8"))
        out = build_ide_customizations(pack, cvd_safe=True)
        wc = out["workbench.colorCustomizations"]
        self.assertIn("scrollbarSlider.background", wc)
        self.assertEqual(wc["diffEditor.insertedTextBackground"], "#3b82f62e")
        self.assertEqual(wc["diffEditor.removedTextBackground"], "#e08b3a30")


if __name__ == "__main__":
    unittest.main()

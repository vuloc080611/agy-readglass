"""Unit tests for Clearframe color math, WCAG 2.1, APCA, OKLCH, CVD, and wallpaper probing."""

from __future__ import annotations

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from clearframe_core.contrast_lib import (  # noqa: E402
    apca_lc,
    blend_over,
    contrast_ratio,
    oklch_to_srgb,
    parse_color_rgba,
    parse_overlay_rgb,
    relative_luminance,
    rgb_to_hex,
    simulate_cvd,
    srgb_to_oklch,
)
from clearframe_core.wallpaper_probe import analyze_wallpaper  # noqa: E402


def _make_test_png(path: Path, width: int, height: int, left_rgb: tuple[int, int, int], right_rgb: tuple[int, int, int]) -> None:
    """Create a tiny valid 8-bit RGB PNG with distinct left/right luminance zones."""
    raw_rows = bytearray()
    split = int(width * 0.22)
    for _y in range(height):
        raw_rows.append(0)  # filter type 0
        for x in range(width):
            rgb = left_rgb if x < split else right_rgb
            raw_rows.extend(rgb)

    def chunk(tag: bytes, payload: bytes) -> bytes:
        crc = zlib.crc32(tag + payload) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + tag + payload + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    idat = zlib.compress(bytes(raw_rows))
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    path.write_bytes(png)


class TestContrastMath(unittest.TestCase):
    def test_wcag_reference_vectors(self) -> None:
        black = (0.0, 0.0, 0.0)
        white = (255.0, 255.0, 255.0)
        self.assertAlmostEqual(relative_luminance(black), 0.0, places=5)
        self.assertAlmostEqual(relative_luminance(white), 1.0, places=5)
        self.assertAlmostEqual(contrast_ratio(black, white), 21.0, places=3)
        # #767676 on #ffffff is the canonical W3C 4.54:1 boundary
        mid_gray = parse_color_rgba("#767676")[:3]
        self.assertGreaterEqual(contrast_ratio(mid_gray, white), 4.5)
        self.assertLess(contrast_ratio(mid_gray, white), 4.6)

    def test_color_parsers_and_alpha_blend(self) -> None:
        self.assertEqual(parse_color_rgba("#abc"), (170.0, 187.0, 204.0, 1.0))
        self.assertEqual(parse_color_rgba("#10203080")[:3], (16.0, 32.0, 48.0))
        self.assertAlmostEqual(parse_color_rgba("#10203080")[3], 128 / 255.0, places=4)
        self.assertEqual(parse_color_rgba("rgb(10 20 30 / 50%)"), (10.0, 20.0, 30.0, 0.5))
        r, g, b, a = parse_color_rgba("hsla(120, 100%, 50%, 0.25)")
        self.assertAlmostEqual(r, 0.0, places=1)
        self.assertAlmostEqual(g, 255.0, places=1)
        self.assertAlmostEqual(b, 0.0, places=1)
        self.assertAlmostEqual(a, 0.25, places=4)
        self.assertEqual(parse_overlay_rgb("10, 12, 16"), (10.0, 12.0, 16.0))
        blended = blend_over((255.0, 255.0, 255.0, 0.5), (0.0, 0.0, 0.0))
        self.assertAlmostEqual(blended[0], 127.5, places=2)

    def test_apca_polarity_and_thresholds(self) -> None:
        # Dark text on light background -> positive Lc
        lc_light = apca_lc((28.0, 25.0, 21.0), (255.0, 252.0, 246.0))
        self.assertGreater(lc_light, 95.0)
        # Light text on dark background -> negative Lc
        lc_dark = apca_lc((244.0, 241.0, 234.0), (14.0, 16.0, 20.0))
        self.assertLess(lc_dark, -90.0)
        # Same color -> 0.0
        self.assertEqual(apca_lc((100.0, 100.0, 100.0), (100.0, 100.0, 100.0)), 0.0)

    def test_oklch_round_trip(self) -> None:
        for hex_col in ("#e0a45a", "#1f6b45", "#3ecf8e", "#8aa4b8", "#f4f1ea", "#1c1915"):
            rgb = parse_color_rgba(hex_col)[:3]
            L, C, h = srgb_to_oklch(rgb)
            back = oklch_to_srgb(L, C, h)
            self.assertEqual(rgb_to_hex(back), hex_col)

    def test_cvd_simulation_bounds(self) -> None:
        deut = simulate_cvd((224.0, 164.0, 90.0), "deuteranopia")
        prot = simulate_cvd((62.0, 207.0, 142.0), "protanopia")
        for ch in deut + prot:
            self.assertGreaterEqual(ch, 0.0)
            self.assertLessEqual(ch, 255.0)

    def test_pure_python_png_wallpaper_probe(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            png_path = Path(tmp) / "split.png"
            # Bright sky on left 22% (sidebar), dark forest on right 78% (chat)
            _make_test_png(png_path, 40, 20, (240, 240, 240), (20, 26, 22))
            report = analyze_wallpaper(png_path, mode="dark", allow_os_fallback=False)
            self.assertEqual(report["sidebarZone"]["p90Rgb"], [240, 240, 240])
            self.assertEqual(report["chatZone"]["p90Rgb"], [20, 26, 22])
            self.assertGreaterEqual(report["recommendedSidebarAlpha"], 0.82)
            self.assertGreaterEqual(report["recommendedAiCardAlpha"], 0.84)
            self.assertTrue(report["sidebarEnhanceText"])


if __name__ == "__main__":
    unittest.main()

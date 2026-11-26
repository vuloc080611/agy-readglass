"""Pure-Python wallpaper luminance zone sampler (zero Pillow dependency).

Reads PNG (8-bit RGB, RGBA, Grayscale, Grayscale+Alpha), BMP (24/32-bit uncompressed),
and PPM (P6 binary) directly with stdlib. On Windows/macOS, optionally falls back to
native OS image APIs only if explicitly enabled for JPEG/WebP files.
"""

from __future__ import annotations

import math
import os
import platform
import struct
import subprocess
import zlib
from pathlib import Path
from typing import Any

from .contrast_lib import RGB, blend_over, contrast_ratio, hex_to_rgb, relative_luminance


def _paeth_predictor(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _decode_png_pixels(data: bytes) -> tuple[int, int, list[RGB]]:
    """Decode non-interlaced 8-bit PNG into sampled RGB pixels."""
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Not a valid PNG signature")
    pos = 8
    width = height = bit_depth = color_type = interlace = 0
    idat_chunks: list[bytes] = []
    palette: list[RGB] = []

    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        ctype = data[pos + 4 : pos + 8]
        chunk = data[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if ctype == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filt, interlace = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"PLTE":
            palette = [(float(chunk[i]), float(chunk[i + 1]), float(chunk[i + 2])) for i in range(0, len(chunk), 3)]
        elif ctype == b"IDAT":
            idat_chunks.append(chunk)
        elif ctype == b"IEND":
            break

    if bit_depth != 8 or interlace != 0:
        raise ValueError(f"Unsupported PNG bit_depth={bit_depth} or interlace={interlace}")

    channels_map = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    if color_type not in channels_map:
        raise ValueError(f"Unsupported PNG color_type={color_type}")
    bpp = channels_map[color_type]
    stride = width * bpp
    raw = zlib.decompress(b"".join(idat_chunks))

    # Downsample step to keep large 4K PNGs fast in pure Python (~120x80 grid)
    step_y = max(1, height // 90)
    step_x = max(1, width // 160)

    prev = bytearray(stride)
    pixels: list[RGB] = []
    idx = 0
    for y in range(height):
        ftype = raw[idx]
        idx += 1
        row = bytearray(raw[idx : idx + stride])
        idx += stride

        if ftype == 1:
            for i in range(bpp, stride):
                row[i] = (row[i] + row[i - bpp]) & 0xFF
        elif ftype == 2:
            for i in range(stride):
                row[i] = (row[i] + prev[i]) & 0xFF
        elif ftype == 3:
            for i in range(stride):
                left = row[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + ((left + prev[i]) >> 1)) & 0xFF
        elif ftype == 4:
            for i in range(stride):
                a = row[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                row[i] = (row[i] + _paeth_predictor(a, b, c)) & 0xFF
        elif ftype != 0:
            raise ValueError(f"Unsupported PNG scanline filter: {ftype}")

        if y % step_y == 0:
            for x in range(0, width, step_x):
                off = x * bpp
                if color_type == 2 or color_type == 6:
                    pixels.append((float(row[off]), float(row[off + 1]), float(row[off + 2])))
                elif color_type == 0 or color_type == 4:
                    v = float(row[off])
                    pixels.append((v, v, v))
                elif color_type == 3:
                    pixels.append(palette[row[off]])
        prev = row

    sampled_w = len(range(0, width, step_x))
    sampled_h = len(range(0, height, step_y))
    return sampled_w, sampled_h, pixels


def _decode_bmp_pixels(data: bytes) -> tuple[int, int, list[RGB]]:
    """Decode uncompressed 24-bit or 32-bit BMP."""
    if data[:2] != b"BM":
        raise ValueError("Not a valid BMP file")
    pixel_offset = struct.unpack("<I", data[10:14])[0]
    width, height = struct.unpack("<ii", data[18:26])
    bpp_bits = struct.unpack("<H", data[28:30])[0]
    compression = struct.unpack("<I", data[30:34])[0]
    if compression != 0 or bpp_bits not in (24, 32):
        raise ValueError(f"Unsupported BMP bpp={bpp_bits}, compression={compression}")
    top_down = height < 0
    height = abs(height)
    bytes_pp = bpp_bits // 8
    row_stride = ((width * bpp_bits + 31) // 32) * 4

    step_y = max(1, height // 90)
    step_x = max(1, width // 160)
    rows_range = range(0, height, step_y)
    pixels: list[RGB] = []
    for y_idx in rows_range:
        src_y = y_idx if top_down else (height - 1 - y_idx)
        base = pixel_offset + src_y * row_stride
        for x in range(0, width, step_x):
            off = base + x * bytes_pp
            b, g, r = data[off], data[off + 1], data[off + 2]
            pixels.append((float(r), float(g), float(b)))
    return len(range(0, width, step_x)), len(list(rows_range)), pixels


def _decode_ppm_pixels(data: bytes) -> tuple[int, int, list[RGB]]:
    """Decode binary P6 PPM image."""
    tokens: list[bytes] = []
    i = 0
    n = len(data)
    while len(tokens) < 4 and i < n:
        if data[i : i + 1] == b"#":
            while i < n and data[i : i + 1] != b"\n":
                i += 1
        elif chr(data[i]).isspace():
            i += 1
        else:
            start = i
            while i < n and not chr(data[i]).isspace():
                i += 1
            tokens.append(data[start:i])
    if len(tokens) < 4 or tokens[0] != b"P6":
        raise ValueError("Unsupported PPM format (expected P6)")
    width, height, maxval = int(tokens[1]), int(tokens[2]), int(tokens[3])
    if maxval != 255:
        raise ValueError("Only 8-bit PPM maxval=255 supported")
    payload = data[i + 1 :]
    step_y = max(1, height // 90)
    step_x = max(1, width // 160)
    pixels: list[RGB] = []
    for y in range(0, height, step_y):
        for x in range(0, width, step_x):
            off = (y * width + x) * 3
            pixels.append((float(payload[off]), float(payload[off + 1]), float(payload[off + 2])))
    return len(range(0, width, step_x)), len(range(0, height, step_y)), pixels


def _os_sample_pixels(image_path: Path) -> tuple[int, int, list[RGB]] | None:
    """Optional OS native fallback (Windows PowerShell System.Drawing) for JPEG/WebP."""
    if platform.system() != "Windows":
        return None
    escaped = str(image_path).replace("'", "''")
    ps = (
        "Add-Type -AssemblyName System.Drawing; "
        f"$img = [System.Drawing.Bitmap]::FromFile('{escaped}'); "
        "$w = 96; $h = 54; "
        "$bmp = New-Object System.Drawing.Bitmap($img, $w, $h); "
        "$out = New-Object System.Text.StringBuilder; "
        "for ($y=0; $y -lt $h; $y++) { "
        "  for ($x=0; $x -lt $w; $x++) { "
        "    $c = $bmp.GetPixel($x, $y); "
        "    [void]$out.AppendFormat('{0},{1},{2};', $c.R, $c.G, $c.B); "
        "  } "
        "}; "
        "$bmp.Dispose(); $img.Dispose(); "
        "Write-Output $out.ToString()"
    )
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        triples = [t for t in res.stdout.strip().split(";") if t]
        pixels = []
        for t in triples:
            r, g, b = t.split(",")
            pixels.append((float(r), float(g), float(b)))
        if len(pixels) == 96 * 54:
            return 96, 54, pixels
    except (subprocess.SubprocessError, ValueError, OSError):
        return None
    return None


def load_image_samples(path: str | os.PathLike[str], allow_os_fallback: bool = True) -> tuple[int, int, list[RGB]]:
    """Load downsampled RGB grid from PNG, BMP, PPM (or JPEG via OS fallback)."""
    p = Path(path)
    data = p.read_bytes()
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return _decode_png_pixels(data)
    if data[:2] == b"BM":
        return _decode_bmp_pixels(data)
    if data[:2] == b"P6":
        return _decode_ppm_pixels(data)
    if allow_os_fallback:
        os_res = _os_sample_pixels(p)
        if os_res is not None:
            return os_res
    raise ValueError(
        f"Unsupported image format for pure-Python decoder: {p.suffix}. Use PNG/BMP/PPM or pass --bg-rgb."
    )


def _zone_stats(zone_pixels: list[RGB]) -> dict[str, Any]:
    lums = sorted((relative_luminance(px), px) for px in zone_pixels)
    n = len(lums)
    avg_r = sum(px[0] for px in zone_pixels) / n
    avg_g = sum(px[1] for px in zone_pixels) / n
    avg_b = sum(px[2] for px in zone_pixels) / n
    p10 = lums[max(0, int(0.10 * (n - 1)))][1]
    p50 = lums[max(0, int(0.50 * (n - 1)))][1]
    p90 = lums[max(0, int(0.90 * (n - 1)))][1]
    return {
        "avgRgb": [round(avg_r), round(avg_g), round(avg_b)],
        "p10Rgb": [round(p10[0]), round(p10[1]), round(p10[2])],
        "p50Rgb": [round(p50[0]), round(p50[1]), round(p50[2])],
        "p90Rgb": [round(p90[0]), round(p90[1]), round(p90[2])],
        "p90Lum": round(relative_luminance(p90), 4),
    }


def _min_alpha_for_target(
    text_rgb: RGB,
    surface_rgb: RGB,
    worst_bg_rgb: RGB,
    target_ratio: float = 4.5,
    floor_alpha: float = 0.82,
) -> float:
    a = floor_alpha
    while a <= 0.99:
        blended = blend_over((surface_rgb[0], surface_rgb[1], surface_rgb[2], a), worst_bg_rgb)
        if contrast_ratio(text_rgb, blended) >= target_ratio:
            return round(a, 2)
        a += 0.02
    return 0.98


def analyze_wallpaper(
    image_path: str | os.PathLike[str],
    mode: str = "dark",
    allow_os_fallback: bool = True,
) -> dict[str, Any]:
    """Analyze Left-22% Sidebar Zone and Right-78% Chat Zone for glass opacity recommendations."""
    w, h, pixels = load_image_samples(image_path, allow_os_fallback=allow_os_fallback)
    split_x = max(1, int(round(w * 0.22)))
    sidebar_px: list[RGB] = []
    chat_px: list[RGB] = []

    for y in range(h):
        row_off = y * w
        for x in range(w):
            px = pixels[row_off + x]
            if x < split_x:
                sidebar_px.append(px)
            else:
                chat_px.append(px)

    sb_stats = _zone_stats(sidebar_px or pixels)
    chat_stats = _zone_stats(chat_px or pixels)
    all_stats = _zone_stats(pixels)

    if mode == "light":
        ink = hex_to_rgb("#1c1915")
        surface = (255.0, 252.0, 246.0)
        sb_worst = tuple(float(c) for c in sb_stats["p10Rgb"])
        chat_worst = tuple(float(c) for c in chat_stats["p10Rgb"])
    else:
        ink = hex_to_rgb("#ebe6dc")
        surface = (16.0, 18.0, 22.0)
        sb_worst = tuple(float(c) for c in sb_stats["p90Rgb"])
        chat_worst = tuple(float(c) for c in chat_stats["p90Rgb"])

    min_sb_alpha = _min_alpha_for_target(ink, surface, sb_worst, target_ratio=4.5, floor_alpha=0.82)
    min_ai_alpha = _min_alpha_for_target(ink, surface, chat_worst, target_ratio=4.5, floor_alpha=0.84)

    return {
        "widthSamples": w,
        "heightSamples": h,
        "mode": mode,
        "overall": all_stats,
        "sidebarZone": sb_stats,
        "chatZone": chat_stats,
        "recommendedOverlayRgb": ", ".join(str(v) for v in all_stats["p50Rgb"]),
        "recommendedSidebarAlpha": min_sb_alpha,
        "recommendedAiCardAlpha": min_ai_alpha,
        "sidebarEnhanceText": True,
    }

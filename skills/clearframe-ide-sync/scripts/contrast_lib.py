"""Core color parsing, alpha compositing, WCAG 2.1, APCA, OKLCH, and CVD math.

Zero external dependencies (Python standard library only).
"""

from __future__ import annotations

import math
import re
from typing import Any

RGBA = tuple[float, float, float, float]
RGB = tuple[float, float, float]

_COLOR_TOKEN_RE = re.compile(
    r"rgba?\([^)]+\)|hsla?\([^)]+\)|#[0-9a-fA-F]{3,8}\b|\btransparent\b",
    re.IGNORECASE,
)

# Minimum required surfaces for text readability in Clearframe schemas
PRIMARY_TEXT_SURFACES = ("sidebarBg", "aiCardBg", "headerBg", "btnBg", "inputGlassBg", "cardBg", "cardSelectedBg")
MODAL_TEXT_SURFACES = ("modalBg", "modalHeaderBg")


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp numeric value into [lo, hi]."""
    return max(lo, min(hi, value))


def hex_to_rgb(hex_str: str) -> RGB:
    """Parse #RGB or #RRGGBB into (r, g, b) floats in [0, 255]."""
    r, g, b, _ = parse_color_rgba(hex_str)
    return (r, g, b)


def rgb_to_hex(rgb: RGB) -> str:
    """Convert an RGB tuple (0-255) into lowercase #rrggbb string."""
    r = int(round(clamp(rgb[0], 0.0, 255.0)))
    g = int(round(clamp(rgb[1], 0.0, 255.0)))
    b = int(round(clamp(rgb[2], 0.0, 255.0)))
    return f"#{r:02x}{g:02x}{b:02x}"


def _hsl_to_rgb(h: float, s: float, l: float) -> RGB:
    """Convert CSS HSL (h in deg, s and l in 0..1) to sRGB (0..255)."""
    h = (h % 360.0) / 360.0
    if s == 0.0:
        v = l * 255.0
        return (v, v, v)

    def hue_to_rgb(p: float, q: float, t: float) -> float:
        if t < 0.0:
            t += 1.0
        if t > 1.0:
            t -= 1.0
        if t < 1.0 / 6.0:
            return p + (q - p) * 6.0 * t
        if t < 0.5:
            return q
        if t < 2.0 / 3.0:
            return p + (q - p) * (2.0 / 3.0 - t) * 6.0
        return p

    q = l * (1.0 + s) if l < 0.5 else l + s - l * s
    p = 2.0 * l - q
    return (
        hue_to_rgb(p, q, h + 1.0 / 3.0) * 255.0,
        hue_to_rgb(p, q, h) * 255.0,
        hue_to_rgb(p, q, h - 1.0 / 3.0) * 255.0,
    )


def _parse_numeric_channel(raw: str, scale: float = 255.0) -> float:
    raw = raw.strip()
    if raw.endswith("%"):
        return clamp(float(raw[:-1]) / 100.0 * scale, 0.0, scale)
    return float(raw)


def _parse_alpha_token(raw: str) -> float:
    raw = raw.strip()
    if raw.endswith("%"):
        return clamp(float(raw[:-1]) / 100.0, 0.0, 1.0)
    return clamp(float(raw), 0.0, 1.0)


def parse_color_rgba(token: str) -> RGBA:
    """Parse hex, rgb(), rgba(), hsl(), hsla(), or transparent into (r, g, b, a)."""
    if not isinstance(token, str):
        raise ValueError(f"Expected color string, got {type(token).__name__}")
    s = token.strip()
    low = s.lower()
    if low == "transparent":
        return (0.0, 0.0, 0.0, 0.0)

    if s.startswith("#"):
        h = s[1:]
        if len(h) == 3:
            return (float(int(h[0] * 2, 16)), float(int(h[1] * 2, 16)), float(int(h[2] * 2, 16)), 1.0)
        if len(h) == 4:
            return (
                float(int(h[0] * 2, 16)),
                float(int(h[1] * 2, 16)),
                float(int(h[2] * 2, 16)),
                int(h[3] * 2, 16) / 255.0,
            )
        if len(h) == 6:
            return (float(int(h[0:2], 16)), float(int(h[2:4], 16)), float(int(h[4:6], 16)), 1.0)
        if len(h) == 8:
            return (
                float(int(h[0:2], 16)),
                float(int(h[2:4], 16)),
                float(int(h[4:6], 16)),
                int(h[6:8], 16) / 255.0,
            )
        raise ValueError(f"Invalid hex color: {token!r}")

    if low.startswith(("rgb(", "rgba(")) and s.endswith(")"):
        inner = s[s.index("(") + 1 : -1].strip()
        alpha = 1.0
        if "/" in inner:
            rgb_part, alpha_part = inner.split("/", 1)
            alpha = _parse_alpha_token(alpha_part)
            parts = [p for p in re.split(r"[\s,]+", rgb_part.strip()) if p]
        elif "," in inner:
            parts = [p.strip() for p in inner.split(",")]
            if len(parts) == 4:
                alpha = _parse_alpha_token(parts[3])
                parts = parts[:3]
        else:
            parts = [p for p in inner.split() if p]
        if len(parts) != 3:
            raise ValueError(f"Invalid rgb/rgba color: {token!r}")
        r = clamp(_parse_numeric_channel(parts[0], 255.0), 0.0, 255.0)
        g = clamp(_parse_numeric_channel(parts[1], 255.0), 0.0, 255.0)
        b = clamp(_parse_numeric_channel(parts[2], 255.0), 0.0, 255.0)
        return (r, g, b, alpha)

    if low.startswith(("hsl(", "hsla(")) and s.endswith(")"):
        inner = s[s.index("(") + 1 : -1].strip()
        alpha = 1.0
        if "/" in inner:
            hsl_part, alpha_part = inner.split("/", 1)
            alpha = _parse_alpha_token(alpha_part)
            parts = [p for p in re.split(r"[\s,]+", hsl_part.strip()) if p]
        elif "," in inner:
            parts = [p.strip() for p in inner.split(",")]
            if len(parts) == 4:
                alpha = _parse_alpha_token(parts[3])
                parts = parts[:3]
        else:
            parts = [p for p in inner.split() if p]
        if len(parts) != 3:
            raise ValueError(f"Invalid hsl/hsla color: {token!r}")
        h_raw = parts[0].lower().rstrip("deg")
        h = float(h_raw)
        sat = clamp(float(parts[1].rstrip("%")) / 100.0, 0.0, 1.0)
        light = clamp(float(parts[2].rstrip("%")) / 100.0, 0.0, 1.0)
        r, g, b = _hsl_to_rgb(h, sat, light)
        return (r, g, b, alpha)

    raise ValueError(f"Unsupported color format: {token!r}")


def extract_color_stops(css_value: str) -> list[RGBA]:
    """Extract all color stops from a CSS color or gradient expression."""
    if not isinstance(css_value, str) or not css_value.strip():
        raise ValueError("Empty color or gradient string")
    matches = _COLOR_TOKEN_RE.findall(css_value)
    if not matches:
        raise ValueError(f"No valid color tokens found in {css_value!r}")
    return [parse_color_rgba(m) for m in matches]


def extract_alpha(css_value: str) -> float:
    """Return alpha channel from a color string (max stop alpha if gradient)."""
    stops = extract_color_stops(css_value)
    return max(stop[3] for stop in stops)


def parse_overlay_rgb(value: Any) -> RGB:
    """Parse overlayRgb from 'r, g, b', [r, g, b], rgb(...), or #hex."""
    if isinstance(value, (list, tuple)) and len(value) == 3:
        return (
            clamp(float(value[0]), 0.0, 255.0),
            clamp(float(value[1]), 0.0, 255.0),
            clamp(float(value[2]), 0.0, 255.0),
        )
    if isinstance(value, str):
        s = value.strip()
        if s.startswith("#") or s.lower().startswith("rgb"):
            r, g, b, _ = parse_color_rgba(s)
            return (r, g, b)
        parts = [p.strip() for p in s.split(",") if p.strip()]
        if len(parts) == 3:
            return (
                clamp(float(parts[0]), 0.0, 255.0),
                clamp(float(parts[1]), 0.0, 255.0),
                clamp(float(parts[2]), 0.0, 255.0),
            )
    raise ValueError(f"Invalid overlayRgb: {value!r}")


def blend_over(fg: RGBA, bg: RGB) -> RGB:
    """Alpha-composite foreground RGBA over opaque background RGB."""
    r, g, b, a = fg
    return (
        a * r + (1.0 - a) * bg[0],
        a * g + (1.0 - a) * bg[1],
        a * b + (1.0 - a) * bg[2],
    )


def _srgb_channel_to_linear(c255: float) -> float:
    c = clamp(c255 / 255.0, 0.0, 1.0)
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _linear_to_srgb_channel(lin: float) -> float:
    val = clamp(lin, 0.0, 1.0)
    if val <= 0.0031308:
        return 12.92 * val * 255.0
    return (1.055 * (val ** (1.0 / 2.4)) - 0.055) * 255.0


def relative_luminance(rgb: RGB) -> float:
    """Compute WCAG 2.1 relative luminance in [0.0, 1.0]."""
    r = _srgb_channel_to_linear(rgb[0])
    g = _srgb_channel_to_linear(rgb[1])
    b = _srgb_channel_to_linear(rgb[2])
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(c1: RGB, c2: RGB) -> float:
    """Compute WCAG 2.1 contrast ratio in [1.0, 21.0]."""
    l1 = relative_luminance(c1)
    l2 = relative_luminance(c2)
    hi, lo = (l1, l2) if l1 >= l2 else (l2, l1)
    return (hi + 0.05) / (lo + 0.05)


def apca_lc(text_rgb: RGB, bg_rgb: RGB) -> float:
    """Compute APCA 0.98G Lightness Contrast (Lc) signed value.

    Positive Lc indicates dark text on light background; negative Lc indicates
    light text on dark background.
    """
    def _apca_y(rgb: RGB) -> float:
        r = (clamp(rgb[0], 0.0, 255.0) / 255.0) ** 2.4
        g = (clamp(rgb[1], 0.0, 255.0) / 255.0) ** 2.4
        b = (clamp(rgb[2], 0.0, 255.0) / 255.0) ** 2.4
        y = 0.2126729 * r + 0.7151522 * g + 0.0721750 * b
        return y + (0.022 - y) ** 1.414 if y < 0.022 else y

    yt = _apca_y(text_rgb)
    yb = _apca_y(bg_rgb)
    if abs(yb - yt) < 0.0005:
        return 0.0
    if yb > yt:
        sapc = (yb ** 0.56 - yt ** 0.57) * 1.14
        lc = 0.0 if sapc < 0.1 else sapc - 0.027
    else:
        sapc = (yb ** 0.65 - yt ** 0.62) * 1.14
        lc = 0.0 if sapc > -0.1 else sapc + 0.027
    return lc * 100.0


def _cbrt(x: float) -> float:
    return math.copysign(abs(x) ** (1.0 / 3.0), x)


def srgb_to_oklch(rgb: RGB) -> tuple[float, float, float]:
    """Convert 8-bit sRGB (0-255) to OKLCH (L in 0..1, C >= 0, h in 0..360)."""
    r = _srgb_channel_to_linear(rgb[0])
    g = _srgb_channel_to_linear(rgb[1])
    b = _srgb_channel_to_linear(rgb[2])

    l = 0.4121656120 * r + 0.5362752080 * g + 0.0514575653 * b
    m = 0.2118591070 * r + 0.6807189584 * g + 0.1074065790 * b
    s = 0.0883097947 * r + 0.2818474174 * g + 0.6302613616 * b

    l_ = _cbrt(l)
    m_ = _cbrt(m)
    s_ = _cbrt(s)

    L = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    bk = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    C = math.hypot(a, bk)
    h = math.degrees(math.atan2(bk, a)) % 360.0 if C > 1e-7 else 0.0
    return (L, C, h)


def _oklab_to_linear_srgb(L: float, a: float, b: float) -> RGB:
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b

    l_cube = l_ ** 3
    m_cube = m_ ** 3
    s_cube = s_ ** 3

    r_lin = +4.0767416621 * l_cube - 3.3077115913 * m_cube + 0.2309699292 * s_cube
    g_lin = -1.2684380046 * l_cube + 2.6097574011 * m_cube - 0.3413193965 * s_cube
    b_lin = -0.0041960863 * l_cube - 0.7034186147 * m_cube + 1.7076147010 * s_cube
    return (r_lin, g_lin, b_lin)


def oklch_to_srgb(L: float, C: float, h: float, gamut_clip: bool = True) -> RGB:
    """Convert OKLCH (L, C, h_deg) to sRGB (0-255), softly reducing chroma to stay in gamut."""
    L = clamp(L, 0.0, 1.0)
    C = max(0.0, C)
    h_rad = math.radians(h)
    cos_h = math.cos(h_rad)
    sin_h = math.sin(h_rad)

    r_lin, g_lin, b_lin = _oklab_to_linear_srgb(L, C * cos_h, C * sin_h)
    if gamut_clip and (min(r_lin, g_lin, b_lin) < -1e-5 or max(r_lin, g_lin, b_lin) > 1.0 + 1e-5):
        lo, hi = 0.0, C
        for _ in range(18):
            mid = 0.5 * (lo + hi)
            rl, gl, bl = _oklab_to_linear_srgb(L, mid * cos_h, mid * sin_h)
            if min(rl, gl, bl) >= 0.0 and max(rl, gl, bl) <= 1.0:
                lo = mid
            else:
                hi = mid
        r_lin, g_lin, b_lin = _oklab_to_linear_srgb(L, lo * cos_h, lo * sin_h)

    return (
        _linear_to_srgb_channel(r_lin),
        _linear_to_srgb_channel(g_lin),
        _linear_to_srgb_channel(b_lin),
    )


def simulate_cvd(rgb: RGB, kind: str = "deuteranopia") -> RGB:
    """Simulate color vision deficiency using Machado et al. (2009) severity 1.0 matrices."""
    r = clamp(rgb[0] / 255.0, 0.0, 1.0)
    g = clamp(rgb[1] / 255.0, 0.0, 1.0)
    b = clamp(rgb[2] / 255.0, 0.0, 1.0)
    if kind == "deuteranopia":
        sr = 0.367322 * r + 0.860646 * g - 0.227968 * b
        sg = 0.280085 * r + 0.672501 * g + 0.047413 * b
        sb = -0.011820 * r + 0.042940 * g + 0.968881 * b
    elif kind == "protanopia":
        sr = 0.152286 * r + 1.052583 * g - 0.204868 * b
        sg = 0.114503 * r + 0.786281 * g + 0.099216 * b
        sb = -0.003882 * r - 0.048116 * g + 1.051998 * b
    else:
        raise ValueError(f"Unsupported CVD simulation kind: {kind}")
    return (clamp(sr * 255.0, 0.0, 255.0), clamp(sg * 255.0, 0.0, 255.0), clamp(sb * 255.0, 0.0, 255.0))


def evaluate_surface_stops(fg_rgb: RGB, css_surface: str, overlay_rgb: RGB) -> tuple[float, float, RGB]:
    """Blend all stops of css_surface over overlay_rgb and return (min_ratio, worst_apca, worst_blended_rgb)."""
    stops = extract_color_stops(css_surface)
    best_min_ratio = 999.0
    worst_apca = 0.0
    worst_rgb = overlay_rgb
    for stop in stops:
        blended = blend_over(stop, overlay_rgb)
        r = contrast_ratio(fg_rgb, blended)
        if r < best_min_ratio:
            best_min_ratio = r
            worst_apca = apca_lc(fg_rgb, blended)
            worst_rgb = blended
    return best_min_ratio, worst_apca, worst_rgb


def audit_preset(name: str, preset: dict[str, Any], strict_ergo: bool = False) -> dict[str, Any]:
    """Run full WCAG 2.1 + APCA + Halation + CVD separation + Wallpaper audit on a preset."""
    errors: list[str] = []
    warnings: list[str] = []

    is_light = bool(preset.get("isLight", False))
    default_ink = "#1c1915" if is_light else "#f4f1ea"

    try:
        overlay = parse_overlay_rgb(preset["overlayRgb"])
    except (KeyError, ValueError) as exc:
        return {
            "name": name,
            "passed": False,
            "errors": [f"overlayRgb invalid or missing: {exc}"],
            "warnings": [],
            "metrics": {},
        }

    try:
        text_rgb = hex_to_rgb(preset["textColor"])
    except (KeyError, ValueError) as exc:
        return {
            "name": name,
            "passed": False,
            "errors": [f"textColor invalid or missing: {exc}"],
            "warnings": [],
            "metrics": {},
        }

    ui_text_str = preset.get("uiTextColor") or default_ink
    try:
        ui_text_rgb = hex_to_rgb(ui_text_str)
    except ValueError as exc:
        errors.append(f"uiTextColor invalid: {exc}")
        ui_text_rgb = text_rgb

    ui_muted_str = preset.get("uiMutedColor")
    ui_muted_rgb: RGB | None = None
    if ui_muted_str:
        try:
            ui_muted_rgb = hex_to_rgb(ui_muted_str)
        except ValueError as exc:
            errors.append(f"uiMutedColor invalid: {exc}")

    # Text luminance gates
    l_text = relative_luminance(text_rgb)
    l_ui = relative_luminance(ui_text_rgb)
    if is_light:
        if l_text > 0.18:
            errors.append(f"Light theme textColor luminance {l_text:.3f} > 0.18")
        if l_ui > 0.18:
            errors.append(f"Light theme uiTextColor luminance {l_ui:.3f} > 0.18")
    else:
        if l_text < 0.70:
            errors.append(f"Dark theme textColor luminance {l_text:.3f} < 0.70")
        if l_ui < 0.70:
            errors.append(f"Dark theme uiTextColor luminance {l_ui:.3f} < 0.70")
        if l_text > 0.89 or l_ui > 0.89:
            warnings.append(
                f"Halation risk: dark text luminance ({max(l_text, l_ui):.3f}) > 0.89; consider softening off-white"
            )

    metrics: dict[str, Any] = {
        "isLight": is_light,
        "textLuminance": round(l_text, 4),
        "uiTextLuminance": round(l_ui, 4),
    }

    # Check primary surfaces (threshold >= 4.5)
    surface_blends: dict[str, RGB] = {}
    for field in PRIMARY_TEXT_SURFACES:
        if field not in preset:
            errors.append(f"Missing required surface field: {field}")
            continue
        try:
            ratio, lc, blended = evaluate_surface_stops(ui_text_rgb, preset[field], overlay)
            surface_blends[field] = blended
            metrics[f"{field}Ratio"] = round(ratio, 2)
            metrics[f"{field}Apca"] = round(lc, 1)
            if ratio < 4.5:
                errors.append(f"{field} contrast {ratio:.2f} < 4.5")
            if abs(lc) < 75.0:
                warnings.append(f"{field} APCA |Lc|={abs(lc):.1f} < 75")
        except ValueError as exc:
            errors.append(f"{field} invalid color: {exc}")

    # Check modal surfaces (threshold >= 7.0 AAA)
    for field in MODAL_TEXT_SURFACES:
        if field not in preset:
            errors.append(f"Missing required modal field: {field}")
            continue
        try:
            ratio, lc, _ = evaluate_surface_stops(ui_text_rgb, preset[field], overlay)
            metrics[f"{field}Ratio"] = round(ratio, 2)
            metrics[f"{field}Apca"] = round(lc, 1)
            if ratio < 7.0:
                errors.append(f"{field} contrast {ratio:.2f} < 7.0 (AAA required)")
            if abs(lc) < 90.0:
                warnings.append(f"{field} APCA |Lc|={abs(lc):.1f} < 90")
        except ValueError as exc:
            errors.append(f"{field} invalid color: {exc}")

    # Check bubble & inputCardBg across ALL stops (>= 4.5)
    for bubble_field in ("bg", "inputCardBg"):
        if bubble_field not in preset:
            errors.append(f"Missing required field: {bubble_field}")
            continue
        try:
            ratio, lc, blended = evaluate_surface_stops(text_rgb, preset[bubble_field], overlay)
            surface_blends[bubble_field] = blended
            metrics[f"{bubble_field}Ratio"] = round(ratio, 2)
            metrics[f"{bubble_field}Apca"] = round(lc, 1)
            if ratio < 4.5:
                errors.append(f"{bubble_field} worst-stop contrast {ratio:.2f} < 4.5")
            if not is_light and ratio > 17.5:
                warnings.append(f"{bubble_field} contrast {ratio:.2f} > 17.5 (possible dark-mode glare)")
        except ValueError as exc:
            errors.append(f"{bubble_field} invalid color: {exc}")

    # Check pillTextColor on pillBg (>= 4.5)
    if "pillBg" in preset:
        pill_text_str = preset.get("pillTextColor") or ui_text_str
        try:
            pill_text_rgb = hex_to_rgb(pill_text_str)
            ratio, lc, _ = evaluate_surface_stops(pill_text_rgb, preset["pillBg"], overlay)
            metrics["pillRatio"] = round(ratio, 2)
            metrics["pillApca"] = round(lc, 1)
            if ratio < 4.5:
                errors.append(f"pillBg contrast {ratio:.2f} < 4.5")
        except ValueError as exc:
            errors.append(f"pillBg/pillTextColor invalid: {exc}")
    else:
        errors.append("Missing required field: pillBg")

    # Check uiMutedColor on sidebarBg and aiCardBg (>= 4.5)
    if ui_muted_rgb is not None:
        for host in ("sidebarBg", "aiCardBg"):
            if host in surface_blends:
                r_m = contrast_ratio(ui_muted_rgb, surface_blends[host])
                lc_m = apca_lc(ui_muted_rgb, surface_blends[host])
                metrics[f"muted_{host}Ratio"] = round(r_m, 2)
                metrics[f"muted_{host}Apca"] = round(lc_m, 1)
                if r_m < 4.5:
                    errors.append(f"uiMutedColor on {host} contrast {r_m:.2f} < 4.5")
                if abs(lc_m) < 60.0:
                    warnings.append(f"uiMutedColor on {host} APCA |Lc|={abs(lc_m):.1f} < 60")

    # Check glow alpha (<= 0.18)
    for g_field in ("glow", "secondaryGlow"):
        if g_field in preset:
            try:
                alpha = extract_alpha(preset[g_field])
                metrics[f"{g_field}Alpha"] = round(alpha, 3)
                if alpha > 0.18 + 1e-6:
                    errors.append(f"{g_field} alpha {alpha:.2f} > 0.18")
            except ValueError as exc:
                errors.append(f"{g_field} invalid: {exc}")
        elif g_field == "glow":
            errors.append("Missing required field: glow")

    # Check wallpaper safety rule
    wallpaper = str(preset.get("wallpaper", "") or "").strip()
    if wallpaper:
        if "aiCardBg" in preset:
            ai_alpha = extract_alpha(preset["aiCardBg"])
            if ai_alpha < 0.84 - 1e-6:
                errors.append(f"Wallpaper active: aiCardBg alpha {ai_alpha:.2f} < 0.84")
        if "sidebarBg" in preset:
            sb_alpha = extract_alpha(preset["sidebarBg"])
            if sb_alpha < 0.82 - 1e-6:
                errors.append(f"Wallpaper active: sidebarBg alpha {sb_alpha:.2f} < 0.82")
        if preset.get("sidebarEnhanceText") is not True:
            errors.append("Wallpaper active: sidebarEnhanceText must be true")
        # Worst-case white/gray stress telemetry
        if "sidebarBg" in preset:
            w_sb, _, _ = evaluate_surface_stops(ui_text_rgb, preset["sidebarBg"], (235.0, 235.0, 235.0))
            metrics["worstWhiteSidebarRatio"] = round(w_sb, 2)
            if w_sb < 4.5:
                warnings.append(f"Wallpaper bright-corner risk: sidebar drops to {w_sb:.2f} over light area")
        if "aiCardBg" in preset:
            w_ai, _, _ = evaluate_surface_stops(ui_text_rgb, preset["aiCardBg"], (235.0, 235.0, 235.0))
            metrics["worstWhiteAiRatio"] = round(w_ai, 2)
            if w_ai < 4.5:
                warnings.append(f"Wallpaper bright-corner risk: aiCard drops to {w_ai:.2f} over light area")

    # Separation telemetry (Deuteranopia + Selected Card)
    if "bg" in surface_blends and "aiCardBg" in surface_blends:
        sep = contrast_ratio(surface_blends["bg"], surface_blends["aiCardBg"])
        d_sep = contrast_ratio(
            simulate_cvd(surface_blends["bg"], "deuteranopia"),
            simulate_cvd(surface_blends["aiCardBg"], "deuteranopia"),
        )
        metrics["bubbleAiSeparation"] = round(sep, 2)
        metrics["deutanBubbleAiSeparation"] = round(d_sep, 2)
        concept_low = str(preset.get("concept", "")).lower()
        if "ai lạnh" in concept_low or "split" in name.lower():
            if sep < 1.20 or d_sep < 1.18:
                warnings.append(
                    f"Split preset bubble/AI luminance separation low (normal={sep:.2f}, deutan={d_sep:.2f})"
                )

    if "cardBg" in surface_blends and "cardSelectedBg" in surface_blends:
        sel_sep = contrast_ratio(surface_blends["cardBg"], surface_blends["cardSelectedBg"])
        metrics["cardSelectedDelta"] = round(sel_sep, 2)
        if sel_sep < 1.15:
            warnings.append(f"cardSelectedBg vs cardBg separation {sel_sep:.2f} < 1.15")

    if strict_ergo and warnings:
        # Surface ergonomic warnings visibly without conflating with WCAG AA failures unless flagged
        pass

    return {
        "name": name,
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "metrics": metrics,
    }

# Clearframe Contrast & Readability Specification

Clearframe enforces a 4-layer readability standard so glassmorphic Antigravity themes stay legible across 4-8 hour coding and review sessions.

## 1. Alpha Compositing (Glass over `overlayRgb`)

A semi-transparent card (`R_s, G_s, B_s, alpha`) rendered over an estimated backdrop (`overlayRgb` = `R_o, G_o, B_o`) produces:

```text
C_visible = alpha * C_surface + (1 - alpha) * C_overlay
```

Never evaluate contrast against `pureBg` mid-gradients; always composite against `overlayRgb`, and when a theme includes multi-stop gradients (`bg`, `inputCardBg`), evaluate **every stop** and pass on the worst-case minimum ratio.

## 2. WCAG 2.1 Relative Luminance & Ratio

For each 8-bit channel `c` normalized to `c_s = c / 255`:

- If `c_s <= 0.04045`: `c_lin = c_s / 12.92`
- Else: `c_lin = ((c_s + 0.055) / 1.055) ^ 2.4`
- `L = 0.2126 * R_lin + 0.7152 * G_lin + 0.0722 * B_lin`
- `ratio = (max(L1, L2) + 0.05) / (min(L1, L2) + 0.05)`

## 3. Mandatory Thresholds (Hard Gate)

| Pair | Minimum Threshold |
| --- | --- |
| `uiTextColor` on `sidebarBg`, `aiCardBg`, `headerBg`, `btnBg`, `inputGlassBg`, `cardBg`, `cardSelectedBg` | `>= 4.5` (AA) |
| `uiTextColor` on `modalBg` and `modalHeaderBg` | `>= 7.0` (AAA) |
| `textColor` on all gradient stops of `bg` and `inputCardBg` | `>= 4.5` (AA) |
| `pillTextColor` on `pillBg` | `>= 4.5` (AA) |
| `uiMutedColor` on `sidebarBg` and `aiCardBg` | `>= 4.5` (AA) |
| Dark theme text luminance (`L(textColor)`, `L(uiTextColor)`) | `>= 0.70` |
| Light theme text luminance (`L(textColor)`, `L(uiTextColor)`) | `<= 0.18` |
| Glow alpha (`glow`, `secondaryGlow`) | `<= 0.18` |
| Active wallpaper (`wallpaper != ""`) | `aiCardBg` alpha `>= 0.84`, `sidebarBg` alpha `>= 0.82`, `sidebarEnhanceText: true` |

## 4. APCA 0.98G & Anti-Halation Ergonomics

- **APCA `Lc` targets:** Primary surfaces `|Lc| >= 75`, Muted metadata `|Lc| >= 60`, Modals `|Lc| >= 90`.
- **Anti-halation guardrail:** In dark mode, avoid pure `#ffffff` on `#000000` (21:1) or text luminance `> 0.89`, which causes edge bloom for developers with astigmatism and blurs Vietnamese diacritics. Prefer warm or cool off-whites (`L` around `0.78 - 0.84`).
- **Repair order when a preset fails:** First increase surface `alpha` in steps of `0.02 - 0.04` (up to `0.98`), enable `sidebarEnhanceText: true` if a wallpaper is active, or shift ink lightness toward `#ebe7df` (dark) / `#1c1915` (light). Never add CSS `backdrop-filter`.

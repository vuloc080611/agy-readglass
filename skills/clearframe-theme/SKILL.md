---
name: clearframe-theme
description: >-
  Design, switch, or scaffold Clearframe work-session glass themes for Antigravity.
  Use when the user asks for a readable low-fatigue glass theme, a named work session
  (deep work, review split, night/lantern, daylight paper, screenshot, one accent),
  or a theme generated from a photo or mood that must pass WCAG AA contrast before saving.
  Do not use for Rust engine forks, live backdrop-filter blur, or app.asar patches.
license: MIT
compatibility: Antigravity IDE, Antigravity 2.0, agy-theme CDP engine
---

# Clearframe Theme Designer

Create or select high-readability glass themes that stay legible for full work sessions.

## Built-in Work-Session Presets

- **Deep Ink** (default): Dark charcoal, minimal amber accent, no stickers.
- **Review Split**: Warm user bubble vs cool slate AI card with luminance + border separation.
- **Lantern Hour**: Warm low-blue charcoal with minimal geometric `lantern-mark.svg`.
- **Mekong Morning**: Warm mist-paper light mode (`isLight: true`, deep charcoal ink).
- **Screenshot Clean**: Neutral high-opacity surfaces, near-zero glow, clean for demos/docs.
- **Delta Mint**: Neutral dark slate with a single muted mint accent.

## Workflow

1. **Clarify intent:** Identify whether the request matches one of the 6 presets or needs a new theme from a photo or mood. If unclear, ask at most 1-2 short questions (which work session, dark or light).
2. **Existing session match:** If it maps directly to one of the 6 presets, instruct the user to select it in Antigravity's Custom Theme UI (`Alt+Shift+T`), install a pack with [install_pack.py](./scripts/install_pack.py), or rotate default preset by work shift with [shift_preset.py](./scripts/shift_preset.py). Do not create redundant duplicate presets.
3. **New theme from photo or mood:**
   - Read [theme-schema.md](./references/theme-schema.md) and [contrast.md](./references/contrast.md).
   - Extract 2 balanced accent colors. Do not bundle copyrighted fanart, anime posters, or watermarked images; leave `wallpaper: ""` unless the user provides their own image with clear rights.
   - If the user provides a local wallpaper image, run [analyze_wallpaper.py](./scripts/analyze_wallpaper.py) to measure Left-22% Sidebar and Right-78% Chat brightness zones and obtain safe `overlayRgb` and opacity floors.
   - Generate the preset deterministically using [scaffold_theme.py](./scripts/scaffold_theme.py).
4. **Mandatory contrast gate:** Run `python scripts/check_contrast.py --apca --file <path>` (or on `themes/themes.json` when working inside the Clearframe repo). If it fails, adjust surface opacity or ink luminance as described in [contrast.md](./references/contrast.md). Never lower thresholds.
5. **Engine boundary:** Never run `cargo`, patch shortcuts, or modify Antigravity binaries unless the user explicitly states they already cloned `agy-theme` and asks to run `agy-theme build` inside that engine repo.

## Prohibited Actions

- Never add CSS `backdrop-filter: blur()`.
- Never hardcode user-specific absolute paths (`C:\Users\...`, `/Users/...`).
- Never set `isLight: true` with light `textColor`.
- Never exceed glow alpha `0.18`.

## Response Format

Reply concisely with: preset name, primary & secondary hex accents, sidebar / AI card / modal contrast ratios (plus APCA `Lc`), and explicit confirmation that AI card text passes WCAG AA/AAA.

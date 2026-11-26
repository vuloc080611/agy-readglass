---
name: clearframe-audit
description: >-
  Audit and minimally repair existing Antigravity themes.json or pack.json files so
  sidebars, AI cards, modals, and muted labels become readable without losing the user's
  wallpaper or accent palette. Use when the user reports washed-out text, unreadable glass
  sidebars, glare, or wants WCAG AA/AAA + APCA contrast verification on a custom theme.
license: MIT
compatibility: Antigravity IDE, Antigravity 2.0, agy-theme, antigravity-custom-theme-mod
---

# Clearframe Contrast Audit & Theme Rescue

Diagnose readability failures in any `themes.json` (including third-party wallpaper themes) and apply minimal, reversible repairs.

## Workflow

1. **Locate target file:** Ask for or inspect the user's `themes.json` or single `pack.json`. Supports `agy-theme` flat maps, `mod-v2` (`defaultTheme` + `presets`), and single packs.
2. **Run initial diagnosis:** Execute:
   ```bash
   python scripts/check_contrast.py --apca --no-sync-check --file <target.json>
   ```
   Read [contrast.md](./references/contrast.md) if explaining why gradient stops, alpha compositing, halation, or `uiMutedColor` failed.
3. **Apply minimal repair:** Dry-run first to preview exact changes:
   ```bash
   python scripts/audit_repair.py --input <target.json>
   ```
   When the user confirms saving repairs, run with `--in-place --fix` (which automatically creates a `.bak` backup) or `--output <new.json>`.
   - Preserves `wallpaper`, `primary`, `secondary`, and theme personality.
   - Enables `sidebarEnhanceText: true` and minimum safe opacities when `wallpaper` is set.
   - Clamps excess `glow` alpha (`> 0.18`) and upgrades failing cards/modals/muted text.
4. **Verify exit code 0:** Re-run `check_contrast.py --apca --no-sync-check --file <repaired.json>` and confirm every preset passes.

## Response Format

Report a concise Before/After table (Sidebar, AI Card, Modal, Muted ratios + APCA `Lc`) and list the exact fields adjusted.

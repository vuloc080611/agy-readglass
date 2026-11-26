---
name: clearframe-ide-sync
description: >-
  Generate matching Antigravity IDE or VS Code workbench.colorCustomizations from a
  Clearframe preset, fixing low-contrast scrollbars and providing color-vision-safe diff
  highlights. Use when the user wants their code editor, tabs, terminal, and diffs to match
  their Clearframe chat theme.
license: MIT
compatibility: Antigravity IDE, Visual Studio Code
---

# Clearframe IDE Color Sync

Align editor panes, sidebars, tabs, terminal, scrollbars, and diffs with the active Clearframe preset.

## Workflow

1. **Select source preset:** Identify which Clearframe preset (`Deep Ink`, `Review Split`, `Lantern Hour`, `Mekong Morning`, `Screenshot Clean`, `Delta Mint`, or custom `pack.json`) the user wants to mirror. Read [ide-tokens.md](./references/ide-tokens.md) for token mapping details.
2. **Generate customizations:** Run:
   ```bash
   python scripts/export_ide_sync.py --preset "<Preset Name>"
   ```
   - Add `--cvd-safe` if the user wants color-vision-deficiency friendly Blue/Amber diff backgrounds instead of Green/Red.
   - Add `--scope "<Current Color Theme>"` if the user only wants overrides applied under a specific base theme.
3. **Safe delivery:** Output the generated `"workbench.colorCustomizations"` JSON snippet for the user to paste into User Settings (`settings.json`). Only run `--apply <path-to-settings.json>` (which creates a `.bak` backup and refuses files with JSONC comments) if the user explicitly asks to write to disk.

## Safety Rules

- Never silently overwrite user `settings.json`.
- Always verify scrollbar slider tokens maintain `>= 3:1` visibility against editor background.

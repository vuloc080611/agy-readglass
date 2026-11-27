# Changelog

All notable changes to **Clearframe (`agy-readglass`)** are documented here.

## [1.1.0] - 2026-11-27

### Added
- `tools/shift_preset.py`: circadian and named work-shift preset switcher (`morning`, `deep`, `review`, `night`, `screenshot`, `mint`) with `--dry-run`, `--time`, and `.bak` backup.
- `src/clearframe_core/env_paths.py`: non-destructive Antigravity IDE/CLI/skills path detection integrated into `tools/doctor.py` and `tools/export_ide_sync.py --detect-settings`.
- Interactive Web Studio (`docs/index.html`) upgrades: mobile-first preview ordering (`<= 980px`), VI/EN language toggle, in-browser OKLCH + Dark/Light harmony lab, 2-zone P90 wallpaper analysis with 1-click alpha auto-fix, Paste & Rescue `themes.json` fixer, full 25+ key IDE sync + CVD diff preview, and `mod-v2` JSON export.
- `docs/assets/social-preview.png` (`1280x640`) + Open Graph / Twitter Card metadata in `docs/index.html`.
- `CONTRIBUTING.md`, `CHANGELOG.md`, and live GitHub Actions CI badge in `README.md`.

## [1.0.0] - 2026-11-26

### Added
- Initial release with 6 work-session presets (`Deep Ink` #1, `Review Split`, `Lantern Hour`, `Mekong Morning`, `Screenshot Clean`, `Delta Mint`) and minimal geometric `themes/assets/lantern-mark.svg`.
- 4-layer readability engine (`WCAG 2.1`, `APCA 0.98G`, anti-halation guardrail, Machado 2009 CVD separation) and pure-Python OKLCH scaffolder + wallpaper zone probe.
- 3 standalone Agent Skills (`clearframe-theme`, `clearframe-audit`, `clearframe-ide-sync`) + `plugin.json` + GitHub Actions validation workflow.

# Contributing to Clearframe (`agy-readglass`)

Thank you for contributing readable, low-fatigue work-session themes and tools!

## Adding a New Work-Session Preset (3 Steps)

1. **Scaffold deterministically on OKLCH:**
   ```bash
   python tools/scaffold_theme.py --name "Your Preset" --primary "#d4a574" --secondary "#8aa4b8" --mode dark --output themes/packs/your-preset.json
   ```
   Register the entry in `themes/manifest.json` (keep `Deep Ink` as the first entry unless changing defaults is requested).

2. **Sync packs, skill bundles, SVG swatches, and Web Studio:**
   ```bash
   python tools/sync_packs.py
   python tools/bundle_skills.py
   python tools/render_swatches.py
   ```

3. **Run all verification gates (must exit `0`):**
   ```bash
   python -m unittest discover -s tests -v
   python tools/check_contrast.py --apca --strict-ergo
   ```

## Hard Rules

- No copyrighted anime/fanart wallpapers, WLOP assets, or copied upstream `SKILL.md` / `core.js`.
- No CSS `backdrop-filter` rules, `app.asar` patches, or absolute local home paths (`C:\Users\...`, `/Users/...`).
- Keep core Python tools **standard-library only** (zero third-party pip packages).

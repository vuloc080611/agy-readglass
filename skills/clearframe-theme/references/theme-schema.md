# Clearframe `themes.json` Schema Reference

Clearframe uses the flat JSON map compatible with `agy-theme` (first entry is loaded as the default preset). Each standalone file under `themes/packs/` mirrors one preset object plus a `"name"` key so it can be shared and merged cleanly.

## Token-to-UI Surface Mapping (Antigravity IDE & Antigravity 2.0)

| Token | Type | UI Region & Purpose |
| --- | --- | --- |
| `concept` | string | Short session summary ending with `• AA` |
| `primary`, `secondary` | hex | Primary & secondary accent colors (never used directly as small body text) |
| `glow`, `secondaryGlow` | rgba | Ambient accent glow (`alpha <= 0.18`) |
| `overlayRgb` | `"r, g, b"` | Estimated solid RGB behind translucent surfaces |
| `textColor` | hex | Text color inside user chat bubbles (`bg`, `inputCardBg`) |
| `uiTextColor` | hex | Primary UI ink across sidebar, AI cards, headers, buttons, and modals |
| `uiMutedColor` | hex | Timestamps, model labels, and secondary hints (`>= 4.5` on sidebar & AI cards) |
| `bg` | color/gradient | User prompt bubble surface |
| `frameBg`, `borderColor`, `innerBorder` | css | Outer frame gradient and subtle structural borders |
| `sidebarBg`, `sidebarHoverBg`, `sidebarEnhanceText` | rgba / bool | Left navigation rail (workspaces, chats, skills) |
| `aiCardBg`, `aiCardBorder` | rgba | AI response cards and auxiliary panels |
| `headerBg`, `headerBorder` | rgba | Top window/panel header bar |
| `unifiedGlass`, `sidebarBlur`, `headerBlur` | bool / px | Pre-baked engine glass hints (never write CSS `backdrop-filter`) |
| `btnBg`, `inputGlassBg`, `inputCardBg` | css | Interactive buttons and prompt composer box |
| `modalBg`, `modalHeaderBg`, `cardBg`, `cardSelectedBg` | rgba | Custom Theme Studio (`Alt+Shift+T`) modal and preset picker cards |
| `pureBg` | css | Background canvas gradient/color when `wallpaper` is empty |
| `wallpaper`, `clearBackdrop` | string / bool | Optional background image path (`""` by default) and `clearBackdrop: true` |
| `isOrnament`, `isLight` | bool | Ornament toggle and light/dark mode flag |
| `sticker`, `stickerW`, `stickerH`, `stickerTop`, `stickerRight`, `cornerSvg` | mixed | Optional SVG mark positioning (used only when `isOrnament: true`) |
| `pillBg`, `pillTextColor`, `pillBorder`, `pillHoverBg` | css | Status chips, model tags, and slash-command pills |

## Forbidden Patterns

- CSS `backdrop-filter` rules
- Binary/asar patches or absolute home-directory paths (`C:\Users\...`, `/Users/...`, `/home/...`)
- Copyrighted fanart/anime/WLOP wallpapers or copied upstream assets

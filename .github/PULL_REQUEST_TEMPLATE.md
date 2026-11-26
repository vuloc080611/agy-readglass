## Checklist

- [ ] Added/updated `themes/packs/<slug>.json` and ran `python tools/sync_packs.py`
- [ ] Ran `python tools/bundle_skills.py` and `python tools/render_swatches.py`
- [ ] `python tools/check_contrast.py --apca --strict-ergo` exits `0`
- [ ] `python -m unittest discover -s tests -v` passes
- [ ] No copyrighted images/fanart, no `backdrop-filter`, no absolute local home paths

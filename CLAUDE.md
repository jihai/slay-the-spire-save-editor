# CLAUDE.md

## Quick Reference

```bash
source .venv/bin/activate    # activate venv (managed by uv)
python -m gui                # run the GUI app
python -m pytest tests/ -v   # run tests
uv pip install <package>     # add new dependencies (then update requirements.txt)
```

## Architecture

PySide6 desktop app for editing Slay the Spire `.autosave` files.

### Save file format

```
JSON dict  →  XOR encrypt (key: b"key")  →  Base64 encode  →  .autosave file
```

Save location (macOS): `~/Library/Application Support/Steam/steamapps/common/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves/`

### Layers

| Layer | File(s) | Purpose |
|-------|---------|---------|
| Codec | `sts_save_editor.py` | XOR + Base64 encode/decode; also works as a standalone CLI (`decode`/`encode`/`edit`) |
| File I/O | `gui/save_io.py` | `load_save`, `write_save`, `create_backup` (timestamped `.bak.*` copies) |
| Data model | `gui/save_model.py` | QObject wrapping the raw save dict. Typed properties for ~10 fields (gold, HP, cards, potions, relics, etc.). Emits `data_changed` signal on mutation. Dirty tracking for unsaved state. ~80 other save-file fields pass through untouched. |
| Game data | `gui/game_data.py` | Loads `cards.csv`, `potions.csv`, `relics.csv` + `wiki_data.json` into frozen dataclasses (`CardInfo`, `PotionInfo`, `RelicInfo`). Dual-index dicts: `*_by_name` (display name) and `*_by_id` (internal save-file ID). |
| Main window | `gui/main_window.py` | Menu bar + QTabWidget with 4 panels + status bar |
| Panels | `gui/panels/{stats,cards,potions,relics}_panel.py` | One QWidget per tab. Stats has spin boxes; Cards/Relics have split-view (current list + available browser); Potions has dynamic combo boxes. |
| Widgets | `gui/widgets/` | `DetailStrip` (inline preview) and `ImagePreviewDialog` (modal zoom) |

### Game resources

`game_resources/` contains:
- `cards.csv` (356 cards), `relics.csv` (186 relics), `potions.csv` (43 potions)
- `wiki_data.json` — descriptions, flavor text, image paths (scraped from wiki)
- `images/{cards,relics,potions}/` — 605 downloaded thumbnails

Re-scrape with: `python scripts/scrape_wiki.py`

### Signal pattern

All panels use an `_updating` boolean guard to prevent signal loops:
1. `SaveModel.data_changed` fires → panel `_refresh()` sets `_updating = True`
2. Widgets are updated programmatically (which fires their change signals)
3. Widget signal handlers check `if self._updating: return` to skip model writes
4. `_refresh()` sets `_updating = False` when done

## Python Environment

- Virtual env managed by **uv** at `.venv/`
- Activate: `source .venv/bin/activate`
- Install all deps: `uv pip install -r requirements.txt`
- Add a new dep: `uv pip install <package>`, then add it to `requirements.txt`
- Key dependencies: `PySide6`, `beautifulsoup4`, `requests`

## Testing

```bash
python -m pytest tests/ -v
```

Tests cover: save encoding round-trip, SaveModel properties/signals/dirty tracking, GameData loading and lookups. Test template: `raw_templates/ironclad_save.json`.

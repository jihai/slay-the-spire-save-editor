# CLAUDE.md

## Quick Reference

```bash
source .venv/bin/activate    # activate venv (managed by uv)
python -m gui                # run STS1 editor (default)
python -m gui --game 2       # run STS2 editor
python -m pytest tests/ -v   # run tests
uv pip install <package>     # add new dependencies (then update requirements.txt)
```

## Architecture

PySide6 desktop app for editing Slay the Spire save files. Supports both STS1 and STS2.

### Save file formats

**STS1:** `JSON dict → XOR encrypt (key: b"key") → Base64 encode → .autosave file`
Save location (macOS): `~/Library/Application Support/Steam/steamapps/common/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves/`

**STS2:** Plain JSON `.save` files (no encryption). Nested structure with `players[0]` containing player data.
Save location (macOS): `~/Library/Application Support/SlayTheSpire2/steam/<long_steam_id>/profile1/saves/`

> **Important:** Steam Cloud sync must be disabled for STS2 save editing to work. Otherwise Steam Cloud will overwrite local changes on next launch. Disable via Steam → Right-click STS2 → Properties → General → uncheck "Keep game saves in the Steam Cloud".

**STS2 save loading priority (game reads short-id location first):**
1. Game loads from `Steam/userdata/<short_id>/2868840/remote/profile1/saves/` (validated via `remotecache.vdf` SHA)
2. If backup (`.save.backup`) exists → game uses it over the primary file
3. On "save & exit", game writes to long-id location which overwrites short-id on next sync

**Our editor's write strategy** (makes edits take effect immediately):
1. Write save to long-id folder (`SlayTheSpire2/steam/<long_id>/...`)
2. Delete `.backup` file so it doesn't override our edit
3. Copy save to short-id folder (`Steam/userdata/<short_id>/2868840/remote/...`)
4. Update `remotecache.vdf` with new SHA-1, size, and timestamp

**Steam ID mapping:** Directory names use long Steam IDs (Steam64, e.g. `76561198060466028`). The app converts to/from short IDs (account ID, e.g. `100200300`) via: `long = short + 76561197960265728`.

### Layers

| Layer | File(s) | Purpose |
|-------|---------|---------|
| Config | `gui/game_config.py` | Frozen dataclass with version-specific constants (save dir, file glob, encryption, etc.). Factory functions: `sts1_config()`, `sts2_config()`. |
| Codec | `sts_save_editor.py` | XOR + Base64 encode/decode for STS1; also works as a standalone CLI (`decode`/`encode`/`edit`) |
| File I/O | `gui/save_io.py` | `load_save`, `write_save`, `find_save_files` — accepts `GameConfig` to handle both encrypted (STS1) and plain JSON (STS2). STS2 `write_save` deletes `.backup`, syncs to old Steam location, and updates `remotecache.vdf`. |
| Data model | `gui/save_model.py` | STS1 model: QObject wrapping flat save dict. Typed properties for ~10 fields. |
| Data model (STS2) | `gui/save_model_sts2.py` | STS2 model: same API as SaveModel but routes through `players[0]` for the nested structure. Maps STS2 field names (`current_hp` → `current_health`). |
| Game data | `gui/game_data.py` | Loads CSVs + `wiki_data.json` from configurable `resources_dir`. Works for both `game_resources/` (STS1) and `game_resources_sts2/` (STS2). |
| Main window | `gui/main_window.py` | Accepts `GameConfig`, creates appropriate model and game data. Menu bar + QTabWidget with 5 panels + status bar. STS2 mode adds a Steam User toolbar for switching between detected accounts. |
| Panels | `gui/panels/{stats,cards,potions,relics,raw_json}_panel.py` | One QWidget per tab. Cards panel supports upgrades for both STS1 and STS2 (Upgrade Selected / Upgrade All buttons). |
| Widgets | `gui/widgets/` | `DetailStrip` (inline preview) and `ImagePreviewDialog` (modal zoom) |
| Settings | `gui/settings.py` | Persists user preferences (Steam user ID) to `~/.config/sts-save-editor/settings.json`. |
| Steam | `gui/steam.py` | Steam ID conversion (`short_to_long_steam_id`, `long_to_short_steam_id`), user detection by scanning `SlayTheSpire2/steam/`, persona name lookup from `loginusers.vdf`. Functions: `detect_steam_users()`, `sts2_save_dir()`, `get_steam_display_names()`. |

### Game resources

`game_resources/` (STS1) contains:
- `cards.csv` (356 cards), `relics.csv` (186 relics), `potions.csv` (43 potions)
- `wiki_data.json` — descriptions, flavor text, image paths
- `images/{cards,relics,potions}/` — thumbnails
- Re-scrape: `python scripts/scrape_wiki.py`

`game_resources_sts2/` (STS2) contains:
- `cards.csv` (576 cards), `relics.csv` (288 relics), `potions.csv` (63 potions)
- `wiki_data.json` + `images/` — all generated from wiki
- Re-scrape: `python scripts/scrape_wiki_sts2.py`
- IDs follow `CARD.NAME`, `RELIC.NAME`, `POTION.NAME` format (inferred from wiki names)

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

Tests cover: save encoding round-trip, SaveModel properties/signals/dirty tracking, GameData loading and lookups for both STS1 and STS2. Test templates: `raw_templates/ironclad_save.json` (STS1), `raw_templates/sts2_silent_save.json` (STS2).

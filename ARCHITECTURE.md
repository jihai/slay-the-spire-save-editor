# Slay the Spire Save Editor — Architecture

## Overview

A desktop GUI application (PySide6/Qt) for editing Slay the Spire (STS1) and Slay the Spire 2 (STS2) save files. A config-driven architecture handles both game versions through a shared codebase, with version-specific models, resource sets, and encoding strategies.

## How Save Files Work

### STS1

Slay the Spire stores game state as `.autosave` files using a simple encoding pipeline:

```
JSON dict  →  JSON string  →  XOR encrypt (key: "key")  →  Base64 encode  →  .autosave file
```

Decoding reverses the process. The existing `sts_save_editor.py` implements this in two functions: `decode_save()` and `encode_save()`.

The default save location on macOS:
```
~/Library/Application Support/Steam/steamapps/common/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves/
```

Files: `IRONCLAD.autosave`, `SILENT.autosave`, `DEFECT.autosave`, `WATCHER.autosave`

### STS2

Slay the Spire 2 stores game state as plain JSON `.save` files — no encryption.

The save structure is nested: player data lives under `players[0]` (unlike STS1's flat dict). Key differences from STS1:

| Aspect | STS1 | STS2 |
|--------|------|------|
| HP field | `current_health` | `current_hp` |
| Card upgrades | `upgrades` (int) | `current_upgrade_level` (int) |
| Act field | `act_num` | `current_act_index` |
| Character detection | Starter relic lookup | `character_id` (e.g., `"CHARACTER.SILENT"`) |
| Cards/potions/relics | Flat strings or simple dicts | Objects with `id` field (e.g., `{"id": "CARD.STRIKE"}`) |
| ID format | Display names (e.g., `Strike_R`) | Dotted names (e.g., `CARD.STRIKE`) |

The primary save location uses the long Steam ID:
```
~/Library/Application Support/SlayTheSpire2/steam/<long_steam_id>/profile1/saves/
```
A secondary copy exists at `Steam/userdata/<short_id>/2868840/remote/profile1/saves/` (used by the game for initial loading, synced via `remotecache.vdf`).

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  app.py + __main__.py                                            │
│  Parses --game flag, resolves Steam user (STS2), creates config  │
└──────────┬───────────────────────────────────────────────────────┘
           │ creates
           ▼
    ┌──────────────┐
    │  GameConfig   │  Frozen dataclass — all version-specific constants
    │               │  Factory: sts1_config() / sts2_config(steam_user_id)
    └──────┬───────┘
           │ injected into
           ▼
┌──────────────────────────────────────────────────────────────────┐
│                         MainWindow                                │
│  ┌──────────────────────────────────────────────────────────┐     │
│  │  QTabWidget                                              │     │
│  │  ┌───────┬───────┬──────────┬────────┬──────────┐        │     │
│  │  │ Stats │ Cards │ Potions  │ Relics │ Raw JSON │ (tabs) │     │
│  │  └───────┴───────┴──────────┴────────┴──────────┘        │     │
│  └──────────────────────────────────────────────────────────┘     │
│  Menu: File → Open Save Dir / Upload / Save / Save As             │
│  STS2: Steam User toolbar (QComboBox for switching accounts)      │
│  Status bar: file path, operation feedback                        │
└──────────────────────┬───────────────────────────────────────────┘
                       │ all panels read/write
                       ▼
        ┌──────────────────────────────┐
        │  SaveModel (STS1)            │
        │         or                   │  QObject, emits data_changed signal
        │  SaveModelSTS2 (STS2)        │  Same public API, different internals
        │                              │
        │  Typed properties: gold,     │──→ Dirty tracking (unsaved changes)
        │  HP, cards, potions, relics  │──→ Character detection
        └──────────────┬───────────────┘
                       │ load / save
                       ▼
                ┌───────────────┐
                │   save_io.py  │  Accepts GameConfig
                │               │
                │  STS1 path:   │──→ decode_save() / encode_save() via sts_save_editor.py
                │  STS2 path:   │──→ json.load() / json.dumps() (plain JSON)
                └───────────────┘

    ┌───────────────────┐     ┌──────────────────┐
    │  steam.py          │     │  settings.py      │
    │                    │     │                    │
    │  detect_steam_     │     │  ~/.config/sts-    │
    │  users()           │     │  save-editor/      │
    │  sts2_save_dir()   │     │  settings.json     │
    └───────────────────┘     └──────────────────┘

    ┌──────────────────────────────────────────────┐
    │  GameData (resources_dir)                     │
    │                                               │
    │  STS1: game_resources/                        │  STS2: game_resources_sts2/
    │  356 cards, 186 relics, 43 potions            │  576 cards, 288 relics, 63 potions
    │  wiki_data.json + images/                     │  wiki_data.json + images/
    └──────────────────────────────────────────────┘
```

## Module Guide

### `gui/game_config.py` — Version configuration
Frozen dataclass `GameConfig` with fields: `game_version`, `app_title`, `save_dir`, `file_glob`, `file_filter`, `game_resources_dir`, `encrypted`, `has_card_upgrades`. Factory functions `sts1_config()` and `sts2_config(steam_user_id)` produce the correct configuration for each game. This is the central mechanism for dual-game support — injected into MainWindow, save_io, and panels.

### `sts_save_editor.py` — CLI tool (STS1 only)
Provides `decode_save()` / `encode_save()` functions for XOR + Base64 encoding. Also works standalone as a CLI: `python sts_save_editor.py decode|encode|edit <file>`. STS2 saves bypass this module entirely since they are plain JSON.

### `gui/save_io.py` — File I/O
Accepts a `GameConfig` to handle both game versions. When `config.encrypted` is `True` (STS1), calls `decode_save()`/`encode_save()`. When `False` (STS2), reads/writes plain JSON directly. `find_save_files()` uses `config.save_dir` and `config.file_glob` to locate save files for either game.

### `gui/game_data.py` — Game reference data
Loads the three CSV files into dataclasses (`CardInfo`, `PotionInfo`, `RelicInfo`) and provides lookup dicts and filter methods. Accepts a configurable `resources_dir` (via `GameConfig.game_resources_dir`) to load from either `game_resources/` (STS1) or `game_resources_sts2/` (STS2) without any code changes.

Also loads `wiki_data.json` and merges wiki descriptions and image paths into each dataclass instance. Name matching is case-insensitive and tries both the display name and the raw CSV id. If wiki data or image files are missing, the app still works — fields default to empty strings.

Dual-index lookups (`cards_by_name` / `cards_by_id`, etc.) let panels find items whether the save file uses display names or internal game IDs.

### `gui/save_model.py` — STS1 data model
A `QObject` subclass that wraps the flat STS1 JSON dict. Key design decisions:

- **Typed properties** for fields the GUI edits (gold, HP, cards, potions, relics, etc.)
- **Raw dict passthrough** for the ~80 other fields the GUI doesn't touch — they're preserved exactly as-is when saving, preventing data loss
- **`data_changed` signal** — emitted whenever any property changes; all panels listen to this single signal to refresh their UI
- **Dirty tracking** — tracks whether any changes have been made since last save
- **Character detection** — identifies the character from the starter relic in the relics list
- Card upgrades use the `"upgrades"` key on each card entry

### `gui/save_model_sts2.py` — STS2 data model
Exposes the same public API as `SaveModel` so all panels work with either model without modification. Internally routes player data through a `_player` property that accesses `players[0]`. Maps STS2 field names to the shared property interface (e.g., `current_hp` → `current_health` property, `current_act_index` → `act_num`). Card upgrades use `"current_upgrade_level"` instead of `"upgrades"`. Character detection parses the `character_id` field (e.g., `"CHARACTER.SILENT"` → `"Silent"`).

### `gui/panels/` — Editor panels
Each panel is a self-contained `QWidget` that reads from and writes to the model:

| Panel | What it edits | Key widgets |
|-------|--------------|-------------|
| `stats_panel.py` | Gold, HP, act, floor, potion slots | `QSpinBox` with form layout |
| `cards_panel.py` | Deck contents and upgrades | Split view: deck table (left) + searchable browser (right). Upgrade Selected / Upgrade All buttons. Reads both `"upgrades"` (STS1) and `"current_upgrade_level"` (STS2). Filter label shows "Color" for STS1, "Character" for STS2. |
| `potions_panel.py` | Potion slots | One `QComboBox` per slot with potion icons and description tooltips |
| `relics_panel.py` | Equipped relics | Split view: relic list (left) + searchable browser (right) with icons, description + flavor tooltips |
| `raw_json_panel.py` | Raw save data | Text editor for direct JSON manipulation |

### `gui/main_window.py` — Main window
Accepts `GameConfig` and optional `steam_user_id`. Creates the appropriate model (`SaveModel` for STS1, `SaveModelSTS2` for STS2) and loads `GameData` from the version-specific resources directory. Assembles menu bar, tab widget with 5 panels, and status bar. In STS2 mode, builds a Steam User toolbar with a `QComboBox` listing detected Steam user IDs; switching users updates the config and persists the choice.

### `gui/app.py` + `gui/__main__.py` — Entry point
`__main__.py` parses `--game 1|2` via argparse and calls `main(game_version)`. `app.py` creates the `QApplication` and, for STS2 mode, runs `_resolve_steam_user()` which follows this priority:
1. Return saved user ID (from `settings.py`) if still valid
2. Auto-select if only one Steam user with STS2 saves is detected
3. Prompt via `QInputDialog` if multiple users are detected
4. Return `None` and fall back to manual file upload if no users found

Creates the appropriate `GameConfig` via factory function and passes it to `MainWindow`.

### `gui/steam.py` — Steam user detection and ID mapping
Scans `~/Library/Application Support/SlayTheSpire2/steam/` for long-Steam-ID directories with `profile1/saves/` subpaths. Converts between short IDs (account ID, e.g. `100200300`) and long IDs (Steam64, e.g. `76561198060466028`) via offset `76561197960265728`. Parses `loginusers.vdf` for persona names. Provides `update_remotecache_sha()` for syncing edited saves to the old Steam Cloud location.

### `gui/settings.py` — Persistent settings
JSON-backed settings stored at `~/.config/sts-save-editor/settings.json`. Currently persists the chosen Steam user ID via `get_steam_user_id()` / `set_steam_user_id()`. Used by `app.py` on startup and by `MainWindow` when the user switches accounts via the toolbar.

### `gui/widgets/` — Shared widgets
`DetailStrip` (inline preview) and `ImagePreviewDialog` (modal zoom) — used by cards, relics, and potions panels.

### `scripts/scrape_wiki.py` — STS1 wiki scraper (run once, offline)
Fetches the three wiki list pages from `slaythespire.wiki.gg` (Cards_List, Relics_List, Potions_List), parses HTML with BeautifulSoup, downloads images to `game_resources/images/`, and writes `game_resources/wiki_data.json`.

### `scripts/scrape_wiki_sts2.py` — STS2 wiki scraper (run once, offline)
Fetches STS2-specific wiki pages (`Slay_the_Spire_2:Cards_List`, `Slay_the_Spire_2:Relics`, `Slay_the_Spire_2:Potions`). Generates CSVs with IDs in `CARD.NAME` / `RELIC.NAME` / `POTION.NAME` format, downloads images, and writes output to `game_resources_sts2/`.

Both scrapers are run manually — output files are committed to the repo so the GUI needs no network access.

## Data Flow: Editing a Value

Example: user changes gold from 99 to 3000.

```
1. User changes QSpinBox value in StatsPanel
2. StatsPanel._on_gold_changed() fires
3. Sets model.gold = 3000
4. SaveModel._set_int() updates the raw dict, sets dirty=True, emits data_changed
5. All panels receive data_changed signal and refresh
6. MainWindow._update_title() adds "*" to title bar
```

The flow is identical for STS2 since `SaveModelSTS2` exposes the same property API. Internally, the write targets `players[0]` instead of the root dict.

## Data Flow: Save to File

```
1. User clicks File → Save (Ctrl+S)
2. MainWindow._save() called
3. write_save() writes the save file:
   - STS1: encode_save(model.raw) → XOR + Base64 → writes to file
   - STS2: json.dumps(model.raw, indent=2) → writes plain JSON
4. model.mark_clean() resets dirty flag, emits data_changed
5. Title bar "*" disappears
```

## Key Design Decisions

**Why wrap the raw dict instead of fully typed dataclass?**
The save JSON has ~80 fields. Typing them all would be premature and fragile. By wrapping the raw dict, only the fields the GUI edits get typed properties. Everything else passes through untouched — so fields like `monster_list`, `seed`, `event_list` survive a round-trip even though the editor never displays them.

**Why a `GameConfig` frozen dataclass instead of if/else everywhere?**
All game-version differences (save directory, file glob, encryption, resource directory, upgrade support) are captured in a single config object created at startup. Modules receive the config as a parameter and branch on its fields. This avoids scattering `if game_version == 2` conditionals through the codebase and makes it straightforward to add support for additional configurations.

**Why two separate model classes (SaveModel + SaveModelSTS2) instead of one?**
STS1 and STS2 have fundamentally different save structures (flat dict vs. nested `players[0]`). A single class with conditional logic would be complex and error-prone. Instead, both classes expose identical property APIs, so panels work with either model without knowing which game is loaded. The factory selection happens once in MainWindow based on `config.game_version`.

**Why a single `data_changed` signal?**
Simplicity. All panels refresh from the same signal. If a future panel needs to react only to specific changes, the model can be extended with fine-grained signals without breaking existing panels.

**Why `_updating` guard in panels?**
Prevents signal loops. When the model emits `data_changed`, panels refresh their widgets, which would normally trigger the widget's own change signal (e.g., `valueChanged` on a `QSpinBox`), which would write back to the model. The `_updating` flag breaks this cycle.

**Why auto-detect Steam users?**
STS2 saves are stored under a Steam-user-specific directory (`userdata/<id>/2868840/...`). Unlike STS1 which has a fixed path, STS2 requires knowing the user ID. `steam.py` scans `userdata/` for accounts that have STS2 saves. If exactly one is found, it is used automatically. If multiple exist, the user is prompted. The chosen ID is persisted via `settings.py` so subsequent launches skip the prompt.

**Why scrape wiki data offline instead of fetching at runtime?**
The wiki has 1500+ images across 6 pages (3 per game). Downloading at startup would add seconds of latency and require network access. Instead, the scraper scripts run once and commit the results. The GUI loads pre-downloaded images from disk — instant and works offline. If wiki data is missing, the app still functions (just without icons/descriptions).

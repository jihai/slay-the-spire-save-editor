# Slay the Spire Save Editor — Architecture

## Overview

A macOS GUI application (PySide6/Qt) for editing Slay the Spire save files. Built on top of an existing CLI tool that handles save file encoding/decoding.

## How Save Files Work

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

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     MainWindow                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │  QTabWidget                                     │    │
│  │  ┌───────┬───────┬──────────┬────────┐          │    │
│  │  │ Stats │ Cards │ Potions  │ Relics │  (tabs)  │    │
│  │  └───────┴───────┴──────────┴────────┘          │    │
│  └─────────────────────────────────────────────────┘    │
│  Menu: File → Open Save Dir / Upload / Save / Save As   │
│  Status bar: file path, operation feedback               │
└──────────────────────┬──────────────────────────────────┘
                       │ all panels read/write
                       ▼
               ┌───────────────┐
               │   SaveModel   │  (QObject, emits data_changed signal)
               │               │
               │  wraps raw    │──→ Typed properties: gold, HP, cards, potions, relics
               │  JSON dict    │──→ Dirty tracking (unsaved changes)
               │               │──→ Character detection from starter relic
               └───────┬───────┘
                       │ load / save
                       ▼
               ┌───────────────┐
               │   save_io.py  │  File I/O layer
               │               │
               │  find_save_   │──→ Scans Steam save dir for .autosave files
               │  files()      │
               │  load_save()  │──→ Reads file, calls decode_save()
               │  write_save() │──→ Calls encode_save(), writes file
               │  create_      │──→ Timestamped .bak copy before overwriting
               │  backup()     │
               └───────┬───────┘
                       │ uses
                       ▼
            ┌──────────────────────┐
            │  sts_save_editor.py  │  Existing CLI tool (unchanged)
            │                      │
            │  decode_save(raw)    │  Base64 → XOR → JSON
            │  encode_save(obj)    │  JSON → XOR → Base64
            └──────────────────────┘

               ┌───────────────┐
               │  GameData     │  Static reference data (loaded once at startup)
               │               │
               │  cards.csv    │──→ 356 cards: name, color, type, rarity
               │  potions.csv  │──→ 43 potions: name
               │  relics.csv   │──→ 186 relics: name, tier
               │               │
               │  wiki_data.   │──→ Descriptions, flavor text, image paths
               │  json         │    (merged into dataclasses at load time)
               │               │
               │  images/      │──→ 605 downloaded wiki images
               │  ├─ cards/    │    (370 card thumbnails)
               │  ├─ relics/   │    (193 relic icons)
               │  └─ potions/  │    (42 potion icons)
               └───────────────┘
```

## Module Guide

### `sts_save_editor.py` — CLI tool (pre-existing, unchanged)
The foundation. Provides `decode_save()` / `encode_save()` functions that the GUI imports directly. Also works standalone as a CLI: `python sts_save_editor.py decode|encode|edit <file>`.

### `gui/save_io.py` — File I/O
Thin layer over the CLI tool. Handles file discovery (scanning the Steam directory), reading/writing save files, and creating timestamped backups. The GUI never calls `decode_save`/`encode_save` directly — it goes through this module.

### `gui/game_data.py` — Game reference data
Loads the three CSV files into dataclasses (`CardInfo`, `PotionInfo`, `RelicInfo`) and provides lookup dicts and filter methods. Column names are defined as constants at the top of the file (e.g., `CARD_NAME_COL = "name"`) so they can be easily changed if the CSV schema changes.

Also loads `game_resources/wiki_data.json` and merges wiki descriptions and image paths into each dataclass instance. Name matching is case-insensitive and tries both the display name and the raw CSV id (e.g., wiki "Apparition" matches CSV `id=Apparition` even though `name=Ghostly`). If wiki data or image files are missing, the app still works — fields default to empty strings.

Dual-index lookups (`cards_by_name` / `cards_by_id`, etc.) let panels find items whether the save file uses display names or internal game IDs.

### `gui/save_model.py` — Save data model
The central piece. A `QObject` subclass that wraps the raw JSON dict from a save file. Key design decisions:

- **Typed properties** for fields the GUI edits (gold, HP, cards, potions, relics, etc.)
- **Raw dict passthrough** for the ~80 other fields the GUI doesn't touch — they're preserved exactly as-is when saving, preventing data loss
- **`data_changed` signal** — emitted whenever any property changes; all panels listen to this single signal to refresh their UI
- **Dirty tracking** — tracks whether any changes have been made since last save
- **Character detection** — identifies the character from the starter relic in the relics list

### `gui/panels/` — Editor panels
Each panel is a self-contained `QWidget` that reads from and writes to the `SaveModel`:

| Panel | What it edits | Key widgets |
|-------|--------------|-------------|
| `stats_panel.py` | Gold, HP, act, floor, potion slots | `QSpinBox` with form layout |
| `cards_panel.py` | Deck contents | Split view: deck table with icons (left) + searchable card browser with thumbnails and description tooltips (right) |
| `potions_panel.py` | Potion slots | One `QComboBox` per slot with potion icons and description tooltips |
| `relics_panel.py` | Equipped relics | Split view: relic list with icons (left) + searchable relic browser with icons, description + flavor tooltips (right) |

### `gui/main_window.py` — Main window
Assembles everything: menu bar, tab widget with the 4 panels, status bar. Handles file open/save dialogs, backup creation, and the unsaved-changes confirmation on close.

### `gui/app.py` + `gui/__main__.py` — Entry point
`QApplication` setup. Run with `python -m gui`.

### `scripts/scrape_wiki.py` — Wiki scraper (run once, offline)
Fetches the three wiki list pages from `slaythespire.wiki.gg` (Cards_List, Relics_List, Potions_List), parses HTML with BeautifulSoup to extract names, descriptions, and image URLs, downloads images to `game_resources/images/`, and writes `game_resources/wiki_data.json`. Run manually with `python scripts/scrape_wiki.py` — output files are committed to the repo so the GUI needs no network access.

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

## Data Flow: Save to File

```
1. User clicks File → Save (Ctrl+S)
2. MainWindow._save() called
3. create_backup() copies original file to .bak.{timestamp}
4. write_save() calls encode_save(model.raw) → writes to file
5. model.mark_clean() resets dirty flag, emits data_changed
6. Title bar "*" disappears
```

## Key Design Decisions

**Why wrap the raw dict instead of fully typed dataclass?**
The save JSON has ~80 fields. Typing them all would be premature and fragile. By wrapping the raw dict, only the fields the GUI edits get typed properties. Everything else passes through untouched — so fields like `monster_list`, `seed`, `event_list` survive a round-trip even though the editor never displays them.

**Why a single `data_changed` signal?**
Simplicity. All panels refresh from the same signal. If a future panel needs to react only to specific changes, the model can be extended with fine-grained signals without breaking existing panels.

**Why backup before every save?**
Save files are active game state — a corrupted file means a lost run. Backups are cheap (~7-10 KB) and provide an easy undo. Backups are timestamped so multiple saves don't overwrite each other.

**Why `_updating` guard in panels?**
Prevents signal loops. When the model emits `data_changed`, panels refresh their widgets, which would normally trigger the widget's own change signal (e.g., `valueChanged` on a `QSpinBox`), which would write back to the model. The `_updating` flag breaks this cycle.

**Why scrape wiki data offline instead of fetching at runtime?**
The wiki has 605 images across 3 pages. Downloading at startup would add seconds of latency and require network access. Instead, `scripts/scrape_wiki.py` runs once and commits the results. The GUI loads pre-downloaded images from disk — instant and works offline. If wiki data is missing, the app still functions (just without icons/descriptions).

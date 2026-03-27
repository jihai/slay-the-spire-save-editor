# Slay the Spire Save Editor

A desktop GUI application for editing [Slay the Spire](https://store.steampowered.com/app/646570/Slay_the_Spire/) (`.autosave`) and [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) (`.save`) files. Built with Python and PySide6 (Qt).

## Features

- **Stats** -- Edit gold, HP, ascension level, act, floor, and potion slots
- **Cards** -- Browse all cards with images, add/remove/upgrade cards in your deck
- **Potions** -- Swap potions in each slot from a dropdown with icons and descriptions
- **Relics** -- Add or remove relics with image previews and wiki descriptions
- **Raw JSON** -- View and manually edit the underlying save data for advanced users
- **Slay the Spire 2** -- Edit STS2 `.save` files with Steam user auto-detection
- STS1 characters: Ironclad, Silent, Defect, Watcher
- STS2 characters: Ironclad, Silent, Defect, Necrobinder, Regent

## Installation

### Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Setup

```bash
# Clone the repository
git clone https://github.com/your-username/slay-the-spire-save-editor.git
cd slay-the-spire-save-editor

# Create and activate a virtual environment with uv
uv venv .venv
source .venv/bin/activate      # macOS / Linux
# .venv\Scripts\activate       # Windows (PowerShell)

# Install dependencies
uv pip install -r requirements.txt
```

### Run

```bash
source .venv/bin/activate
python -m gui                # Slay the Spire 1 (default)
python -m gui --game 2       # Slay the Spire 2
```

For STS2, the editor auto-detects your Steam user ID. If multiple Steam accounts are found, you will be prompted to select one. Your choice is saved for future launches.

## OS Compatibility

| OS | Status | Notes |
|----|--------|-------|
| macOS | Fully supported | Auto-detects save directories for both STS1 and STS2 |
| Linux | Supported | Point to your Steam save directory manually via File > Upload Save File |
| Windows | Supported | Point to your Steam save directory manually via File > Upload Save File |

The GUI is built on PySide6 (Qt 6), which runs on all three major platforms. Save file encoding is platform-independent.

## Save File Location

### STS1

Slay the Spire stores saves as `.autosave` files (one per character):

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Steam/steamapps/common/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves/` |
| Windows | `C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\saves\` |
| Linux | `~/.local/share/Steam/steamapps/common/SlayTheSpire/saves/` |

### STS2

Slay the Spire 2 stores saves as plain JSON `.save` files. The primary save directory uses your long Steam ID:

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/SlayTheSpire2/steam/<long_steam_id>/profile1/saves/` |

> **Important:** Disable Steam Cloud sync for STS2 before editing saves, otherwise Steam Cloud will overwrite your changes. In Steam: right-click STS2 → Properties → General → uncheck "Keep game saves in the Steam Cloud".

The editor auto-detects your Steam user ID on macOS. On other platforms, use File > Upload Save File to open saves manually.

## Dependencies

| Package | Purpose |
|---------|---------|
| [PySide6](https://doc.qt.io/qtforpython-6/) | Qt 6 GUI framework |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing (wiki scraper only) |
| [requests](https://requests.readthedocs.io/) | HTTP client (wiki scraper only) |

## Credits

Card, relic, and potion descriptions, flavor text, and images for both games are sourced from the community-maintained [Slay the Spire Wiki](https://slaythespire.wiki.gg). This project is not affiliated with the wiki or its contributors -- thank you to the wiki community for maintaining such a comprehensive resource.

[Slay the Spire](https://store.steampowered.com/app/646570/Slay_the_Spire/) and [Slay the Spire 2](https://store.steampowered.com/app/2868840/Slay_the_Spire_2/) are developed by [Mega Crit Games](https://www.megacrit.com/). This project is an unofficial fan tool and is not affiliated with or endorsed by Mega Crit Games.

## License

This project is provided as-is for personal use. Slay the Spire and all related game assets are property of Mega Crit Games.

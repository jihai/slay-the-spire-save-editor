# Slay the Spire Save Editor

A desktop GUI application for editing [Slay the Spire](https://store.steampowered.com/app/646570/Slay_the_Spire/) `.autosave` files. Built with Python and PySide6 (Qt).

## Features

- **Stats** -- Edit gold, HP, ascension level, act, floor, and potion slots
- **Cards** -- Browse all cards with images, add/remove/upgrade cards in your deck
- **Potions** -- Swap potions in each slot from a dropdown with icons and descriptions
- **Relics** -- Add or remove relics with image previews and wiki descriptions
- **Raw JSON** -- View and manually edit the underlying save data for advanced users
- Automatic timestamped backups on every save
- Supports all four characters: Ironclad, Silent, Defect, Watcher

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
python -m gui
```

## OS Compatibility

| OS | Status | Notes |
|----|--------|-------|
| macOS | Fully supported | Auto-detects save directory under `~/Library/Application Support/Steam/...` |
| Linux | Supported | Point to your Steam save directory manually via File > Upload Save File |
| Windows | Supported | Point to your Steam save directory manually via File > Upload Save File |

The GUI is built on PySide6 (Qt 6), which runs on all three major platforms. Save file encoding is platform-independent.

## Save File Location

Slay the Spire stores saves as `.autosave` files (one per character):

| OS | Path |
|----|------|
| macOS | `~/Library/Application Support/Steam/steamapps/common/SlayTheSpire/SlayTheSpire.app/Contents/Resources/saves/` |
| Windows | `C:\Program Files (x86)\Steam\steamapps\common\SlayTheSpire\saves\` |
| Linux | `~/.local/share/Steam/steamapps/common/SlayTheSpire/saves/` |

## Dependencies

| Package | Purpose |
|---------|---------|
| [PySide6](https://doc.qt.io/qtforpython-6/) | Qt 6 GUI framework |
| [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/) | HTML parsing (wiki scraper only) |
| [requests](https://requests.readthedocs.io/) | HTTP client (wiki scraper only) |

## Credits

Card, relic, and potion descriptions, flavor text, and images are sourced from the community-maintained [Slay the Spire Wiki](https://slaythespire.wiki.gg). This project is not affiliated with the wiki or its contributors -- thank you to the wiki community for maintaining such a comprehensive resource.

[Slay the Spire](https://store.steampowered.com/app/646570/Slay_the_Spire/) is developed by [Mega Crit Games](https://www.megacrit.com/). This project is an unofficial fan tool and is not affiliated with or endorsed by Mega Crit Games.

## License

This project is provided as-is for personal use. Slay the Spire and all related game assets are property of Mega Crit Games.

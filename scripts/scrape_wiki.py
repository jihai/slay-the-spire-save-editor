#!/usr/bin/env python3
"""Scrape card, relic, and potion data (descriptions + images) from the StS wiki.

Usage:
    python scripts/scrape_wiki.py

Outputs:
    game_resources/wiki_data.json   — descriptions and image paths
    game_resources/images/cards/    — card art thumbnails
    game_resources/images/relics/   — relic icons
    game_resources/images/potions/  — potion icons
"""

import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://slaythespire.wiki.gg"
CARDS_URL = f"{BASE_URL}/wiki/Cards_List"
RELICS_URL = f"{BASE_URL}/wiki/Relics_List"
POTIONS_URL = f"{BASE_URL}/wiki/Potions_List"

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "game_resources"
IMAGES_DIR = OUTPUT_DIR / "images"
WIKI_DATA_PATH = OUTPUT_DIR / "wiki_data.json"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "StS-Save-Editor/1.0 (educational project)"})


def fetch_page(url: str) -> BeautifulSoup:
    print(f"  Fetching {url} ...")
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def download_image(src: str, dest: Path) -> bool:
    """Download an image from the wiki. Returns True if successful."""
    if dest.exists():
        return True
    url = urljoin(BASE_URL, src)
    try:
        r = SESSION.get(url, timeout=15)
        r.raise_for_status()
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(r.content)
        return True
    except Exception as e:
        print(f"    Warning: failed to download {url}: {e}")
        return False


def clean_description(element) -> str:
    """Extract clean text from a description element, removing inline icons."""
    if element is None:
        return ""
    # Get text, collapsing whitespace
    text = element.get_text(separator=" ", strip=True)
    # Clean up multiple spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def scrape_cards(soup: BeautifulSoup) -> dict:
    """Parse card-box elements from Cards_List page."""
    cards = {}
    card_dir = IMAGES_DIR / "cards"
    card_dir.mkdir(parents=True, exist_ok=True)

    for box in soup.find_all("div", class_="card-box"):
        # Title
        title_el = box.select_one(".card-title a")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)

        # Description (base version only)
        desc_el = box.select_one(".desc-base")
        description = clean_description(desc_el)

        # Image (base version)
        img_el = box.select_one(".img-base img")
        image_path = ""
        if img_el:
            src = img_el.get("src", "")
            filename = img_el.get("alt", "").replace(" ", "_")
            if src and filename:
                dest = card_dir / filename
                if download_image(src, dest):
                    image_path = f"cards/{filename}"

        cards[name] = {"description": description, "image": image_path}

    return cards


# ---------------------------------------------------------------------------
# Relics
# ---------------------------------------------------------------------------

def scrape_relics(soup: BeautifulSoup) -> dict:
    """Parse relic-box elements from Relics_List page."""
    relics = {}
    relic_dir = IMAGES_DIR / "relics"
    relic_dir.mkdir(parents=True, exist_ok=True)

    for box in soup.find_all("div", class_="relic-box"):
        # Title
        title_el = box.select_one(".relic-title a")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)

        # Description
        desc_el = box.select_one(".relic-desc .relic-desc")
        if not desc_el:
            desc_el = box.select_one(".relic-desc")
        description = clean_description(desc_el)

        # Flavor text
        flavor_el = box.select_one(".relic-flavor")
        flavor = clean_description(flavor_el)

        # Remove flavor from description if it got merged
        if flavor and description.endswith(flavor):
            description = description[: -len(flavor)].strip()

        # Image
        img_el = box.select_one(".img-base img")
        image_path = ""
        if img_el:
            src = img_el.get("src", "")
            filename = img_el.get("alt", "").replace(" ", "_")
            if src and filename:
                dest = relic_dir / filename
                if download_image(src, dest):
                    image_path = f"relics/{filename}"

        relics[name] = {"description": description, "flavor": flavor, "image": image_path}

    return relics


# ---------------------------------------------------------------------------
# Potions
# ---------------------------------------------------------------------------

def scrape_potions(soup: BeautifulSoup) -> dict:
    """Parse potion-box elements from Potions_List page."""
    potions = {}
    potion_dir = IMAGES_DIR / "potions"
    potion_dir.mkdir(parents=True, exist_ok=True)

    for box in soup.find_all("div", class_="potion-box"):
        # Title
        title_el = box.select_one(".potion-title")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)

        # Description — nested .potion-desc inside .potion-desc
        desc_el = box.select_one(".potion-desc .potion-desc")
        if not desc_el:
            desc_el = box.select_one(".potion-desc")
        description = clean_description(desc_el)

        # Image
        img_el = box.select_one(".img-base img")
        image_path = ""
        if img_el:
            src = img_el.get("src", "")
            filename = img_el.get("alt", "").replace(" ", "_")
            if src and filename:
                dest = potion_dir / filename
                if download_image(src, dest):
                    image_path = f"potions/{filename}"

        potions[name] = {"description": description, "image": image_path}

    return potions


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print("Scraping Slay the Spire wiki...\n")

    print("[1/3] Cards")
    cards_soup = fetch_page(CARDS_URL)
    cards = scrape_cards(cards_soup)
    print(f"  Found {len(cards)} cards\n")

    print("[2/3] Relics")
    relics_soup = fetch_page(RELICS_URL)
    relics = scrape_relics(relics_soup)
    print(f"  Found {len(relics)} relics\n")

    print("[3/3] Potions")
    potions_soup = fetch_page(POTIONS_URL)
    potions = scrape_potions(potions_soup)
    print(f"  Found {len(potions)} potions\n")

    # Write wiki_data.json
    wiki_data = {"cards": cards, "relics": relics, "potions": potions}
    WIKI_DATA_PATH.write_text(json.dumps(wiki_data, indent=2, ensure_ascii=False))
    print(f"Wrote {WIKI_DATA_PATH}")
    print(f"Images saved to {IMAGES_DIR}/")
    print(f"\nTotal: {len(cards)} cards, {len(relics)} relics, {len(potions)} potions")


if __name__ == "__main__":
    main()

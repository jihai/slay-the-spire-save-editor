#!/usr/bin/env python3
"""Scrape STS2 card, relic, and potion data from the wiki.

Generates CSVs, wiki_data.json, and downloads images to game_resources_sts2/.

Usage:
    python scripts/scrape_wiki_sts2.py
"""

import csv
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://slaythespire.wiki.gg"
CARDS_URL = f"{BASE_URL}/wiki/Slay_the_Spire_2:Cards_List"
RELICS_URL = f"{BASE_URL}/wiki/Slay_the_Spire_2:Relics"
POTIONS_URL = f"{BASE_URL}/wiki/Slay_the_Spire_2:Potions"

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "game_resources_sts2"
IMAGES_DIR = OUTPUT_DIR / "images"

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "StS-Save-Editor/1.0 (educational project)"})


def fetch_page(url: str) -> BeautifulSoup:
    print(f"  Fetching {url} ...")
    r = SESSION.get(url, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def download_image(src: str, dest: Path) -> bool:
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
    if element is None:
        return ""
    text = element.get_text(separator=" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def name_to_id(name: str, prefix: str) -> str:
    """Convert display name to save-file ID.

    e.g., "Strike (Silent)" -> "CARD.STRIKE_SILENT"
         "Ring of the Snake" -> "RELIC.RING_OF_THE_SNAKE"
    """
    # Remove parentheses, replace spaces/hyphens with underscores
    clean = re.sub(r"[()']", "", name)
    clean = re.sub(r"[\s\-]+", "_", clean)
    clean = clean.upper().strip("_")
    return f"{prefix}.{clean}"


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def scrape_cards(soup: BeautifulSoup) -> tuple[list[dict], dict]:
    """Return (csv_rows, wiki_data) for cards."""
    rows = []
    wiki = {}
    card_dir = IMAGES_DIR / "cards"
    card_dir.mkdir(parents=True, exist_ok=True)

    for box in soup.find_all("div", class_="card-box"):
        title_el = box.select_one(".card-title a")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)
        color = box.get("data-color", "")
        rarity = box.get("data-rarity", "")
        card_type = box.get("data-type", "")

        # Description (base version only)
        desc_el = box.select_one(".desc-base")
        description = clean_description(desc_el)

        # Generate save-file ID
        card_id = name_to_id(name, "CARD")

        # Image
        img_el = box.select_one(".img-base img")
        image_path = ""
        if img_el:
            src = img_el.get("src", "")
            alt = img_el.get("alt", "")
            filename = alt.replace(" ", "_") if alt else ""
            if src and filename:
                if not filename.lower().endswith((".png", ".jpg", ".gif")):
                    filename += ".png"
                dest = card_dir / filename
                if download_image(src, dest):
                    image_path = f"cards/{filename}"

        rows.append({
            "id": card_id,
            "name": name,
            "color": color,
            "type": card_type,
            "rarity": rarity,
        })
        wiki[name] = {"description": description, "image": image_path}

    return rows, wiki


# ---------------------------------------------------------------------------
# Relics
# ---------------------------------------------------------------------------

def scrape_relics(soup: BeautifulSoup) -> tuple[list[dict], dict]:
    rows = []
    wiki = {}
    relic_dir = IMAGES_DIR / "relics"
    relic_dir.mkdir(parents=True, exist_ok=True)

    for box in soup.find_all("div", class_="relic-box"):
        title_el = box.select_one(".relic-title a")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)
        tier = box.get("data-rarity", "")

        # Description
        desc_el = box.select_one(".relic-desc .relic-desc")
        if not desc_el:
            desc_el = box.select_one(".relic-desc")
        description = clean_description(desc_el)

        # Flavor text
        flavor_el = box.select_one(".relic-flavor")
        flavor = clean_description(flavor_el)

        # Remove flavor from description if merged
        if flavor and description.endswith(flavor):
            description = description[: -len(flavor)].strip()

        # Generate save-file ID
        relic_id = name_to_id(name, "RELIC")

        # Image
        img_el = box.select_one(".img-base img")
        image_path = ""
        if img_el:
            src = img_el.get("src", "")
            alt = img_el.get("alt", "")
            filename = alt.replace(" ", "_") if alt else ""
            if src and filename:
                if not filename.lower().endswith((".png", ".jpg", ".gif")):
                    filename += ".png"
                dest = relic_dir / filename
                if download_image(src, dest):
                    image_path = f"relics/{filename}"

        rows.append({
            "id": relic_id,
            "name": name,
            "tier": tier,
        })
        wiki[name] = {
            "description": description,
            "flavor": flavor,
            "image": image_path,
        }

    return rows, wiki


# ---------------------------------------------------------------------------
# Potions
# ---------------------------------------------------------------------------

def scrape_potions(soup: BeautifulSoup) -> tuple[list[dict], dict]:
    rows = []
    wiki = {}
    potion_dir = IMAGES_DIR / "potions"
    potion_dir.mkdir(parents=True, exist_ok=True)

    for box in soup.find_all("div", class_="potion-box"):
        title_el = box.select_one(".potion-title")
        if not title_el:
            continue
        name = title_el.get_text(strip=True)

        # Description
        desc_el = box.select_one(".potion-desc .potion-desc")
        if not desc_el:
            desc_el = box.select_one(".potion-desc")
        description = clean_description(desc_el)

        # Generate save-file ID
        potion_id = name_to_id(name, "POTION")

        # Image
        img_el = box.select_one(".img-base img")
        image_path = ""
        if img_el:
            src = img_el.get("src", "")
            alt = img_el.get("alt", "")
            filename = alt.replace(" ", "_") if alt else ""
            if src and filename:
                if not filename.lower().endswith((".png", ".jpg", ".gif")):
                    filename += ".png"
                dest = potion_dir / filename
                if download_image(src, dest):
                    image_path = f"potions/{filename}"

        rows.append({
            "id": potion_id,
            "name": name,
        })
        wiki[name] = {"description": description, "image": image_path}

    return rows, wiki


# ---------------------------------------------------------------------------
# CSV / JSON output
# ---------------------------------------------------------------------------

def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Scraping Slay the Spire 2 wiki...\n")

    print("[1/3] Cards")
    cards_soup = fetch_page(CARDS_URL)
    card_rows, card_wiki = scrape_cards(cards_soup)
    print(f"  Found {len(card_rows)} cards\n")

    print("[2/3] Relics")
    relics_soup = fetch_page(RELICS_URL)
    relic_rows, relic_wiki = scrape_relics(relics_soup)
    print(f"  Found {len(relic_rows)} relics\n")

    print("[3/3] Potions")
    potions_soup = fetch_page(POTIONS_URL)
    potion_rows, potion_wiki = scrape_potions(potions_soup)
    print(f"  Found {len(potion_rows)} potions\n")

    # Write CSVs
    write_csv(
        OUTPUT_DIR / "cards.csv",
        card_rows,
        ["id", "name", "color", "type", "rarity"],
    )
    write_csv(
        OUTPUT_DIR / "relics.csv",
        relic_rows,
        ["id", "name", "tier"],
    )
    write_csv(
        OUTPUT_DIR / "potions.csv",
        potion_rows,
        ["id", "name"],
    )

    # Write wiki_data.json
    wiki_data = {"cards": card_wiki, "relics": relic_wiki, "potions": potion_wiki}
    wiki_path = OUTPUT_DIR / "wiki_data.json"
    wiki_path.write_text(json.dumps(wiki_data, indent=2, ensure_ascii=False))

    print(f"Wrote CSVs to {OUTPUT_DIR}/")
    print(f"Wrote {wiki_path}")
    print(f"Images saved to {IMAGES_DIR}/")
    print(f"\nTotal: {len(card_rows)} cards, {len(relic_rows)} relics, {len(potion_rows)} potions")


if __name__ == "__main__":
    main()

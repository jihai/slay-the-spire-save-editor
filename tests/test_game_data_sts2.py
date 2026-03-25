"""Tests for loading STS2 game resources via GameData."""

from pathlib import Path

from gui.game_data import GameData

STS2_RESOURCES = Path(__file__).parent.parent / "game_resources_sts2"


class TestSTS2GameDataLoading:
    def test_loads_cards(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        assert len(gd.cards) > 100

    def test_loads_relics(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        assert len(gd.relics) > 50

    def test_loads_potions(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        assert len(gd.potions) > 20

    def test_card_has_expected_fields(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        card = gd.cards[0]
        assert card.id
        assert card.name
        assert card.color  # character name in STS2
        assert card.card_type

    def test_card_lookup_by_id(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        card = gd.cards_by_id.get("CARD.BASH")
        assert card is not None
        assert card.name == "Bash"

    def test_card_lookup_by_name(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        card = gd.cards_by_name.get("Bash")
        assert card is not None
        assert card.id == "CARD.BASH"

    def test_relic_lookup_by_id(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        relic = gd.relics_by_id.get("RELIC.BURNING_BLOOD")
        assert relic is not None
        assert relic.name == "Burning Blood"

    def test_potion_lookup_by_id(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        potion = gd.potions_by_id.get("POTION.ATTACK_POTION")
        assert potion is not None
        assert potion.name == "Attack Potion"

    def test_filter_cards_by_color(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        ironclad = gd.filter_cards(color="Ironclad")
        assert len(ironclad) > 10
        assert all(c.color == "Ironclad" for c in ironclad)

    def test_card_colors_include_sts2_characters(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        colors = gd.card_colors()
        assert "Ironclad" in colors
        assert "Silent" in colors

    def test_wiki_data_has_descriptions(self):
        gd = GameData(resources_dir=STS2_RESOURCES)
        card = gd.cards_by_name.get("Bash")
        assert card is not None
        assert card.description  # should have description from wiki

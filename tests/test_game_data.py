"""Tests for gui.game_data module."""

from gui.game_data import GameData, load_cards, load_potions, load_relics


class TestLoadFunctions:
    def test_load_cards_returns_list(self):
        cards = load_cards()
        assert len(cards) > 300
        assert cards[0].name
        assert cards[0].color
        assert cards[0].card_type
        assert cards[0].rarity

    def test_load_potions_returns_list(self):
        potions = load_potions()
        assert len(potions) > 40
        assert potions[0].name

    def test_load_relics_returns_list(self):
        relics = load_relics()
        assert len(relics) > 180
        assert relics[0].name
        assert relics[0].tier


class TestGameData:
    def setup_method(self):
        self.gd = GameData()

    def test_lookup_card_by_name(self):
        card = self.gd.cards_by_name["Bash"]
        assert card.color == "Red"
        assert card.card_type == "Attack"

    def test_lookup_potion_by_name(self):
        potion = self.gd.potions_by_name["Attack Potion"]
        assert potion.name == "Attack Potion"

    def test_lookup_relic_by_name(self):
        relic = self.gd.relics_by_name["Burning Blood"]
        assert relic.tier == "Starter"

    def test_filter_cards_by_color(self):
        red = self.gd.filter_cards(color="Red")
        assert all(c.color == "Red" for c in red)
        assert len(red) > 0

    def test_filter_cards_by_type(self):
        attacks = self.gd.filter_cards(card_type="Attack")
        assert all(c.card_type == "Attack" for c in attacks)

    def test_filter_cards_combined(self):
        rare_blue = self.gd.filter_cards(color="Blue", rarity="Rare")
        assert all(c.color == "Blue" and c.rarity == "Rare" for c in rare_blue)

    def test_filter_relics_by_tier(self):
        boss = self.gd.filter_relics(tier="Boss")
        assert all(r.tier == "Boss" for r in boss)
        assert len(boss) > 0

    def test_card_colors(self):
        colors = self.gd.card_colors()
        assert "Red" in colors
        assert "Blue" in colors

    def test_relic_tiers(self):
        tiers = self.gd.relic_tiers()
        assert "Common" in tiers
        assert "Boss" in tiers

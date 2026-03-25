"""Tests for gui.save_model_sts2 — STS2 SaveModel with nested players[0] access."""

import copy
import json
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication

from gui.save_model_sts2 import SaveModelSTS2

TEMPLATE_PATH = Path(__file__).parent.parent / "raw_templates" / "sts2_silent_save.json"


@pytest.fixture(scope="session", autouse=True)
def qapp():
    """Ensure a QCoreApplication exists for signal tests."""
    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication([])
    return app


@pytest.fixture
def sample_data():
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


@pytest.fixture
def model(sample_data):
    m = SaveModelSTS2()
    m.load(sample_data, file_path="/tmp/test.save")
    return m


class TestBasics:
    def test_is_loaded(self, model):
        assert model.is_loaded is True

    def test_not_loaded_initially(self):
        m = SaveModelSTS2()
        assert m.is_loaded is False

    def test_file_path(self, model):
        assert model.file_path == "/tmp/test.save"

    def test_file_path_setter(self, model):
        model.file_path = "/tmp/other.save"
        assert model.file_path == "/tmp/other.save"

    def test_raw_returns_full_dict(self, model, sample_data):
        assert model.raw is not None
        assert "players" in model.raw
        assert "acts" in model.raw

    def test_character_detection(self, model):
        assert model.character == "Silent"

    def test_character_unknown(self):
        m = SaveModelSTS2()
        m.load({"players": [{"character_id": ""}]})
        assert m.character == "Unknown"


class TestScalarProperties:
    def test_gold(self, model):
        assert model.gold == 264

    def test_set_gold(self, model):
        model.gold = 500
        assert model.gold == 500
        assert model.raw["players"][0]["gold"] == 500

    def test_current_health(self, model):
        assert model.current_health == 28

    def test_set_current_health(self, model):
        model.current_health = 50
        assert model.current_health == 50
        assert model.raw["players"][0]["current_hp"] == 50

    def test_max_health(self, model):
        assert model.max_health == 70

    def test_set_max_health(self, model):
        model.max_health = 100
        assert model.max_health == 100
        assert model.raw["players"][0]["max_hp"] == 100

    def test_act_num(self, model):
        assert model.act_num == 0

    def test_set_act_num(self, model):
        model.act_num = 2
        assert model.act_num == 2
        assert model.raw["current_act_index"] == 2

    def test_ascension_level(self, model):
        assert model.ascension_level == 0

    def test_set_ascension_level(self, model):
        model.ascension_level = 10
        assert model.ascension_level == 10
        assert model.raw["ascension"] == 10

    def test_potion_slots(self, model):
        assert model.potion_slots == 3

    def test_set_potion_slots(self, model):
        model.potion_slots = 5
        assert model.potion_slots == 5
        assert model.raw["players"][0]["max_potion_slot_count"] == 5


class TestDirtyTracking:
    def test_not_dirty_after_load(self, model):
        assert model.dirty is False

    def test_dirty_after_gold_change(self, model):
        model.gold = 999
        assert model.dirty is True

    def test_mark_clean(self, model):
        model.gold = 999
        assert model.dirty is True
        model.mark_clean()
        assert model.dirty is False


class TestCardOperations:
    def test_cards_returns_deck(self, model):
        cards = model.cards
        assert len(cards) == 9
        assert cards[0]["id"] == "CARD.STRIKE_SILENT"

    def test_add_card(self, model):
        initial = len(model.cards)
        model.add_card("CARD.DASH")
        assert len(model.cards) == initial + 1
        added = model.cards[-1]
        assert added["id"] == "CARD.DASH"
        assert added["floor_added_to_deck"] == 0

    def test_remove_card(self, model):
        initial = len(model.cards)
        model.remove_card(0)
        assert len(model.cards) == initial - 1

    def test_remove_cards(self, model):
        initial = len(model.cards)
        model.remove_cards([0, 2])
        assert len(model.cards) == initial - 2

    def test_set_card_upgrades(self, model):
        """STS2 cards use current_upgrade_level for upgrades."""
        model.set_card_upgrades(0, 2)
        assert model.cards[0]["current_upgrade_level"] == 2
        assert model.dirty is True

    def test_set_card_upgrades_zero_removes_key(self, model):
        """Setting upgrades to 0 removes the current_upgrade_level key."""
        # Card at index 7 (CARD.DASH) has current_upgrade_level=1 in fixture
        model.set_card_upgrades(7, 0)
        assert "current_upgrade_level" not in model.cards[7]

    def test_add_card_with_upgrades(self, model):
        initial = len(model.cards)
        model.add_card("CARD.TEST", upgrades=1)
        added = model.cards[-1]
        assert added["current_upgrade_level"] == 1

    def test_existing_upgrade_level_preserved(self, model):
        """The fixture has CARD.DASH at index 7 with current_upgrade_level=1."""
        dash = model.cards[7]
        assert dash["id"] == "CARD.DASH"
        assert dash["current_upgrade_level"] == 1


class TestRelicOperations:
    def test_relics_returns_ids(self, model):
        relics = model.relics
        assert len(relics) == 3
        assert relics[0] == "RELIC.RING_OF_THE_SNAKE"

    def test_add_relic(self, model):
        model.add_relic("RELIC.NEW_RELIC")
        assert "RELIC.NEW_RELIC" in model.relics
        # Verify the underlying dict has the right shape
        raw_relics = model.raw["players"][0]["relics"]
        added = raw_relics[-1]
        assert added["id"] == "RELIC.NEW_RELIC"
        assert added["floor_added_to_deck"] == 0

    def test_remove_relic(self, model):
        initial = len(model.relics)
        model.remove_relic(0)
        assert len(model.relics) == initial - 1


class TestPotionOperations:
    def test_potions_returns_ids(self, model):
        potions = model.potions
        assert len(potions) == 2
        assert potions[0] == "POTION.CLARITY"
        assert potions[1] == "POTION.LUCKY_TONIC"

    def test_set_potion(self, model):
        model.set_potion(0, "POTION.FIRE_POTION")
        assert model.potions[0] == "POTION.FIRE_POTION"
        # Verify underlying dict preserves slot_index
        raw = model.raw["players"][0]["potions"][0]
        assert raw["id"] == "POTION.FIRE_POTION"
        assert raw["slot_index"] == 0


class TestSignals:
    def test_data_changed_on_load(self, sample_data):
        m = SaveModelSTS2()
        signals = []
        m.data_changed.connect(lambda: signals.append(True))
        m.load(sample_data)
        assert len(signals) == 1

    def test_data_changed_on_property_change(self, model):
        signals = []
        model.data_changed.connect(lambda: signals.append(True))
        model.gold = 999
        assert len(signals) >= 1

    def test_data_changed_on_add_card(self, model):
        signals = []
        model.data_changed.connect(lambda: signals.append(True))
        model.add_card("CARD.TEST")
        assert len(signals) >= 1

    def test_data_changed_on_mark_clean(self, model):
        signals = []
        model.data_changed.connect(lambda: signals.append(True))
        model.mark_clean()
        assert len(signals) >= 1


class TestRawPassthrough:
    def test_unedited_fields_preserved(self, model):
        """Fields not exposed as properties should survive edits."""
        model.gold = 1000
        assert model.raw["schema_version"] == 14
        assert model.raw["platform_type"] == "steam"
        assert model.raw["rng"]["seed"] == "TESTSEED"
        assert model.raw["players"][0]["net_id"] == "test_net_id"

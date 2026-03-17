"""Tests for gui.save_model module."""

import json
from pathlib import Path

from gui.save_model import SaveModel

TEMPLATE_PATH = Path(__file__).resolve().parent.parent / "raw_templates" / "ironclad_save.json"


def _make_model(data=None):
    model = SaveModel()
    if data is None:
        data = json.loads(TEMPLATE_PATH.read_text())
    model.load(data, file_path="/fake/path")
    return model


class TestSaveModelBasics:
    def test_load_sets_data(self):
        model = _make_model()
        assert model.is_loaded
        assert model.file_path == "/fake/path"
        assert not model.dirty

    def test_character_detection_ironclad(self):
        model = _make_model()
        assert model.character == "Ironclad"

    def test_character_detection_unknown(self):
        model = _make_model({"relics": ["SomeRandomRelic"]})
        assert model.character == "Unknown"


class TestScalarProperties:
    def test_gold_get_and_set(self):
        model = _make_model()
        original = model.gold
        model.gold = 9999
        assert model.gold == 9999
        assert model.dirty

    def test_health_get_and_set(self):
        model = _make_model()
        model.current_health = 50
        model.max_health = 100
        assert model.current_health == 50
        assert model.max_health == 100

    def test_act_and_floor(self):
        model = _make_model()
        model.act_num = 3
        model.floor_num = 42
        assert model.act_num == 3
        assert model.floor_num == 42

    def test_setting_same_value_does_not_dirty(self):
        model = _make_model()
        original_gold = model.gold
        model.gold = original_gold
        assert not model.dirty

    def test_mark_clean(self):
        model = _make_model()
        model.gold = 1
        assert model.dirty
        model.mark_clean()
        assert not model.dirty


class TestCardOperations:
    def test_add_card(self):
        model = _make_model()
        count = len(model.cards)
        model.add_card("Bash", upgrades=1)
        assert len(model.cards) == count + 1
        assert model.cards[-1] == {"id": "Bash", "upgrades": 1, "misc": 0}
        assert model.dirty

    def test_remove_card(self):
        model = _make_model()
        count = len(model.cards)
        model.remove_card(0)
        assert len(model.cards) == count - 1

    def test_set_card_upgrades(self):
        model = _make_model()
        model.set_card_upgrades(0, 5)
        assert model.cards[0]["upgrades"] == 5


class TestPotionOperations:
    def test_set_potion(self):
        model = _make_model()
        model.set_potion(0, "StrengthPotion")
        assert model.potions[0] == "StrengthPotion"
        assert model.dirty


class TestRelicOperations:
    def test_add_relic(self):
        model = _make_model()
        count = len(model.relics)
        model.add_relic("Vajra")
        assert len(model.relics) == count + 1
        assert model.relics[-1] == "Vajra"

    def test_remove_relic(self):
        model = _make_model()
        count = len(model.relics)
        model.remove_relic(0)
        assert len(model.relics) == count - 1


class TestSignals:
    def test_data_changed_emitted_on_load(self):
        model = SaveModel()
        signals = []
        model.data_changed.connect(lambda: signals.append(True))
        model.load({"gold": 100})
        assert len(signals) == 1

    def test_data_changed_emitted_on_property_change(self):
        model = _make_model()
        signals = []
        model.data_changed.connect(lambda: signals.append(True))
        model.gold = 5000
        assert len(signals) >= 1


class TestRawPassthrough:
    def test_unedited_fields_preserved(self):
        data = json.loads(TEMPLATE_PATH.read_text())
        model = _make_model(data)
        model.gold = 9999
        # All original keys should still be present
        assert "monster_list" in model.raw
        assert "seed" in model.raw
        assert "event_list" in model.raw
        assert model.raw["gold"] == 9999

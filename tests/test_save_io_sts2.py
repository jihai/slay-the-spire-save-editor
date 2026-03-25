"""Tests for gui.save_io with STS2 config (plain JSON, no encryption)."""

import json
from pathlib import Path

from gui.game_config import sts2_config
from gui.save_io import find_save_files, load_save, write_save

STS2_SAMPLE = {
    "ascension": 0,
    "current_act_index": 0,
    "players": [
        {
            "character_id": "CHARACTER.SILENT",
            "gold": 264,
            "current_hp": 28,
            "max_hp": 70,
            "deck": [{"id": "CARD.STRIKE_SILENT", "floor_added_to_deck": 1}],
            "relics": [{"id": "RELIC.RING_OF_THE_SNAKE", "floor_added_to_deck": 1}],
            "potions": [{"id": "POTION.CLARITY", "slot_index": 0}],
        }
    ],
}


class TestFindSaveFilesSTS2:
    def test_finds_save_files(self, tmp_path):
        cfg = sts2_config()
        (tmp_path / "current_run.save").write_text("{}")
        (tmp_path / "run2.save").write_text("{}")
        (tmp_path / "other.txt").write_text("nope")
        result = find_save_files(save_dir=tmp_path, config=cfg)
        assert len(result) == 2
        assert all(p.suffix == ".save" for p in result)

    def test_returns_empty_for_nonexistent(self):
        cfg = sts2_config()
        assert find_save_files(save_dir=Path("/nonexistent"), config=cfg) == []


class TestLoadAndWriteSaveSTS2:
    def test_round_trip_plain_json(self, tmp_path):
        cfg = sts2_config()
        save_path = tmp_path / "current_run.save"

        # Write plain JSON
        write_save(save_path, STS2_SAMPLE, config=cfg)

        # File should be valid JSON (not encrypted)
        raw = save_path.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert parsed["players"][0]["gold"] == 264

        # Load via save_io
        loaded = load_save(save_path, config=cfg)
        assert loaded["ascension"] == 0
        assert loaded["players"][0]["character_id"] == "CHARACTER.SILENT"
        assert loaded["players"][0]["current_hp"] == 28
        assert loaded["players"][0]["deck"][0]["id"] == "CARD.STRIKE_SILENT"

    def test_write_then_load_preserves_data(self, tmp_path):
        cfg = sts2_config()
        save_path = tmp_path / "test.save"
        write_save(save_path, STS2_SAMPLE, config=cfg)
        loaded = load_save(save_path, config=cfg)
        assert loaded == STS2_SAMPLE

    def test_plain_json_is_human_readable(self, tmp_path):
        """STS2 saves should be written as indented, human-readable JSON."""
        cfg = sts2_config()
        save_path = tmp_path / "test.save"
        write_save(save_path, STS2_SAMPLE, config=cfg)
        raw = save_path.read_text(encoding="utf-8")
        assert "\n" in raw  # indented output has newlines

"""Tests for gui.save_io module."""

import json
from pathlib import Path

from sts_save_editor import encode_save
from gui.save_io import create_backup, find_save_files, load_save, write_save

SAMPLE_DATA = {"gold": 99, "current_health": 72, "cards": [{"id": "Bash", "upgrades": 0, "misc": 0}]}


class TestFindSaveFiles:
    def test_returns_empty_for_nonexistent_dir(self):
        assert find_save_files(Path("/nonexistent/path")) == []

    def test_finds_autosave_files(self, tmp_path):
        (tmp_path / "IRONCLAD.autosave").write_text("data")
        (tmp_path / "SILENT.autosave").write_text("data")
        (tmp_path / "other.txt").write_text("not a save")
        result = find_save_files(tmp_path)
        assert len(result) == 2
        assert all(p.suffix == ".autosave" for p in result)


class TestLoadAndWriteSave:
    def test_round_trip(self, tmp_path):
        save_path = tmp_path / "test.autosave"
        encoded = encode_save(SAMPLE_DATA)
        save_path.write_text(encoded)

        loaded = load_save(save_path)
        assert loaded["gold"] == 99
        assert loaded["current_health"] == 72
        assert loaded["cards"][0]["id"] == "Bash"

    def test_write_then_load(self, tmp_path):
        save_path = tmp_path / "test.autosave"
        write_save(save_path, SAMPLE_DATA)
        loaded = load_save(save_path)
        assert loaded == SAMPLE_DATA


class TestCreateBackup:
    def test_creates_backup_file(self, tmp_path):
        original = tmp_path / "test.autosave"
        original.write_text("original content")
        backup = create_backup(original)
        assert backup.exists()
        assert backup.read_text() == "original content"
        assert ".bak." in backup.name

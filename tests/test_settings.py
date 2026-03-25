"""Tests for gui.settings — persistent settings."""

import json
from unittest.mock import patch

from gui import settings


class TestSettings:
    def test_get_returns_none_when_no_file(self, tmp_path):
        fake_file = tmp_path / "settings.json"
        with patch.object(settings, "_SETTINGS_FILE", fake_file):
            assert settings.get_steam_user_id() is None

    def test_set_and_get_round_trip(self, tmp_path):
        fake_dir = tmp_path / "config"
        fake_file = fake_dir / "settings.json"
        with (
            patch.object(settings, "_SETTINGS_DIR", fake_dir),
            patch.object(settings, "_SETTINGS_FILE", fake_file),
        ):
            settings.set_steam_user_id("12345")
            assert settings.get_steam_user_id() == "12345"

    def test_set_overwrites_previous(self, tmp_path):
        fake_dir = tmp_path / "config"
        fake_file = fake_dir / "settings.json"
        with (
            patch.object(settings, "_SETTINGS_DIR", fake_dir),
            patch.object(settings, "_SETTINGS_FILE", fake_file),
        ):
            settings.set_steam_user_id("11111")
            settings.set_steam_user_id("22222")
            assert settings.get_steam_user_id() == "22222"

    def test_preserves_other_keys(self, tmp_path):
        fake_dir = tmp_path / "config"
        fake_file = fake_dir / "settings.json"
        fake_dir.mkdir(parents=True)
        fake_file.write_text(json.dumps({"other_key": "value"}))
        with (
            patch.object(settings, "_SETTINGS_DIR", fake_dir),
            patch.object(settings, "_SETTINGS_FILE", fake_file),
        ):
            settings.set_steam_user_id("12345")
            data = json.loads(fake_file.read_text())
            assert data["other_key"] == "value"
            assert data["steam_user_id"] == "12345"

    def test_handles_corrupt_json(self, tmp_path):
        fake_dir = tmp_path / "config"
        fake_file = fake_dir / "settings.json"
        fake_dir.mkdir(parents=True)
        fake_file.write_text("not valid json{{{")
        with patch.object(settings, "_SETTINGS_FILE", fake_file):
            assert settings.get_steam_user_id() is None

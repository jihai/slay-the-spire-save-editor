"""Tests for gui.game_config — factory functions and field values."""

from pathlib import Path

from gui.game_config import GameConfig, sts1_config, sts2_config


class TestSTS1Config:
    def test_game_version(self):
        cfg = sts1_config()
        assert cfg.game_version == 1

    def test_app_title(self):
        cfg = sts1_config()
        assert "Slay the Spire" in cfg.app_title
        assert "2" not in cfg.app_title

    def test_file_glob(self):
        cfg = sts1_config()
        assert cfg.file_glob == "*.autosave"

    def test_file_filter_contains_autosave(self):
        cfg = sts1_config()
        assert "autosave" in cfg.file_filter

    def test_encrypted(self):
        cfg = sts1_config()
        assert cfg.encrypted is True

    def test_has_card_upgrades(self):
        cfg = sts1_config()
        assert cfg.has_card_upgrades is True

    def test_game_resources_dir_exists(self):
        cfg = sts1_config()
        assert cfg.game_resources_dir.exists()
        assert cfg.game_resources_dir.name == "game_resources"

    def test_frozen(self):
        cfg = sts1_config()
        try:
            cfg.game_version = 99
            assert False, "Should have raised"
        except AttributeError:
            pass


class TestSTS2Config:
    def test_game_version(self):
        cfg = sts2_config()
        assert cfg.game_version == 2

    def test_app_title(self):
        cfg = sts2_config()
        assert "2" in cfg.app_title

    def test_file_glob(self):
        cfg = sts2_config()
        assert cfg.file_glob == "*.save"

    def test_file_filter_contains_save(self):
        cfg = sts2_config()
        assert ".save" in cfg.file_filter

    def test_encrypted(self):
        cfg = sts2_config()
        assert cfg.encrypted is False

    def test_has_card_upgrades(self):
        cfg = sts2_config()
        assert cfg.has_card_upgrades is False

    def test_game_resources_dir_name(self):
        cfg = sts2_config()
        assert cfg.game_resources_dir.name == "game_resources_sts2"

    def test_is_gameconfig_instance(self):
        assert isinstance(sts1_config(), GameConfig)
        assert isinstance(sts2_config(), GameConfig)

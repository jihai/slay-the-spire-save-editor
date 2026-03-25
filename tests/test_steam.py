"""Tests for gui.steam — Steam user ID detection."""

from pathlib import Path

from gui.steam import STS2_SAVE_SUBPATH, detect_steam_users, sts2_save_dir


class TestDetectSteamUsers:
    def test_no_users_when_dir_missing(self, tmp_path):
        assert detect_steam_users(tmp_path / "nonexistent") == []

    def test_no_users_when_empty(self, tmp_path):
        assert detect_steam_users(tmp_path) == []

    def test_ignores_non_numeric_dirs(self, tmp_path):
        (tmp_path / "abc" / STS2_SAVE_SUBPATH).mkdir(parents=True)
        assert detect_steam_users(tmp_path) == []

    def test_ignores_users_without_sts2(self, tmp_path):
        (tmp_path / "12345").mkdir()
        assert detect_steam_users(tmp_path) == []

    def test_detects_single_user(self, tmp_path):
        (tmp_path / "12345" / STS2_SAVE_SUBPATH).mkdir(parents=True)
        assert detect_steam_users(tmp_path) == ["12345"]

    def test_detects_multiple_users_sorted(self, tmp_path):
        (tmp_path / "99999" / STS2_SAVE_SUBPATH).mkdir(parents=True)
        (tmp_path / "11111" / STS2_SAVE_SUBPATH).mkdir(parents=True)
        assert detect_steam_users(tmp_path) == ["11111", "99999"]

    def test_mixed_valid_and_invalid(self, tmp_path):
        (tmp_path / "55555" / STS2_SAVE_SUBPATH).mkdir(parents=True)
        (tmp_path / "abc" / STS2_SAVE_SUBPATH).mkdir(parents=True)
        (tmp_path / "22222").mkdir()  # no saves subdir
        assert detect_steam_users(tmp_path) == ["55555"]


class TestSts2SaveDir:
    def test_returns_correct_path(self, tmp_path):
        result = sts2_save_dir("12345", userdata_dir=tmp_path)
        assert result == tmp_path / "12345" / STS2_SAVE_SUBPATH

    def test_default_base(self):
        result = sts2_save_dir("12345")
        assert "12345" in str(result)
        assert "2868840" in str(result)
        assert str(result).endswith("saves")

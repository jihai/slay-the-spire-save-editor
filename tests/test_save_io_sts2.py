"""Tests for gui.save_io with STS2 config (plain JSON, no encryption)."""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from gui.game_config import GameConfig, sts2_config
from gui.save_io import find_save_files, load_save, write_save
from gui.steam import STS2_APP_ID, STS2_OLD_SAVE_SUBPATH

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

    def test_write_deletes_backup_file(self, tmp_path):
        """Writing an STS2 save should remove the .backup sibling."""
        cfg = sts2_config()
        save_path = tmp_path / "current_run.save"
        backup_path = tmp_path / "current_run.save.backup"

        # Create an existing backup file
        backup_path.write_text('{"old": true}', encoding="utf-8")
        assert backup_path.exists()

        write_save(save_path, STS2_SAMPLE, config=cfg)

        assert save_path.exists()
        assert not backup_path.exists()  # backup must be deleted

    def test_write_works_without_backup(self, tmp_path):
        """Writing should succeed even if no backup file exists."""
        cfg = sts2_config()
        save_path = tmp_path / "current_run.save"
        write_save(save_path, STS2_SAMPLE, config=cfg)
        assert save_path.exists()


class TestSteamCacheSync:
    """Tests for dual-write to old Steam location + remotecache.vdf update."""

    SAMPLE_VDF = '''"2868840"
{{
\t"ChangeNumber"\t\t"6"
\t"profile1/saves/current_run.save"
\t{{
\t\t"root"\t\t"0"
\t\t"size"\t\t"100"
\t\t"localtime"\t\t"1000000"
\t\t"time"\t\t"1000000"
\t\t"remotetime"\t\t"999999"
\t\t"sha"\t\t"oldsha"
\t\t"syncstate"\t\t"1"
\t\t"persiststate"\t\t"0"
\t\t"platformstosync2"\t\t"-1"
\t}}
}}
'''

    def _setup_old_dir(self, tmp_path, user_id="12345"):
        """Create old Steam dir structure and return (old_saves_dir, vdf_path)."""
        userdata = tmp_path / "userdata"
        old_saves = userdata / user_id / STS2_OLD_SAVE_SUBPATH
        old_saves.mkdir(parents=True)
        vdf_path = userdata / user_id / STS2_APP_ID / "remotecache.vdf"
        vdf_path.write_text(self.SAMPLE_VDF)
        return old_saves, vdf_path, userdata

    def _make_config(self, tmp_path, user_id="12345", userdata=None):
        """Create a GameConfig with steam_user_id pointing to tmp dirs."""
        # We need to patch the default STEAM_USERDATA_DIR so the sync finds our tmp dir
        save_dir = tmp_path / "new_saves"
        save_dir.mkdir(parents=True, exist_ok=True)
        return GameConfig(
            game_version=2,
            app_title="test",
            save_dir=save_dir,
            file_glob="*.save",
            file_filter="Save Files (*.save)",
            game_resources_dir=tmp_path,
            encrypted=False,
            has_card_upgrades=True,
            steam_user_id=user_id,
        )

    def test_syncs_file_to_old_location(self, tmp_path):
        old_saves, vdf_path, userdata = self._setup_old_dir(tmp_path)
        cfg = self._make_config(tmp_path)
        save_path = tmp_path / "new_saves" / "current_run.save"

        with patch("gui.steam.sts2_old_save_dir", return_value=old_saves), \
             patch("gui.steam.remotecache_vdf_path", return_value=vdf_path):
            write_save(save_path, STS2_SAMPLE, config=cfg)

        # File should exist in old location with same content
        old_file = old_saves / "current_run.save"
        assert old_file.exists()
        assert json.loads(old_file.read_text()) == STS2_SAMPLE

    def test_updates_remotecache_vdf(self, tmp_path):
        old_saves, vdf_path, userdata = self._setup_old_dir(tmp_path)
        cfg = self._make_config(tmp_path)
        save_path = tmp_path / "new_saves" / "current_run.save"

        with patch("gui.steam.sts2_old_save_dir", return_value=old_saves), \
             patch("gui.steam.remotecache_vdf_path", return_value=vdf_path):
            write_save(save_path, STS2_SAMPLE, config=cfg)

        # Compute expected SHA
        file_bytes = save_path.read_bytes()
        expected_sha = hashlib.sha1(file_bytes).hexdigest()
        expected_size = str(len(file_bytes))

        vdf_text = vdf_path.read_text()
        assert expected_sha in vdf_text
        assert f'"size"\t\t"{expected_size}"' in vdf_text
        # Old SHA should be gone
        assert "oldsha" not in vdf_text

    def test_no_sync_without_steam_user_id(self, tmp_path):
        """write_save with no steam_user_id should not attempt sync."""
        cfg = sts2_config()  # no steam_user_id
        save_path = tmp_path / "current_run.save"
        # Should not raise even though old location doesn't exist
        write_save(save_path, STS2_SAMPLE, config=cfg)
        assert save_path.exists()

    def test_sync_failure_does_not_block_primary_save(self, tmp_path):
        """If sync fails, the primary save should still succeed."""
        cfg = self._make_config(tmp_path)
        save_path = tmp_path / "new_saves" / "current_run.save"

        # Don't create old dir — sync will fail, but primary save should work
        with patch("gui.steam.sts2_old_save_dir", return_value=tmp_path / "nonexistent"):
            write_save(save_path, STS2_SAMPLE, config=cfg)

        assert save_path.exists()
        assert json.loads(save_path.read_text()) == STS2_SAMPLE

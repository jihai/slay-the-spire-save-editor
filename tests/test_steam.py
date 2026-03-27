"""Tests for gui.steam — Steam ID conversion, user detection, and display names."""

from pathlib import Path

from gui.steam import (
    STEAM_ID_OFFSET,
    STS2_APP_ID,
    STS2_NEW_SAVE_SUBPATH,
    STS2_OLD_SAVE_SUBPATH,
    detect_steam_users,
    get_steam_display_names,
    long_to_short_steam_id,
    parse_login_users_vdf,
    remotecache_vdf_path,
    short_to_long_steam_id,
    sts2_old_save_dir,
    sts2_save_dir,
    update_remotecache_sha,
)


class TestSteamIdConversion:
    def test_short_to_long_known_value(self):
        assert short_to_long_steam_id("100200300") == "76561198060466028"

    def test_long_to_short_known_value(self):
        assert long_to_short_steam_id("76561198060466028") == "100200300"

    def test_round_trip_short_to_long_to_short(self):
        assert long_to_short_steam_id(short_to_long_steam_id("12345")) == "12345"

    def test_round_trip_long_to_short_to_long(self):
        long_id = str(STEAM_ID_OFFSET + 99999)
        assert short_to_long_steam_id(long_to_short_steam_id(long_id)) == long_id

    def test_zero(self):
        assert short_to_long_steam_id("0") == str(STEAM_ID_OFFSET)
        assert long_to_short_steam_id(str(STEAM_ID_OFFSET)) == "0"


class TestDetectSteamUsers:
    def _make_user(self, base: Path, long_id: str) -> None:
        """Create a fake STS2 user directory with the new path structure."""
        (base / long_id / STS2_NEW_SAVE_SUBPATH).mkdir(parents=True)

    def test_no_users_when_dir_missing(self, tmp_path):
        assert detect_steam_users(tmp_path / "nonexistent") == []

    def test_no_users_when_empty(self, tmp_path):
        assert detect_steam_users(tmp_path) == []

    def test_ignores_non_numeric_dirs(self, tmp_path):
        (tmp_path / "abc" / STS2_NEW_SAVE_SUBPATH).mkdir(parents=True)
        assert detect_steam_users(tmp_path) == []

    def test_ignores_users_without_saves_subpath(self, tmp_path):
        (tmp_path / "76561198060466028").mkdir()
        assert detect_steam_users(tmp_path) == []

    def test_detects_single_user(self, tmp_path):
        long_id = short_to_long_steam_id("12345")
        self._make_user(tmp_path, long_id)
        assert detect_steam_users(tmp_path) == ["12345"]

    def test_detects_multiple_users_sorted(self, tmp_path):
        self._make_user(tmp_path, short_to_long_steam_id("99999"))
        self._make_user(tmp_path, short_to_long_steam_id("11111"))
        assert detect_steam_users(tmp_path) == ["11111", "99999"]

    def test_mixed_valid_and_invalid(self, tmp_path):
        self._make_user(tmp_path, short_to_long_steam_id("55555"))
        (tmp_path / "abc" / STS2_NEW_SAVE_SUBPATH).mkdir(parents=True)
        (tmp_path / short_to_long_steam_id("22222")).mkdir()  # no saves subdir
        assert detect_steam_users(tmp_path) == ["55555"]


class TestSts2SaveDir:
    def test_returns_correct_new_path(self, tmp_path):
        result = sts2_save_dir("12345", new_base_dir=tmp_path)
        long_id = short_to_long_steam_id("12345")
        assert result == tmp_path / long_id / STS2_NEW_SAVE_SUBPATH

    def test_default_base_contains_slaythe_spire2(self):
        result = sts2_save_dir("12345")
        assert "SlayTheSpire2" in str(result)
        assert str(result).endswith("saves")

    def test_path_contains_long_id(self):
        result = sts2_save_dir("100200300")
        assert "76561198060466028" in str(result)


class TestParseLoginUsersVdf:
    SAMPLE_VDF = '''"users"
{
\t"76561198060466028"
\t{
\t\t"AccountName"\t\t"testuser"
\t\t"PersonaName"\t\t"TestPlayer"
\t\t"RememberPassword"\t\t"1"
\t}
\t"76561198360766328"
\t{
\t\t"AccountName"\t\t"otheruser"
\t\t"PersonaName"\t\t"OtherPlayer"
\t\t"RememberPassword"\t\t"1"
\t}
}
'''

    def test_parses_persona_names(self, tmp_path):
        vdf = tmp_path / "loginusers.vdf"
        vdf.write_text(self.SAMPLE_VDF)
        result = parse_login_users_vdf(vdf)
        assert result == {
            "76561198060466028": "TestPlayer",
            "76561198360766328": "OtherPlayer",
        }

    def test_returns_empty_when_file_missing(self, tmp_path):
        assert parse_login_users_vdf(tmp_path / "nope.vdf") == {}

    def test_returns_empty_for_empty_file(self, tmp_path):
        vdf = tmp_path / "loginusers.vdf"
        vdf.write_text("")
        assert parse_login_users_vdf(vdf) == {}


class TestGetSteamDisplayNames:
    def test_maps_short_ids_to_names(self, tmp_path):
        vdf = tmp_path / "loginusers.vdf"
        vdf.write_text('''"users"
{
\t"76561198060466028"
\t{
\t\t"PersonaName"\t\t"TestPlayer"
\t}
}
''')
        result = get_steam_display_names(vdf_path=vdf)
        assert result == {"100200300": "TestPlayer"}

    def test_returns_empty_when_no_vdf(self, tmp_path):
        assert get_steam_display_names(vdf_path=tmp_path / "nope.vdf") == {}


class TestSts2OldSaveDir:
    def test_returns_correct_path(self, tmp_path):
        result = sts2_old_save_dir("12345", userdata_dir=tmp_path)
        assert result == tmp_path / "12345" / STS2_OLD_SAVE_SUBPATH

    def test_default_base_contains_userdata(self):
        result = sts2_old_save_dir("12345")
        assert "userdata" in str(result)
        assert "12345" in str(result)
        assert "2868840" in str(result)
        assert str(result).endswith("saves")


class TestRemotecacheVdfPath:
    def test_returns_correct_path(self, tmp_path):
        result = remotecache_vdf_path("12345", userdata_dir=tmp_path)
        assert result == tmp_path / "12345" / STS2_APP_ID / "remotecache.vdf"


class TestUpdateRemotecacheSha:
    SAMPLE_VDF = '''"2868840"
{
\t"ChangeNumber"\t\t"6"
\t"ostype"\t\t"-102"
\t"profile1/saves/current_run.save"
\t{
\t\t"root"\t\t"0"
\t\t"size"\t\t"45325"
\t\t"localtime"\t\t"1774644148"
\t\t"time"\t\t"1774644148"
\t\t"remotetime"\t\t"1774591751"
\t\t"sha"\t\t"2865c17d26c14db9e40b9e9b658839f932fd7723"
\t\t"syncstate"\t\t"3"
\t\t"persiststate"\t\t"0"
\t\t"platformstosync2"\t\t"-1"
\t}
\t"profile1/saves/progress.save"
\t{
\t\t"root"\t\t"0"
\t\t"size"\t\t"121962"
\t\t"localtime"\t\t"1774644148"
\t\t"time"\t\t"1774644148"
\t\t"remotetime"\t\t"1774594497"
\t\t"sha"\t\t"84d42e5bc934c08ce7428fd29ccddc53d9bf230d"
\t\t"syncstate"\t\t"3"
\t\t"persiststate"\t\t"0"
\t\t"platformstosync2"\t\t"-1"
\t}
}
'''

    def test_updates_sha_size_and_timestamps(self, tmp_path):
        vdf = tmp_path / "remotecache.vdf"
        vdf.write_text(self.SAMPLE_VDF)

        result = update_remotecache_sha(
            vdf, "profile1/saves/current_run.save",
            sha="aaaa1111bbbb2222cccc3333dddd4444eeee5555",
            size=99999,
            timestamp=1800000000,
        )
        assert result is True

        updated = vdf.read_text()
        assert "aaaa1111bbbb2222cccc3333dddd4444eeee5555" in updated
        assert '"size"\t\t"99999"' in updated
        assert '"localtime"\t\t"1800000000"' in updated
        assert '"time"\t\t"1800000000"' in updated

    def test_does_not_modify_other_entries(self, tmp_path):
        vdf = tmp_path / "remotecache.vdf"
        vdf.write_text(self.SAMPLE_VDF)

        update_remotecache_sha(
            vdf, "profile1/saves/current_run.save",
            sha="newsha", size=1, timestamp=1,
        )
        updated = vdf.read_text()
        # progress.save entry should be untouched
        assert "84d42e5bc934c08ce7428fd29ccddc53d9bf230d" in updated
        assert '"size"\t\t"121962"' in updated

    def test_returns_false_when_key_not_found(self, tmp_path):
        vdf = tmp_path / "remotecache.vdf"
        vdf.write_text(self.SAMPLE_VDF)
        result = update_remotecache_sha(
            vdf, "nonexistent.save", sha="x", size=0, timestamp=0,
        )
        assert result is False

    def test_returns_false_when_file_missing(self, tmp_path):
        result = update_remotecache_sha(
            tmp_path / "nope.vdf", "key", sha="x", size=0, timestamp=0,
        )
        assert result is False

"""Smoke tests for paige_core.

These cover the parts of Paige that actually matter for data integrity:
the atomic-save guarantee, settings round-tripping, validation edge cases,
and line-ending detection. The Tk-driven UI code lives in main.py and is
exercised by daily use rather than automated tests.

Run: pytest tests/
"""

import json
import os
import re

import pytest

import paige_core


# ------------------------------------------------------------------------------
# Version
# ------------------------------------------------------------------------------
def test_version_is_string():
    assert isinstance(paige_core.__version__, str)
    assert paige_core.__version__  # not empty


def test_version_matches_simple_format():
    # Either "X.Y" or "X.Y.Z" — keep the build workflow's parsing happy.
    assert re.match(r"^\d+\.\d+(\.\d+)?$", paige_core.__version__)


# ------------------------------------------------------------------------------
# parse_cli_args
# ------------------------------------------------------------------------------
def test_parse_cli_args_no_args_returns_none():
    assert paige_core.parse_cli_args(["paige.exe"]) is None


def test_parse_cli_args_returns_first_positional():
    assert paige_core.parse_cli_args(["paige.exe", "foo.txt"]) == "foo.txt"


def test_parse_cli_args_returns_first_of_multiple_positionals():
    assert paige_core.parse_cli_args(["paige.exe", "a.txt", "b.txt"]) == "a.txt"


def test_parse_cli_args_skips_flags():
    assert paige_core.parse_cli_args(["paige.exe", "--debug", "foo.txt"]) == "foo.txt"


def test_parse_cli_args_returns_none_if_only_flags():
    assert paige_core.parse_cli_args(["paige.exe", "--help"]) is None


def test_parse_cli_args_accepts_path_with_spaces():
    # Shells strip the quotes; we get the literal string.
    assert paige_core.parse_cli_args(["paige.exe", "C:\\path with space\\file.log"]) == "C:\\path with space\\file.log"


# ------------------------------------------------------------------------------
# Settings round-trip
# ------------------------------------------------------------------------------
def test_settings_round_trip(tmp_path):
    path = str(tmp_path / "settings.json")
    original = {
        "version": 1,
        "font_size": 18,
        "appearance_mode": "Light",
        "word_wrap": True,
        "window_geometry": "1024x768+100+50",
        "recent_files": ["/tmp/a.txt", "/tmp/b.log"],
    }
    paige_core.save_settings(original, path=path)
    loaded = paige_core.load_settings(path=path)
    assert loaded == original


def test_load_settings_returns_empty_on_missing_file(tmp_path):
    assert paige_core.load_settings(path=str(tmp_path / "nonexistent.json")) == {}


def test_load_settings_returns_empty_on_corrupt_json(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("{this is not valid json")
    assert paige_core.load_settings(path=str(path)) == {}


def test_load_settings_returns_empty_on_non_dict_root(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text("[1, 2, 3]")
    assert paige_core.load_settings(path=str(path)) == {}


def test_save_settings_silently_succeeds_on_unwritable_dir(tmp_path):
    # Pointing at a path whose parent we can't create — should not raise.
    bad_path = "/this/path/definitely/does/not/exist/and/cannot/be/created/settings.json"
    paige_core.save_settings({"font_size": 14}, path=bad_path)
    # No assertion needed; we just need this to not raise.


# ------------------------------------------------------------------------------
# validate_settings
# ------------------------------------------------------------------------------
def test_validate_settings_empty_returns_full_defaults():
    out = paige_core.validate_settings({})
    assert out["font_size"] == 14
    assert out["appearance_mode"] == "Dark"
    assert out["word_wrap"] is False
    assert out["window_geometry"] == "900x700"
    assert out["recent_files"] == []


def test_validate_settings_handles_non_dict_input():
    assert paige_core.validate_settings(None)["font_size"] == 14
    assert paige_core.validate_settings("oops")["font_size"] == 14
    assert paige_core.validate_settings(42)["font_size"] == 14


def test_validate_settings_clamps_font_size_too_low():
    assert paige_core.validate_settings({"font_size": 4})["font_size"] == 14


def test_validate_settings_clamps_font_size_too_high():
    assert paige_core.validate_settings({"font_size": 999})["font_size"] == 14


def test_validate_settings_rejects_non_int_font_size():
    assert paige_core.validate_settings({"font_size": "big"})["font_size"] == 14


def test_validate_settings_accepts_valid_font_size():
    assert paige_core.validate_settings({"font_size": 18})["font_size"] == 18


def test_validate_settings_rejects_invalid_theme():
    assert paige_core.validate_settings({"appearance_mode": "Hot Pink"})["appearance_mode"] == "Dark"


def test_validate_settings_accepts_light_theme():
    assert paige_core.validate_settings({"appearance_mode": "Light"})["appearance_mode"] == "Light"


def test_validate_settings_rejects_invalid_geometry():
    assert paige_core.validate_settings({"window_geometry": "not a geometry"})["window_geometry"] == "900x700"


def test_validate_settings_accepts_geometry_without_position():
    assert paige_core.validate_settings({"window_geometry": "800x600"})["window_geometry"] == "800x600"


def test_validate_settings_accepts_geometry_with_position():
    assert paige_core.validate_settings({"window_geometry": "800x600+100+50"})["window_geometry"] == "800x600+100+50"


def test_validate_settings_filters_non_string_recents():
    out = paige_core.validate_settings({"recent_files": ["good.txt", 42, None, "also-good.txt"]})
    assert out["recent_files"] == ["good.txt", "also-good.txt"]


def test_validate_settings_handles_non_list_recents():
    assert paige_core.validate_settings({"recent_files": "oops"})["recent_files"] == []


def test_validate_settings_truncates_recents_to_max():
    paths = [f"/tmp/{i}.txt" for i in range(20)]
    out = paige_core.validate_settings({"recent_files": paths})
    assert len(out["recent_files"]) == paige_core.RECENT_FILES_MAX
    assert out["recent_files"] == paths[:paige_core.RECENT_FILES_MAX]


def test_validate_settings_word_wrap_coerced_to_bool():
    assert paige_core.validate_settings({"word_wrap": 1})["word_wrap"] is True
    assert paige_core.validate_settings({"word_wrap": 0})["word_wrap"] is False


# ------------------------------------------------------------------------------
# detect_newline
# ------------------------------------------------------------------------------
def test_detect_newline_crlf():
    assert paige_core.detect_newline("line1\r\nline2\r\n") == "\r\n"


def test_detect_newline_lf():
    assert paige_core.detect_newline("line1\nline2\n") == "\n"


def test_detect_newline_cr_only():
    assert paige_core.detect_newline("line1\rline2\r") == "\r"


def test_detect_newline_empty_defaults_to_lf():
    assert paige_core.detect_newline("") == "\n"


def test_detect_newline_single_line_no_trailing_nl_defaults_to_lf():
    assert paige_core.detect_newline("just one line") == "\n"


def test_detect_newline_mixed_prefers_crlf():
    # If \r\n is present, it wins — that's the Windows convention and
    # the most common real-world case for a mixed file.
    assert paige_core.detect_newline("line1\r\nline2\nline3\r\n") == "\r\n"


# ------------------------------------------------------------------------------
# read_text_file
# ------------------------------------------------------------------------------
def test_read_text_file_round_trip_lf(tmp_path):
    path = tmp_path / "f.txt"
    path.write_bytes(b"hello\nworld\n")
    content, nl = paige_core.read_text_file(str(path))
    assert content == "hello\nworld\n"
    assert nl == "\n"


def test_read_text_file_round_trip_crlf(tmp_path):
    path = tmp_path / "f.txt"
    path.write_bytes(b"hello\r\nworld\r\n")
    content, nl = paige_core.read_text_file(str(path))
    # Content is normalized to \n for the Tk widget.
    assert content == "hello\nworld\n"
    assert nl == "\r\n"


def test_read_text_file_raises_on_bad_encoding(tmp_path):
    path = tmp_path / "f.txt"
    path.write_bytes(b"\xff\xfe\x00invalid utf-8")
    with pytest.raises(UnicodeDecodeError):
        paige_core.read_text_file(str(path))


# ------------------------------------------------------------------------------
# write_atomic — the heart of the data-integrity guarantee
# ------------------------------------------------------------------------------
def test_write_atomic_writes_content(tmp_path):
    path = tmp_path / "out.txt"
    paige_core.write_atomic(str(path), "hello world")
    assert path.read_text(encoding="utf-8") == "hello world"


def test_write_atomic_preserves_lf_newline(tmp_path):
    path = tmp_path / "out.txt"
    paige_core.write_atomic(str(path), "a\nb\nc", newline="\n")
    # Read raw bytes to confirm no translation occurred.
    assert path.read_bytes() == b"a\nb\nc"


def test_write_atomic_converts_lf_to_crlf_when_requested(tmp_path):
    path = tmp_path / "out.txt"
    paige_core.write_atomic(str(path), "a\nb\nc", newline="\r\n")
    assert path.read_bytes() == b"a\r\nb\r\nc"


def test_write_atomic_leaves_no_temp_files_on_success(tmp_path):
    path = tmp_path / "out.txt"
    paige_core.write_atomic(str(path), "hello")
    leftover = list(tmp_path.glob(".paige-*.tmp"))
    assert leftover == []


def test_write_atomic_leaves_original_intact_on_replace_failure(tmp_path, monkeypatch):
    """The atomic-save claim: if anything fails after the temp file is
    written, the destination must still hold the original content."""
    path = tmp_path / "important.txt"
    path.write_text("ORIGINAL CONTENT")

    def boom(src, dst):
        raise OSError("simulated disk full")

    monkeypatch.setattr(os, "replace", boom)

    with pytest.raises(OSError, match="simulated"):
        paige_core.write_atomic(str(path), "NEW CONTENT")

    assert path.read_text() == "ORIGINAL CONTENT"
    # And no temp file should be left behind.
    leftover = list(tmp_path.glob(".paige-*.tmp"))
    assert leftover == []


def test_write_atomic_leaves_original_intact_on_fsync_failure(tmp_path, monkeypatch):
    """Failure during fsync (e.g. disk error before commit) must also
    leave the original untouched."""
    path = tmp_path / "important.txt"
    path.write_text("ORIGINAL")

    def boom(fd):
        raise OSError("simulated I/O error")

    monkeypatch.setattr(os, "fsync", boom)

    with pytest.raises(OSError, match="simulated"):
        paige_core.write_atomic(str(path), "NEW")

    assert path.read_text() == "ORIGINAL"
    leftover = list(tmp_path.glob(".paige-*.tmp"))
    assert leftover == []


def test_write_atomic_creates_file_when_target_missing(tmp_path):
    path = tmp_path / "brand-new.txt"
    assert not path.exists()
    paige_core.write_atomic(str(path), "hello")
    assert path.read_text() == "hello"


# ------------------------------------------------------------------------------
# stat_for_change_detection
# ------------------------------------------------------------------------------
def test_stat_for_change_detection_returns_mtime_and_size(tmp_path):
    path = tmp_path / "f.txt"
    path.write_text("hello")
    mtime, size = paige_core.stat_for_change_detection(str(path))
    assert isinstance(mtime, int)
    assert size == 5


def test_stat_for_change_detection_returns_none_for_missing(tmp_path):
    mtime, size = paige_core.stat_for_change_detection(str(tmp_path / "nope.txt"))
    assert mtime is None
    assert size is None


# ------------------------------------------------------------------------------
# settings_path — basic platform sanity
# ------------------------------------------------------------------------------
def test_settings_path_returns_paige_in_path():
    path = paige_core.settings_path()
    # Whatever the OS, "Paige" or "paige" should be a path component.
    assert "paige" in path.lower()
    assert path.endswith("settings.json")

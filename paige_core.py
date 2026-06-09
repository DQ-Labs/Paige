"""Pure-Python helpers for Paige.

Everything in this module avoids importing Tkinter / customtkinter so it can be
imported and tested in a headless environment (CI runners without a display).
The GUI shell in `main.py` imports from here.

This is also the single source of truth for `__version__` — the build workflow
extracts it from this file when stamping the Windows executable's version
metadata.
"""

import json
import os
import re
import sys
import tempfile


__version__ = "1.0"

RECENT_FILES_MAX = 10
GEOMETRY_RE = re.compile(r"^\d+x\d+([+-]\d+[+-]\d+)?$")


# ------------------------------------------------------------------------------
# CLI argument parsing
# ------------------------------------------------------------------------------
def parse_cli_args(argv):
    """Returns the first non-flag positional argument from argv, or None.

    Intentionally minimal — Paige is a windowed binary, so flag parsing
    can't usefully report errors to stdout. Anything starting with '-' is
    skipped so PyInstaller / shell internals can't be misread as a filename.
    """
    for arg in argv[1:]:
        if arg.startswith("-"):
            continue
        return arg
    return None


# ------------------------------------------------------------------------------
# Settings persistence
# ------------------------------------------------------------------------------
def settings_path():
    """Returns the per-user settings file path for the current OS."""
    if os.name == "nt":
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return os.path.join(base, "Paige", "settings.json")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support/Paige/settings.json")
    xdg = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    return os.path.join(xdg, "paige", "settings.json")


def load_settings(path=None):
    """Reads settings.json. Returns {} on any failure — a corrupt or missing
    prefs file must never prevent the editor from launching.

    `path` is overridable so tests can inject a temp file.
    """
    if path is None:
        path = settings_path()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError, ValueError):
        return {}


def save_settings(settings, path=None):
    """Atomically writes settings to disk. Best-effort — never raises;
    a failure to save prefs shouldn't disrupt edits."""
    if path is None:
        path = settings_path()
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except OSError:
        return
    try:
        write_atomic(path, json.dumps(settings, indent=2, sort_keys=True))
    except OSError:
        pass


def validate_settings(raw):
    """Coerce a raw settings dict into a fully-populated, type-checked one.

    Every key has a known default. Out-of-range or wrong-type values fall
    back to the default rather than crashing the editor. This is the single
    place all settings validation lives, so tests can cover it directly.
    """
    if not isinstance(raw, dict):
        raw = {}

    out = {}

    font_size = raw.get("font_size", 14)
    out["font_size"] = font_size if isinstance(font_size, int) and 10 <= font_size <= 30 else 14

    appearance = raw.get("appearance_mode", "Dark")
    out["appearance_mode"] = appearance if appearance in ("Dark", "Light") else "Dark"

    out["word_wrap"] = bool(raw.get("word_wrap", False))

    geom = raw.get("window_geometry", "900x700")
    out["window_geometry"] = geom if isinstance(geom, str) and GEOMETRY_RE.match(geom) else "900x700"

    recents = raw.get("recent_files", [])
    if not isinstance(recents, list):
        recents = []
    out["recent_files"] = [p for p in recents if isinstance(p, str)][:RECENT_FILES_MAX]

    return out


# ------------------------------------------------------------------------------
# File I/O
# ------------------------------------------------------------------------------
def detect_newline(raw):
    """Detect the line-ending style of raw text. Returns '\\r\\n', '\\r', or '\\n'.

    Empty / single-line text defaults to '\\n'.
    """
    if "\r\n" in raw:
        return "\r\n"
    if "\r" in raw:
        return "\r"
    return "\n"


def read_text_file(path, encoding="utf-8"):
    """Read a text file, detect its line ending, and normalize content to \\n.

    Returns (content, newline). Raises UnicodeDecodeError on bad encoding,
    OSError on I/O failure — callers decide how to surface those.
    """
    with open(path, "r", encoding=encoding, newline="") as f:
        raw = f.read()
    nl = detect_newline(raw)
    content = raw.replace("\r\n", "\n").replace("\r", "\n")
    return content, nl


def write_atomic(path, content, encoding="utf-8", newline=None):
    """Atomically write content to path.

    Strategy: write to a sibling temp file, flush + fsync, then os.replace()
    into place. A crash, power loss, or full disk during the write cannot
    leave the destination half-written — either the old contents or the new
    contents are on disk, never a truncated hybrid.

    If `newline` is given (and not '\\n'), '\\n' in content is translated to
    `newline` before writing. The file itself is opened with newline="" so
    Python does no additional translation of its own.

    Raises OSError on failure. On any exception, the destination file is
    untouched and the partial temp file is cleaned up.
    """
    if newline is not None and newline != "\n":
        content = content.replace("\n", newline)

    target_dir = os.path.dirname(os.path.abspath(path)) or "."

    tmp_fd = None
    tmp_path = None
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(
            prefix=".paige-", suffix=".tmp", dir=target_dir
        )
        with os.fdopen(tmp_fd, "w", encoding=encoding, newline="") as f:
            tmp_fd = None  # fdopen now owns the descriptor
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, path)
        tmp_path = None
    finally:
        if tmp_fd is not None:
            try:
                os.close(tmp_fd)
            except OSError:
                pass
        if tmp_path is not None and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def stat_for_change_detection(path):
    """Returns (mtime_ns, size) for external-change detection, or (None, None)
    if the path can't be stat'd. Nanosecond precision avoids false positives
    from filesystem mtime resolution."""
    try:
        st = os.stat(path)
        return st.st_mtime_ns, st.st_size
    except OSError:
        return None, None

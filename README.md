# Paige

![Build Status](https://github.com/DQ-Labs/paige/actions/workflows/build.yml/badge.svg)

## The "Why"
Paige is a **Dumb Text Editor** — and that's the entire point.

Modern editors like Windows Notepad, VS Code, and Notepad++ have grown into complex document *renderers*. They interpret Markdown, resolve protocol handlers (`file://`, `ms-appinstaller://`), and spin up entire language server processes. Every one of those features is an attack surface.

Paige refuses to render *anything*. It reads bytes and displays them as text. That's it. No Markdown preview. No protocol resolution. No shell execution. No cloud sync. The RCE attack surface found in modern Notepad **does not exist here**, because the feature that enables it doesn't exist either.

Built by a sysadmin, for sysadmins — optimized for opening multi-gigabyte log files, editing configs over RDP, and not having to think about whether your editor is a malware vector.

## Security Design
Paige's security model is "do less." Every item below is something the editor deliberately *doesn't* do — which is what keeps the attack surface small.

- **No rendering, no parsing.** Text is displayed verbatim. Markdown, HTML, RTF, and embedded objects are shown as the literal characters they consist of. There is no preview pane and no link auto-detection — `file://`, `http://`, `ms-appinstaller://` and similar URIs are never resolved or executed.
- **No shell, no subprocess, no eval.** The source contains no calls to `subprocess`, `os.system`, `eval`, `exec`, `pickle`, or any other dynamic-code-execution primitive. Opening a file is literally `open(path, 'r', encoding='utf-8')`.
- **No network.** Zero outbound connections. No update check, no telemetry, no cloud sync. Your files never leave your machine.
- **Atomic saves.** Writes go to a sibling temp file, are `fsync`ed, then atomically renamed into place via `os.replace`. A crash, power loss, or full disk during save cannot leave you with a half-written file — either the old contents or the new contents are on disk, never a truncated hybrid.
- **Line-ending fidelity.** Paige detects whether a file uses `\r\n`, `\n`, or `\r` on open and writes the same style back out. Round-tripping an LF-only file on Windows does not silently convert it to CRLF.
- **Strict UTF-8.** Files are read as UTF-8. If a file isn't valid UTF-8, Paige refuses to guess — it surfaces a decode error and leaves the buffer untouched, rather than silently mis-decoding bytes (which can corrupt non-ASCII data on save).
- **Supply-chain hardened CI.** The build pipeline defaults to `contents: read`, uses `persist-credentials: false` on checkout so no git token sits on disk during the build, and pins third-party actions by commit SHA rather than mutable tag — the attack vector behind the March 2025 `tj-actions/changed-files` compromise.

## Features
- **Dark/Light Theme Toggle** — switch appearance on the fly without restarting.
- **Unsaved-Changes Guard** — prompts before close, reopen, or discard; cancelling the save dialog aborts the action instead of silently dropping your work.
- **Atomic Saves** — crash-safe writes via temp-file + rename, with full `fsync` before commit.
- **Line-Ending Preservation** — opens CRLF/LF/CR and writes the same style back out.
- **Large File Warning** — confirmation prompt before opening files over 50 MB.
- **Search** — inline find bar (`Ctrl+F`) and floating Find/Replace dialog (`Ctrl+H`), with case-insensitive wrap-around search.
- **Word Wrap Toggle** — off by default for log viewing; toggle via the checkbox in the menu bar.
- **Text Zoom** — `Ctrl+Scroll` or `Ctrl++`/`Ctrl+-` to resize dynamically.
- **Context Menu** — right-click for Cut, Copy, Paste, Select All.
- **Portable Windows Build** — single `.exe`, no installer, no registry writes, no admin rights.

## Installation

### For Users
Download the latest `Paige.exe` from the [Releases page](https://github.com/DQ-Labs/paige/releases). It's a portable executable — no installer, no admin rights, no registry entries. Drop it anywhere and double-click.

**Verifying the download.** GitHub records a SHA-256 digest for each release asset (shown on the Releases page under the asset name). You can confirm the file you downloaded matches it:
```powershell
Get-FileHash Paige.exe -Algorithm SHA256
```

> Windows SmartScreen may warn the first time you run Paige because the binary is not code-signed (signing certificates are not free for hobby projects). Every release is built from this repository by GitHub Actions; the [build workflow](.github/workflows/build.yml) is the entire build process, and the commit it ran on is linked from the release page.

### For Developers
If you'd like to run from source or contribute:
1. Clone the repository:
   ```bash
   git clone https://github.com/DQ-Labs/paige.git
   cd paige
   ```
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   source venv/bin/activate  # On Linux
   pip install -r requirements.txt
   ```
3. Run the application:
   ```bash
   python main.py
   ```

## Future Possibilities
- [ ] **Syntax Highlighting**: Support for `.py`, `.json`, `.yml`, and `.log` files.
- [ ] **JSON Formatting**: One-click "Prettify" for JSON strings.

## Release Notes

### v0.7 (2026-05-16)
**Security & integrity hardening.**

*Editor:*
- **Atomic saves.** Writes now go through a sibling temp file and `os.replace()` so a crash mid-save can no longer truncate the original file.
- **Save-cancellation respected.** Cancelling the Save As dialog when prompted on unsaved changes now aborts the close/reopen instead of silently discarding work.
- **Reopen guard.** Opening a new file now triggers the unsaved-changes prompt; previously it would wipe the buffer without asking.
- **Find/Replace marks modified.** Programmatic edits via Replace / Replace All now mark the document dirty, so the close prompt fires correctly afterward.
- **Line-ending preservation.** CRLF/LF/CR detected on open and preserved on save; no more silent LF→CRLF conversion on Windows round-trips.

*CI / supply chain:*
- **Pinned `softprops/action-gh-release` to a commit SHA** (was `@v1`, a mutable tag — the same attack vector as the March 2025 `tj-actions/changed-files` compromise). Also bumped to v3.
- **Least-privilege workflow.** Default `permissions: contents: read`; release split into its own job that opts in to `contents: write`, so the build steps never see a write-scoped token.
- **`persist-credentials: false`** on `actions/checkout` — no usable git credential sits in `.git/config` during the build.

### v0.6.1 (2026-02-23)
- **Patch**: Fixed application icon bundling in Windows executable.

### v0.6 (2026-02-23)
- **Unsaved Changes Guard**: App now tracks unsaved changes and prompts the user before closing or discarding work.
- **Theme Toggle**: New "Toggle Theme" menu button switches between Dark and Light modes at runtime.
- **Large File Warning**: Opening files > 50 MB now triggers a Yes/No confirmation dialog.
- **Dependency Pinning**: `customtkinter==5.2.2` and `pyinstaller==6.19.0` pinned in `requirements.txt` for reproducible builds.
- **Security Documentation**: README updated to explicitly document Paige's "Dumb Editor" security model and reference CVE-2026-20841.

### v0.5 (2026-02-12)
- **UI Improvements**: Added dynamic window title that displays the current filename.
- **Shortcuts**: Added `Ctrl+O` (Open), `Ctrl+S` (Save), and `Ctrl+Shift+S` (Save As).
- **Refactor**: Improved code maintainability with a centralized `update_title()` method and standardized state management.

### v0.4 (2026-02-11)
- **Context Menu**: Added a standard right-click context menu to the main text area.
- **Standard Actions**: Integrated Cut, Copy, Paste, and Select All commands.
- **System Clipboard**: Full integration with the system clipboard via standard event generation.

### v0.3 (2026-02-10)
- **Find & Replace**: Added a robust Find/Replace system accessible via the menu or `Ctrl+H`.
- **Floating Dialog**: New "stay-on-top" dialog window for easier searching.
- **Highlighting**: Matches are now highlighted in yellow for better visibility.
- **Advanced Features**: Includes "Find Next", "Replace" (single), "Replace All", wrap-around search, and auto-scrolling.

### v0.2 (2026-02-08)
- **Zoom / Text Size**: Added dynamic text scaling via UI controls and keyboard shortcuts (Ctrl+Scroll, Ctrl+/-, Ctrl+Plus).
- **Icon Fix**: Properly integrated custom application icon into the build and window frame.
- **Release Automation**: Fully automated CI/CD pipeline for Windows executables via GitHub Actions.

### v0.1
- Initial release with basic text editing, Regex search, and dark mode support.

## License
MIT License - See [LICENSE](LICENSE) for details.

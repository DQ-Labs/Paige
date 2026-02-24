# Paige

![Build Status](https://github.com/DQ-Labs/paige/actions/workflows/build.yml/badge.svg)

## The "Why"
Paige is a **Dumb Text Editor** — and that's the entire point.

Modern editors like Windows Notepad, VS Code, and Notepad++ have grown into complex document *renderers*. They interpret Markdown, resolve protocol handlers (`file://`, `ms-appinstaller://`), and spin up entire language server processes. Every one of those features is an attack surface.

Paige refuses to render *anything*. It reads bytes and displays them as text. That's it. No Markdown preview. No protocol resolution. No shell execution. No cloud sync. The RCE attack surface found in modern Notepad **does not exist here**, because the feature that enables it doesn't exist either.

Built by a sysadmin, for sysadmins — optimized for opening multi-gigabyte log files, editing configs over RDP, and not having to think about whether your editor is a malware vector.

## Security Design
- **No rendering engine.** Text is displayed verbatim. Markdown, HTML, and RTF are treated as plain strings.
- **No protocol handlers.** `file://`, `http://`, `ms-appinstaller://`, and similar URIs are never resolved or executed.
- **No shell integration.** Paige never calls `subprocess`, `os.system`, or equivalent. Opening a file means `open(path, 'r')`.
- **No telemetry.** Zero network calls. Your files never leave your machine.
- **UTF-8 by default.** Falls back to `latin-1` on decode failure, displays a warning instead of crashing or silently corrupting data.

## Features
- **Dark/Light Theme Toggle**: Switch appearance on the fly without restarting.
- **Unsaved Changes Guard**: Prompted before closing or overwriting unsaved work.
- **Large File Warning**: Alerts you before opening files > 50 MB that may cause lag.
- **Search**: Built-in find bar (Ctrl+F) and floating Find/Replace dialog (Ctrl+H).
- **Word Wrap Toggle**: Disabled by default for clean log viewing; toggle via checkbox.
- **Text Zoom**: Ctrl+Scroll, Ctrl++/- to resize text dynamically.
- **Context Menu**: Right-click for Cut, Copy, Paste, Select All.
- **Cross-Platform**: Developed on Windows & Linux; deployed as a portable Windows executable.

## Installation

### For Users
Download the latest pre-compiled `Paige.exe` from the [Releases](https://github.com/DQ-Labs/paige/releases) page. No installation required; it's a portable executable.

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

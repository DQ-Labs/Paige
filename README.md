# Paige

![Build Status](https://github.com/DQ-Labs/paige/actions/workflows/build.yml/badge.svg)

## The "Why"
A lightweight, secure text editor built in Python/CustomTkinter. Designed to replace Notepad (or Notepad++) without the unnecessary bloat or security risks of modern "electron-heavy" editors. It's built by a sysadmin, for sysadmins, focusing on speed and stability when opening large logs or configuration files.

## Features
- 🌙 **Dark Mode**: Forced by default for eye comfort (`customtkinter` dark theme).
- 📜 **Large File Support**: Optimized handling by disabling word wrap by default, preventing GUI lag on million-line log files.
- 🔍 **Search**: Built-in find functionality (Ctrl+F).
- 🖱️ **Context Menu**: Right-click support for Cut, Copy, Paste, and Select All.
- 💻 **Cross-Platform**: Developed on Windows & Linux; deployed as a native Windows executable.
- 🔒 **Security**: No external telemetry or cloud sync. Your data stays on your machine.

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

### v0.4 (2026-02-11)
- 🖱️ **Context Menu**: Added a standard right-click context menu to the main text area.
- ✂️ **Standard Actions**: Integrated Cut, Copy, Paste, and Select All commands.
- 📋 **System Clipboard**: Full integration with the system clipboard via standard event generation.

### v0.3 (2026-02-10)
- 🔍 **Find & Replace**: Added a robust Find/Replace system accessible via the menu or `Ctrl+H`.
- ✨ **Floating Dialog**: New "stay-on-top" dialog window for easier searching.
- 🟡 **Highlighting**: Matches are now highlighted in yellow for better visibility.
- 🔄 **Advanced Features**: Includes "Find Next", "Replace" (single), "Replace All", wrap-around search, and auto-scrolling.


### v0.2 (2026-02-08)
- ✨ **Zoom / Text Size**: Added dynamic text scaling via UI controls and keyboard shortcuts (Ctrl+Scroll, Ctrl+/-, Ctrl+Plus).
- 🎨 **Icon Fix**: Properly integrated custom application icon into the build and window frame.
- 🤖 **Release Automation**: Fully automated CI/CD pipeline for Windows executables via GitHub Actions.

### v0.1
- Initial release with basic text editing, Regex search, and dark mode support.

## License
MIT License - See [LICENSE](LICENSE) for details.

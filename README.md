# Paige

![Build Status](https://github.com/DQ-Labs/paige/actions/workflows/build.yml/badge.svg)

## The "Why"
A lightweight, secure text editor built in Python/CustomTkinter. Designed to replace Notepad (or Notepad++) without the unnecessary bloat or security risks of modern "electron-heavy" editors. It's built by a sysadmin, for sysadmins, focusing on speed and stability when opening large logs or configuration files.

## Features
- 🌙 **Dark Mode**: Forced by default for eye comfort (`customtkinter` dark theme).
- 📜 **Large File Support**: Optimized handling by disabling word wrap by default, preventing GUI lag on million-line log files.
- 🔍 **Search**: Built-in find functionality (Ctrl+F).
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

## Roadmap
- [ ] **Syntax Highlighting**: Planned support for `.py`, `.json`, `.yml`, and `.log` files.
- [ ] **JSON Formatting**: One-click "Prettify" for JSON strings.
- [ ] **Tabbed Interface**: Manage multiple files in one window.

## License
MIT License - See [LICENSE](LICENSE) for details.

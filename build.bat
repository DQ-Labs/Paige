@echo off
echo Building Paige...
pyinstaller --noconfirm --onefile --windowed --name "Paige" --icon="assets/icon.ico" --add-data "assets;assets" main.py
echo Build complete. Check the dist folder for Paige.exe.
pause

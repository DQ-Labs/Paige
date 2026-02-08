@echo off
echo Building Paige...
pyinstaller --noconfirm --onefile --windowed --name "Paige" main.py
echo Build complete. Check the dist folder for Paige.exe.
pause

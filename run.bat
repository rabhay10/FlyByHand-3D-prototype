@echo off
echo ==========================================
echo   Hand Gesture Drone Controller Setup
echo ==========================================
echo.
echo [1/2] Installing/Verifying dependencies...
echo   - Cleaning potential conflicting OpenCV installations...
pip uninstall -y opencv-python opencv-python-headless opencv-contrib-python
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Failed to install dependencies. Check your internet connection or python installation.
    pause
    exit /b
)

echo.
echo [2/2] Starting Drone Controller...
python main.py
pause

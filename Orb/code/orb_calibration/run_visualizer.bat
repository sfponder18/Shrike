@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting Orb Visualizer...
python orb_visualizer.py
pause

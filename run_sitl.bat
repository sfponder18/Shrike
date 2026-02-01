@echo off
REM SwarmDrones SITL Launcher (Real ArduPilot)
REM Starts 3 SITL instances: bird1 (plane) + chick1.1, chick1.2 (copters)
REM Requires Mission Planner SITL binaries - see instructions if missing

cd /d "%~dp0"

REM Kill any existing SITL processes
echo Killing any existing SITL processes...
taskkill /F /IM ArduCopter.exe >nul 2>&1
taskkill /F /IM ArduPlane.exe >nul 2>&1
taskkill /F /IM ArduRover.exe >nul 2>&1
timeout /t 2 /nobreak >nul

REM Start SITL with --wipe for clean params
python tools\start_sitl.py --wipe

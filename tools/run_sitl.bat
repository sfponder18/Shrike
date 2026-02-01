@echo off
REM SwarmDrones Multi-SITL Launcher
REM Runs 3 SITL instances: 1 Plane (bird) + 2 Copters (chicks)
REM
REM Prerequisites:
REM   1. Install WSL2 with Ubuntu, OR
REM   2. Install Cygwin with ArduPilot dependencies
REM
REM This script uses the Mission Planner SITL binaries located at:
REM   %LOCALAPPDATA%\Mission Planner\sitl\
REM

set SITL_DIR=%LOCALAPPDATA%\Mission Planner\sitl

echo ============================================
echo  SwarmDrones Multi-SITL Launcher
echo ============================================
echo.

REM Check if SITL binaries exist
if not exist "%SITL_DIR%\ArduPlane.exe" (
    echo ERROR: ArduPlane.exe not found!
    echo.
    echo Please start SITL once from Mission Planner to download the binaries:
    echo   Mission Planner ^> Simulation ^> Plane ^> Start SITL
    echo.
    echo Then close it and run this script again.
    pause
    exit /b 1
)

if not exist "%SITL_DIR%\ArduCopter.exe" (
    echo ERROR: ArduCopter.exe not found!
    echo.
    echo Please start SITL once from Mission Planner to download the binaries:
    echo   Mission Planner ^> Simulation ^> Multirotor ^> Start SITL
    echo.
    echo Then close it and run this script again.
    pause
    exit /b 1
)

echo Found SITL binaries at: %SITL_DIR%
echo.
echo Starting 3 SITL instances...
echo   Instance 0: ArduPlane  (Bird)   - TCP 5760/5762/5763
echo   Instance 1: ArduCopter (Chick1) - TCP 5770/5772/5773
echo   Instance 2: ArduCopter (Chick2) - TCP 5780/5782/5783
echo.

REM Create temp directories for each instance
mkdir "%TEMP%\sitl_bird" 2>nul
mkdir "%TEMP%\sitl_chick1" 2>nul
mkdir "%TEMP%\sitl_chick2" 2>nul

REM Start Bird (ArduPlane) - Instance 0
echo Starting Bird (ArduPlane)...
start "SITL - Bird (Plane)" cmd /k "cd /d %TEMP%\sitl_bird && %SITL_DIR%\ArduPlane.exe --model plane --defaults %SITL_DIR%\default_params\plane.parm -I0 --serial0 tcp:0:5760 --serial1 tcp:0:5762"

timeout /t 2 >nul

REM Start Chick1 (ArduCopter) - Instance 1
echo Starting Chick1 (ArduCopter)...
start "SITL - Chick1 (Copter)" cmd /k "cd /d %TEMP%\sitl_chick1 && %SITL_DIR%\ArduCopter.exe --model quad --defaults %SITL_DIR%\default_params\copter.parm -I1 --serial0 tcp:0:5770 --serial1 tcp:0:5772"

timeout /t 2 >nul

REM Start Chick2 (ArduCopter) - Instance 2
echo Starting Chick2 (ArduCopter)...
start "SITL - Chick2 (Copter)" cmd /k "cd /d %TEMP%\sitl_chick2 && %SITL_DIR%\ArduCopter.exe --model quad --defaults %SITL_DIR%\default_params\copter.parm -I2 --serial0 tcp:0:5780 --serial1 tcp:0:5782"

echo.
echo ============================================
echo  All SITL instances started!
echo ============================================
echo.
echo Connect Mission Planner to:
echo   Bird:   TCP 127.0.0.1:5760
echo   Chick1: TCP 127.0.0.1:5770
echo   Chick2: TCP 127.0.0.1:5780
echo.
echo Connect SwarmDrones GCS:
echo   Menu ^> Connect ^> SITL (ArduPilot)
echo   (Uses ports 5762, 5772, 5782)
echo.
echo Close the SITL windows to stop simulation.
echo.
pause

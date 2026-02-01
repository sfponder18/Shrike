@echo off
REM SwarmDrones Sandbox GCS Launcher (EW Panel Experimental)
cd /d "%~dp0.."
python -m Sandbox.gcs_sandbox.main
pause

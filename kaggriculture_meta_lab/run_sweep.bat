@echo off
REM ============================================================
REM  Parameter sweep: screen hundreds of configs, promote the
REM  best through the 500-game Wilson gate, then crown one via
REM  a Bradley-Terry round-robin. ~15 min on a 5950X.
REM    CONFIG = sweeps\v8_tuning.json   (edit / add your own)
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%CONFIG%"=="" set CONFIG=sweeps\v8_tuning.json
if "%WORKERS%"=="" set WORKERS=16

if not exist .venv (
  echo [setup] creating virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt

echo.
echo Running sweep %CONFIG% on %WORKERS% workers ...
python scripts\sweep.py --config %CONFIG% --workers %WORKERS%
if errorlevel 1 goto :err

echo.
echo ============================================================
echo  SWEEP DONE. Commit the results\sweep-*.md file (UTF-8).
echo ============================================================
pause
goto :eof

:err
echo.
echo  SWEEP ERRORED - see output above.
pause
exit /b 1

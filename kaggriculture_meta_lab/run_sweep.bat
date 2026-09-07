@echo off
REM ============================================================
REM  Budgeted current-agent sweep. The default projects about 1,250
REM  full games, not the old 18,000-game V8 torture run. The script
REM  refuses >3,000 games unless --allow-large is explicitly used.
REM    CONFIG = sweeps\v10_b21_opening.json
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%CONFIG%"=="" set CONFIG=sweeps\v10_b21_opening.json
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

@echo off
REM ============================================================
REM  Kaggriculture Meta-Lab - quick start for Windows
REM ============================================================
if not exist .venv (
  echo [setup] creating virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt

echo.
echo [1/3] unit tests
python -m pytest -q
if errorlevel 1 goto :err

echo.
echo [2/3] closed-loop tournament SMOKE (starter vs pass, 8 games)
python scripts\run_tournament.py --candidate starter --opponent pass=pass --games 8 --workers 8
if errorlevel 1 goto :err

echo.
echo [3/3] open-loop corpus smoke (bundled sample, 3 episodes)
python scripts\run_corpus.py --candidate starter --corpus corpus\sample --team __none__ --workers 8 --limit 3
if errorlevel 1 goto :err

echo.
echo ALL SMOKE CHECKS PASSED. See reports\ for JSON/CSV.
goto :eof

:err
echo.
echo SMOKE FAILED - see output above.
exit /b 1

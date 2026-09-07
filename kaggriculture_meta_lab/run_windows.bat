@echo off
REM ============================================================
REM  Kaggriculture Meta-Lab - Windows quick start
REM  GAMES = closed-loop seeds (x2 seats). Default 20 -> 40 games.
REM  Set GAMES=100 and WORKERS=16 for a real overnight validation.
REM
REM  IMPORTANT: this runs the REAL validation (V8 vs V7 + elite
REM  corpus), NOT the old starter-vs-pass smoke. If your output
REM  says "SMOKE", you have an old copy - git pull / redownload.
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%GAMES%"=="" set GAMES=20
if "%WORKERS%"=="" set WORKERS=8

if not exist .venv (
  echo [setup] creating virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -U pip
pip install -r requirements.txt

echo.
echo [1/2] unit tests
python -m pytest -q
if errorlevel 1 goto :err

echo.
echo [2/2] FULL validation: V8 vs V7 (closed loop + elite corpus)
echo       GAMES=%GAMES%  WORKERS=%WORKERS%
python scripts\validate.py --games %GAMES% --workers %WORKERS%
if errorlevel 2 goto :gatefail
if errorlevel 1 goto :err

echo.
echo ============================================================
echo  VALIDATION PASSED. Commit the new results\validate-*.md
echo  file (UTF-8) and push it so the team sees the numbers.
echo ============================================================
echo.
pause
goto :eof

:gatefail
echo.
echo  GATE FAILED - the candidate did not beat the baseline with
echo  statistical confidence. See results\validate-*.md for detail.
pause
exit /b 2

:err
echo.
echo  VALIDATION ERRORED - see output above.
pause
exit /b 1

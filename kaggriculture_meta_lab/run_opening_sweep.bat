@echo off
REM ============================================================
REM  OPENING sweep: vary the opening wheat buy/sell of the
REM  champion tape (B21/S16) and score each closed-loop vs the
REM  champion. This is the strongest lever found so far.
REM    GAMES  = seeds per variant (x2 seats). Default 25=50 games.
REM    BUYS   = comma list of buy amounts to try
REM    RESERVE= comma list of reserves (sell = buy - reserve)
REM  Example: set BUYS=19,21,23 & set RESERVE=3,5
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%GAMES%"=="" set GAMES=25
if "%WORKERS%"=="" set WORKERS=16
if "%BUYS%"=="" set BUYS=17,19,21,23,25
if "%RESERVE%"=="" set RESERVE=3,5

if not exist .venv (
  echo [setup] creating virtual environment...
  py -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install -U pip >nul
pip install -q -r requirements.txt

echo.
echo Opening sweep: GAMES=%GAMES% (x2 seats) BUYS=%BUYS% RESERVE=%RESERVE%
python scripts\opening_sweep.py --games %GAMES% --workers %WORKERS% --buys %BUYS% --reserve %RESERVE%
if errorlevel 1 goto :err

echo.
echo ============================================================
echo  DONE. Commit results\opening-sweep-*.md (UTF-8).
echo ============================================================
pause
goto :eof

:err
echo.
echo  SWEEP ERRORED - see output above.
pause
exit /b 1

@echo off
REM ============================================================
REM  Opening sweep (LEGACY single-purpose): vary the opening wheat
REM  buy/sell of the champion tape and score closed-loop vs champion.
REM  Prefer the general funnel - it does the same via constants:
REM    run_sweep.bat   (CONFIG=sweeps\v10_b21_opening_direct.json)
REM  WARNING: a mirror win-rate vs the champion at ~$0 margin is a
REM  near-tie tie-break artefact - always cross-check TOP49 / controls.
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

REM ---- robust venv setup: works even when the `py` launcher is absent
REM (Microsoft Store Python). Falls back to `python` on PATH. ----
set PYEXE=
where py >nul 2>&1 && set PYEXE=py
if "%PYEXE%"=="" where python >nul 2>&1 && set PYEXE=python
if "%PYEXE%"=="" (
  echo [setup] ERROR: no Python found. Install Python 3.10+ and put it on PATH.
  pause & exit /b 1
)

if not exist .venv (
  echo [setup] creating virtual environment with %PYEXE% ...
  %PYEXE% -m venv .venv
  if errorlevel 1 (
    echo [setup] venv creation failed. On Store Python, run: python -m pip install --user virtualenv
    pause & exit /b 1
  )
)
call .venv\Scripts\activate.bat
python -m pip install -U pip -q
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

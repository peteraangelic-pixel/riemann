@echo off
REM ============================================================
REM  Parameter sweep: screen configs, promote the best through
REM  the Wilson gate, then crown one in a finals round-robin.
REM
REM    CONFIG = sweeps\*.json to run.
REM      default sweeps\v10_b21_rating_finalists.json  (~3000 games,
REM      the 3 near-tie finalists vs champion - the run requested).
REM      sweeps\v10_b21_opening_direct.json = 23-variant grid (~3000).
REM      sweeps\v10_b21_opening.json        = small 15-variant grid.
REM
REM    WORKERS = parallel games (5950X -> 16-24).
REM
REM  Budget note: sweeps over 1200 games normally need --allow-large.
REM  ALLOW_LARGE=1 is the default here so the funnel runs end to end;
REM  set ALLOW_LARGE=0 to keep the refusal guard, or run scripts\sweep.py
REM  directly for a small smoke test (e.g. --screen-games 4 --promote-games 4).
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%CONFIG%"=="" set CONFIG=sweeps\v10_b21_rating_finalists.json
if "%WORKERS%"=="" set WORKERS=16
if "%ALLOW_LARGE%"=="" set ALLOW_LARGE=1

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

set EXTRA=
if "%ALLOW_LARGE%"=="1" set EXTRA=--allow-large

echo.
echo Running sweep %CONFIG% on %WORKERS% workers (ALLOW_LARGE=%ALLOW_LARGE%) ...
python scripts\sweep.py --config %CONFIG% --workers %WORKERS% %EXTRA%
if errorlevel 1 goto :err

echo.
echo ============================================================
echo  SWEEP DONE. Commit results\sweep-*.md / .json (UTF-8).
echo ============================================================
pause
goto :eof

:err
echo.
echo  SWEEP ERRORED - see output above.
echo  If it refused on game budget, re-run with ALLOW_LARGE=1 or pass
echo  --allow-large / a smaller config.
pause
exit /b 1

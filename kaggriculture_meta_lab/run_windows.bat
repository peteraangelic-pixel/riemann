@echo off
REM ============================================================
REM  Kaggriculture Meta-Lab - Windows quick start / health check
REM
REM  This validates the HARNESS and the current champion tape
REM  (B21/S16) against itself and the frozen V7/V8 controls.
REM  GAMES = closed-loop seeds per control (x2 seats). Default
REM  50 -> 100 games per control (~2-3 min on a 5950X).
REM
REM  Real research runs elsewhere:
REM    run_opening_sweep.bat   - search wheat buy/sell openings
REM    run_sweep.bat           - general parameter funnel (sweeps\*.json)
REM    scripts\validate_current.py - champion vs all 3 controls
REM
REM  To validate a SPECIFIC candidate, set CANDIDATE:
REM    set CANDIDATE=agents\current\agent_v9_b21_s16.py
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%GAMES%"=="" set GAMES=50
if "%WORKERS%"=="" set WORKERS=16
if "%CANDIDATE%"=="" set CANDIDATE=agents\current\agent_v9_b21_s16.py

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
echo [1/2] unit tests
REM Scope pytest to THIS folder's tests only (a nested "LAB centralny"
REM copy of the lab would otherwise cause same-named test collisions).
if exist tests\__pycache__ rmdir /s /q tests\__pycache__
if exist kaggriculture_lab\__pycache__ rmdir /s /q kaggriculture_lab\__pycache__
python -m pytest tests -q --import-mode=importlib
if errorlevel 1 goto :err

echo.
echo [2/2] validate champion vs all frozen controls (V7/V8)
echo       CANDIDATE=%CANDIDATE%  GAMES=%GAMES%  WORKERS=%WORKERS%
python scripts\validate_current.py --candidate "%CANDIDATE%" --games %GAMES% --workers %WORKERS%
if errorlevel 2 goto :gatefail
if errorlevel 1 goto :err

echo.
echo ============================================================
echo  HARNESS OK - champion clears all controls. Commit any new
echo  results\validate-current-*.json and push it.
echo ============================================================
pause
goto :eof

:gatefail
echo.
echo  GATE FAILED - candidate did not beat a control with Wilson
echo  confidence. See results\validate-current-*.json for detail.
pause
exit /b 2

:err
echo.
echo  VALIDATION ERRORED - see output above.
pause
exit /b 1

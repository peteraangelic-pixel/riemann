@echo off
REM ============================================================
REM  STRUCTURAL sweep: mutate the champion tape's BODY (workers
REM  via HIRE, fertilizer scale, late-buy cutoff, endgame
REM  liquidation) - not the saturated wheat opening - and run
REM  the funnel. Uses the Rust kg_sim binary automatically if it
REM  is built (~80x), else falls back to the Python engine.
REM
REM    BUILD=1 -> first run `cargo build --release` in rust_port
REM               (needs Rust 1.85+), then sweep. Omit to just run.
REM    CONFIG  -> defaults to sweeps\v11_struct.json
REM
REM  Generate a fresh grid yourself, e.g.:
REM    python scripts\structural_gen.py --emit-sweep sweeps\v12.json ^
REM      --grid "{\"hire_scale\":[0.85,1.0,1.15],\"fert_scale\":[1,2,3]}"
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%CONFIG%"=="" set CONFIG=sweeps\v11_struct.json
if "%WORKERS%"=="" set WORKERS=16

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
)
call .venv\Scripts\activate.bat
python -m pip install -U pip -q
pip install -q -r requirements.txt

if "%BUILD%"=="1" (
  echo.
  echo [build] compiling Rust simulator ^(needs Rust 1.85+^)...
  pushd rust_port
  cargo build --release --locked
  if errorlevel 1 ( popd & echo [build] cargo failed - is Rust installed? & pause & exit /b 1 )
  popd
)

echo.
echo Running structural sweep %CONFIG% on %WORKERS% workers ...
python scripts\sweep.py --config %CONFIG% --workers %WORKERS% --allow-large
if errorlevel 1 goto :err

echo.
echo ============================================================
echo  SWEEP DONE. Commit results\sweep-*.md / .json (UTF-8).
echo  Remember: mirror win-rate at ~$0 margin is a near-tie -
echo  gate winners on margin vs varied controls + TOP49.
echo ============================================================
pause
goto :eof

:err
echo.
echo  SWEEP ERRORED - see output above.
pause
exit /b 1

@echo off
REM ============================================================
REM  Kaggriculture LAB v12: timing + endgame structural sweep
REM
REM  Usage from this folder:
REM    BUILD=1 run_v12_timing.bat   (first run, compiles Rust)
REM    run_v12_timing.bat            (later runs)
REM
REM  Optional environment variables:
REM    BUILD=1       build Rust before the sweep
REM    WORKERS=16    Rayon/Python workers
REM    BACKEND=auto  auto, rust, or python
REM
REM  After completion, send only results\sweep-*.json and *.md.
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%WORKERS%"=="" set WORKERS=16
if "%BACKEND%"=="" set BACKEND=auto
set CONFIG=sweeps\v12_timing_endgame.json

set PYEXE=
where py >nul 2>&1 && set PYEXE=py
if "%PYEXE%"=="" where python >nul 2>&1 && set PYEXE=python
if "%PYEXE%"=="" (
  echo [setup] ERROR: Python 3.10+ not found on PATH.
  pause & exit /b 1
)

if not exist .venv (
  echo [setup] creating virtual environment ...
  %PYEXE% -m venv .venv
  if errorlevel 1 goto :err
)
call .venv\Scripts\activate.bat
python -m pip install -U pip -q
pip install -q -r requirements.txt
if errorlevel 1 goto :err

if "%BUILD%"=="1" (
  echo.
  echo [build] compiling Rust simulator ...
  pushd rust_port
  cargo build --release --locked
  if errorlevel 1 ( popd & echo [build] cargo failed - install Rust 1.85+ & goto :err )
  popd
)

echo.
echo [run] v12 timing/endgame: %WORKERS% workers, backend=%BACKEND%
python scripts\sweep.py --config %CONFIG% --workers %WORKERS% --backend %BACKEND% --allow-large
if errorlevel 1 goto :err

echo.
echo ============================================================
echo V12 DONE. Send files from results\ matching sweep-*.json and sweep-*.md.
echo Do not send generated agents/sweeps or the .venv directory.
echo ============================================================
pause
goto :eof

:err
echo.
echo V12 FAILED. See the error above. No submission was made.
pause
exit /b 1

@echo off
REM ============================================================
REM  Subin reactive market-overlay evolution
REM
REM  One-command LAB runner:
REM    set BUILD=1
REM    run_reactive_overlay_evolution.bat
REM
REM  Required input (one of):
REM    ..\TOP30.7z
REM    TOP30.7z
REM    corpus\top30_2026-09-08\TOP30\
REM
REM  Optional:
REM    WORKERS=16   Rust workers
REM    POP=1000     Generation-0 profiles
REM    MAXRANK=10   initial curriculum rank (default 10)
REM ============================================================
chcp 65001 >nul
set PYTHONUTF8=1
if "%WORKERS%"=="" set WORKERS=16
if "%POP%"=="" set POP=1000
if "%MAXRANK%"=="" set MAXRANK=10

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
pip install -q -r requirements.txt py7zr
if errorlevel 1 goto :err

if "%BUILD%"=="1" (
  echo [build] compiling Rust simulator ...
  pushd rust_port
  cargo build --release --locked
  if errorlevel 1 ( popd & echo [build] cargo failed - install Rust 1.85+ & goto :err )
  popd
)

set CORPUS=
if exist corpus\top30_2026-09-08\TOP30\manifest.json set CORPUS=corpus\top30_2026-09-08\TOP30
if exist TOP30\manifest.json set CORPUS=TOP30
if "%CORPUS%"=="" if exist TOP30.7z (
  echo [data] extracting TOP30.7z ...
  python -c "import py7zr; py7zr.SevenZipFile('TOP30.7z').extractall('work\\top30')"
  if errorlevel 1 goto :err
  set CORPUS=work\top30\TOP30
)
if "%CORPUS%"=="" if exist ..\TOP30.7z (
  echo [data] extracting ..\TOP30.7z ...
  python -c "import py7zr; py7zr.SevenZipFile('..\TOP30.7z').extractall('work\\top30')"
  if errorlevel 1 goto :err
  set CORPUS=work\top30\TOP30
)
if "%CORPUS%"=="" (
  echo [data] ERROR: TOP30.7z or extracted TOP30 corpus not found.
  echo         Put TOP30.7z in this folder or in the repository root.
  pause & exit /b 1
)

if not exist results mkdir results
if not exist work mkdir work
set BIN=rust_port\target\release\kg_sim.exe

 echo [G0] sampling %POP% bounded market profiles on TOP%MAXRANK% ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --population %POP% --generation g0 --max-rank %MAXRANK% --seed 20260909 --workers %WORKERS% --output results\top%MAXRANK%-market-overlay-g0.json
if errorlevel 1 goto :err

 echo [G1] refining retained profiles ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --population 500 --generation g1 --max-rank %MAXRANK% --seed 20260910 --workers %WORKERS% --output results\top%MAXRANK%-market-overlay-g1.json
if errorlevel 1 goto :err

 echo [G2] refined search ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --population 500 --generation g2 --max-rank %MAXRANK% --seed 20260911 --workers %WORKERS% --output results\top%MAXRANK%-market-overlay-g2.json
if errorlevel 1 goto :err

 echo [VALIDATION] retained G2 profiles on full TOP30 ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --profiles-from results\top%MAXRANK%-market-overlay-g2.json --max-rank 30 --seed 20260909 --workers %WORKERS% --output results\top30-market-overlay-validation.json
if errorlevel 1 goto :err

 echo.
echo ============================================================
echo EVOLUTION DONE. Send these files from results\:
echo   top%MAXRANK%-market-overlay-g0.json
echo   top%MAXRANK%-market-overlay-g1.json
echo   top%MAXRANK%-market-overlay-g2.json
echo   top30-market-overlay-validation.json
echo Do not send work\, .venv\, or extracted TOP30 raw data.
echo ============================================================
pause
goto :eof

:err
echo.
echo EVOLUTION FAILED. No submission was made. See the error above.
pause
exit /b 1

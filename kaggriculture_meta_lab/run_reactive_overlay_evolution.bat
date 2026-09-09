@echo off
REM ============================================================
REM  Subin reactive market-overlay evolution
REM
REM  One-command LAB runner:
REM    set BUILD=1
REM    run_reactive_overlay_evolution.bat
REM
REM  Required input (one of):
REM    ..\TOP15.7z
REM    TOP15.7z
REM    corpus\top15_2026-09-09\TOP15\
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
REM Curriculum is fixed to the current TOP15: TOP5 -> TOP10 -> TOP15.


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

if "%BUILD%"=="1" if not exist rust_port\target\release\kg_sim.exe set NEED_BUILD=1
if not exist rust_port\target\release\kg_sim.exe set NEED_BUILD=1
if "%NEED_BUILD%"=="1" (
  echo [build] compiling Rust simulator ...
  where cargo >nul 2>&1
  if errorlevel 1 ( echo [build] ERROR: cargo not found. Install Rust 1.85+ or use an existing kg_sim.exe. & goto :err )
  pushd rust_port
  set CARGO_CMD=cargo
  rustup toolchain list 2>nul | findstr /C:"stable-x86_64-pc-windows-msvc" >nul
  if not errorlevel 1 set CARGO_CMD=cargo +stable-x86_64-pc-windows-msvc
  echo [build] using %CARGO_CMD%
  %CARGO_CMD% build --release --locked
  if errorlevel 1 (
    popd
    echo [build] Rust build failed.
    echo [build] On Windows prefer the MSVC toolchain and Visual Studio C++ Build Tools:
    echo [build]   rustup toolchain install stable-x86_64-pc-windows-msvc
    echo [build]   rustup default stable-x86_64-pc-windows-msvc
    echo [build] Then reopen PowerShell and rerun this file.
    goto :err
  )
  popd
)

set CORPUS=
if exist corpus\top15_2026-09-09\TOP15\manifest.json set CORPUS=corpus\top15_2026-09-09\TOP15
if exist TOP15\manifest.json set CORPUS=TOP15
if "%CORPUS%"=="" if exist TOP15.7z (
  echo [data] extracting TOP15.7z ...
  python -c "import py7zr; py7zr.SevenZipFile('TOP15.7z').extractall('work\\top15')"
  if errorlevel 1 goto :err
  set CORPUS=work\top15\TOP15
)
if "%CORPUS%"=="" if exist ..\TOP15.7z (
  echo [data] extracting ..\TOP15.7z ...
  python -c "import py7zr; py7zr.SevenZipFile('..\TOP15.7z').extractall('work\\top15')"
  if errorlevel 1 goto :err
  set CORPUS=work\top15\TOP15
)
if "%CORPUS%"=="" (
  echo [data] ERROR: TOP15.7z or extracted TOP15 corpus not found.
  echo         Put TOP15.7z in this folder or in the repository root.
  pause & exit /b 1
)

if not exist results mkdir results
if not exist work mkdir work
set BIN=rust_port\target\release\kg_sim.exe

 echo [G0] sampling %POP% bounded market profiles on TOP5 ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --population %POP% --generation g0 --max-rank 5 --seed 20260909 --workers %WORKERS% --output results\top5-market-overlay-g0.json
if errorlevel 1 goto :err

 echo [G1] refining profiles on TOP10 ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --population 500 --generation g1 --max-rank 10 --seed 20260910 --workers %WORKERS% --output results\top10-market-overlay-g1.json
if errorlevel 1 goto :err

 echo [G2] refined search on TOP15 ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --population 500 --generation g2 --max-rank 15 --seed 20260911 --workers %WORKERS% --output results\top15-market-overlay-g2.json
if errorlevel 1 goto :err

 echo [VALIDATION] retained G2 profiles on full TOP15 ...
python scripts\screen_market_overlays.py --corpus "%CORPUS%" --candidate agents\variants\agent_v10_subin_106845775.py --binary "%BIN%" --profiles-from results\top15-market-overlay-g2.json --max-rank 15 --seed 20260909 --workers %WORKERS% --output results\top15-market-overlay-validation.json
if errorlevel 1 goto :err

 echo.
echo ============================================================
echo EVOLUTION DONE. Send these files from results\:
echo   top5-market-overlay-g0.json
echo   top10-market-overlay-g1.json
echo   top15-market-overlay-g2.json
echo   top15-market-overlay-validation.json
echo Do not send work\, .venv\, or extracted TOP15 raw data.
echo ============================================================
pause
goto :eof

:err
echo.
echo EVOLUTION FAILED. No submission was made. See the error above.
pause
exit /b 1

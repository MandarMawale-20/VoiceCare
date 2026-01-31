@echo off
REM ============================================
REM VoiceCare SMALL MODEL - Safe Build Script
REM ============================================
REM SAFE BUILD - Does NOT delete any source code
REM Only builds Small Model version
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Building VoiceCare.exe (Small Model)
echo ========================================
echo.

REM Step 1: Verify virtual environment
echo [1/4] Verifying virtual environment...
if exist ".venv\Scripts\activate.bat" (
    echo   ✓ Virtual environment found
) else (
    echo   ✗ Virtual environment NOT found
    echo   Run: setup.bat
    pause
    exit /b 1
)

REM Step 2: Verify Small Model folder
echo.
echo [2/4] Verifying Small Model folder...
if exist "Small Model\voicecare_frontend.py" (
    echo   ✓ Small Model folder is SAFE
) else (
    echo   ✗ Small Model folder NOT found!
    pause
    exit /b 1
)

REM Step 3: Verify Vosk model
echo.
echo [3/4] Verifying Vosk model...
if exist "vosk\vosk-model-small-en-us-0.15" (
    echo   ✓ Vosk model found
) else (
    echo   ✗ Vosk model NOT found!
    pause
    exit /b 1
)

REM Step 4: Clean only old build artifacts (SAFE)
echo.
echo [4/4] Cleaning old builds...
if exist "build" (
    rmdir /s /q "build" 2>nul
    echo   ✓ build/ removed
)
echo   ✓ Safe cleanup complete (dist/ preserved)
echo   ✓ Google EXE is PROTECTED: dist\VoiceCareGoogle\

REM Step 5: Build with PyInstaller
echo.
echo Building VoiceCare.exe...
echo This will take 10-15 minutes...
echo.

call .venv\Scripts\activate.bat
.venv\Scripts\pyinstaller.exe --noconfirm voicecare.spec

if !errorlevel! neq 0 (
    echo.
    echo ✗ Build FAILED
    pause
    exit /b 1
)

REM Step 6: Verify results
echo.
echo ========================================
if exist "dist\VoiceCare\VoiceCare.exe" (
    echo ✓ Build SUCCESSFUL!
    echo.
    echo Your executable:
    echo   dist\VoiceCare\VoiceCare.exe
    echo.
    echo ✓ All source folders are SAFE:
    if exist "Small Model" echo   ✓ Small Model\
    if exist "Bigger model" echo   ✓ Bigger model\
    if exist "GoogleSpeech recognition" echo   ✓ GoogleSpeech recognition\
    if exist "vosk" echo   ✓ vosk\
    echo.
    echo To run:
    echo   cd dist\VoiceCare
    echo   VoiceCare.exe
) else (
    echo ✗ Build FAILED - No executable found
)

echo ========================================
pause

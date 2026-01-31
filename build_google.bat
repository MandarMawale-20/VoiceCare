@echo off
REM ============================================
REM VoiceCare GOOGLE SPEECH - Safe Build Script
REM ============================================
REM SAFE BUILD - Does NOT delete any source code
REM Only builds Google Speech version
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo Building VoiceCareGoogle.exe (Google Speech)
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

REM Step 2: Verify Google Speech folder
echo.
echo [2/4] Verifying GoogleSpeech recognition folder...
if exist "GoogleSpeech recognition\voiceCare_frontend.py" (
    echo   ✓ GoogleSpeech recognition folder is SAFE
) else (
    echo   ✗ GoogleSpeech recognition folder NOT found!
    pause
    exit /b 1
)

REM Step 3: Clean only old build artifacts (SAFE)
echo.
echo [3/4] Cleaning old builds...
if exist "build" (
    rmdir /s /q "build" 2>nul
    echo   ✓ build/ removed
)
echo   ✓ Safe cleanup complete (dist/ preserved)
echo   ✓ Small Model EXE is PROTECTED: dist\VoiceCare\
echo.

REM Step 4: Build with PyInstaller
echo [4/4] Building VoiceCareGoogle.exe...
echo This will take 10-15 minutes...
echo.

call .venv\Scripts\activate.bat
.venv\Scripts\pyinstaller.exe --noconfirm voicecare_google.spec

if !errorlevel! neq 0 (
    echo.
    echo ✗ Build FAILED
    pause
    exit /b 1
)

REM Step 5: Verify results
echo.
echo ========================================
if exist "dist\VoiceCareGoogle\VoiceCareGoogle.exe" (
    echo ✓ Build SUCCESSFUL!
    echo.
    echo Your executable:
    echo   dist\VoiceCareGoogle\VoiceCareGoogle.exe
    echo.
    echo ✓ All source folders are SAFE:
    if exist "Small Model" echo   ✓ Small Model\
    if exist "Bigger model" echo   ✓ Bigger model\
    if exist "GoogleSpeech recognition" echo   ✓ GoogleSpeech recognition\
    if exist "vosk" echo   ✓ vosk\
    echo.
    echo ✓ Small Model EXE still exists:
    if exist "dist\VoiceCare\VoiceCare.exe" echo   ✓ dist\VoiceCare\VoiceCare.exe
    echo.
    echo To run:
    echo   cd dist\VoiceCareGoogle
    echo   VoiceCareGoogle.exe
) else (
    echo ✗ Build FAILED - No executable found
)

echo ========================================
pause

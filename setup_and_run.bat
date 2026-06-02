@echo off
title Phoenix Subs Muxer Fixer - Bootstrapper (DEBUG MODE)
color 0A
set LOCAL_DIR=%~dp0
cd /d "%LOCAL_DIR%"

echo ====================================================================
echo        PHOENIX SUBS MUXER FIXER - COMPONENT BOOTSTRAPPER
echo ====================================================================
echo.

:: 1. إنشاء مجلد الأدوات المحلي
if not exist "tools" (
    echo [+] [tools] Creating isolated local tools directory...
    mkdir "tools"
)

:: 2. التحقق من البايثون
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [X] Error: Python is not installed or not added to your system PATH!
    pause
    exit /b
)

:: 3. بناء بيئة برمجية افتراضية
if not exist ".venv" (
    echo [+] [.venv] Creating isolated local Virtual Environment...
    python -m venv .venv
)

:: 4. تحميل المكتبات (بدون كتم الأخطاء عشان نشوف المشكلة فين)
echo [+] Activating local environment and downloading dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r requirements.txt

:: 5. فحص ملفات المكس
if not exist "tools\ffmpeg.exe" set TOOLS_MISSING=1
if not exist "tools\ffprobe.exe" set TOOLS_MISSING=1

if defined TOOLS_MISSING (
    echo.
    echo [!] WARNING: 'ffmpeg.exe' or 'ffprobe.exe' is missing from the local 'tools' folder!
    echo ====================================================================
    echo.
)

:: 6. تشغيل البرنامج (مباشرة في نفس النافذة عشان نمسك أي خطأ في البايثون)
echo [+] Launching Phoenix Subs Muxer Fixer...
.venv\Scripts\python.exe main.py

echo.
echo [!] Script execution finished or crashed. Check for errors above.
pause
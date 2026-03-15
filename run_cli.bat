@echo off
REM System Manager CLI - Windows Batch Runner
setlocal enabledelayedexpansion

:menu
cls
echo.
echo ================================================
echo     SYSTEM MANAGER CLI - Main Menu
echo ================================================
echo.
echo 1. Check System Health
echo 2. Clean Temporary Files
echo 3. Backup Folder
echo 4. Generate System Report
echo 5. Setup Configuration
echo 6. Exit
echo.
set /p choice="Select an option (1-6): "

if "%choice%"=="1" goto health
if "%choice%"=="2" goto clean
if "%choice%"=="3" goto backup
if "%choice%"=="4" goto report
if "%choice%"=="5" goto setup
if "%choice%"=="6" goto exit
echo Invalid choice. Please try again.
timeout /t 2
goto menu

:health
cls
echo Checking system health...
python main.py check-health
echo.
pause
goto menu

:clean
cls
echo.
set /p folder="Enter folder path to clean: "
if not exist "!folder!" (
    echo Error: Folder not found
    pause
    goto menu
)
python main.py clean-temp "!folder!"
echo.
pause
goto menu

:backup
cls
echo.
set /p source="Enter folder path to backup: "
if not exist "!source!" (
    echo Error: Folder not found
    pause
    goto menu
)
echo Do you want to compress the backup? (y/n)
set /p compress="Enter choice: "
if /i "!compress!"=="y" (
    python main.py backup-folder "!source!" --compress
) else (
    python main.py backup-folder "!source!"
)
echo.
pause
goto menu

:report
cls
echo.
set /p logpath="Enter log file or folder path: "
if not exist "!logpath!" (
    echo Error: Path not found
    pause
    goto menu
)
python main.py generate-report "!logpath!" --export
echo.
pause
goto menu

:setup
cls
echo Running setup...
python main.py setup
echo.
pause
goto menu

:exit
echo Goodbye!
exit /b 0

@echo off
chcp 65001 >nul
title XHS Publisher - Browser Install Helper

echo ========================================
echo XHS Publisher - Browser Install Helper
echo ========================================
echo.

:: Check if running as administrator (some systems may require)
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [OK] Running with administrator privileges
) else (
    echo [Warning] Recommend running as administrator
    echo    Right-click this file and select "Run as administrator"
    echo.
    choice /C YN /M "Continue? (Y/N)"
    if errorlevel 2 exit
)

:: Run PowerShell script
echo.
echo [Starting] Launching installer...
powershell -ExecutionPolicy Bypass -File "%~dp0install_firefox.ps1"

:: Check PowerShell script exit code
if %errorLevel% == 0 (
    echo.
    echo [OK] Installation completed!
) else (
    echo.
    echo [Error] Installation failed, please check the error messages above
)

echo.
pause
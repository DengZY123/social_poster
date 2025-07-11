@echo off
chcp 65001 >nul
title 小红书发布工具 - 浏览器安装助手

echo ========================================
echo 小红书发布工具 - 浏览器安装助手
echo ========================================
echo.

:: 检查是否以管理员身份运行（某些系统可能需要）
net session >nul 2>&1
if %errorLevel% == 0 (
    echo ✅ 正在以管理员权限运行
) else (
    echo ⚠️  建议以管理员身份运行此脚本
    echo    右键点击此文件，选择"以管理员身份运行"
    echo.
    choice /C YN /M "是否继续？(Y/N)"
    if errorlevel 2 exit
)

:: 运行PowerShell脚本
echo.
echo 🚀 启动安装程序...
powershell -ExecutionPolicy Bypass -File "%~dp0install_firefox.ps1"

:: 检查PowerShell脚本的退出码
if %errorLevel% == 0 (
    echo.
    echo ✅ 安装程序执行完成！
) else (
    echo.
    echo ❌ 安装过程中出现错误，请查看上面的错误信息
)

echo.
pause
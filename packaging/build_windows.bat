@echo off
chcp 65001 > nul
echo 🚀 小红书发布工具 - Windows构建脚本
echo ================================================

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python未安装或未添加到PATH
    echo 请安装Python 3.8或更高版本
    pause
    exit /b 1
)

:: 显示Python版本
echo ✅ Python版本:
python --version

:: 检查是否在正确的目录
if not exist "xhs_publisher_windows.spec" (
    echo ❌ 请在packaging目录中运行此脚本
    pause
    exit /b 1
)

:: 检查虚拟环境
if defined VIRTUAL_ENV (
    echo ✅ 虚拟环境: %VIRTUAL_ENV%
) else (
    echo ⚠️ 未检测到虚拟环境，建议使用虚拟环境
)

:: 安装依赖（如果需要）
echo.
echo 📦 检查依赖包...
pip list | findstr PyInstaller >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ PyInstaller未安装，正在安装...
    pip install PyInstaller
)

:: 运行构建脚本
echo.
echo 🔨 开始构建...
python build_windows.py

if %errorlevel% eq 0 (
    echo.
    echo 🎉 构建完成！
    echo 可执行文件位置: dist\XhsPublisher.exe
    echo.
    echo 按任意键打开构建目录...
    pause >nul
    explorer dist
) else (
    echo.
    echo ❌ 构建失败，请检查错误信息
    pause
)

echo.
echo 按任意键退出...
pause >nul 
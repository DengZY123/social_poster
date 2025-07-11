#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试版本构建脚本
专门用于构建小红书发布工具的调试版本
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 项目配置
PROJECT_NAME = "XhsPublisherDebug"
PROJECT_VERSION = "1.0.0-debug"
SPEC_FILE = "xhs_publisher_debug.spec"

def print_step(message, level="INFO"):
    """输出构建步骤信息"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = {
        "INFO": "📋",
        "SUCCESS": "✅", 
        "WARNING": "⚠️",
        "ERROR": "❌",
        "DEBUG": "🔍"
    }.get(level, "📋")
    
    print(f"[{timestamp}] {prefix} {message}")

def print_section(title):
    """输出分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_environment():
    """检查构建环境"""
    print_section("构建环境检查")
    
    # 检查Python版本
    python_version = sys.version_info
    print_step(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print_step("需要Python 3.8或更高版本", "ERROR")
        return False
    
    # 检查必要的包
    required_packages = [
        ("PyInstaller", "PyInstaller"), 
        ("PyQt6", "PyQt6"), 
        ("playwright", "playwright"), 
        ("pandas", "pandas"),
        ("openpyxl", "openpyxl"), 
        ("loguru", "loguru"), 
        ("pydantic", "pydantic"), 
        ("ujson", "ujson")
    ]
    
    print_step("检查Python包依赖...")
    missing_packages = []
    for display_name, import_name in required_packages:
        try:
            module = __import__(import_name)
            version = getattr(module, '__version__', '未知版本')
            print_step(f"{display_name} - 版本: {version}", "SUCCESS")
        except ImportError:
            missing_packages.append(display_name)
            print_step(f"{display_name} - 缺失", "ERROR")
    
    if missing_packages:
        print_step(f"缺失以下包: {', '.join(missing_packages)}", "ERROR")
        print_step("请运行: pip install -r requirements.txt", "INFO")
        return False
    
    # 检查PyInstaller
    try:
        result = subprocess.run(["pyinstaller", "--version"], capture_output=True, text=True)
        print_step(f"PyInstaller版本: {result.stdout.strip()}", "SUCCESS")
    except FileNotFoundError:
        print_step("PyInstaller未安装", "ERROR")
        return False
    
    print_step("构建环境检查完成", "SUCCESS")
    return True

def check_files():
    """检查必要文件"""
    print_section("项目文件检查")
    
    # 当前在debug目录中
    debug_dir = Path(__file__).parent
    packaging_dir = debug_dir.parent
    project_root = packaging_dir.parent
    
    print_step(f"调试目录: {debug_dir}")
    print_step(f"打包目录: {packaging_dir}")
    print_step(f"项目根目录: {project_root}")
    
    # 检查必要文件
    required_files = [
        ("调试主程序", debug_dir / "main_debug.py"),
        ("调试配置文件", debug_dir / SPEC_FILE),
        ("Firefox查找器", packaging_dir / "firefox_finder.py"),
        ("应用配置", packaging_dir / "app_config.py"),
        ("项目配置", project_root / "config.json"),
    ]
    
    missing_files = []
    for description, file_path in required_files:
        if file_path.exists():
            print_step(f"{description}: {file_path}", "SUCCESS")
        else:
            print_step(f"{description}: 文件不存在 - {file_path}", "ERROR")
            missing_files.append(description)
    
    if missing_files:
        print_step(f"缺失文件: {', '.join(missing_files)}", "ERROR")
        return False
    
    print_step("项目文件检查完成", "SUCCESS")
    return True

def clean_build():
    """清理构建目录"""
    print_section("清理构建目录")
    
    # 在debug目录中执行构建
    debug_dir = Path(__file__).parent
    os.chdir(debug_dir)
    
    build_dirs = ["build", "dist", "__pycache__"]
    cleaned_items = []
    
    for dir_name in build_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            cleaned_items.append(str(dir_path))
            print_step(f"删除目录: {dir_path}", "SUCCESS")
    
    # 清理.pyc文件
    pyc_count = 0
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
        pyc_count += 1
    
    if pyc_count > 0:
        print_step(f"删除 {pyc_count} 个 .pyc 文件", "SUCCESS")
    
    if cleaned_items or pyc_count > 0:
        print_step("构建目录清理完成", "SUCCESS")
    else:
        print_step("构建目录已经是干净的", "INFO")
    
    return True  # 清理步骤总是成功

def build_application():
    """构建应用程序"""
    print_section("构建调试版应用程序")
    
    # 确保在debug目录中
    debug_dir = Path(__file__).parent
    os.chdir(debug_dir)
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--clean",  # 清理缓存
        "--noconfirm",  # 不询问覆盖
        "--log-level=INFO",  # 显示详细日志
        SPEC_FILE
    ]
    
    print_step(f"执行构建命令: {' '.join(cmd)}")
    print_step("开始构建过程，这可能需要几分钟时间...")
    
    # 执行构建
    start_time = datetime.now()
    
    try:
        # 实时显示构建输出
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 实时输出构建日志
        build_output = []
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                build_output.append(line)
                # 只显示重要信息
                if any(keyword in line.lower() for keyword in 
                       ['info:', 'warning:', 'error:', 'building', 'analyzing', 'collecting']):
                    print(f"  {line}")
        
        process.wait()
        end_time = datetime.now()
        build_time = end_time - start_time
        
        if process.returncode == 0:
            print_step(f"构建成功! 耗时: {build_time}", "SUCCESS")
            return True
        else:
            print_step("构建失败!", "ERROR")
            # 显示错误相关的输出
            print_step("构建错误信息:", "ERROR")
            for line in build_output[-20:]:  # 显示最后20行
                if any(keyword in line.lower() for keyword in ['error', 'failed', 'traceback']):
                    print(f"  {line}")
            return False
            
    except Exception as e:
        print_step(f"构建过程出现异常: {e}", "ERROR")
        return False

def check_build_result():
    """检查构建结果"""
    print_section("构建结果检查")
    
    # 确定可执行文件路径
    if sys.platform == "win32":
        exe_name = f"{PROJECT_NAME}.exe"
    elif sys.platform == "darwin":
        exe_name = f"{PROJECT_NAME}.app"
    else:
        exe_name = PROJECT_NAME
    
    exe_path = Path("dist") / exe_name
    
    if not exe_path.exists():
        print_step(f"未找到可执行文件: {exe_path}", "ERROR")
        # 列出dist目录内容
        dist_path = Path("dist")
        if dist_path.exists():
            print_step("dist目录内容:", "INFO")
            for item in dist_path.iterdir():
                print(f"  {item}")
        return False
    
    # 获取文件大小
    if exe_path.is_file():
        file_size = exe_path.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        print_step(f"可执行文件: {exe_path}", "SUCCESS")
        print_step(f"文件大小: {file_size_mb:.1f} MB", "INFO")
    else:
        print_step(f"应用包: {exe_path}", "SUCCESS")
    
    # 检查关键文件
    if sys.platform == "win32":
        # Windows检查
        internal_dir = exe_path.parent / "_internal"
        if internal_dir.exists():
            print_step("内部文件目录存在", "SUCCESS")
            
            # 检查Firefox
            firefox_exe = internal_dir / "browsers" / "firefox" / "firefox.exe"
            if firefox_exe.exists():
                print_step("内置Firefox浏览器", "SUCCESS")
            else:
                print_step("未找到内置Firefox浏览器", "WARNING")
        else:
            print_step("内部文件目录不存在", "WARNING")
    
    print_step("构建结果检查完成", "SUCCESS")
    return True

def create_run_script():
    """创建运行脚本"""
    print_section("创建运行脚本")
    
    if sys.platform == "win32":
        # Windows批处理脚本
        script_content = f"""@echo off
chcp 65001 >nul
echo 🚀 启动小红书发布工具 - 调试版
echo.
echo 📋 调试版特性:
echo   ✅ 详细的启动过程显示
echo   ✅ 完整的错误信息输出
echo   ✅ 控制台窗口保持打开
echo   ✅ 依赖检查和路径验证
echo.
echo 🔍 正在启动应用程序...
echo.

dist\\{PROJECT_NAME}.exe

echo.
echo 📋 应用程序已退出
pause
"""
        script_path = Path("run_debug.bat")
        
    else:
        # Unix shell脚本
        script_content = f"""#!/bin/bash
echo "🚀 启动小红书发布工具 - 调试版"
echo ""
echo "📋 调试版特性:"
echo "  ✅ 详细的启动过程显示"
echo "  ✅ 完整的错误信息输出"
echo "  ✅ 控制台窗口保持打开"
echo "  ✅ 依赖检查和路径验证"
echo ""
echo "🔍 正在启动应用程序..."
echo ""

./dist/{PROJECT_NAME}

echo ""
echo "📋 应用程序已退出"
read -p "按回车键退出..."
"""
        script_path = Path("run_debug.sh")
    
    try:
        script_path.write_text(script_content, encoding='utf-8')
        if not sys.platform == "win32":
            script_path.chmod(0o755)  # 设置执行权限
        print_step(f"创建运行脚本: {script_path}", "SUCCESS")
        return True
    except Exception as e:
        print_step(f"创建运行脚本失败: {e}", "ERROR")
        return False

def main():
    """主构建流程"""
    print_section("小红书发布工具 - 调试版构建")
    print_step(f"项目: {PROJECT_NAME}")
    print_step(f"版本: {PROJECT_VERSION}")
    print_step(f"平台: {sys.platform}")
    print_step(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 构建步骤
    build_steps = [
        ("环境检查", check_environment),
        ("文件检查", check_files),
        ("清理构建目录", clean_build),
        ("构建应用程序", build_application),
        ("检查构建结果", check_build_result),
        ("创建运行脚本", create_run_script),
    ]
    
    for step_name, step_func in build_steps:
        print_step(f"执行: {step_name}")
        if callable(step_func):
            if not step_func():
                print_step(f"步骤失败: {step_name}", "ERROR")
                print_step("构建过程终止", "ERROR")
                return 1
        else:
            step_func()
    
    print_section("构建完成")
    print_step("🎉 调试版构建成功!", "SUCCESS")
    print_step("📋 使用说明:")
    print_step("  1. 运行生成的可执行文件或运行脚本")
    print_step("  2. 查看详细的启动过程和错误信息")
    print_step("  3. 如有问题，请将控制台输出发送给开发者")
    
    # 显示文件位置
    if sys.platform == "win32":
        print_step(f"  可执行文件: dist\\{PROJECT_NAME}.exe")
        print_step("  运行脚本: run_debug.bat")
    else:
        print_step(f"  可执行文件: dist/{PROJECT_NAME}")
        print_step("  运行脚本: run_debug.sh")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
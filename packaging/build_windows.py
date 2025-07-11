#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows 构建脚本
用于在Windows环境下构建小红书发布工具
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

# 项目配置
PROJECT_NAME = "XhsPublisher"
PROJECT_VERSION = "1.0.0"
SPEC_FILE = "xhs_publisher_windows.spec"

def check_environment():
    """检查构建环境"""
    print("🔍 检查构建环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
        print("❌ 需要Python 3.8或更高版本")
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
    
    missing_packages = []
    for display_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {display_name}")
        except ImportError:
            missing_packages.append(display_name)
            print(f"❌ {display_name} (缺失)")
    
    if missing_packages:
        print(f"\n❌ 缺失以下包: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements.txt")
        return False
    
    # 检查PyInstaller
    try:
        result = subprocess.run(["pyinstaller", "--version"], capture_output=True, text=True)
        print(f"✅ PyInstaller版本: {result.stdout.strip()}")
    except FileNotFoundError:
        print("❌ PyInstaller未安装")
        return False
    
    # 检查Playwright浏览器
    print("\n🦊 检查Playwright Firefox...")
    firefox_paths = [
        Path.home() / "AppData/Local/ms-playwright/firefox-1488/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1489/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1490/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1491/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1492/firefox",
    ]
    
    firefox_found = False
    for firefox_path in firefox_paths:
        if firefox_path.exists() and (firefox_path / "firefox.exe").exists():
            print(f"✅ 找到Firefox: {firefox_path}")
            firefox_found = True
            break
    
    if not firefox_found:
        print("⚠️ 未找到Playwright Firefox，请运行:")
        print("playwright install firefox")
        # 不阻止构建，但给出警告
    
    return True

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    build_dirs = ["build", "dist", "__pycache__"]
    for dir_name in build_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  删除: {dir_path}")
    
    # 清理.pyc文件
    for pyc_file in Path(".").rglob("*.pyc"):
        pyc_file.unlink()
    
    print("✅ 清理完成")

def build_application():
    """构建应用程序"""
    print("🔨 开始构建应用程序...")
    
    # 确保在packaging目录中
    packaging_dir = Path(__file__).parent
    os.chdir(packaging_dir)
    
    # 构建命令
    cmd = [
        "pyinstaller",
        "--clean",
        "--noconfirm",
        SPEC_FILE
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 执行构建
    start_time = datetime.now()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = datetime.now()
    
    build_time = end_time - start_time
    print(f"构建耗时: {build_time}")
    
    if result.returncode == 0:
        print("✅ 构建成功!")
        
        # 显示构建输出的关键信息
        output_lines = result.stdout.split('\n')
        for line in output_lines:
            if any(keyword in line.lower() for keyword in ['warning', 'error', 'firefox', 'missing']):
                print(f"  {line}")
        
        return True
    else:
        print("❌ 构建失败!")
        print("错误输出:")
        print(result.stderr)
        return False

def check_build_result():
    """检查构建结果"""
    print("🔍 检查构建结果...")
    
    exe_path = Path("dist") / f"{PROJECT_NAME}.exe"
    
    if not exe_path.exists():
        print(f"❌ 未找到可执行文件: {exe_path}")
        return False
    
    # 获取文件大小
    file_size = exe_path.stat().st_size
    file_size_mb = file_size / (1024 * 1024)
    
    print(f"✅ 可执行文件: {exe_path}")
    print(f"   文件大小: {file_size_mb:.1f} MB")
    
    # 检查是否有Firefox
    firefox_exe = exe_path.parent / "_internal" / "browsers" / "firefox" / "firefox.exe"
    if firefox_exe.exists():
        print("✅ 内置Firefox浏览器")
    else:
        print("⚠️ 未找到内置Firefox浏览器")
    
    return True

def create_installer():
    """创建安装程序（可选）"""
    print("📦 创建安装程序...")
    
    # 检查是否有NSIS或其他安装程序制作工具
    try:
        subprocess.run(["makensis", "/VERSION"], capture_output=True, check=True)
        print("✅ 找到NSIS，可以创建安装程序")
        # 这里可以添加创建NSIS脚本的代码
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("⚠️ 未找到NSIS，跳过安装程序创建")
        print("   可手动使用NSIS或其他工具创建安装程序")

def main():
    """主构建流程"""
    print("🚀 Windows构建脚本")
    print("=" * 50)
    print(f"项目: {PROJECT_NAME}")
    print(f"版本: {PROJECT_VERSION}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查环境
    if not check_environment():
        print("❌ 环境检查失败，构建终止")
        sys.exit(1)
    
    # 清理构建目录
    clean_build()
    
    # 构建应用程序
    if not build_application():
        print("❌ 构建失败")
        sys.exit(1)
    
    # 检查构建结果
    if not check_build_result():
        print("❌ 构建结果检查失败")
        sys.exit(1)
    
    # 创建安装程序（可选）
    create_installer()
    
    print("\n🎉 构建完成!")
    print("=" * 50)
    print(f"可执行文件位置: dist/{PROJECT_NAME}.exe")
    print("可以直接运行或分发给用户")
    print("=" * 50)

if __name__ == "__main__":
    main() 
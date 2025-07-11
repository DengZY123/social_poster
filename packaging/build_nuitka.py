#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Nuitka构建脚本 - 支持跨平台编译
用于生成Windows版本的可执行文件
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# 添加项目路径以导入 firefox_finder
sys.path.insert(0, str(Path(__file__).parent))
from firefox_finder import FirefoxFinder

# 项目配置
PROJECT_NAME = "XhsPublisher"
PROJECT_VERSION = "1.0.0"
TARGET_PLATFORM = "windows"

def check_nuitka():
    """检查Nuitka是否已安装"""
    try:
        result = subprocess.run(["python", "-m", "nuitka", "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Nuitka版本: {result.stdout.strip()}")
            return True
        else:
            print("❌ Nuitka未正确安装")
            return False
    except FileNotFoundError:
        print("❌ 找不到Nuitka")
        return False

def check_dependencies():
    """检查依赖包"""
    print("📦 检查项目依赖...")
    
    # 包名映射：包名 -> 实际导入名
    package_map = {
        "PyQt6": "PyQt6",
        "playwright": "playwright", 
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "loguru": "loguru",
        "pydantic": "pydantic", 
        "ujson": "ujson"
    }
    
    missing_packages = []
    for display_name, import_name in package_map.items():
        try:
            __import__(import_name)
            print(f"✅ {display_name}")
        except ImportError:
            missing_packages.append(display_name)
            print(f"❌ {display_name} (缺失)")
    
    if missing_packages:
        print(f"\n⚠️ 缺失依赖: {', '.join(missing_packages)}")
        print("请运行: pip install -r requirements_windows.txt")
        return False
    
    return True

def clean_build():
    """清理构建目录"""
    print("🧹 清理构建目录...")
    
    build_dirs = ["build", "dist", f"{PROJECT_NAME}.dist", f"{PROJECT_NAME}.build"]
    for dir_name in build_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            shutil.rmtree(dir_path)
            print(f"  删除: {dir_path}")

def build_with_nuitka():
    """使用Nuitka构建应用"""
    print("🔨 开始Nuitka构建...")
    
    # 确保在packaging目录中
    packaging_dir = Path(__file__).parent
    os.chdir(packaging_dir)
    
    # 主脚本路径
    main_script = "main_packaged.py"
    
    # 检测Firefox路径
    firefox_finder = FirefoxFinder()
    firefox_path = firefox_finder.find_playwright_firefox()
    
    # Nuitka构建命令 - 使用基本选项
    cmd = [
        "python", "-m", "nuitka",
        
        # 基本选项
        "--standalone",              # 独立可执行文件
        "--assume-yes-for-downloads", # 自动下载依赖
        
        # 优化选项
        "--lto=yes",                # 链接时优化
        
        # 包含模块
        "--include-package=PyQt6",
        "--include-package=playwright", 
        "--include-package=core",
        "--include-package=gui",
        "--include-package=packaging",
        
        # 包含数据文件
        "--include-data-dir=scripts=packaging/scripts",
        "--include-data-dir=firefox_portable=firefox_portable",
        
        # 输出设置
        f"--output-dir=dist",
        
        # 主脚本
        main_script
    ]
    
    # 如果找到Firefox，添加到打包中
    if firefox_path:
        firefox_info = firefox_finder.get_firefox_info(firefox_path)
        if firefox_info['app_dir']:
            print(f"📦 包含Firefox浏览器: {firefox_info['app_dir']}")
            cmd.insert(-1, f"--include-data-dir={firefox_info['app_dir']}=browsers/firefox")
        else:
            print("⚠️ 未找到Firefox应用目录，应用将需要手动下载浏览器")
    else:
        print("⚠️ 未找到本地Firefox，应用将需要手动下载浏览器")
    
    print(f"执行命令: {' '.join(cmd)}")
    
    # 执行构建
    start_time = datetime.now()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        end_time = datetime.now()
        build_time = end_time - start_time
        
        print(f"✅ 构建成功!")
        print(f"构建耗时: {build_time}")
        
        # 显示输出关键信息
        if result.stdout:
            lines = result.stdout.split('\n')
            for line in lines[-10:]:  # 显示最后10行
                if line.strip():
                    print(f"  {line}")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败!")
        print(f"错误代码: {e.returncode}")
        if e.stderr:
            print("错误输出:")
            print(e.stderr)
        if e.stdout:
            print("标准输出:")
            print(e.stdout)
        return False

def build_with_alternative_options():
    """使用备选选项构建（如果标准方式失败）"""
    print("🔄 尝试备选构建选项...")
    
    # 更简单的构建命令
    cmd = [
        "python", "-m", "nuitka",
        "--standalone",
        "--assume-yes-for-downloads",
        "--include-package=PyQt6",
        "--include-package=core",
        "--include-package=gui",
        f"--output-dir=dist",
        "main_packaged.py"
    ]
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ 备选构建成功!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 备选构建也失败: {e}")
        return False

def check_build_result():
    """检查构建结果"""
    print("🔍 检查构建结果...")
    
    # 查找可能的输出文件
    possible_paths = [
        Path("dist") / f"{PROJECT_NAME}.exe",
        Path("dist") / "main_packaged.exe", 
        Path(f"{PROJECT_NAME}.dist") / f"{PROJECT_NAME}.exe",
        Path("main_packaged.dist") / "main_packaged.exe"
    ]
    
    for exe_path in possible_paths:
        if exe_path.exists():
            file_size = exe_path.stat().st_size
            file_size_mb = file_size / (1024 * 1024)
            
            print(f"✅ 找到可执行文件: {exe_path}")
            print(f"   文件大小: {file_size_mb:.1f} MB")
            return True
    
    print("❌ 未找到可执行文件")
    print("可能的位置:")
    for path in possible_paths:
        print(f"  {path}")
    
    return False

def main():
    """主构建流程"""
    print("🚀 Nuitka跨平台构建脚本")
    print("=" * 50)
    print(f"项目: {PROJECT_NAME}")
    print(f"版本: {PROJECT_VERSION}")
    print(f"目标平台: {TARGET_PLATFORM}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 检查Nuitka
    if not check_nuitka():
        print("❌ Nuitka检查失败")
        return False
    
    # 检查依赖
    if not check_dependencies():
        print("❌ 依赖检查失败")
        return False
    
    # 清理构建目录
    clean_build()
    
    # 尝试构建
    if not build_with_nuitka():
        print("⚠️ 标准构建失败，尝试备选方案...")
        if not build_with_alternative_options():
            print("❌ 所有构建方案都失败")
            return False
    
    # 检查构建结果
    if not check_build_result():
        print("❌ 构建结果检查失败")
        return False
    
    print("\n🎉 Nuitka构建完成!")
    print("=" * 50)
    print("注意: Nuitka在macOS上生成的文件可能仍需要在Windows上测试")
    print("建议在Windows环境中验证可执行文件的兼容性")
    print("=" * 50)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
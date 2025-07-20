# -*- mode: python ; coding: utf-8 -*-
"""
小红书发布工具 - Windows PyInstaller配置文件
用于将Python应用打包为Windows可执行文件
"""
import os
import sys
from pathlib import Path

# 获取项目路径
PROJECT_ROOT = Path(SPECPATH).parent
PACKAGING_DIR = Path(SPECPATH)

# 应用信息
APP_NAME = "XhsPublisher_Console"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "小红书定时发布工具"
APP_AUTHOR = "XHS Publisher Team"

# 主程序文件 - 使用打包专用入口
MAIN_SCRIPT = str(PACKAGING_DIR / "main_packaged.py")

# ===================== 数据文件收集 =====================

# 项目源代码目录
datas = []

# Windows下的Firefox路径检测
# 常见的Playwright Firefox路径
firefox_paths = [
    Path.home() / "AppData/Local/ms-playwright/firefox-1488/firefox",
    Path.home() / "AppData/Local/ms-playwright/firefox-1489/firefox", 
    Path.home() / "AppData/Local/ms-playwright/firefox-1490/firefox",
    Path.home() / "AppData/Local/ms-playwright/firefox-1491/firefox",
    Path.home() / "AppData/Local/ms-playwright/firefox-1492/firefox",
    # 添加更多可能的版本
]

# 查找可用的Firefox
firefox_found = False
for firefox_path in firefox_paths:
    if firefox_path.exists() and (firefox_path / "firefox.exe").exists():
        print(f"[Firefox] 发现本地 Firefox，将打包到应用中: {firefox_path}")
        # 打包到 browsers/firefox 目录
        datas.append((str(firefox_path), "browsers/firefox"))
        firefox_found = True
        break

if not firefox_found:
    print("[警告] 未找到本地 Firefox，应用将需要手动下载浏览器")
    print("请确保已安装 Playwright 并下载了 Firefox 浏览器")

# 添加配置文件和资源
datas.extend([
    # 示例图片
    (str(PROJECT_ROOT / "images"), "images"),
    
    # 默认配置
    (str(PROJECT_ROOT / "config.json"), "."),
    
    # 打包配置和脚本
    (str(PACKAGING_DIR / "scripts"), "packaging/scripts"),
    (str(PACKAGING_DIR / "app_config.py"), "packaging"),
    
    # Firefox配置信息
    (str(PACKAGING_DIR / "firefox_portable"), "firefox_portable"),
])

# 添加GUI组件模板或资源（如果有的话）
gui_resources = PROJECT_ROOT / "gui" / "resources"
if gui_resources.exists():
    datas.append((str(gui_resources), "gui/resources"))

# ===================== 分析配置 =====================

# 排除不必要的大型库
excludes = [
    # 测试相关
    'unittest', 'pytest', 'nose',
    
    # 开发工具
    'pdb', 'doctest', 'pydoc',
    
    # 大型科学计算库（如果不需要）
    'matplotlib', 'scipy', 'sympy',
    
    # 网络相关（如果不需要）
    'http.server', 'xmlrpc',
    
    # 数据库相关（如果不需要）
    'sqlite3', 'dbm',
    
    # 其他不必要的模块
    'tkinter', 'turtle', 'curses',
    'multiprocessing.dummy',
    
    # Windows不需要的模块
    'readline', 'rlcompleter',
]

# 隐藏导入（确保这些模块被包含）
hiddenimports = [
    # PyQt6 相关
    'PyQt6.QtCore',
    'PyQt6.QtWidgets', 
    'PyQt6.QtGui',
    
    # Playwright 相关
    'playwright',
    'playwright.sync_api',
    'playwright.async_api',
    
    # 项目模块
    'core.models',
    'core.scheduler',
    'core.publisher',
    'core.storage',
    'core.process_manager',
    'gui.main_window',
    'gui.components',
    'gui.components.account_tab',
    'gui.components.control_panel',
    'gui.components.excel_importer',
    'gui.components.task_detail_table',
    
    # 打包相关
    'packaging.app_config',
    'packaging.scripts.path_detector',
    
    # 数据处理
    'pandas',
    'numpy',
    'openpyxl',
    'ujson',
    'loguru',
    'pydantic',
    
    # Windows特定
    'win32api', 'win32con', 'win32gui', 'win32process',
]

# 主分析对象
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT), str(PACKAGING_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 依赖收集
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ===================== Windows应用配置 =====================

# Windows应用配置
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f"{APP_NAME}.exe",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[
        # 排除可能导致问题的文件
        "firefox.exe",
        "vcruntime140.dll",
        "msvcp140.dll",
    ],
    runtime_tmpdir=None,
    console=True,  # 控制台版本，显示调试信息
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # 可以添加图标文件路径
    version_file=None,  # 可以添加版本信息文件
)

# ===================== 调试信息 =====================

print("=" * 60)
print(f"[配置] Windows PyInstaller配置信息")
print("=" * 60)
print(f"应用名称: {APP_NAME}")
print(f"版本号: {APP_VERSION}")
print(f"平台: {sys.platform}")
print(f"项目根目录: {PROJECT_ROOT}")
print(f"打包目录: {PACKAGING_DIR}")
print(f"主脚本: {MAIN_SCRIPT}")
print(f"数据文件数量: {len(datas)}")
print(f"隐藏导入数量: {len(hiddenimports)}")
print(f"排除模块数量: {len(excludes)}")
print(f"Firefox已找到: {firefox_found}")
print("=" * 60) 
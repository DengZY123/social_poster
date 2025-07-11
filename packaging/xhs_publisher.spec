# -*- mode: python ; coding: utf-8 -*-
"""
小红书发布工具 - PyInstaller配置文件
用于将Python应用打包为可执行文件
"""
import os
import sys
from pathlib import Path

# 获取项目路径
PROJECT_ROOT = Path(SPECPATH).parent
PACKAGING_DIR = Path(SPECPATH)

# 应用信息
APP_NAME = "XhsPublisher"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "小红书定时发布工具"
APP_AUTHOR = "XHS Publisher Team"

# 平台检测
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# 主程序文件 - 使用打包专用入口
MAIN_SCRIPT = str(PACKAGING_DIR / "main_packaged.py")

# ===================== 数据文件收集 =====================

# 项目源代码目录
datas = []

# 添加本地 Playwright Firefox 到打包中
import os
firefox_source = "/Users/dzy/Library/Caches/ms-playwright/firefox-1488/firefox/"
if os.path.exists(firefox_source):
    print(f"📦 发现本地 Firefox，将打包到应用中: {firefox_source}")
    if IS_MACOS:
        # macOS: 将 Firefox 打包到 Frameworks/browsers 目录
        datas.append((firefox_source, "browsers/firefox"))
    elif IS_WINDOWS:
        # Windows: 将 Firefox 打包到 browsers 目录  
        datas.append((firefox_source, "browsers/firefox"))
else:
    print("⚠️ 未找到本地 Firefox，应用将在首次运行时下载")

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

# ===================== 隐藏导入模块 =====================

hiddenimports = [
    # PyQt6相关
    "PyQt6.QtCore",
    "PyQt6.QtGui", 
    "PyQt6.QtWidgets",
    "PyQt6.sip",
    
    # Playwright相关
    "playwright",
    "playwright.async_api",
    "playwright._impl",
    
    # 数据处理
    "pandas",
    "openpyxl",
    "xlsxwriter",
    
    # 日志系统
    "loguru",
    
    # 数据验证
    "pydantic",
    "pydantic.dataclasses",
    
    # JSON处理
    "ujson",
    
    # 异步支持
    "asyncio",
    "concurrent.futures",
    
    # 系统相关
    "subprocess",
    "multiprocessing",
    "threading",
    
    # 网络相关
    "urllib3",
    "certifi",
    
    # 项目模块
    "core",
    "core.models",
    "core.scheduler", 
    "core.storage",
    "core.publisher",
    "core.process_manager",
    "gui",
    "gui.main_window",
    "gui.components",
    "gui.components.excel_importer",
    "utils",
    "utils.excel_importer",
    
    # 打包环境模块
    "packaging.scripts.path_detector",
    "packaging.app_config",
]

# ===================== 排除模块 =====================

excludes = [
    # 开发工具
    "pytest",
    "black",
    "flake8",
    "mypy",
    
    # 不需要的GUI工具包
    "tkinter",
    "matplotlib",
    
    # 不需要的数据科学库
    "numpy.tests",
    "pandas.tests",
    "scipy",
    "sklearn",
    
    # 开发服务器
    "tornado",
    "flask",
    "django",
    
    # 不需要的网络库
    "requests_oauthlib",
    "oauthlib",
]

# ===================== 路径和钩子 =====================

# 添加项目路径到pathex
pathex = [
    str(PROJECT_ROOT),
    str(PACKAGING_DIR),
]

# 运行时钩子
runtime_hooks = []

# ===================== 构建配置 =====================

# 分析阶段
a = Analysis(
    [MAIN_SCRIPT],
    pathex=pathex,
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=runtime_hooks,
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 依赖收集
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# ===================== 平台特定配置 =====================

if IS_MACOS:
    # macOS应用配置
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        console=False,  # GUI应用
        disable_windowed_traceback=False,
        target_arch=None,  # 使用当前架构，避免通用二进制问题
        codesign_identity=None,
        entitlements_file=None,
    )

    # 收集所有文件
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=True,
        upx_exclude=[],
        name=APP_NAME,
    )

    # 创建.app包
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,  # 可以添加图标文件路径
        bundle_identifier=f"com.xhspublisher.{APP_NAME.lower()}",
        version=APP_VERSION,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": "小红书发布工具",
            "CFBundleVersion": APP_VERSION,
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleIdentifier": f"com.xhspublisher.{APP_NAME.lower()}",
            "LSMinimumSystemVersion": "10.14",  # macOS Mojave或更高
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.productivity",
            "CFBundleDocumentTypes": [
                {
                    "CFBundleTypeName": "Excel Files",
                    "CFBundleTypeExtensions": ["xlsx", "xls"],
                    "CFBundleTypeRole": "Editor",
                }
            ],
        },
    )

elif IS_WINDOWS:
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
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # GUI应用
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        version="version_info.txt",  # 可以创建版本信息文件
        icon=None,  # 可以添加图标文件路径
    )

else:
    # Linux应用配置
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=True,
        upx_exclude=[],
        runtime_tmpdir=None,
        console=False,  # GUI应用
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )

# ===================== 调试信息 =====================

print("=" * 60)
print(f"📦 PyInstaller配置信息")
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
print("=" * 60)
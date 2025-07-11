# -*- mode: python ; coding: utf-8 -*-
"""
小红书发布工具 - 调试版 PyInstaller配置文件
用于打包调试版本，包含详细的控制台输出
"""
import os
import sys
from pathlib import Path

# 获取项目路径（现在在debug子目录中）
PROJECT_ROOT = Path(SPECPATH).parent.parent.parent
PACKAGING_DIR = Path(SPECPATH).parent.parent

# 应用信息
APP_NAME = "XhsPublisherDebug"
APP_VERSION = "1.0.0-debug"
APP_DESCRIPTION = "小红书定时发布工具 - 调试版"
APP_AUTHOR = "XHS Publisher Team"

# 平台检测
IS_MACOS = sys.platform == "darwin"
IS_WINDOWS = sys.platform == "win32"
IS_LINUX = sys.platform.startswith("linux")

# 主程序文件 - 使用调试版入口（在debug目录中）
MAIN_SCRIPT = "main_debug.py"

print("=" * 60)
print("小红书发布工具 - 调试版打包配置")
print("=" * 60)
print(f"应用名称: {APP_NAME}")
print(f"版本号: {APP_VERSION}")
print(f"平台: {sys.platform}")
print(f"项目根目录: {PROJECT_ROOT}")
print(f"打包目录: {PACKAGING_DIR}")
print(f"主脚本: {MAIN_SCRIPT}")
print("=" * 60)

# ===================== 数据文件收集 =====================

# 项目源代码目录
datas = []

# 添加本地 Playwright Firefox 到打包中
# 使用动态检测获取 Firefox 路径
import sys
sys.path.insert(0, str(PACKAGING_DIR))

try:
    from firefox_finder import FirefoxFinder
except ImportError:
    # 如果导入失败，跳过Firefox检测
    print("警告: 无法导入firefox_finder模块，跳过Firefox检测")
    FirefoxFinder = None

if FirefoxFinder is not None:
    firefox_finder = FirefoxFinder()
    firefox_path = firefox_finder.find_playwright_firefox()

    if firefox_path:
        firefox_info = firefox_finder.get_firefox_info(firefox_path)
        if firefox_info['app_dir'] and os.path.exists(firefox_info['app_dir']):
            print(f"发现本地 Firefox，将打包到应用中: {firefox_info['app_dir']}")
            # 只打包到 Resources/browsers 目录，避免重复
            datas.append((firefox_info['app_dir'], "browsers/firefox"))
            print("Firefox 数据已添加到打包配置")
        else:
            print("Firefox 应用目录无效，应用将需要手动下载浏览器")
    else:
        print("未找到本地 Firefox，应用将需要手动下载浏览器")
else:
    print("跳过 Firefox 检测，应用将需要手动下载浏览器")

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
    print(f"GUI资源已添加: {gui_resources}")

print(f"总共添加 {len(datas)} 个数据文件/目录")

# ===================== 分析配置 =====================

# 排除不必要的大型库（调试版减少排除，确保完整性）
excludes = [
    # 测试相关
    'unittest', 'pytest', 'nose',
    
    # 开发工具（保留更多用于调试）
    'pdb',  # 保留用于调试
    
    # 大型科学计算库（如果不需要）
    'matplotlib', 'scipy', 'sympy',
    
    # 数据库相关（如果不需要）
    'sqlite3', 'dbm',
    
    # 其他不必要的模块
    'tkinter', 'turtle', 'curses',
]

# 隐藏导入（确保这些模块被包含，调试版包含更多）
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
    'gui.main_window',
    'gui.components',
    
    # 打包相关
    'packaging.app_config',
    'packaging.scripts.path_detector',
    
    # 数据处理
    'pandas',
    'openpyxl',
    'ujson',
    'loguru',
    'pydantic',
    
    # 调试相关（额外添加）
    'traceback',
    'inspect',
    'pprint',
]

print(f"隐藏导入模块数量: {len(hiddenimports)}")
print(f"排除模块数量: {len(excludes)}")

# 主分析对象
a = Analysis(
    [MAIN_SCRIPT],
    pathex=[str(PROJECT_ROOT)],  # 只添加项目根目录，避免packaging目录名冲突
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

# ===================== 平台特定配置 =====================

if IS_WINDOWS:
    # Windows调试版配置
    print("配置Windows调试版应用...")
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=f"{APP_NAME}.exe",
        debug=True,  # 启用调试模式
        bootloader_ignore_signals=False,
        strip=False,  # 不剥离符号，保留调试信息
        upx=False,  # 不压缩，便于调试
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,  # 强制显示控制台
        disable_windowed_traceback=False,  # 启用错误回溯
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        icon=None,  # 可以添加图标文件路径
    )
    print("Windows调试版EXE配置完成")

elif IS_MACOS:
    # macOS调试版配置
    print("配置macOS调试版应用...")
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name=APP_NAME,
        debug=True,  # 启用调试模式
        bootloader_ignore_signals=False,
        strip=False,  # 不剥离符号
        upx=False,  # 不压缩
        console=True,  # 显示控制台
        disable_windowed_traceback=False,
        target_arch=None,
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
        upx=False,
        upx_exclude=[],
        name=APP_NAME,
    )

    # 创建.app包
    app = BUNDLE(
        coll,
        name=f"{APP_NAME}.app",
        icon=None,
        bundle_identifier=f"com.xhspublisher.{APP_NAME.lower()}",
        version=APP_VERSION,
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": "小红书发布工具 - 调试版",
            "CFBundleVersion": APP_VERSION,
            "CFBundleShortVersionString": APP_VERSION,
            "CFBundleIdentifier": f"com.xhspublisher.{APP_NAME.lower()}",
            "LSMinimumSystemVersion": "10.14",
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.developer-tools",
        },
    )
    print("macOS调试版APP包配置完成")

else:
    # Linux调试版配置
    print("配置Linux调试版应用...")
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name=APP_NAME,
        debug=True,  # 启用调试模式
        bootloader_ignore_signals=False,
        strip=False,  # 不剥离符号
        upx=False,  # 不压缩
        upx_exclude=[],
        runtime_tmpdir=None,
        console=True,  # 显示控制台
        disable_windowed_traceback=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
    )
    print("Linux调试版可执行文件配置完成")

# ===================== 调试信息 =====================

print("\n" + "=" * 60)
print("调试版打包配置完成")
print("=" * 60)
print("调试特性:")
print("  启用调试模式")
print("  保留符号信息")
print("  强制显示控制台")
print("  详细启动日志")
print("  完整错误回溯")
print("  依赖检查功能")
print("  路径验证功能")
print("=" * 60)
print("使用说明:")
print("  1. 运行后会显示详细的启动过程")
print("  2. 任何错误都会有完整的错误信息")
print("  3. 控制台窗口会保持打开状态")
print("  4. 按回车键可关闭控制台")
print("=" * 60) 
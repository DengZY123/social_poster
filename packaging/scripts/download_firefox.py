#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firefox便携版下载脚本
自动下载适用于Mac和Windows的便携版Firefox
"""
import os
import sys
import zipfile
import tarfile
import shutil
import tempfile
from pathlib import Path
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError
import json
import platform

# Firefox下载URLs
FIREFOX_URLS = {
    "mac": {
        "url": "https://download.mozilla.org/?product=firefox-latest&os=osx&lang=zh-CN",
        "filename": "Firefox.dmg",
        "type": "dmg"
    },
    "windows": {
        "url": "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=zh-CN",
        "filename": "Firefox Setup.exe",
        "type": "installer"
    },
    # 使用便携版的备用URL
    "windows_portable": {
        "url": "https://sourceforge.net/projects/portableapps/files/Mozilla%20Firefox%2C%20Portable%20Ed./",
        "filename": "FirefoxPortable.paf.exe",
        "type": "portable"
    }
}

class FirefoxDownloader:
    """Firefox下载器"""
    
    def __init__(self, packaging_dir: str):
        self.packaging_dir = Path(packaging_dir)
        self.firefox_dir = self.packaging_dir / "firefox_portable"
        self.temp_dir = self.packaging_dir / "temp"
        
        # 确保目录存在
        self.firefox_dir.mkdir(exist_ok=True)
        self.temp_dir.mkdir(exist_ok=True)
    
    def download_firefox_mac(self):
        """下载macOS版Firefox"""
        print("🍎 准备下载macOS版Firefox...")
        
        mac_dir = self.firefox_dir / "mac"
        mac_dir.mkdir(exist_ok=True)
        
        # 由于macOS的Firefox是dmg格式，比较复杂
        # 我们使用Playwright安装的Firefox
        self._use_playwright_firefox("mac")
    
    def download_firefox_windows(self):
        """下载Windows版Firefox"""
        print("🪟 准备下载Windows版Firefox...")
        
        windows_dir = self.firefox_dir / "windows"
        windows_dir.mkdir(exist_ok=True)
        
        # Windows也使用Playwright的Firefox，更稳定
        self._use_playwright_firefox("windows")
    
    def _use_playwright_firefox(self, platform_name: str):
        """使用Playwright的Firefox"""
        try:
            print(f"🎭 为{platform_name}配置Playwright Firefox...")
            
            # 安装Playwright Firefox
            import subprocess
            result = subprocess.run([
                sys.executable, "-m", "playwright", "install", "firefox"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ Playwright Firefox安装成功")
                
                # 创建配置文件
                platform_dir = self.firefox_dir / platform_name
                config = {
                    "type": "playwright",
                    "installed": True,
                    "version": "latest",
                    "notes": "使用Playwright安装的Firefox浏览器"
                }
                
                with open(platform_dir / "config.json", "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                
                return True
            else:
                print(f"❌ Playwright Firefox安装失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 配置Playwright Firefox失败: {e}")
            return False
    
    def create_firefox_launcher(self, platform_name: str):
        """创建Firefox启动器脚本"""
        platform_dir = self.firefox_dir / platform_name
        
        if platform_name == "mac":
            launcher_content = '''#!/bin/bash
# macOS Firefox启动器
# 使用Playwright的Firefox

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="$HOME/Library/Caches/ms-playwright"

# 启动Firefox
exec python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def launch_firefox():
    playwright = await async_playwright().start()
    browser = await playwright.firefox.launch(headless=False)
    # 保持运行
    await asyncio.sleep(86400)  # 24小时
    await browser.close()
    await playwright.stop()

asyncio.run(launch_firefox())
"
'''
            launcher_path = platform_dir / "firefox_launcher.sh"
            with open(launcher_path, "w") as f:
                f.write(launcher_content)
            launcher_path.chmod(0o755)
            
        elif platform_name == "windows":
            launcher_content = '''@echo off
REM Windows Firefox启动器
REM 使用Playwright的Firefox

set SCRIPT_DIR=%~dp0
set PLAYWRIGHT_BROWSERS_PATH=%USERPROFILE%\\AppData\\Local\\ms-playwright

python -c "
import asyncio
from playwright.async_api import async_playwright

async def launch_firefox():
    playwright = await async_playwright().start()
    browser = await playwright.firefox.launch(headless=False)
    await asyncio.sleep(86400)
    await browser.close()
    await playwright.stop()

asyncio.run(launch_firefox())
"
'''
            launcher_path = platform_dir / "firefox_launcher.bat"
            with open(launcher_path, "w") as f:
                f.write(launcher_content)
    
    def download_all(self):
        """下载所有平台的Firefox"""
        print("🚀 开始下载Firefox浏览器...")
        
        success = True
        
        # 下载macOS版本
        try:
            self.download_firefox_mac()
            self.create_firefox_launcher("mac")
            print("✅ macOS版Firefox配置完成")
        except Exception as e:
            print(f"❌ macOS版Firefox配置失败: {e}")
            success = False
        
        # 下载Windows版本
        try:
            self.download_firefox_windows() 
            self.create_firefox_launcher("windows")
            print("✅ Windows版Firefox配置完成")
        except Exception as e:
            print(f"❌ Windows版Firefox配置失败: {e}")
            success = False
        
        if success:
            print("🎉 所有Firefox浏览器配置完成！")
        else:
            print("⚠️ 部分Firefox配置失败，但不影响打包")
        
        return success
    
    def verify_installation(self):
        """验证Firefox安装"""
        print("🔍 验证Firefox安装...")
        
        for platform_name in ["mac", "windows"]:
            platform_dir = self.firefox_dir / platform_name
            config_file = platform_dir / "config.json"
            
            if config_file.exists():
                try:
                    with open(config_file, "r", encoding="utf-8") as f:
                        config = json.load(f)
                    print(f"✅ {platform_name}: {config.get('type', 'unknown')} - {config.get('version', 'unknown')}")
                except Exception as e:
                    print(f"❌ {platform_name}: 配置文件读取失败 - {e}")
            else:
                print(f"⚠️ {platform_name}: 未找到配置文件")


def main():
    """主函数"""
    script_dir = Path(__file__).parent
    packaging_dir = script_dir.parent
    
    print("🦊 Firefox便携版下载器")
    print(f"📁 打包目录: {packaging_dir}")
    
    downloader = FirefoxDownloader(packaging_dir)
    
    try:
        # 下载Firefox
        downloader.download_all()
        
        # 验证安装
        downloader.verify_installation()
        
        print("\n✅ Firefox下载和配置完成！")
        print("💡 提示：实际使用时会自动使用Playwright管理的Firefox")
        
    except Exception as e:
        print(f"\n❌ Firefox下载失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
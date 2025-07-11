#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firefox 浏览器查找器
自动检测系统中的 Playwright Firefox 安装位置
"""
import os
import platform
import subprocess
from pathlib import Path
from typing import Optional, List, Tuple


class FirefoxFinder:
    """Firefox 浏览器查找器"""
    
    def __init__(self):
        self.platform = platform.system().lower()
        self.is_mac = self.platform == "darwin"
        self.is_windows = self.platform == "windows"
        self.is_linux = self.platform == "linux"
        
    def find_playwright_firefox(self) -> Optional[str]:
        """查找 Playwright Firefox 浏览器"""
        print("🔍 正在查找 Playwright Firefox...")
        
        # 获取所有可能的 Firefox 路径
        firefox_paths = self._get_all_firefox_paths()
        
        if not firefox_paths:
            print("❌ 未找到任何 Playwright Firefox 安装")
            return None
        
        # 选择最新版本
        latest_firefox = self._select_latest_firefox(firefox_paths)
        
        if latest_firefox:
            print(f"✅ 找到 Firefox: {latest_firefox}")
            return latest_firefox
        else:
            print("❌ 未找到有效的 Firefox 可执行文件")
            return None
    
    def _get_all_firefox_paths(self) -> List[Tuple[str, str]]:
        """获取所有可能的 Firefox 路径"""
        firefox_paths = []
        
        # 1. 从环境变量获取 Playwright 浏览器路径
        playwright_path = os.environ.get('PLAYWRIGHT_BROWSERS_PATH')
        if playwright_path:
            firefox_paths.extend(self._scan_directory(Path(playwright_path)))
        
        # 2. 检查默认的 Playwright 缓存位置
        cache_paths = self._get_playwright_cache_paths()
        for cache_path in cache_paths:
            if cache_path.exists():
                firefox_paths.extend(self._scan_directory(cache_path))
        
        # 3. 使用 playwright 命令获取路径（如果可用）
        playwright_firefox = self._get_firefox_from_playwright_command()
        if playwright_firefox:
            version = self._extract_version_from_path(playwright_firefox)
            firefox_paths.append((playwright_firefox, version))
        
        # 去重并排序
        unique_paths = list(set(firefox_paths))
        unique_paths.sort(key=lambda x: x[1], reverse=True)
        
        return unique_paths
    
    def _get_playwright_cache_paths(self) -> List[Path]:
        """获取 Playwright 缓存路径"""
        paths = []
        
        if self.is_mac:
            # macOS 缓存位置
            paths.extend([
                Path.home() / "Library" / "Caches" / "ms-playwright",
                Path("/Users") / os.environ.get('USER', '') / "Library" / "Caches" / "ms-playwright",
            ])
        elif self.is_windows:
            # Windows 缓存位置
            paths.extend([
                Path.home() / "AppData" / "Local" / "ms-playwright",
                Path(os.environ.get('LOCALAPPDATA', '')) / "ms-playwright",
            ])
        else:
            # Linux 缓存位置
            paths.extend([
                Path.home() / ".cache" / "ms-playwright",
                Path("/var/cache") / "ms-playwright",
            ])
        
        return [p for p in paths if p and p != Path('.')]
    
    def _scan_directory(self, base_path: Path) -> List[Tuple[str, str]]:
        """扫描目录查找 Firefox"""
        firefox_paths = []
        
        if not base_path.exists():
            return firefox_paths
        
        print(f"  扫描目录: {base_path}")
        
        # 查找 firefox-* 目录
        for firefox_dir in base_path.glob("firefox-*"):
            if firefox_dir.is_dir():
                print(f"    找到 Firefox 目录: {firefox_dir}")
                # 提取版本号
                version = self._extract_version_from_path(str(firefox_dir))
                
                # 查找可执行文件
                executable = self._find_firefox_executable(firefox_dir)
                if executable:
                    print(f"    找到可执行文件: {executable}")
                    firefox_paths.append((str(executable), version))
                else:
                    print(f"    未找到可执行文件")
        
        return firefox_paths
    
    def _find_firefox_executable(self, firefox_dir: Path) -> Optional[Path]:
        """在 Firefox 目录中查找可执行文件"""
        if self.is_mac:
            # macOS: Firefox 在 .app 包中
            candidates = [
                firefox_dir / "firefox" / "Nightly.app" / "Contents" / "MacOS" / "firefox",
                firefox_dir / "firefox" / "Firefox.app" / "Contents" / "MacOS" / "firefox",
                firefox_dir / "Firefox.app" / "Contents" / "MacOS" / "firefox",
                firefox_dir / "Nightly.app" / "Contents" / "MacOS" / "firefox",
            ]
        elif self.is_windows:
            # Windows: firefox.exe
            candidates = [
                firefox_dir / "firefox" / "firefox.exe",
                firefox_dir / "firefox.exe",
            ]
        else:
            # Linux: firefox 二进制文件
            candidates = [
                firefox_dir / "firefox" / "firefox",
                firefox_dir / "firefox",
            ]
        
        for candidate in candidates:
            if candidate.exists() and candidate.is_file():
                return candidate
        
        return None
    
    def _extract_version_from_path(self, path: str) -> str:
        """从路径中提取版本号"""
        import re
        
        # 匹配 firefox-1488 这样的模式
        match = re.search(r'firefox-(\d+)', path)
        if match:
            return match.group(1)
        
        return "0"
    
    def _get_firefox_from_playwright_command(self) -> Optional[str]:
        """使用 playwright 命令获取 Firefox 路径"""
        try:
            # 运行 playwright 命令获取浏览器信息
            result = subprocess.run(
                ["playwright", "show-trace", "--help"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # 这只是为了验证 playwright 命令可用
            if result.returncode == 0:
                # 实际上我们无法直接从 playwright 命令获取浏览器路径
                # 但可以确认 playwright 已安装
                pass
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        return None
    
    def _select_latest_firefox(self, firefox_paths: List[Tuple[str, str]]) -> Optional[str]:
        """选择最新版本的 Firefox"""
        if not firefox_paths:
            return None
        
        # 验证每个路径并选择第一个有效的
        for firefox_path, version in firefox_paths:
            if self._verify_firefox(firefox_path):
                print(f"  版本: firefox-{version}")
                return firefox_path
        
        return None
    
    def _verify_firefox(self, firefox_path: str) -> bool:
        """验证 Firefox 是否可用"""
        firefox_file = Path(firefox_path)
        
        if not firefox_file.exists():
            return False
        
        if not firefox_file.is_file():
            return False
        
        # macOS 的 Firefox 启动器较小，但仍然可用
        # 检查文件大小（启动器至少要有 10KB）
        if firefox_file.stat().st_size < 10 * 1024:
            return False
        
        # 检查执行权限（Unix 系统）
        if not self.is_windows:
            if not os.access(firefox_path, os.X_OK):
                # 尝试添加执行权限
                try:
                    os.chmod(firefox_path, 0o755)
                    return True
                except:
                    return False
        
        return True
    
    def get_firefox_info(self, firefox_path: str) -> dict:
        """获取 Firefox 详细信息"""
        info = {
            "path": firefox_path,
            "exists": False,
            "size_mb": 0,
            "version": "unknown",
            "app_dir": None,
        }
        
        firefox_file = Path(firefox_path)
        if firefox_file.exists():
            info["exists"] = True
            info["size_mb"] = firefox_file.stat().st_size / (1024 * 1024)
            info["version"] = self._extract_version_from_path(firefox_path)
            
            # 获取应用目录（包含所有相关文件的目录）
            if self.is_mac:
                # macOS: 获取 .app 目录
                for parent in firefox_file.parents:
                    if parent.name.endswith('.app'):
                        info["app_dir"] = str(parent.parent)
                        break
            else:
                # Windows/Linux: 获取包含 firefox 的目录
                info["app_dir"] = str(firefox_file.parent)
        
        return info


def find_firefox() -> Optional[str]:
    """查找 Firefox 的便捷函数"""
    finder = FirefoxFinder()
    return finder.find_playwright_firefox()


def main():
    """测试 Firefox 查找"""
    print("🦊 Firefox 查找器测试")
    print("=" * 60)
    
    finder = FirefoxFinder()
    firefox_path = finder.find_playwright_firefox()
    
    if firefox_path:
        print(f"\n✅ 找到 Firefox: {firefox_path}")
        
        # 获取详细信息
        info = finder.get_firefox_info(firefox_path)
        print(f"\n📋 Firefox 信息:")
        print(f"  路径: {info['path']}")
        print(f"  存在: {info['exists']}")
        print(f"  大小: {info['size_mb']:.1f} MB")
        print(f"  版本: firefox-{info['version']}")
        print(f"  应用目录: {info['app_dir']}")
        
        # 用于 PyInstaller 打包
        if info['app_dir']:
            print(f"\n📦 PyInstaller 数据项:")
            print(f'  ("{info["app_dir"]}", "browsers/firefox")')
    else:
        print("\n❌ 未找到 Firefox")
        print("\n💡 请运行以下命令安装 Firefox:")
        print("  playwright install firefox")


if __name__ == "__main__":
    main()
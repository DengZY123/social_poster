#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能路径检测器
自动检测运行环境（开发/打包），提供正确的资源路径
"""
import os
import sys
import platform
from pathlib import Path
from typing import Optional, Dict, Any

class PathDetector:
    """路径检测器 - 智能适配开发和打包环境"""
    
    def __init__(self):
        self._is_frozen = getattr(sys, 'frozen', False)
        self._is_bundle = getattr(sys, '_MEIPASS', None) is not None
        self._platform = platform.system().lower()
        
        # 缓存路径结果
        self._cache = {}
    
    @property
    def is_packaged(self) -> bool:
        """检查是否为打包后的应用"""
        return self._is_frozen or self._is_bundle
    
    @property
    def is_development(self) -> bool:
        """检查是否为开发环境"""
        return not self.is_packaged
    
    @property
    def platform_name(self) -> str:
        """获取平台名称"""
        return self._platform
    
    def get_base_dir(self) -> Path:
        """获取应用基础目录"""
        if 'base_dir' in self._cache:
            return self._cache['base_dir']
        
        if self.is_packaged:
            # 打包环境 - 使用PyInstaller的临时目录
            base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent.parent.parent))
        else:
            # 开发环境 - 使用项目根目录
            base_dir = Path(__file__).parent.parent.parent
        
        self._cache['base_dir'] = base_dir.resolve()
        return self._cache['base_dir']
    
    def get_firefox_path(self) -> Optional[str]:
        """获取Firefox浏览器路径"""
        if 'firefox_path' in self._cache:
            return self._cache['firefox_path']
        
        firefox_path = None
        
        if self.is_packaged:
            # 打包环境 - 使用内置Firefox
            base_dir = self.get_base_dir()
            
            # 定义可能的Firefox路径
            possible_paths = []
            
            if self._platform == "darwin":  # macOS
                # 在 macOS 的 .app 包中，PyInstaller 将数据文件放在 Resources 目录
                # 获取 Resources 目录路径
                if base_dir.name == "MacOS" and base_dir.parent.name == "Contents":
                    # 我们在 .app 包内
                    resources_dir = base_dir.parent / "Resources"
                else:
                    resources_dir = base_dir.parent / "Resources"
                
                possible_paths.extend([
                    # PyInstaller 标准位置 - Resources 目录
                    resources_dir / "browsers" / "firefox" / "Nightly.app" / "Contents" / "MacOS" / "firefox",
                    resources_dir / "browsers" / "firefox" / "Firefox.app" / "Contents" / "MacOS" / "firefox",
                    # 旧的位置（兼容性）
                    base_dir / "browsers" / "firefox" / "Nightly.app" / "Contents" / "MacOS" / "firefox",
                    base_dir / "browsers" / "firefox" / "Firefox.app" / "Contents" / "MacOS" / "firefox",
                    # 其他可能的位置
                    base_dir.parent / "Frameworks" / "browsers" / "firefox" / "Nightly.app" / "Contents" / "MacOS" / "firefox",
                ])
            elif self._platform == "windows":  # Windows
                possible_paths.extend([
                    base_dir / "browsers" / "firefox" / "firefox.exe",
                    base_dir / "_internal" / "browsers" / "firefox" / "firefox.exe",
                    base_dir / "browsers" / "firefox" / "firefox" / "firefox.exe",
                ])
            else:  # Linux
                possible_paths.extend([
                    base_dir / "browsers" / "firefox" / "firefox",
                    base_dir / "_internal" / "browsers" / "firefox" / "firefox",
                    base_dir / "browsers" / "firefox" / "firefox" / "firefox",
                ])
            
            # 尝试每个可能的路径
            print(f"🔍 在打包环境中查找 Firefox...")
            print(f"  基础目录: {base_dir}")
            print(f"  基础目录存在: {base_dir.exists()}")
            
            # 打印 Resources 目录信息
            if base_dir.name == "MacOS" and base_dir.parent.name == "Contents":
                resources_dir = base_dir.parent / "Resources"
                print(f"  Resources 目录: {resources_dir}")
                print(f"  Resources 目录存在: {resources_dir.exists()}")
                
                # 列出 Resources 目录内容
                if resources_dir.exists():
                    browsers_dir = resources_dir / "browsers"
                    if browsers_dir.exists():
                        print(f"  browsers 目录存在: {browsers_dir}")
                        # 列出 browsers 目录内容
                        for item in browsers_dir.iterdir():
                            print(f"    - {item.name}")
            
            for path in possible_paths:
                print(f"  检查路径: {path}")
                print(f"    存在: {path.exists()}")
                print(f"    是文件: {path.is_file() if path.exists() else 'N/A'}")
                if path.exists() and path.is_file():
                    firefox_path = str(path)
                    print(f"✅ 找到内置 Firefox: {firefox_path}")
                    break
            
            if not firefox_path:
                print(f"⚠️ 未找到内置 Firefox")
                print(f"  基础目录: {base_dir}")
                print(f"  尝试的路径数: {len(possible_paths)}")
        else:
            # 开发环境 - 让Playwright自动管理
            print("🔧 开发环境 - Firefox 由 Playwright 自动管理")
            firefox_path = None
        
        self._cache['firefox_path'] = firefox_path
        return firefox_path
    
    def get_user_data_dir(self) -> Path:
        """获取用户数据目录"""
        if 'user_data_dir' in self._cache:
            return self._cache['user_data_dir']
        
        if self.is_packaged:
            # 打包环境 - 使用用户目录下的应用数据文件夹
            if self._platform == "darwin":  # macOS
                user_data_dir = Path.home() / "Library" / "Application Support" / "XhsPublisher"
            elif self._platform == "windows":  # Windows
                user_data_dir = Path.home() / "AppData" / "Local" / "XhsPublisher"
            else:  # Linux
                user_data_dir = Path.home() / ".config" / "XhsPublisher"
        else:
            # 开发环境 - 使用项目目录下的firefox_profile
            user_data_dir = self.get_base_dir() / "firefox_profile"
        
        # 确保目录存在
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        self._cache['user_data_dir'] = user_data_dir
        return user_data_dir
    
    def get_config_dir(self) -> Path:
        """获取配置文件目录 - 强制使用用户目录确保权限"""
        if 'config_dir' in self._cache:
            return self._cache['config_dir']
        
        # 强制使用用户目录，避免权限问题
        if self._platform == "darwin":  # macOS
            config_dir = Path.home() / "Library" / "Application Support" / "XhsPublisher" / "config"
        elif self._platform == "windows":  # Windows
            config_dir = Path.home() / "AppData" / "Local" / "XhsPublisher" / "config"
        else:  # Linux
            config_dir = Path.home() / ".config" / "XhsPublisher"
        
        config_dir.mkdir(parents=True, exist_ok=True)
        self._cache['config_dir'] = config_dir
        return config_dir
    
    def get_logs_dir(self) -> Path:
        """获取日志目录 - 强制使用用户目录确保权限"""
        if 'logs_dir' in self._cache:
            return self._cache['logs_dir']
        
        # 强制使用用户目录，避免权限问题
        if self._platform == "darwin":  # macOS
            logs_dir = Path.home() / "Library" / "Application Support" / "XhsPublisher" / "logs"
        elif self._platform == "windows":  # Windows
            logs_dir = Path.home() / "AppData" / "Local" / "XhsPublisher" / "logs"
        else:  # Linux
            logs_dir = Path.home() / ".config" / "XhsPublisher" / "logs"
        
        logs_dir.mkdir(parents=True, exist_ok=True)
        self._cache['logs_dir'] = logs_dir
        return logs_dir
    
    def get_temp_dir(self) -> Path:
        """获取临时文件目录 - 强制使用系统临时目录确保权限"""
        if 'temp_dir' in self._cache:
            return self._cache['temp_dir']
        
        # 强制使用系统临时目录，避免权限问题
        import tempfile
        temp_dir = Path(tempfile.gettempdir()) / "XhsPublisher"
        
        temp_dir.mkdir(parents=True, exist_ok=True)
        self._cache['temp_dir'] = temp_dir
        return temp_dir
    
    def get_resource_path(self, resource_name: str) -> Path:
        """获取资源文件路径"""
        cache_key = f"resource_{resource_name}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        base_dir = self.get_base_dir()
        
        if self.is_packaged:
            # 打包环境 - 资源文件在应用包内
            resource_path = base_dir / "resources" / resource_name
        else:
            # 开发环境 - 资源文件在项目目录
            resource_path = base_dir / resource_name
        
        self._cache[cache_key] = resource_path
        return resource_path
    
    def get_tasks_file_path(self) -> Path:
        """获取任务文件路径"""
        return self.get_config_dir() / "tasks.json"
    
    def get_config_file_path(self) -> Path:
        """获取配置文件路径"""
        return self.get_config_dir() / "config.json"
    
    def get_log_file_path(self) -> Path:
        """获取日志文件路径"""
        return self.get_logs_dir() / "app.log"
    
    def get_playwright_config(self) -> Dict[str, Any]:
        """获取Playwright配置"""
        config = {
            "user_data_dir": str(self.get_user_data_dir()),
            "downloads_path": str(self.get_temp_dir() / "downloads"),
        }
        
        # Firefox路径配置
        firefox_path = self.get_firefox_path()
        if firefox_path:
            config["executable_path"] = firefox_path
        
        return config
    
    def get_environment_info(self) -> Dict[str, Any]:
        """获取环境信息"""
        return {
            "is_packaged": self.is_packaged,
            "is_development": self.is_development,
            "platform": self.platform_name,
            "python_executable": sys.executable,
            "base_dir": str(self.get_base_dir()),
            "user_data_dir": str(self.get_user_data_dir()),
            "config_dir": str(self.get_config_dir()),
            "logs_dir": str(self.get_logs_dir()),
            "firefox_path": self.get_firefox_path(),
        }
    
    def validate_environment(self) -> Dict[str, bool]:
        """验证环境配置"""
        validation = {}
        
        # 检查基础目录
        validation["base_dir_exists"] = self.get_base_dir().exists()
        
        # 检查用户数据目录
        validation["user_data_dir_exists"] = self.get_user_data_dir().exists()
        
        # 检查配置目录
        validation["config_dir_exists"] = self.get_config_dir().exists()
        
        # 检查日志目录
        validation["logs_dir_exists"] = self.get_logs_dir().exists()
        
        # 检查Firefox（仅在打包环境）
        if self.is_packaged:
            firefox_path = self.get_firefox_path()
            validation["firefox_available"] = firefox_path is not None and Path(firefox_path).exists()
        else:
            validation["firefox_available"] = True  # 开发环境由Playwright管理
        
        return validation


# 全局路径检测器实例
path_detector = PathDetector()


def get_app_paths() -> Dict[str, str]:
    """获取应用所有路径的便捷函数"""
    return {
        "base_dir": str(path_detector.get_base_dir()),
        "user_data_dir": str(path_detector.get_user_data_dir()),
        "config_dir": str(path_detector.get_config_dir()),
        "logs_dir": str(path_detector.get_logs_dir()),
        "temp_dir": str(path_detector.get_temp_dir()),
        "tasks_file": str(path_detector.get_tasks_file_path()),
        "config_file": str(path_detector.get_config_file_path()),
        "log_file": str(path_detector.get_log_file_path()),
    }


def main():
    """测试路径检测器"""
    print("🔍 路径检测器测试")
    print("=" * 50)
    
    detector = PathDetector()
    
    # 显示环境信息
    print("\n📋 环境信息:")
    env_info = detector.get_environment_info()
    for key, value in env_info.items():
        print(f"  {key}: {value}")
    
    # 显示路径信息
    print("\n📁 路径配置:")
    paths = get_app_paths()
    for key, value in paths.items():
        print(f"  {key}: {value}")
    
    # 验证环境
    print("\n✅ 环境验证:")
    validation = detector.validate_environment()
    for key, value in validation.items():
        status = "✅" if value else "❌"
        print(f"  {status} {key}: {value}")
    
    # Playwright配置
    print("\n🎭 Playwright配置:")
    playwright_config = detector.get_playwright_config()
    for key, value in playwright_config.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
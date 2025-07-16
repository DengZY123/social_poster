#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置适配器
为打包后的应用提供配置适配和路径管理
"""
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加项目路径到sys.path（确保能导入项目模块）
def setup_python_path():
    """设置Python路径，确保能导入项目模块"""
    # 获取应用基础目录
    if getattr(sys, 'frozen', False):
        # 打包环境
        base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
    else:
        # 开发环境
        base_dir = Path(__file__).parent.parent
    
    # 添加到sys.path
    if str(base_dir) not in sys.path:
        sys.path.insert(0, str(base_dir))
    
    return base_dir

# 设置路径
BASE_DIR = setup_python_path()

# 导入路径检测器
try:
    from packaging.scripts.path_detector import path_detector
except ImportError:
    try:
        # 尝试从scripts目录导入
        from scripts.path_detector import path_detector
    except ImportError:
        # 如果在打包环境中，可能路径不同
        sys.path.insert(0, str(BASE_DIR / "packaging" / "scripts"))
        from path_detector import path_detector

# 导入项目模块
from core.models import AppConfig

class PackagedAppConfig:
    """打包应用配置管理器"""
    
    def __init__(self):
        self.path_detector = path_detector
        self._app_config = None
    
    def get_app_config(self) -> AppConfig:
        """获取适配后的应用配置"""
        if self._app_config is None:
            self._app_config = self._create_adapted_config()
        return self._app_config
    
    def _create_adapted_config(self) -> AppConfig:
        """创建适配打包环境的配置"""
        # 获取路径
        firefox_profile_path = str(self.path_detector.get_user_data_dir())
        tasks_file_path = str(self.path_detector.get_tasks_file_path())
        log_file_path = str(self.path_detector.get_log_file_path())
        
        # 创建配置
        config = AppConfig(
            firefox_profile_path=firefox_profile_path,
            tasks_file_path=tasks_file_path,
            log_file_path=log_file_path,
            check_interval_seconds=60,
            publish_timeout_seconds=300,
            min_publish_interval_minutes=5,
            headless_mode=False,  # 用户版本默认显示界面
            browser_launch_timeout=90,
            page_load_timeout=60
        )
        
        return config
    
    def setup_logging(self):
        """设置日志配置"""
        from loguru import logger
        
        # 移除默认处理器
        logger.remove()
        
        # 控制台日志（简化）
        logger.add(
            sys.stderr,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
            colorize=True
        )
        
        # 文件日志
        log_file = self.path_detector.get_log_file_path()
        logger.add(
            str(log_file),
            level="DEBUG",
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8"
        )
        
        logger.info(f"📋 日志系统初始化完成，日志文件: {log_file}")
        return logger
    
    def setup_environment(self):
        """设置运行环境"""
        # 创建必要的目录
        self.path_detector.get_user_data_dir()
        self.path_detector.get_config_dir()
        self.path_detector.get_logs_dir()
        self.path_detector.get_temp_dir()
        
        # 设置环境变量
        os.environ['XHS_PUBLISHER_DATA_DIR'] = str(self.path_detector.get_user_data_dir())
        os.environ['XHS_PUBLISHER_CONFIG_DIR'] = str(self.path_detector.get_config_dir())
        
        # Playwright环境变量配置
        if self.path_detector.is_packaged:
            # 检查是否有内置的 Firefox
            firefox_path = self.path_detector.get_firefox_path()
            if firefox_path:
                # 有内置 Firefox，直接使用
                print(f"🦊 使用内置 Firefox: {firefox_path}")
                # 清除可能存在的环境变量，避免冲突
                for env_var in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_DRIVER_PATH', 'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD']:
                    if env_var in os.environ:
                        del os.environ[env_var]
            else:
                # 没有内置 Firefox，使用Playwright默认路径
                print("⚠️ 未找到内置 Firefox，使用Playwright默认浏览器路径")
                # 确保移除所有可能干扰的环境变量
                for env_var in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_DRIVER_PATH', 'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD']:
                    if env_var in os.environ:
                        del os.environ[env_var]
                        print(f"  清除环境变量: {env_var}")
                
                # 让Playwright使用系统默认路径
                print(f"  默认浏览器路径: {self._get_default_playwright_path()}")
        else:
            # 开发环境中清理环境变量
            for env_var in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_DRIVER_PATH', 'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD']:
                if env_var in os.environ:
                    del os.environ[env_var]
    
    def _get_default_playwright_path(self) -> str:
        """获取Playwright默认浏览器路径"""
        import platform
        if platform.system() == "Darwin":  # macOS
            return str(Path.home() / "Library" / "Caches" / "ms-playwright")
        elif platform.system() == "Windows":
            return str(Path.home() / "AppData" / "Local" / "ms-playwright")
        else:  # Linux
            return str(Path.home() / ".cache" / "ms-playwright")
    
    def get_firefox_launch_config(self) -> dict:
        """获取Firefox启动配置"""
        import os
        import json
        from pathlib import Path
        
        firefox_found = False
        firefox_executable = None
        
        if sys.platform == "darwin":
            # macOS - 使用写死的路径
            firefox_path = Path("/Users/dzy/Library/Caches/ms-playwright/firefox-1488/firefox/Nightly.app/Contents/MacOS/firefox")
            
            print(f"[检测] 检查写死的Firefox路径: {firefox_path}")
            print(f"[检测] 路径存在: {firefox_path.exists()}")
            
            if firefox_path.exists():
                firefox_found = True
                firefox_executable = str(firefox_path)
                print(f"✅ 找到Firefox可执行文件: {firefox_executable}")
                
                # 清除所有可能的环境变量
                for env_var in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_DRIVER_PATH']:
                    if env_var in os.environ:
                        del os.environ[env_var]
                        print(f"🧹 清除环境变量: {env_var}")
            else:
                # 如果写死的路径不存在，尝试其他可能的路径
                possible_paths = [
                    Path.home() / "Library" / "Caches" / "ms-playwright" / "firefox-1488" / "firefox" / "Nightly.app" / "Contents" / "MacOS" / "firefox",
                    Path.home() / "Library" / "Caches" / "ms-playwright" / "firefox-1488" / "Firefox.app" / "Contents" / "MacOS" / "firefox",
                    Path.home() / "Library" / "Caches" / "ms-playwright" / "firefox-1488" / "firefox" / "Firefox.app" / "Contents" / "MacOS" / "firefox",
                ]
                
                for path in possible_paths:
                    print(f"[检测] 尝试路径: {path}")
                    if path.exists():
                        firefox_found = True
                        firefox_executable = str(path)
                        print(f"✅ 找到Firefox: {firefox_executable}")
                        break
                        
        elif sys.platform == "win32":
            # Windows - 从配置文件读取
            config_dir = Path.home() / "AppData" / "Local" / "XhsPublisher"
            
            # 1. 尝试读取JSON配置
            json_config = config_dir / "browser_config.json"
            if json_config.exists():
                try:
                    with open(json_config, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                        firefox_path = config.get('firefox_path')
                        if firefox_path and Path(firefox_path).exists():
                            firefox_found = True
                            firefox_executable = firefox_path
                            print(f"✅ 从配置文件读取Firefox路径: {firefox_executable}")
                except Exception as e:
                    print(f"⚠️ 读取JSON配置失败: {e}")
            
            # 2. 尝试读取文本配置（备用）
            if not firefox_found:
                txt_config = config_dir / "firefox_path.txt"
                if txt_config.exists():
                    try:
                        firefox_path = txt_config.read_text(encoding='utf-8').strip()
                        if firefox_path and Path(firefox_path).exists():
                            firefox_found = True
                            firefox_executable = firefox_path
                            print(f"✅ 从文本配置读取Firefox路径: {firefox_executable}")
                    except Exception as e:
                        print(f"⚠️ 读取文本配置失败: {e}")
            
            # 3. 尝试自动检测
            if not firefox_found:
                playwright_path = Path.home() / "AppData" / "Local" / "ms-playwright"
                if playwright_path.exists():
                    # 查找最新的firefox目录
                    firefox_dirs = sorted(playwright_path.glob("firefox-*"), reverse=True)
                    for firefox_dir in firefox_dirs:
                        exe_path = firefox_dir / "firefox" / "firefox.exe"
                        if exe_path.exists():
                            firefox_found = True
                            firefox_executable = str(exe_path)
                            print(f"✅ 自动检测到Firefox: {firefox_executable}")
                            break
            
            if not firefox_found:
                print("❌ 未找到Firefox浏览器")
                print("💡 请运行 windows_setup\\install.bat 安装Firefox")
                raise Exception("浏览器未安装：请运行 install.bat 安装Firefox浏览器")
        
        else:
            # Linux
            print("❌ Linux系统暂不支持")
            raise Exception("Linux系统暂不支持")
        
        if not firefox_found:
            print("❌ 未找到Firefox浏览器")
            raise Exception("浏览器未安装：请安装Firefox浏览器后重试")
        
        config = {
            "user_data_dir": str(self.path_detector.get_user_data_dir()),
            "headless": False,
            "viewport": {"width": 1366, "height": 768},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
            "timeout": 90000,  # 增加启动超时时间
            "args": ['--no-sandbox'],  # 添加安全参数
        }
        
        # 使用写死的Firefox路径
        if firefox_executable:
            config["executable_path"] = firefox_executable
            print(f"🦊 配置使用Firefox: {firefox_executable}")
        
        # 添加Firefox偏好设置
        config["firefox_user_prefs"] = {
            "dom.webdriver.enabled": False,
            "useAutomationExtension": False,
            "general.platform.override": "MacIntel",
            "browser.search.suggest.enabled": False,
            "browser.search.update": False,
            "services.sync.engine.prefs": False,
            "datareporting.policy.dataSubmissionEnabled": False,
            "datareporting.healthreport.uploadEnabled": False,
            "toolkit.telemetry.enabled": False,
            "browser.ping-centre.telemetry": False,
            "app.shield.optoutstudies.enabled": False,
            "app.normandy.enabled": False,
            "breakpad.reportURL": "",
            "browser.tabs.crashReporting.sendReport": False,
            "browser.crashReports.unsubmittedCheck.autoSubmit2": False,
            "network.captive-portal-service.enabled": False
        }
        
        return config
    
    def validate_installation(self) -> dict:
        """验证应用安装"""
        validation = self.path_detector.validate_environment()
        
        # 额外检查
        validation["playwright_available"] = self._check_playwright()
        validation["config_writable"] = self._check_config_writable()
        
        return validation
    
    def _check_playwright(self) -> bool:
        """检查Playwright是否可用"""
        try:
            from playwright.async_api import async_playwright
            return True
        except ImportError:
            return False
    
    def _check_config_writable(self) -> bool:
        """检查配置目录是否可写"""
        try:
            config_dir = self.path_detector.get_config_dir()
            test_file = config_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except Exception:
            return False
    
    # 已禁用自动下载浏览器功能
    # def _check_and_install_browsers(self, browsers_path: Path):
    #     """检查并安装 Playwright 浏览器（已禁用）"""
    #     pass
    
    def show_environment_info(self):
        """显示环境信息（调试用）"""
        print("[检测] 应用环境信息")
        print("=" * 50)
        
        env_info = self.path_detector.get_environment_info()
        for key, value in env_info.items():
            print(f"  {key}: {value}")
        
        print("\n✅ 环境验证:")
        validation = self.validate_installation()
        for key, value in validation.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")


# 全局配置实例
app_config_manager = PackagedAppConfig()

def get_app_config() -> AppConfig:
    """获取应用配置的便捷函数"""
    return app_config_manager.get_app_config()

def setup_packaged_app():
    """设置打包应用的便捷函数"""
    # 设置环境
    app_config_manager.setup_environment()
    
    # 设置日志
    logger = app_config_manager.setup_logging()
    
    # 获取配置
    config = app_config_manager.get_app_config()
    
    logger.info("🚀 打包应用初始化完成")
    logger.info(f"📁 用户数据目录: {config.firefox_profile_path}")
    logger.info(f"📝 任务文件: {config.tasks_file_path}")
    
    return config, logger

def main():
    """测试配置适配器"""
    print("⚙️ 应用配置适配器测试")
    app_config_manager.show_environment_info()
    
    print("\n📋 应用配置:")
    config = get_app_config()
    config_dict = config.to_dict()
    for key, value in config_dict.items():
        print(f"  {key}: {value}")
    
    print("\n🦊 Firefox配置:")
    firefox_config = app_config_manager.get_firefox_launch_config()
    for key, value in firefox_config.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    main()
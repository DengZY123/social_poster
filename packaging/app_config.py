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
        
        # Playwright环境变量（改进版）
        if self.path_detector.is_packaged:
            # 检查是否有内置的 Firefox
            firefox_path = self.path_detector.get_firefox_path()
            if firefox_path:
                # 有内置 Firefox，不设置 PLAYWRIGHT_BROWSERS_PATH，直接使用可执行文件路径
                print(f"🦊 使用内置 Firefox: {firefox_path}")
                # 清除可能存在的环境变量，避免冲突
                for env_var in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_DRIVER_PATH', 'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD']:
                    if env_var in os.environ:
                        del os.environ[env_var]
            else:
                # 没有内置 Firefox，使用下载模式
                print("🔍 未找到内置 Firefox，将在首次运行时下载")
                browsers_path = self.path_detector.get_user_data_dir() / "playwright-browsers"
                
                # 设置多个 Playwright 相关的环境变量确保路径被正确识别
                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(browsers_path)
                os.environ['PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD'] = '0'  # 允许下载浏览器
                
                # 强制清除可能存在的其他 Playwright 路径设置
                if 'PLAYWRIGHT_DRIVER_PATH' in os.environ:
                    del os.environ['PLAYWRIGHT_DRIVER_PATH']
                
                # 检查是否需要安装浏览器
                self._check_and_install_browsers(browsers_path)
        else:
            # 开发环境中也确保清理环境变量
            for env_var in ['PLAYWRIGHT_BROWSERS_PATH', 'PLAYWRIGHT_DRIVER_PATH', 'PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD']:
                if env_var in os.environ:
                    del os.environ[env_var]
    
    def get_firefox_launch_config(self) -> dict:
        """获取Firefox启动配置"""
        config = {
            "user_data_dir": str(self.path_detector.get_user_data_dir()),
            "headless": False,
            "viewport": {"width": 1366, "height": 768},
            "locale": "zh-CN",
            "timezone_id": "Asia/Shanghai",
        }
        
        # 在打包环境中，优先使用内置 Firefox
        if self.path_detector.is_packaged:
            firefox_path = self.path_detector.get_firefox_path()
            if firefox_path:
                config["executable_path"] = firefox_path
                print(f"🦊 配置使用内置 Firefox: {firefox_path}")
            # 如果没有内置 Firefox，则依赖 PLAYWRIGHT_BROWSERS_PATH 环境变量
        else:
            # 开发环境中让 Playwright 自动管理浏览器
            firefox_path = self.path_detector.get_firefox_path()
            if firefox_path:
                config["executable_path"] = firefox_path
        
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
    
    def _check_and_install_browsers(self, browsers_path: Path):
        """检查并安装 Playwright 浏览器"""
        try:
            from loguru import logger
            
            # 确保浏览器目录存在
            browsers_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 浏览器目录: {browsers_path}")
            
            # 检查 Firefox 是否已安装
            firefox_marker = browsers_path / "firefox-installed.marker"
            
            # 简单检查：如果标记文件存在且最近30天内创建，则认为已安装
            if firefox_marker.exists():
                try:
                    marker_time = datetime.fromisoformat(firefox_marker.read_text().strip())
                    days_since_install = (datetime.now() - marker_time).days
                    if days_since_install < 30:  # 30天内安装的认为有效
                        logger.info(f"✅ Firefox 浏览器已安装 ({days_since_install}天前)")
                        return
                    else:
                        logger.info(f"🔄 Firefox 安装已过期 ({days_since_install}天前)，重新安装...")
                except (ValueError, FileNotFoundError):
                    logger.info("🔄 无效的安装标记，重新安装...")
            
            logger.info("🔍 检测到首次运行或需要重新安装，开始安装 Firefox 浏览器...")
            
            # 使用 subprocess 安装 Firefox
            import subprocess
            try:
                # 设置环境变量确保安装到正确位置
                env = os.environ.copy()
                env['PLAYWRIGHT_BROWSERS_PATH'] = str(browsers_path)
                
                # 构建安装命令
                install_cmd = [sys.executable, "-m", "playwright", "install", "firefox"]
                logger.info(f"🚀 执行安装命令: {' '.join(install_cmd)}")
                logger.info(f"📍 安装环境变量 PLAYWRIGHT_BROWSERS_PATH: {env.get('PLAYWRIGHT_BROWSERS_PATH')}")
                
                # 运行 playwright install firefox
                result = subprocess.run(
                    install_cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600,  # 10分钟超时
                    cwd=str(self.path_detector.get_base_dir())  # 设置工作目录
                )
                
                # 记录详细的输出信息
                if result.stdout:
                    logger.info(f"📤 安装输出: {result.stdout}")
                if result.stderr:
                    logger.info(f"📥 安装错误流: {result.stderr}")
                
                if result.returncode == 0:
                    logger.info("✅ Firefox 浏览器安装成功")
                    
                    # 验证安装结果
                    firefox_dirs = list(browsers_path.glob("firefox-*"))
                    if firefox_dirs:
                        logger.info(f"🦊 找到 Firefox 目录: {[d.name for d in firefox_dirs]}")
                        
                        # 创建标记文件
                        firefox_marker.write_text(datetime.now().isoformat())
                        logger.info("✅ 创建安装标记文件")
                    else:
                        logger.warning("⚠️ 安装完成但未找到 Firefox 目录，可能安装到了其他位置")
                        # 仍然创建标记文件，避免重复安装
                        firefox_marker.write_text(datetime.now().isoformat())
                else:
                    logger.error(f"❌ Firefox 安装失败，返回码: {result.returncode}")
                    logger.error(f"❌ 错误输出: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error("❌ Firefox 安装超时（10分钟）")
            except FileNotFoundError:
                logger.error("❌ 未找到 playwright 命令，请检查 Playwright 是否正确安装")
            except Exception as e:
                logger.error(f"❌ Firefox 安装出错: {e}")
                
        except Exception as e:
            print(f"❌ 检查浏览器时出错: {e}")
            # 不要因为浏览器安装失败而阻止应用启动
            logger.error(f"❌ 浏览器安装过程异常: {e}")
            logger.info("💡 提示：如果持续出现此问题，请尝试手动执行 'playwright install firefox'")
    
    def show_environment_info(self):
        """显示环境信息（调试用）"""
        print("🔍 应用环境信息")
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
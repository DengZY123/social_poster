#!/usr/bin/env python3
"""
小红书定时发布工具 - 简单版
主程序入口
"""
import sys
import argparse
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from gui.main_window import MainWindow


def setup_logging(debug: bool = False):
    """设置日志"""
    logger.remove()  # 移除默认处理器
    
    # 控制台日志
    log_level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
        colorize=True
    )
    
    # 文件日志
    logger.add(
        "app.log",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} | {message}",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8"
    )
    
    logger.info("✅ 日志系统初始化完成")


def check_dependencies():
    """检查依赖"""
    try:
        import playwright
        logger.info("✅ Playwright 依赖检查通过")
    except ImportError:
        logger.error("❌ 缺少 Playwright 依赖")
        QMessageBox.critical(
            None, 
            "依赖错误", 
            "缺少 Playwright 依赖\n\n请执行以下命令安装：\npip install playwright\nplaywright install firefox"
        )
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            # 检查Firefox是否已安装
            try:
                browser = p.firefox.launch(headless=True)
                browser.close()
                logger.info("✅ Firefox 浏览器检查通过")
            except Exception as e:
                logger.error(f"❌ Firefox 浏览器检查失败: {e}")
                QMessageBox.critical(
                    None,
                    "浏览器错误",
                    "Firefox 浏览器未正确安装\n\n请执行以下命令：\nplaywright install firefox"
                )
                return False
    except Exception as e:
        logger.error(f"❌ 浏览器依赖检查失败: {e}")
        return False
    
    return True


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description="小红书定时发布工具 - 简单版",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python main.py                # 正常启动
  python main.py --debug        # 调试模式
  python main.py --headless     # 无头模式（发布时不显示浏览器）
        """
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="启用调试模式"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="无头模式（发布时不显示浏览器窗口）"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="小红书定时发布工具 - 简单版 v1.0.0"
    )
    
    return parser.parse_args()


def create_application():
    """创建QApplication"""
    app = QApplication(sys.argv)
    
    # 设置应用属性
    app.setApplicationName("小红书定时发布工具")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("XHS Publisher")
    
    # 设置高DPI支持（兼容不同PyQt6版本）
    try:
        app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
    except AttributeError:
        # 较新版本的PyQt6可能不需要这些属性或使用不同的方式
        pass
    
    return app


def show_startup_info():
    """显示启动信息"""
    logger.info("=" * 50)
    logger.info("🚀 小红书定时发布工具 - 简单版")
    logger.info("版本: 1.0.0")
    logger.info("=" * 50)
    logger.info("📋 功能特点：")
    logger.info("  ✅ 零死锁风险 - 使用QTimer + subprocess")
    logger.info("  ✅ 易于使用 - 直观的GUI界面")
    logger.info("  ✅ 完全隔离 - 浏览器操作在独立进程")
    logger.info("  ✅ 定时发布 - 支持精确到分钟的定时")
    logger.info("  ✅ 任务管理 - 实时查看任务状态")
    logger.info("=" * 50)


def main():
    """主函数"""
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 设置日志
        setup_logging(args.debug)
        
        # 显示启动信息
        show_startup_info()
        
        # 检查依赖
        logger.info("[检测] 检查运行环境...")
        if not check_dependencies():
            return 1
        
        # 创建应用
        logger.info("🎨 创建应用界面...")
        app = create_application()
        
        # 创建主窗口
        logger.info("🏠 初始化主窗口...")
        window = MainWindow()
        
        # 如果指定了无头模式，更新配置
        if args.headless:
            window.scheduler.config_storage.update_config(headless_mode=True)
            logger.info("🔧 已启用无头模式")
        
        # 显示窗口
        window.show()
        
        logger.info("✅ 应用启动完成")
        logger.info("💡 使用提示：")
        logger.info("  - 首次使用请先登录小红书账号")
        logger.info("  - 支持立即发布和定时发布")
        logger.info("  - 任务列表实时显示执行状态")
        logger.info("  - 可以选择多张图片进行发布")
        
        # 运行应用
        return app.exec()
        
    except KeyboardInterrupt:
        logger.info("👋 用户中断，正在退出...")
        return 0
    except Exception as e:
        logger.error(f"❌ 应用启动失败: {e}")
        import traceback
        logger.error(f"错误详情:\n{traceback.format_exc()}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
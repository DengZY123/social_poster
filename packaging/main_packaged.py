#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书发布工具 - 打包版本主入口
适配打包环境，处理路径和依赖问题
"""
import sys
import os
from pathlib import Path

def setup_packaged_environment():
    """设置打包环境"""
    # 获取应用基础路径
    if getattr(sys, 'frozen', False):
        # 打包环境
        base_path = Path(sys._MEIPASS)
        app_path = Path(sys.executable).parent
    else:
        # 开发环境
        base_path = Path(__file__).parent.parent
        app_path = base_path
    
    # 添加项目路径到sys.path
    sys.path.insert(0, str(base_path))
    
    # 设置环境变量
    os.environ['XHS_PUBLISHER_BASE_PATH'] = str(base_path)
    os.environ['XHS_PUBLISHER_APP_PATH'] = str(app_path)
    
    return base_path, app_path

def main():
    """主函数"""
    # 检查命令行参数
    if "--help" in sys.argv or "-h" in sys.argv:
        print("小红书发布工具 - 打包版")
        print("用法: XhsPublisher [选项]")
        print("选项:")
        print("  --help, -h     显示帮助信息")
        print("  --version      显示版本信息")
        return
    
    if "--version" in sys.argv:
        print("小红书发布工具 v1.0.0")
        return
    
    try:
        # 设置环境
        base_path, app_path = setup_packaged_environment()
        
        # 导入并设置打包配置
        from packaging.app_config import setup_packaged_app
        config, logger = setup_packaged_app()
        
        logger.info("🚀 启动小红书发布工具（打包版）")
        logger.info(f"📁 基础路径: {base_path}")
        logger.info(f"📱 应用路径: {app_path}")
        
        # 导入并启动主应用
        from PyQt6.QtWidgets import QApplication
        from gui.main_window import MainWindow
        
        # 创建QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("小红书发布工具")
        app.setApplicationDisplayName("小红书发布工具")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("XHS Publisher")
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        logger.info("✅ 应用界面已显示")
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        # 错误处理
        import traceback
        error_msg = f"应用启动失败: {e}\n{traceback.format_exc()}"
        
        try:
            # 尝试显示错误对话框
            from PyQt6.QtWidgets import QApplication, QMessageBox
            if not QApplication.instance():
                app = QApplication(sys.argv)
            QMessageBox.critical(None, "启动错误", error_msg)
        except:
            # 如果GUI显示失败，输出到控制台
            print(error_msg)
        
        sys.exit(1)

if __name__ == "__main__":
    main()
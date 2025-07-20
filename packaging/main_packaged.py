#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书发布工具 - 打包版主入口
优化启动性能，延迟导入大型库
"""
import sys
import os
from pathlib import Path

def show_startup_info():
    """显示启动信息"""
    print("[启动] 小红书发布工具 v1.0.0 启动中...")
    print("[初始化] 正在初始化应用环境...")

def setup_environment():
    """快速设置环境"""
    # 设置应用路径
    if getattr(sys, 'frozen', False):
        # 打包环境
        app_path = Path(sys.executable).parent.parent
        os.environ['APP_PATH'] = str(app_path)
    
    # 设置编码
    if hasattr(sys, 'setdefaultencoding'):
        sys.setdefaultencoding('utf-8')

def main():
    """主函数 - 快速启动"""
    try:
        # 显示启动信息
        show_startup_info()
        
        # 快速环境设置
        setup_environment()
        
        print("[加载] 正在加载核心模块...")
        
        # 延迟导入大型库
        from packaging.app_config import setup_packaged_app
        
        print("[配置] 正在配置应用...")
        
        # 设置打包应用
        config, logger = setup_packaged_app()
        
        print("[界面] 正在启动用户界面...")
        
        # 延迟导入 GUI 相关库
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt
        from gui.main_window import MainWindow
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("小红书发布工具")
        app.setApplicationVersion("1.0.0")
        
        # PyQt6 默认启用高DPI支持，不需要手动设置
        # 如果需要特定的DPI设置，可以使用环境变量
        
        print("[完成] 应用启动完成！")
        
        # 创建主窗口
        window = MainWindow()
        window.show()
        
        # 运行应用
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"[错误] 应用启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
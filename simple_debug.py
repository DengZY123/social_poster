#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
超级简化的调试版本
专门用于排查打包程序执行就退出的问题
"""
import sys
import os
import traceback
from pathlib import Path
import time

def print_debug(message, level="INFO"):
    """输出调试信息"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level}] {message}")
    sys.stdout.flush()

def print_section(title):
    """输出分节标题"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50)

def check_basic_environment():
    """检查基本环境"""
    print_section("基本环境检查")
    
    print_debug(f"Python版本: {sys.version}")
    print_debug(f"Python路径: {sys.executable}")
    print_debug(f"平台: {sys.platform}")
    print_debug(f"当前目录: {os.getcwd()}")
    
    # 检查是否为打包环境
    if getattr(sys, 'frozen', False):
        print_debug("运行在打包环境中")
        if hasattr(sys, '_MEIPASS'):
            print_debug(f"临时目录: {sys._MEIPASS}")
    else:
        print_debug("运行在开发环境中")
    
    return True

def test_imports():
    """测试关键模块导入"""
    print_section("模块导入测试")
    
    modules_to_test = [
        ('sys', 'sys'),
        ('os', 'os'),
        ('pathlib', 'pathlib'),
        ('PyQt6', 'PyQt6'),
        ('PyQt6.QtWidgets', 'PyQt6.QtWidgets'),
        ('PyQt6.QtCore', 'PyQt6.QtCore'),
        ('loguru', 'loguru'),
        ('pandas', 'pandas'),
        ('playwright', 'playwright'),
    ]
    
    failed_imports = []
    for name, module in modules_to_test:
        try:
            __import__(module)
            print_debug(f"成功导入: {name}")
        except ImportError as e:
            print_debug(f"导入失败: {name} - {e}", "ERROR")
            failed_imports.append(name)
        except Exception as e:
            print_debug(f"导入异常: {name} - {e}", "WARNING")
    
    if failed_imports:
        print_debug(f"失败的模块: {', '.join(failed_imports)}", "ERROR")
        return False
    else:
        print_debug("所有模块导入成功")
        return True

def test_gui_creation():
    """测试GUI创建"""
    print_section("GUI创建测试")
    
    try:
        print_debug("导入PyQt6...")
        from PyQt6.QtWidgets import QApplication, QWidget, QLabel
        from PyQt6.QtCore import Qt
        
        print_debug("创建QApplication...")
        app = QApplication(sys.argv)
        
        print_debug("创建测试窗口...")
        window = QWidget()
        window.setWindowTitle("调试测试窗口")
        window.resize(300, 200)
        
        label = QLabel("如果你看到这个窗口，说明GUI基本正常！\n\n点击关闭按钮退出。", window)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        label.resize(280, 180)
        label.move(10, 10)
        
        print_debug("显示测试窗口...")
        window.show()
        
        print_debug("GUI创建成功，进入事件循环...")
        print_debug("注意：GUI窗口将显示5秒后自动关闭，或者你可以手动关闭")
        
        # 设置5秒后自动关闭
        from PyQt6.QtCore import QTimer
        timer = QTimer()
        timer.timeout.connect(app.quit)
        timer.start(5000)  # 5秒
        
        app.exec()
        print_debug("GUI测试完成")
        return True
        
    except Exception as e:
        print_debug(f"GUI创建失败: {e}", "ERROR")
        traceback.print_exc()
        return False

def test_project_files():
    """检查项目文件"""
    print_section("项目文件检查")
    
    # 重要文件列表
    important_files = [
        'main.py',
        'config.json',
        'requirements.txt',
        'gui',
        'core',
    ]
    
    missing_files = []
    for file_name in important_files:
        file_path = Path(file_name)
        if file_path.exists():
            print_debug(f"找到: {file_name}")
        else:
            print_debug(f"缺失: {file_name}", "WARNING")
            missing_files.append(file_name)
    
    if missing_files:
        print_debug(f"缺失文件: {', '.join(missing_files)}", "WARNING")
    
    return True

def main():
    """主函数"""
    print_section("小红书发布工具 - 简化调试版本")
    print_debug("开始调试检查...")
    
    try:
        # 测试步骤
        steps = [
            ("基本环境检查", check_basic_environment),
            ("项目文件检查", test_project_files),
            ("模块导入测试", test_imports),
            ("GUI创建测试", test_gui_creation),
        ]
        
        for step_name, step_func in steps:
            print_debug(f"执行: {step_name}")
            if not step_func():
                print_debug(f"步骤失败: {step_name}", "ERROR")
                print_debug("调试过程中止，问题可能在这里！", "ERROR")
                break
        else:
            print_debug("所有测试步骤完成！", "SUCCESS")
            print_debug("如果程序能运行到这里，说明基本环境是正常的", "SUCCESS")
        
    except Exception as e:
        print_debug(f"严重错误: {e}", "ERROR")
        traceback.print_exc()
    
    finally:
        # 保持窗口打开
        if sys.platform == "win32":
            print_debug("按回车键退出...")
            input()

if __name__ == "__main__":
    main() 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小红书发布工具 - 调试版主入口
包含详细的控制台输出，用于排查打包问题
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
    sys.stdout.flush()  # 强制刷新输出

def print_section(title):
    """输出分节标题"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python_environment():
    """检查Python环境"""
    print_section("Python环境检查")
    
    print_debug(f"Python版本: {sys.version}")
    print_debug(f"Python可执行文件: {sys.executable}")
    print_debug(f"平台: {sys.platform}")
    print_debug(f"当前工作目录: {os.getcwd()}")
    
    # 检查是否为打包环境
    if getattr(sys, 'frozen', False):
        print_debug("✅ 运行在打包环境中")
        print_debug(f"可执行文件路径: {sys.executable}")
        print_debug(f"_MEIPASS: {getattr(sys, '_MEIPASS', '未设置')}")
    else:
        print_debug("⚠️ 运行在开发环境中")
    
    return True

def check_system_paths():
    """检查系统路径"""
    print_section("系统路径检查")
    
    print_debug("Python路径:")
    for i, path in enumerate(sys.path):
        print_debug(f"  [{i}] {path}")
    
    # 检查环境变量
    important_env_vars = ['PATH', 'PYTHONPATH', 'APP_PATH']
    print_debug("重要环境变量:")
    for var in important_env_vars:
        value = os.environ.get(var, '未设置')
        print_debug(f"  {var}: {value}")
    
    return True

def check_dependencies():
    """检查依赖模块"""
    print_section("依赖模块检查")
    
    required_modules = [
        ('PyQt6', 'PyQt6'),
        ('PyQt6.QtCore', 'PyQt6.QtCore'),
        ('PyQt6.QtWidgets', 'PyQt6.QtWidgets'),
        ('playwright', 'playwright'),
        ('loguru', 'loguru'),
        ('pandas', 'pandas'),
        ('pydantic', 'pydantic'),
    ]
    
    failed_imports = []
    
    for display_name, module_name in required_modules:
        try:
            print_debug(f"检查模块: {display_name}")
            module = __import__(module_name)
            version = getattr(module, '__version__', '未知版本')
            print_debug(f"  ✅ {display_name} - 版本: {version}")
        except ImportError as e:
            print_debug(f"  ❌ {display_name} - 导入失败: {e}", "ERROR")
            failed_imports.append(display_name)
        except Exception as e:
            print_debug(f"  ⚠️ {display_name} - 导入异常: {e}", "WARNING")
    
    if failed_imports:
        print_debug(f"❌ 失败的模块: {', '.join(failed_imports)}", "ERROR")
        return False
    else:
        print_debug("✅ 所有依赖模块检查通过")
        return True

def check_project_structure():
    """检查项目结构"""
    print_section("项目结构检查")
    
    # 确定项目根目录
    if getattr(sys, 'frozen', False):
        # 打包环境
        if hasattr(sys, '_MEIPASS'):
            project_root = Path(sys._MEIPASS)
        else:
            project_root = Path(sys.executable).parent
    else:
        # 开发环境
        project_root = Path(__file__).parent.parent
    
    print_debug(f"项目根目录: {project_root}")
    
    # 检查重要目录和文件
    important_paths = [
        'core',
        'gui',
        'config.json',
        'images',
    ]
    
    missing_paths = []
    for path_name in important_paths:
        path = project_root / path_name
        if path.exists():
            print_debug(f"  ✅ {path_name}: {path}")
        else:
            print_debug(f"  ❌ {path_name}: 不存在", "ERROR")
            missing_paths.append(path_name)
    
    if missing_paths:
        print_debug(f"❌ 缺失的路径: {', '.join(missing_paths)}", "ERROR")
        return False
    else:
        print_debug("✅ 项目结构检查通过")
        return True

def setup_environment():
    """设置环境"""
    print_section("环境设置")
    
    try:
        # 设置应用路径
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                app_path = Path(sys._MEIPASS)
                os.environ['APP_PATH'] = str(app_path)
                print_debug(f"设置APP_PATH: {app_path}")
            
            # 确保项目路径在sys.path中
            project_paths = [
                str(Path(sys.executable).parent),
                str(Path(sys.executable).parent / "core"),
                str(Path(sys.executable).parent / "gui"),
            ]
            
            for path in project_paths:
                if path not in sys.path:
                    sys.path.insert(0, path)
                    print_debug(f"添加到sys.path: {path}")
        
        # 设置编码
        if hasattr(sys, 'setdefaultencoding'):
            sys.setdefaultencoding('utf-8')
            print_debug("设置默认编码为UTF-8")
        
        print_debug("✅ 环境设置完成")
        return True
        
    except Exception as e:
        print_debug(f"❌ 环境设置失败: {e}", "ERROR")
        traceback.print_exc()
        return False

def start_application():
    """启动应用程序"""
    print_section("应用程序启动")
    
    try:
        # 添加父目录到路径
        import sys
        from pathlib import Path
        parent_dir = str(Path(__file__).parent.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        print_debug("导入打包配置模块...")
        from packaging.app_config import setup_packaged_app
        
        print_debug("设置打包应用...")
        config, logger = setup_packaged_app()
        
        print_debug("导入PyQt6模块...")
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import Qt
        
        print_debug("导入主窗口模块...")
        from gui.main_window import MainWindow
        
        print_debug("创建QApplication...")
        app = QApplication(sys.argv)
        app.setApplicationName("小红书发布工具")
        app.setApplicationVersion("1.0.0")
        
        print_debug("创建主窗口...")
        window = MainWindow()
        
        print_debug("显示主窗口...")
        window.show()
        
        print_debug("✅ 应用程序启动成功！")
        print_debug("正在进入主事件循环...")
        
        # 运行应用
        return app.exec()
        
    except ImportError as e:
        print_debug(f"❌ 模块导入失败: {e}", "ERROR")
        traceback.print_exc()
        return 1
    except Exception as e:
        print_debug(f"❌ 应用启动失败: {e}", "ERROR")
        traceback.print_exc()
        return 1

def main():
    """主函数"""
    print_section("小红书发布工具 - 调试启动")
    print_debug("开始启动过程...")
    
    try:
        # 保持控制台窗口打开
        if sys.platform == "win32":
            print_debug("Windows平台，控制台将保持打开状态")
        
        # 逐步检查和初始化
        steps = [
            ("Python环境检查", check_python_environment),
            ("系统路径检查", check_system_paths),
            ("依赖模块检查", check_dependencies),
            ("项目结构检查", check_project_structure),
            ("环境设置", setup_environment),
        ]
        
        for step_name, step_func in steps:
            print_debug(f"执行步骤: {step_name}")
            if not step_func():
                print_debug(f"❌ 步骤失败: {step_name}", "ERROR")
                print_debug("启动过程中止")
                input("按回车键退出...")
                return 1
        
        print_debug("✅ 所有检查步骤完成，准备启动应用...")
        
        # 启动应用
        exit_code = start_application()
        
        print_debug(f"应用程序退出，退出代码: {exit_code}")
        return exit_code
        
    except KeyboardInterrupt:
        print_debug("用户中断，正在退出...", "WARNING")
        return 0
    except Exception as e:
        print_debug(f"❌ 严重错误: {e}", "ERROR")
        traceback.print_exc()
        print_debug("请将上述错误信息发送给开发者")
        input("按回车键退出...")
        return 1
    finally:
        print_debug("清理资源...")
        # 在Windows上，让用户有机会看到输出
        if sys.platform == "win32" and getattr(sys, 'frozen', False):
            print_debug("程序即将退出...")
            input("按回车键关闭控制台...")

if __name__ == "__main__":
    sys.exit(main()) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
打包配置测试脚本
验证所有打包相关的组件是否正常工作
"""
import sys
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

def test_firefox_finder():
    """测试 Firefox 查找器"""
    print("\n🔍 测试 Firefox 查找器...")
    try:
        from firefox_finder import FirefoxFinder
        finder = FirefoxFinder()
        firefox_path = finder.find_playwright_firefox()
        
        if firefox_path:
            info = finder.get_firefox_info(firefox_path)
            print(f"✅ 找到 Firefox: {firefox_path}")
            print(f"   版本: firefox-{info['version']}")
            print(f"   大小: {info['size_mb']:.1f} MB")
            print(f"   应用目录: {info['app_dir']}")
            return True
        else:
            print("❌ 未找到 Firefox")
            return False
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_path_detector():
    """测试路径检测器"""
    print("\n🔍 测试路径检测器...")
    try:
        from scripts.path_detector import PathDetector
        detector = PathDetector()
        
        print(f"✅ 运行环境: {'打包' if detector.is_packaged else '开发'}")
        print(f"   平台: {detector.platform_name}")
        print(f"   基础目录: {detector.get_base_dir()}")
        
        # 测试 Firefox 路径检测
        firefox_path = detector.get_firefox_path()
        if firefox_path:
            print(f"✅ Firefox 路径: {firefox_path}")
        else:
            print("⚠️  Firefox 路径: 未配置（将使用 Playwright 默认）")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_app_config():
    """测试应用配置"""
    print("\n🔍 测试应用配置...")
    try:
        from app_config import app_config_manager
        
        # 获取配置
        config = app_config_manager.get_app_config()
        print(f"✅ 配置加载成功")
        print(f"   Firefox 配置目录: {config.firefox_profile_path}")
        print(f"   任务文件: {config.tasks_file_path}")
        
        # 获取 Firefox 启动配置
        firefox_config = app_config_manager.get_firefox_launch_config()
        if firefox_config.get("executable_path"):
            print(f"✅ Firefox 可执行文件: {firefox_config['executable_path']}")
        else:
            print("⚠️  Firefox 可执行文件: 未配置")
        
        return True
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

def test_pyinstaller_spec():
    """测试 PyInstaller 配置"""
    print("\n🔍 测试 PyInstaller 配置...")
    spec_file = Path(__file__).parent / "xhs_publisher.spec"
    
    if spec_file.exists():
        print(f"✅ 配置文件存在: {spec_file}")
        
        # 检查文件内容
        content = spec_file.read_text()
        if "firefox_finder" in content:
            print("✅ 已集成动态 Firefox 检测")
        else:
            print("❌ 未集成动态 Firefox 检测")
        
        return True
    else:
        print(f"❌ 配置文件不存在: {spec_file}")
        return False

def test_build_scripts():
    """测试构建脚本"""
    print("\n🔍 测试构建脚本...")
    
    scripts = {
        "build.py": Path(__file__).parent / "build.py",
        "build.sh": Path(__file__).parent / "build.sh",
        "build_nuitka.py": Path(__file__).parent / "build_nuitka.py",
    }
    
    all_exist = True
    for name, path in scripts.items():
        if path.exists():
            print(f"✅ {name} 存在")
            
            # 检查执行权限（仅限 shell 脚本）
            if name.endswith('.sh'):
                import os
                if os.access(path, os.X_OK):
                    print(f"   可执行权限: ✅")
                else:
                    print(f"   可执行权限: ❌")
        else:
            print(f"❌ {name} 不存在")
            all_exist = False
    
    return all_exist

def test_dependencies():
    """测试依赖"""
    print("\n🔍 测试依赖...")
    
    dependencies = {
        "PyQt6": "PyQt6",
        "playwright": "playwright",
        "PyInstaller": "PyInstaller",
        "pandas": "pandas",
        "loguru": "loguru",
    }
    
    all_installed = True
    for name, import_name in dependencies.items():
        try:
            __import__(import_name)
            print(f"✅ {name}")
        except ImportError:
            print(f"❌ {name} 未安装")
            all_installed = False
    
    return all_installed

def run_all_tests():
    """运行所有测试"""
    print("🚀 小红书发布工具 - 打包配置测试")
    print("=" * 60)
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")
    print("=" * 60)
    
    tests = [
        ("依赖检查", test_dependencies),
        ("Firefox 查找器", test_firefox_finder),
        ("路径检测器", test_path_detector),
        ("应用配置", test_app_config),
        ("PyInstaller 配置", test_pyinstaller_spec),
        ("构建脚本", test_build_scripts),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n❌ {name} 测试异常: {e}")
            results.append((name, False))
    
    # 显示总结
    print("\n" + "=" * 60)
    print("📊 测试总结")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！可以开始打包。")
        print("\n下一步：")
        print("1. 运行 ./build.sh 开始打包")
        print("2. 查看 dist/ 目录获取打包结果")
    else:
        print("\n⚠️  部分测试失败，请解决问题后再打包。")
        print("\n建议：")
        print("1. 安装缺失的依赖: pip install -r requirements.txt")
        print("2. 安装 Firefox: playwright install firefox")
        print("3. 检查文件权限和路径")

if __name__ == "__main__":
    run_all_tests()
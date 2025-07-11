#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows构建测试脚本
用于验证Windows版本的构建配置
"""
import sys
import os
import platform
from pathlib import Path

def test_environment():
    """测试环境配置"""
    print("🔍 测试Windows构建环境")
    print("=" * 50)
    
    # 基本信息
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")
    
    # 检查必要模块
    required_modules = [
        'PyQt6', 'playwright', 'pandas', 'openpyxl', 
        'loguru', 'pydantic', 'ujson', 'PyInstaller'
    ]
    
    print("\n📦 检查依赖模块:")
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.lower().replace('-', '_'))
            print(f"✅ {module}")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} (缺失)")
    
    if missing_modules:
        print(f"\n⚠️ 缺失模块: {', '.join(missing_modules)}")
        return False
    
    return True

def test_firefox_detection():
    """测试Firefox检测"""
    print("\n🦊 测试Firefox检测:")
    
    # 常见Firefox路径
    firefox_paths = [
        Path.home() / "AppData/Local/ms-playwright/firefox-1488/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1489/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1490/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1491/firefox",
        Path.home() / "AppData/Local/ms-playwright/firefox-1492/firefox",
    ]
    
    firefox_found = False
    for firefox_path in firefox_paths:
        if firefox_path.exists() and (firefox_path / "firefox.exe").exists():
            print(f"✅ 找到Firefox: {firefox_path}")
            firefox_found = True
            break
    
    if not firefox_found:
        print("❌ 未找到Playwright Firefox")
        print("请运行: playwright install firefox")
        return False
    
    return True

def test_path_detector():
    """测试路径检测器"""
    print("\n📁 测试路径检测器:")
    
    try:
        # 导入路径检测器
        sys.path.insert(0, str(Path(__file__).parent / "scripts"))
        from path_detector import PathDetector
        
        detector = PathDetector()
        
        print(f"平台: {detector.platform_name}")
        print(f"是否打包: {detector.is_packaged}")
        print(f"基础目录: {detector.get_base_dir()}")
        print(f"用户数据目录: {detector.get_user_data_dir()}")
        print(f"配置目录: {detector.get_config_dir()}")
        print(f"日志目录: {detector.get_logs_dir()}")
        print(f"Firefox路径: {detector.get_firefox_path()}")
        
        # 验证环境
        validation = detector.validate_environment()
        print("\n环境验证:")
        for key, value in validation.items():
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        return all(validation.values())
        
    except Exception as e:
        print(f"❌ 路径检测器测试失败: {e}")
        return False

def test_spec_file():
    """测试spec文件配置"""
    print("\n📄 测试spec文件:")
    
    spec_file = Path(__file__).parent / "xhs_publisher_windows.spec"
    if not spec_file.exists():
        print(f"❌ spec文件不存在: {spec_file}")
        return False
    
    print(f"✅ spec文件存在: {spec_file}")
    
    # 读取并检查关键配置
    try:
        with open(spec_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查关键配置项
        checks = [
            ('APP_NAME', 'APP_NAME = "XhsPublisher"'),
            ('Windows平台', 'IS_WINDOWS = sys.platform == "win32"'),
            ('Firefox路径', 'firefox_paths = ['),
            ('主脚本', 'MAIN_SCRIPT = str(PACKAGING_DIR / "main_packaged.py")'),
            ('EXE配置', 'exe = EXE('),
        ]
        
        for check_name, check_pattern in checks:
            if check_pattern in content:
                print(f"✅ {check_name}")
            else:
                print(f"❌ {check_name}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ 读取spec文件失败: {e}")
        return False

def main():
    """主测试函数"""
    print("🚀 Windows构建测试")
    print("=" * 60)
    
    # 检查是否在Windows上
    if platform.system() != "Windows":
        print("❌ 此脚本仅在Windows上运行")
        return False
    
    # 运行各项测试
    tests = [
        ("环境配置", test_environment),
        ("Firefox检测", test_firefox_detection),
        ("路径检测器", test_path_detector),
        ("spec文件", test_spec_file),
    ]
    
    all_passed = True
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"❌ {test_name}测试出错: {e}")
            all_passed = False
    
    # 总结
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有测试通过！可以开始构建Windows版本")
        print("运行构建命令: python build_windows.py")
    else:
        print("❌ 部分测试失败，请检查上述问题")
        print("解决问题后再次运行此测试脚本")
    
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Windows配置读取功能
用于验证安装脚本生成的配置是否能被正确读取
"""
import sys
import json
from pathlib import Path

def test_config_reading():
    """测试配置文件读取"""
    print("=" * 50)
    print("Windows Firefox配置测试")
    print("=" * 50)
    print()
    
    # 模拟Windows环境
    if sys.platform != "win32":
        print(f"⚠️  当前系统: {sys.platform}")
        print("   此脚本用于Windows系统测试")
        print()
    
    # 配置目录
    config_dir = Path.home() / "AppData" / "Local" / "XhsPublisher"
    print(f"📁 配置目录: {config_dir}")
    print(f"   目录存在: {config_dir.exists()}")
    print()
    
    # 测试JSON配置
    print("📄 检查JSON配置文件...")
    json_config = config_dir / "browser_config.json"
    if json_config.exists():
        print(f"✅ 找到配置文件: {json_config}")
        try:
            with open(json_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                print("   配置内容:")
                for key, value in config.items():
                    print(f"   - {key}: {value}")
                
                # 验证Firefox路径
                firefox_path = config.get('firefox_path')
                if firefox_path:
                    if Path(firefox_path).exists():
                        print(f"✅ Firefox路径有效: {firefox_path}")
                    else:
                        print(f"❌ Firefox路径无效: {firefox_path}")
        except Exception as e:
            print(f"❌ 读取配置失败: {e}")
    else:
        print("❌ 未找到JSON配置文件")
    
    print()
    
    # 测试文本配置
    print("📄 检查文本配置文件...")
    txt_config = config_dir / "firefox_path.txt"
    if txt_config.exists():
        print(f"✅ 找到配置文件: {txt_config}")
        try:
            firefox_path = txt_config.read_text(encoding='utf-8').strip()
            print(f"   路径内容: {firefox_path}")
            if Path(firefox_path).exists():
                print(f"✅ Firefox路径有效")
            else:
                print(f"❌ Firefox路径无效")
        except Exception as e:
            print(f"❌ 读取配置失败: {e}")
    else:
        print("❌ 未找到文本配置文件")
    
    print()
    print("测试完成！")

if __name__ == "__main__":
    test_config_reading()
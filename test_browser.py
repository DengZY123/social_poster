#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试浏览器启动脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.publisher import XhsPublisher


async def test_browser_launch():
    """测试浏览器启动"""
    print("🧪 开始测试浏览器启动...")
    
    try:
        async with XhsPublisher(headless=False, user_data_dir="firefox_profile") as publisher:
            print("✅ 浏览器启动成功！")
            
            # 测试访问小红书
            print("🔍 测试访问小红书...")
            await publisher.page.goto("https://www.xiaohongshu.com", timeout=45000)
            print("✅ 小红书访问成功！")
            
            # 等待几秒钟观察
            await asyncio.sleep(3)
            
        print("✅ 测试完成，浏览器已关闭")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    
    return True


if __name__ == "__main__":
    result = asyncio.run(test_browser_launch())
    sys.exit(0 if result else 1)
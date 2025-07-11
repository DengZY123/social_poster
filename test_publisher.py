#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试发布器与登录助手的浏览器配置文件共享
"""
import asyncio
import json
from core.publisher import XhsPublisher

async def test_shared_profile():
    """测试共享浏览器配置文件"""
    print("🧪 开始测试浏览器配置文件共享...")
    
    try:
        async with XhsPublisher(headless=False, user_data_dir="firefox_profile") as publisher:
            print("✅ 发布器启动成功")
            
            # 检查登录状态
            login_status = await publisher.check_login_status()
            print(f"🔍 登录状态: {'已登录' if login_status else '未登录'}")
            
            if login_status:
                print("🎉 浏览器配置文件共享成功！发布器检测到登录状态")
                return True
            else:
                print("⚠️ 发布器未检测到登录状态，可能需要重新登录")
                return False
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_shared_profile())
    print(f"\n🏁 测试结果: {'成功' if result else '失败'}")
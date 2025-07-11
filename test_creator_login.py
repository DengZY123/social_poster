#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试创作者中心登录页面跳转逻辑
"""
import asyncio
from playwright.async_api import async_playwright

async def test_creator_login():
    """测试创作者中心登录逻辑"""
    print("🧪 开始测试创作者中心登录检测...")
    
    try:
        async with async_playwright() as p:
            # 使用共享的浏览器配置文件
            context = await p.firefox.launch_persistent_context(
                user_data_dir="firefox_profile",
                headless=False,
                timeout=30000,
                viewport={'width': 1366, 'height': 768},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            page = await context.new_page()
            print("✅ 浏览器启动成功")
            
            # 测试URL（你提供的登录页面）
            login_url = "https://creator.xiaohongshu.com/login?source=&redirectReason=401&lastUrl=%2Fpublish%2Fpublish%3Ffrom%3Dtab_switch"
            target_url = "https://creator.xiaohongshu.com"
            
            print(f"🎯 访问登录页面: {login_url}")
            await page.goto(login_url, wait_until="domcontentloaded", timeout=30000)
            
            # 等待页面加载完成
            await asyncio.sleep(3)
            
            # 获取当前URL
            current_url = page.url
            print(f"📍 当前URL: {current_url}")
            
            # 检查是否跳转到目标页面
            if current_url.startswith(target_url) and "login" not in current_url:
                print("🎉 登录检测成功！页面已跳转到创作者中心")
                print(f"✅ 目标URL: {target_url}")
                print(f"✅ 实际URL: {current_url}")
                
                # 进一步验证：检查页面内容
                try:
                    page_title = await page.title()
                    print(f"📄 页面标题: {page_title}")
                    
                    # 检查是否有发布相关元素
                    publish_elements = await page.evaluate("""
                        () => {
                            const publishText = document.body.innerText;
                            return {
                                hasPublish: publishText.includes('发布') || publishText.includes('创作'),
                                hasLogin: publishText.includes('登录'),
                                bodyText: publishText.substring(0, 200)
                            };
                        }
                    """)
                    
                    print(f"🔍 页面内容检查:")
                    print(f"  - 包含发布/创作: {publish_elements['hasPublish']}")
                    print(f"  - 包含登录: {publish_elements['hasLogin']}")
                    print(f"  - 页面内容片段: {publish_elements['bodyText']}")
                    
                    if publish_elements['hasPublish'] and not publish_elements['hasLogin']:
                        return True
                        
                except Exception as e:
                    print(f"⚠️ 页面内容检查失败: {e}")
                
                return True
                
            elif "login" in current_url:
                print("❌ 仍在登录页面，用户未登录")
                print(f"🔗 登录页面URL: {current_url}")
                
                # 等待用户登录
                print("⏳ 等待用户完成登录...")
                
                for i in range(60):  # 最多等待5分钟
                    await asyncio.sleep(5)
                    current_url = page.url
                    print(f"📍 检查第{i+1}次，当前URL: {current_url}")
                    
                    if current_url.startswith(target_url) and "login" not in current_url:
                        print("🎉 检测到登录成功！页面已跳转")
                        return True
                        
                    if page.is_closed():
                        print("⚠️ 浏览器已关闭")
                        break
                
                return False
                
            else:
                print(f"🤔 意外的URL跳转: {current_url}")
                return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False
    finally:
        try:
            await context.close()
        except:
            pass

async def test_simple_creator_access():
    """简单测试：直接访问创作者中心"""
    print("\n🧪 开始简单测试：直接访问创作者中心...")
    
    try:
        async with async_playwright() as p:
            context = await p.firefox.launch_persistent_context(
                user_data_dir="firefox_profile",
                headless=False,
                timeout=30000,
                viewport={'width': 1366, 'height': 768},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            page = await context.new_page()
            
            # 直接访问创作者中心
            creator_url = "https://creator.xiaohongshu.com"
            print(f"🎯 直接访问: {creator_url}")
            
            await page.goto(creator_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            current_url = page.url
            print(f"📍 跳转后URL: {current_url}")
            
            if "login" in current_url:
                print("❌ 被重定向到登录页面，用户未登录")
                return False
            elif current_url.startswith(creator_url):
                print("✅ 成功访问创作者中心，用户已登录")
                return True
            else:
                print(f"🤔 意外跳转: {current_url}")
                return False
                
    except Exception as e:
        print(f"❌ 简单测试失败: {e}")
        return False
    finally:
        try:
            await context.close()
        except:
            pass

async def main():
    """主测试函数"""
    print("=" * 50)
    print("🔐 创作者中心登录状态测试")
    print("=" * 50)
    
    # 测试1：简单访问创作者中心
    simple_result = await test_simple_creator_access()
    
    # 测试2：完整登录流程测试
    if not simple_result:
        login_result = await test_creator_login()
        print(f"\n🏁 登录测试结果: {'成功' if login_result else '失败'}")
    else:
        print(f"\n🏁 简单测试结果: 用户已登录")

if __name__ == "__main__":
    asyncio.run(main())
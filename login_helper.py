#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的登录助手
打开浏览器让用户登录小红书账号
"""
import sys
import asyncio
from pathlib import Path
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.publisher import XhsPublisher


async def open_login_page(account_name: str):
    """打开登录页面"""
    try:
        logger.info(f"🔐 为账号 {account_name} 打开登录页面...")
        
        # 使用最简单的浏览器启动方式
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            # 使用与发布器相同的持久化浏览器上下文
            context = await p.firefox.launch_persistent_context(
                user_data_dir="firefox_profile",  # 与发布器使用相同的目录
                headless=False,
                timeout=30000,
                viewport={'width': 1366, 'height': 768},
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            # 创建新页面
            page = await context.new_page()
            
            logger.info("✅ 浏览器启动成功，正在跳转到小红书...")
            
            # 直接访问小红书首页
            try:
                await page.goto("https://www.xiaohongshu.com", timeout=30000)
                logger.info("✅ 小红书页面加载完成")
                
                # 等待页面完全加载
                await asyncio.sleep(2)
                
                # 显示简单提示（可选）
                try:
                    await page.evaluate("""
                        () => {
                            console.log('登录助手已就绪，请手动登录');
                            document.title = '🔐 请登录小红书账号 - 登录助手';
                        }
                    """)
                except:
                    pass
                    
            except Exception as e:
                logger.error(f"❌ 跳转到小红书失败: {e}")
                # 如果跳转失败，至少让用户看到浏览器
                await page.goto("about:blank")
                logger.info("⚠️ 自动跳转失败，请手动访问 https://www.xiaohongshu.com")
            
            logger.info("🎯 请在浏览器中完成登录，完成后关闭浏览器窗口")
            
            # 循环检测登录状态
            login_success = False
            check_interval = 5  # 每5秒检测一次
            max_wait_time = 1800  # 最多等待30分钟
            elapsed_time = 0
            
            try:
                while elapsed_time < max_wait_time:
                    try:
                        # 检测登录状态的方法
                        login_success = await check_login_status(page)
                        
                        if login_success:
                            logger.info("✅ 检测到登录成功！")
                            await save_login_state(page, account_name)
                            break
                        
                        # 检测浏览器是否被用户关闭
                        if page.is_closed():
                            logger.info("⚠️ 浏览器已关闭，结束检测")
                            break
                            
                    except Exception as e:
                        logger.debug(f"检测过程中的异常: {e}")
                        # 可能页面还在加载，继续等待
                        pass
                    
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                    
                    # 每分钟输出一次状态
                    if elapsed_time % 60 == 0:
                        logger.info(f"⏳ 等待登录中... 已等待 {elapsed_time//60} 分钟")
                        
            except Exception as e:
                logger.error(f"❌ 登录检测过程出错: {e}")
            finally:
                try:
                    if not page.is_closed():
                        await context.close()
                except:
                    pass
            
            if login_success:
                logger.info("🎉 登录助手完成，登录状态已保存")
            else:
                logger.info("⚠️ 登录助手结束，未检测到登录成功")
            
        logger.info("✅ 登录助手任务完成")
        
    except Exception as e:
        logger.error(f"❌ 登录助手失败: {e}")
        # 作为后备方案，直接用系统默认浏览器打开
        try:
            import webbrowser
            webbrowser.open("https://www.xiaohongshu.com")
            logger.info("✅ 已用系统默认浏览器打开小红书页面")
        except:
            logger.error("❌ 所有方式都失败了")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法: python login_helper.py <账号名称>")
        sys.exit(1)
    
    account_name = sys.argv[1]
    
    try:
        # 运行登录助手
        asyncio.run(open_login_page(account_name))
    except KeyboardInterrupt:
        logger.info("⚠️ 登录助手被用户中断")
    except Exception as e:
        logger.error(f"❌ 登录助手异常: {e}")


async def check_login_status(page) -> bool:
    """检测登录状态"""
    try:
        # 等待页面加载完成
        await page.wait_for_load_state('networkidle', timeout=10000)
        
        # 方法1：检查是否存在登录按钮（未登录状态）
        login_button_selectors = [
            'button.login-btn',  # 主要的登录按钮
            '#login-btn',        # 带ID的登录按钮
            'button[data-v-a93a7d02]',  # 你提供的特殊属性按钮
            '.login-btn'         # 通用登录按钮类
        ]
        
        for selector in login_button_selectors:
            try:
                login_btn = await page.query_selector(selector)
                if login_btn:
                    # 检查按钮文本是否包含"登录"
                    text_content = await login_btn.text_content()
                    if text_content and "登录" in text_content:
                        logger.debug("检测到登录按钮，用户未登录")
                        return False
            except:
                continue
        
        # 方法2：检查是否存在用户头像/用户信息（已登录状态）
        # 基于你提供的精确HTML结构
        user_info_selectors = [
            # 你提供的精确选择器
            '.channel-list-content > li:nth-child(4)',  # 准确的第4个li元素
            '/html/body/div[2]/div[1]/div[2]/div[1]/ul/div[1]/li[4]',  # XPath
            # 检查包含"我"的span元素
            'span.channel:has-text("我")',
            'span.channel',  # 直接检查channel类
            # 检查包含头像的链接
            'a[href*="/user/profile/"]',  # 用户profile链接
            # 检查头像容器
            '.reds-avatar',
            '.reds-image-container.reds-avatar'
        ]
        
        for selector in user_info_selectors:
            try:
                if selector.startswith('/html'):
                    # XPath选择器需要特殊处理
                    continue  # 暂时跳过XPath，因为playwright默认用CSS选择器
                    
                user_element = await page.query_selector(selector)
                if user_element:
                    # 检查是否包含"我"或者头像相关内容
                    text_content = await user_element.text_content()
                    if text_content and "我" in text_content.strip():
                        logger.debug(f"检测到用户信息，用户已登录: {selector} -> {text_content.strip()}")
                        return True
                    
                    # 检查是否是头像元素
                    if 'avatar' in selector.lower() or 'profile' in selector.lower():
                        logger.debug(f"检测到用户头像，用户已登录: {selector}")
                        return True
            except:
                continue
        
        # 方法2.5：直接检查页面中是否有"我"字符（更暴力但有效）
        try:
            page_text = await page.evaluate("""
                () => {
                    // 获取左侧导航栏的文本
                    const leftNav = document.querySelector('.left-nav') || 
                                   document.querySelector('.sidebar') ||
                                   document.querySelector('nav') ||
                                   document.querySelector('.menu');
                    
                    if (leftNav) {
                        return leftNav.textContent || '';
                    }
                    
                    // 获取所有导航相关元素的文本
                    const navElements = document.querySelectorAll('a, button, span, div');
                    for (let elem of navElements) {
                        const text = elem.textContent || '';
                        if (text.trim() === '我' && elem.offsetParent !== null) {
                            return '找到我: ' + text;
                        }
                    }
                    
                    return '';
                }
            """)
            
            if page_text and "我" in page_text:
                logger.debug(f"在页面文本中检测到用户标识，用户已登录: {page_text.strip()}")
                return True
                
        except Exception as e:
            logger.debug(f"检查页面文本时出错: {e}")
        
        # 方法3：检查URL变化（登录后可能跳转）
        current_url = page.url
        # 根据你的截图，登录后URL变为 /explore
        if "/user/" in current_url or "/profile" in current_url or "/explore" in current_url:
            logger.debug(f"检测到用户相关URL，用户已登录: {current_url}")
            return True
        
        # 方法4：检查localStorage或cookies中的登录信息
        try:
            # 检查是否有用户token或session
            user_info = await page.evaluate("""
                () => {
                    // 检查localStorage中的用户信息
                    const userToken = localStorage.getItem('user_token') || 
                                    localStorage.getItem('token') ||
                                    localStorage.getItem('access_token');
                    
                    // 检查是否有用户ID
                    const userId = localStorage.getItem('user_id') ||
                                 localStorage.getItem('uid');
                    
                    // 检查cookies中是否有session
                    const hasSession = document.cookie.includes('session') ||
                                      document.cookie.includes('user') ||
                                      document.cookie.includes('login');
                    
                    return {
                        hasToken: !!userToken,
                        hasUserId: !!userId,
                        hasSession: hasSession,
                        cookieCount: document.cookie.split(';').length
                    };
                }
            """)
            
            if user_info['hasToken'] or user_info['hasUserId'] or (user_info['hasSession'] and user_info['cookieCount'] > 5):
                logger.debug("检测到登录相关的存储信息，用户已登录")
                return True
                
        except Exception as e:
            logger.debug(f"检查存储信息时出错: {e}")
        
        # 默认返回未登录
        logger.debug("未检测到登录状态，用户未登录")
        return False
        
    except Exception as e:
        logger.debug(f"检测登录状态时出错: {e}")
        return False


async def save_login_state(page, account_name: str):
    """保存登录状态"""
    try:
        from datetime import datetime
        import json
        # 获取所有cookies
        cookies = await page.context.cookies()
        
        # 获取localStorage数据
        local_storage = await page.evaluate("""
            () => {
                const storage = {};
                for (let i = 0; i < localStorage.length; i++) {
                    const key = localStorage.key(i);
                    storage[key] = localStorage.getItem(key);
                }
                return storage;
            }
        """)
        
        # 保存到文件（简单实现）
        login_data = {
            'account_name': account_name,
            'login_time': datetime.now().isoformat(),
            'cookies': cookies,
            'local_storage': local_storage,
            'url': page.url
        }
        
        # 保存到浏览器profile目录（由于使用了持久化上下文，数据会自动保存）
        logger.info(f"✅ 已保存账号 {account_name} 的登录状态")
        
        # 可选：保存到JSON文件作为备份
        with open(f"login_state_{account_name}.json", 'w', encoding='utf-8') as f:
            # 简化数据结构，只保存关键信息
            simple_data = {
                'account_name': account_name,
                'login_time': login_data['login_time'],
                'cookies_count': len(cookies),
                'has_local_storage': len(local_storage) > 0
            }
            json.dump(simple_data, f, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"保存登录状态失败: {e}")


if __name__ == "__main__":
    main()
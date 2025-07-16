"""
账号测试器 - 使用 Playwright 测试账号登录状态
"""
import asyncio
import json
import platform
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger


class AccountTester:
    """账号测试器"""
    
    def __init__(self, account_name: str, headless: bool = False):
        self.account_name = account_name
        self.headless = headless
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.executable_path = self._get_firefox_path()
    
    async def test_account(self) -> Tuple[bool, str]:
        """
        测试账号登录状态
        返回: (是否成功, 状态信息)
        """
        try:
            logger.info(f"[检测] 开始测试账号: {self.account_name}")
            
            # 启动浏览器
            await self._setup_browser()
            
            # 访问创作者中心发布页面
            logger.info("📱 访问创作者中心发布页面...")
            publish_url = 'https://creator.xiaohongshu.com/publish/publish?from=tab_switch'
            await self.page.goto(publish_url, wait_until='networkidle')
            await asyncio.sleep(3)
            
            # 检查登录状态
            is_logged_in, current_url = await self._check_login_status()
            
            if is_logged_in:
                # 获取用户信息
                user_info = await self._get_user_info()
                status_info = f"✅ 账号有效 - {user_info}"
                logger.success(f"✅ 账号 {self.account_name} 测试通过: {user_info}")
                return True, status_info
            else:
                # 如果未登录，等待用户手动登录
                logger.info(f"🔗 当前在登录页面: {current_url}")
                status_info = await self._wait_for_manual_login()
                return status_info.startswith("✅"), status_info
                
        except Exception as e:
            error_msg = f"❌ 测试失败: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
        finally:
            await self._cleanup()
    
    async def _setup_browser(self):
        """设置浏览器"""
        self.playwright = await async_playwright().start()
        
        # 创建持久化上下文目录（使用账号对应的profile）
        profile_dir = Path(f"firefox_profile/{self.account_name}")
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        # 准备launch_persistent_context的参数（参考publisher.py）
        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": self.headless,
            "timeout": 90000,
            "viewport": {'width': 1366, 'height': 768},
            "locale": 'zh-CN',
            "timezone_id": 'Asia/Shanghai',
            "args": ['--no-sandbox'],
            "firefox_user_prefs": {
                "dom.webdriver.enabled": False,
                "useAutomationExtension": False,
                "general.platform.override": "MacIntel",
                "browser.search.suggest.enabled": False,
                "browser.search.update": False,
                "services.sync.engine.prefs": False,
                "datareporting.policy.dataSubmissionEnabled": False,
                "datareporting.healthreport.uploadEnabled": False,
                "toolkit.telemetry.enabled": False,
                "browser.ping-centre.telemetry": False,
                "app.shield.optoutstudies.enabled": False,
                "app.normandy.enabled": False,
                "breakpad.reportURL": "",
                "browser.tabs.crashReporting.sendReport": False,
                "browser.crashReports.unsubmittedCheck.autoSubmit2": False,
                "network.captive-portal-service.enabled": False
            }
        }
        
        # 如果指定了executable_path，添加到参数中
        if self.executable_path:
            launch_kwargs["executable_path"] = self.executable_path
            logger.info(f"🦊 使用指定的Firefox路径: {self.executable_path}")
        
        # 尝试启动浏览器，包含详细的错误处理
        try:
            self.context = await self.playwright.firefox.launch_persistent_context(**launch_kwargs)
        except Exception as browser_error:
            error_msg = str(browser_error)
            
            # 检查是否是浏览器未安装的错误
            if "Executable doesn't exist" in error_msg:
                logger.error("❌ Firefox 浏览器未找到")
                logger.error("📦 解决方案：")
                logger.error("  🔧 开发环境解决方案：")
                logger.error("  1. 运行：playwright install firefox")
                logger.error("  2. 或在项目根目录运行：python -m playwright install firefox")
                        
            elif "Failed to launch" in error_msg:
                logger.error("❌ Firefox 启动失败")
                logger.error("可能的原因和解决方案：")
                logger.error("  • 权限不足 - 请以管理员身份运行")
                logger.error("  • 依赖库缺失 - 请重新下载浏览器")
                logger.error("  • Firefox 文件损坏 - 请重新下载浏览器")
                logger.error("  • 防火墙阻止 - 请检查防火墙设置")
                    
            elif "timeout" in error_msg.lower():
                logger.error("❌ 浏览器启动超时")
                logger.error("解决方案：")
                logger.error("  • 系统资源不足 - 请关闭其他程序")
                logger.error("  • 网络连接问题 - 请检查网络连接")
                logger.error("  • 重启应用程序")
                    
            else:
                logger.error(f"❌ 浏览器启动错误: {error_msg}")
                logger.error("通用解决方案：")
                logger.error("  1. 重启应用程序")
                logger.error("  2. 重新下载浏览器")
                logger.error("  3. 检查系统权限")
            
            # 重新抛出错误给上层调用者
            raise Exception(f"浏览器启动失败: {error_msg}")
        
        self.page = await self.context.new_page()
        
        # 设置用户代理
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
    
    async def _check_login_status(self) -> tuple[bool, str]:
        """检查登录状态
        返回: (是否登录, 当前 URL)
        """
        try:
            # 等待页面加载
            await self.page.wait_for_load_state('networkidle')
            await asyncio.sleep(2)  # 等待可能的重定向
            
            # 获取当前 URL
            current_url = self.page.url
            logger.info(f"🔗 当前 URL: {current_url}")
            
            # 根据 URL 判断登录状态
            if 'creator.xiaohongshu.com/login' in current_url:
                # 跳转到了登录页面，说明未登录
                logger.info("❌ 跳转到登录页面，账号未登录")
                return False, current_url
            elif 'creator.xiaohongshu.com/publish/publish' in current_url:
                # 在发布页面，说明已登录
                logger.info("✅ 保持在发布页面，账号已登录")
                return True, current_url
            else:
                # 其他情况，需要进一步检查
                logger.warning(f"⚠️ 未知页面: {current_url}")
                # 尝试再次访问发布页面
                await self.page.goto('https://creator.xiaohongshu.com/publish/publish?from=tab_switch', wait_until='networkidle')
                await asyncio.sleep(2)
                final_url = self.page.url
                logger.info(f"🔗 再次访问后的 URL: {final_url}")
                
                if 'creator.xiaohongshu.com/login' in final_url:
                    return False, final_url
                elif 'creator.xiaohongshu.com/publish/publish' in final_url:
                    return True, final_url
                else:
                    logger.error(f"无法判断登录状态，当前 URL: {final_url}")
                    return False, final_url
            
        except Exception as e:
            logger.error(f"检查登录状态失败: {e}")
            return False, self.page.url if self.page else "unknown"
    
    async def _get_user_info(self) -> str:
        """获取用户信息"""
        try:
            # 等待页面元素加载
            await asyncio.sleep(2)
            
            # 在创作者中心页面尝试获取用户信息
            # 更广泛的选择器，适应不同的页面结构
            nickname_selectors = [
                # 可能的用户名显示位置
                '[data-testid*="user"] span',
                '[class*="user"] span',
                '[class*="avatar"] + span',
                '[class*="nickname"]',
                '[class*="username"]',
                '[class*="user-name"]',
                'span[class*="name"]',
                # 通用选择器
                'span:contains("用户")',
                'div[class*="user"] span'
            ]
            
            for selector in nickname_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    for element in elements:
                        if element:
                            nickname = await element.text_content()
                            if nickname and len(nickname.strip()) > 0 and len(nickname.strip()) < 50:
                                # 过滤明显不是用户名的内容
                                nickname = nickname.strip()
                                if not any(keyword in nickname for keyword in ['登录', '注册', '发布', '保存', '取消', '确定']):
                                    logger.info(f"✅ 获取到用户信息: {nickname}")
                                    return f"用户: {nickname}"
                except Exception as e:
                    continue
            
            # 如果找不到具体用户名，返回通用信息
            logger.info("ℹ️ 未能获取具体用户名，但登录状态正常")
            return "已登录创作者中心"
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return "已登录创作者中心"
    
    async def _wait_for_manual_login(self) -> str:
        """等待用户手动登录"""
        try:
            logger.info("⏳ 等待用户手动登录...")
            logger.info("请在浏览器中完成登录，登录成功后会自动检测")
            
            # 设置超时时间（3分钟）
            timeout = 180000  # 180秒
            start_time = datetime.now()
            
            while True:
                # 检查是否超时
                if (datetime.now() - start_time).total_seconds() > timeout / 1000:
                    return "❌ 登录超时"
                
                # 检查登录状态
                is_logged_in, current_url = await self._check_login_status()
                if is_logged_in:
                    # 保存登录状态
                    await self._save_storage_state()
                    user_info = await self._get_user_info()
                    logger.success(f"✅ 检测到登录成功，跳转到发布页面: {current_url}")
                    return f"✅ 手动登录成功 - {user_info}"
                
                # 等待一段时间再检查
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"等待手动登录失败: {e}")
            return f"❌ 等待登录失败: {str(e)}"
    
    async def _save_storage_state(self):
        """保存浏览器存储状态"""
        try:
            # 使用持久化上下文时，状态会自动保存到user_data_dir
            # 这里只需要记录日志
            logger.info(f"💾 账号 {self.account_name} 的登录状态已自动保存到持久化目录")
            
        except Exception as e:
            logger.error(f"保存存储状态失败: {e}")
    
    async def _cleanup(self):
        """清理资源"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            if self.context:
                await self.context.close()
                self.context = None
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            logger.info("🔒 浏览器已关闭")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    def _get_firefox_path(self) -> Optional[str]:
        """获取Firefox浏览器路径"""
        try:
            # 尝试从配置文件读取
            config_file = Path("config.json")
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    firefox_path = config.get('firefox_path')
                    if firefox_path and Path(firefox_path).exists():
                        return firefox_path
            
            # 在macOS上查找常见的Firefox路径
            import platform
            if platform.system() == "Darwin":  # macOS
                common_paths = [
                    "/Applications/Firefox.app/Contents/MacOS/firefox",
                    "/Applications/Firefox Developer Edition.app/Contents/MacOS/firefox",
                    "~/Applications/Firefox.app/Contents/MacOS/firefox"
                ]
                
                for path_str in common_paths:
                    path = Path(path_str).expanduser()
                    if path.exists():
                        logger.info(f"[检测] 找到系统 Firefox: {path}")
                        return str(path)
            
            return None
            
        except Exception as e:
            logger.error(f"获取Firefox路径失败: {e}")
            return None


async def test_account(account_name: str, headless: bool = False) -> Tuple[bool, str]:
    """
    测试账号的便捷函数
    """
    tester = AccountTester(account_name, headless)
    return await tester.test_account()


def main():
    """主函数 - 用于命令行调用"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python account_tester.py <account_name> [--headless]")
        sys.exit(1)
    
    account_name = sys.argv[1]
    headless = '--headless' in sys.argv
    
    # 运行测试
    success, status = asyncio.run(test_account(account_name, headless))
    
    # 更新账号状态
    try:
        accounts_file = Path("accounts.json")
        if accounts_file.exists():
            with open(accounts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 更新对应账号的状态
            for account in data.get('accounts', []):
                if account['name'] == account_name:
                    account['status'] = status
                    account['last_login'] = datetime.now().isoformat() if success else account.get('last_login', '')
                    break
            
            # 保存更新
            with open(accounts_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
    except Exception as e:
        logger.error(f"更新账号状态失败: {e}")
    
    # 返回结果
    print(f"\n测试结果: {status}")
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
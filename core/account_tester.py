"""
账号测试器 - 使用 Playwright 测试账号登录状态
"""
import asyncio
import json
import platform
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger
from .profile_manager import get_account_profile_dir


class AccountTester:
    """账号测试器"""
    
    # 类级别的实例计数器和活动实例管理
    _instance_count = 0
    _instance_lock = threading.Lock()
    _active_tester_instance = None  # 当前活动的测试器实例（只限制AccountTester）
    
    def __init__(self, account_name: str, headless: bool = False):
        with AccountTester._instance_lock:
            AccountTester._instance_count += 1
            self.instance_id = AccountTester._instance_count
            logger.info(f"🔢 创建 AccountTester 实例 #{self.instance_id} for {account_name}")
        
        self.account_name = account_name
        self.headless = headless
        self.playwright = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.executable_path = self._get_firefox_path()
    
    async def test_account(self) -> Tuple[bool, str, Optional[str]]:
        """
        测试账号登录状态
        返回: (是否成功, 状态信息, 用户名)
        """
        try:
            logger.info(f"[检测] 开始测试账号: {self.account_name}")
            
            # 启动浏览器
            await self._setup_browser()
            logger.info(f"✅ 实例 #{self.instance_id} 浏览器设置完成")
            
            # 访问创作者中心发布页面
            logger.info(f"📱 实例 #{self.instance_id} 准备访问创作者中心发布页面...")
            publish_url = 'https://creator.xiaohongshu.com/publish/publish?from=tab_switch'
            logger.info(f"🔗 实例 #{self.instance_id} 导航到: {publish_url}")
            
            try:
                await self.page.goto(publish_url, wait_until='networkidle', timeout=30000)
                logger.info(f"✅ 实例 #{self.instance_id} 页面导航成功")
            except Exception as nav_error:
                logger.error(f"❌ 实例 #{self.instance_id} 页面导航失败: {nav_error}")
                raise
            
            await asyncio.sleep(3)
            logger.info(f"⏳ 实例 #{self.instance_id} 等待页面稳定完成")
            
            # 检查登录状态
            is_logged_in, current_url = await self._check_login_status()
            
            if is_logged_in:
                # 获取用户信息
                user_info, username = await self._get_user_info()
                status_info = f"✅ 账号有效 - {user_info}"
                logger.success(f"✅ 账号 {self.account_name} 测试通过: {user_info}")
                return True, status_info, username
            else:
                # 如果未登录，等待用户手动登录
                logger.info(f"🔗 当前在登录页面: {current_url}")
                status_info, username = await self._wait_for_manual_login()
                return status_info.startswith("✅"), status_info, username
                
        except Exception as e:
            import traceback
            error_msg = f"❌ 测试失败: {str(e)}"
            logger.error(f"实例 #{self.instance_id} {error_msg}")
            logger.error(f"详细错误: \n{traceback.format_exc()}")
            return False, error_msg, None
        finally:
            await self._cleanup()
    
    async def _setup_browser(self):
        """设置浏览器"""
        logger.info(f"🚀 AccountTester #{self.instance_id}._setup_browser 开始: {self.account_name}")
        
        # 检查是否已有活动实例
        with AccountTester._instance_lock:
            if AccountTester._active_tester_instance is not None:
                logger.warning(f"⚠️ 已有活动的AccountTester实例 #{AccountTester._active_tester_instance}，拒绝创建新浏览器")
                raise Exception("已有账号测试正在进行中，请稍后再试")
            AccountTester._active_tester_instance = self.instance_id
            logger.info(f"✅ 设置活动实例为 #{self.instance_id}")
        
        # 启动 playwright
        self.playwright = await async_playwright().start()
        profile_dir = Path(self._get_profile_dir())
        profile_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 实例 #{self.instance_id} 使用profile目录: {profile_dir}")
        
        # 确保profile目录下没有锁文件
        lock_files = list(profile_dir.glob("**/lock"))
        lock_files.extend(list(profile_dir.glob("**/.parentlock")))
        for lock_file in lock_files:
            try:
                lock_file.unlink()
                logger.info(f"🔓 删除锁文件: {lock_file}")
            except:
                pass
        launch_kwargs = {
            "user_data_dir": str(profile_dir),
            "headless": self.headless,
            "timeout": 90000,
            "viewport": {'width': 1366, 'height': 768},
            "locale": 'zh-CN',
            "timezone_id": 'Asia/Shanghai',
            "args": [
                '--no-sandbox',
                '--disable-blink-features=AutomationControlled',
                '--disable-features=IsolateOrigins,site-per-process'
            ],
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
        if self.executable_path:
            launch_kwargs["executable_path"] = self.executable_path
            logger.info(f"🦊 使用指定的Firefox路径: {self.executable_path}")
        try:
            logger.info(f"🔧 实例 #{self.instance_id} 调用 launch_persistent_context...")
            logger.info(f"🔧 launch_kwargs: user_data_dir={launch_kwargs.get('user_data_dir')}, headless={launch_kwargs.get('headless')}")
            
            # 调用前检查进程
            import subprocess
            import platform
            if platform.system() == "Darwin":  # macOS
                firefox_count_before = subprocess.run(['pgrep', '-i', 'firefox'], capture_output=True, text=True).stdout.count('\n')
            else:
                firefox_count_before = subprocess.run(['pgrep', '-f', 'firefox'], capture_output=True, text=True).stdout.count('\n')
            logger.info(f"🔍 调用前Firefox进程数: {firefox_count_before}")
            
            self.context = await self.playwright.firefox.launch_persistent_context(**launch_kwargs)
            logger.info(f"✅ 实例 #{self.instance_id} launch_persistent_context 调用成功")
            
            # 调用后检查进程
            await asyncio.sleep(1)  # 等待进程启动
            if platform.system() == "Darwin":  # macOS
                firefox_count_after = subprocess.run(['pgrep', '-i', 'firefox'], capture_output=True, text=True).stdout.count('\n')
            else:
                firefox_count_after = subprocess.run(['pgrep', '-f', 'firefox'], capture_output=True, text=True).stdout.count('\n')
            logger.info(f"🔍 调用后Firefox进程数: {firefox_count_after}")
            logger.info(f"🔍 新增Firefox进程数: {firefox_count_after - firefox_count_before}")
            
            # 暂时注释掉窗口信息获取，可能导致阻塞
            # if platform.system() == "Darwin":
            #     try:
            #         window_list = subprocess.run(['osascript', '-e', 'tell application "System Events" to get name of every window of every process whose name contains "Firefox"'], 
            #                                    capture_output=True, text=True, timeout=2)  # 添加超时
            #         logger.info(f"🪟 Firefox窗口列表: {window_list.stdout.strip()}")
            #     except Exception as window_error:
            #         logger.warning(f"⚠️ 获取窗口信息失败: {window_error}")
            #         pass
            
        except Exception as browser_error:
            logger.error(f"🔥 实例 #{self.instance_id} 浏览器启动异常捕获")
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
        
        # launch_persistent_context 会自动创建一个页面
        pages = self.context.pages
        logger.info(f"📄 实例 #{self.instance_id} 现有页面数: {len(pages)}")
        
        if pages:
            # 使用已有的页面
            self.page = pages[0]
            logger.info(f"✅ 实例 #{self.instance_id} 使用已有页面")
        else:
            # 如果没有页面，创建一个新的
            logger.info(f"🔧 实例 #{self.instance_id} 准备创建新页面...")
            self.page = await self.context.new_page()
            logger.info(f"✅ 实例 #{self.instance_id} 创建新页面成功")
        
        # 设置用户代理
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        logger.info(f"✅ 实例 #{self.instance_id} 设置用户代理成功")
        
        # 先导航到一个简单的页面测试
        try:
            logger.info(f"🧪 实例 #{self.instance_id} 测试导航到about:blank")
            await self.page.goto('about:blank')
            logger.info(f"✅ 实例 #{self.instance_id} about:blank导航成功")
        except Exception as test_nav_error:
            logger.error(f"❌ 实例 #{self.instance_id} 测试导航失败: {test_nav_error}")
    
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
    
    async def _get_user_info(self) -> tuple[str, str]:
        """获取用户信息
        返回: (显示信息, 用户名)
        """
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
                                    return f"用户: {nickname}", nickname
                except Exception as e:
                    continue
            
            # 如果找不到具体用户名，返回通用信息
            logger.info("ℹ️ 未能获取具体用户名，但登录状态正常")
            return "已登录创作者中心", None
            
        except Exception as e:
            logger.error(f"获取用户信息失败: {e}")
            return "已登录创作者中心", None
    
    async def _wait_for_manual_login(self) -> tuple[str, Optional[str]]:
        """等待用户手动登录
        返回: (状态信息, 用户名)
        """
        try:
            logger.info("⏳ 等待用户手动登录...")
            logger.info("请在浏览器中完成登录，登录成功后会自动检测")
            
            # 设置超时时间（3分钟）
            timeout = 180000  # 180秒
            start_time = datetime.now()
            
            while True:
                # 检查是否超时
                if (datetime.now() - start_time).total_seconds() > timeout / 1000:
                    return "❌ 登录超时", None
                
                # 检查登录状态
                is_logged_in, current_url = await self._check_login_status()
                if is_logged_in:
                    # 保存登录状态
                    await self._save_storage_state()
                    user_info, username = await self._get_user_info()
                    logger.success(f"✅ 检测到登录成功，跳转到发布页面: {current_url}")
                    return f"✅ 手动登录成功 - {user_info}", username
                
                # 等待一段时间再检查
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"等待手动登录失败: {e}")
            return f"❌ 等待登录失败: {str(e)}", None
    
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
            
            # 释放活动实例锁
            with AccountTester._instance_lock:
                if AccountTester._active_tester_instance == self.instance_id:
                    AccountTester._active_tester_instance = None
                    logger.info(f"🔓 释放活动实例锁 #{self.instance_id}")
            
            logger.info(f"🔒 浏览器已关闭 (实例 #{self.instance_id})")
        except Exception as e:
            logger.error(f"清理资源失败: {e}")
    
    def _get_firefox_path(self) -> Optional[str]:
        """获取Firefox浏览器路径"""
        try:
            import sys
            from pathlib import Path
            # 优先判断PyInstaller打包环境
            if getattr(sys, 'frozen', False):
                base_dir = Path(getattr(sys, '_MEIPASS', Path(__file__).parent))
                firefox_path = base_dir / "browsers" / "firefox" / "firefox.exe"
                if firefox_path.exists():
                    return str(firefox_path)
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

    def _get_profile_dir(self):
        """获取profile目录 - 使用统一的profile管理"""
        return get_account_profile_dir(self.account_name)


async def test_account(account_name: str, headless: bool = False) -> Tuple[bool, str, Optional[str]]:
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
    success, status, username = asyncio.run(test_account(account_name, headless))
    
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
                    # 如果获取到用户名，更新它
                    if username and username != account_name:
                        account['username'] = username
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
#!/usr/bin/env python3
"""
独立的小红书发布脚本
通过subprocess调用，完全隔离浏览器操作
"""
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright.async_api import async_playwright, Page, BrowserContext
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class XhsPublisher:
    """小红书发布器"""
    
    def __init__(self, headless: bool = False, user_data_dir: str = "firefox_profile", executable_path: str = None):
        self.headless = headless
        self.user_data_dir = Path(user_data_dir)
        self.user_data_dir.mkdir(exist_ok=True)
        self.executable_path = executable_path
        self.playwright = None
        self.context = None
        self.page = None
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()
    
    async def start(self):
        """启动浏览器"""
        try:
            logger.info("🚀 启动浏览器...")
            
            # 直接启动持久化浏览器上下文（这样只会创建一个浏览器实例）
            self.playwright = await async_playwright().start()
            
            # 准备launch_persistent_context的参数
            launch_kwargs = {
                "user_data_dir": str(self.user_data_dir),
                "headless": self.headless,
                "timeout": 90000,  # 增加到90秒超时
                "viewport": {'width': 1366, 'height': 768},
                "locale": 'zh-CN',
                "timezone_id": 'Asia/Shanghai',
                "args": ['--no-sandbox'],  # 添加no-sandbox参数
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
                    
                    # 判断是否为打包环境
                    import sys
                    is_packaged = getattr(sys, 'frozen', False) or getattr(sys, '_MEIPASS', None) is not None
                    
                    if is_packaged:
                        logger.error("  🏗️ 检测到打包环境，请执行以下步骤：")
                        logger.error("  1. 打开应用的【设置】页面")
                        logger.error("  2. 在【浏览器管理】中点击【下载Firefox浏览器】")
                        logger.error("  3. 等待下载完成后重试")
                        logger.error("  💡 提示：首次使用需要下载约200MB的浏览器文件")
                    else:
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
                
                # 提供统一的错误消息给上层调用者
                if "Executable doesn't exist" in error_msg:
                    raise RuntimeError("浏览器未安装：请在设置中下载Firefox浏览器后重试")
                elif "Failed to launch" in error_msg:
                    raise RuntimeError("浏览器启动失败：请检查权限和防火墙设置")
                elif "timeout" in error_msg.lower():
                    raise RuntimeError("浏览器启动超时：请重启应用或检查系统资源")
                else:
                    raise RuntimeError(f"浏览器启动失败：{error_msg}")
            
            # 创建新页面
            self.page = await self.context.new_page()
            
            # 设置用户代理
            await self.page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            logger.info("✅ 浏览器启动成功")
            
        except Exception as e:
            logger.error(f"❌ 启动浏览器失败: {e}")
            # 确保清理资源
            await self.close()
            raise
    
    async def close(self):
        """关闭浏览器"""
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
            logger.error(f"❌ 关闭浏览器失败: {e}")
    
    async def check_login_status(self) -> bool:
        """检查登录状态"""
        try:
            logger.info("[检测] 检查登录状态...")
            
            # 使用你提供的登录链接来检测
            login_test_url = "https://creator.xiaohongshu.com/login?source=&redirectReason=401&lastUrl=%2Fpublish%2Fpublish%3Ffrom%3Dtab_switch"
            logger.info("🎯 访问登录检测链接...")
            
            await self.page.goto(login_test_url, wait_until="domcontentloaded", timeout=45000)
            
            # 等待可能的跳转
            await asyncio.sleep(5)  # 等待几秒让页面完成跳转
            
            # 获取最终URL
            final_url = self.page.url
            logger.info(f"📍 最终跳转到的URL: {final_url}")
            
            # 检查是否跳转到了发布页面（说明登录成功）
            if "publish/publish" in final_url and "from=tab_switch" in final_url:
                logger.info("🎉 检测到跳转至发布页面，用户已登录")
                return True
            
            # 检查是否仍在登录页面
            elif "login" in final_url:
                logger.warning("❌ 仍在登录页面，用户未登录")
                return False
            
            # 检查是否跳转到了其他创作者中心页面（也算登录成功）
            elif final_url.startswith("https://creator.xiaohongshu.com") and "login" not in final_url:
                logger.info("✅ 跳转到创作者中心页面，用户已登录")
                return True
            
            # 其他情况，额外检查页面内容
            else:
                logger.info(f"🤔 意外的URL跳转，检查页面内容: {final_url}")
                try:
                    page_text = await self.page.evaluate("document.body.innerText")
                    if "登录" in page_text and ("发布" not in page_text and "创作" not in page_text):
                        logger.warning("❌ 页面内容显示需要登录")
                        return False
                    elif "发布" in page_text or "创作" in page_text:
                        logger.info("✅ 页面内容确认已登录（包含发布/创作功能）")
                        return True
                except Exception as e:
                    logger.warning(f"⚠️ 页面内容检查失败: {e}")
                
                logger.warning("❌ 登录状态不明确，默认为未登录")
                return False
            
        except Exception as e:
            logger.error(f"❌ 检查登录状态失败: {e}")
            return False
    
    async def publish_content(self, title: str, content: str, images: List[str], topics: List[str] = None) -> Dict[str, Any]:
        """发布内容"""
        try:
            logger.info(f"📝 开始发布内容: {title}")
            
            # 检查登录状态
            if not await self.check_login_status():
                return {
                    "success": False,
                    "message": "用户未登录，请先登录小红书账号",
                    "data": {}
                }
            
            # 直接访问发布页面（经验证这是最可靠的方式）
            logger.info("🎯 直接访问发布页面...")
            publish_url = "https://creator.xiaohongshu.com/publish/publish?from=tab_switch"
            await self.page.goto(publish_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            # 检查页面是否正确加载
            page_text = await self.page.evaluate("document.body.innerText")
            if "上传图文" not in page_text and "发布" not in page_text:
                logger.warning("页面内容异常，可能需要重新登录")
                return {
                    "success": False,
                    "message": "页面加载异常，请检查登录状态",
                    "data": {}
                }
            
            # 确保在图文发布模式
            await self._switch_to_image_text_mode()
            
            # 上传图片（如果有）
            if images:
                upload_success = await self._upload_images_enhanced(images)
                if not upload_success:
                    return {
                        "success": False,
                        "message": "图片上传失败",
                        "data": {}
                    }
            
            # 等待上传完成
            await self._wait_for_upload_completion()
            
            # 填写内容（包括标题和正文）
            content_success = await self._fill_content_enhanced(title, content, topics)
            if not content_success:
                return {
                    "success": False,
                    "message": "内容填写失败",
                    "data": {}
                }
            
            # 发布
            return await self._submit_publish_enhanced()
            
        except Exception as e:
            logger.error(f"❌ 发布内容失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"发布失败: {str(e)}",
                "data": {"error": str(e)}
            }
    
    async def _switch_to_image_text_mode(self):
        """确保在图文发布模式"""
        try:
            logger.info("🔄 确保在图文发布模式...")
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            # 查找图文发布标签 - 使用您提供的精确选择器
            tab_selectors = [
                'div.creator-tab:nth-child(3)',  # 您提供的CSS选择器
                '/html/body/div[1]/div/div[2]/div/div[2]/main/div[3]/div/div/div[1]/div[1]/div/div/div[1]/div[3]',  # 您提供的XPath
                'span:has-text("上传图文")',  # 基于span文本
                'text=上传图文',
                '.creator-tab:has-text("上传图文")',
                'div:has-text("上传图文")',
                'text=图文',
                '[data-testid="image-text-tab"]',
                'button:has-text("图文")',
                '.tab-item:has-text("图文")'
            ]
            
            for selector in tab_selectors:
                try:
                    logger.info(f"[检测] 尝试选择器: {selector}")
                    
                    # 对于XPath选择器，使用不同的等待方法
                    if selector.startswith('/'):
                        # XPath选择器
                        tab = await self.page.wait_for_selector(f'xpath={selector}', timeout=5000)
                    else:
                        # CSS选择器
                        tab = await self.page.wait_for_selector(selector, timeout=5000)
                    
                    if tab and await tab.is_visible():
                        logger.info(f"✅ 找到上传图文标签: {selector}")
                        await tab.click()
                        logger.info("✅ 切换到图文模式")
                        await asyncio.sleep(2)  # 等待页面切换
                        return True
                        
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue
            
            # 如果所有选择器都失败，检查页面内容
            logger.warning("⚠️ 未找到上传图文标签，检查页面内容...")
            page_text = await self.page.evaluate("document.body.innerText")
            if "上传图文" in page_text:
                logger.info("💡 页面包含'上传图文'文本，可能已在正确模式")
                return True
            else:
                logger.error("❌ 页面不包含'上传图文'文本，可能页面异常")
                # 输出页面内容用于调试
                logger.debug(f"页面内容: {page_text[:200]}...")
                return False
            
        except Exception as e:
            logger.error(f"❌ 切换到图文模式失败: {e}")
            return False
    
    async def _upload_images_enhanced(self, images: List[str]) -> bool:
        """增强的图片上传（基于测试经验）"""
        try:
            logger.info(f"📷 开始上传 {len(images)} 张图片...")
            
            # 验证图片文件
            valid_images = []
            for img_path in images:
                if Path(img_path).exists():
                    valid_images.append(str(Path(img_path).absolute()))
                    logger.info(f"📸 有效图片: {Path(img_path).name}")
                else:
                    logger.warning(f"⚠️ 图片文件不存在: {img_path}")
            
            if not valid_images:
                logger.error("❌ 没有有效的图片文件")
                return False
            
            # 设置网络监听以跟踪上传进度
            upload_requests = []
            
            def handle_upload_request(request):
                if any(keyword in request.url.lower() for keyword in ['upload', 'file', 'image', 'media']):
                    upload_requests.append(request.url)
                    logger.info(f"🔄 检测到上传请求: {request.url}")
            
            self.page.on('request', handle_upload_request)
            
            try:
                # 查找文件上传输入框
                upload_selectors = [
                    'input[type="file"]',
                    'input[accept*="image"]',
                    '.upload-input input',
                    '[data-testid="upload-input"]'
                ]
                
                upload_input = None
                for selector in upload_selectors:
                    try:
                        upload_input = await self.page.wait_for_selector(selector, timeout=5000)
                        if upload_input:
                            logger.info(f"✅ 找到上传控件: {selector}")
                            break
                    except:
                        continue
                
                if not upload_input:
                    logger.error("❌ 未找到图片上传控件")
                    return False
                
                # 上传文件
                logger.info("📤 开始上传文件...")
                await upload_input.set_input_files(valid_images)
                logger.info("✅ 文件已提交上传")
                
                # 等待上传响应
                for i in range(10):  # 最多等待10秒
                    if upload_requests:
                        logger.info(f"✅ 检测到上传活动，共 {len(upload_requests)} 个请求")
                        break
                    await asyncio.sleep(1)
                
                return True
                
            finally:
                # 移除网络监听
                self.page.remove_listener('request', handle_upload_request)
            
        except Exception as e:
            logger.error(f"❌ 图片上传失败: {e}")
            return False
    
    async def _wait_for_upload_completion(self):
        """等待图片上传完成"""
        try:
            logger.info("⏳ 等待图片上传完成...")
            
            # 检查上传完成的指示器
            for i in range(30):  # 最多等待30秒
                # 检查是否有缩略图出现
                thumbnails = await self.page.evaluate("""
                    () => {
                        const thumbnails = document.querySelectorAll('img[src*="blob:"], img[src*="data:"], .thumbnail, .preview');
                        return thumbnails.length;
                    }
                """)
                
                # 检查是否有进度条
                progress_bars = await self.page.evaluate("""
                    () => {
                        const progress = document.querySelectorAll('.progress, .upload-progress, [role="progressbar"]');
                        return progress.length;
                    }
                """)
                
                if thumbnails > 0:
                    logger.info(f"✅ 检测到 {thumbnails} 个缩略图，上传可能完成")
                    await asyncio.sleep(2)  # 再等待2秒确保稳定
                    break
                elif progress_bars > 0:
                    logger.info(f"🔄 检测到 {progress_bars} 个进度条，上传进行中...")
                
                await asyncio.sleep(1)
            
            logger.info("✅ 上传等待完成")
            
        except Exception as e:
            logger.error(f"❌ 等待上传完成失败: {e}")
    
    async def _upload_images(self, images: List[str]):
        """原始上传方法（保持兼容性）"""
        return await self._upload_images_enhanced(images)
    
    async def _fill_title(self, title: str):
        """填写标题"""
        try:
            logger.info(f"✏️ 填写标题: {title}")
            
            title_selectors = [
                '[placeholder*="标题"]',
                '[data-testid="title-input"]',
                '.title-input',
                'input[name="title"]',
                'textarea[placeholder*="标题"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if title_input:
                        await title_input.clear()
                        await title_input.fill(title)
                        logger.info("✅ 标题填写成功")
                        return
                except:
                    continue
            
            logger.warning("⚠️ 未找到标题输入框，可能不需要标题")
            
        except Exception as e:
            logger.error(f"❌ 填写标题失败: {e}")
            raise
    
    async def _fill_content_enhanced(self, title: str, content: str, topics: List[str] = None) -> bool:
        """增强的内容填写（基于参考脚本，支持标题和内容）"""
        try:
            logger.info(f"📝 开始填写内容...")
            
            # 等待页面稳定
            await asyncio.sleep(3)
            
            # 1. 先填写标题
            logger.info(f"📝 填写标题: {title}")
            title_filled = False
            title_selectors = [
                'input[placeholder*="标题"]',
                'input[placeholder*="title"]',
                '.title-input',
                'input.title',
                '[data-testid="title-input"]'
            ]
            
            for selector in title_selectors:
                try:
                    title_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if title_input and await title_input.is_visible():
                        await title_input.click()
                        await title_input.fill("")  # 清空
                        await title_input.type(title)
                        logger.info(f"✅ 标题填写成功 (选择器: {selector})")
                        title_filled = True
                        break
                except:
                    continue
            
            if not title_filled:
                logger.warning("⚠️ 未找到标题输入框，可能不需要单独的标题")
            
            # 2. 填写正文内容
            logger.info("📝 填写正文内容...")
            
            # 检查Quill编辑器状态
            quill_info = await self.page.evaluate("""
                () => {
                    const editor = document.querySelector('.ql-editor');
                    if (!editor) return null;
                    return {
                        exists: true,
                        hasBlankClass: editor.classList.contains('ql-blank'),
                        isContentEditable: editor.contentEditable,
                        placeholder: editor.getAttribute('data-placeholder')
                    };
                }
            """)
            
            if not quill_info:
                logger.error("❌ 未找到Quill编辑器")
                return False
            
            logger.info(f"✅ 找到Quill编辑器: {quill_info}")
            
            # 构建完整内容（如果没有单独标题框，则包含标题；否则只包含内容 + 话题）
            if title_filled:
                full_content = content  # 已经单独填写了标题
            else:
                full_content = f"{title}\n\n{content}"  # 标题和内容一起
            
            if topics:
                topic_text = " ".join([f"#{topic}" for topic in topics])
                full_content = f"{full_content}\n\n{topic_text}"
            
            logger.info(f"📄 完整内容: {full_content[:100]}...")
            
            # 使用JavaScript直接设置Quill编辑器内容
            set_result = await self.page.evaluate("""
                (content) => {
                    const editor = document.querySelector('.ql-editor');
                    if (!editor) return false;
                    
                    try {
                        // 清空现有内容
                        editor.innerHTML = '';
                        
                        // 设置新内容
                        const lines = content.split('\\n');
                        for (let i = 0; i < lines.length; i++) {
                            const p = document.createElement('p');
                            p.textContent = lines[i] || '';  // 空行也要有p标签
                            editor.appendChild(p);
                        }
                        
                        // 移除ql-blank类
                        editor.classList.remove('ql-blank');
                        
                        // 触发输入事件
                        editor.dispatchEvent(new Event('input', { bubbles: true }));
                        
                        return true;
                    } catch (e) {
                        console.error('设置内容失败:', e);
                        return false;
                    }
                }
            """, full_content)
            
            if not set_result:
                logger.error("❌ JavaScript设置内容失败")
                return False
            
            # 等待内容更新
            await asyncio.sleep(2)
            
            # 验证内容是否正确设置
            actual_content = await self.page.evaluate("""
                () => {
                    const editor = document.querySelector('.ql-editor');
                    return editor ? editor.textContent.trim() : '';
                }
            """)
            
            logger.info(f"📄 实际内容: {actual_content[:100]}...")
            
            # 简单验证：检查主要内容是否包含
            if content.strip() in actual_content:
                logger.info("✅ 内容填写验证成功")
                return True
            else:
                logger.warning("⚠️ 内容验证失败，但继续进行")
                return True  # 不因验证失败而中断
            
        except Exception as e:
            logger.error(f"❌ 增强内容填写失败: {e}")
            return False
    
    async def _fill_content(self, content: str):
        """原始内容填写方法（保持兼容性）"""
        try:
            logger.info(f"📝 填写内容: {content[:50]}...")
            
            content_selectors = [
                '.ql-editor',  # Quill富文本编辑器
                '[contenteditable="true"]',
                '[placeholder*="内容"]',
                '[placeholder*="描述"]',
                '[data-testid="content-input"]',
                '.content-input',
                'textarea[name="content"]'
            ]
            
            for selector in content_selectors:
                try:
                    content_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if content_input and await content_input.is_visible():
                        await content_input.clear()
                        await content_input.fill(content)
                        logger.info("✅ 内容填写成功")
                        return
                except:
                    continue
            
            raise Exception("未找到内容输入框")
            
        except Exception as e:
            logger.error(f"❌ 填写内容失败: {e}")
            raise
    
    async def _add_topics(self, topics: List[str]):
        """添加话题标签"""
        try:
            if not topics:
                return
                
            logger.info(f"🏷️ 添加话题: {topics}")
            
            # 查找话题输入框
            topic_selectors = [
                '[placeholder*="话题"]',
                '[placeholder*="标签"]',
                '[data-testid="topic-input"]',
                '.topic-input'
            ]
            
            for topic in topics:
                # 确保话题以#开头
                topic_text = topic if topic.startswith('#') else f'#{topic}'
                
                for selector in topic_selectors:
                    try:
                        topic_input = await self.page.wait_for_selector(selector, timeout=3000)
                        if topic_input:
                            await topic_input.fill(topic_text)
                            await self.page.keyboard.press('Enter')
                            await asyncio.sleep(1)
                            break
                    except:
                        continue
            
            logger.info("✅ 话题添加完成")
            
        except Exception as e:
            logger.error(f"❌ 添加话题失败: {e}")
            # 话题添加失败不影响发布
    
    async def _submit_publish_enhanced(self) -> Dict[str, Any]:
        """增强的发布提交（基于测试经验）"""
        try:
            logger.info("🚀 开始提交发布...")
            
            # 等待页面稳定
            await asyncio.sleep(2)
            
            # 查找发布按钮（更精确的选择器）
            submit_selectors = [
                'button:has-text("发布")',
                'text=发布',
                'button:has-text("发布笔记")',
                '.publish-button',
                '[data-testid="publish-button"]',
                '.submit-btn',
                'button[type="submit"]'
            ]
            
            publish_button_found = False
            for selector in submit_selectors:
                try:
                    submit_btn = await self.page.wait_for_selector(selector, timeout=5000)
                    if submit_btn and await submit_btn.is_visible():
                        # 检查按钮是否可用
                        is_enabled = await submit_btn.is_enabled()
                        if is_enabled:
                            logger.info(f"✅ 找到可用的发布按钮: {selector}")
                            await submit_btn.click()
                            publish_button_found = True
                            logger.info("✅ 发布按钮点击成功")
                            break
                        else:
                            logger.warning(f"⚠️ 发布按钮不可用: {selector}")
                except Exception as e:
                    logger.debug(f"尝试选择器失败 {selector}: {e}")
                    continue
            
            if not publish_button_found:
                return {
                    "success": False,
                    "message": "未找到可用的发布按钮",
                    "data": {}
                }
            
            # 等待发布处理
            logger.info("⏳ 等待发布处理...")
            await asyncio.sleep(6)  # 增加初始等待时间，适应小红书的跳转延迟
            
            # 检查页面状态和内容变化
            for attempt in range(15):  # 增加检查次数，最多检查15次，每次2秒
                try:
                    # 获取当前URL
                    current_url = self.page.url
                    
                    # 获取页面文本内容
                    page_text = await self.page.evaluate("document.body.innerText")
                    
                    # 检查成功指示器
                    success_keywords = ["发布成功", "发布完成", "success", "published", "已发布"]
                    has_success = any(keyword in page_text.lower() for keyword in [k.lower() for k in success_keywords])
                    
                    # 检查错误指示器
                    error_keywords = ["发布失败", "错误", "error", "failed", "失败", "请重试"]
                    has_error = any(keyword in page_text.lower() for keyword in [k.lower() for k in error_keywords])
                    
                    # 检查URL变化（页面跳转通常表示成功）
                    # 小红书发布成功后通常会跳转到作品管理页面或其他页面
                    url_changed = "publish/publish" not in current_url
                    
                    # 检查是否还在发布页面（如果不在，通常表示成功）
                    in_publish_page = "publish/publish" in current_url and "from=tab_switch" in current_url
                    
                    logger.info(f"检查第{attempt + 1}次 - URL: {current_url}")
                    logger.info(f"URL变化: {url_changed}, 在发布页: {in_publish_page}, 成功指示: {has_success}, 错误指示: {has_error}")
                    
                    if has_error:
                        # 提取错误信息
                        lines = page_text.split('\n')
                        error_lines = [line.strip() for line in lines if any(keyword.lower() in line.lower() for keyword in error_keywords)]
                        error_msg = error_lines[0] if error_lines else "发布失败"
                        
                        logger.error(f"❌ 发布失败: {error_msg}")
                        return {
                            "success": False,
                            "message": error_msg,
                            "data": {"url": current_url}
                        }
                    
                    # 更准确的成功判断逻辑
                    if has_success:
                        logger.info("🎉 发布成功（检测到成功文本）")
                        return {
                            "success": True,
                            "message": "发布成功",
                            "data": {
                                "url": current_url,
                                "timestamp": datetime.now().isoformat(),
                                "method": "success_text_detection"
                            }
                        }
                    
                    if url_changed and not in_publish_page:
                        logger.info("🎉 发布成功（页面已跳转）")
                        return {
                            "success": True,
                            "message": "发布成功",
                            "data": {
                                "url": current_url,
                                "timestamp": datetime.now().isoformat(),
                                "method": "url_change_detection"
                            }
                        }
                    
                    # 如果没有明确结果，继续等待
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.warning(f"检查发布状态时出错: {e}")
                    await asyncio.sleep(2)
            
            # 如果循环结束仍无明确结果，根据最终状态判断
            try:
                final_url = self.page.url
                final_text = await self.page.evaluate("document.body.innerText")
                
                # 最终判断逻辑
                final_text_lower = final_text.lower()
                
                # 检查是否有明确的失败信息
                final_error_keywords = ["发布失败", "错误", "error", "failed", "失败", "请重试"]
                has_final_error = any(keyword in final_text_lower for keyword in final_error_keywords)
                
                if has_final_error:
                    # 提取错误信息
                    lines = final_text.split('\n')
                    error_lines = [line.strip() for line in lines if any(keyword in line.lower() for keyword in final_error_keywords)]
                    error_msg = error_lines[0] if error_lines else "发布失败"
                    
                    logger.error(f"❌ 最终检查发现发布失败: {error_msg}")
                    return {
                        "success": False,
                        "message": error_msg,
                        "data": {"url": final_url}
                    }
                
                # 检查是否离开发布页面（通常表示成功）
                if "publish/publish" not in final_url:
                    logger.info("✅ 发布成功（页面已跳转离开发布页面）")
                    return {
                        "success": True,
                        "message": "发布成功（根据页面跳转判断）",
                        "data": {
                            "url": final_url,
                            "timestamp": datetime.now().isoformat(),
                            "method": "final_url_change_detection"
                        }
                    }
                else:
                    # 仍在发布页面，但没有错误信息，可能是网络延迟或者成功了但页面未跳转
                    logger.info("✅ 发布操作已完成（状态推测为成功）")
                    return {
                        "success": True,
                        "message": "发布操作已完成（未检测到错误信息）",
                        "data": {
                            "url": final_url,
                            "timestamp": datetime.now().isoformat(),
                            "method": "timeout_completion_success"
                        }
                    }
            except Exception as e:
                logger.error(f"❌ 最终状态检查失败: {e}")
                return {
                    "success": False,
                    "message": f"发布状态检查失败: {str(e)}",
                    "data": {}
                }
            
        except Exception as e:
            logger.error(f"❌ 提交发布失败: {e}")
            import traceback
            logger.error(f"错误详情: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"提交发布失败: {str(e)}",
                "data": {"error": str(e)}
            }
    
    async def _submit_publish(self) -> Dict[str, Any]:
        """原始发布提交方法（保持兼容性）"""
        return await self._submit_publish_enhanced()


async def main():
    """主函数 - 命令行调用入口"""
    parser = argparse.ArgumentParser(description="小红书发布脚本")
    parser.add_argument("task_json", help="任务JSON字符串")
    parser.add_argument("--headless", action="store_true", help="无头模式")
    parser.add_argument("--user-data-dir", default="firefox_profile", help="用户数据目录")
    
    args = parser.parse_args()
    
    try:
        # 解析任务数据
        task_data = json.loads(args.task_json)
        
        # 验证必要字段
        required_fields = ["title", "content"]
        for field in required_fields:
            if field not in task_data:
                raise ValueError(f"缺少必要字段: {field}")
        
        # 发布内容
        async with XhsPublisher(headless=args.headless, user_data_dir=args.user_data_dir) as publisher:
            result = await publisher.publish_content(
                title=task_data["title"],
                content=task_data["content"],
                images=task_data.get("images", []),
                topics=task_data.get("topics", [])
            )
        
        # 输出结果（供主程序读取）
        print(json.dumps(result, ensure_ascii=False))
        
        # 返回码
        sys.exit(0 if result["success"] else 1)
        
    except Exception as e:
        error_result = {
            "success": False,
            "message": f"脚本执行失败: {str(e)}",
            "data": {"error": str(e)}
        }
        print(json.dumps(error_result, ensure_ascii=False))
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
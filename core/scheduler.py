"""
简单任务调度器
使用QTimer + QProcess进行真异步调度，避免GUI阻塞
"""
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Callable
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from loguru import logger

from .models import PublishTask, TaskStatus, PublishResult
from .storage import TaskStorage, ConfigStorage
from .process_manager import ProcessManager


class SimpleScheduler(QObject):
    """简单任务调度器"""
    
    # 信号定义
    task_started = pyqtSignal(str)      # 任务开始执行 (task_id)
    task_completed = pyqtSignal(str, dict)  # 任务完成 (task_id, result)
    task_failed = pyqtSignal(str, str)  # 任务失败 (task_id, error_message)
    scheduler_status = pyqtSignal(str)  # 调度器状态变化
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # 存储管理器 - 适配打包环境
        self.task_storage = TaskStorage()
        
        # 配置管理 - 使用打包环境适配的配置
        try:
            from packaging.app_config import get_app_config
            self.config = get_app_config()
            logger.info("📋 使用打包环境配置")
        except ImportError:
            # 开发环境fallback
            self.config_storage = ConfigStorage()
            self.config = self.config_storage.get_config()
            logger.info("📋 使用开发环境配置")
        
        # 进程管理器（替代subprocess）
        self.process_manager = ProcessManager(max_processes=2, parent=self)
        self.process_manager.process_finished.connect(self._handle_task_success)
        self.process_manager.process_failed.connect(self._handle_task_error)
        self.process_manager.process_started.connect(lambda task_id: self.task_started.emit(task_id))
        
        # QTimer定时器
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_and_execute_tasks)
        
        # 状态
        self.is_running = False
        self.executing_tasks = set()  # 正在执行的任务ID
        
        # 定期清理定时器（每半小时清理一次）
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self._periodic_cleanup)
        self.cleanup_timer.start(30 * 60 * 1000)  # 30分钟
        
        logger.info("✅ 简单调度器初始化完成（已集成进程管理器）")
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        
        # 启动定时器，每分钟检查一次
        interval_ms = self.config.check_interval_seconds * 1000
        self.timer.start(interval_ms)
        
        logger.info(f"🚀 调度器已启动，检查间隔: {self.config.check_interval_seconds}秒")
        self.scheduler_status.emit("运行中")
        
        # 立即执行一次检查
        self.check_and_execute_tasks()
    
    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        try:
            self.is_running = False
            
            # 停止定时器
            if self.timer and self.timer.isActive():
                self.timer.stop()
            
            # 清理所有进程
            if hasattr(self, 'process_manager'):
                self.process_manager.kill_all_processes()
            
            # 清理执行中的任务记录
            self.executing_tasks.clear()
            
            logger.info("🛑 调度器已停止")
            self.scheduler_status.emit("已停止")
            
        except Exception as e:
            logger.error(f"❌ 停止调度器失败: {e}")
    
    def add_task(self, task: PublishTask) -> bool:
        """添加任务"""
        if not task or not task.title.strip():
            logger.error("❌ 无效的任务数据")
            return False
        
        success = self.task_storage.add_task(task)
        if success:
            logger.info(f"➕ 添加任务: {task.title} (发布时间: {task.publish_time})")
        return success
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        if not task_id or not task_id.strip():
            logger.error("❌ 无效的任务ID")
            return False
        
        success = self.task_storage.delete_task(task_id)
        if success:
            logger.info(f"🗑️ 删除任务: {task_id[:8]}")
        return success
    
    def get_all_tasks(self) -> List[PublishTask]:
        """获取所有任务"""
        return self.task_storage.load_tasks()
    
    def get_task_by_id(self, task_id: str) -> Optional[PublishTask]:
        """根据ID获取任务"""
        if not task_id or not task_id.strip():
            return None
        return self.task_storage.get_task_by_id(task_id)
    
    def check_and_execute_tasks(self):
        """检查并执行到期任务"""
        if not self.is_running:
            return
        
        try:
            # 获取准备执行的任务
            ready_tasks = self.task_storage.get_ready_tasks()
            
            # 获取可重试的失败任务
            retry_tasks = self.task_storage.get_failed_retry_tasks()
            
            all_ready_tasks = ready_tasks + retry_tasks
            
            if not all_ready_tasks:
                logger.debug("⏸️ 没有需要执行的任务")
                return
            
            logger.info(f"🎯 发现 {len(all_ready_tasks)} 个待执行任务")
            
            for task in all_ready_tasks:
                if task.id in self.executing_tasks:
                    logger.debug(f"⏳ 任务正在执行中，跳过: {task.title}")
                    continue
                
                # 检查发布间隔限制
                if not self._check_publish_interval():
                    logger.warning("⚠️ 发布间隔太短，跳过本次执行")
                    continue
                
                # 异步执行任务
                self._execute_task_async(task)
                
        except Exception as e:
            logger.error(f"❌ 检查任务时出错: {e}")
    
    def _check_publish_interval(self) -> bool:
        """检查发布间隔"""
        # 获取最近完成的任务
        all_tasks = self.task_storage.load_tasks()
        completed_tasks = [t for t in all_tasks if t.status == TaskStatus.COMPLETED]
        
        if not completed_tasks:
            return True
        
        # 按更新时间排序，获取最近的一个
        completed_tasks.sort(key=lambda x: x.updated_time or datetime.min, reverse=True)
        last_task = completed_tasks[0]
        
        # 检查时间间隔
        if last_task.updated_time:
            from datetime import timedelta
            min_interval = timedelta(minutes=self.config.min_publish_interval_minutes)
            time_since_last = datetime.now() - last_task.updated_time
            
            if time_since_last < min_interval:
                remaining = min_interval - time_since_last
                logger.warning(f"⚠️ 距离上次发布时间过短，还需等待 {remaining.total_seconds():.0f} 秒")
                return False
        
        return True
    
    def _execute_task_async(self, task: PublishTask):
        """异步执行任务 - 直接调用版本"""
        try:
            # 检查是否已有任务在执行中（避免多个浏览器实例）
            if len(self.executing_tasks) > 0:
                logger.warning(f"⚠️ 已有 {len(self.executing_tasks)} 个任务在执行，拒绝新任务")
                self._handle_task_error(task.id, "已有任务在执行中，请等待完成")
                return
            
            # 标记任务开始执行
            task.mark_running()
            self.task_storage.update_task(task)
            self.executing_tasks.add(task.id)
            
            logger.info(f"🚀 开始执行任务: {task.title}")
            self.task_started.emit(task.id)
            
            # 直接调用发布功能而不是子进程
            import asyncio
            from .publisher import XhsPublisher
            
            async def publish_task():
                try:
                    # 判断是否为打包环境
                    import sys
                    is_packaged = getattr(sys, 'frozen', False) or getattr(sys, '_MEIPASS', None) is not None
                    
                    if is_packaged:
                        # 打包环境 - 直接使用app_config的配置（已经处理了Firefox检测和fallback）
                        try:
                            from packaging.app_config import app_config_manager
                            firefox_config = app_config_manager.get_firefox_launch_config()
                            logger.info("🦊 使用打包环境的Firefox配置")
                            logger.info(f"🌐 Firefox配置: headless={firefox_config.get('headless', False)}, "
                                      f"executable_path={firefox_config.get('executable_path', 'Playwright默认')}")
                        except Exception as config_error:
                            logger.warning(f"⚠️ 无法加载打包配置，使用默认配置: {config_error}")
                            firefox_config = {
                                "user_data_dir": self.config.firefox_profile_path,
                                "headless": self.config.headless_mode,
                                "timeout": 90000,
                                "args": ['--no-sandbox']
                            }
                    else:
                        # 开发环境 - 需要检查Firefox是否可用
                        import os
                        from pathlib import Path
                        
                        # 检查浏览器是否已安装
                        if sys.platform == "darwin":
                            custom_path = Path.home() / "Library" / "Application Support" / "XhsPublisher" / "playwright-browsers"
                            default_path = Path.home() / "Library" / "Caches" / "ms-playwright"
                        elif sys.platform == "win32":
                            custom_path = Path.home() / "AppData" / "Local" / "XhsPublisher" / "playwright-browsers"
                            default_path = Path.home() / "AppData" / "Local" / "ms-playwright"
                        else:
                            custom_path = Path.home() / ".cache" / "XhsPublisher" / "playwright-browsers"
                            default_path = Path.home() / ".cache" / "ms-playwright"
                        
                        firefox_found = False
                        # 优先使用默认路径（如果存在）
                        if default_path.exists():
                            # 在macOS下搜索所有可能的Firefox应用
                            if sys.platform == "darwin":
                                # 搜索 Nightly.app 和 Firefox.app
                                firefox_apps = list(default_path.glob("firefox-*/firefox/Nightly.app/Contents/MacOS/firefox"))
                                if not firefox_apps:
                                    firefox_apps = list(default_path.glob("firefox-*/firefox/Firefox.app/Contents/MacOS/firefox"))
                                if firefox_apps:
                                    firefox_found = True
                            else:
                                # Windows和Linux的检测逻辑
                                firefox_paths = list(default_path.glob("firefox-*/firefox*"))
                                if firefox_paths:
                                    firefox_found = True
                            
                            if firefox_found:
                                # 不设置环境变量，让 Playwright 使用默认路径
                                if 'PLAYWRIGHT_BROWSERS_PATH' in os.environ:
                                    del os.environ['PLAYWRIGHT_BROWSERS_PATH']
                                logger.info(f"📁 使用默认浏览器路径: {default_path}")
                        
                        # 否则使用自定义路径
                        if not firefox_found and custom_path.exists():
                            if sys.platform == "darwin":
                                # 搜索 Nightly.app 和 Firefox.app
                                firefox_apps = list(custom_path.glob("firefox-*/firefox/Nightly.app/Contents/MacOS/firefox"))
                                if not firefox_apps:
                                    firefox_apps = list(custom_path.glob("firefox-*/firefox/Firefox.app/Contents/MacOS/firefox"))
                                if firefox_apps:
                                    firefox_found = True
                            else:
                                # Windows和Linux的检测逻辑
                                firefox_paths = list(custom_path.glob("firefox-*/firefox*"))
                                if firefox_paths:
                                    firefox_found = True
                            
                            if firefox_found:
                                os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(custom_path)
                                logger.info(f"📁 使用自定义浏览器路径: {custom_path}")
                        
                        if not firefox_found:
                            error_msg = "浏览器未安装：请在设置中下载Firefox浏览器后重试"
                            logger.error(f"❌ {error_msg}")
                            raise Exception(error_msg)
                        
                        # 开发环境 - 使用简单配置
                        firefox_config = {
                            "user_data_dir": self.config.firefox_profile_path,
                            "headless": self.config.headless_mode,
                            "timeout": 60000
                        }
                        
                        logger.info(f"🌐 Firefox配置: headless={firefox_config.get('headless', False)}, "
                                  f"executable_path={firefox_config.get('executable_path', 'Playwright默认')}")
                    
                    # 只传递 XhsPublisher 支持的参数，但不传递user_data_dir让其自动检测
                    publisher_params = {
                        'headless': firefox_config.get('headless', False),
                        # 移除user_data_dir参数，让XhsPublisher自动检测正确路径
                        'executable_path': firefox_config.get('executable_path', None)
                    }
                    
                    async with XhsPublisher(**publisher_params) as publisher:
                        logger.info(f"✅ 浏览器启动成功，开始发布内容")
                        result = await publisher.publish_content(
                            title=task.title,
                            content=task.content,
                            images=task.images,
                            topics=task.topics
                        )
                        return result
                except Exception as e:
                    logger.error(f"❌ 发布失败: {e}")
                    raise
            
            # 在新线程中运行异步任务
            import threading
            
            def run_async_task():
                try:
                    logger.info(f"🔄 在新线程中启动异步任务: {task.title}")
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(publish_task())
                    loop.close()
                    
                    logger.info(f"✅ 任务执行完成: {task.title}")
                    
                    # 检查实际发布结果
                    if result and result.get("success", False):
                        # 真正的成功
                        logger.info(f"✅ 任务执行成功: {task.title}")
                        self._handle_task_success(task.id, result)
                    else:
                        # 实际发布失败
                        error_msg = result.get("message", "发布失败") if result else "未获取到发布结果"
                        logger.error(f"❌ 任务发布失败: {task.title} - {error_msg}")
                        self._handle_task_error(task.id, error_msg)
                        
                except Exception as e:
                    logger.error(f"❌ 任务执行失败: {task.title} - {e}")
                    # 失败回调
                    self._handle_task_error(task.id, str(e))
            
            thread = threading.Thread(target=run_async_task, daemon=True)
            thread.start()
            logger.info(f"🚀 任务线程已启动: {task.title}")
            
            return  # 直接返回，不再使用process_manager
            
        except Exception as e:
            logger.error(f"❌ 启动任务执行失败: {e}")
            self._handle_task_error(task.id, str(e))
    
    def _run_subprocess_async(self, task: PublishTask, cmd: List[str]):
        """使用进程管理器执行任务（真异步，不阻塞GUI）"""
        try:
            # 标记任务开始执行
            task.mark_running()
            self.task_storage.update_task(task)
            self.executing_tasks.add(task.id)
            
            logger.info(f"🚀 开始执行任务: {task.title}")
            
            # 使用进程管理器启动任务
            if self.process_manager.start_task(task, cmd):
                logger.info(f"✅ 任务已提交给进程管理器: {task.title}")
            else:
                # 进程池满，任务会自动加入等待队列
                logger.info(f"📋 任务已加入等待队列: {task.title}")
                
        except Exception as e:
            logger.error(f"❌ 启动任务失败: {e}")
            self._handle_task_error(task.id, str(e))
    
    def _handle_task_success(self, task_id: str, result: dict):
        """处理任务成功（从ProcessManager接收task_id）"""
        try:
            task = self.task_storage.get_task_by_id(task_id)
            if not task:
                logger.error(f"❌ 找不到任务: {task_id}")
                return
            
            # 双重检查确保真正成功
            if result and result.get("success", False):
                task.mark_completed(result.get("message", "发布成功"))
                self.task_storage.update_task(task)
                self.executing_tasks.discard(task_id)
                
                logger.info(f"✅ 任务执行成功: {task.title}")
                self.task_completed.emit(task_id, result)
            else:
                # 即使调用了success回调，但实际结果是失败
                error_msg = result.get("message", "发布失败") if result else "未获取到发布结果"
                logger.error(f"❌ 任务实际执行失败: {task.title} - {error_msg}")
                self._handle_task_error(task_id, error_msg)
            
        except Exception as e:
            logger.error(f"❌ 处理任务成功结果失败: {e}")
    
    def _handle_task_error(self, task_id: str, error_message: str):
        """处理任务失败（从ProcessManager接收task_id）"""
        try:
            task = self.task_storage.get_task_by_id(task_id)
            if not task:
                logger.error(f"❌ 找不到任务: {task_id}")
                # 创建临时任务对象以发送信号
                self.executing_tasks.discard(task_id)
                self.task_failed.emit(task_id, error_message)
                return
                
            task.mark_failed(error_message)
            self.task_storage.update_task(task)
            self.executing_tasks.discard(task_id)
            
            if task.can_retry():
                logger.warning(f"⚠️ 任务失败，将重试: {task.title} (重试次数: {task.retry_count}/{task.max_retries})")
            else:
                logger.error(f"❌ 任务失败且无法重试: {task.title}")
            
            self.task_failed.emit(task_id, error_message)
            
        except Exception as e:
            logger.error(f"❌ 处理任务失败时出错: {e}")
    
    def get_task_statistics(self) -> dict:
        """获取任务统计"""
        tasks = self.task_storage.load_tasks()
        
        stats = {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING]),
            "running": len([t for t in tasks if t.status == TaskStatus.RUNNING]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED]),
            "executing": len(self.executing_tasks)
        }
        
        return stats
    
    def cleanup_old_tasks(self, keep_days: int = 7):
        """清理旧任务"""
        try:
            self.task_storage.cleanup_old_tasks(keep_days)
            logger.info(f"🧹 清理了超过 {keep_days} 天的旧任务")
        except Exception as e:
            logger.error(f"❌ 清理旧任务失败: {e}")
    
    def _periodic_cleanup(self):
        """定期清理任务"""
        try:
            # 清理已完成的进程
            if hasattr(self, 'process_manager'):
                self.process_manager.cleanup_finished_processes()
            
            # 清理超过7天的旧任务
            self.cleanup_old_tasks(7)
            
            logger.debug("🧹 定期清理完成")
            
        except Exception as e:
            logger.error(f"❌ 定期清理失败: {e}")
    
    def publish_immediately(self, title: str, content: str, images: List[str], topics: List[str] = None) -> str:
        """立即发布"""
        task = PublishTask.create_new(
            title=title,
            content=content,
            images=images,
            topics=topics or [],
            publish_time=datetime.now()
        )
        
        if self.add_task(task):
            logger.info(f"📤 创建立即发布任务: {task.title}")
            # 立即检查执行
            self.check_and_execute_tasks()
            return task.id
        else:
            raise Exception("创建任务失败")
    
    def execute_task_immediately(self, task_id: str) -> bool:
        """立即执行指定任务（跳过发布间隔检查）"""
        if not self.is_running:
            logger.warning("⚠️ 调度器未运行，无法立即执行任务")
            return False
        
        try:
            # 检查是否有任务正在执行中
            if self.executing_tasks:
                logger.warning(f"⚠️ 已有任务正在执行中，请等待完成: {list(self.executing_tasks)}")
                return False
            
            # 获取任务
            task = self.task_storage.get_task_by_id(task_id)
            if not task:
                logger.error(f"❌ 找不到任务: {task_id}")
                return False
            
            # 检查任务状态
            if task.status != TaskStatus.PENDING:
                logger.warning(f"⚠️ 任务状态不是等待中，无法执行: {task.title} (状态: {task.status})")
                return False
            
            # 检查是否已在执行中
            if task.id in self.executing_tasks:
                logger.warning(f"⏳ 任务正在执行中: {task.title}")
                return False
            
            logger.info(f"🚀 立即执行任务（跳过间隔检查）: {task.title}")
            
            # 直接执行任务，跳过发布间隔检查
            self._execute_task_async(task)
            return True
            
        except Exception as e:
            logger.error(f"❌ 立即执行任务失败: {e}")
            return False
    
    def cleanup_resources(self):
        """清理所有资源（应用退出时调用）"""
        try:
            logger.info("🧹 开始清理调度器资源...")
            
            # 停止调度器
            self.stop()
            
            # 清理进程管理器
            if hasattr(self, 'process_manager'):
                self.process_manager.kill_all_processes()
            
            # 清理存储资源
            if hasattr(self, 'task_storage'):
                self.task_storage.cleanup_resources()
            
            if hasattr(self, 'config_storage'):
                self.config_storage.cleanup_resources()
            
            # 清理定时器
            if hasattr(self, 'timer') and self.timer:
                self.timer.stop()
                self.timer.deleteLater()
                self.timer = None
            
            # 清理状态
            self.executing_tasks.clear()
            
            logger.info("✅ 调度器资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 清理调度器资源失败: {e}")
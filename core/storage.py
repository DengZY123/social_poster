"""
数据存储管理
"""
import json
from typing import List, Optional
from pathlib import Path
from loguru import logger

from .models import PublishTask, AppConfig, TaskStatus


class TaskStorage:
    """任务存储管理器 - 内存存储版本"""
    
    def __init__(self, file_path: str = "tasks.json"):
        # 内存中存储任务列表
        self._tasks: List[PublishTask] = []
        logger.info("🧠 TaskStorage初始化 - 使用内存存储")
    
    def load_tasks(self) -> List[PublishTask]:
        """加载所有任务"""
        logger.debug(f"📋 加载了 {len(self._tasks)} 个任务")
        return self._tasks.copy()
    
    def save_tasks(self, tasks: List[PublishTask]):
        """保存所有任务到内存"""
        self._tasks = tasks.copy()
        logger.debug(f"💾 内存保存了 {len(tasks)} 个任务")
    
    def add_task(self, task: PublishTask) -> bool:
        """添加任务"""
        try:
            self._tasks.append(task)
            logger.info(f"➕ 添加任务: {task.title} (ID: {task.id[:8]})")
            return True
        except Exception as e:
            logger.error(f"❌ 添加任务失败: {e}")
            return False
    
    def update_task(self, task: PublishTask) -> bool:
        """更新任务"""
        try:
            for i, t in enumerate(self._tasks):
                if t.id == task.id:
                    self._tasks[i] = task
                    logger.debug(f"🔄 更新任务: {task.title} (ID: {task.id[:8]})")
                    return True
            
            logger.warning(f"⚠️ 未找到要更新的任务: {task.id}")
            return False
        except Exception as e:
            logger.error(f"❌ 更新任务失败: {e}")
            return False
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        try:
            initial_count = len(self._tasks)
            self._tasks = [t for t in self._tasks if t.id != task_id]
            
            if len(self._tasks) < initial_count:
                logger.info(f"🗑️ 删除任务: {task_id[:8]}")
                return True
            else:
                logger.warning(f"⚠️ 未找到要删除的任务: {task_id}")
                return False
        except Exception as e:
            logger.error(f"❌ 删除任务失败: {e}")
            return False
    
    def get_task_by_id(self, task_id: str) -> Optional[PublishTask]:
        """根据ID获取任务"""
        for task in self._tasks:
            if task.id == task_id:
                return task
        return None
    
    def get_pending_tasks(self) -> List[PublishTask]:
        """获取待执行的任务"""
        return [t for t in self._tasks if t.status == TaskStatus.PENDING]
    
    def get_ready_tasks(self) -> List[PublishTask]:
        """获取准备执行的任务（时间已到）"""
        return [t for t in self._tasks if t.is_ready_to_execute()]
    
    def get_failed_retry_tasks(self) -> List[PublishTask]:
        """获取可重试的失败任务"""
        return [t for t in self._tasks if t.can_retry()]
    
    def cleanup_old_tasks(self, keep_days: int = 7):
        """清理旧任务"""
        from datetime import datetime, timedelta
        
        try:
            cutoff_time = datetime.now() - timedelta(days=keep_days)
            
            # 保留未完成的任务和最近的已完成任务
            filtered_tasks = []
            for task in self._tasks:
                if (task.status in [TaskStatus.PENDING, TaskStatus.RUNNING] or
                    (task.updated_time and task.updated_time > cutoff_time)):
                    filtered_tasks.append(task)
            
            removed_count = len(self._tasks) - len(filtered_tasks)
            if removed_count > 0:
                self._tasks = filtered_tasks
                logger.info(f"🧹 清理了 {removed_count} 个旧任务")
            
        except Exception as e:
            logger.error(f"❌ 清理旧任务失败: {e}")
    
    def cleanup_resources(self):
        """清理所有资源（应用退出时调用）"""
        try:
            self._tasks.clear()
            logger.info("✅ 内存存储资源清理完成")
        except Exception as e:
            logger.error(f"❌ 清理存储资源失败: {e}")


class ConfigStorage:
    """配置存储管理器"""
    
    def __init__(self, file_path: str = "config.json"):
        self.file_path = Path(file_path)
        self.config = self.load_config()
    
    def load_config(self) -> AppConfig:
        """加载配置"""
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return AppConfig.from_dict(data)
            else:
                # 使用默认配置
                config = AppConfig()
                self.save_config(config)
                return config
        except Exception as e:
            logger.error(f"加载配置失败: {e}, 使用默认配置")
            return AppConfig()
    
    def save_config(self, config: AppConfig):
        """保存配置"""
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(config.to_dict(), f, ensure_ascii=False, indent=2)
            logger.debug("配置已保存")
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
    
    def get_config(self) -> AppConfig:
        """获取当前配置"""
        return self.config
    
    def update_config(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
        self.save_config(self.config)
    
    def cleanup_resources(self):
        """清理配置存储资源"""
        try:
            # 清理临时配置文件
            temp_config = self.file_path.with_suffix('.tmp')
            if temp_config.exists():
                temp_config.unlink()
                logger.debug("🧹 清理临时配置文件")
            
            logger.info("✅ 配置存储资源清理完成")
            
        except Exception as e:
            logger.error(f"❌ 清理配置存储资源失败: {e}")
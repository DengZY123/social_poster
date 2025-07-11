"""
数据模型定义
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Optional
from enum import Enum
import uuid
import json


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中  
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败


@dataclass
class PublishTask:
    """发布任务"""
    id: str
    title: str
    content: str
    images: List[str]           # 图片文件路径列表
    topics: List[str]           # 话题标签
    publish_time: datetime      # 发布时间
    status: TaskStatus = TaskStatus.PENDING
    created_time: Optional[datetime] = None
    updated_time: Optional[datetime] = None
    result_message: str = ""    # 执行结果消息
    retry_count: int = 0        # 重试次数
    max_retries: int = 3        # 最大重试次数
    
    def __post_init__(self):
        if self.created_time is None:
            self.created_time = datetime.now()
        self.updated_time = datetime.now()
    
    @classmethod
    def create_new(cls, title: str, content: str, images: List[str], 
                   topics: List[str], publish_time: datetime) -> "PublishTask":
        """创建新任务"""
        return cls(
            id=str(uuid.uuid4()),
            title=title,
            content=content,
            images=images,
            topics=topics,
            publish_time=publish_time
        )
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        # 处理日期时间序列化
        if self.publish_time:
            data['publish_time'] = self.publish_time.isoformat()
        if self.created_time:
            data['created_time'] = self.created_time.isoformat()
        if self.updated_time:
            data['updated_time'] = self.updated_time.isoformat()
        # 处理枚举序列化
        data['status'] = self.status.value
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> "PublishTask":
        """从字典创建对象"""
        # 处理日期时间反序列化
        if 'publish_time' in data and isinstance(data['publish_time'], str):
            data['publish_time'] = datetime.fromisoformat(data['publish_time'])
        if 'created_time' in data and isinstance(data['created_time'], str):
            data['created_time'] = datetime.fromisoformat(data['created_time'])
        if 'updated_time' in data and isinstance(data['updated_time'], str):
            data['updated_time'] = datetime.fromisoformat(data['updated_time'])
        # 处理枚举反序列化
        if 'status' in data and isinstance(data['status'], str):
            data['status'] = TaskStatus(data['status'])
        
        return cls(**data)
    
    def is_ready_to_execute(self) -> bool:
        """检查是否准备执行"""
        return (self.status == TaskStatus.PENDING and 
                self.publish_time <= datetime.now())
    
    def can_retry(self) -> bool:
        """检查是否可以重试"""
        return (self.status == TaskStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def mark_running(self):
        """标记为执行中"""
        self.status = TaskStatus.RUNNING
        self.updated_time = datetime.now()
    
    def mark_completed(self, message: str = "发布成功"):
        """标记为完成"""
        self.status = TaskStatus.COMPLETED
        self.result_message = message
        self.updated_time = datetime.now()
    
    def mark_failed(self, message: str):
        """标记为失败"""
        self.status = TaskStatus.FAILED
        self.result_message = message
        self.retry_count += 1
        self.updated_time = datetime.now()
    
    def reset_for_retry(self):
        """重置任务状态以便重试"""
        self.status = TaskStatus.PENDING
        self.result_message = None
        self.updated_time = datetime.now()


@dataclass 
class AppConfig:
    """应用配置"""
    firefox_profile_path: str = "firefox_profile"
    tasks_file_path: str = "tasks.json"
    log_file_path: str = "app.log"
    check_interval_seconds: int = 60        # 检查任务的间隔（秒）
    publish_timeout_seconds: int = 300      # 发布超时时间（秒）
    min_publish_interval_minutes: int = 5   # 最小发布间隔（分钟）
    headless_mode: bool = False             # 是否无头模式
    browser_launch_timeout: int = 90        # 浏览器启动超时（秒）
    page_load_timeout: int = 60             # 页面加载超时（秒）
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        """从字典创建对象"""
        return cls(**data)


class PublishResult:
    """发布结果"""
    def __init__(self, success: bool, message: str, data: dict = None):
        self.success = success
        self.message = message
        self.data = data or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PublishResult":
        """从字典创建对象"""
        result = cls(
            success=data["success"],
            message=data["message"],
            data=data.get("data", {})
        )
        if "timestamp" in data:
            result.timestamp = datetime.fromisoformat(data["timestamp"])
        return result
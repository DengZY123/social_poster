#!/usr/bin/env python3
"""
测试立即发布功能
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt6.QtCore import QTimer

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from core.models import PublishTask, TaskStatus
from core.scheduler import SimpleScheduler
from gui.components.task_detail_table import TaskDetailTable
from loguru import logger


class TestWindow(QMainWindow):
    """测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("测试立即发布功能")
        self.setGeometry(100, 100, 1200, 600)
        
        # 设置中央组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # 创建调度器
        self.scheduler = SimpleScheduler(self)
        
        # 创建任务表格
        self.task_table = TaskDetailTable()
        self.task_table.set_scheduler(self.scheduler)
        
        # 连接信号
        self.task_table.task_publish_immediately_requested.connect(self.on_publish_immediately)
        
        layout.addWidget(self.task_table)
        
        # 创建测试任务
        self.create_test_task()
        
        # 设置定时器刷新
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(2000)  # 每2秒刷新
        
        logger.info("✅ 测试窗口初始化完成")
    
    def create_test_task(self):
        """创建测试任务"""
        test_task = PublishTask.create_new(
            title="测试立即发布按钮点击事件",
            content="这是一个专门用于测试立即发布按钮点击事件的任务。点击绿色按钮应该触发立即发布流程。#测试 #立即发布",
            images=[],
            topics=["测试", "立即发布"],
            publish_time=datetime.now() + timedelta(hours=1)
        )
        
        if self.scheduler.add_task(test_task):
            logger.info(f"✅ 创建测试任务: {test_task.title}")
        else:
            logger.error("❌ 创建测试任务失败")
    
    def on_publish_immediately(self, task_id: str):
        """处理立即发布请求"""
        logger.info(f"🎉 测试成功！收到立即发布请求: {task_id}")
        
        # 获取任务信息
        task = self.scheduler.get_task_by_id(task_id)
        if task:
            logger.info(f"📝 任务详情: {task.title}")
            logger.info(f"📅 原发布时间: {task.publish_time}")
            
            # 模拟立即发布（更新时间为当前时间）
            task.publish_time = datetime.now()
            task.updated_time = datetime.now()
            self.scheduler.task_storage.update_task(task)
            
            logger.info(f"✅ 任务时间已更新为当前时间: {task.publish_time}")
            
            # 刷新显示
            self.refresh_display()
        else:
            logger.error(f"❌ 找不到任务: {task_id}")
    
    def refresh_display(self):
        """刷新显示"""
        self.task_table.refresh_table()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置日志
    logger.add(
        "test_immediate_publish.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        level="INFO"
    )
    
    window = TestWindow()
    window.show()
    
    logger.info("🚀 启动测试应用")
    logger.info("📋 测试步骤:")
    logger.info("1. 查看表格中的等待中任务")
    logger.info("2. 点击绿色的「立即发布」按钮")
    logger.info("3. 观察控制台和日志文件中的输出")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
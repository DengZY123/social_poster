"""
控制面板组件
包含文件操作、发布控制、状态显示等功能
"""
import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QGroupBox, QPushButton,
    QLabel, QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont
from loguru import logger

# 添加core模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.models import PublishTask, TaskStatus


class ControlPanel(QWidget):
    """控制面板组件"""
    
    # 信号定义
    import_excel_requested = pyqtSignal(str)  # 导入Excel文件
    add_sample_tasks_requested = pyqtSignal()  # 添加示例任务
    clear_all_tasks_requested = pyqtSignal()  # 清空所有任务
    publish_all_requested = pyqtSignal()  # 发布所有任务
    stop_publishing_requested = pyqtSignal()  # 停止发布
    refresh_status_requested = pyqtSignal()  # 刷新状态
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scheduler = None  # 调度器引用，由父组件设置
        self.setup_ui()
        self.setup_status_timer()
        
    def setup_ui(self):
        """设置界面"""
        layout = QHBoxLayout(self)
        layout.setSpacing(15)
        
        # 文件操作组
        file_group = self.create_file_operations_group()
        layout.addWidget(file_group)
        
        # 发布控制组
        publish_group = self.create_publish_control_group()
        layout.addWidget(publish_group)
        
        # 状态显示组
        status_group = self.create_status_display_group()
        layout.addWidget(status_group)
        
        layout.addStretch()
    
    def create_file_operations_group(self) -> QGroupBox:
        """创建文件操作组"""
        group = QGroupBox("文件操作")
        layout = QHBoxLayout(group)
        
        # 导入Excel按钮 - 绿色
        self.import_excel_btn = QPushButton("📂 导入Excel")
        self.import_excel_btn.clicked.connect(self.on_import_excel)
        self.import_excel_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        layout.addWidget(self.import_excel_btn)
        
        # 添加示例按钮 - 紫色
        self.add_sample_btn = QPushButton("📝 添加示例")
        self.add_sample_btn.clicked.connect(self.on_add_sample_tasks)
        self.add_sample_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
            QPushButton:pressed {
                background-color: #512b92;
            }
        """)
        layout.addWidget(self.add_sample_btn)
        
        # 清空任务按钮 - 红色
        self.clear_tasks_btn = QPushButton("🗑️ 清空任务")
        self.clear_tasks_btn.clicked.connect(self.on_clear_all_tasks)
        self.clear_tasks_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:pressed {
                background-color: #bd2130;
            }
        """)
        layout.addWidget(self.clear_tasks_btn)
        
        return group
    
    def create_publish_control_group(self) -> QGroupBox:
        """创建发布控制组"""
        group = QGroupBox("发布控制")
        layout = QHBoxLayout(group)
        
        # 发布所有按钮
        self.publish_all_btn = QPushButton("🚀 发布所有")
        self.publish_all_btn.clicked.connect(self.on_publish_all)
        self.publish_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        layout.addWidget(self.publish_all_btn)
        
        # 停止发布按钮
        self.stop_publish_btn = QPushButton("🛑 停止发布")
        self.stop_publish_btn.clicked.connect(self.on_stop_publishing)
        self.stop_publish_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #e8690b;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
        """)
        layout.addWidget(self.stop_publish_btn)
        
        # 刷新状态按钮
        self.refresh_btn = QPushButton("🔄 刷新状态")
        self.refresh_btn.clicked.connect(self.on_refresh_status)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
            QPushButton:pressed {
                background-color: #495057;
            }
        """)
        layout.addWidget(self.refresh_btn)
        
        return group
    
    def create_status_display_group(self) -> QGroupBox:
        """创建状态显示组"""
        group = QGroupBox("状态显示")
        layout = QVBoxLayout(group)
        
        # 运行状态
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("📊 运行状态:"))
        self.status_label = QLabel("准备中...")
        self.status_label.setStyleSheet("color: #6c757d; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 任务统计
        stats_layout = QHBoxLayout()
        stats_layout.addWidget(QLabel("📈 任务统计:"))
        self.stats_label = QLabel("总数: 0")
        self.stats_label.setStyleSheet("color: #495057;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        # 存储状态
        storage_layout = QHBoxLayout()
        storage_layout.addWidget(QLabel("💾 存储状态:"))
        self.storage_label = QLabel("正常")
        self.storage_label.setStyleSheet("color: #28a745; font-weight: bold;")
        storage_layout.addWidget(self.storage_label)
        storage_layout.addStretch()
        layout.addLayout(storage_layout)
        
        return group
    
    def setup_status_timer(self):
        """设置状态更新定时器"""
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # 每2秒更新一次状态
    
    def set_scheduler(self, scheduler):
        """设置调度器引用"""
        self.scheduler = scheduler
        self.update_status()
    
    def on_import_excel(self):
        """导入Excel文件"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "选择Excel文件",
            "",
            "Excel文件 (*.xlsx *.xls)"
        )
        
        if file_path:
            logger.info(f"📂 选择导入Excel文件: {file_path}")
            self.import_excel_requested.emit(file_path)
        
    def on_add_sample_tasks(self):
        """添加示例任务"""
        reply = QMessageBox.question(
            self, "确认添加", 
            "确定要添加3个示例任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("📝 添加示例任务")
            self.add_sample_tasks_requested.emit()
    
    def on_clear_all_tasks(self):
        """清空所有任务"""
        reply = QMessageBox.question(
            self, "确认清空", 
            "确定要清空所有任务吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("🗑️ 清空所有任务")
            self.clear_all_tasks_requested.emit()
    
    def on_publish_all(self):
        """发布所有任务"""
        if not self.scheduler:
            QMessageBox.warning(self, "错误", "调度器未初始化")
            return
            
        # 获取待发布任务数量
        tasks = self.scheduler.get_all_tasks()
        pending_tasks = [t for t in tasks if t.status == TaskStatus.PENDING]
        
        if not pending_tasks:
            QMessageBox.information(self, "提示", "没有待发布的任务")
            return
        
        reply = QMessageBox.question(
            self, "确认发布", 
            f"确定要发布 {len(pending_tasks)} 个待发布任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info(f"🚀 开始发布所有任务 ({len(pending_tasks)}个)")
            self.publish_all_requested.emit()
    
    def on_stop_publishing(self):
        """停止发布"""
        reply = QMessageBox.question(
            self, "确认停止", 
            "确定要停止当前的发布任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            logger.info("🛑 停止发布")
            self.stop_publishing_requested.emit()
    
    def on_refresh_status(self):
        """刷新状态"""
        logger.info("🔄 手动刷新状态")
        self.refresh_status_requested.emit()
        self.update_status()
    
    def update_status(self):
        """更新状态显示"""
        if not self.scheduler:
            return
            
        try:
            # 更新调度器状态
            if self.scheduler.is_running:
                self.status_label.setText("运行中")
                self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
            else:
                self.status_label.setText("已停止")
                self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
            
            # 更新任务统计
            stats = self.scheduler.get_task_statistics()
            stats_text = f"总数: {stats['total']} (等待: {stats['pending']}, 执行中: {stats['running']}, 完成: {stats['completed']}, 失败: {stats['failed']})"
            self.stats_label.setText(stats_text)
            
            # 更新按钮状态
            has_pending = stats['pending'] > 0
            has_running = stats['running'] > 0
            
            self.publish_all_btn.setEnabled(has_pending and self.scheduler.is_running)
            self.stop_publish_btn.setEnabled(has_running)
            
        except Exception as e:
            logger.error(f"❌ 更新状态失败: {e}")
            self.status_label.setText("错误")
            self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
    
    @pyqtSlot(str)
    def on_scheduler_status_changed(self, status: str):
        """调度器状态变化"""
        self.status_label.setText(status)
        if status == "运行中":
            self.status_label.setStyleSheet("color: #28a745; font-weight: bold;")
        elif status == "已停止":
            self.status_label.setStyleSheet("color: #dc3545; font-weight: bold;")
        else:
            self.status_label.setStyleSheet("color: #6c757d; font-weight: bold;")
    
    def set_import_enabled(self, enabled: bool):
        """设置导入按钮的启用状态"""
        if hasattr(self, 'import_excel_btn'):
            self.import_excel_btn.setEnabled(enabled)
            if not enabled:
                self.import_excel_btn.setText("📂 导入中...")
            else:
                self.import_excel_btn.setText("📂 导入Excel")
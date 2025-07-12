"""
任务编辑对话框
用于编辑任务的标题、内容、图片、话题和发布时间
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QTextEdit, QPushButton, QDateTimeEdit,
    QLabel, QMessageBox, QListWidget, QListWidgetItem,
    QGroupBox, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QDateTime
from PyQt6.QtGui import QFont
from loguru import logger

# 添加core模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.models import PublishTask


class TaskEditDialog(QDialog):
    """任务编辑对话框"""
    
    # 信号：任务更新成功 (task)
    task_updated = pyqtSignal(PublishTask)
    
    def __init__(self, task: PublishTask, parent=None):
        super().__init__(parent)
        self.task = task
        self.setup_ui()
        self.load_task_data()
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle(f"编辑任务 - {self.task.title}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout(self)
        
        # 创建表单
        form_widget = self.create_form()
        layout.addWidget(form_widget)
        
        # 底部按钮
        button_layout = self.create_buttons()
        layout.addLayout(button_layout)
    
    def create_form(self) -> QWidget:
        """创建表单"""
        splitter = QSplitter(Qt.Orientation.Vertical)
        
        # 基本信息组
        basic_group = QGroupBox("基本信息")
        basic_layout = QFormLayout(basic_group)
        
        # 标题
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("请输入任务标题")
        basic_layout.addRow("标题:", self.title_edit)
        
        # 发布时间
        self.time_edit = QDateTimeEdit()
        self.time_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.time_edit.setCalendarPopup(True)
        self.time_edit.setMinimumDateTime(QDateTime.currentDateTime())
        basic_layout.addRow("发布时间:", self.time_edit)
        
        splitter.addWidget(basic_group)
        
        # 内容组
        content_group = QGroupBox("正文内容")
        content_layout = QVBoxLayout(content_group)
        
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("请输入正文内容...")
        self.content_edit.setFont(QFont("Microsoft YaHei", 10))
        content_layout.addWidget(self.content_edit)
        
        # 字数统计
        self.char_count_label = QLabel("字数: 0")
        content_layout.addWidget(self.char_count_label)
        self.content_edit.textChanged.connect(self.update_char_count)
        
        splitter.addWidget(content_group)
        
        # 图片组
        image_group = QGroupBox("图片地址（每行一个URL或本地路径）")
        image_layout = QVBoxLayout(image_group)
        
        self.images_edit = QTextEdit()
        self.images_edit.setPlaceholderText("https://example.com/image1.jpg\nhttps://example.com/image2.jpg\n/path/to/local/image.jpg")
        self.images_edit.setMaximumHeight(100)
        image_layout.addWidget(self.images_edit)
        
        splitter.addWidget(image_group)
        
        # 话题组
        topic_group = QGroupBox("话题标签（用空格或逗号分隔）")
        topic_layout = QVBoxLayout(topic_group)
        
        self.topics_edit = QLineEdit()
        self.topics_edit.setPlaceholderText("美食 旅行 生活分享")
        topic_layout.addWidget(self.topics_edit)
        
        splitter.addWidget(topic_group)
        
        return splitter
    
    def create_buttons(self) -> QHBoxLayout:
        """创建按钮"""
        layout = QHBoxLayout()
        layout.addStretch()
        
        # 保存按钮
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_task)
        self.save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        layout.addWidget(self.save_btn)
        
        # 取消按钮
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        layout.addWidget(self.cancel_btn)
        
        return layout
    
    def load_task_data(self):
        """加载任务数据"""
        self.title_edit.setText(self.task.title)
        self.content_edit.setText(self.task.content)
        
        # 设置发布时间
        qt_datetime = QDateTime.fromString(
            self.task.publish_time.strftime("%Y-%m-%d %H:%M:%S"),
            "yyyy-MM-dd HH:mm:ss"
        )
        self.time_edit.setDateTime(qt_datetime)
        
        # 设置图片列表
        if self.task.images:
            self.images_edit.setText("\n".join(self.task.images))
        
        # 设置话题
        if self.task.topics:
            # 移除#号显示
            topics = [t.lstrip('#') for t in self.task.topics]
            self.topics_edit.setText(" ".join(topics))
    
    def update_char_count(self):
        """更新字数统计"""
        char_count = len(self.content_edit.toPlainText())
        self.char_count_label.setText(f"字数: {char_count}")
    
    def save_task(self):
        """保存任务"""
        try:
            # 获取输入值
            title = self.title_edit.text().strip()
            content = self.content_edit.toPlainText().strip()
            
            # 验证必填字段
            if not title:
                QMessageBox.warning(self, "错误", "标题不能为空")
                return
            
            if not content:
                QMessageBox.warning(self, "错误", "内容不能为空")
                return
            
            # 解析图片列表
            images_text = self.images_edit.toPlainText().strip()
            images = []
            if images_text:
                for line in images_text.split('\n'):
                    line = line.strip()
                    if line:
                        images.append(line)
            
            # 验证图片
            if not images:
                reply = QMessageBox.question(
                    self, "确认", 
                    "未添加图片，确定要继续吗？",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply != QMessageBox.StandardButton.Yes:
                    return
            
            # 解析话题
            topics_text = self.topics_edit.text().strip()
            topics = []
            if topics_text:
                # 支持空格和逗号分隔
                import re
                topic_list = re.split(r'[,，\s]+', topics_text)
                for topic in topic_list:
                    topic = topic.strip()
                    if topic:
                        # 确保以#开头
                        if not topic.startswith('#'):
                            topic = f'#{topic}'
                        topics.append(topic)
            
            # 获取发布时间
            publish_time = self.time_edit.dateTime().toPyDateTime()
            
            # 检查时间是否合理
            if publish_time <= datetime.now():
                QMessageBox.warning(self, "错误", "发布时间必须是未来时间")
                return
            
            # 更新任务对象
            self.task.title = title
            self.task.content = content
            self.task.images = images
            self.task.topics = topics
            self.task.publish_time = publish_time
            self.task.updated_time = datetime.now()
            
            # 发出更新信号
            self.task_updated.emit(self.task)
            
            # 关闭对话框
            self.accept()
            
            logger.info(f"✅ 任务编辑成功: {title}")
            
        except Exception as e:
            logger.error(f"保存任务失败: {e}")
            QMessageBox.critical(self, "错误", f"保存任务失败: {str(e)}")
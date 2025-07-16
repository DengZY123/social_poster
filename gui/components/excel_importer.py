# -*- coding: utf-8 -*-
"""
异步Excel导入器组件
使用QThread实现真异步Excel处理，避免GUI阻塞
"""
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from PyQt6.QtCore import QThread, QObject, pyqtSignal, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFileDialog, QDateTimeEdit, QSpinBox,
                             QTextEdit, QProgressBar, QMessageBox, QFrame)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from loguru import logger

from core.models import PublishTask
from utils.excel_importer import ExcelImporter


class AsyncExcelImporter(QObject):
    """异步Excel导入器"""
    
    # 信号定义
    import_started = pyqtSignal()                                    # 开始导入
    import_progress = pyqtSignal(int, str)                          # 进度更新 (进度%, 消息)
    import_completed = pyqtSignal(bool, str, list)                  # 导入完成 (成功, 消息, 任务列表)
    validation_completed = pyqtSignal(bool, str)                    # 验证完成 (成功, 消息)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.excel_importer = ExcelImporter()
        self.import_thread = None
        self.is_importing = False
        
    def validate_file_async(self, file_path: str):
        """异步验证Excel文件"""
        if self.is_importing:
            logger.warning("正在导入中，请稍后")
            return
            
        # 使用QTimer延迟执行，避免阻塞GUI
        QTimer.singleShot(100, lambda: self._do_validation(file_path))
    
    def _do_validation(self, file_path: str):
        """执行验证"""
        try:
            is_valid, message = self.excel_importer.validate_file(file_path)
            self.validation_completed.emit(is_valid, message)
        except Exception as e:
            logger.error(f"验证文件异常: {e}")
            self.validation_completed.emit(False, f"验证异常: {e}")
    
    def import_excel_async(self, file_path: str, start_time: Optional[datetime] = None, 
                          interval_minutes: int = 30):
        """异步导入Excel文件"""
        if self.is_importing:
            logger.warning("正在导入中，请稍后")
            return
            
        self.is_importing = True
        self.import_started.emit()
        
        # 创建导入线程
        self.import_thread = ExcelImportThread(
            file_path=file_path,
            start_time=start_time,
            interval_minutes=interval_minutes,
            parent=self
        )
        
        # 连接信号
        self.import_thread.progress_updated.connect(self.import_progress.emit)
        self.import_thread.import_finished.connect(self._on_import_finished)
        self.import_thread.finished.connect(self._on_thread_finished)
        
        # 启动线程
        self.import_thread.start()
        logger.info(f"🚀 启动异步Excel导入: {file_path}")
    
    def _on_import_finished(self, success: bool, message: str, tasks: List[PublishTask]):
        """导入完成处理"""
        self.import_completed.emit(success, message, tasks)
        logger.info(f"📋 Excel导入完成: {message}")
    
    def _on_thread_finished(self):
        """线程完成处理"""
        self.is_importing = False
        if self.import_thread:
            self.import_thread.deleteLater()
            self.import_thread = None
        logger.debug("Excel导入线程已清理")
    
    def cancel_import(self):
        """取消导入"""
        if self.import_thread and self.import_thread.isRunning():
            self.import_thread.requestInterruption()
            self.import_thread.wait(3000)  # 等待3秒
            logger.info("Excel导入已取消")


class ExcelImportThread(QThread):
    """Excel导入线程"""
    
    progress_updated = pyqtSignal(int, str)                         # 进度更新
    import_finished = pyqtSignal(bool, str, list)                  # 导入完成
    
    def __init__(self, file_path: str, start_time: Optional[datetime] = None,
                 interval_minutes: int = 30, parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.start_time = start_time
        self.interval_minutes = interval_minutes
        self.excel_importer = ExcelImporter()
    
    def run(self):
        """线程执行函数"""
        try:
            # 发送开始信号
            self.progress_updated.emit(0, "开始导入Excel文件...")
            
            # 检查是否被中断
            if self.isInterruptionRequested():
                return
            
            # 验证文件
            self.progress_updated.emit(10, "验证Excel文件...")
            is_valid, message = self.excel_importer.validate_file(self.file_path)
            if not is_valid:
                self.import_finished.emit(False, message, [])
                return
            
            # 检查是否被中断
            if self.isInterruptionRequested():
                return
            
            # 导入任务
            self.progress_updated.emit(30, "解析Excel数据...")
            success, message, tasks = self.excel_importer.import_tasks(
                self.file_path, 
                self.start_time, 
                self.interval_minutes
            )
            
            # 检查是否被中断
            if self.isInterruptionRequested():
                return
            
            # 完成导入
            self.progress_updated.emit(100, f"导入完成: {message}")
            self.import_finished.emit(success, message, tasks)
            
        except Exception as e:
            logger.error(f"Excel导入线程异常: {e}")
            self.import_finished.emit(False, f"导入异常: {e}", [])


class ExcelImportWidget(QWidget):
    """Excel导入界面组件"""
    
    # 信号定义
    tasks_imported = pyqtSignal(list)  # 任务导入完成 (任务列表)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.async_importer = AsyncExcelImporter(self)
        self.selected_file = ""
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """初始化界面"""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # 标题
        title_label = QLabel("📂 Excel批量导入")
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2c3e50; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # 文件选择区域
        file_frame = QFrame()
        file_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        file_frame.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px; }")
        file_layout = QVBoxLayout(file_frame)
        
        # 文件选择按钮
        file_btn_layout = QHBoxLayout()
        self.select_file_btn = QPushButton("📁 选择Excel文件")
        self.select_file_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """)
        
        self.create_template_btn = QPushButton("📝 创建模板")
        self.create_template_btn.setStyleSheet("""
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """)
        
        file_btn_layout.addWidget(self.select_file_btn)
        file_btn_layout.addWidget(self.create_template_btn)
        file_btn_layout.addStretch()
        file_layout.addLayout(file_btn_layout)
        
        # 选中文件显示
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        file_layout.addWidget(self.file_label)
        
        layout.addWidget(file_frame)
        
        # 导入设置区域
        settings_frame = QFrame()
        settings_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        settings_frame.setStyleSheet("QFrame { border: 1px solid #bdc3c7; border-radius: 5px; padding: 10px; }")
        settings_layout = QVBoxLayout(settings_frame)
        
        settings_title = QLabel("⚙️ 导入设置")
        settings_title.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        settings_title.setStyleSheet("color: #2c3e50; margin-bottom: 5px;")
        settings_layout.addWidget(settings_title)
        
        # 开始时间设置
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("开始时间:"))
        self.start_time_edit = QDateTimeEdit()
        self.start_time_edit.setDateTime(datetime.now() + timedelta(minutes=5))
        self.start_time_edit.setCalendarPopup(True)
        self.start_time_edit.setStyleSheet("padding: 5px;")
        time_layout.addWidget(self.start_time_edit)
        time_layout.addStretch()
        settings_layout.addLayout(time_layout)
        
        # 发布间隔设置
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("发布间隔:"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(5, 1440)  # 5分钟到24小时
        self.interval_spin.setValue(30)
        self.interval_spin.setSuffix(" 分钟")
        self.interval_spin.setStyleSheet("padding: 5px;")
        interval_layout.addWidget(self.interval_spin)
        interval_layout.addStretch()
        settings_layout.addLayout(interval_layout)
        
        layout.addWidget(settings_frame)
        
        # 操作按钮区域
        btn_layout = QHBoxLayout()
        
        self.validate_btn = QPushButton("[检测] 验证文件")
        self.validate_btn.setEnabled(False)
        self.validate_btn.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
            QPushButton:pressed {
                background-color: #d35400;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        
        self.import_btn = QPushButton("📥 导入任务")
        self.import_btn.setEnabled(False)
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:pressed {
                background-color: #1e8449;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        
        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
                color: #7f8c8d;
            }
        """)
        
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addWidget(self.import_btn)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                text-align: center;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                background-color: #3498db;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # 状态信息
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setReadOnly(True)
        self.status_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                background-color: #f8f9fa;
                color: #2c3e50;
                font-family: Consolas, monospace;
            }
        """)
        layout.addWidget(self.status_text)
        
        layout.addStretch()
    
    def connect_signals(self):
        """连接信号"""
        # 按钮信号
        self.select_file_btn.clicked.connect(self.select_file)
        self.create_template_btn.clicked.connect(self.create_template)
        self.validate_btn.clicked.connect(self.validate_file)
        self.import_btn.clicked.connect(self.import_tasks)
        self.cancel_btn.clicked.connect(self.cancel_import)
        
        # 导入器信号
        self.async_importer.import_started.connect(self.on_import_started)
        self.async_importer.import_progress.connect(self.on_import_progress)
        self.async_importer.import_completed.connect(self.on_import_completed)
        self.async_importer.validation_completed.connect(self.on_validation_completed)
    
    def select_file(self):
        """选择Excel文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "选择Excel文件", 
            "", 
            "Excel文件 (*.xlsx *.xls);;所有文件 (*)"
        )
        
        if file_path:
            self.selected_file = file_path
            self.file_label.setText(f"已选择: {os.path.basename(file_path)}")
            self.file_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            self.validate_btn.setEnabled(True)
            self.append_status(f"✅ 选择文件: {file_path}")
    
    def create_template(self):
        """创建Excel模板"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存Excel模板",
            "小红书发布模板.xlsx",
            "Excel文件 (*.xlsx);;所有文件 (*)"
        )
        
        if file_path:
            try:
                importer = ExcelImporter()
                if importer.create_template(file_path):
                    self.append_status(f"✅ 模板创建成功: {file_path}")
                    QMessageBox.information(self, "成功", f"Excel模板创建成功！\n{file_path}")
                else:
                    self.append_status(f"❌ 模板创建失败")
                    QMessageBox.warning(self, "失败", "Excel模板创建失败！")
            except Exception as e:
                self.append_status(f"❌ 模板创建异常: {e}")
                QMessageBox.critical(self, "错误", f"创建模板时发生错误:\n{e}")
    
    def validate_file(self):
        """验证Excel文件"""
        if not self.selected_file:
            QMessageBox.warning(self, "警告", "请先选择Excel文件！")
            return
        
        self.append_status("[检测] 开始验证文件...")
        self.async_importer.validate_file_async(self.selected_file)
    
    def import_tasks(self):
        """导入任务"""
        if not self.selected_file:
            QMessageBox.warning(self, "警告", "请先选择Excel文件！")
            return
        
        start_time = self.start_time_edit.dateTime().toPython()
        interval_minutes = self.interval_spin.value()
        
        self.append_status(f"📥 开始导入任务 (开始时间: {start_time}, 间隔: {interval_minutes}分钟)...")
        self.async_importer.import_excel_async(self.selected_file, start_time, interval_minutes)
    
    def cancel_import(self):
        """取消导入"""
        self.async_importer.cancel_import()
        self.append_status("❌ 用户取消导入")
    
    def on_import_started(self):
        """导入开始"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.import_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.append_status("🚀 开始导入...")
    
    def on_import_progress(self, progress: int, message: str):
        """导入进度更新"""
        self.progress_bar.setValue(progress)
        self.append_status(f"📊 {progress}% - {message}")
    
    def on_import_completed(self, success: bool, message: str, tasks: List[PublishTask]):
        """导入完成"""
        self.progress_bar.setVisible(False)
        self.import_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        
        if success:
            self.append_status(f"✅ {message}")
            self.tasks_imported.emit(tasks)  # 发送任务导入完成信号
            QMessageBox.information(self, "成功", f"导入成功！\n{message}")
        else:
            self.append_status(f"❌ {message}")
            QMessageBox.warning(self, "失败", f"导入失败！\n{message}")
    
    def on_validation_completed(self, success: bool, message: str):
        """验证完成"""
        if success:
            self.append_status(f"✅ 验证成功: {message}")
            self.import_btn.setEnabled(True)
        else:
            self.append_status(f"❌ 验证失败: {message}")
            self.import_btn.setEnabled(False)
            QMessageBox.warning(self, "验证失败", f"文件验证失败！\n{message}")
    
    def append_status(self, message: str):
        """添加状态信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.status_text.append(formatted_message)
        # 滚动到底部
        cursor = self.status_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.status_text.setTextCursor(cursor)
        logger.info(formatted_message)
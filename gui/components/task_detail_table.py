"""
任务详情表格组件
支持排序、筛选、批量操作等功能
"""
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPushButton, QComboBox, QLineEdit,
    QLabel, QCheckBox, QMessageBox, QMenu, QDateTimeEdit, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer
from PyQt6.QtGui import QFont, QAction, QBrush, QColor
from loguru import logger

# 添加core模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.models import PublishTask, TaskStatus


class TaskDetailTable(QWidget):
    """任务详情表格组件"""
    
    # 信号定义
    task_selected = pyqtSignal(str)  # 任务被选中 (task_id)
    task_delete_requested = pyqtSignal(str)  # 请求删除任务 (task_id)
    task_retry_requested = pyqtSignal(str)  # 请求重试任务 (task_id)
    task_publish_immediately_requested = pyqtSignal(str)  # 请求立即发布任务 (task_id)
    tasks_delete_requested = pyqtSignal(list)  # 请求批量删除任务 (task_ids)
    task_time_updated = pyqtSignal(str, datetime)  # 任务时间更新 (task_id, new_time)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.filtered_tasks = []
        self.scheduler = None
        self.setup_ui()
        self.setup_refresh_timer()
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 筛选控制栏
        filter_layout = self.create_filter_controls()
        layout.addLayout(filter_layout)
        
        # 表格
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
        # 批量操作栏
        batch_layout = self.create_batch_controls()
        layout.addLayout(batch_layout)
    
    def create_filter_controls(self) -> QHBoxLayout:
        """创建筛选控制栏"""
        layout = QHBoxLayout()
        
        # 状态筛选
        layout.addWidget(QLabel("状态筛选:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "等待中", "执行中", "已完成", "失败"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        layout.addWidget(self.status_filter)
        
        # 关键词搜索
        layout.addWidget(QLabel("搜索:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索标题或内容...")
        self.search_input.textChanged.connect(self.apply_filters)
        layout.addWidget(self.search_input)
        
        # 清除筛选
        clear_filter_btn = QPushButton("清除筛选")
        clear_filter_btn.clicked.connect(self.clear_filters)
        layout.addWidget(clear_filter_btn)
        
        layout.addStretch()
        
        # 显示统计
        self.count_label = QLabel("显示: 0 / 0")
        layout.addWidget(self.count_label)
        
        return layout
    
    def create_batch_controls(self) -> QHBoxLayout:
        """创建批量操作栏"""
        layout = QHBoxLayout()
        
        # 全选复选框
        self.select_all_cb = QCheckBox("全选")
        self.select_all_cb.toggled.connect(self.on_select_all)
        layout.addWidget(self.select_all_cb)
        
        # 批量删除按钮
        self.batch_delete_btn = QPushButton("批量删除")
        self.batch_delete_btn.clicked.connect(self.on_batch_delete)
        self.batch_delete_btn.setEnabled(False)
        self.batch_delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        layout.addWidget(self.batch_delete_btn)
        
        layout.addStretch()
        
        # 选中统计
        self.selection_label = QLabel("已选中: 0")
        layout.addWidget(self.selection_label)
        
        return layout
    
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = ["", "标题", "正文内容", "图片地址", "平台", "发布时间", "状态", "最后执行时间", "操作"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # 复选框
        header.resizeSection(0, 30)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 标题
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # 内容
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 图片
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 平台
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 发布时间
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 最后执行时间
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)  # 操作
        header.resizeSection(8, 120)
        
        # 连接选择变化信号
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # 连接双击编辑信号
        self.table.itemDoubleClicked.connect(self.on_item_double_clicked)
    
    def setup_refresh_timer(self):
        """设置刷新定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_table)
        self.refresh_timer.start(5000)  # 每5秒刷新一次
    
    def set_scheduler(self, scheduler):
        """设置调度器引用"""
        self.scheduler = scheduler
        self.refresh_table()
    
    def refresh_table(self):
        """刷新表格数据"""
        if not self.scheduler:
            return
            
        try:
            # 获取最新任务列表
            self.tasks = self.scheduler.get_all_tasks()
            self.apply_filters()
            
        except Exception as e:
            logger.error(f"❌ 刷新任务表格失败: {e}")
    
    def apply_filters(self):
        """应用筛选条件"""
        try:
            # 状态筛选
            status_filter = self.status_filter.currentText()
            search_text = self.search_input.text().lower()
            
            self.filtered_tasks = []
            for task in self.tasks:
                # 状态筛选
                if status_filter != "全部":
                    status_map = {
                        "等待中": TaskStatus.PENDING,
                        "执行中": TaskStatus.RUNNING,
                        "已完成": TaskStatus.COMPLETED,
                        "失败": TaskStatus.FAILED
                    }
                    if task.status != status_map.get(status_filter):
                        continue
                
                # 关键词搜索
                if search_text:
                    searchable_text = f"{task.title} {task.content}".lower()
                    if search_text not in searchable_text:
                        continue
                
                self.filtered_tasks.append(task)
            
            # 更新表格显示
            self.update_table_display()
            self.update_count_display()
            
        except Exception as e:
            logger.error(f"❌ 应用筛选失败: {e}")
    
    def update_table_display(self):
        """更新表格显示"""
        try:
            self.table.setRowCount(len(self.filtered_tasks))
            
            for row, task in enumerate(self.filtered_tasks):
                # 复选框
                checkbox = QCheckBox()
                checkbox.toggled.connect(self.update_selection_stats)
                self.table.setCellWidget(row, 0, checkbox)
                
                # 标题
                title_item = QTableWidgetItem(task.title)
                title_item.setData(Qt.ItemDataRole.UserRole, task.id)  # 存储task_id
                self.table.setItem(row, 1, title_item)
                
                # 正文内容 - 截取显示
                content = task.content
                if len(content) > 50:
                    content = content[:50] + "..."
                self.table.setItem(row, 2, QTableWidgetItem(content))
                
                # 图片地址 - 显示数量
                image_count = len(task.images) if task.images else 0
                image_text = f"{image_count}张图片" if image_count > 0 else "无图片"
                self.table.setItem(row, 3, QTableWidgetItem(image_text))
                
                # 平台
                self.table.setItem(row, 4, QTableWidgetItem("小红书"))
                
                # 发布时间
                publish_time = task.publish_time.strftime("%m-%d %H:%M")
                self.table.setItem(row, 5, QTableWidgetItem(publish_time))
                
                # 状态 - 带颜色
                status_item = QTableWidgetItem(self.get_status_text(task.status))
                status_item.setForeground(QBrush(self.get_status_color(task.status)))
                self.table.setItem(row, 6, status_item)
                
                # 最后执行时间
                if task.updated_time:
                    updated_time = task.updated_time.strftime("%m-%d %H:%M")
                else:
                    updated_time = "-"
                self.table.setItem(row, 7, QTableWidgetItem(updated_time))
                
                # 操作按钮
                actions_widget = self.create_action_buttons(task)
                self.table.setCellWidget(row, 8, actions_widget)
                
        except Exception as e:
            logger.error(f"❌ 更新表格显示失败: {e}")
    
    def create_action_buttons(self, task: PublishTask) -> QWidget:
        """创建操作按钮"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        
        # 立即发布按钮（仅等待中任务显示）
        if task.status == TaskStatus.PENDING:
            publish_btn = QPushButton("立即发布")
            publish_btn.clicked.connect(lambda checked, tid=task.id: self.on_publish_immediately(tid))
            publish_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 2px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            layout.addWidget(publish_btn)
        
        # 重试按钮（仅失败任务显示）
        if task.status == TaskStatus.FAILED and task.can_retry():
            retry_btn = QPushButton("重试")
            retry_btn.clicked.connect(lambda checked, tid=task.id: self.on_retry_task(tid))
            retry_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #212529;
                    border: none;
                    padding: 4px 8px;
                    border-radius: 2px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            layout.addWidget(retry_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.clicked.connect(lambda checked, tid=task.id: self.on_delete_task(tid))
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 2px;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        layout.addWidget(delete_btn)
        
        return widget
    
    def get_status_text(self, status: TaskStatus) -> str:
        """获取状态显示文本"""
        status_map = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败"
        }
        return status_map.get(status, "未知")
    
    def get_status_color(self, status: TaskStatus) -> QColor:
        """获取状态颜色"""
        color_map = {
            TaskStatus.PENDING: QColor("#6c757d"),     # 灰色
            TaskStatus.RUNNING: QColor("#007bff"),     # 蓝色
            TaskStatus.COMPLETED: QColor("#28a745"),   # 绿色
            TaskStatus.FAILED: QColor("#dc3545")       # 红色
        }
        return color_map.get(status, QColor("#000000"))
    
    def show_context_menu(self, position):
        """显示右键菜单"""
        item = self.table.itemAt(position)
        if not item:
            return
            
        row = item.row()
        task_id = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
        task = next((t for t in self.filtered_tasks if t.id == task_id), None)
        
        if not task:
            return
            
        menu = QMenu(self)
        
        # 查看详情
        view_action = QAction("查看详情", self)
        view_action.triggered.connect(lambda: self.show_task_details(task))
        menu.addAction(view_action)
        
        # 删除任务
        delete_action = QAction("删除任务", self)
        delete_action.triggered.connect(lambda: self.on_delete_task(task.id))
        menu.addAction(delete_action)
        
        # 重试任务（仅失败任务）
        if task.status == TaskStatus.FAILED and task.can_retry():
            retry_action = QAction("重试任务", self)
            retry_action.triggered.connect(lambda: self.on_retry_task(task.id))
            menu.addAction(retry_action)
        
        menu.exec(self.table.mapToGlobal(position))
    
    def show_task_details(self, task: PublishTask):
        """显示任务详情"""
        details = f"""
任务详情：

标题：{task.title}

内容：
{task.content}

图片：{len(task.images)}张
{chr(10).join(task.images) if task.images else "无图片"}

话题：{', '.join(task.topics) if task.topics else "无话题"}

发布时间：{task.publish_time.strftime("%Y-%m-%d %H:%M:%S")}
状态：{self.get_status_text(task.status)}
创建时间：{task.created_time.strftime("%Y-%m-%d %H:%M:%S")}
更新时间：{task.updated_time.strftime("%Y-%m-%d %H:%M:%S") if task.updated_time else "未更新"}

重试次数：{task.retry_count}/{task.max_retries}
结果信息：{task.result_message or "无"}
        """
        
        QMessageBox.information(self, "任务详情", details.strip())
    
    def clear_filters(self):
        """清除筛选条件"""
        self.status_filter.setCurrentText("全部")
        self.search_input.clear()
        self.apply_filters()
    
    def on_select_all(self, checked: bool):
        """全选/取消全选"""
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox:
                checkbox.setChecked(checked)
    
    def on_selection_changed(self):
        """选择变化"""
        self.update_selection_stats()
    
    def update_selection_stats(self):
        """更新选择统计"""
        selected_count = 0
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                selected_count += 1
        
        self.selection_label.setText(f"已选中: {selected_count}")
        self.batch_delete_btn.setEnabled(selected_count > 0)
        
        # 更新全选复选框状态
        if selected_count == 0:
            self.select_all_cb.setChecked(False)
        elif selected_count == self.table.rowCount():
            self.select_all_cb.setChecked(True)
        else:
            self.select_all_cb.setCheckState(Qt.CheckState.PartiallyChecked)
    
    def update_count_display(self):
        """更新计数显示"""
        total_count = len(self.tasks)
        filtered_count = len(self.filtered_tasks)
        self.count_label.setText(f"显示: {filtered_count} / {total_count}")
    
    def on_delete_task(self, task_id: str):
        """删除单个任务"""
        self.task_delete_requested.emit(task_id)
    
    def on_retry_task(self, task_id: str):
        """重试任务"""
        self.task_retry_requested.emit(task_id)
    
    def on_publish_immediately(self, task_id: str):
        """立即发布任务"""
        logger.info(f"🚀 TaskDetailTable: 请求立即发布任务 {task_id}")
        self.task_publish_immediately_requested.emit(task_id)
    
    def on_batch_delete(self):
        """批量删除"""
        selected_task_ids = []
        for row in range(self.table.rowCount()):
            checkbox = self.table.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                task_id = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
                selected_task_ids.append(task_id)
        
        if not selected_task_ids:
            return
            
        reply = QMessageBox.question(
            self, "确认批量删除", 
            f"确定要删除选中的 {len(selected_task_ids)} 个任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tasks_delete_requested.emit(selected_task_ids)
    
    def on_item_double_clicked(self, item):
        """处理双击编辑"""
        if not item:
            return
            
        row = item.row()
        column = item.column()
        
        # 只允许编辑发布时间列（第5列）
        if column == 5:  # 发布时间列
            task_id = self.table.item(row, 1).data(Qt.ItemDataRole.UserRole)
            task = None
            
            # 找到对应的任务
            for t in self.tasks:
                if t.id == task_id:
                    task = t
                    break
            
            if task:
                self.edit_publish_time(task)
    
    def edit_publish_time(self, task: PublishTask):
        """编辑发布时间"""
        dialog = QDialog(self)
        dialog.setWindowTitle("编辑发布时间")
        dialog.setModal(True)
        dialog.resize(300, 150)
        
        layout = QVBoxLayout(dialog)
        
        # 时间选择器
        time_edit = QDateTimeEdit(task.publish_time)
        time_edit.setDisplayFormat("yyyy-MM-dd hh:mm")
        time_edit.setCalendarPopup(True)
        time_edit.setMinimumDateTime(datetime.now())
        layout.addWidget(QLabel("选择发布时间:"))
        layout.addWidget(time_edit)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(ok_btn)
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 正确的方法：使用 toPython() 或 toPyDateTime()
            qt_datetime = time_edit.dateTime()
            new_time = qt_datetime.toPyDateTime()
            
            # 更新任务时间
            task.publish_time = new_time
            task.updated_time = datetime.now()
            
            # 发出信号通知更新
            self.task_time_updated.emit(task.id, new_time)
            
            # 刷新显示
            self.refresh_table()
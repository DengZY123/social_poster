# 任务分配详细说明

## 🎯 任务A：核心调度器重构 (后端负责)

### A1. 进程管理器 ✅ 已完成
文件：`core/process_manager.py` (已创建)

### A2. 调度器重构 📋 待完成
**文件：** `core/scheduler.py`

**关键修改：**
```python
# 第28行左右，添加导入
from .process_manager import ProcessManager

# 第41行左右，修改__init__方法
def __init__(self, parent=None):
    super().__init__(parent)
    
    # 使用进程管理器替代subprocess
    self.process_manager = ProcessManager(max_processes=2, parent=self)
    self.process_manager.process_finished.connect(self._handle_task_success)
    self.process_manager.process_failed.connect(self._handle_task_error)
    self.process_manager.process_started.connect(lambda task_id: self.task_started.emit(task_id))
    
    # 其他初始化保持不变...

# 第210行左右，完全替换_run_subprocess_async方法
def _run_subprocess_async(self, task: PublishTask, cmd: List[str]):
    """使用进程管理器执行任务"""
    try:
        # 标记任务开始执行  
        task.mark_running()
        self.task_storage.update_task(task)
        self.executing_tasks.add(task.id)
        
        # 使用进程管理器启动
        if self.process_manager.start_task(task, cmd):
            logger.info(f"🚀 任务已提交给进程管理器: {task.title}")
        else:
            raise Exception("进程管理器启动任务失败")
            
    except Exception as e:
        logger.error(f"❌ 启动任务失败: {e}")
        self._handle_task_error(task, str(e))

# 修改信号处理方法的签名
def _handle_task_success(self, task_id: str, result: dict):
    """处理任务成功"""
    try:
        task = self.task_storage.get_task_by_id(task_id)
        if not task:
            logger.error(f"❌ 找不到任务: {task_id}")
            return
            
        task.mark_completed(result.get("message", "发布成功"))
        self.task_storage.update_task(task)
        self.executing_tasks.discard(task_id)
        
        logger.info(f"✅ 任务执行成功: {task.title}")
        self.task_completed.emit(task_id, result)
        
    except Exception as e:
        logger.error(f"❌ 处理任务成功结果失败: {e}")

def _handle_task_error(self, task_id: str, error_message: str):
    """处理任务失败"""
    try:
        task = self.task_storage.get_task_by_id(task_id)
        if not task:
            task = PublishTask(id=task_id, title="未知任务", content="", images=[], topics=[], publish_time=datetime.now())
            
        task.mark_failed(error_message)
        self.task_storage.update_task(task)
        self.executing_tasks.discard(task_id)
        
        logger.error(f"❌ 任务失败: {task.title}, 错误: {error_message}")
        self.task_failed.emit(task_id, error_message)
        
    except Exception as e:
        logger.error(f"❌ 处理任务失败时出错: {e}")

# 删除第216-259行的整个_run_subprocess_async方法中的QTimer和subprocess代码
```

### A3. 存储安全增强 📋 待完成
**文件：** `core/storage.py`

**添加原子文件操作类：**
```python
import shutil
import os
from pathlib import Path

class SafeTaskStorage(TaskStorage):
    """安全的任务存储，支持原子操作"""
    
    def __init__(self, file_path: str = "tasks.json"):
        super().__init__(file_path)
        self.backup_path = Path(f"{file_path}.backup")
        self.lock_path = Path(f"{file_path}.lock")
    
    def save_tasks_atomic(self, tasks: List[PublishTask]):
        """原子性保存任务"""
        try:
            # 创建锁文件
            with open(self.lock_path, 'w') as lock_file:
                lock_file.write(str(os.getpid()))
            
            # 备份现有文件
            if self.file_path.exists():
                shutil.copy2(self.file_path, self.backup_path)
            
            # 写入临时文件
            temp_path = Path(f"{self.file_path}.tmp")
            data = [task.to_dict() for task in tasks]
            
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            temp_path.replace(self.file_path)
            
            logger.info(f"保存了 {len(tasks)} 个任务")
            
        except Exception as e:
            # 恢复备份
            if self.backup_path.exists():
                shutil.copy2(self.backup_path, self.file_path)
            logger.error(f"保存任务失败，已恢复备份: {e}")
            raise
        finally:
            # 清理锁文件
            if self.lock_path.exists():
                self.lock_path.unlink()
    
    def save_tasks(self, tasks: List[PublishTask]):
        """覆盖原方法，使用原子操作"""
        self.save_tasks_atomic(tasks)
```

---

## 🎨 任务B：界面组件开发 (前端负责)

### B1. 控制面板组件 📋 待完成
**创建文件：** `gui/components/__init__.py`
```python
# 空文件，使components成为Python包
```

**创建文件：** `gui/components/control_panel.py`
```python
"""
操作控制面板组件
"""
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QVBoxLayout, QPushButton, 
    QFileDialog, QMessageBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, QTimer
from loguru import logger


class ControlPanelWidget(QGroupBox):
    """操作控制面板"""
    
    # 信号定义
    excel_import_requested = pyqtSignal(str)  # file_path
    example_tasks_requested = pyqtSignal()
    clear_all_requested = pyqtSignal()
    publish_all_requested = pyqtSignal()
    stop_publish_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__("操作控制", parent)
        self.operation_lock = set()  # 防重复操作
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QHBoxLayout(self)
        
        # 文件操作组
        file_group = self.create_file_group()
        layout.addWidget(file_group)
        
        # 发布控制组
        publish_group = self.create_publish_group()
        layout.addWidget(publish_group)
        
        # 状态显示组
        status_group = self.create_status_group()
        layout.addWidget(status_group)
        
    def create_file_group(self):
        """创建文件操作按钮组"""
        group = QGroupBox("文件操作")
        layout = QHBoxLayout(group)
        
        # Excel导入按钮
        self.import_btn = QPushButton("📂 导入Excel文件")
        self.import_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.import_btn.clicked.connect(self.import_excel)
        layout.addWidget(self.import_btn)
        
        # 添加示例任务按钮
        self.example_btn = QPushButton("📝 添加示例任务")
        self.example_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8E24AA;
            }
            QPushButton:pressed {
                background-color: #7B1FA2;
            }
        """)
        self.example_btn.clicked.connect(self.add_example_tasks)
        layout.addWidget(self.example_btn)
        
        # 清空所有任务按钮
        self.clear_btn = QPushButton("🗑️ 清空所有任务")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #F44336;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E53935;
            }
            QPushButton:pressed {
                background-color: #D32F2F;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_all_tasks)
        layout.addWidget(self.clear_btn)
        
        return group
        
    def create_publish_group(self):
        """创建发布控制按钮组"""
        group = QGroupBox("发布控制")
        layout = QHBoxLayout(group)
        
        # 发布所有任务按钮
        self.publish_all_btn = QPushButton("🚀 发布所有任务")
        self.publish_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
        """)
        self.publish_all_btn.clicked.connect(self.publish_all_tasks)
        layout.addWidget(self.publish_all_btn)
        
        # 停止发布按钮
        self.stop_btn = QPushButton("🛑 停止发布")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
            QPushButton:pressed {
                background-color: #D84315;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_publish)
        layout.addWidget(self.stop_btn)
        
        # 刷新状态按钮
        self.refresh_btn = QPushButton("🔄 刷新状态")
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
            QPushButton:pressed {
                background-color: #455A64;
            }
        """)
        self.refresh_btn.clicked.connect(self.refresh_status)
        layout.addWidget(self.refresh_btn)
        
        return group
        
    def create_status_group(self):
        """创建状态显示组"""
        group = QGroupBox("状态显示")
        layout = QVBoxLayout(group)
        
        self.status_label = QLabel("📊 就绪")
        self.status_label.setStyleSheet("font-weight: bold; color: #4CAF50;")
        layout.addWidget(self.status_label)
        
        self.task_count_label = QLabel("📋 任务: 0")
        layout.addWidget(self.task_count_label)
        
        return group
    
    def import_excel(self):
        """导入Excel文件"""
        if "import_excel" in self.operation_lock:
            QMessageBox.warning(self, "提示", "导入操作正在进行中...")
            return
            
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择Excel文件", "", "Excel files (*.xlsx *.xls)"
        )
        
        if file_path:
            self.operation_lock.add("import_excel")
            self.excel_import_requested.emit(file_path)
            
            # 5秒后解锁
            QTimer.singleShot(5000, lambda: self.operation_lock.discard("import_excel"))
    
    def add_example_tasks(self):
        """添加示例任务"""
        if "add_example" in self.operation_lock:
            QMessageBox.warning(self, "提示", "添加示例操作正在进行中...")
            return
            
        self.operation_lock.add("add_example")
        self.example_tasks_requested.emit()
        
        # 3秒后解锁
        QTimer.singleShot(3000, lambda: self.operation_lock.discard("add_example"))
    
    def clear_all_tasks(self):
        """清空所有任务"""
        reply = QMessageBox.question(
            self, "确认清空", "确定要清空所有任务吗？此操作不可撤销！",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.clear_all_requested.emit()
    
    def publish_all_tasks(self):
        """发布所有任务"""
        self.publish_all_requested.emit()
    
    def stop_publish(self):
        """停止发布"""
        self.stop_publish_requested.emit()
    
    def refresh_status(self):
        """刷新状态"""
        self.refresh_requested.emit()
    
    def update_status(self, message: str, task_count: int = 0):
        """更新状态显示"""
        self.status_label.setText(f"📊 {message}")
        self.task_count_label.setText(f"📋 任务: {task_count}")
```

### B2. 任务详情表格 📋 待完成
**创建文件：** `gui/components/task_detail_table.py`
```python
"""
任务详情表格组件
"""
from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QPushButton, QHeaderView,
    QAbstractItemView, QGroupBox, QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from typing import List
from loguru import logger

# 这里需要导入模型
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.models import PublishTask, TaskStatus


class TaskDetailTable(QGroupBox):
    """任务详情表格"""
    
    # 信号定义
    task_edit_requested = pyqtSignal(str)  # task_id
    task_delete_requested = pyqtSignal(str)  # task_id
    
    def __init__(self, parent=None):
        super().__init__("任务详情", parent)
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 操作按钮行
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.clear_completed_btn = QPushButton("清除已完成")
        self.clear_completed_btn.clicked.connect(self.clear_completed)
        button_layout.addWidget(self.clear_completed_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        # 表格
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)
        
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = [
            "标题", "正文内容", "图片地址", "平台", 
            "发布时间", "状态", "最后执行时间", "操作"
        ]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 标题
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 内容
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 图片
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 平台
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 发布时间
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)  # 执行时间
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)  # 操作
        
    def update_tasks(self, tasks: List[PublishTask]):
        """更新任务列表"""
        try:
            self.table.setRowCount(len(tasks))
            
            for row, task in enumerate(tasks):
                # 标题
                title_item = QTableWidgetItem(task.title)
                title_item.setData(Qt.ItemDataRole.UserRole, task.id)
                self.table.setItem(row, 0, title_item)
                
                # 正文内容 (截取前50字符)
                content_preview = task.content[:50] + "..." if len(task.content) > 50 else task.content
                self.table.setItem(row, 1, QTableWidgetItem(content_preview))
                
                # 图片地址
                image_info = f"{len(task.images)}张图片" if task.images else "无图片"
                self.table.setItem(row, 2, QTableWidgetItem(image_info))
                
                # 平台
                self.table.setItem(row, 3, QTableWidgetItem("小红书"))
                
                # 发布时间
                publish_time = task.publish_time.strftime("%Y-%m-%d %H:%M")
                self.table.setItem(row, 4, QTableWidgetItem(publish_time))
                
                # 状态
                status_item = QTableWidgetItem(self.get_status_text(task.status))
                status_item = self.set_status_color(status_item, task.status)
                self.table.setItem(row, 5, status_item)
                
                # 最后执行时间
                last_update = ""
                if task.updated_time:
                    last_update = task.updated_time.strftime("%m-%d %H:%M")
                self.table.setItem(row, 6, QTableWidgetItem(last_update))
                
                # 操作按钮
                self.add_action_buttons(row, task.id)
                
        except Exception as e:
            logger.error(f"❌ 更新任务表格失败: {e}")
    
    def get_status_text(self, status: TaskStatus) -> str:
        """获取状态显示文本"""
        status_map = {
            TaskStatus.PENDING: "已调度",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.COMPLETED: "已完成", 
            TaskStatus.FAILED: "失败"
        }
        return status_map.get(status, "未知")
    
    def set_status_color(self, item: QTableWidgetItem, status: TaskStatus) -> QTableWidgetItem:
        """设置状态颜色"""
        color_map = {
            TaskStatus.PENDING: "#FF9800",    # 橙色
            TaskStatus.RUNNING: "#2196F3",    # 蓝色
            TaskStatus.COMPLETED: "#4CAF50",  # 绿色
            TaskStatus.FAILED: "#F44336"      # 红色
        }
        
        color = color_map.get(status, "#666666")
        item.setForeground(Qt.GlobalColor.white)
        item.setBackground(Qt.GlobalColor.transparent)
        item.setToolTip(f"状态: {self.get_status_text(status)}")
        
        return item
    
    def add_action_buttons(self, row: int, task_id: str):
        """添加操作按钮"""
        # 创建按钮容器
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(2, 2, 2, 2)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setMaximumWidth(50)
        edit_btn.clicked.connect(lambda: self.task_edit_requested.emit(task_id))
        button_layout.addWidget(edit_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setMaximumWidth(50)
        delete_btn.setStyleSheet("QPushButton { background-color: #F44336; color: white; }")
        delete_btn.clicked.connect(lambda: self.delete_task(task_id))
        button_layout.addWidget(delete_btn)
        
        self.table.setCellWidget(row, 7, button_widget)
    
    def delete_task(self, task_id: str):
        """删除任务确认"""
        reply = QMessageBox.question(
            self, "确认删除", "确定要删除这个任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.task_delete_requested.emit(task_id)
    
    def select_all(self):
        """全选/取消全选"""
        self.table.selectAll()
    
    def clear_completed(self):
        """清除已完成任务"""
        reply = QMessageBox.question(
            self, "确认清除", "确定要清除所有已完成的任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 这里需要通过信号通知主窗口清除已完成任务
            pass


from PyQt6.QtWidgets import QWidget
```

### B3. 账号管理标签页 📋 待完成
**创建文件：** `gui/components/account_tab.py`
```python
"""
账号管理标签页
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont


class AccountManagementTab(QWidget):
    """账号管理标签页"""
    
    # 信号定义
    login_check_requested = pyqtSignal()
    login_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # 定期检查登录状态
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_login_status)
        self.status_timer.start(30000)  # 每30秒检查一次
        
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 账号状态组
        status_group = self.create_status_group()
        layout.addWidget(status_group)
        
        # 操作按钮组
        action_group = self.create_action_group()
        layout.addWidget(action_group)
        
        # 登录日志组
        log_group = self.create_log_group()
        layout.addWidget(log_group)
        
    def create_status_group(self):
        """创建状态显示组"""
        group = QGroupBox("账号状态")
        layout = QVBoxLayout(group)
        
        # 状态显示
        status_layout = QHBoxLayout()
        
        self.status_label = QLabel("🔍 检查中...")
        self.status_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.last_check_label = QLabel("最后检查: 未知")
        self.last_check_label.setStyleSheet("color: #666666;")
        status_layout.addWidget(self.last_check_label)
        
        layout.addLayout(status_layout)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 详细信息
        self.detail_label = QLabel("点击'检查登录状态'来验证账号状态")
        self.detail_label.setWordWrap(True)
        self.detail_label.setStyleSheet("color: #666666; padding: 10px;")
        layout.addWidget(self.detail_label)
        
        return group
    
    def create_action_group(self):
        """创建操作按钮组"""
        group = QGroupBox("账号操作")
        layout = QHBoxLayout(group)
        
        # 检查登录状态按钮
        self.check_btn = QPushButton("🔍 检查登录状态")
        self.check_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.check_btn.clicked.connect(self.start_login_check)
        layout.addWidget(self.check_btn)
        
        # 登录按钮
        self.login_btn = QPushButton("🚪 登录账号")
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.login_btn.clicked.connect(self.start_login)
        layout.addWidget(self.login_btn)
        
        # 退出登录按钮
        self.logout_btn = QPushButton("🚪 退出登录")
        self.logout_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF5722;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #E64A19;
            }
        """)
        self.logout_btn.clicked.connect(self.start_logout)
        self.logout_btn.setEnabled(False)
        layout.addWidget(self.logout_btn)
        
        layout.addStretch()
        
        return group
    
    def create_log_group(self):
        """创建日志显示组"""
        group = QGroupBox("操作日志")
        layout = QVBoxLayout(group)
        
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 清除日志按钮
        clear_btn = QPushButton("清除日志")
        clear_btn.clicked.connect(self.log_text.clear)
        layout.addWidget(clear_btn)
        
        return group
    
    def start_login_check(self):
        """开始检查登录状态"""
        self.set_checking_state(True)
        self.add_log("开始检查登录状态...")
        self.login_check_requested.emit()
    
    def start_login(self):
        """开始登录"""
        self.set_checking_state(True)
        self.add_log("开始登录流程...")
        self.login_requested.emit()
    
    def start_logout(self):
        """开始退出登录"""
        self.set_checking_state(True)
        self.add_log("开始退出登录...")
        self.logout_requested.emit()
    
    def check_login_status(self):
        """定期检查登录状态"""
        self.login_check_requested.emit()
    
    def set_checking_state(self, checking: bool):
        """设置检查状态"""
        self.progress_bar.setVisible(checking)
        if checking:
            self.progress_bar.setRange(0, 0)  # 不确定进度
            self.check_btn.setEnabled(False)
            self.login_btn.setEnabled(False)
            self.logout_btn.setEnabled(False)
        else:
            self.progress_bar.setVisible(False)
            self.check_btn.setEnabled(True)
            self.login_btn.setEnabled(True)
    
    def update_login_status(self, is_logged_in: bool, message: str = ""):
        """更新登录状态"""
        self.set_checking_state(False)
        
        from datetime import datetime
        current_time = datetime.now().strftime("%H:%M:%S")
        self.last_check_label.setText(f"最后检查: {current_time}")
        
        if is_logged_in:
            self.status_label.setText("✅ 已登录")
            self.status_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
            self.detail_label.setText(f"账号状态正常。{message}")
            self.logout_btn.setEnabled(True)
            self.add_log(f"✅ 登录状态检查成功: {message}")
        else:
            self.status_label.setText("❌ 未登录")
            self.status_label.setStyleSheet("color: #F44336; font-weight: bold;")
            self.detail_label.setText(f"需要登录账号。{message}")
            self.logout_btn.setEnabled(False)
            self.add_log(f"❌ 登录状态检查失败: {message}")
    
    def add_log(self, message: str):
        """添加日志"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        
        self.log_text.append(log_line)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
```

### B4. 主界面重构 📋 待完成
**修改文件：** `gui/main_window.py`

**主要修改：** 将setup_ui方法完全替换为新的布局设计，参考目标界面的上下分区结构。

---

## 📊 任务C：Excel导入功能 (全栈负责)

### C1. Excel处理脚本 📋 待完成
**修改文件：** `utils/excel_importer.py`

需要改造为独立脚本，支持命令行调用，输出JSON格式结果。

---

## 🔒 任务D：安全机制增强 (后端负责)

### D1. 操作防护装饰器 📋 待完成
**创建文件：** `utils/operation_guard.py`

### D2. 异常处理增强 📋 待完成
在各个组件中添加完善的try-catch和用户友好提示。

---

## 🚀 立即开始

1. **选择任务** - 根据技能选择A/B/C/D中的任务
2. **创建分支** - `git checkout -b task-A` (或B/C/D)
3. **开始开发** - 按照上述详细说明实施
4. **定期提交** - 每完成一个小功能就commit
5. **及时测试** - 每个文件完成后立即测试

**预计时间分配：**
- 任务A: 2-3小时 (最关键)
- 任务B: 3-4小时 (界面工作量大)
- 任务C: 2小时 (相对简单)
- 任务D: 1-2小时 (增强功能)
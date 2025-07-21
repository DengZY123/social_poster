"""
简洁的主窗口界面
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QDateTimeEdit, QFileDialog, QMessageBox, QSplitter, QGroupBox,
    QComboBox, QSpinBox, QCheckBox, QTabWidget, QProgressBar,
    QHeaderView, QAbstractItemView
)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSlot
from PyQt6.QtGui import QFont, QTextCursor
from loguru import logger

# 添加core模块路径
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.models import PublishTask, TaskStatus
from core.scheduler import SimpleScheduler

# 导入新组件
from gui.components.control_panel import ControlPanel
from gui.components.task_detail_table import TaskDetailTable
from gui.components.account_tab import AccountTab
from gui.components.excel_importer import AsyncExcelImporter

# 导入安全机制
from utils.operation_guard import operation_guard, safe_method, cleanup_on_exit


class SampleTaskCreator:
    """示例任务创建器"""
    
    @staticmethod
    def create_sample_tasks() -> List[PublishTask]:
        """创建示例任务"""
        sample_tasks = []
        
        # 获取项目根目录下的图片路径
        project_root = Path(__file__).parent.parent
        sample_image = project_root / "images" / "news1.png"
        
        # 使用绝对路径
        image_path = str(sample_image.absolute()) if sample_image.exists() else ""
        
        # 示例任务1 - 美食分享
        task1 = PublishTask.create_new(
            title="分享今日美食制作心得",
            content="今天尝试制作了红烧肉，经过3小时的慢炖，肉质软糯香甜。制作过程中有几个小技巧分享给大家：\n\n1. 肉要先焯水去腥\n2. 糖色要炒制得当\n3. 小火慢炖是关键\n\n大家有什么烹饪心得欢迎分享！ #美食制作 #红烧肉 #烹饪技巧",
            images=[image_path] if image_path else [],
            topics=["美食制作", "红烧肉", "烹饪技巧"],
            publish_time=datetime.now() + timedelta(minutes=10)
        )
        sample_tasks.append(task1)
        
        # 示例任务2 - 户外活动
        task2 = PublishTask.create_new(
            title="周末户外徒步记录",
            content="昨天和朋友们一起去爬山，路程虽然有点累，但是山顶的风景真的很美！\n\n路线推荐：\n📍 起点：山脚停车场\n📍 终点：观景台\n⏰ 用时：约3小时\n💪 难度：中等\n\n记得带足够的水和零食，还有防晒用品。下次还要再来！ #户外徒步 #爬山 #周末活动",
            images=[image_path] if image_path else [],
            topics=["户外徒步", "爬山", "周末活动"],
            publish_time=datetime.now() + timedelta(hours=2)
        )
        sample_tasks.append(task2)
        
        # 示例任务3 - 读书笔记
        task3 = PublishTask.create_new(
            title="读书笔记：《高效能人士的七个习惯》",
            content="最近在读这本经典的自我管理书籍，其中几个观点很有启发：\n\n📖 主要收获：\n1. 以终为始 - 明确目标很重要\n2. 要事第一 - 区分重要和紧急\n3. 双赢思维 - 合作大于竞争\n\n这些习惯不仅适用于工作，生活中也很实用。推荐给想要提升自己的朋友们！ #读书笔记 #自我提升 #高效能",
            images=[image_path] if image_path else [],
            topics=["读书笔记", "自我提升", "高效能"],
            publish_time=datetime.now() + timedelta(days=1)
        )
        sample_tasks.append(task3)
        
        return sample_tasks


class TaskTableWidget(QTableWidget):
    """任务表格组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = ["标题", "发布时间", "状态", "结果", "操作"]
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setAlternatingRowColors(True)
        
        # 设置列宽
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # 标题自动调整
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # 时间
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # 结果
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # 操作
    
    def update_tasks(self, tasks: List[PublishTask]):
        """更新任务列表"""
        self.setRowCount(len(tasks))
        
        for row, task in enumerate(tasks):
            # 标题
            self.setItem(row, 0, QTableWidgetItem(task.title))
            
            # 发布时间
            time_str = task.publish_time.strftime("%m-%d %H:%M")
            self.setItem(row, 1, QTableWidgetItem(time_str))
            
            # 状态
            status_text = self.get_status_text(task.status)
            status_item = QTableWidgetItem(status_text)
            self.setItem(row, 2, status_item)
            
            # 结果
            result_text = task.result_message or ""
            if len(result_text) > 30:
                result_text = result_text[:30] + "..."
            self.setItem(row, 3, QTableWidgetItem(result_text))
            
            # 操作按钮
            delete_btn = QPushButton("删除")
            delete_btn.clicked.connect(lambda checked, tid=task.id: self.delete_task(tid))
            self.setCellWidget(row, 4, delete_btn)
            
            # 存储任务ID
            self.item(row, 0).setData(Qt.ItemDataRole.UserRole, task.id)
    
    def get_status_text(self, status: TaskStatus) -> str:
        """获取状态显示文本"""
        status_map = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.RUNNING: "执行中",
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败"
        }
        return status_map.get(status, "未知")
    
    def delete_task(self, task_id: str):
        """删除任务"""
        if hasattr(self.parent(), 'delete_task'):
            self.parent().delete_task(task_id)




class LogWidget(QGroupBox):
    """日志显示组件"""
    
    def __init__(self, parent=None):
        super().__init__("运行日志", parent)
        self.setup_log()
    
    def setup_log(self):
        """设置日志"""
        layout = QVBoxLayout(self)
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # 清除按钮
        clear_btn = QPushButton("清除日志")
        clear_btn.clicked.connect(self.clear_log)
        layout.addWidget(clear_btn)
    
    def add_log(self, message: str):
        """添加日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        
        self.log_text.append(log_line)
        
        # 自动滚动到底部
        cursor = self.log_text.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.log_text.setTextCursor(cursor)
    
    def clear_log(self):
        """清除日志"""
        self.log_text.clear()


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        self.scheduler = SimpleScheduler(self)
        
        # 初始化Excel导入器
        self.excel_importer = AsyncExcelImporter(self)
        self.connect_excel_importer_signals()
        
        self.setup_ui()
        self.connect_signals()
        self.setup_refresh_timer()
        
        # 启动调度器
        self.scheduler.start()
        
        logger.info("✅ 主窗口初始化完成")
    
    def setup_ui(self):
        """设置界面"""
        self.setWindowTitle("小红书定时发布工具 - 专业版")
        self.setGeometry(100, 100, 1400, 900)
        
        # 中心组件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 标签页组件（放在最上面）
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 任务管理标签页
        self.setup_task_tab()
        
        # 账号管理标签页
        self.setup_account_tab()
        
        
        # 日志组件（放在底部）
        self.log_widget = LogWidget()
        main_layout.addWidget(self.log_widget)
        
        # 初始加载任务
        self.refresh_tasks()
    
    def setup_task_tab(self):
        """设置任务管理标签页"""
        task_tab = QWidget()
        self.tab_widget.addTab(task_tab, "📋 任务管理")
        
        # 任务标签页布局
        task_layout = QVBoxLayout(task_tab)
        
        # 控制面板（第一排）
        self.control_panel = ControlPanel()
        self.control_panel.set_scheduler(self.scheduler)
        self.connect_control_panel_signals()
        task_layout.addWidget(self.control_panel)
        
        # 任务详情表格（第二排，占主要空间）
        self.task_detail_table = TaskDetailTable()
        self.task_detail_table.set_scheduler(self.scheduler)
        self.connect_task_table_signals()
        task_layout.addWidget(self.task_detail_table)
    
    def setup_account_tab(self):
        """设置账号管理标签页"""
        self.account_tab = AccountTab()
        self.connect_account_tab_signals()
        self.tab_widget.addTab(self.account_tab, "👤 账号管理")
    
    
    def connect_control_panel_signals(self):
        """连接控制面板信号"""
        self.control_panel.import_excel_requested.connect(self.on_import_excel_requested)
        self.control_panel.add_sample_tasks_requested.connect(self.on_add_sample_tasks)
        self.control_panel.clear_all_tasks_requested.connect(self.on_clear_all_tasks)
        self.control_panel.publish_all_requested.connect(self.on_publish_all_tasks)
        self.control_panel.stop_publishing_requested.connect(self.on_stop_publishing)
        self.control_panel.refresh_status_requested.connect(self.refresh_tasks)
        
        # 连接调度器状态信号
        self.scheduler.scheduler_status.connect(self.control_panel.on_scheduler_status_changed)
    
    def connect_task_table_signals(self):
        """连接任务表格信号"""
        self.task_detail_table.task_delete_requested.connect(self.delete_task)
        self.task_detail_table.task_retry_requested.connect(self.retry_task)
        self.task_detail_table.task_publish_immediately_requested.connect(self.on_publish_immediately)
        self.task_detail_table.tasks_delete_requested.connect(self.batch_delete_tasks)
        self.task_detail_table.task_time_updated.connect(self.on_task_time_updated)
        self.task_detail_table.task_edit_requested.connect(self.on_edit_task)
    
    def connect_account_tab_signals(self):
        """连接账号管理标签页信号"""
        self.account_tab.account_selected.connect(self.on_account_selected)
        self.account_tab.login_requested.connect(self.on_login_requested)
    
    def connect_excel_importer_signals(self):
        """连接Excel导入器信号"""
        self.excel_importer.import_started.connect(self.on_excel_import_started)
        self.excel_importer.import_progress.connect(self.on_excel_import_progress)
        self.excel_importer.import_completed.connect(self.on_excel_import_completed)
        self.excel_importer.validation_completed.connect(self.on_excel_validation_completed)
    
    @operation_guard("import_excel", timeout_seconds=60)
    @safe_method(fallback_result=None, error_message="Excel导入失败")
    def on_import_excel_requested(self, file_path: str):
        """处理Excel导入请求"""
        if not file_path or not Path(file_path).exists():
            QMessageBox.warning(self, "错误", "请选择有效的Excel文件")
            return
        
        self.log_widget.add_log(f"📂 开始导入Excel: {Path(file_path).name}")
        
        # 使用异步Excel导入器
        self.excel_importer.import_excel_async(
            file_path=file_path,
            start_time=None,  # 使用默认时间
            interval_minutes=30  # 默认30分钟间隔
        )
    
    @operation_guard("add_sample_tasks", timeout_seconds=15)
    @safe_method(fallback_result=None, error_message="添加示例任务失败")
    def on_add_sample_tasks(self):
        """添加示例任务"""
        sample_tasks = SampleTaskCreator.create_sample_tasks()
        added_count = 0
        
        for task in sample_tasks:
            if self.scheduler.add_task(task):
                added_count += 1
        
        if added_count > 0:
            self.log_widget.add_log(f"📝 成功添加 {added_count} 个示例任务")
            self.refresh_tasks()
            QMessageBox.information(self, "成功", f"成功添加 {added_count} 个示例任务")
        else:
            QMessageBox.warning(self, "失败", "添加示例任务失败")
    
    def on_clear_all_tasks(self):
        """清空所有任务"""
        try:
            tasks = self.scheduler.get_all_tasks()
            if not tasks:
                QMessageBox.information(self, "提示", "没有任务需要清空")
                return
            
            removed_count = 0
            for task in tasks:
                if self.scheduler.delete_task(task.id):
                    removed_count += 1
            
            self.log_widget.add_log(f"🗑️ 清空了 {removed_count} 个任务")
            self.refresh_tasks()
            
        except Exception as e:
            logger.error(f"清空任务失败: {e}")
            QMessageBox.critical(self, "错误", f"清空任务失败: {e}")
    
    def on_publish_all_tasks(self):
        """发布所有待发布任务"""
        try:
            # 触发调度器检查
            self.scheduler.check_and_execute_tasks()
            self.log_widget.add_log("🚀 开始发布所有待发布任务")
            
        except Exception as e:
            logger.error(f"发布所有任务失败: {e}")
            QMessageBox.critical(self, "错误", f"发布所有任务失败: {e}")
    
    def on_stop_publishing(self):
        """停止发布"""
        try:
            # 停止调度器
            if self.scheduler.is_running:
                self.scheduler.stop()
                self.log_widget.add_log("🛑 已停止发布")
            else:
                self.log_widget.add_log("ℹ️ 调度器未在运行")
                
        except Exception as e:
            logger.error(f"停止发布失败: {e}")
    
    def retry_task(self, task_id: str):
        """重试任务"""
        try:
            task = self.scheduler.get_task_by_id(task_id)
            if task and task.can_retry():
                task.reset_for_retry()
                self.scheduler.task_storage.update_task(task)
                self.log_widget.add_log(f"🔄 任务已重置为重试: {task.title}")
                self.refresh_tasks()
            else:
                QMessageBox.warning(self, "提示", "任务无法重试")
                
        except Exception as e:
            logger.error(f"重试任务失败: {e}")
            QMessageBox.critical(self, "错误", f"重试任务失败: {e}")
    
    @operation_guard("publish_immediately", timeout_seconds=30)
    @safe_method(fallback_result=None, error_message="立即发布任务失败")
    def on_publish_immediately(self, task_id: str):
        """立即发布任务"""
        logger.info(f"🎯 MainWindow: 收到立即发布请求 {task_id}")
        
        # 获取任务
        task = self.scheduler.get_task_by_id(task_id)
        if not task:
            QMessageBox.warning(self, "错误", "找不到指定的任务")
            return
        
        # 检查任务状态
        if task.status != TaskStatus.PENDING:
            QMessageBox.warning(self, "错误", f"任务状态不是等待中，无法立即发布\n当前状态: {self.get_status_text(task.status)}")
            return
        
        # 检查是否已有任务在执行
        if self.scheduler.executing_tasks:
            QMessageBox.warning(self, "提示", f"已有任务正在执行中，请等待完成后再试")
            return
        
        # 确认对话框
        reply = QMessageBox.question(
            self, 
            "确认立即发布", 
            f"确定要立即发布任务「{task.title}」吗？\n\n原定发布时间: {task.publish_time.strftime('%Y-%m-%d %H:%M:%S')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 记录日志
            self.log_widget.add_log(f"🚀 立即发布任务: {task.title}")
            
            # 使用新的立即执行方法（跳过发布间隔检查）
            # 注意：不修改任务的发布时间，保持原有时间
            if self.scheduler.execute_task_immediately(task_id):
                self.log_widget.add_log(f"✅ 任务已提交立即执行: {task.title}")
                # 显示成功提示
                QMessageBox.information(self, "发布成功", f"任务「{task.title}」已开始立即发布！")
            else:
                self.log_widget.add_log(f"❌ 立即执行任务失败: {task.title}")
                QMessageBox.warning(self, "执行失败", f"立即执行任务「{task.title}」失败，请检查任务状态")
            
            # 刷新显示
            self.refresh_tasks()
    
    def get_status_text(self, status: TaskStatus) -> str:
        """获取状态显示文本"""
        status_map = {
            TaskStatus.PENDING: "等待中",
            TaskStatus.RUNNING: "执行中", 
            TaskStatus.COMPLETED: "已完成",
            TaskStatus.FAILED: "失败"
        }
        return status_map.get(status, "未知")
    
    def batch_delete_tasks(self, task_ids: List[str]):
        """批量删除任务"""
        try:
            removed_count = 0
            for task_id in task_ids:
                if self.scheduler.delete_task(task_id):
                    removed_count += 1
            
            self.log_widget.add_log(f"🗑️ 批量删除了 {removed_count} 个任务")
            self.refresh_tasks()
            
        except Exception as e:
            logger.error(f"批量删除任务失败: {e}")
            QMessageBox.critical(self, "错误", f"批量删除任务失败: {e}")
    
    def on_task_time_updated(self, task_id: str, new_time: datetime):
        """处理任务时间更新"""
        try:
            # 从调度器获取任务
            task = self.scheduler.get_task_by_id(task_id)
            if task:
                # 更新任务时间
                task.publish_time = new_time
                task.updated_time = datetime.now()
                
                # 使用存储管理器的update_task方法保存更改
                success = self.scheduler.task_storage.update_task(task)
                
                if success:
                    # 记录日志
                    self.log_widget.add_log(f"⏰ 任务时间已更新: {task.title} -> {new_time.strftime('%m-%d %H:%M')}")
                    
                    # 刷新显示
                    self.refresh_tasks()
                else:
                    QMessageBox.warning(self, "错误", "更新任务时间失败")
            else:
                QMessageBox.warning(self, "错误", "找不到指定的任务")
                
        except Exception as e:
            logger.error(f"更新任务时间失败: {e}")
            QMessageBox.critical(self, "错误", f"更新任务时间失败: {e}")
    
    @operation_guard("edit_task", timeout_seconds=30)
    @safe_method(fallback_result=None, error_message="编辑任务失败")
    def on_edit_task(self, task_id: str):
        """编辑任务"""
        try:
            # 获取任务
            task = self.scheduler.get_task_by_id(task_id)
            if not task:
                QMessageBox.warning(self, "错误", "找不到指定的任务")
                return
            
            # 检查任务状态
            if task.status not in [TaskStatus.PENDING, TaskStatus.FAILED]:
                QMessageBox.warning(self, "错误", "只能编辑等待中或失败的任务")
                return
            
            # 导入编辑对话框
            from gui.components.task_edit_dialog import TaskEditDialog
            
            # 创建并显示编辑对话框
            dialog = TaskEditDialog(task, self)
            dialog.task_updated.connect(self.on_task_edited)
            dialog.exec()
            
        except Exception as e:
            logger.error(f"编辑任务失败: {e}")
            QMessageBox.critical(self, "错误", f"编辑任务失败: {e}")
    
    def _handle_test_error(self):
        """处理账号测试错误（在主线程中）"""
        if hasattr(self, '_test_error'):
            error_msg = self._test_error
            del self._test_error
            self.log_widget.add_log(f"❌ 运行账号测试失败: {error_msg}")
            self.account_tab.add_log(f"运行账号测试失败: {error_msg}")
    
    def _restore_login_button(self):
        """恢复登录按钮状态（在主线程中）"""
        if hasattr(self.account_tab, '_login_button') and self.account_tab._login_button:
            try:
                self.account_tab._login_button.setEnabled(True)
                self.account_tab._login_button.setText("登录")
                self.account_tab._login_button = None
                logger.info("✅ 恢复登录按钮状态")
            except Exception as e:
                logger.error(f"恢复登录按钮失败: {e}")
    
    def _handle_test_result(self):
        """处理账号测试结果（在主线程中）"""
        if not hasattr(self, '_test_result'):
            return
            
        success, status, account_name, username = self._test_result
        del self._test_result  # 清理临时变量
        
        if success:
            self.log_widget.add_log(f"✅ 账号测试完成")
            self.account_tab.add_log(f"账号测试完成: {account_name}")
            
            # 如果获取到用户名，更新账号信息
            if username and username != account_name:
                self.account_tab.update_account_info(account_name, username=username, status=status)
            else:
                # 只更新状态
                self.account_tab.update_account_info(account_name, status=status)
        else:
            self.log_widget.add_log(f"❌ 账号测试失败")
            self.account_tab.add_log(f"账号测试失败: {account_name}")
            self.account_tab.add_log(f"测试错误: {status}")
            # 更新失败状态
            self.account_tab.update_account_info(account_name, status=status)
            
        if status:
            for line in status.strip().split('\n'):
                if "测试结果:" in line:
                    self.log_widget.add_log(line.strip())
                    self.account_tab.add_log(line.strip())
                elif line.strip() and not line.startswith("["):
                    self.account_tab.add_log(line.strip())
    
    def on_task_edited(self, task: PublishTask):
        """任务编辑完成"""
        try:
            # 更新任务到存储
            success = self.scheduler.task_storage.update_task(task)
            
            if success:
                self.log_widget.add_log(f"✏️ 任务已更新: {task.title}")
                self.refresh_tasks()
                QMessageBox.information(self, "成功", "任务更新成功")
            else:
                QMessageBox.warning(self, "错误", "更新任务失败")
                
        except Exception as e:
            logger.error(f"更新任务失败: {e}")
            QMessageBox.critical(self, "错误", f"更新任务失败: {e}")
    
    def on_account_selected(self, account_name: str):
        """账号被选中"""
        self.log_widget.add_log(f"👤 选择账号: {account_name}")
        self.account_tab.add_log(f"选择账号: {account_name}")

    

    @operation_guard("login_account", timeout_seconds=60, warning_message="正在登录中，请勿重复点击")
    @safe_method(fallback_result=None, error_message="启动登录失败")
    def on_login_requested(self, account_name: str):
        """请求登录账号（测试账号）"""
        import threading  # 保证线程模块已导入
        try:
            logger.info(f"🔑 on_login_requested 被调用: {account_name}")
            self.log_widget.add_log(f"🔑 正在测试账号 {account_name} 的登录状态...")
            def run_account_test():
                try:
                    import asyncio
                    from core.account_tester import AccountTester
                    logger.info(f"🧵 线程 {threading.current_thread().name} 开始运行账号测试")
                    
                    # 创建新的事件循环
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    try:
                        tester = AccountTester(account_name, headless=False)
                        success, status, username = loop.run_until_complete(tester.test_account())
                        logger.info(f"✅ 账号测试完成: success={success}, status={status}, username={username}")
                    except Exception as test_error:
                        logger.error(f"❌ 账号测试异常: {test_error}")
                        success = False
                        status = f"测试异常: {test_error}"
                        username = None
                    finally:
                        loop.close()
                    # 保存结果到变量，稍后在主线程中使用
                    self._test_result = (success, status, account_name, username)
                    
                    # 使用信号确保在主线程中更新GUI
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, self._handle_test_result)
                except Exception as e:
                    import traceback
                    logger.error(f"❌ 运行账号测试失败: {e}\n{traceback.format_exc()}")
                    # 保存错误信息，在主线程中显示
                    self._test_error = str(e)
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(0, self._handle_test_error)
                finally:
                    # 确保按钮状态被恢复（在主线程中）
                    from PyQt6.QtCore import QTimer
                    QTimer.singleShot(100, self._restore_login_button)
            thread = threading.Thread(target=run_account_test, daemon=True)
            logger.info(f"📋 创建线程: {thread.name} for {account_name}")
            thread.start()
            logger.info(f"📋 线程已启动: {thread.name}")
            self.log_widget.add_log(f"📋 正在启动账号测试器，请稍候...")
            
            # 设置一个超时定时器，确保按钮状态能恢复
            def check_thread_timeout():
                if thread.is_alive():
                    logger.warning("⚠️ 登录线程超时，强制恢复按钮状态")
                    self.account_tab.add_log("登录超时，请重试")
                    if hasattr(self.account_tab, '_login_button') and self.account_tab._login_button:
                        try:
                            self.account_tab._login_button.setEnabled(True)
                            self.account_tab._login_button.setText("登录")
                            self.account_tab._login_button = None
                        except:
                            pass
            
            QTimer.singleShot(60000, check_thread_timeout)  # 60秒超时
        except Exception as e:
            import traceback
            logger.error(f"启动账号测试失败: {e}\n{traceback.format_exc()}")
            self.log_widget.add_log(f"❌ 启动账号测试失败: {e}")
            self.account_tab.add_log(f"启动账号测试失败: {e}")
            QMessageBox.critical(self, "错误", f"启动账号测试失败: {e}")
    
    def on_tasks_imported(self, tasks: List[PublishTask]):
        """处理Excel导入的任务"""
        try:
            added_count = 0
            failed_count = 0
            
            for task in tasks:
                if self.scheduler.add_task(task):
                    added_count += 1
                else:
                    failed_count += 1
            
            # 记录日志
            self.log_widget.add_log(f"📥 Excel导入完成: 成功 {added_count} 个，失败 {failed_count} 个")
            
            # 刷新任务列表
            self.refresh_tasks()
            
            # 切换到任务管理标签页
            self.tab_widget.setCurrentIndex(0)
            
            # 显示成功提示
            if added_count > 0:
                QMessageBox.information(
                    self, 
                    "导入成功", 
                    f"成功导入 {added_count} 个任务！\n已自动切换到任务管理页面查看。"
                )
            
        except Exception as e:
            logger.error(f"处理Excel导入任务失败: {e}")
            self.log_widget.add_log(f"❌ 处理Excel导入任务失败: {e}")
            QMessageBox.critical(self, "错误", f"处理导入任务失败: {e}")
    
    def connect_signals(self):
        """连接信号"""
        self.scheduler.task_started.connect(self.on_task_started)
        self.scheduler.task_completed.connect(self.on_task_completed)
        self.scheduler.task_failed.connect(self.on_task_failed)
        self.scheduler.scheduler_status.connect(self.on_scheduler_status)
        self.scheduler.scheduler_message.connect(self.on_scheduler_message)
    
    def setup_refresh_timer(self):
        """设置刷新定时器"""
        self.refresh_timer = QTimer(self)
        self.refresh_timer.timeout.connect(self.refresh_tasks)
        self.refresh_timer.start(10000)  # 每10秒刷新一次
    
    
    def delete_task(self, task_id: str):
        """删除任务"""
        reply = QMessageBox.question(
            self, "确认删除", 
            "确定要删除这个任务吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            if self.scheduler.delete_task(task_id):
                self.log_widget.add_log("🗑️ 任务删除成功")
                self.refresh_tasks()
            else:
                self.log_widget.add_log("❌ 任务删除失败")
    
    def refresh_tasks(self):
        """刷新任务列表"""
        try:
            # 刷新任务详情表格
            self.task_detail_table.refresh_table()
            
        except Exception as e:
            logger.error(f"刷新任务失败: {e}")
    
    def clear_completed_tasks(self):
        """清除已完成的任务"""
        try:
            tasks = self.scheduler.get_all_tasks()
            completed_tasks = [t for t in tasks if t.status == TaskStatus.COMPLETED]
            
            if not completed_tasks:
                QMessageBox.information(self, "提示", "没有已完成的任务")
                return
            
            reply = QMessageBox.question(
                self, "确认清除", 
                f"确定要清除 {len(completed_tasks)} 个已完成的任务吗？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                removed_count = 0
                for task in completed_tasks:
                    if self.scheduler.delete_task(task.id):
                        removed_count += 1
                
                self.log_widget.add_log(f"🧹 清除了 {removed_count} 个已完成任务")
                self.refresh_tasks()
                
        except Exception as e:
            logger.error(f"清除已完成任务失败: {e}")
            QMessageBox.critical(self, "错误", f"清除任务失败: {e}")
    
    @pyqtSlot(str)
    def on_task_started(self, task_id: str):
        """任务开始执行"""
        task = self.scheduler.get_task_by_id(task_id)
        if task:
            self.log_widget.add_log(f"🚀 开始执行: {task.title}")
        self.refresh_tasks()
    
    @pyqtSlot(str, dict)
    def on_task_completed(self, task_id: str, result: dict):
        """任务完成"""
        task = self.scheduler.get_task_by_id(task_id)
        if task:
            self.log_widget.add_log(f"✅ 发布成功: {task.title}")
        self.refresh_tasks()
    
    @pyqtSlot(str, str)
    def on_task_failed(self, task_id: str, error: str):
        """任务失败"""
        task = self.scheduler.get_task_by_id(task_id)
        if task:
            self.log_widget.add_log(f"❌ 发布失败: {task.title} - {error}")
        self.refresh_tasks()
    
    @pyqtSlot(str)
    def on_scheduler_status(self, status: str):
        """调度器状态变化"""
        # 状态已经由控制面板处理
        pass
    
    @pyqtSlot(str)
    def on_scheduler_message(self, message: str):
        """处理调度器消息"""
        self.log_widget.add_log(message)
    
    @safe_method(fallback_result=None, error_message="应用关闭处理失败")
    def closeEvent(self, event):
        """关闭事件"""
        try:
            logger.info("🔄 开始关闭应用...")
            
            # 停止定时器
            if hasattr(self, 'refresh_timer') and self.refresh_timer:
                self.refresh_timer.stop()
                self.refresh_timer.deleteLater()
                self.refresh_timer = None
            
            # 清理调度器资源
            if hasattr(self, 'scheduler'):
                self.scheduler.cleanup_resources()
            
            # 清理账号管理组件
            
            # 清理Excel导入器
            if hasattr(self, 'excel_importer'):
                self.excel_importer.cancel_import()
                self.excel_importer.deleteLater()
            
            # 清理组件
            components_to_cleanup = [
                'control_panel', 'task_detail_table', 'account_tab', 'log_widget'
            ]
            
            for component_name in components_to_cleanup:
                if hasattr(self, component_name):
                    component = getattr(self, component_name)
                    if component:
                        component.deleteLater()
            
            # 清理操作锁
            cleanup_on_exit()
            
            logger.info("🏁 应用正常关闭")
            
        except Exception as e:
            logger.error(f"❌ 应用关闭时出错: {e}")
        finally:
            event.accept()
    
    # Excel导入事件处理方法
    @safe_method(fallback_result=None, error_message="Excel导入事件处理失败")
    def on_excel_import_started(self):
        """处理Excel导入开始事件"""
        self.log_widget.add_log("🚀 开始导入Excel文件...")
        # 禁用导入按钮防止重复操作
        if hasattr(self, 'control_panel'):
            self.control_panel.set_import_enabled(False)
    
    @safe_method(fallback_result=None, error_message="Excel导入进度处理失败")
    def on_excel_import_progress(self, progress: int, message: str):
        """处理Excel导入进度事件"""
        self.log_widget.add_log(f"📈 导入进度: {progress}% - {message}")
    
    @safe_method(fallback_result=None, error_message="Excel导入完成处理失败")
    def on_excel_import_completed(self, success: bool, message: str, tasks: List[PublishTask]):
        """处理Excel导入完成事件"""
        # 重新启用导入按钮
        if hasattr(self, 'control_panel'):
            self.control_panel.set_import_enabled(True)
        
        if success:
            self.log_widget.add_log(f"✅ Excel导入成功: {message}")
            
            # 添加任务到调度器
            added_count = 0
            for task in tasks:
                if self.scheduler.add_task(task):
                    added_count += 1
            
            self.log_widget.add_log(f"📝 成功添加 {added_count} 个任务")
            self.refresh_tasks()
            
            # 显示成功提示
            QMessageBox.information(
                self, 
                "导入成功", 
                f"成功导入 {added_count} 个任务！\n已自动刷新任务列表。"
            )
            
            # 切换到任务管理标签页
            if hasattr(self, 'tab_widget'):
                self.tab_widget.setCurrentIndex(0)
                
        else:
            self.log_widget.add_log(f"❌ Excel导入失败: {message}")
            QMessageBox.critical(self, "导入失败", f"Excel导入失败：\n{message}")
    
    @safe_method(fallback_result=None, error_message="Excel文件验证处理失败")
    def on_excel_validation_completed(self, is_valid: bool, message: str):
        """处理Excel文件验证完成事件"""
        if is_valid:
            self.log_widget.add_log(f"✅ Excel文件验证通过: {message}")
        else:
            self.log_widget.add_log(f"❌ Excel文件验证失败: {message}")
            QMessageBox.warning(self, "文件验证失败", f"Excel文件格式不符合要求：\n{message}")
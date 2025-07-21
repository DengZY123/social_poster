"""
专业版账号管理标签页
参考专业界面设计，采用表格式布局
"""
import sys
import json
import webbrowser
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QLineEdit, QLabel, QMessageBox, QComboBox,
    QTextEdit, QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QBrush, QColor
from loguru import logger

# 添加core模块路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class AccountTab(QWidget):
    """专业版账号管理标签页"""
    
    # 信号定义
    account_selected = pyqtSignal(str)      # 账号被选中
    login_requested = pyqtSignal(str)       # 请求登录
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.accounts = []  # 账号列表
        self.current_account = None  # 当前选中的账号
        
        self.setup_ui()
        self.load_accounts()
    
    def setup_ui(self):
        """设置UI"""
        layout = QVBoxLayout(self)
        
        # 顶部操作按钮区域
        self.create_toolbar(layout)
        
        # 账号表格
        self.create_account_table(layout)
        
        # 底部执行日志
        self.create_log_area(layout)
    
    def create_toolbar(self, parent_layout):
        """创建顶部工具栏"""
        toolbar_layout = QHBoxLayout()
        
        # 添加账号按钮
        self.add_btn = QPushButton("添加账号")
        self.add_btn.clicked.connect(self.add_account)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        toolbar_layout.addWidget(self.add_btn)
        
        # 刷新列表按钮
        self.refresh_btn = QPushButton("刷新列表")
        self.refresh_btn.clicked.connect(self.refresh_accounts)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        toolbar_layout.addWidget(self.refresh_btn)
        
        toolbar_layout.addStretch()
        parent_layout.addLayout(toolbar_layout)
    
    def create_account_table(self, parent_layout):
        """创建账号表格"""
        # 表格
        self.account_table = QTableWidget()
        self.setup_table()
        parent_layout.addWidget(self.account_table)
    
    def create_log_area(self, parent_layout):
        """创建执行日志区域"""
        # 执行日志
        log_group = QGroupBox("执行日志")
        log_group_layout = QVBoxLayout(log_group)
        
        self.operation_log = QTextEdit()
        self.operation_log.setPlaceholderText("账号相关操作日志将在这里显示...")
        self.operation_log.setReadOnly(True)
        self.operation_log.setFont(QFont("Monaco", 10))  # 使用 Monaco 等宽字体
        log_group_layout.addWidget(self.operation_log)
        
        parent_layout.addWidget(log_group)
    
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = ["平台", "账号名称", "状态", "最后登录时间", "备注", "操作", "登录"]
        self.account_table.setColumnCount(len(headers))
        self.account_table.setHorizontalHeaderLabels(headers)
        
        # 设置表格属性
        self.account_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.account_table.setAlternatingRowColors(True)
        self.account_table.setSortingEnabled(True)
        
        # 设置列宽
        header = self.account_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # 平台
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # 账号名称
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # 状态
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # 最后登录时间
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)  # 备注
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # 操作
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 登录
        header.resizeSection(5, 180)  # 增加宽度以容纳新按钮
        header.resizeSection(6, 80)
        
        # 连接选择变化信号
        self.account_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def load_accounts(self):
        """加载账号列表"""
        try:
            accounts_file = Path("accounts.json")
            if accounts_file.exists():
                with open(accounts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.accounts = data.get('accounts', [])
            
            # 如果没有账号，创建默认账号
            if not self.accounts:
                self.accounts = [
                    {
                        "name": "默认账号",
                        "platform": "小红书",
                        "status": "未测试",
                        "last_login": "",
                        "notes": "test",
                        "created_time": datetime.now().isoformat()
                    }
                ]
                self.save_accounts()
            
            self.update_table()
            self.add_log("账号列表加载完成")
            
        except Exception as e:
            logger.error(f"加载账号失败: {e}")
            # 创建默认账号
            self.accounts = [
                {
                    "name": "默认账号", 
                    "platform": "小红书",
                    "status": "未测试",
                    "last_login": "",
                    "notes": "test",
                    "created_time": datetime.now().isoformat()
                }
            ]
            self.update_table()
            self.add_log("创建默认账号")
    
    def save_accounts(self):
        """保存账号列表"""
        try:
            accounts_file = Path("accounts.json")
            with open(accounts_file, 'w', encoding='utf-8') as f:
                json.dump({"accounts": self.accounts}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存账号失败: {e}")
    
    def _parse_display_status(self, raw_status: str) -> str:
        """解析原始状态信息，返回显示用的简洁状态"""
        if not raw_status:
            return "未测试"
        
        # 转换为小写便于匹配
        status_lower = raw_status.lower()
        
        # 根据关键词判断状态
        if '有效' in raw_status or '登录成功' in raw_status or '已登录' in status_lower:
            return "已登录"
        elif '失败' in raw_status or '失效' in raw_status or '未登录' in status_lower or 'error' in status_lower:
            return "未登录"
        elif raw_status == '未测试':
            return "未测试"
        else:
            # 默认返回未测试
            return "未测试"
    
    def update_table(self):
        """更新表格显示"""
        # 清理现有的单元格部件，防止重复创建
        for row in range(self.account_table.rowCount()):
            # 清理操作按钮
            widget = self.account_table.cellWidget(row, 5)
            if widget:
                self.account_table.removeCellWidget(row, 5)
                widget.deleteLater()
            
            # 清理登录按钮
            widget = self.account_table.cellWidget(row, 6)
            if widget:
                self.account_table.removeCellWidget(row, 6)
                widget.deleteLater()
        
        self.account_table.setRowCount(len(self.accounts))
        
        for row, account in enumerate(self.accounts):
            # 平台
            platform_item = QTableWidgetItem(account['platform'])
            self.account_table.setItem(row, 0, platform_item)
            
            # 账号名称 - 优先显示实际用户名
            display_name = account.get('username', account['name'])
            name_item = QTableWidgetItem(display_name)
            name_item.setData(Qt.ItemDataRole.UserRole, account)  # 存储完整账号数据
            self.account_table.setItem(row, 1, name_item)
            
            # 状态 - 解析并显示简洁状态
            raw_status = account.get('status', '未测试')
            display_status = self._parse_display_status(raw_status)
            status_item = QTableWidgetItem(display_status)
            
            # 根据状态设置颜色
            if display_status == '已登录':
                status_item.setBackground(QBrush(QColor("#d4edda")))
                status_item.setForeground(QBrush(QColor("#155724")))
            elif display_status == '未登录':
                status_item.setBackground(QBrush(QColor("#f8d7da")))
                status_item.setForeground(QBrush(QColor("#721c24")))
            else:  # 未测试
                status_item.setBackground(QBrush(QColor("#fff3cd")))
                status_item.setForeground(QBrush(QColor("#856404")))
            self.account_table.setItem(row, 2, status_item)
            
            # 最后登录时间
            last_login = account.get('last_login', '')
            if last_login:
                # 格式化时间显示
                try:
                    if 'T' in last_login:  # ISO格式
                        dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                        formatted_time = dt.strftime("%Y-%m-%d %H:%M")
                    else:
                        formatted_time = last_login
                except:
                    formatted_time = last_login
            else:
                formatted_time = ""
            
            time_item = QTableWidgetItem(formatted_time)
            self.account_table.setItem(row, 3, time_item)
            
            # 备注
            notes_item = QTableWidgetItem(account.get('notes', ''))
            self.account_table.setItem(row, 4, notes_item)
            
            # 操作按钮
            self.create_action_buttons(row, account)
            
            # 登录按钮
            self.create_login_button(row, account)
    
    def create_action_buttons(self, row: int, account: dict):
        """创建操作按钮"""
        button_widget = QWidget()
        button_layout = QHBoxLayout(button_widget)
        button_layout.setContentsMargins(2, 2, 2, 2)
        button_layout.setSpacing(2)
        
        # 编辑按钮
        edit_btn = QPushButton("编辑")
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        edit_btn.clicked.connect(lambda checked=False, acc=account: self.edit_account(acc))
        button_layout.addWidget(edit_btn)
        
        # 删除按钮
        delete_btn = QPushButton("删除")
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
        delete_btn.clicked.connect(lambda checked=False, acc=account: self.delete_account(acc))
        button_layout.addWidget(delete_btn)
        
        # 打开创作中心按钮
        creator_btn = QPushButton("创作中心")
        creator_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        creator_btn.clicked.connect(lambda checked=False, acc=account: self.open_creator_center(acc))
        button_layout.addWidget(creator_btn)
        
        self.account_table.setCellWidget(row, 5, button_widget)
    
    def create_login_button(self, row: int, account: dict):
        """创建登录按钮"""
        login_btn = QPushButton("登录")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                cursor: not-allowed;
            }
        """)
        # 传递按钮引用，以便在登录时禁用
        # 使用默认参数来避免闭包问题
        login_btn.clicked.connect(lambda checked=False, acc=account, btn=login_btn: self.login_account(acc, btn))
        self.account_table.setCellWidget(row, 6, login_btn)
    
    def add_account(self):
        """添加账号"""
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox
        
        dialog = QDialog(self)
        dialog.setWindowTitle("添加账号")
        dialog.setModal(True)
        dialog.resize(400, 250)
        
        layout = QFormLayout(dialog)
        
        # 输入字段
        name_input = QLineEdit()
        name_input.setPlaceholderText("请输入账号名称")
        
        platform_combo = QComboBox()
        platform_combo.addItems(["小红书"])
        
        notes_input = QLineEdit()
        notes_input.setPlaceholderText("备注信息（可选）")
        
        layout.addRow("账号名称:", name_input)
        layout.addRow("平台:", platform_combo)
        layout.addRow("备注:", notes_input)
        
        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            account_name = name_input.text().strip()
            platform = platform_combo.currentText()
            notes = notes_input.text().strip()
            
            if not account_name:
                QMessageBox.warning(self, "错误", "请输入账号名称")
                return
            
            # 检查重复
            if any(acc['name'] == account_name for acc in self.accounts):
                QMessageBox.warning(self, "错误", "账号名称已存在")
                return
            
            # 添加账号
            new_account = {
                "name": account_name,
                "platform": platform,
                "status": "未测试",
                "last_login": "",
                "notes": notes,
                "created_time": datetime.now().isoformat()
            }
            
            self.accounts.append(new_account)
            self.save_accounts()
            self.update_table()
            
            self.add_log(f"添加账号: {account_name}")
            
            QMessageBox.information(self, "成功", f"账号 '{account_name}' 添加成功")
    
    def edit_account(self, account: dict):
        """编辑账号"""
        self.add_log(f"编辑账号功能待实现: {account['name']}")
        QMessageBox.information(self, "提示", f"编辑账号功能待实现\n账号: {account['name']}")
    
    def delete_account(self, account: dict):
        """删除账号"""
        if len(self.accounts) <= 1:
            QMessageBox.warning(self, "错误", "至少要保留一个账号")
            return
        
        reply = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除账号 '{account['name']}' 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # 删除账号
            self.accounts = [acc for acc in self.accounts if acc['name'] != account['name']]
            self.save_accounts()
            self.update_table()
            
            self.add_log(f"删除账号: {account['name']}")
            
            QMessageBox.information(self, "成功", f"账号 '{account['name']}' 已删除")
    
    def login_account(self, account: dict, button: QPushButton = None):
        """登录账号"""
        logger.info(f"🔐 登录账号: {account['name']}")
        self.add_log(f"登录账号: {account['name']}")
        
        # 禁用按钮，防止重复点击
        if button:
            button.setEnabled(False)
            button.setText("登录中...")
        
        # 存储按钮引用，以便在登录完成后重新启用
        self._login_button = button
        self._login_account_name = account['name']
        
        self.login_requested.emit(account['name'])
    
    def open_creator_center(self, account: dict):
        """打开创作中心"""
        import webbrowser
        
        account_name = account['name']
        
        # 检查账号状态（可选，提醒用户）
        status = account.get('status', '未测试')
        if '有效' not in status and '登录' not in status:
            reply = QMessageBox.question(
                self, 
                "提示", 
                f"账号 {account_name} 未登录，创作中心可能需要重新登录。\n\n是否继续打开？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        
        url = "https://creator.xiaohongshu.com/new/note-manager?source=official"
        logger.info(f"🌐 打开创作中心: {url}")
        self.add_log(f"打开创作中心")
        
        try:
            webbrowser.open(url)
            self.add_log("创作中心已在默认浏览器中打开")
        except Exception as e:
            logger.error(f"打开创作中心失败: {e}")
            self.add_log(f"打开创作中心失败: {e}")
            QMessageBox.warning(self, "错误", f"无法打开创作中心: {e}")
    
    def _show_error(self, error_msg: str):
        """在主线程中显示错误消息"""
        self.add_log(f"❌ {error_msg}")
        QMessageBox.warning(self, "错误", error_msg)
    
    def refresh_accounts(self):
        """刷新账号列表"""
        self.load_accounts()
        self.add_log("刷新账号列表")
    
    def on_selection_changed(self):
        """选择变化处理"""
        current_row = self.account_table.currentRow()
        if current_row >= 0 and current_row < len(self.accounts):
            account = self.accounts[current_row]
            self.current_account = account['name']
            
            # 发出信号
            self.account_selected.emit(account['name'])
    
    def get_current_account(self) -> Optional[str]:
        """获取当前选中的账号"""
        return self.current_account
    
    def get_current_platform(self) -> str:
        """获取当前账号的平台"""
        if not self.current_account:
            return "小红书"
        
        account = next((acc for acc in self.accounts if acc['name'] == self.current_account), None)
        return account['platform'] if account else "小红书"
    
    def add_log(self, message: str):
        """添加日志信息"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.operation_log.append(f"[{timestamp}] {message}")
        
        # 自动滚动到底部
        cursor = self.operation_log.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        self.operation_log.setTextCursor(cursor)
        
        # 检查是否是登录完成的消息，恢复按钮状态
        if hasattr(self, '_login_button') and self._login_button:
            if ("账号测试完成" in message or "账号测试失败" in message or 
                "运行账号测试失败" in message or "测试结果:" in message or
                "账号有效" in message or "手动登录成功" in message or
                "登录超时" in message or "启动账号测试失败" in message):
                # 恢复按钮状态
                self._login_button.setEnabled(True)
                self._login_button.setText("登录")
                self._login_button = None
                self._login_account_name = None
    
    def clear_log(self):
        """清空日志"""
        self.operation_log.clear()
        self.add_log("日志已清空")
    
    def update_account_info(self, account_name: str, username: str = None, status: str = None):
        """更新账号信息（用户名、状态等）"""
        try:
            # 查找账号
            account_updated = False
            for account in self.accounts:
                if account['name'] == account_name:
                    # 更新用户名
                    if username and username != account_name:
                        account['username'] = username
                        self.add_log(f"更新账号用户名: {account_name} → {username}")
                    
                    # 更新状态
                    if status:
                        account['status'] = status
                        account['last_login'] = datetime.now().isoformat()
                    
                    account_updated = True
                    break
            
            if account_updated:
                # 保存更新
                self.save_accounts()
                # 刷新表格显示
                self.update_table()
                return True
            else:
                logger.warning(f"未找到账号: {account_name}")
                return False
                
        except Exception as e:
            logger.error(f"更新账号信息失败: {e}")
            return False
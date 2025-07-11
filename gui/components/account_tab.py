"""
专业版账号管理标签页
参考专业界面设计，采用表格式布局
"""
import sys
import json
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
        
        # 统计信息区域
        self.create_stats_area(layout)
        
        # 账号表格
        self.create_account_table(layout)
        
        # 底部信息区域
        self.create_info_area(layout)
    
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
        
        # 批量测试账号按钮
        self.batch_test_btn = QPushButton("批量测试账号")
        self.batch_test_btn.clicked.connect(self.batch_test_accounts)
        self.batch_test_btn.setStyleSheet("""
            QPushButton {
                background-color: #17a2b8;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #138496;
            }
        """)
        toolbar_layout.addWidget(self.batch_test_btn)
        
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
    
    def create_stats_area(self, parent_layout):
        """创建统计信息区域"""
        stats_layout = QHBoxLayout()
        
        # 统计标签
        self.stats_label = QLabel("总账号: 0  有效: 0  失效: 0")
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #495057;
                padding: 8px;
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
            }
        """)
        stats_layout.addWidget(self.stats_label)
        
        stats_layout.addStretch()
        parent_layout.addLayout(stats_layout)
    
    def create_account_table(self, parent_layout):
        """创建账号表格"""
        # 表格
        self.account_table = QTableWidget()
        self.setup_table()
        parent_layout.addWidget(self.account_table)
    
    def setup_table(self):
        """设置表格"""
        # 设置列
        headers = ["平台", "账号名称", "状态", "最后登录时间", "备注", "操作", "测试"]
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
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)  # 测试
        header.resizeSection(5, 120)
        header.resizeSection(6, 80)
        
        # 连接选择变化信号
        self.account_table.itemSelectionChanged.connect(self.on_selection_changed)
    
    def create_info_area(self, parent_layout):
        """创建底部信息区域"""
        info_layout = QHBoxLayout()
        
        # 左侧：账号信息
        info_group = QGroupBox("账号信息")
        info_group_layout = QVBoxLayout(info_group)
        
        self.account_info = QTextEdit()
        self.account_info.setPlaceholderText("选择账号查看详细信息...")
        self.account_info.setMaximumHeight(120)
        self.account_info.setReadOnly(True)
        info_group_layout.addWidget(self.account_info)
        
        info_layout.addWidget(info_group, 1)
        
        # 右侧：操作日志
        log_group = QGroupBox("操作日志")
        log_group_layout = QVBoxLayout(log_group)
        
        self.operation_log = QTextEdit()
        self.operation_log.setPlaceholderText("账号操作日志将在这里显示...")
        self.operation_log.setMaximumHeight(120)
        self.operation_log.setReadOnly(True)
        log_group_layout.addWidget(self.operation_log)
        
        info_layout.addWidget(log_group, 1)
        
        parent_layout.addLayout(info_layout)
    
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
            self.update_stats()
            
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
            self.update_stats()
    
    def save_accounts(self):
        """保存账号列表"""
        try:
            accounts_file = Path("accounts.json")
            with open(accounts_file, 'w', encoding='utf-8') as f:
                json.dump({"accounts": self.accounts}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存账号失败: {e}")
    
    def update_table(self):
        """更新表格显示"""
        self.account_table.setRowCount(len(self.accounts))
        
        for row, account in enumerate(self.accounts):
            # 平台
            platform_item = QTableWidgetItem(account['platform'])
            self.account_table.setItem(row, 0, platform_item)
            
            # 账号名称
            name_item = QTableWidgetItem(account['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, account)  # 存储完整账号数据
            self.account_table.setItem(row, 1, name_item)
            
            # 状态
            status_item = QTableWidgetItem(account.get('status', '未测试'))
            # 根据状态设置颜色
            status = account.get('status', '未测试')
            if '有效' in status:
                status_item.setBackground(QBrush(QColor("#d4edda")))
                status_item.setForeground(QBrush(QColor("#155724")))
            elif '失效' in status or '失败' in status:
                status_item.setBackground(QBrush(QColor("#f8d7da")))
                status_item.setForeground(QBrush(QColor("#721c24")))
            else:
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
            
            # 测试按钮
            self.create_test_button(row, account)
    
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
        edit_btn.clicked.connect(lambda: self.edit_account(account))
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
        delete_btn.clicked.connect(lambda: self.delete_account(account))
        button_layout.addWidget(delete_btn)
        
        self.account_table.setCellWidget(row, 5, button_widget)
    
    def create_test_button(self, row: int, account: dict):
        """创建测试按钮"""
        test_btn = QPushButton("测试")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
        test_btn.clicked.connect(lambda: self.test_account(account))
        self.account_table.setCellWidget(row, 6, test_btn)
    
    def update_stats(self):
        """更新统计信息"""
        total = len(self.accounts)
        valid = len([acc for acc in self.accounts if '有效' in acc.get('status', '')])
        invalid = len([acc for acc in self.accounts if '失效' in acc.get('status', '') or '失败' in acc.get('status', '')])
        
        self.stats_label.setText(f"总账号: {total}  有效: {valid}  失效: {invalid}")
    
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
            self.update_stats()
            
            self.operation_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 添加账号: {account_name}")
            
            QMessageBox.information(self, "成功", f"账号 '{account_name}' 添加成功")
    
    def edit_account(self, account: dict):
        """编辑账号"""
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
            self.update_stats()
            
            self.operation_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 删除账号: {account['name']}")
            
            QMessageBox.information(self, "成功", f"账号 '{account['name']}' 已删除")
    
    def test_account(self, account: dict):
        """测试账号（打开登录页面）"""
        logger.info(f"🔐 测试账号: {account['name']}")
        self.operation_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 测试账号: {account['name']}")
        self.login_requested.emit(account['name'])
    
    def batch_test_accounts(self):
        """批量测试账号"""
        QMessageBox.information(self, "提示", "批量测试功能待实现")
    
    def refresh_accounts(self):
        """刷新账号列表"""
        self.load_accounts()
        self.operation_log.append(f"[{datetime.now().strftime('%H:%M:%S')}] 刷新账号列表")
    
    def on_selection_changed(self):
        """选择变化处理"""
        current_row = self.account_table.currentRow()
        if current_row >= 0 and current_row < len(self.accounts):
            account = self.accounts[current_row]
            self.current_account = account['name']
            
            # 更新账号信息显示
            info_text = f"""账号名称: {account['name']}
平台: {account['platform']}
状态: {account.get('status', '未测试')}
最后登录: {account.get('last_login', '未登录')}
备注: {account.get('notes', '')}
创建时间: {account.get('created_time', '')}"""
            
            self.account_info.setText(info_text)
            
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
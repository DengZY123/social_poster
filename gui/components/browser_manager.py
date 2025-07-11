"""
浏览器管理组件
"""
import os
import sys
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QProgressBar, QGroupBox, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from loguru import logger


class BrowserDownloadThread(QThread):
    """浏览器下载线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, browser_type="firefox"):
        super().__init__()
        self.browser_type = browser_type
        
    def run(self):
        """执行下载"""
        try:
            self.progress.emit(0, "正在准备下载...")
            
            # 使用默认路径，不设置自定义路径
            # 这样浏览器会下载到 Playwright 的默认位置
            env = os.environ.copy()
            
            # 移除可能存在的自定义路径环境变量
            if 'PLAYWRIGHT_BROWSERS_PATH' in env:
                del env['PLAYWRIGHT_BROWSERS_PATH']
            
            self.progress.emit(20, "使用 Playwright 默认下载路径...")
            
            # 构建命令
            cmd = [sys.executable, "-m", "playwright", "install", self.browser_type]
            
            self.progress.emit(40, f"开始下载 {self.browser_type}...")
            
            # 执行下载
            process = subprocess.Popen(
                cmd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            # 读取输出
            for line in process.stdout:
                line = line.strip()
                if line:
                    # 不要将playwright的输出记录到日志，避免日志混乱
                    # 简单的进度估算
                    if "Downloading" in line:
                        self.progress.emit(60, "正在下载浏览器文件...")
                    elif "Installing" in line:
                        self.progress.emit(80, "正在安装浏览器...")
                    elif "browser" in line.lower() and "installed" in line.lower():
                        self.progress.emit(90, "浏览器安装中...")
            
            process.wait()
            
            if process.returncode == 0:
                self.progress.emit(100, "浏览器下载安装完成！")
                self.finished.emit(True, f"{self.browser_type} 浏览器已成功安装")
            else:
                self.finished.emit(False, f"下载失败，返回码: {process.returncode}")
                
        except Exception as e:
            logger.error(f"下载浏览器失败: {e}")
            self.finished.emit(False, str(e))


class BrowserManager(QGroupBox):
    """浏览器管理器组件"""
    
    def __init__(self, parent=None):
        super().__init__("浏览器管理", parent)
        self.download_thread = None
        self.setup_ui()
        # 延迟检查浏览器状态，避免初始化时的问题
        QTimer.singleShot(100, self.check_browser_status)
        
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 状态显示
        status_layout = QHBoxLayout()
        status_layout.addWidget(QLabel("浏览器状态："))
        self.status_label = QLabel("检查中...")
        self.status_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)
        
        # 说明文字
        info_label = QLabel(
            "小红书发布工具需要Firefox浏览器来运行。\n"
            "首次使用需要下载浏览器（约200MB），请确保网络连接正常。"
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # 下载按钮和进度条
        self.download_btn = QPushButton("下载Firefox浏览器")
        self.download_btn.clicked.connect(self.download_browser)
        layout.addWidget(self.download_btn)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setVisible(False)
        layout.addWidget(self.progress_label)
        
        # Windows特别说明
        if sys.platform == "win32":
            win_info = QLabel(
                "Windows用户注意：\n"
                "• 下载过程可能需要5-10分钟\n"
                "• 请确保防火墙允许程序联网\n"
                "• 如果下载失败，请检查网络代理设置"
            )
            win_info.setWordWrap(True)
            win_info.setStyleSheet("color: #666; font-size: 11px;")
            layout.addWidget(win_info)
            
    def check_browser_status(self):
        """检查浏览器状态"""
        try:
            # 检查两个可能的路径
            # 1. 自定义路径（PLAYWRIGHT_BROWSERS_PATH环境变量指定的路径）
            if sys.platform == "darwin":
                custom_path = Path.home() / "Library" / "Application Support" / "XhsPublisher" / "playwright-browsers"
                default_path = Path.home() / "Library" / "Caches" / "ms-playwright"
            elif sys.platform == "win32":
                custom_path = Path.home() / "AppData" / "Local" / "XhsPublisher" / "playwright-browsers"
                default_path = Path.home() / "AppData" / "Local" / "ms-playwright"
            else:
                custom_path = Path.home() / ".cache" / "XhsPublisher" / "playwright-browsers"
                default_path = Path.home() / ".cache" / "ms-playwright"
            
            # 检查Firefox是否存在（在任一路径中）
            firefox_found = False
            
            # 先检查自定义路径
            if custom_path.exists():
                firefox_paths = list(custom_path.glob("firefox-*/firefox*"))
                if firefox_paths:
                    firefox_found = True
                    logger.debug(f"在自定义路径找到Firefox: {custom_path}")
            
            # 再检查默认路径
            if not firefox_found and default_path.exists():
                firefox_paths = list(default_path.glob("firefox-*/firefox*"))
                if firefox_paths:
                    firefox_found = True
                    logger.debug(f"在默认路径找到Firefox: {default_path}")
            
            if firefox_found:
                self.status_label.setText("✅ 已安装")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.download_btn.setText("重新下载Firefox浏览器")
            else:
                self.status_label.setText("❌ 未安装")
                self.status_label.setStyleSheet("color: red; font-weight: bold;")
                self.download_btn.setText("下载Firefox浏览器")
                
        except Exception as e:
            logger.error(f"检查浏览器状态失败: {e}")
            self.status_label.setText("⚠️ 检查失败")
            self.status_label.setStyleSheet("color: orange; font-weight: bold;")
            
    def download_browser(self):
        """下载浏览器"""
        if self.download_thread and self.download_thread.isRunning():
            QMessageBox.warning(self, "提示", "浏览器正在下载中，请稍候...")
            return
            
        reply = QMessageBox.question(
            self,
            "确认下载",
            "即将下载Firefox浏览器（约200MB），是否继续？\n\n"
            "下载过程中请保持网络连接，不要关闭程序。",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.start_download()
            
    def start_download(self):
        """开始下载"""
        self.download_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_label.setVisible(True)
        
        self.download_thread = BrowserDownloadThread("firefox")
        self.download_thread.progress.connect(self.update_progress)
        self.download_thread.finished.connect(self.download_finished)
        self.download_thread.start()
        
    def update_progress(self, value: int, message: str):
        """更新进度"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def download_finished(self, success: bool, message: str):
        """下载完成"""
        logger.info(f"浏览器下载完成: success={success}, message={message}")
        
        self.download_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_label.setVisible(False)
        
        if success:
            QMessageBox.information(self, "下载成功", message)
            self.check_browser_status()
        else:
            QMessageBox.critical(self, "下载失败", f"浏览器下载失败：\n{message}")
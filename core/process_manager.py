"""
进程池管理器
使用QProcess实现真正的异步执行，避免GUI阻塞
"""
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path
from PyQt6.QtCore import QObject, QProcess, QTimer, pyqtSignal
from loguru import logger

from .models import PublishTask


class ProcessManager(QObject):
    """进程池管理器"""
    
    # 信号定义
    process_finished = pyqtSignal(str, dict)  # task_id, result
    process_failed = pyqtSignal(str, str)     # task_id, error_message
    process_started = pyqtSignal(str)         # task_id
    
    def __init__(self, max_processes=2, parent=None):
        super().__init__(parent)
        
        self.max_processes = max_processes
        self.active_processes = {}      # task_id -> QProcess
        self.process_data = {}          # QProcess -> process_info
        self.pending_tasks = []         # 等待队列
        
        # 进程清理定时器
        self.cleanup_timer = QTimer(self)
        self.cleanup_timer.timeout.connect(self.cleanup_finished_processes)
        self.cleanup_timer.start(5000)  # 每5秒清理一次
        
        logger.info(f"✅ 进程管理器初始化完成，最大并发数: {max_processes}")
    
    def can_start_new_process(self) -> bool:
        """检查是否可以启动新进程"""
        return len(self.active_processes) < self.max_processes
    
    def start_task(self, task: PublishTask, cmd: List[str]) -> bool:
        """启动任务进程"""
        try:
            # 检查是否已经在执行
            if task.id in self.active_processes:
                logger.warning(f"⚠️ 任务已在执行中: {task.title}")
                return False
            
            # 检查进程池是否已满
            if not self.can_start_new_process():
                logger.info(f"📋 进程池已满，任务加入等待队列: {task.title}")
                self.pending_tasks.append((task, cmd))
                return True
            
            # 创建新进程
            process = self._create_process(task, cmd)
            if not process:
                return False
            
            # 启动进程
            logger.info(f"🚀 启动进程: {task.title}")
            process.start(cmd[0], cmd[1:])
            
            # 检查启动是否成功
            if not process.waitForStarted(3000):  # 等待3秒
                logger.error(f"❌ 进程启动失败: {task.title}")
                self._cleanup_process(process)
                return False
            
            logger.info(f"✅ 进程启动成功: {task.title}")
            self.process_started.emit(task.id)
            return True
            
        except Exception as e:
            logger.error(f"❌ 启动任务进程异常: {e}")
            return False
    
    def _create_process(self, task: PublishTask, cmd: List[str]) -> Optional[QProcess]:
        """创建并配置进程"""
        try:
            process = QProcess(self)
            
            # 设置进程通道模式
            process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
            
            # 设置工作目录
            process.setWorkingDirectory(str(Path(__file__).parent.parent))
            
            # 连接信号
            process.finished.connect(lambda exit_code, exit_status: 
                                   self._on_process_finished(process, task.id, exit_code))
            process.errorOccurred.connect(lambda error: 
                                        self._on_process_error(process, task.id, error))
            
            # 创建超时定时器
            timeout_timer = QTimer(self)
            timeout_timer.setSingleShot(True)
            timeout_timer.timeout.connect(lambda: self._kill_process(process, task.id, "超时"))
            timeout_timer.start(300000)  # 5分钟超时
            
            # 存储进程信息
            self.active_processes[task.id] = process
            self.process_data[process] = {
                'task': task,
                'timeout_timer': timeout_timer,
                'start_time': datetime.now(),
                'cmd': cmd
            }
            
            return process
            
        except Exception as e:
            logger.error(f"❌ 创建进程失败: {e}")
            return None
    
    def _on_process_finished(self, process: QProcess, task_id: str, exit_code: int):
        """处理进程完成"""
        try:
            process_info = self.process_data.get(process)
            if not process_info:
                logger.warning(f"⚠️ 找不到进程信息: {task_id}")
                return
            
            task = process_info['task']
            
            logger.info(f"📊 进程完成: {task.title}, 退出码: {exit_code}")
            
            if exit_code == 0:
                # 成功完成，解析结果
                try:
                    output = process.readAllStandardOutput().data().decode('utf-8')
                    
                    # 尝试从输出中提取JSON结果
                    result = self._extract_json_result(output)
                    
                    logger.info(f"✅ 任务执行成功: {task.title}")
                    self.process_finished.emit(task_id, result)
                    
                except json.JSONDecodeError as e:
                    logger.error(f"❌ 解析进程输出失败: {e}, 输出: {output[:200]}...")
                    self.process_failed.emit(task_id, f"解析结果失败: {str(e)}")
                    
                except Exception as e:
                    logger.error(f"❌ 处理进程结果异常: {e}")
                    self.process_failed.emit(task_id, f"处理结果异常: {str(e)}")
            else:
                # 进程异常退出
                error_output = process.readAllStandardError().data().decode('utf-8')
                standard_output = process.readAllStandardOutput().data().decode('utf-8')
                
                error_msg = error_output or standard_output or f"进程异常退出，退出码: {exit_code}"
                logger.error(f"❌ 进程异常退出: {task.title}, 错误: {error_msg}")
                
                self.process_failed.emit(task_id, error_msg)
            
            # 清理进程
            self._cleanup_process(process)
            
            # 处理等待队列
            self._process_pending_tasks()
            
        except Exception as e:
            logger.error(f"❌ 处理进程完成异常: {e}")
            self._cleanup_process(process)
    
    def _on_process_error(self, process: QProcess, task_id: str, error: QProcess.ProcessError):
        """处理进程错误"""
        try:
            process_info = self.process_data.get(process)
            task_title = process_info['task'].title if process_info else "未知任务"
            
            error_messages = {
                QProcess.ProcessError.FailedToStart: "进程启动失败",
                QProcess.ProcessError.Crashed: "进程崩溃",
                QProcess.ProcessError.Timedout: "进程超时",
                QProcess.ProcessError.WriteError: "进程写入错误",
                QProcess.ProcessError.ReadError: "进程读取错误",
                QProcess.ProcessError.UnknownError: "未知进程错误"
            }
            
            error_msg = error_messages.get(error, f"进程错误: {error}")
            logger.error(f"❌ 进程错误: {task_title}, {error_msg}")
            
            self.process_failed.emit(task_id, error_msg)
            
            # 清理进程
            self._cleanup_process(process)
            
            # 处理等待队列
            self._process_pending_tasks()
            
        except Exception as e:
            logger.error(f"❌ 处理进程错误异常: {e}")
    
    def _kill_process(self, process: QProcess, task_id: str, reason: str):
        """强制终止进程"""
        try:
            process_info = self.process_data.get(process)
            task_title = process_info['task'].title if process_info else "未知任务"
            
            logger.warning(f"💀 强制终止进程: {task_title}, 原因: {reason}")
            
            if process.state() != QProcess.ProcessState.NotRunning:
                # 先尝试温和终止
                process.terminate()
                
                # 等待2秒
                if not process.waitForFinished(2000):
                    # 强制杀死
                    process.kill()
                    process.waitForFinished(1000)
            
            self.process_failed.emit(task_id, f"进程被终止: {reason}")
            
            # 清理进程
            self._cleanup_process(process)
            
        except Exception as e:
            logger.error(f"❌ 终止进程异常: {e}")
    
    def _cleanup_process(self, process: QProcess):
        """清理进程资源"""
        try:
            # 获取进程信息
            process_info = self.process_data.get(process)
            if process_info:
                # 停止超时定时器
                timeout_timer = process_info.get('timeout_timer')
                if timeout_timer and timeout_timer.isActive():
                    timeout_timer.stop()
                
                # 从活动进程中移除
                task_id = process_info['task'].id
                if task_id in self.active_processes:
                    del self.active_processes[task_id]
                
                # 从进程数据中移除
                if process in self.process_data:
                    del self.process_data[process]
            
            # 清理进程对象
            if process.state() != QProcess.ProcessState.NotRunning:
                process.kill()
                process.waitForFinished(1000)
            
            process.deleteLater()
            
        except Exception as e:
            logger.error(f"❌ 清理进程资源异常: {e}")
    
    def _process_pending_tasks(self):
        """处理等待队列中的任务"""
        try:
            while self.pending_tasks and self.can_start_new_process():
                task, cmd = self.pending_tasks.pop(0)
                logger.info(f"📋 从等待队列启动任务: {task.title}")
                
                if not self.start_task(task, cmd):
                    logger.error(f"❌ 从等待队列启动任务失败: {task.title}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ 处理等待队列异常: {e}")
    
    def cleanup_finished_processes(self):
        """定期清理已完成的进程"""
        try:
            finished_processes = []
            
            for process in list(self.process_data.keys()):
                if process.state() == QProcess.ProcessState.NotRunning:
                    finished_processes.append(process)
            
            for process in finished_processes:
                logger.debug("🧹 清理已完成的进程")
                self._cleanup_process(process)
                
        except Exception as e:
            logger.error(f"❌ 定期清理进程异常: {e}")
    
    def kill_all_processes(self):
        """终止所有进程"""
        try:
            logger.info("🛑 终止所有进程...")
            
            for process in list(self.process_data.keys()):
                process_info = self.process_data[process]
                task_title = process_info['task'].title
                logger.info(f"🛑 终止进程: {task_title}")
                
                self._kill_process(process, process_info['task'].id, "应用退出")
            
            # 清空等待队列
            self.pending_tasks.clear()
            
            logger.info("✅ 所有进程已终止")
            
        except Exception as e:
            logger.error(f"❌ 终止所有进程异常: {e}")
    
    def _extract_json_result(self, output: str) -> dict:
        """从进程输出中提取JSON结果"""
        if not output.strip():
            return {"success": True, "message": "执行完成"}
        
        # 尝试直接解析整个输出
        try:
            return json.loads(output.strip())
        except json.JSONDecodeError:
            pass
        
        # 尝试从输出中找到JSON部分
        # 查找以 { 开始，} 结束的JSON字符串
        lines = output.strip().split('\n')
        
        # 查找最后一行是否为JSON
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        
        # 尝试查找连续的JSON块
        json_lines = []
        in_json = False
        brace_count = 0
        
        for line in lines:
            line = line.strip()
            if line.startswith('{'):
                in_json = True
                json_lines = [line]
                brace_count = line.count('{') - line.count('}')
            elif in_json:
                json_lines.append(line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    # JSON块结束
                    try:
                        json_str = '\n'.join(json_lines)
                        return json.loads(json_str)
                    except json.JSONDecodeError:
                        pass
                    in_json = False
                    json_lines = []
        
        # 如果都失败了，根据输出内容推断结果
        output_lower = output.lower()
        if any(keyword in output_lower for keyword in ['success": true', '发布成功', 'published']):
            return {"success": True, "message": "发布成功"}
        elif any(keyword in output_lower for keyword in ['success": false', '发布失败', 'failed']):
            return {"success": False, "message": "发布失败"}
        else:
            return {"success": True, "message": "执行完成（从输出推断）"}
    
    def get_process_status(self) -> Dict:
        """获取进程池状态"""
        try:
            running_tasks = []
            for process_info in self.process_data.values():
                task = process_info['task']
                running_time = (datetime.now() - process_info['start_time']).total_seconds()
                running_tasks.append({
                    'task_id': task.id,
                    'title': task.title,
                    'running_time': running_time
                })
            
            return {
                'active_count': len(self.active_processes),
                'max_processes': self.max_processes,
                'pending_count': len(self.pending_tasks),
                'running_tasks': running_tasks
            }
            
        except Exception as e:
            logger.error(f"❌ 获取进程状态异常: {e}")
            return {
                'active_count': 0,
                'max_processes': self.max_processes,
                'pending_count': 0,
                'running_tasks': []
            }
"""
操作防护装饰器和工具
防止重复操作、提供用户友好的错误处理
"""
import functools
import time
from typing import Set, Dict, Any, Callable
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtCore import QTimer, QObject
from loguru import logger


class OperationGuard:
    """操作防护管理器"""
    
    def __init__(self):
        self.active_operations: Set[str] = set()
        self.operation_timers: Dict[str, QTimer] = {}
        self.operation_start_times: Dict[str, float] = {}
    
    def is_operation_active(self, operation_id: str) -> bool:
        """检查操作是否正在进行"""
        return operation_id in self.active_operations
    
    def start_operation(self, operation_id: str, timeout_seconds: int = 30) -> bool:
        """开始操作，返回是否成功获取锁"""
        if operation_id in self.active_operations:
            return False
        
        self.active_operations.add(operation_id)
        self.operation_start_times[operation_id] = time.time()
        
        # 设置超时自动清理
        if timeout_seconds > 0:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(lambda: self._timeout_cleanup(operation_id))
            timer.start(timeout_seconds * 1000)
            self.operation_timers[operation_id] = timer
        
        logger.debug(f"🔒 操作开始: {operation_id}")
        return True
    
    def end_operation(self, operation_id: str):
        """结束操作"""
        if operation_id in self.active_operations:
            self.active_operations.discard(operation_id)
            
            # 清理定时器
            if operation_id in self.operation_timers:
                timer = self.operation_timers[operation_id]
                if timer.isActive():
                    timer.stop()
                timer.deleteLater()
                del self.operation_timers[operation_id]
            
            # 记录操作时间
            if operation_id in self.operation_start_times:
                duration = time.time() - self.operation_start_times[operation_id]
                logger.debug(f"🔓 操作完成: {operation_id} (耗时: {duration:.2f}s)")
                del self.operation_start_times[operation_id]
    
    def _timeout_cleanup(self, operation_id: str):
        """超时清理"""
        if operation_id in self.active_operations:
            logger.warning(f"⏰ 操作超时自动清理: {operation_id}")
            self.end_operation(operation_id)
    
    def get_active_operations(self) -> Set[str]:
        """获取当前活跃的操作"""
        return self.active_operations.copy()
    
    def clear_all_operations(self):
        """清理所有操作（应用退出时调用）"""
        operations_to_clear = list(self.active_operations)
        for operation_id in operations_to_clear:
            self.end_operation(operation_id)
        logger.info("🧹 已清理所有操作锁")


# 全局操作防护实例
_global_guard = OperationGuard()


def operation_guard(operation_id: str, timeout_seconds: int = 30, 
                   show_warning: bool = True, warning_message: str = None):
    """
    操作防护装饰器
    
    Args:
        operation_id: 操作标识符
        timeout_seconds: 超时时间（秒）
        show_warning: 是否显示警告对话框
        warning_message: 自定义警告消息
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # 检查是否已在执行
            if _global_guard.is_operation_active(operation_id):
                message = warning_message or f"操作'{operation_id}'正在进行中，请稍候..."
                
                if show_warning and hasattr(self, 'parent') and self.parent():
                    QMessageBox.warning(self.parent(), "操作进行中", message)
                elif show_warning and hasattr(self, 'window') and callable(self.window):
                    QMessageBox.warning(self.window(), "操作进行中", message)
                
                logger.warning(f"⚠️ 重复操作被阻止: {operation_id}")
                return None
            
            # 开始操作
            if not _global_guard.start_operation(operation_id, timeout_seconds):
                return None
            
            try:
                result = func(self, *args, **kwargs)
                return result
            except Exception as e:
                logger.error(f"❌ 操作执行异常 {operation_id}: {e}")
                raise
            finally:
                # 确保操作锁被释放
                _global_guard.end_operation(operation_id)
        
        return wrapper
    return decorator


def with_operation_lock(operation_id: str, timeout_seconds: int = 30):
    """
    上下文管理器方式的操作锁
    
    用法:
    with with_operation_lock("my_operation"):
        # 执行需要保护的操作
        pass
    """
    class OperationLock:
        def __init__(self, op_id: str, timeout: int):
            self.operation_id = op_id
            self.timeout = timeout
            self.acquired = False
        
        def __enter__(self):
            self.acquired = _global_guard.start_operation(self.operation_id, self.timeout)
            if not self.acquired:
                raise RuntimeError(f"无法获取操作锁: {self.operation_id}")
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.acquired:
                _global_guard.end_operation(self.operation_id)
    
    return OperationLock(operation_id, timeout_seconds)


class SafeExecutor:
    """安全执行器，提供统一的异常处理"""
    
    @staticmethod
    def execute_safely(func: Callable, 
                      fallback_result: Any = None,
                      error_message: str = "操作失败",
                      show_error: bool = True,
                      parent_widget: QObject = None) -> Any:
        """
        安全执行函数，统一异常处理
        
        Args:
            func: 要执行的函数
            fallback_result: 失败时的默认返回值
            error_message: 错误消息前缀
            show_error: 是否显示错误对话框
            parent_widget: 父组件（用于显示对话框）
        
        Returns:
            函数执行结果或fallback_result
        """
        try:
            return func()
        except FileNotFoundError as e:
            message = f"文件未找到: {e}"
            logger.error(f"❌ {error_message} - {message}")
            if show_error and parent_widget:
                QMessageBox.critical(parent_widget, "文件错误", message)
            return fallback_result
        except PermissionError as e:
            message = f"权限不足: {e}"
            logger.error(f"❌ {error_message} - {message}")
            if show_error and parent_widget:
                QMessageBox.critical(parent_widget, "权限错误", 
                                   f"{message}\n\n请尝试以管理员身份运行程序")
            return fallback_result
        except OSError as e:
            message = f"系统错误: {e}"
            logger.error(f"❌ {error_message} - {message}")
            if show_error and parent_widget:
                QMessageBox.critical(parent_widget, "系统错误", message)
            return fallback_result
        except ValueError as e:
            message = f"数据格式错误: {e}"
            logger.error(f"❌ {error_message} - {message}")
            if show_error and parent_widget:
                QMessageBox.warning(parent_widget, "数据错误", message)
            return fallback_result
        except Exception as e:
            message = f"未知错误: {e}"
            logger.error(f"❌ {error_message} - {message}")
            if show_error and parent_widget:
                QMessageBox.critical(parent_widget, "错误", f"{error_message}\n\n{message}")
            return fallback_result


def safe_method(fallback_result: Any = None, 
               error_message: str = "操作失败",
               show_error: bool = True):
    """
    安全方法装饰器
    
    用法:
    @safe_method(fallback_result=False, error_message="保存失败")
    def save_data(self):
        # 可能抛出异常的代码
        pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            parent_widget = None
            
            # 尝试获取父组件
            if hasattr(self, 'parent') and callable(self.parent):
                parent_widget = self.parent()
            elif hasattr(self, 'window') and callable(self.window):
                parent_widget = self.window()
            elif hasattr(self, 'parentWidget') and callable(self.parentWidget):
                parent_widget = self.parentWidget()
            
            return SafeExecutor.execute_safely(
                lambda: func(self, *args, **kwargs),
                fallback_result=fallback_result,
                error_message=error_message,
                show_error=show_error,
                parent_widget=parent_widget
            )
        
        return wrapper
    return decorator


def cleanup_on_exit():
    """应用退出时的清理函数"""
    _global_guard.clear_all_operations()
    logger.info("🧹 应用退出清理完成")


# 导出的公共接口
__all__ = [
    'operation_guard',
    'with_operation_lock', 
    'safe_method',
    'SafeExecutor',
    'cleanup_on_exit',
    'OperationGuard'
]
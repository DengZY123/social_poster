"""
统一的浏览器Profile管理
确保账号登录和任务发布使用相同的profile目录
"""
from pathlib import Path
from loguru import logger


def get_account_profile_dir(account_name: str = "默认账号") -> str:
    """
    获取账号专用的profile目录
    
    Args:
        account_name: 账号名称，默认为"默认账号"
        
    Returns:
        profile目录路径
    """
    # 检查是否为打包环境
    try:
        from packaging.scripts.path_detector import path_detector
        base_dir = path_detector.get_user_data_dir()
        profile_dir = base_dir / account_name
    except ImportError:
        # 开发环境 - 使用项目下的firefox_profile目录
        profile_dir = Path(f"firefox_profile/{account_name}")
    
    # 确保目录存在
    profile_dir = Path(profile_dir)
    if not profile_dir.exists():
        logger.info(f"📁 创建账号profile目录: {profile_dir}")
        profile_dir.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"📁 使用已存在的账号profile目录: {profile_dir}")
    
    return str(profile_dir)


def get_current_account_name() -> str:
    """
    获取当前选中的账号名称
    
    Returns:
        账号名称，默认返回"默认账号"
    """
    # TODO: 从账号管理模块获取当前选中的账号
    # 暂时返回默认账号
    return "默认账号"
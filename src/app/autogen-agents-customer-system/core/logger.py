"""
日志记录模块
提供统一的日志配置和管理功能
"""
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from config.settings import settings


class UTF8FileHandler(RotatingFileHandler):
    """强制使用UTF-8编码的文件处理器"""
    
    def __init__(self, *args, **kwargs):
        kwargs['encoding'] = 'utf-8'
        super().__init__(*args, **kwargs)


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        
    Returns:
        配置好的日志记录器
    """
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 创建日志目录
    log_dir = os.path.dirname(settings.LOG_FILE)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 文件处理器 - 强制使用UTF-8编码
    file_handler = UTF8FileHandler(
        settings.LOG_FILE,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    
    # 控制台处理器 - 使用UTF-8编码
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if settings.LOG_LEVEL == "DEBUG" else logging.INFO)
    
    # 在Windows系统中设置控制台编码
    if sys.platform.startswith('win'):
        try:
            # 尝试设置控制台编码为UTF-8
            if hasattr(sys.stdout, 'reconfigure'):
                sys.stdout.reconfigure(encoding='utf-8')
            if hasattr(sys.stderr, 'reconfigure'):
                sys.stderr.reconfigure(encoding='utf-8')
        except Exception:
            pass  # 如果设置失败，继续使用默认编码
    
    # 格式化器
    formatter = logging.Formatter(settings.LOG_FORMAT)
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # 添加处理器
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# 默认日志记录器
default_logger = setup_logger("multi_agent_system")
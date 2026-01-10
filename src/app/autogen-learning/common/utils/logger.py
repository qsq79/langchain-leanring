"""日志工具

提供统一的日志配置和工具函数。
"""

import logging
import sys
from typing import Optional
from common.config.constants import LogLevel, LogFormat


def setup_logging(level: str = "INFO", format_type: str = "console") -> None:
    """配置日志系统

    Args:
        level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: 日志格式 (console, json)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)

    # 创建根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # 清除现有 handlers
    root_logger.handlers.clear()

    # 创建 handler
    if format_type == LogFormat.JSON.value:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )

    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """获取 logger 实例

    Args:
        name: logger 名称

    Returns:
        logging.Logger 实例
    """
    return logging.getLogger(name)


class JsonFormatter(logging.Formatter):
    """JSON 格式的日志格式化器"""

    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为 JSON"""
        import json

        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)

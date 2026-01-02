#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统模块
基于 Loguru 的结构化日志
"""

import sys
import os
from pathlib import Path
from loguru import logger

from src.config.settings import settings


def setup_logger():
    """配置日志系统"""

    # 移除默认的处理器
    logger.remove()

    # 1. 控制台输出（带颜色）
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.LOG_LEVEL,
        colorize=True
    )

    # 2. 日志文件（按天轮转）
    log_dir = Path(settings.LOG_DIR)
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "app_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )

    # 3. 错误日志单独记录
    logger.add(
        log_dir / "error_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="1 day",
        retention="90 days",
        compression="zip",
        encoding="utf-8"
    )

    logger.info(f"日志系统初始化完成 - 日志级别: {settings.LOG_LEVEL}")


def get_logger(name: str = None):
    """获取 logger 实例"""
    if name:
        return logger.bind(name=name)
    return logger


# 自动初始化
setup_logger()


if __name__ == "__main__":
    # 测试日志
    logger.debug("这是调试信息")
    logger.info("这是普通信息")
    logger.warning("这是警告信息")
    logger.error("这是错误信息")
    logger.critical("这是严重错误")

    # 带上下文的日志
    logger.info("用户请求", extra={"user_id": 123, "query": "测试"})
    logger.error("API调用失败", extra={"api": "openai", "error": "Connection timeout"})

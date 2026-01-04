#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统模块
基于 Loguru 的结构化日志
"""

import sys
from pathlib import Path
from loguru import logger

from config.settings import settings


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

    # 4. 智能体交互日志
    logger.add(
        log_dir / "agent_interaction_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="1 day",
        retention="30 days",
        compression="zip",
        encoding="utf-8",
        filter=lambda record: "agent" in record["name"].lower() or "interaction" in record["extra"].get("type", "")
    )

    logger.info(f"日志系统初始化完成 - 日志级别: {settings.LOG_LEVEL}")


def get_logger(name: str = None):
    """获取 logger 实例"""
    if name:
        return logger.bind(name=name)
    return logger


def log_agent_message(from_agent: str, to_agent: str, message_type: str, content: str):
    """记录智能体之间的消息传递"""
    logger.info(
        f"[{message_type}] {from_agent} -> {to_agent}: {content}",
        extra={"type": "interaction", "from": from_agent, "to": to_agent, "message_type": message_type}
    )


def log_agent_action(agent_name: str, action: str, details: str = ""):
    """记录智能体的动作"""
    if details:
        logger.info(f"[{agent_name}] {action}: {details}", extra={"type": "interaction", "agent": agent_name})
    else:
        logger.info(f"[{agent_name}] {action}", extra={"type": "interaction", "agent": agent_name})


# 自动初始化
setup_logger()
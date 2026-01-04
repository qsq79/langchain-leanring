#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重试机制模块
实现指数级退避策略的API调用重试
"""

import time
import asyncio
from typing import Callable, TypeVar, Any
from functools import wraps

from core.logger import get_logger
from config.settings import settings

logger = get_logger(__name__)

T = TypeVar('T')


class RetryMechanism:
    """重试机制类"""

    def __init__(
        self,
        initial_delay: float = None,
        max_delay: float = None,
        multiplier: float = None,
        max_attempts: int = None
    ):
        """
        初始化重试机制

        Args:
            initial_delay: 初始延迟时间（秒）
            max_delay: 最大延迟时间（秒）
            multiplier: 退避因子
            max_attempts: 最大重试次数
        """
        retry_config = settings.get_retry_config()
        self.initial_delay = initial_delay or retry_config["initial_delay"]
        self.max_delay = max_delay or retry_config["max_delay"]
        self.multiplier = multiplier or retry_config["multiplier"]
        self.max_attempts = max_attempts or retry_config["max_attempts"]

        logger.info(
            f"重试机制初始化 - 初始延迟: {self.initial_delay}s, "
            f"最大延迟: {self.max_delay}s, 退避因子: {self.multiplier}, "
            f"最大重试: {self.max_attempts}次"
        )

    def calculate_delay(self, attempt: int) -> float:
        """
        计算第 n 次重试的延迟时间

        Args:
            attempt: 重试次数（从1开始）

        Returns:
            延迟时间（秒）
        """
        delay = min(
            self.initial_delay * (self.multiplier ** (attempt - 1)),
            self.max_delay
        )
        logger.debug(f"第 {attempt} 次重试延迟: {delay:.2f}秒")
        return delay

    def should_retry(self, exception: Exception) -> bool:
        """
        判断是否应该重试

        Args:
            exception: 异常对象

        Returns:
            是否应该重试
        """
        retryable_errors = (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )

        non_retryable_errors = (
            ValueError,
            KeyError,
            LookupError,
        )

        if isinstance(exception, retryable_errors):
            logger.warning(f"可重试错误: {type(exception).__name__} - {str(exception)}")
            return True

        if isinstance(exception, non_retryable_errors):
            logger.error(f"不可重试错误: {type(exception).__name__} - {str(exception)}")
            return False

        logger.warning(f"未知错误类型: {type(exception).__name__}，尝试重试")
        return True

    async def async_execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        异步执行函数，带有重试机制

        Args:
            func: 要执行的异步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 重试失败后抛出最后的异常
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"尝试执行函数 {func.__name__} (第 {attempt}/{self.max_attempts} 次)")
                result = await func(*args, **kwargs)
                logger.info(f"函数 {func.__name__} 执行成功")
                return result

            except Exception as e:
                last_exception = e
                logger.error(
                    f"函数 {func.__name__} 执行失败 (第 {attempt}/{self.max_attempts} 次): {e}"
                )

                if not self.should_retry(e):
                    logger.error(f"错误不可重试，直接抛出异常")
                    raise

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.info(f"等待 {delay:.2f} 秒后重试...")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"已达到最大重试次数 {self.max_attempts}，放弃重试")

        raise last_exception

    def sync_execute_with_retry(
        self,
        func: Callable[..., Any],
        *args,
        **kwargs
    ) -> Any:
        """
        同步执行函数，带有重试机制

        Args:
            func: 要执行的同步函数
            *args: 位置参数
            **kwargs: 关键字参数

        Returns:
            函数执行结果

        Raises:
            Exception: 重试失败后抛出最后的异常
        """
        last_exception = None

        for attempt in range(1, self.max_attempts + 1):
            try:
                logger.info(f"尝试执行函数 {func.__name__} (第 {attempt}/{self.max_attempts} 次)")
                result = func(*args, **kwargs)
                logger.info(f"函数 {func.__name__} 执行成功")
                return result

            except Exception as e:
                last_exception = e
                logger.error(
                    f"函数 {func.__name__} 执行失败 (第 {attempt}/{self.max_attempts} 次): {e}"
                )

                if not self.should_retry(e):
                    logger.error(f"错误不可重试，直接抛出异常")
                    raise

                if attempt < self.max_attempts:
                    delay = self.calculate_delay(attempt)
                    logger.info(f"等待 {delay:.2f} 秒后重试...")
                    time.sleep(delay)
                else:
                    logger.error(f"已达到最大重试次数 {self.max_attempts}，放弃重试")

        raise last_exception


# 全局重试机制实例
global_retry_mechanism = RetryMechanism()
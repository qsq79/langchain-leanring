#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
基于 Pydantic Settings 的类型安全配置
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal
from pydantic import Field


class Settings(BaseSettings):
    """应用配置类"""

    # ========== 模型配置 ==========
    MODEL_NAME: Literal["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"] = "gpt-4"
    MODEL_TEMPERATURE: float = 0.7
    MODEL_MAX_TOKENS: int = 2000

    # ========== API 密钥 ==========
    OPENAI_API_KEY: str = Field(..., description="OpenAI API 密钥")
    OPENAI_API_BASE: str = "https://api.openai.com/v1"

    # ========== API 服务配置 ==========
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8001

    # ========== 服务接口配置 ==========
    ORDER_API_BASE_URL: str = "http://localhost:8001/api/v1"
    LOGISTICS_API_BASE_URL: str = "http://localhost:8001/api/v1"

    # ========== 重试机制配置 ==========
    RETRY_INITIAL_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 10.0
    RETRY_MULTIPLIER: float = 2.0
    RETRY_MAX_ATTEMPTS: int = 3

    # ========== 日志配置 ==========
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_DIR: str = "logs"

    # ========== 应用配置 ==========
    APP_NAME: str = "Multi-Agent Customer Service System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ========== 可视化配置 ==========
    VISUALIZE_AGENT_INTERACTION: bool = True
    SHOW_API_LOGS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def get_openai_config(self) -> dict:
        """获取 OpenAI 配置字典"""
        return {
            "api_key": self.OPENAI_API_KEY,
            "base_url": self.OPENAI_API_BASE,
            "temperature": self.MODEL_TEMPERATURE,
            "max_tokens": self.MODEL_MAX_TOKENS
        }

    def get_retry_config(self) -> dict:
        """获取重试机制配置字典"""
        return {
            "initial_delay": self.RETRY_INITIAL_DELAY,
            "max_delay": self.RETRY_MAX_DELAY,
            "multiplier": self.RETRY_MULTIPLIER,
            "max_attempts": self.RETRY_MAX_ATTEMPTS
        }


# 创建全局配置实例
settings = Settings()


if __name__ == "__main__":
    # 测试配置加载
    print("=" * 60)
    print("配置信息")
    print("=" * 60)
    print(f"应用名称: {settings.APP_NAME}")
    print(f"版本: {settings.APP_VERSION}")
    print(f"模型: {settings.MODEL_NAME}")
    print(f"调试模式: {settings.DEBUG}")
    print(f"日志级别: {settings.LOG_LEVEL}")
    print(f"API端口: {settings.API_PORT}")
    print(f"重试次数: {settings.RETRY_MAX_ATTEMPTS}")
    print("=" * 60)
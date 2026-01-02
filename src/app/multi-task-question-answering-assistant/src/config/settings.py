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

    TAVILY_API_KEY: str = Field(default="", description="Tavily 搜索 API 密钥")
    AMAP_API_KEY: str = Field(default="", description="高德地图 API 密钥")

    # ========== Redis 配置 ==========
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # ========== 日志配置 ==========
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    LOG_DIR: str = "logs"

    # ========== 应用配置 ==========
    APP_NAME: str = "Multi-Task QA Assistant"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ========== 动态模型选择配置 ==========
    ENABLE_DYNAMIC_ROUTING: bool = True
    COST_OPTIMIZATION_ENABLED: bool = True
    PERFORMANCE_MODE: Literal["cost", "balanced", "performance"] = "balanced"

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

    def get_redis_config(self) -> dict:
        """获取 Redis 配置字典"""
        config = {
            "host": self.REDIS_HOST,
            "port": self.REDIS_PORT,
            "db": self.REDIS_DB
        }
        if self.REDIS_PASSWORD:
            config["password"] = self.REDIS_PASSWORD
        return config


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
    print(f"动态路由: {settings.ENABLE_DYNAMIC_ROUTING}")
    print("=" * 60)

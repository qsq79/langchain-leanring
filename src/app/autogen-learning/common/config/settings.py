"""配置管理

使用 pydantic-settings 管理应用配置。
"""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# 加载环境变量
load_dotenv()


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ===== OpenAI 配置 =====
    openai_api_key: str = Field(default="", description="OpenAI API Key")
    openai_api_base: Optional[str] = Field(
        default="https://api.openai.com/v1", description="OpenAI API Base URL"
    )
    openai_model: str = Field(default="gpt-4o", description="默认使用的模型")

    # ===== Azure OpenAI 配置 =====
    azure_openai_api_key: Optional[str] = Field(default="", description="Azure OpenAI API Key")
    azure_openai_endpoint: Optional[str] = Field(default="", description="Azure OpenAI Endpoint")
    azure_openai_api_version: str = Field(default="2024-02-15-preview", description="Azure OpenAI API Version")
    azure_openai_deployment: str = Field(default="gpt-4", description="Azure OpenAI Deployment Name")

    # ===== Anthropic 配置 =====
    anthropic_api_key: Optional[str] = Field(default="", description="Anthropic API Key")

    # ===== 日志配置 =====
    log_level: str = Field(default="INFO", description="日志级别")
    log_format: str = Field(default="console", description="日志格式 (console/json)")

    # ===== 代码执行配置 =====
    docker_enabled: bool = Field(default=False, description="是否启用 Docker")
    code_execution_timeout: int = Field(default=300, description="代码执行超时时间（秒）")

    # ===== 应用配置 =====
    app_name: str = Field(default="AutoGen Learning", description="应用名称")
    debug: bool = Field(default=False, description="调试模式")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 清理 API key 中的非 ASCII 字符
        self.openai_api_key = self._clean_api_key(self.openai_api_key)
        if self.azure_openai_api_key:
            self.azure_openai_api_key = self._clean_api_key(self.azure_openai_api_key)
        if self.anthropic_api_key:
            self.anthropic_api_key = self._clean_api_key(self.anthropic_api_key)
        self._validate()

    def _clean_api_key(self, api_key: str) -> str:
        """清理 API key 中的非 ASCII 字符和引号"""
        if not api_key:
            return api_key
        # 移除所有非 ASCII 字符（只保留可打印的 ASCII 字符）
        cleaned = ''.join(char for char in api_key if ord(char) < 128)
        # 移除可能的引号
        cleaned = cleaned.strip('"').strip("'").strip('`')
        return cleaned

    def _validate(self) -> None:
        """验证配置"""
        # 验证至少有一个 LLM 配置
        if not any([self.openai_api_key, self.azure_openai_api_key, self.anthropic_api_key]):
            print(
                "⚠️  警告: 未配置任何 LLM API Key"
                "\n   请在 .env 文件中配置 OPENAI_API_KEY 或其他 API Key"
            )

    @property
    def has_openai(self) -> bool:
        """是否配置了 OpenAI"""
        return bool(self.openai_api_key)

    @property
    def has_azure_openai(self) -> bool:
        """是否配置了 Azure OpenAI"""
        return bool(self.azure_openai_api_key and self.azure_openai_endpoint)

    @property
    def has_anthropic(self) -> bool:
        """是否配置了 Anthropic"""
        return bool(self.anthropic_api_key)


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reload_settings() -> Settings:
    """重新加载配置"""
    global _settings
    _settings = Settings()
    return _settings

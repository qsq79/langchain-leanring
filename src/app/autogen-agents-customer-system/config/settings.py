"""
多智能体客服系统 - 命令行工具配置
专注于CLI应用需求，移除Web相关配置
"""
import os
from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """CLI应用配置类"""
    
    # OpenAI配置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o"
    
    # 重试配置 - 增强CLI体验
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 1.0
    TIMEOUT: int = 30
    BACKOFF_FACTOR: float = 2.0  # 指数退避因子
    EXPONENTIAL_BACKOFF: bool = True  # 启用指数退避
    
    # 日志配置 - 针对CLI优化
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/app.log"
    LOG_TO_CONSOLE: bool = True  # 是否输出到控制台
    LOG_TO_FILE: bool = True  # 是否输出到文件
    
    # 模拟服务配置
    MOCK_SERVER_HOST: str = "127.0.0.1"
    MOCK_SERVER_PORT: int = 8001  # 避免与常见Web服务冲突
    MOCK_ORDER_DELAY: float = 0.5  # 模拟订单查询延迟
    MOCK_LOGISTICS_DELAY: float = 0.8  # 模拟物流查询延迟
    MOCK_ERROR_RATE: float = 0.1  # 模拟错误率
    
    # 智能体配置
    AGENT_MEMORY_ENABLED: bool = True  # 启用智能体记忆
    AGENT_VERBOSE: bool = True  # 显示详细智能体交互
    AGENT_MAX_ITERATIONS: int = 10  # 最大迭代次数
    
    # CLI界面配置
    CLI_THEME: str = "dark"  # 界面主题
    CLI_SHOW_PROGRESS: bool = True  # 显示进度条
    CLI_SHOW_STATUS: bool = True  # 显示状态信息
    
    # 文件路径配置
    DATA_DIR: str = "data"  # 数据目录
    OUTPUT_DIR: str = "output"  # 输出目录
    
    # AutoGen配置
    AUTOGEN_API_KEY: Optional[str] = None  # AutoGen API密钥
    AUTOGEN_MODEL: str = "gpt-4o"  # AutoGen使用的模型
    AUTOGEN_BASE_URL: str = "https://api.vveai.com/v1"  # API基础URL
    AUTOGEN_TEMPERATURE: float = 0.7  # 温度参数
    AUTOGEN_TIMEOUT: int = 60  # 超时时间
    AUTOGEN_MAX_ROUNDS: int = 12  # 最大对话轮数
    AUTOGEN_HUMAN_INPUT_MODE: str = "NEVER"  # 人工输入模式
    AUTOGEN_MAX_CONSECUTIVE_AUTO_REPLY: int = 10  # 最大连续自动回复数
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


# 全局配置实例
settings = Settings()

# 确保必要的目录存在
def ensure_directories():
    """确保必要的目录存在"""
    dirs = [
        Path(settings.DATA_DIR),
        Path(settings.OUTPUT_DIR),
        Path("logs"),
        Path("temp")
    ]
    
    for dir_path in dirs:
        dir_path.mkdir(parents=True, exist_ok=True)

# 初始化目录
ensure_directories()
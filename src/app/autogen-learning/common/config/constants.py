"""常量定义

定义项目中使用的常量。
"""

from enum import Enum


class LogLevel(str, Enum):
    """日志级别"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogFormat(str, Enum):
    """日志格式"""

    CONSOLE = "console"
    JSON = "json"


class AgentType(str, Enum):
    """Agent 类型"""

    ROUTED = "routed"
    ASSISTANT = "assistant"
    CODING = "coding"
    TEXT_CHAT = "text_chat"
    USER_PROXY = "user_proxy"


class MessageType(str, Enum):
    """消息类型"""

    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"


# 常用 Topic 类型
class TopicType(str, Enum):
    """Topic 类型"""

    # 基础 Topic
    DEFAULT = "default"
    NOTIFICATION = "notification"

    # 业务 Topic
    ORDER_CREATED = "order_created"
    ORDER_SHIPPED = "order_shipped"
    LOGISTICS_UPDATE = "logistics_update"
    PAYMENT_RECEIVED = "payment_received"

    # Agent Chat Topic
    CHAT_MESSAGE = "chat_message"
    TOOL_EXECUTION = "tool_execution"
    CODE_EXECUTION = "code_execution"


# Topic Source
class TopicSource(str, Enum):
    """Topic Source"""

    DEFAULT = "default"
    CLIENT_A = "client_a"
    CLIENT_B = "client_b"
    SYSTEM = "system"


# 默认值
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_TURNS = 10
DEFAULT_MODEL = "gpt-4o"
DEFAULT_TEMPERATURE = 0.7

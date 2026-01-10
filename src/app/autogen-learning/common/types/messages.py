"""消息类型定义

定义项目中使用的各种消息类型。
"""

from typing import Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TextMessage:
    """文本消息"""

    content: str
    sender: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AgentMessage:
    """Agent 消息基类"""

    sender: str
    receiver: str
    content: Any
    message_id: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.message_id is None:
            self.message_id = f"{self.sender}-{self.receiver}-{self.timestamp.timestamp()}"


@dataclass
class TaskMessage:
    """任务消息"""

    task_id: str
    task_type: str
    payload: dict
    sender: str
    priority: int = 0
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ResultMessage:
    """结果消息"""

    task_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class CommandMessage:
    """命令消息"""

    command: str
    args: dict
    sender: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class EventMessage:
    """事件消息"""

    event_type: str
    event_data: dict
    source: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

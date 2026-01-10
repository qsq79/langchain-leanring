"""Agent 相关类型定义

定义 Agent 配置、状态等类型。
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    """Agent 配置"""

    name: str
    description: str = ""
    agent_type: str = "routed"
    config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.description:
            self.description = f"Agent: {self.name}"


@dataclass
class AgentState:
    """Agent 状态"""

    agent_id: str
    is_active: bool = True
    message_count: int = 0
    last_activity: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MessageContext:
    """消息上下文"""

    topic_id: Optional[str] = None
    sender_id: Optional[str] = None
    message_id: Optional[str] = None
    is_reply: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

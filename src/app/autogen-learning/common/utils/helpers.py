"""辅助工具函数

提供常用的辅助函数。
"""

import os
from common.config import get_settings


def print_banner(title: str, width: int = 80) -> None:
    """打印横幅

    Args:
        title: 标题
        width: 宽度
    """
    print("\n" + "=" * width)
    print(f"{title:^{width}}")
    print("=" * width + "\n")


def print_section(title: str, width: int = 80) -> None:
    """打印分隔符和章节标题

    Args:
        title: 章节标题
        width: 宽度
    """
    print("\n" + "-" * width)
    print(f"{title}")
    print("-" * width + "\n")


def validate_env(required_vars: list[str]) -> bool:
    """验证环境变量

    Args:
        required_vars: 必需的环境变量列表

    Returns:
        bool: 是否所有必需的环境变量都已设置
    """
    settings = get_settings()
    missing_vars = []

    for var_name in required_vars:
        # 从环境变量或 settings 中获取
        env_value = os.getenv(var_name) or getattr(settings, var_name.lower(), None)

        if not env_value:
            missing_vars.append(var_name)

    if missing_vars:
        print("⚠️  缺少以下必需的环境变量:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n请在 .env 文件中配置这些变量。")
        return False

    return True


def print_agent_info(agent_name: str, agent_id: str = None, description: str = None) -> None:
    """打印 Agent 信息

    Args:
        agent_name: Agent 名称
        agent_id: Agent ID
        description: Agent 描述
    """
    print(f"\n📦 Agent: {agent_name}")
    if agent_id:
        print(f"   ID: {agent_id}")
    if description:
        print(f"   描述: {description}")
    print()


def print_message(agent_name: str, message: str, msg_type: str = "INFO") -> None:
    """打印消息

    Args:
        agent_name: Agent 名称
        message: 消息内容
        msg_type: 消息类型
    """
    icons = {"INFO": "💬", "SUCCESS": "✅", "WARNING": "⚠️", "ERROR": "❌", "DEBUG": "🔍"}
    icon = icons.get(msg_type, "📌")
    print(f"{icon} [{agent_name}] {message}")

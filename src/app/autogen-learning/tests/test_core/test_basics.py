"""Core API 基础测试

测试 AutoGen Core 的基础功能。
"""

import pytest
from autogen_core import RoutedAgent, AgentId, TopicId, TypeSubscription, message_handler


class SimpleAgent(RoutedAgent):
    """简单的测试 Agent"""

    def __init__(self, description: str = "Simple Test Agent"):
        super().__init__(description)
        self.received_messages = []

    @message_handler
    async def handle_text(self, message: str, ctx) -> None:
        """处理文本消息"""
        self.received_messages.append(message)


@pytest.mark.asyncio
async def test_agent_registration(runtime):
    """测试 Agent 注册"""
    # 注册 Agent
    await SimpleAgent.register(runtime, "simple", lambda: SimpleAgent())
    await runtime.add_subscription(TypeSubscription("test", "simple"))

    # 启动 Runtime
    runtime.start()

    # 发布消息
    await runtime.publish_message("Hello", TopicId("test", "default"))

    # 等待处理
    await runtime.stop_when_idle()

    # 验证消息已处理
    # 注意: 在实际测试中，我们需要一种方式来检查 Agent 的状态
    # 这里只是演示测试结构


@pytest.mark.asyncio
async def test_topic_subscription(runtime):
    """测试 Topic 订阅"""
    await SimpleAgent.register(runtime, "agent1", lambda: SimpleAgent())
    await SimpleAgent.register(runtime, "agent2", lambda: SimpleAgent())

    # 两个 Agent 订阅同一个 Topic
    await runtime.add_subscription(TypeSubscription("broadcast", "agent1"))
    await runtime.add_subscription(TypeSubscription("broadcast", "agent2"))

    runtime.start()

    # 发布消息到 broadcast topic
    await runtime.publish_message("Test Message", TopicId("broadcast", "default"))

    await runtime.stop_when_idle()


@pytest.mark.asyncio
async def test_multiple_messages(runtime):
    """测试多条消息处理"""
    await SimpleAgent.register(runtime, "processor", lambda: SimpleAgent())
    await runtime.add_subscription(TypeSubscription("messages", "processor"))

    runtime.start()

    # 发送多条消息
    messages = ["Message 1", "Message 2", "Message 3"]
    for msg in messages:
        await runtime.publish_message(msg, TopicId("messages", "default"))

    await runtime.stop_when_idle()

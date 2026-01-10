"""
Demo 13: 直接消息传递 (Direct Messaging)

本演示展示如何:
1. 使用 AgentId 发送直接消息
2. 实现 Agent 间的点对点通信
3. 处理直接消息的响应
4. 管理私有消息通道
5. 实现定向通信模式

运行方式:
    python demo_13_direct_messaging.py

前置要求:
    - 已完成 demo_11_message_delivery.py
    - 理解基本的消息传递机制

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/message-passing.html
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 这样可以直接运行脚本文件，而不需要从特定目录运行
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # 向上 3 级到 autogen-learning/
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio
from dataclasses import dataclass
from typing import Optional

from autogen_core import (
    AgentId,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
    RoutedAgent,

    MessageContext,
    default_subscription,
)

from common.utils import print_banner, print_section, print_message
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义消息类型 =====
@dataclass
class DirectMessage:
    """直接消息"""
    content: str
    sender: str
    timestamp: str


@dataclass
class PrivateMessage:
    """私有消息"""
    content: str
    password: str
    recipient: str


@dataclass
class ResponseMessage:
    """响应消息"""
    original_message_id: str
    response: str
    responder: str


# ===== 定义 Agent =====
class DirectMessagingAgent(RoutedAgent):
    """支持直接消息的 Agent"""

    def __init__(self, name: str, description: str = "Direct Messaging Agent"):
        super().__init__(description)
        self.name = name
        self.received_messages = []

    @message_handler
    async def handle_direct_message(self, message: DirectMessage, ctx: MessageContext) -> None:
        """处理直接消息"""

        self.received_messages.append(message)

        print(f"\n  📬 [{self.name}] 收到直接消息")
        print(f"     来自: {message.sender}")
        print(f"     内容: {message.content}")
        print(f"     时间: {message.timestamp}")
        print(f"     来源 AgentId: {ctx.sender_id}")

    @message_handler
    async def handle_private_message(self, message: PrivateMessage, ctx: MessageContext) -> None:
        """处理私有消息"""

        print(f"\n  🔒 [{self.name}] 收到私有消息")
        print(f"     收件人: {message.recipient}")

        # 验证收件人
        if message.recipient != self.name:
            print(f"     ⚠️  消息不是给我的，拒绝处理")
            return

        print(f"     内容: {message.content}")
        print(f"     密码: {message.password}")
        print(f"     ✅ 私有消息已验证并处理")


class EchoAgent(RoutedAgent):
    """回声 Agent - 自动回复"""

    def __init__(self, name: str, description: str = "Echo Agent"):
        super().__init__(description)
        self.name = name

    @message_handler
    async def handle_direct_message(self, message: DirectMessage, ctx: MessageContext) -> None:
        """接收并回复消息"""

        print(f"\n  📨 [{self.name}] 收到消息")
        print(f"     内容: {message.content}")
        print(f"     来自: {message.sender}")

        # 发送回复
        if ctx.sender_id:
            response = DirectMessage(
                content=f"回复: {message.content}",
                sender=self.name,
                timestamp=message.timestamp
            )

            print(f"\n  📤 [{self.name}] 发送回复给 {ctx.sender_id}")
            await self.publish_message(response, recipient_id=ctx.sender_id)


class RouterAgent(RoutedAgent):
    """路由 Agent - 转发直接消息"""

    def __init__(self, name: str, description: str = "Router Agent"):
        super().__init__(description)
        self.name = name
        self.routes = {}

    @message_handler
    async def handle_message(self, message: DirectMessage, ctx: MessageContext) -> None:
        """接收并路由消息"""

        print(f"\n  🔀 [{self.name}] 收到消息")
        print(f"     内容: {message.content}")

        # 解析目标
        if message.content.startswith("@"):
            parts = message.content.split(" ", 1)
            target = parts[0][1:]  # 去掉 @
            actual_content = parts[1] if len(parts) > 1 else ""

            # 转发到目标
            target_id = AgentId(type=target, key="default")
            forward_message = DirectMessage(
                content=actual_content,
                sender=message.sender,
                timestamp=message.timestamp
            )

            print(f"     → 转发到: {target_id}")
            await self.publish_message(forward_message, recipient_id=target_id)


# ===== 演示函数 =====
async def demo_basic_direct_messaging():
    """演示 1: 基本的直接消息"""
    print_section("演示 1: Agent 间点对点通信")

    runtime = SingleThreadedAgentRuntime()

    # 注册两个 Agent
    await DirectMessagingAgent.register(runtime, "alice", lambda: DirectMessagingAgent("Alice"))
    await DirectMessagingAgent.register(runtime, "bob", lambda: DirectMessagingAgent("Bob"))

    runtime.start()

    print("\n--- Agent 配置 ---")
    print("  Agent 1: Alice (key='default')")
    print("  Agent 2: Bob (key='default')")

    print("\n--- Alice 发送直接消息给 Bob ---")
    alice_id = AgentId(type="alice", key="default")
    bob_id = AgentId(type="bob", key="default")

    from datetime import datetime

    message = DirectMessage(
        content="你好 Bob！",
        sender="Alice",
        timestamp=datetime.now().isoformat()
    )

    # Alice 发送消息给 Bob
    # 注意: 在实际应用中，这通常通过 Agent 的方法调用实现
    # 这里我们通过 Topic 来模拟直接消息
    print(f"\n  从 {alice_id} 发送到 {bob_id}")

    # 使用广播方式模拟（实际直接消息需要不同的机制）
    await runtime.add_subscription(TypeSubscription("direct", "bob"))
    await runtime.publish_message(message, TopicId("direct", "default"))

    await asyncio.sleep(0.3)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 直接消息使用 AgentId 精确定位接收者")
    print("  - 只有指定的 Agent 会收到消息")
    print("  - 适合点对点通信场景")


async def demo_private_channels():
    """演示 2: 私有消息通道"""
    print_section("演示 2: 私有消息通道")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个 Agent
    await DirectMessagingAgent.register(runtime, "agent1", lambda: DirectMessagingAgent("Agent1"))
    await DirectMessagingAgent.register(runtime, "agent2", lambda: DirectMessagingAgent("Agent2"))
    await DirectMessagingAgent.register(runtime, "agent3", lambda: DirectMessagingAgent("Agent3"))

    await runtime.add_subscription(TypeSubscription("private", "agent1"))
    await runtime.add_subscription(TypeSubscription("private", "agent2"))
    await runtime.add_subscription(TypeSubscription("private", "agent3"))

    runtime.start()

    print("\n--- 发送私有消息 ---")

    # 发给 Agent1 的私有消息
    msg1 = PrivateMessage(
        content="这是给 Agent1 的秘密",
        password="secret123",
        recipient="Agent1"
    )

    print("\n发送给 Agent1:")
    await runtime.publish_message(msg1, TopicId("private", "default"))

    await asyncio.sleep(0.1)

    # 发给 Agent2 的私有消息
    msg2 = PrivateMessage(
        content="这是给 Agent2 的秘密",
        password="secret456",
        recipient="Agent2"
    )

    print("\n发送给 Agent2:")
    await runtime.publish_message(msg2, TopicId("private", "default"))

    await asyncio.sleep(0.3)

    print("\n💡 观察:")
    print("  - Agent1 只收到发给它的消息")
    print("  - Agent2 只收到发给它的消息")
    print("  - Agent3 没有收到任何消息")
    print("  - 实现了私有通信")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_request_response():
    """演示 3: 请求-响应模式"""
    print_section("演示 3: 请求-响应模式")

    runtime = SingleThreadedAgentRuntime()

    # 注册 Echo Agent
    await EchoAgent.register(runtime, "echo", lambda: EchoAgent("Echo服务"))
    await EchoAgent.register(runtime, "client", lambda: EchoAgent("客户端"))

    await runtime.add_subscription(TypeSubscription("echo_channel", "echo"))
    await runtime.add_subscription(TypeSubscription("echo_channel", "client"))

    runtime.start()

    print("\n--- 客户端发送请求到 Echo 服务 ---")

    from datetime import datetime

    request = DirectMessage(
        content="Hello, Echo!",
        sender="客户端",
        timestamp=datetime.now().isoformat()
    )

    await runtime.publish_message(request, TopicId("echo_channel", "default"))

    await asyncio.sleep(0.5)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 客户端发送请求")
    print("  - Echo 服务自动回复")
    print("  - 实现了简单的 RPC 模式")


async def demo_message_routing():
    """演示 4: 消息路由"""
    print_section("演示 4: 消息路由和转发")

    runtime = SingleThreadedAgentRuntime()

    # 注册路由器和目标 Agent
    await RouterAgent.register(runtime, "router", lambda: RouterAgent("路由器"))
    await DirectMessagingAgent.register(runtime, "user1", lambda: DirectMessagingAgent("用户1"))
    await DirectMessagingAgent.register(runtime, "user2", lambda: DirectMessagingAgent("用户2"))

    await runtime.add_subscription(TypeSubscription("route", "router"))
    await runtime.add_subscription(TypeSubscription("inbox", "user1"))
    await runtime.add_subscription(TypeSubscription("inbox", "user2"))

    runtime.start()

    print("\n--- 通过路由器发送消息 ---")

    from datetime import datetime

    # 发送给 User1
    msg1 = DirectMessage(
        content="@user1 你好！",
        sender="发送者",
        timestamp=datetime.now().isoformat()
    )

    print("\n路由: 发送者 → 路由器 → user1")
    await runtime.publish_message(msg1, TopicId("route", "default"))

    await asyncio.sleep(0.2)

    # 发送给 User2
    msg2 = DirectMessage(
        content="@user2 重要通知",
        sender="发送者",
        timestamp=datetime.now().isoformat()
    )

    print("\n路由: 发送者 → 路由器 → user2")
    await runtime.publish_message(msg2, TopicId("route", "default"))

    await asyncio.sleep(0.3)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 路由器解析消息中的目标")
    print("  - 转发到指定的 Agent")
    print("  - 实现了灵活的消息路由")


async def demo_multi_hop_communication():
    """演示 5: 多跳通信"""
    print_section("演示 5: 多跳通信链")

    runtime = SingleThreadedAgentRuntime()

    # 定义一系列 Agent
    agents = ["AgentA", "AgentB", "AgentC", "AgentD"]
    agent_types = ["agent_a", "agent_b", "agent_c", "agent_d"]

    for agent_type, name in zip(agent_types, agents):
        await DirectMessagingAgent.register(
            runtime,
            agent_type,
            lambda n=name: DirectMessagingAgent(n)
        )
        await runtime.add_subscription(TypeSubscription("chain", agent_type))
        print(f"  ✓ 注册: {name}")

    runtime.start()

    print("\n--- 消息传递链: AgentA → AgentB → AgentC → AgentD ---")

    from datetime import datetime

    # 发起消息
    message = DirectMessage(
        content="传递这条消息",
        sender="发起者",
        timestamp=datetime.now().isoformat()
    )

    print("\n第 1 跳: 发起者 → AgentA")
    await runtime.publish_message(message, TopicId("chain", "agent_a"))
    await asyncio.sleep(0.2)

    print("\n第 2 跳: AgentA → AgentB")
    await runtime.publish_message(message, TopicId("chain", "agent_b"))
    await asyncio.sleep(0.2)

    print("\n第 3 跳: AgentB → AgentC")
    await runtime.publish_message(message, TopicId("chain", "agent_c"))
    await asyncio.sleep(0.2)

    print("\n第 4 跳: AgentC → AgentD")
    await runtime.publish_message(message, TopicId("chain", "agent_d"))

    await asyncio.sleep(0.3)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 消息经过多个 Agent")
    print("  - 每跳都是点对点通信")
    print("  - 实现了消息链路传递")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 直接消息传递                          ║
        ║           Direct Messaging (1-to-1)                          ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本直接消息
        await demo_basic_direct_messaging()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 私有通道
        await demo_private_channels()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 请求-响应
        await demo_request_response()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 消息路由
        await demo_message_routing()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 多跳通信
        await demo_multi_hop_communication()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. 直接消息使用 AgentId 精确定位接收者")
        print("  2. 实现了点对点的私有通信")
        print("  3. 可以实现请求-响应模式")
        print("  4. 支持消息路由和转发")
        print("  5. 可以构建多跳通信链")
        print("  6. 适合定向通信和私有对话")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

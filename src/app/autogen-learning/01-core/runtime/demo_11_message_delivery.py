"""
Demo 11: 消息传递机制

本演示展示如何:
1. 理解消息传递的顺序保证
2. 处理消息传递错误
3. 观察消息路由过程
4. 实现消息重试机制
5. 处理消息丢失场景

运行方式:
    python demo_11_message_delivery.py

前置要求:
    - 已完成 demo_09_runtime_basic.py
    - 已完成 demo_10_agent_registration.py

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
from typing import List
from datetime import datetime

from autogen_core import (
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
    RoutedAgent,

    MessageContext,
)

from common.utils import print_banner, print_section, print_message
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义消息类型 =====
@dataclass
class TrackedMessage:
    """可追踪的消息"""
    content: str
    message_id: str
    timestamp: datetime = None
    retry_count: int = 0

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AckMessage:
    """确认消息"""
    original_message_id: str
    receiver: str
    status: str


# ===== 定义 Agent =====
class OrderPreservingAgent(RoutedAgent):
    """保持消息顺序的 Agent"""

    def __init__(self, name: str, description: str = "Order Preserving Agent"):
        super().__init__(description)
        self.name = name
        self.received_order: List[str] = []

    @message_handler
    async def handle_tracked_message(self, message: TrackedMessage, ctx: MessageContext) -> None:
        """处理追踪消息"""

        self.received_order.append(message.message_id)

        print(f"\n  [{self.name}] 收到消息")
        print(f"    ID: {message.message_id}")
        print(f"    内容: {message.content}")
        print(f"    接收顺序: {len(self.received_order)}")

        # 发送确认
        ack = AckMessage(
            original_message_id=message.message_id,
            receiver=self.name,
            status="received"
        )
        if ctx.topic_id:
            await self.publish_message(ack, ctx.topic_id)


class TrackingAgent(RoutedAgent):
    """消息追踪 Agent"""

    def __init__(self, description: str = "Tracking Agent"):
        super().__init__(description)
        self.sent_messages = {}
        self.acknowledgements = {}

    @message_handler
    async def handle_ack(self, message: AckMessage, ctx: MessageContext) -> None:
        """处理确认消息"""

        self.acknowledgements[message.original_message_id] = message

        print(f"\n  📨 [追踪] 收到确认")
        print(f"    消息 ID: {message.original_message_id}")
        print(f"    接收者: {message.receiver}")
        print(f"    状态: {message.status}")


class FailingAgent(RoutedAgent):
    """会失败的 Agent - 演示错误处理"""

    def __init__(self, failure_rate: float = 0.0, description: str = "Failing Agent"):
        super().__init__(description)
        self.failure_rate = failure_rate
        self.processed_count = 0
        self.failed_count = 0

    @message_handler
    async def handle_message(self, message: TrackedMessage, ctx: MessageContext) -> None:
        """处理消息，可能失败"""

        import random

        self.processed_count += 1

        # 根据失败率决定是否失败
        if random.random() < self.failure_rate:
            self.failed_count += 1
            print(f"\n  ❌ [失败Agent] 处理失败")
            print(f"    消息: {message.message_id}")
            print(f"    失败率: {self.failure_rate}")
            raise Exception("模拟的处理失败")

        print(f"\n  ✅ [失败Agent] 处理成功")
        print(f"    消息: {message.message_id}")
        print(f"    总处理: {self.processed_count}")
        print(f"    总失败: {self.failed_count}")


class RetryAgent(RoutedAgent):
    """支持重试的 Agent"""

    def __init__(self, max_retries: int = 3, description: str = "Retry Agent"):
        super().__init__(description)
        self.max_retries = max_retries
        self.retry_attempts = {}

    @message_handler
    async def handle_message(self, message: TrackedMessage, ctx: MessageContext) -> None:
        """处理带重试的消息"""

        retry_count = message.retry_count

        print(f"\n  [重试Agent] 处理消息")
        print(f"    ID: {message.message_id}")
        print(f"    重试次数: {retry_count}/{self.max_retries}")

        # 模拟处理，前两次失败
        if retry_count < 2:
            print(f"    ❌ 处理失败，需要重试")
            # 增加重试计数
            message.retry_count += 1
            # 重新发布到同一个 topic
            if ctx.topic_id:
                await self.publish_message(message, ctx.topic_id)
        else:
            print(f"    ✅ 处理成功")


class BroadcastAgent(RoutedAgent):
    """广播接收 Agent"""

    def __init__(self, name: str, description: str = "Broadcast Agent"):
        super().__init__(description)
        self.name = name
        self.messages_received = 0

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """处理广播消息"""

        self.messages_received += 1
        print(f"\n  📡 [{self.name}] 收到广播 #{self.messages_received}")
        print(f"    消息: {message}")
        print(f"    来源 Topic: {ctx.topic_id}")


# ===== 演示函数 =====
async def demo_message_ordering():
    """演示 1: 消息顺序保证"""
    print_section("演示 1: 消息传递顺序保证")

    runtime = SingleThreadedAgentRuntime()

    await OrderPreservingAgent.register(runtime, "receiver", lambda: OrderPreservingAgent("接收者"))
    await TrackingAgent.register(runtime, "tracker", lambda: TrackingAgent())

    await runtime.add_subscription(TypeSubscription("ordered", "receiver"))
    await runtime.add_subscription(TypeSubscription("ordered", "tracker"))

    runtime.start()

    print("\n--- 发送多条消息 ---")
    messages = [
        ("消息 1", "msg-001"),
        ("消息 2", "msg-002"),
        ("消息 3", "msg-003"),
        ("消息 4", "msg-004"),
        ("消息 5", "msg-005"),
    ]

    print("\n发送顺序:")
    for content, msg_id in messages:
        print(f"  {msg_id}: {content}")
        await runtime.publish_message(
            TrackedMessage(content, msg_id),
            TopicId("ordered", "default")
        )
        await asyncio.sleep(0.05)

    print("\n--- 等待处理完成 ---")
    await asyncio.sleep(0.5)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 观察:")
    print("  - 消息按发送顺序依次处理")
    print("  - 单线程 Runtime 保证消息顺序")
    print("  - 不会出现乱序或并发问题")


async def demo_no_subscriber():
    """演示 2: 没有订阅者的消息"""
    print_section("演示 2: 发送到无订阅者的 Topic")

    runtime = SingleThreadedAgentRuntime()

    await OrderPreservingAgent.register(runtime, "agent", lambda: OrderPreservingAgent("Agent"))
    await runtime.add_subscription(TypeSubscription("subscribed", "agent"))

    runtime.start()

    print("\n--- 发送到有订阅者的 topic ---")
    await runtime.publish_message(
        TrackedMessage("有订阅者", "msg-001"),
        TopicId("subscribed", "default")
    )
    await asyncio.sleep(0.1)

    print("\n--- 发送到无订阅者的 topic ---")
    await runtime.publish_message(
        TrackedMessage("无订阅者", "msg-002"),
        TopicId("nonexistent", "default")
    )
    await asyncio.sleep(0.1)

    print("\n💡 结果:")
    print("  - 不会抛出异常")
    print("  - 消息被静默丢弃")
    print("  - 应用需要确认订阅关系")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_error_handling():
    """演示 3: 消息处理错误"""
    print_section("演示 3: 消息处理错误处理")

    runtime = SingleThreadedAgentRuntime()

    # 使用会失败的 Agent
    await FailingAgent.register(
        runtime,
        "failing",
        lambda: FailingAgent(failure_rate=0.5)
    )
    await runtime.add_subscription(TypeSubscription("errors", "failing"))

    runtime.start()

    print("\n--- 发送多条消息 ---")
    for i in range(5):
        msg = TrackedMessage(f"测试消息 {i+1}", f"error-msg-{i+1}")
        await runtime.publish_message(msg, TopicId("errors", "default"))
        await asyncio.sleep(0.1)

    print("\n💡 观察:")
    print("  - Agent 处理失败会抛出异常")
    print("  - 异常会被传播")
    print("  - 需要适当的错误处理机制")

    try:
        await runtime.stop_when_idle()
        runtime.stop()
    except Exception as e:
        print(f"\n❌ 捕获到异常: {e}")


async def demo_retry_mechanism():
    """演示 4: 消息重试机制"""
    print_section("演示 4: 消息重试机制")

    runtime = SingleThreadedAgentRuntime()

    await RetryAgent.register(
        runtime,
        "retry_agent",
        lambda: RetryAgent(max_retries=3)
    )
    await runtime.add_subscription(TypeSubscription("retry", "retry_agent"))

    runtime.start()

    print("\n--- 发送需要重试的消息 ---")
    msg = TrackedMessage("需要重试的消息", "retry-msg-001", retry_count=0)

    await runtime.publish_message(msg, TopicId("retry", "default"))
    await asyncio.sleep(1.0)

    print("\n💡 观察:")
    print("  - 消息被重新发布到同一个 topic")
    print("  - retry_count 递增")
    print("  - 达到最大重试次数后成功")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_broadcast_delivery():
    """演示 5: 广播消息传递"""
    print_section("演示 5: 广播消息传递 (1对多)")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个订阅同一个 topic 的 Agent
    agent_names = ["订阅者1", "订阅者2", "订阅者3"]
    for name in agent_names:
        await BroadcastAgent.register(
            runtime,
            name.lower().replace(" ", "_"),
            lambda n=name: BroadcastAgent(n)
        )
        await runtime.add_subscription(TypeSubscription("broadcast", name.lower().replace(" ", "_")))
        print(f"  ✓ 注册: {name}")

    runtime.start()

    print("\n--- 发送广播消息 ---")
    await runtime.publish_message(
        "这是广播消息",
        TopicId("broadcast", "default")
    )

    await asyncio.sleep(0.5)

    print("\n💡 观察:")
    print(f"  - 所有 {len(agent_names)} 个 Agent 都收到了消息")
    print("  - 消息被复制到每个订阅者")
    print("  - 每个 Agent 独立处理")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_message_tracking():
    """演示 6: 消息追踪系统"""
    print_section("演示 6: 消息追踪和确认")

    runtime = SingleThreadedAgentRuntime()

    await OrderPreservingAgent.register(runtime, "worker", lambda: OrderPreservingAgent("工作进程"))
    await TrackingAgent.register(runtime, "tracker", lambda: TrackingAgent())

    await runtime.add_subscription(TypeSubscription("tracked", "worker"))
    await runtime.add_subscription(TypeSubscription("tracked", "tracker"))

    runtime.start()

    print("\n--- 发送可追踪的消息 ---")
    messages = [
        TrackedMessage("任务 1", "track-001"),
        TrackedMessage("任务 2", "track-002"),
        TrackedMessage("任务 3", "track-003"),
    ]

    for msg in messages:
        await runtime.publish_message(msg, TopicId("tracked", "default"))
        await asyncio.sleep(0.2)

    print("\n--- 等待确认 ---")
    await asyncio.sleep(0.5)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 追踪系统功能:")
    print("  - 每个消息有唯一 ID")
    print("  - Agent 发送处理确认")
    print("  - 可以追踪消息状态")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 消息传递机制                          ║
        ║           Understanding Message Delivery                      ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 消息顺序
        await demo_message_ordering()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 无订阅者
        await demo_no_subscriber()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 错误处理
        await demo_error_handling()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 重试机制
        await demo_retry_mechanism()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 广播
        await demo_broadcast_delivery()

        print("\n" + "=" * 80 + "\n")

        # 演示 6: 追踪
        await demo_message_tracking()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. 单线程 Runtime 保证消息顺序")
        print("  2. 没有订阅者的消息会被丢弃")
        print("  3. Agent 处理错误会传播异常")
        print("  4. 可以实现重试机制")
        print("  5. 广播消息会复制到所有订阅者")
        print("  6. 可以实现消息追踪系统")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

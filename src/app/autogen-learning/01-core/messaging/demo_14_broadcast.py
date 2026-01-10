"""
Demo 14: 广播消息传递 (Broadcast Messaging)

本演示展示如何:
1. 实现一对多的消息传递
2. 使用 Topic 进行广播
3. 管理广播订阅
4. 实现扇出模式
5. 对比直接消息和广播消息

运行方式:
    python demo_14_broadcast.py

前置要求:
    - 已完成 demo_13_direct_messaging.py
    - 理解直接消息机制

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
class Announcement:
    """公告消息"""
    title: str
    content: str
    priority: str = "normal"
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class Event:
    """事件消息"""
    event_type: str
    data: dict
    source: str


@dataclass
class Notification:
    """通知消息"""
    recipient_type: str
    message: str
    metadata: dict = None


# ===== 定义 Agent =====
class SubscriberAgent(RoutedAgent):
    """订阅者 Agent - 接收广播消息"""

    def __init__(self, name: str, description: str = "Subscriber Agent"):
        super().__init__(description)
        self.name = name
        self.notifications_received = 0
        self.announcements_received = 0

    @message_handler
    async def handle_announcement(self, message: Announcement, ctx: MessageContext) -> None:
        """处理公告"""

        self.announcements_received += 1

        icons = {"low": "🔵", "normal": "🟢", "high": "🟠", "urgent": "🔴"}
        icon = icons.get(message.priority, "⚪")

        print(f"\n  {icon} [{self.name}] 收到公告 #{self.announcements_received}")
        print(f"     标题: {message.title}")
        print(f"     内容: {message.content}")
        print(f"     优先级: {message.priority}")
        print(f"     来源 Topic: {ctx.topic_id}")

    @message_handler
    async def handle_notification(self, message: Notification, ctx: MessageContext) -> None:
        """处理通知"""

        self.notifications_received += 1
        print(f"\n  📬 [{self.name}] 收到通知 #{self.notifications_received}")
        print(f"     消息: {message.message}")


class SelectiveSubscriberAgent(RoutedAgent):
    """选择性订阅 Agent - 根据条件接收消息"""

    def __init__(self, name: str, min_priority: str = "normal", description: str = "Selective Subscriber"):
        super().__init__(description)
        self.name = name
        self.min_priority = min_priority
        self.priority_order = {"low": 0, "normal": 1, "high": 2, "urgent": 3}
        self.received_count = 0

    @message_handler
    async def handle_announcement(self, message: Announcement, ctx: MessageContext) -> None:
        """只处理符合优先级的消息"""

        message_priority_level = self.priority_order.get(message.priority, 0)
        min_priority_level = self.priority_order.get(self.min_priority, 0)

        if message_priority_level < min_priority_level:
            # 优先级不够，忽略
            print(f"\n  ⏭️  [{self.name}] 忽略低优先级消息: {message.title}")
            print(f"     消息优先级: {message.priority}, 要求: {self.min_priority}")
            return

        self.received_count += 1
        print(f"\n  ✅ [{self.name}] 接收公告 #{self.received_count}")
        print(f"     标题: {message.title}")
        print(f"     优先级: {message.priority}")


class BroadcastingAgent(RoutedAgent):
    """广播 Agent - 发送广播消息"""

    def __init__(self, name: str, description: str = "Broadcasting Agent"):
        super().__init__(description)
        self.name = name
        self.broadcast_count = 0

    @message_handler
    async def handle_broadcast_request(self, message: str, ctx: MessageContext) -> None:
        """处理广播请求"""

        self.broadcast_count += 1

        print(f"\n  📢 [{self.name}] 准备广播 #{self.broadcast_count}")
        print(f"     内容: {message}")

        # 创建广播消息
        announcement = Announcement(
            title=f"广播 #{self.broadcast_count}",
            content=message,
            priority="normal"
        )

        # 广播到所有订阅者
        if ctx.topic_id:
            await self.publish_message(announcement, ctx.topic_id)
            print(f"     ✓ 已广播到 Topic: {ctx.topic_id}")


# ===== 演示函数 =====
async def demo_basic_broadcast():
    """演示 1: 基本的广播消息"""
    print_section("演示 1: 一对多广播")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个订阅者
    subscribers = ["订阅者A", "订阅者B", "订阅者C"]
    for i, name in enumerate(subscribers, 1):
        await SubscriberAgent.register(
            runtime,
            f"sub{i}",
            lambda n=name: SubscriberAgent(n)
        )
        await runtime.add_subscription(TypeSubscription("announcements", f"sub{i}"))
        print(f"  ✓ 注册: {name}")

    runtime.start()

    print("\n--- 发送广播消息 ---")
    announcement = Announcement(
        title="系统维护通知",
        content="系统将于今晚进行维护",
        priority="high"
    )

    await runtime.publish_message(announcement, TopicId("announcements", "default"))

    await asyncio.sleep(0.5)

    print("\n💡 观察:")
    print(f"  - 所有 {len(subscribers)} 个订阅者都收到了消息")
    print("  - 每个订阅者独立处理消息")
    print("  - 实现了一对多的广播模式")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_fanout_pattern():
    """演示 2: 扇出模式"""
    print_section("演示 2: 扇出模式 (Fan-out Pattern)")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- 注册多个不同类型的订阅者 ---")

    # 不同类型的 Agent 订阅同一个 topic
    await SubscriberAgent.register(runtime, "logger", lambda: SubscriberAgent("日志记录器"))
    await SubscriberAgent.register(runtime, "monitor", lambda: SubscriberAgent("监控器"))
    await SubscriberAgent.register(runtime, "analyzer", lambda: SubscriberAgent("分析器"))
    await SubscriberAgent.register(runtime, "archiver", lambda: SubscriberAgent("归档器"))

    # 都订阅 events topic
    for agent_type in ["logger", "monitor", "analyzer", "archiver"]:
        await runtime.add_subscription(TypeSubscription("events", agent_type))
        print(f"  ✓ {agent_type}: 订阅 'events'")

    runtime.start()

    print("\n--- 发布事件（扇出）---")
    event = Event(
        event_type="system_event",
        data={"action": "user_login", "user_id": "12345"},
        source="auth_service"
    )

    print(f"\n事件: {event.event_type}")
    print("扇出到:")
    print("  → 日志记录器")
    print("  → 监控器")
    print("  → 分析器")
    print("  → 归档器")

    await runtime.publish_message(event, TopicId("events", "default"))

    await asyncio.sleep(0.5)

    print("\n💡 扇出模式特点:")
    print("  - 一个消息源")
    print("  - 多个接收者")
    print("  - 并行处理")
    print("  - 解耦耦合")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_selective_broadcast():
    """演示 3: 选择性广播"""
    print_section("演示 3: 选择性广播（基于优先级）")

    runtime = SingleThreadedAgentRuntime()

    # 注册不同优先级要求的订阅者
    await SelectiveSubscriberAgent.register(
        runtime,
        "urgent_only",
        lambda: SelectiveSubscriberAgent("紧急订阅者", min_priority="high")
    )
    await SelectiveSubscriberAgent.register(
        runtime,
        "normal_and_above",
        lambda: SelectiveSubscriberAgent("普通订阅者", min_priority="normal")
    )
    await SelectiveSubscriberAgent.register(
        runtime,
        "all_messages",
        lambda: SelectiveSubscriberAgent("全部订阅者", min_priority="low")
    )

    # 都订阅同一个 topic
    await runtime.add_subscription(TypeSubscription("priority_msgs", "urgent_only"))
    await runtime.add_subscription(TypeSubscription("priority_msgs", "normal_and_above"))
    await runtime.add_subscription(TypeSubscription("priority_msgs", "all_messages"))

    runtime.start()

    print("\n--- 发送不同优先级的消息 ---")

    messages = [
        ("低优先级消息", "low"),
        ("普通消息", "normal"),
        ("高优先级消息", "high"),
        ("紧急消息", "urgent"),
    ]

    for content, priority in messages:
        announcement = Announcement(
            title=f"{priority.upper()} 消息",
            content=content,
            priority=priority
        )

        print(f"\n发送: {priority} - {content}")
        await runtime.publish_message(announcement, TopicId("priority_msgs", "default"))
        await asyncio.sleep(0.2)

    print("\n💡 观察结果:")
    print("  - 紧急订阅者: 只收到 high + urgent")
    print("  - 普通订阅者: 收到 normal + high + urgent")
    print("  - 全部订阅者: 收到所有消息")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_topic_based_broadcast():
    """演示 4: 基于 Topic 的广播"""
    print_section("演示 4: 多 Topic 广播")

    runtime = SingleThreadedAgentRuntime()

    # 注册订阅者
    await SubscriberAgent.register(runtime, "sub1", lambda: SubscriberAgent("订阅者1"))
    await SubscriberAgent.register(runtime, "sub2", lambda: SubscriberAgent("订阅者2"))
    await SubscriberAgent.register(runtime, "sub3", lambda: SubscriberAgent("订阅者3"))

    # 不同的订阅模式
    await runtime.add_subscription(TypeSubscription("notifications", "sub1"))
    await runtime.add_subscription(TypeSubscription("notifications", "sub2"))
    await runtime.add_subscription(TypeSubscription("alerts", "sub2"))
    await runtime.add_subscription(TypeSubscription("alerts", "sub3"))

    runtime.start()

    print("\n--- 订阅关系 ---")
    print("  notifications: 订阅者1, 订阅者2")
    print("  alerts: 订阅者2, 订阅者3")

    print("\n--- 发送到 notifications ---")
    await runtime.publish_message(
        Announcement("普通通知", "这是一条普通通知"),
        TopicId("notifications", "default")
    )
    await asyncio.sleep(0.2)

    print("\n--- 发送到 alerts ---")
    await runtime.publish_message(
        Announcement("紧急警报", "这是一条紧急警报"),
        TopicId("alerts", "default")
    )

    await asyncio.sleep(0.5)

    print("\n💡 说明:")
    print("  - notifications: 订阅者1 和 订阅者2 收到")
    print("  - alerts: 订阅者2 和 订阅者3 收到")
    print("  - 订阅者2 同时订阅了两个 topic")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_broadcast_vs_direct():
    """演示 5: 广播 vs 直接消息对比"""
    print_section("演示 5: 广播消息 vs 直接消息")

    runtime = SingleThreadedAgentRuntime()

    await SubscriberAgent.register(runtime, "agent", lambda: SubscriberAgent("Agent"))
    await runtime.add_subscription(TypeSubscription("all", "agent"))

    runtime.start()

    print("\n--- 模式 1: 广播消息 ---")
    print("  特点: 一对多，所有订阅者都收到")

    await runtime.publish_message(
        Announcement("广播", "这是广播消息"),
        TopicId("all", "default")
    )

    await asyncio.sleep(0.2)

    print("\n--- 模式 2: 直接消息 ---")
    print("  特点: 一对一，只有指定接收者收到")
    print("  (通过特定 key 实现)")

    await runtime.publish_message(
        Announcement("直接", "这是直接消息"),
        TopicId("all", "specific_agent")  # 使用特定 key
    )

    await asyncio.sleep(0.2)

    print("\n💡 对比总结:")
    print("  广播消息:")
    print("    - Topic: (type, 'default') 或 (type, '*')")
    print("    - 接收者: 所有订阅该 type 的 Agent")
    print("    - 用途: 通知、事件分发")
    print("")
    print("  直接消息:")
    print("    - Topic: (type, 'specific_key')")
    print("    - 接收者: 只有 key='specific_key' 的 Agent")
    print("    - 用途: 私有通信、定向请求")

    await runtime.stop_when_idle()
    runtime.stop()


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 广播消息传递                          ║
        ║           Broadcast Messaging (1-to-Many)                    ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本广播
        await demo_basic_broadcast()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 扇出模式
        await demo_fanout_pattern()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 选择性广播
        await demo_selective_broadcast()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 基于 Topic
        await demo_topic_based_broadcast()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 对比
        await demo_broadcast_vs_direct()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. 广播消息实现一对多通信")
        print("  2. 使用 Topic 管理广播通道")
        print("  3. 可以实现选择性接收")
        print("  4. 支持扇出模式")
        print("  5. 与直接消息互补使用")
        print("  6. 适合通知和事件分发")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

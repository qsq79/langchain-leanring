"""
Demo 02: Topic 和 Subscription 深入解析

本演示展示如何:
1. 理解 Topic 的组成 (type + source)
2. 使用 TypeSubscription 和 DefaultSubscription
3. 实现多租户架构 (使用 topic source)
4. 理解消息路由机制

运行方式:
    python demo_02_topic_subscription.py

前置要求:
    - 已完成 demo_01_quickstart.py
    - 理解基本的 Agent 和 Runtime 概念

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/topic-and-subscription.html
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/topic-subscription-scenarios.html
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
    DefaultSubscription,
    message_handler,

    RoutedAgent,
    MessageContext,
)

from common.utils import print_banner, print_section, print_message
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义消息类型 =====
@dataclass
class OrderEvent:
    """订单事件"""
    order_id: str
    customer: str
    amount: float
    items: list[str]

    def __str__(self):
        return f"订单 {self.order_id} - {self.customer}: ¥{self.amount} ({len(self.items)} 件商品)"


@dataclass
class NotificationEvent:
    """通知事件"""
    recipient: str
    message: str
    priority: str = "normal"  # low, normal, high


# ===== 定义 Agent =====
class NotificationAgent(RoutedAgent):
    """通知 Agent - 发送通知"""

    def __init__(self, description: str = "Notification Agent"):
        super().__init__(description)
        self.notification_count = 0

    @message_handler
    async def handle_order_event(self, message: OrderEvent, ctx: MessageContext) -> None:
        """处理订单事件，发送通知"""
        self.notification_count += 1

        # 从 topic source 获取客户/租户 ID
        tenant_id = ctx.topic_id.source if ctx.topic_id else "unknown"

        print(f"\n📧 [{self.id.key}] 收到订单事件:")
        print(f"   订单: {message.order_id}")
        print(f"   客户: {message.customer}")
        print(f"   租户: {tenant_id}")
        print(f"   金额: ¥{message.amount}")
        print(f"   ✅ 已发送通知 (第 {self.notification_count} 条)")


class InventoryAgent(RoutedAgent):
    """库存 Agent - 管理库存"""

    def __init__(self, description: str = "Inventory Agent"):
        super().__init__(description)
        self.inventory = {
            "iPhone 15 Pro": 50,
            "MacBook Pro": 30,
            "AirPods": 100,
        }

    @message_handler
    async def handle_order_event(self, message: OrderEvent, ctx: MessageContext) -> None:
        """处理订单事件，更新库存"""
        tenant_id = ctx.topic_id.source if ctx.topic_id else "unknown"

        print(f"\n📊 [{self.id.key}] 更新库存:")
        print(f"   订单: {message.order_id}")
        print(f"   租户: {tenant_id}")

        # 扣减库存
        for item in message.items:
            if item in self.inventory:
                old_stock = self.inventory[item]
                self.inventory[item] = max(0, old_stock - 1)
                print(f"   🔻 {item}: {old_stock} → {self.inventory[item]}")
            else:
                print(f"   ⚠️  商品不存在: {item}")


class AnalyticsAgent(RoutedAgent):
    """分析 Agent - 分析订单"""

    def __init__(self, description: str = "Analytics Agent"):
        super().__init__(description)
        self.total_amount = 0.0
        self.order_count = 0

    @message_handler
    async def handle_order_event(self, message: OrderEvent, ctx: MessageContext) -> None:
        """分析订单数据"""
        self.order_count += 1
        self.total_amount += message.amount

        # 分析订单价值
        if message.amount > 5000:
            category = "高价值订单 💎"
        elif message.amount > 2000:
            category = "中等订单 💰"
        else:
            category = "普通订单 📦"

        print(f"\n📈 [{self.id.key}] 订单分析:")
        print(f"   订单: {message.order_id}")
        print(f"   金额: ¥{message.amount}")
        print(f"   分类: {category}")
        print(f"   累计: {self.order_count} 单, 总额 ¥{self.total_amount:.2f}")


# ===== 演示函数 =====
async def demo_topic_structure():
    """演示 1: Topic 的结构"""
    print_section("演示 1: Topic 的结构 (type + source)")

    print("\nTopic 由两部分组成:")
    print("  Topic = (Topic Type, Topic Source)")
    print("  Topic ID = 'topic_type/topic_source'\n")

    # 创建不同的 Topic
    topics = [
        TopicId("order_created", "default"),
        TopicId("order_created", "client_a"),
        TopicId("order_created", "client_b"),
        TopicId("logistics_update", "default"),
    ]

    print("示例 Topics:")
    for topic in topics:
        print(f"  • Type: '{topic.type}', Source: '{topic.source}'")
        print(f"    → Topic ID: '{topic}'")
    print()

    print("说明:")
    print("  • Topic Type: 消息的类型（如订单创建、物流更新）")
    print("  • Topic Source: 消息的源（如客户 ID、会话 ID）")
    print("  • 同一个 Type 可以有多个不同的 Source\n")


async def demo_type_subscription():
    """演示 2: TypeSubscription - 基于类型的订阅"""
    print_section("演示 2: TypeSubscription - 单租户，多 Agent")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个 Agent
    await NotificationAgent.register(runtime, "notification", lambda: NotificationAgent())
    await InventoryAgent.register(runtime, "inventory", lambda: InventoryAgent())
    await AnalyticsAgent.register(runtime, "analytics", lambda: AnalyticsAgent())

    print("\n已注册的 Agent:")
    print("  📧 notification - 通知 Agent")
    print("  📊 inventory - 库存 Agent")
    print("  📈 analytics - 分析 Agent")

    # 添加订阅 - 所有 Agent 都订阅 order_created
    await runtime.add_subscription(TypeSubscription("order_created", "notification"))
    await runtime.add_subscription(TypeSubscription("order_created", "inventory"))
    await runtime.add_subscription(TypeSubscription("order_created", "analytics"))

    print("\n订阅关系:")
    print("  Topic: order_created/default")
    print("  Subscribers:")
    print("    → notification/default")
    print("    → inventory/default")
    print("    → analytics/default")

    runtime.start()

    # 发布订单事件
    print("\n" + "-" * 80)
    print("发布订单事件")
    print("-" * 80)

    order = OrderEvent(
        order_id="ORD-2025-001",
        customer="张三",
        amount=6999.0,
        items=["MacBook Pro", "AirPods"]
    )

    await runtime.publish_message(order, TopicId("order_created", "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n" + "-" * 80)
    print_message("System", "✓ 订单处理完成 - 三个 Agent 都收到了消息", "SUCCESS")


async def demo_multitenancy():
    """演示 3: 多租户架构 - 使用 topic source"""
    print_section("演示 3: 多租户架构 - 客户隔离")

    runtime = SingleThreadedAgentRuntime()

    # 注册 Agent
    await NotificationAgent.register(runtime, "notification", lambda: NotificationAgent())

    # 添加订阅 - TypeSubscription 会自动映射 source 到 agent key
    await runtime.add_subscription(TypeSubscription("order_created", "notification"))

    print("\n订阅配置:")
    print("  TypeSubscription(topic_type='order_created', agent_type='notification')")
    print("\n这意味着:")
    print("  • ('order_created', 'client_a') → notification/client_a")
    print("  • ('order_created', 'client_b') → notification/client_b")
    print("  • Runtime 会为每个 source 创建独立的 Agent 实例")

    runtime.start()

    # 为不同客户发布订单
    print("\n" + "-" * 80)
    print("多租户场景")
    print("-" * 80)

    orders = [
        (OrderEvent("ORD-A-001", "客户A", 2999.0, ["iPhone 15 Pro"]), "client_a"),
        (OrderEvent("ORD-B-001", "客户B", 6999.0, ["MacBook Pro"]), "client_b"),
        (OrderEvent("ORD-A-002", "客户A", 1299.0, ["AirPods"]), "client_a"),
        (OrderEvent("ORD-B-002", "客户B", 8999.0, ["MacBook Pro", "AirPods"]), "client_b"),
    ]

    for order, client in orders:
        print(f"\n📦 为 {client.upper()} 发布订单: {order.order_id}")
        await runtime.publish_message(order, TopicId("order_created", client))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n" + "-" * 80)
    print_message("System", "✓ 多租户订单处理完成", "SUCCESS")
    print("\n关键点:")
    print("  • 每个客户 (client_a, client_b) 有独立的 Agent 实例")
    print("  • 数据完全隔离")
    print("  • 使用 TypeSubscription 自动管理多租户")


async def demo_multiple_topics():
    """演示 4: 一个 Agent 订阅多个 Topic"""
    print_section("演示 4: 一个 Agent 订阅多个 Topic")

    runtime = SingleThreadedAgentRuntime()

    # 注册 Agent
    await NotificationAgent.register(runtime, "notification", lambda: NotificationAgent())

    # 订阅多个不同的 topic type
    await runtime.add_subscription(TypeSubscription("order_created", "notification"))
    await runtime.add_subscription(TypeSubscription("order_shipped", "notification"))
    await runtime.add_subscription(TypeSubscription("payment_received", "notification"))

    print("\n订阅配置:")
    print("  notification 订阅了:")
    print("    • order_created")
    print("    • order_shipped")
    print("    • payment_received")

    runtime.start()

    # 发布不同类型的消息
    print("\n" + "-" * 80)
    print("多主题场景")
    print("-" * 80)

    events = [
        (OrderEvent("ORD-001", "李四", 2999.0, ["iPhone"]), "order_created"),
        (OrderEvent("ORD-001", "李四", 0, []), "order_shipped"),
        (OrderEvent("ORD-001", "李四", 2999.0, []), "payment_received"),
    ]

    for event, topic_type in events:
        print(f"\n📤 发布事件类型: {topic_type}")
        await runtime.publish_message(event, TopicId(topic_type, "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n" + "-" * 80)
    print_message("System", "✓ 多主题事件处理完成", "SUCCESS")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║        AutoGen 0.4+ - Topic 和 Subscription 深入解析          ║
        ║           Understanding Message Routing                       ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: Topic 结构
        await demo_topic_structure()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: TypeSubscription
        await demo_type_subscription()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 多租户
        await demo_multitenancy()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 多主题订阅
        await demo_multiple_topics()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")
        print("\n关键要点:")
        print("  1. Topic = (type, source) - 定义消息的范围")
        print("  2. TypeSubscription 将 topic_type 映射到 agent_type")
        print("  3. topic_source 自动映射到 agent 的 key")
        print("  4. 使用 topic source 可以实现多租户架构")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

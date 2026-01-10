"""
Demo 07: DefaultSubscription - 默认订阅机制

本演示展示如何:
1. 使用 DefaultSubscription
2. 理解默认主题的行为
3. 对比 TypeSubscription 和 DefaultSubscription
4. 使用默认订阅简化配置

运行方式:
    python demo_07_default_subscription.py

前置要求:
    - 已完成 demo_02_topic_subscription.py
    - 理解 TypeSubscription 的使用

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/topic-and-subscription.html
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

from autogen_core import (
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,
    RoutedAgent,
    MessageContext,
)
from autogen_core._default_subscription import DefaultSubscription

from common.utils import print_banner, print_section, print_message
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义消息类型 =====

@dataclass
class NotificationMessage:
    """通知消息"""
    title: str
    body: str
    priority: str = "normal"


@dataclass
class AlertMessage:
    """警报消息"""
    alert_type: str
    message: str


# ===== 定义 Agent =====
class NotificationAgent(RoutedAgent):
    """通知 Agent - 使用默认订阅"""

    def __init__(self, name: str, description: str = "Notification Agent"):
        super().__init__(description)
        self.name = name
        self.notifications_received = 0

    @message_handler
    async def handle_notification(self, message: NotificationMessage, ctx: MessageContext) -> None:
        """处理通知消息"""
        self.notifications_received += 1

        print(f"\n📬 [{self.name}] 收到通知 #{self.notifications_received}")
        print(f"   标题: {message.title}")
        print(f"   内容: {message.body}")
        print(f"   优先级: {message.priority}")
        print(f"   来源 Topic: {ctx.topic_id}")

    @message_handler
    async def handle_alert(self, message: AlertMessage, ctx: MessageContext) -> None:
        """处理警报消息"""
        print(f"\n🚨 [{self.name}] 收到警报")
        print(f"   类型: {message.alert_type}")
        print(f"   消息: {message.message}")


class LoggerAgent(RoutedAgent):
    """日志 Agent - 记录所有消息"""

    def __init__(self, description: str = "Logger Agent"):
        super().__init__(description)
        self.log_count = 0

    @message_handler
    async def log_notification(self, message: NotificationMessage, ctx: MessageContext) -> None:
        """记录通知"""
        self.log_count += 1
        print(f"\n📝 [Logger] 记录通知 #{self.log_count}")
        print(f"   └─ {message.title}: {message.body}")

    @message_handler
    async def log_alert(self, message: AlertMessage, ctx: MessageContext) -> None:
        """记录警报"""
        self.log_count += 1
        print(f"\n📝 [Logger] 记录警报 #{self.log_count}")
        print(f"   └─ [{message.alert_type}] {message.message}")


# ===== 演示函数 =====
async def demo_default_subscription():
    """演示 1: 基本的默认订阅"""
    print_section("演示 1: DefaultSubscription 基础使用")

    runtime = SingleThreadedAgentRuntime()

    # 注册 Agent
    await NotificationAgent.register(runtime, "notifier", lambda: NotificationAgent("通知中心"))

    # 使用默认订阅 - 订阅默认主题
    # DefaultSubscription 会订阅到 ("default", "default") 这个 Topic
    await runtime.add_subscription(DefaultSubscription(agent_type="notifier"))

    runtime.start()

    print("\n--- 发送消息到默认主题 ---")
    print("💡 说明: DefaultSubscription 订阅到 Topic('default', 'default')")

    # 发送到默认主题
    await runtime.publish_message(
        NotificationMessage(
            title="系统更新",
            body="系统将在今晚进行维护",
            priority="high"
        ),
        TopicId("default", "default")  # 默认主题
    )

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_comparison():
    """演示 2: TypeSubscription vs DefaultSubscription"""
    print_section("演示 2: TypeSubscription vs DefaultSubscription")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个 Agent
    await NotificationAgent.register(runtime, "agent1", lambda: NotificationAgent("Agent1 (TypeSub)"))
    await NotificationAgent.register(runtime, "agent2", lambda: NotificationAgent("Agent2 (DefaultSub)"))
    await NotificationAgent.register(runtime, "agent3", lambda: NotificationAgent("Agent3 (DefaultSub)"))

    # 使用不同的订阅方式
    print("\n--- 配置订阅 ---")

    # agent1: 使用 TypeSubscription - 订阅特定类型
    await runtime.add_subscription(
        TypeSubscription(topic_type="notifications", agent_type="agent1")
    )
    print("✓ Agent1: TypeSubscription('notifications', 'agent1')")
    print("  → 只接收 topic_type='notifications' 的消息")

    # agent2: 使用 DefaultSubscription
    await runtime.add_subscription(DefaultSubscription(agent_type="agent2"))
    print("✓ Agent2: DefaultSubscription('agent2')")
    print("  → 接收 Topic('default', 'default') 的消息")

    # agent3: 另一个 DefaultSubscription
    await runtime.add_subscription(DefaultSubscription(agent_type="agent3"))
    print("✓ Agent3: DefaultSubscription('agent3')")
    print("  → 接收 Topic('default', 'default') 的消息")

    runtime.start()

    print("\n--- 测试 TypeSubscription ---")
    await runtime.publish_message(
        NotificationMessage("测试消息", "发送到 notifications 类型", "normal"),
        TopicId("notifications", "default")
    )
    await asyncio.sleep(0.2)

    print("\n--- 测试 DefaultSubscription ---")
    await runtime.publish_message(
        NotificationMessage("默认消息", "发送到默认主题", "normal"),
        TopicId("default", "default")
    )
    await asyncio.sleep(0.2)

    print("\n💡 观察:")
    print("  - notifications 消息: 只有 Agent1 收到")
    print("  - default 消息: Agent2 和 Agent3 都收到")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_multiple_default_subscribers():
    """演示 3: 多个默认订阅者"""
    print_section("演示 3: 多个 Agent 使用默认订阅")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个使用默认订阅的 Agent
    agents = ["Logger", "Monitor", "Archiver"]
    for agent_name in agents:
        await NotificationAgent.register(
            runtime,
            agent_name.lower(),
            lambda name=agent_name: NotificationAgent(name)
        )
        await runtime.add_subscription(
            DefaultSubscription(agent_type=agent_name.lower())
        )

    runtime.start()

    print(f"\n--- 已注册 {len(agents)} 个 Agent，都使用 DefaultSubscription ---")

    # 发送消息到默认主题
    print("\n--- 发送广播消息 ---")
    await runtime.publish_message(
        NotificationMessage(
            title="系统广播",
            body="重要通知发送给所有订阅者",
            priority="urgent"
        ),
        TopicId("default", "default")
    )

    await asyncio.sleep(0.3)

    print("\n💡 所有使用 DefaultSubscription 的 Agent 都收到了消息")
    print("   这是广播模式的实现")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_mixed_subscriptions():
    """演示 4: 混合使用不同订阅类型"""
    print_section("演示 4: 混合订阅模式")

    runtime = SingleThreadedAgentRuntime()

    # 注册不同类型的 Agent
    await NotificationAgent.register(runtime, "specific", lambda: NotificationAgent("特定Agent"))
    await NotificationAgent.register(runtime, "default1", lambda: NotificationAgent("默认Agent1"))
    await NotificationAgent.register(runtime, "default2", lambda: NotificationAgent("默认Agent2"))
    await LoggerAgent.register(runtime, "logger", lambda: LoggerAgent())

    # 配置不同的订阅
    print("\n--- 订阅配置 ---")

    # 特定订阅
    await runtime.add_subscription(
        TypeSubscription("urgent_alerts", "specific")
    )
    print("✓ specific: TypeSubscription('urgent_alerts')")

    # 默认订阅
    await runtime.add_subscription(DefaultSubscription(agent_type="default1"))
    await runtime.add_subscription(DefaultSubscription(agent_type="default2"))
    print("✓ default1, default2: DefaultSubscription()")

    # Logger 使用默认订阅记录所有消息
    await runtime.add_subscription(
        TypeSubscription("urgent_alerts", "logger")
    )
    await runtime.add_subscription(DefaultSubscription(agent_type="logger"))
    print("✓ logger: TypeSubscription + DefaultSubscription (多订阅)")

    runtime.start()

    print("\n--- 发送紧急警报 ---")
    await runtime.publish_message(
        AlertMessage("系统故障", "CPU温度过高"),
        TopicId("urgent_alerts", "server1")
    )
    await asyncio.sleep(0.2)

    print("\n--- 发送默认通知 ---")
    await runtime.publish_message(
        NotificationMessage("日常通知", "系统运行正常", "normal"),
        TopicId("default", "default")
    )
    await asyncio.sleep(0.2)

    print("\n💡 观察:")
    print("  - 紧急警报: specific + logger 收到")
    print("  - 日常通知: default1 + default2 + logger 收到")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_subscription_patterns():
    """演示 5: 订阅模式最佳实践"""
    print_section("演示 5: 订阅模式选择指南")

    runtime = SingleThreadedAgentRuntime()

    await NotificationAgent.register(runtime, "agent", lambda: NotificationAgent("DemoAgent"))

    runtime.start()

    print("\n--- 场景对比 ---\n")

    print("场景 1: 特定业务事件")
    print("  推荐: TypeSubscription")
    print("  原因: 明确的消息类型，易于维护")
    print("  示例:")
    await runtime.add_subscription(TypeSubscription("order_created", "agent"))
    await runtime.publish_message(
        NotificationMessage("订单创建", "订单 #12345 已创建", "normal"),
        TopicId("order_created", "default")
    )
    await asyncio.sleep(0.1)

    print("\n场景 2: 通用通知")
    print("  推荐: DefaultSubscription")
    print("  原因: 简化配置，统一入口")
    print("  示例:")
    await runtime.publish_message(
        NotificationMessage("系统通知", "这是一条通用通知", "normal"),
        TopicId("default", "default")
    )
    await asyncio.sleep(0.1)

    print("\n场景 3: 多源消息")
    print("  推荐: TypeSubscription with different sources")
    print("  原因: 支持多租户，灵活路由")
    print("  示例:")

    # 移除之前的订阅
    print("\n💡 最佳实践总结:")
    print("  1. 明确的业务事件 → TypeSubscription")
    print("  2. 通用/全局消息 → DefaultSubscription")
    print("  3. 需要多租户 → TypeSubscription + source")
    print("  4. 需要多订阅 → Agent 可以添加多个订阅")

    await runtime.stop_when_idle()
    runtime.stop()


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - DefaultSubscription 深入解析            ║
        ║           Understanding Default Subscriptions                 ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本使用
        await demo_default_subscription()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 对比
        await demo_comparison()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 多订阅者
        await demo_multiple_default_subscribers()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 混合订阅
        await demo_mixed_subscriptions()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 最佳实践
        await demo_subscription_patterns()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. DefaultSubscription 订阅 Topic('default', 'default')")
        print("  2. 适合通用/全局消息场景")
        print("  3. TypeSubscription 适合特定业务事件")
        print("  4. 可以混合使用不同订阅类型")
        print("  5. 一个 Agent 可以有多个订阅")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

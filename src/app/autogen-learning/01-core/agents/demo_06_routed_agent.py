"""
Demo 06: RoutedAgent 深入解析

本演示展示如何:
1. 创建复杂的 RoutedAgent
2. 使用多个 @message_handler
3. 实现消息类型匹配和路由
4. 处理消息优先级
5. 实现 Agent 间的协作

运行方式:
    python demo_06_routed_agent.py

前置要求:
    - 已完成 concepts 系列的所有 demo
    - 理解基本的 Agent 和消息处理

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/agents.html
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
from typing import List, Literal
from enum import Enum

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
class Priority(str, Enum):
    """消息优先级"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class PriorityMessage:
    """带优先级的消息"""
    content: str
    priority: Priority
    sender: str

    def __str__(self):
        icon = {"low": "🟢", "normal": "🟡", "high": "🟠", "urgent": "🔴"}.get(self.priority, "⚪")
        return f"{icon} [{self.priority.upper()}] {self.content}"


@dataclass
class DataMessage:
    """数据消息"""
    data_id: str
    payload: dict
    operation: Literal["create", "update", "delete", "query"]


@dataclass
class ControlMessage:
    """控制消息"""
    command: Literal["start", "stop", "pause", "resume"]
    params: dict = None


@dataclass
class BatchMessage:
    """批量消息"""
    messages: List[str]
    batch_id: str


# ===== 定义 Agent =====
class MultiHandlerAgent(RoutedAgent):
    """多消息处理器 Agent - 演示一个 Agent 处理多种消息"""

    def __init__(self, description: str = "Multi-Handler Agent"):
        super().__init__(description)
        self.stats = {
            "priority": 0,
            "data": 0,
            "control": 0,
            "batch": 0,
        }
        self.is_paused = False

    @message_handler
    async def handle_priority_message(self, message: PriorityMessage, ctx: MessageContext) -> None:
        """处理优先级消息"""
        self.stats["priority"] += 1

        print(f"\n📨 [优先级消息 #{self.stats['priority']}]")
        print(f"   {message}")
        print(f"   来自: {message.sender}")

        # 根据优先级处理
        if message.priority == Priority.URGENT:
            print(f"   ⚠️  紧急消息，立即处理!")
        elif message.priority == Priority.HIGH:
            print(f"   🔼 高优先级，优先处理")
        elif message.priority == Priority.NORMAL:
            print(f"   ➡️  正常处理")
        else:
            print(f"   🔽 低优先级，延后处理")

    @message_handler
    async def handle_data_message(self, message: DataMessage, ctx: MessageContext) -> None:
        """处理数据消息"""
        self.stats["data"] += 1

        if self.is_paused and message.operation != "query":
            print(f"\n⏸️  Agent 已暂停，忽略操作: {message.operation}")
            return

        print(f"\n💾 [数据操作 #{self.stats['data']}]")
        print(f"   ID: {message.data_id}")
        print(f"   操作: {message.operation}")
        print(f"   数据: {message.payload}")

        # 模拟操作
        if message.operation == "create":
            print(f"   ✅ 数据已创建")
        elif message.operation == "update":
            print(f"   ✅ 数据已更新")
        elif message.operation == "delete":
            print(f"   ✅ 数据已删除")
        elif message.operation == "query":
            print(f"   📊 查询结果: ...")

    @message_handler
    async def handle_control_message(self, message: ControlMessage, ctx: MessageContext) -> None:
        """处理控制消息"""
        self.stats["control"] += 1

        print(f"\n🎛️  [控制命令 #{self.stats['control']}]")
        print(f"   命令: {message.command}")

        if message.command == "start":
            print(f"   ▶️  Agent 已启动")
        elif message.command == "stop":
            print(f"   ⏹️  Agent 已停止")
        elif message.command == "pause":
            self.is_paused = True
            print(f"   ⏸️  Agent 已暂停")
        elif message.command == "resume":
            self.is_paused = False
            print(f"   ▶️  Agent 已恢复")

    @message_handler
    async def handle_batch_message(self, message: BatchMessage, ctx: MessageContext) -> None:
        """处理批量消息"""
        self.stats["batch"] += 1

        print(f"\n📦 [批量消息 #{self.stats['batch']}]")
        print(f"   批次 ID: {message.batch_id}")
        print(f"   消息数: {len(message.messages)}")

        for i, msg in enumerate(message.messages, 1):
            print(f"      {i}. {msg}")

        print(f"   ✅ 批量处理完成")

    async def print_stats(self):
        """打印统计信息"""
        print(f"\n📊 Agent 统计:")
        total = sum(self.stats.values())
        for msg_type, count in self.stats.items():
            if count > 0:
                print(f"   {msg_type}: {count}")
        print(f"   总计: {total}")


class CollaboratingAgent(RoutedAgent):
    """协作 Agent - 演示 Agent 间的协作"""

    def __init__(self, name: str, role: str, description: str = ""):
        super().__init__(description or f"{role} Agent")
        self.name = name
        self.role = role
        self.task_count = 0

    @message_handler
    async def handle_task(self, message: PriorityMessage, ctx: MessageContext) -> None:
        """处理任务并转发给其他 Agent"""

        self.task_count += 1
        print(f"\n👤 [{self.name}] ({self.role}) 处理任务 #{self.task_count}")
        print(f"   任务: {message.content}")

        # 模拟处理
        await asyncio.sleep(0.1)

        # 如果需要协作，转发给其他 topic
        if "协作" in message.content and ctx.topic_id:
            collaboration_topic = TopicId("collaboration", "team")
            forward_msg = PriorityMessage(
                content=f"{self.name} 完成部分，请求协作",
                priority=message.priority,
                sender=self.name
            )
            print(f"   🤝 请求协作...")
            await self.publish_message(forward_msg, collaboration_topic)


class FilteringAgent(RoutedAgent):
    """过滤 Agent - 演示消息过滤"""

    def __init__(self, description: str = "Filtering Agent"):
        super().__init__(description)
        self.allowed_senders = {"admin", "system"}
        self.blocked_count = 0
        self.allowed_count = 0

    @message_handler
    async def handle_message(self, message: PriorityMessage, ctx: MessageContext) -> None:
        """处理消息，根据发送者过滤"""

        # 检查发送者权限
        if message.sender not in self.allowed_senders:
            self.blocked_count += 1
            print(f"\n🚫 [过滤器] 消息被拦截")
            print(f"   发送者: {message.sender}")
            print(f"   原因: 未授权")
            print(f"   总拦截: {self.blocked_count}")
            return

        self.allowed_count += 1
        print(f"\n✅ [过滤器] 消息通过")
        print(f"   发送者: {message.sender}")
        print(f"   内容: {message.content}")
        print(f"   总通过: {self.allowed_count}")


# ===== 演示函数 =====
async def demo_multi_handler():
    """演示 1: 一个 Agent 处理多种消息类型"""
    print_section("演示 1: 多类型消息处理器")

    runtime = SingleThreadedAgentRuntime()

    await MultiHandlerAgent.register(runtime, "multi", lambda: MultiHandlerAgent())
    await runtime.add_subscription(TypeSubscription("multi", "multi"))

    runtime.start()

    # 发送不同类型的消息
    print("\n--- 发送各种类型的消息 ---")

    # 优先级消息
    await runtime.publish_message(
        PriorityMessage("紧急任务", Priority.URGENT, "admin"),
        TopicId("multi", "default")
    )

    await runtime.publish_message(
        PriorityMessage("普通任务", Priority.NORMAL, "user"),
        TopicId("multi", "default")
    )

    # 数据消息
    await runtime.publish_message(
        DataMessage("data-001", {"name": "test", "value": 100}, "create"),
        TopicId("multi", "default")
    )

    # 控制消息
    await runtime.publish_message(
        ControlMessage("pause", {"duration": 10}),
        TopicId("multi", "default")
    )

    # 尝试数据操作（应该被暂停）
    await runtime.publish_message(
        DataMessage("data-002", {"name": "test2"}, "create"),
        TopicId("multi", "default")
    )

    # 恢复
    await runtime.publish_message(
        ControlMessage("resume"),
        TopicId("multi", "default")
    )

    # 批量消息
    await runtime.publish_message(
        BatchMessage(["msg1", "msg2", "msg3"], "batch-001"),
        TopicId("multi", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_collaboration():
    """演示 2: Agent 协作"""
    print_section("演示 2: 多 Agent 协作")

    runtime = SingleThreadedAgentRuntime()

    # 创建不同角色的 Agent
    await CollaboratingAgent.register(runtime, "agent1", lambda: CollaboratingAgent("Alice", "分析师"))
    await CollaboratingAgent.register(runtime, "agent2", lambda: CollaboratingAgent("Bob", "开发者"))
    await CollaboratingAgent.register(runtime, "agent3", lambda: CollaboratingAgent("Charlie", "测试员"))

    # 所有 Agent 订阅任务 topic
    await runtime.add_subscription(TypeSubscription("tasks", "agent1"))
    await runtime.add_subscription(TypeSubscription("tasks", "agent2"))
    await runtime.add_subscription(TypeSubscription("tasks", "agent3"))

    # 订阅协作 topic
    await runtime.add_subscription(TypeSubscription("collaboration", "agent1"))
    await runtime.add_subscription(TypeSubscription("collaboration", "agent2"))

    runtime.start()

    print("\n--- 分发任务 ---")
    tasks = [
        PriorityMessage("分析需求", Priority.HIGH, "manager"),
        PriorityMessage("开发功能并协作", Priority.NORMAL, "manager"),
        PriorityMessage("编写测试", Priority.NORMAL, "manager"),
    ]

    for task in tasks:
        await runtime.publish_message(task, TopicId("tasks", "default"))
        await asyncio.sleep(0.3)

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_filtering():
    """演示 3: 消息过滤"""
    print_section("演示 3: 消息过滤和权限控制")

    runtime = SingleThreadedAgentRuntime()

    await FilteringAgent.register(runtime, "filter", lambda: FilteringAgent())
    await runtime.add_subscription(TypeSubscription("filtered", "filter"))

    runtime.start()

    print("\n--- 发送消息，不同发送者 ---")

    # 授权用户
    await runtime.publish_message(
        PriorityMessage("系统命令", Priority.HIGH, "admin"),
        TopicId("filtered", "default")
    )

    await runtime.publish_message(
        PriorityMessage("系统日志", Priority.NORMAL, "system"),
        TopicId("filtered", "default")
    )

    # 未授权用户
    await runtime.publish_message(
        PriorityMessage("用户请求", Priority.NORMAL, "user"),
        TopicId("filtered", "default")
    )

    await runtime.publish_message(
        PriorityMessage("可疑操作", Priority.HIGH, "hacker"),
        TopicId("filtered", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  1. Agent 可以实现消息过滤逻辑")
    print("  2. 基于 sender_id 或消息内容做决策")
    print("  3. 可以实现权限控制和安全性")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - RoutedAgent 深入解析                   ║
        ║           Advanced Agent Patterns                            ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 多处理器
        await demo_multi_handler()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 协作
        await demo_collaboration()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 过滤
        await demo_filtering()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. RoutedAgent 可以有多个 @message_handler")
        print("  2. 每个处理器处理特定类型的消息")
        print("  3. Agent 可以维护内部状态")
        print("  4. Agent 之间可以通过 Topic 协作")
        print("  5. 可以实现过滤、权限控制等模式")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
Demo 03: Agent 生命周期管理

本演示展示如何:
1. 理解 Agent 的生命周期阶段
2. 管理 Agent 的初始化和状态
3. 处理 Agent 的创建和复用
4. 实现 Agent 的清理逻辑

运行方式:
    python demo_03_agent_lifecycle.py

前置要求:
    - 已完成 demo_01_quickstart.py
    - 理解基本的 Agent 和 Runtime 概念

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
from datetime import datetime
from typing import Optional

from autogen_core import (
    AgentId,
    AgentRuntime,
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
class CreateAgentMessage:
    """创建 Agent 的消息"""

    def __init__(self, agent_type: str, config: dict = None):
        self.agent_type = agent_type
        self.config = config or {}
        self.timestamp = datetime.now()


class ShutdownMessage:
    """关闭 Agent 的消息"""

    def __init__(self, reason: str = "normal"):
        self.reason = reason
        self.timestamp = datetime.now()


class TaskMessage:
    """任务消息"""

    def __init__(self, task_id: str, description: str):
        self.task_id = task_id
        self.description = description
        self.timestamp = datetime.now()


class StatusQueryMessage:
    """状态查询消息"""

    def __init__(self):
        self.timestamp = datetime.now()


# ===== 定义 Agent =====
class LifecycleAgent(RoutedAgent):
    """演示 Agent 生命周期的 Agent

    生命周期阶段:
    1. __init__: 构造函数，初始化 Agent
    2. register: 注册到 Runtime
    3. 运行: 处理消息
    4. 关闭: 清理资源
    """

    # 类变量，跟踪所有实例
    instance_count = 0
    active_instances = {}

    def __init__(self, description: str = "Lifecycle Demo Agent"):
        super().__init__(description)

        # 实例变量
        self.agent_id_str = f"agent_{LifecycleAgent.instance_count}"
        self.created_at = datetime.now()
        self.message_count = 0
        self.is_shutdown = False

        # 更新类级别的计数
        LifecycleAgent.instance_count += 1
        LifecycleAgent.active_instances[self.agent_id_str] = {
            "created_at": self.created_at,
            "status": "active",
        }

        print(f"\n🎬 [Agent 初始化] 创建 Agent: {self.agent_id_str}")
        print(f"   创建时间: {self.created_at.strftime('%H:%M:%S.%f')[:-3]}")
        print(f"   总实例数: {LifecycleAgent.instance_count}")

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务消息"""
        if self.is_shutdown:
            print(f"⚠️  [{self.agent_id_str}] Agent 已关闭，拒绝处理任务")
            return

        self.message_count += 1

        print(f"\n📨 [{self.agent_id_str}] 处理任务 #{self.message_count}")
        print(f"   任务 ID: {message.task_id}")
        print(f"   描述: {message.description}")
        print(f"   处理时间: {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")

        # 模拟处理
        await asyncio.sleep(0.1)
        print(f"   ✅ 任务完成")

    @message_handler
    async def handle_status_query(self, message: StatusQueryMessage, ctx: MessageContext) -> None:
        """处理状态查询"""
        uptime = datetime.now() - self.created_at

        print(f"\n📊 [{self.agent_id_str}] Agent 状态:")
        print(f"   创建时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   运行时长: {uptime.total_seconds():.2f} 秒")
        print(f"   处理消息数: {self.message_count}")
        print(f"   状态: {'关闭' if self.is_shutdown else '运行中'}")
        print(f"   Agent ID: {self.id}")

    @message_handler
    async def handle_shutdown(self, message: ShutdownMessage, ctx: MessageContext) -> None:
        """处理关闭消息"""
        if self.is_shutdown:
            print(f"⚠️  [{self.agent_id_str}] Agent 已经关闭")
            return

        print(f"\n🛑 [{self.agent_id_str}] 关闭 Agent")
        print(f"   原因: {message.reason}")
        print(f"   总处理消息数: {self.message_count}")

        # 更新状态
        self.is_shutdown = True
        if self.agent_id_str in LifecycleAgent.active_instances:
            LifecycleAgent.active_instances[self.agent_id_str]["status"] = "shutdown"
            LifecycleAgent.active_instances[self.agent_id_str]["shutdown_at"] = datetime.now()

        print(f"   ✓ Agent 已关闭")

    def __del__(self):
        """析构函数 - 清理资源"""
        if hasattr(self, "agent_id_str") and self.agent_id_str in LifecycleAgent.active_instances:
            del LifecycleAgent.active_instances[self.agent_id_str]
            print(f"\n🗑️  [析构] Agent {self.agent_id_str} 被销毁")


class StatefulAgent(RoutedAgent):
    """有状态的 Agent - 演示状态管理"""

    def __init__(self, description: str = "Stateful Agent"):
        super().__init__(description)

        # Agent 状态
        self.state = {
            "initialized": True,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "last_activity": None,
        }

        print(f"🔧 [StatefulAgent] 初始化状态")

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务并更新状态"""
        self.state["last_activity"] = datetime.now()

        # 模拟任务处理
        success = len(message.description) % 2 == 0  # 偶数长度成功

        if success:
            self.state["tasks_completed"] += 1
            print(f"✅ [StatefulAgent] 任务成功")
        else:
            self.state["tasks_failed"] += 1
            print(f"❌ [StatefulAgent] 任务失败")

    @message_handler
    async def handle_status_query(self, message: StatusQueryMessage, ctx: MessageContext) -> None:
        """返回当前状态"""
        print(f"\n📋 [StatefulAgent] 当前状态:")
        for key, value in self.state.items():
            if isinstance(value, datetime):
                value = value.strftime("%H:%M:%S")
            print(f"   {key}: {value}")


# ===== 演示函数 =====
async def demo_agent_creation():
    """演示 1: Agent 创建和初始化"""
    print_section("演示 1: Agent 创建和初始化")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- 注册第一个 Agent ---")
    await LifecycleAgent.register(runtime, "lifecycle", lambda: LifecycleAgent())

    print("\n--- 注册第二个 Agent ---")
    await LifecycleAgent.register(runtime, "lifecycle", lambda: LifecycleAgent())

    await runtime.add_subscription(TypeSubscription("task", "lifecycle"))
    runtime.start()

    print("\n--- 发送任务 ---")
    await runtime.publish_message(
        TaskMessage("task-1", "第一个任务"), TopicId("task", "instance_1")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print(f"\n📊 总共创建了 {LifecycleAgent.instance_count} 个 Agent 实例")


async def demo_agent_reuse():
    """演示 2: Agent 复用"""
    print_section("演示 2: Agent 复用 (同一个 key)")

    runtime = SingleThreadedAgentRuntime()

    # 只注册一次
    await LifecycleAgent.register(runtime, "reusable", lambda: LifecycleAgent())
    await runtime.add_subscription(TypeSubscription("tasks", "reusable"))

    runtime.start()

    print("\n--- 发送多个任务到同一个 Agent ---")
    for i in range(3):
        await runtime.publish_message(
            TaskMessage(f"task-{i+1}", f"任务 {i+1}"), TopicId("tasks", "default")
        )
        await asyncio.sleep(0.2)

    # 查询状态
    await runtime.publish_message(StatusQueryMessage(), TopicId("tasks", "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明: 虽然发送了多条消息，但只有一个 Agent 实例")
    print("   Runtime 会复用已存在的 Agent (相同 key)")


async def demo_multi_instance():
    """演示 3: 多实例 Agent"""
    print_section("演示 3: 多实例 Agent (不同的 key)")

    runtime = SingleThreadedAgentRuntime()

    await LifecycleAgent.register(runtime, "multi", lambda: LifecycleAgent())
    await runtime.add_subscription(TypeSubscription("work", "multi"))

    runtime.start()

    print("\n--- 发送任务到不同的 instance ---")
    instances = ["client_a", "client_b", "client_c"]

    for instance in instances:
        print(f"\n📤 发送到 {instance}")
        await runtime.publish_message(
            TaskMessage(f"task-{instance}", f"{instance} 的任务"), TopicId("work", instance)
        )
        await asyncio.sleep(0.1)

    print(f"\n💡 每个不同的 source 会创建独立的 Agent 实例")
    print(f"   总实例数: {LifecycleAgent.instance_count}")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_agent_state():
    """演示 4: Agent 状态管理"""
    print_section("演示 4: Agent 状态管理")

    runtime = SingleThreadedAgentRuntime()

    await StatefulAgent.register(runtime, "stateful", lambda: StatefulAgent())
    await runtime.add_subscription(TypeSubscription("stateful_tasks", "stateful"))

    runtime.start()

    print("\n--- 执行多个任务 ---")
    tasks = [
        ("task-1", "任务1"),  # 成功 (长度 4)
        ("task-2", "任务"),   # 失败 (长度 6)
        ("task-3", "任务123"),  # 成功 (长度 8)
    ]

    for task_id, desc in tasks:
        await runtime.publish_message(
            TaskMessage(task_id, desc), TopicId("stateful_tasks", "default")
        )
        await asyncio.sleep(0.1)

    print("\n--- 查询最终状态 ---")
    await runtime.publish_message(StatusQueryMessage(), TopicId("stateful_tasks", "default"))

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_agent_shutdown():
    """演示 5: Agent 关闭和清理"""
    print_section("演示 5: Agent 关闭流程")

    runtime = SingleThreadedAgentRuntime()

    await LifecycleAgent.register(runtime, "shutdown_demo", lambda: LifecycleAgent())
    await runtime.add_subscription(TypeSubscription("control", "shutdown_demo"))

    runtime.start()

    print("\n--- Agent 运行中 ---")
    await runtime.publish_message(
        TaskMessage("task-1", "正常任务"), TopicId("control", "default")
    )
    await runtime.publish_message(StatusQueryMessage(), TopicId("control", "default"))

    print("\n--- 请求关闭 Agent ---")
    await runtime.publish_message(
        ShutdownMessage("用户请求"), TopicId("control", "default")
    )

    print("\n--- 尝试发送新任务 ---")
    await runtime.publish_message(
        TaskMessage("task-2", "关闭后的任务"), TopicId("control", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 Agent 关闭后拒绝处理新任务")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - Agent 生命周期管理                     ║
        ║           Understanding Agent Lifecycle                       ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: Agent 创建
        await demo_agent_creation()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: Agent 复用
        await demo_agent_reuse()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 多实例
        await demo_multi_instance()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 状态管理
        await demo_agent_state()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 关闭流程
        await demo_agent_shutdown()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. Agent 生命周期: 初始化 → 运行 → 关闭")
        print("  2. Runtime 会复用相同 key 的 Agent 实例")
        print("  3. 不同 source 创建不同的 Agent 实例 (多租户)")
        print("  4. Agent 可以维护内部状态")
        print("  5. 应该实现优雅的关闭逻辑")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
Demo 08: Agent 状态管理

本演示展示如何:
1. 在 Agent 中维护状态
2. 实现状态的持久化
3. 处理并发状态更新
4. 实现状态查询和快照
5. 管理状态生命周期

运行方式:
    python demo_08_agent_state.py

前置要求:
    - 已完成 demo_03_agent_lifecycle.py
    - 理解 Agent 的基本概念

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
import json
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
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
class AgentStatus(str, Enum):
    """Agent 状态"""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    SUSPENDED = "suspended"


@dataclass
class StateUpdateMessage:
    """状态更新消息"""
    key: str
    value: Any
    operation: str = "set"  # set, increment, decrement


@dataclass
class StateQueryMessage:
    """状态查询消息"""
    query: str = "all"  # all, specific
    key: Optional[str] = None


@dataclass
class StateSnapshotMessage:
    """状态快照消息"""
    snapshot_id: str


@dataclass
class TaskMessage:
    """任务消息"""
    task_id: str
    task_data: dict


# ===== 定义 Agent =====
class StatefulAgent(RoutedAgent):
    """有状态的 Agent - 基础状态管理"""

    def __init__(self, agent_id: str, description: str = "Stateful Agent"):
        super().__init__(description)

        # Agent 的内部状态
        self.agent_id = agent_id
        self.state = {
            "status": AgentStatus.IDLE,
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "task_count": 0,
            "error_count": 0,
            "last_activity": None,
        }

        # 状态变更历史
        self.state_history = []

        print(f"\n🔧 [{agent_id}] Agent 初始化完成")
        print(f"   初始状态: {self.state['status']}")

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务并更新状态"""

        # 更新状态
        self._update_state("status", AgentStatus.BUSY)
        self._update_state("task_count", self.state["task_count"] + 1, operation="increment")
        self._update_state("last_activity", datetime.now().isoformat())

        print(f"\n🔨 [{self.agent_id}] 处理任务")
        print(f"   任务 ID: {message.task_id}")
        print(f"   当前状态: {self.state['status']}")
        print(f"   已处理任务: {self.state['task_count']}")

        # 模拟任务处理
        await asyncio.sleep(0.2)

        # 任务完成，恢复空闲状态
        self._update_state("status", AgentStatus.IDLE)
        print(f"   ✅ 任务完成，状态: {self.state['status']}")

    @message_handler
    async def handle_state_update(self, message: StateUpdateMessage, ctx: MessageContext) -> None:
        """处理状态更新请求"""

        print(f"\n⚙️  [{self.agent_id}] 更新状态")
        print(f"   键: {message.key}")
        print(f"   操作: {message.operation}")

        if message.operation == "set":
            self._update_state(message.key, message.value)
        elif message.operation == "increment":
            current = self.state.get(message.key, 0)
            self._update_state(message.key, current + 1, operation="increment")
        elif message.operation == "decrement":
            current = self.state.get(message.key, 0)
            self._update_state(message.key, current - 1, operation="decrement")

        print(f"   新值: {self.state.get(message.key)}")

    @message_handler
    async def handle_state_query(self, message: StateQueryMessage, ctx: MessageContext) -> None:
        """处理状态查询"""

        print(f"\n🔍 [{self.agent_id}] 状态查询")
        print(f"   查询类型: {message.query}")

        if message.query == "all":
            print(f"\n   📋 完整状态:")
            for key, value in self.state.items():
                print(f"      {key}: {value}")
        elif message.query == "specific" and message.key:
            value = self.state.get(message.key)
            print(f"   {message.key}: {value}")

    def _update_state(self, key: str, value: Any, operation: str = "set") -> None:
        """更新状态并记录历史"""

        old_value = self.state.get(key)

        # 更新状态
        self.state[key] = value

        # 记录历史
        history_entry = {
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "old_value": old_value,
            "new_value": value,
            "operation": operation,
        }

        self.state_history.append(history_entry)

        # 限制历史记录大小
        if len(self.state_history) > 100:
            self.state_history = self.state_history[-100:]


class PersistentAgent(RoutedAgent):
    """持久化状态 Agent - 支持状态保存和加载"""

    def __init__(self, agent_id: str, save_file: str = None, description: str = "Persistent Agent"):
        super().__init__(description)

        self.agent_id = agent_id
        self.save_file = save_file or f"{agent_id}_state.json"
        self.state = {}
        self.auto_save = True

        # 尝试加载之前的状态
        self._load_state()

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务"""

        task_count = self.state.get("completed_tasks", 0)
        self.state["completed_tasks"] = task_count + 1
        self.state["last_task"] = {
            "id": message.task_id,
            "completed_at": datetime.now().isoformat()
        }

        print(f"\n✅ [{self.agent_id}] 完成任务 #{self.state['completed_tasks']}")

        # 自动保存
        if self.auto_save:
            await self._save_state_async()

    @message_handler
    async def handle_save_state(self, message: StateSnapshotMessage, ctx: MessageContext) -> None:
        """保存状态快照"""

        snapshot = {
            "snapshot_id": message.snapshot_id,
            "timestamp": datetime.now().isoformat(),
            "state": self.state
        }

        # 这里简化为内存保存，实际应该写入文件或数据库
        print(f"\n💾 [{self.agent_id}] 保存状态快照")
        print(f"   快照 ID: {message.snapshot_id}")
        print(f"   状态项: {len(self.state)}")

    def _load_state(self) -> None:
        """加载状态（简化版）"""
        # 实际实现中应该从文件/数据库加载
        print(f"\n📂 [{self.agent_id}] 尝试加载状态...")
        print(f"   状态文件: {self.save_file}")
        print(f"   当前: 使用初始状态")

        self.state = {
            "created_at": datetime.now().isoformat(),
            "completed_tasks": 0,
            "loaded_from_file": False
        }

    async def _save_state_async(self) -> None:
        """异步保存状态"""
        # 实际实现中应该写入文件或数据库
        pass


class MetricsAgent(RoutedAgent):
    """指标收集 Agent - 收集和统计状态"""

    def __init__(self, description: str = "Metrics Agent"):
        super().__init__(description)

        # 指标状态
        self.metrics = {
            "total_messages": 0,
            "total_tasks": 0,
            "success_rate": 1.0,
            "average_processing_time": 0.0,
            "peak_concurrent_tasks": 0,
        }

        # 详细指标
        self.task_history = []
        self.performance_samples = []

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务并收集指标"""

        start_time = datetime.now()

        # 更新消息计数
        self.metrics["total_messages"] += 1
        self.metrics["total_tasks"] += 1

        print(f"\n📊 [MetricsAgent] 处理任务")
        print(f"   总消息数: {self.metrics['total_messages']}")
        print(f"   总任务数: {self.metrics['total_tasks']}")

        # 模拟处理
        await asyncio.sleep(0.1)

        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()

        # 更新平均处理时间
        current_avg = self.metrics["average_processing_time"]
        n = self.metrics["total_tasks"]
        new_avg = ((current_avg * (n - 1)) + processing_time) / n
        self.metrics["average_processing_time"] = new_avg

        # 记录历史
        self.task_history.append({
            "task_id": message.task_id,
            "completed_at": datetime.now().isoformat(),
            "processing_time": processing_time
        })

        print(f"   平均处理时间: {new_avg:.3f}秒")

    @message_handler
    async def handle_metrics_query(self, message: StateQueryMessage, ctx: MessageContext) -> None:
        """查询指标"""

        print(f"\n📈 [MetricsAgent] 性能指标")
        print(f"   总消息: {self.metrics['total_messages']}")
        print(f"   总任务: {self.metrics['total_tasks']}")
        print(f"   成功率: {self.metrics['success_rate']:.1%}")
        print(f"   平均处理时间: {self.metrics['average_processing_time']:.3f}秒")
        print(f"   峰值并发: {self.metrics['peak_concurrent_tasks']}")


class StateSnapshotAgent(RoutedAgent):
    """状态快照 Agent - 支持状态回滚"""

    def __init__(self, description: str = "Snapshot Agent"):
        super().__init__(description)

        self.current_state = {}
        self.snapshots = {}  # snapshot_id -> state

    @message_handler
    async def handle_state_update(self, message: StateUpdateMessage, ctx: MessageContext) -> None:
        """更新状态"""

        self.current_state[message.key] = message.value
        print(f"\n✏️  [SnapshotAgent] 更新: {message.key} = {message.value}")

    @message_handler
    async def handle_create_snapshot(self, message: StateSnapshotMessage, ctx: MessageContext) -> None:
        """创建状态快照"""

        snapshot = self.current_state.copy()
        snapshot["_metadata"] = {
            "created_at": datetime.now().isoformat(),
            "snapshot_id": message.snapshot_id
        }

        self.snapshots[message.snapshot_id] = snapshot

        print(f"\n📸 [SnapshotAgent] 创建快照")
        print(f"   快照 ID: {message.snapshot_id}")
        print(f"   状态项: {len(self.current_state)}")

    @message_handler
    async def handle_restore_snapshot(self, message: StateSnapshotMessage, ctx: MessageContext) -> None:
        """从快照恢复状态"""

        if message.snapshot_id not in self.snapshots:
            print(f"\n❌ 快照不存在: {message.snapshot_id}")
            return

        snapshot = self.snapshots[message.snapshot_id]
        # 移除元数据
        state_data = {k: v for k, v in snapshot.items() if not k.startswith("_")}

        self.current_state = state_data.copy()

        print(f"\n♻️  [SnapshotAgent] 恢复快照")
        print(f"   快照 ID: {message.snapshot_id}")
        print(f"   恢复状态项: {len(self.current_state)}")


# ===== 演示函数 =====
async def demo_basic_state():
    """演示 1: 基本状态管理"""
    print_section("演示 1: 基本状态管理")

    runtime = SingleThreadedAgentRuntime()

    await StatefulAgent.register(runtime, "stateful", lambda: StatefulAgent("Agent1"))
    await runtime.add_subscription(TypeSubscription("state_ops", "stateful"))

    runtime.start()

    # 发送任务
    print("\n--- 发送任务 ---")
    for i in range(3):
        await runtime.publish_message(
            TaskMessage(f"task-{i+1}", {"data": f"test{i+1}"}),
            TopicId("state_ops", "default")
        )
        await asyncio.sleep(0.1)

    # 查询状态
    print("\n--- 查询状态 ---")
    await runtime.publish_message(
        StateQueryMessage("all"),
        TopicId("state_ops", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_state_updates():
    """演示 2: 状态更新操作"""
    print_section("演示 2: 状态更新操作")

    runtime = SingleThreadedAgentRuntime()

    await StatefulAgent.register(runtime, "updater", lambda: StatefulAgent("Updater"))
    await runtime.add_subscription(TypeSubscription("updates", "updater"))

    runtime.start()

    print("\n--- 执行状态更新 ---")

    # Set 操作
    await runtime.publish_message(
        StateUpdateMessage("counter", 0, "set"),
        TopicId("updates", "default")
    )

    # Increment 操作
    for _ in range(3):
        await runtime.publish_message(
            StateUpdateMessage("counter", None, "increment"),
            TopicId("updates", "default")
        )
        await asyncio.sleep(0.1)

    # Decrement 操作
    await runtime.publish_message(
        StateUpdateMessage("counter", None, "decrement"),
        TopicId("updates", "default")
    )

    # 查询结果
    await runtime.publish_message(
        StateQueryMessage("specific", "counter"),
        TopicId("updates", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_persistent_state():
    """演示 3: 持久化状态"""
    print_section("演示 3: 持久化状态")

    runtime = SingleThreadedAgentRuntime()

    await PersistentAgent.register(runtime, "persistent", lambda: PersistentAgent("PersistentAgent"))
    await runtime.add_subscription(TypeSubscription("persistent", "persistent"))

    runtime.start()

    print("\n--- 处理任务 ---")
    for i in range(3):
        await runtime.publish_message(
            TaskMessage(f"persist-{i+1}", {}),
            TopicId("persistent", "default")
        )
        await asyncio.sleep(0.1)

    # 创建快照
    await runtime.publish_message(
        StateSnapshotMessage("snapshot-1"),
        TopicId("persistent", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_metrics_collection():
    """演示 4: 指标收集"""
    print_section("演示 4: 性能指标收集")

    runtime = SingleThreadedAgentRuntime()

    await MetricsAgent.register(runtime, "metrics", lambda: MetricsAgent())
    await runtime.add_subscription(TypeSubscription("metrics", "metrics"))

    runtime.start()

    print("\n--- 处理多个任务收集指标 ---")
    for i in range(5):
        await runtime.publish_message(
            TaskMessage(f"metric-task-{i+1}", {}),
            TopicId("metrics", "default")
        )
        await asyncio.sleep(0.05)

    # 查询指标
    await runtime.publish_message(
        StateQueryMessage("all"),
        TopicId("metrics", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_state_snapshots():
    """演示 5: 状态快照和回滚"""
    print_section("演示 5: 状态快照和回滚")

    runtime = SingleThreadedAgentRuntime()

    await StateSnapshotAgent.register(runtime, "snapshooter", lambda: StateSnapshotAgent())
    await runtime.add_subscription(TypeSubscription("snapshots", "snapshooter"))

    runtime.start()

    print("\n--- 初始状态更新 ---")
    await runtime.publish_message(
        StateUpdateMessage("value1", 100, "set"),
        TopicId("snapshots", "default")
    )
    await runtime.publish_message(
        StateUpdateMessage("value2", 200, "set"),
        TopicId("snapshots", "default")
    )

    print("\n--- 创建快照 1 ---")
    await runtime.publish_message(
        StateSnapshotMessage("snapshot-1"),
        TopicId("snapshots", "default")
    )

    print("\n--- 修改状态 ---")
    await runtime.publish_message(
        StateUpdateMessage("value1", 999, "set"),
        TopicId("snapshots", "default")
    )
    await runtime.publish_message(
        StateUpdateMessage("value3", 300, "set"),
        TopicId("snapshots", "default")
    )

    print("\n--- 回滚到快照 1 ---")
    await runtime.publish_message(
        StateSnapshotMessage("snapshot-1"),
        TopicId("snapshots", "default")
    )
    # 注意: 这里应该发送 restore 消息，简化演示

    await runtime.stop_when_idle()
    runtime.stop()


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - Agent 状态管理                        ║
        ║           Managing Agent State                               ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本状态
        await demo_basic_state()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 状态更新
        await demo_state_updates()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 持久化
        await demo_persistent_state()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 指标
        await demo_metrics_collection()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 快照
        await demo_state_snapshots()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. Agent 可以维护内部状态")
        print("  2. 状态可以通过消息更新和查询")
        print("  3. 支持状态持久化和快照")
        print("  4. 可以收集性能指标")
        print("  5. 注意并发状态更新的问题")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

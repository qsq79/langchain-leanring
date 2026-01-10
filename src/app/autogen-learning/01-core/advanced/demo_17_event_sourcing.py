"""
Demo 17: 事件溯源 (Event Sourcing)

本演示展示如何:
1. 理解事件溯源的概念
2. 实现事件存储和重放
3. 基于事件重建状态
4. 实现快照和恢复
5. 应用事件溯源模式

运行方式:
    python demo_17_event_sourcing.py

前置要求:
    - 已完成 demo_08_agent_state.py
    - 理解状态管理和持久化

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/event-sourcing.html
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
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional
from datetime import datetime
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


# ===== 定义事件类型 =====
class EventType(str, Enum):
    """事件类型"""
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    ORDER_PLACED = "order_placed"
    ORDER_CANCELLED = "order_cancelled"
    PAYMENT_MADE = "payment_made"


@dataclass
class Event:
    """事件基类"""
    event_id: str
    event_type: EventType
    aggregate_id: str  # 聚合根 ID
    data: Dict[str, Any]
    timestamp: str
    version: int = 1

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Event':
        """从字典创建"""
        data['event_type'] = EventType(data['event_type'])
        return cls(**data)


@dataclass
class UserEvent(Event):
    """用户事件"""
    pass


@dataclass
class OrderEvent(Event):
    """订单事件"""
    pass


# ===== 定义命令 =====
@dataclass
class Command:
    """命令基类"""
    command_id: str
    aggregate_id: str
    command_type: str
    data: Dict[str, Any]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


# ===== 事件存储 =====
class EventStore:
    """事件存储 - 内存实现"""

    def __init__(self):
        self.events: List[Event] = []
        self.snapshots: Dict[str, Dict] = {}

    def append(self, event: Event) -> None:
        """追加事件"""
        self.events.append(event)
        print(f"  💾 事件已存储: {event.event_type.value} (ID: {event.event_id})")

    def get_events(self, aggregate_id: str) -> List[Event]:
        """获取聚合的所有事件"""
        return [e for e in self.events if e.aggregate_id == aggregate_id]

    def save_snapshot(self, aggregate_id: str, state: Dict) -> None:
        """保存快照"""
        snapshot = {
            "aggregate_id": aggregate_id,
            "state": state,
            "timestamp": datetime.now().isoformat(),
            "event_count": len([e for e in self.events if e.aggregate_id == aggregate_id])
        }
        self.snapshots[aggregate_id] = snapshot
        print(f"  📸 快照已保存: {aggregate_id}")

    def get_snapshot(self, aggregate_id: str) -> Optional[Dict]:
        """获取快照"""
        return self.snapshots.get(aggregate_id)

    def clear(self) -> None:
        """清空事件存储"""
        self.events.clear()
        self.snapshots.clear()
        print("  🗑️  事件存储已清空")


# ===== 聚合根 =====
class AggregateRoot:
    """聚合根基类"""

    def __init__(self, aggregate_id: str, event_store: EventStore):
        self.aggregate_id = aggregate_id
        self.event_store = event_store
        self.version = 0
        self._changes: List[Event] = []

    def apply_event(self, event: Event) -> None:
        """应用事件"""
        self.version += 1
        event.version = self.version
        self._apply(event)
        self._changes.append(event)

    def _apply(self, event: Event) -> None:
        """应用事件的具体逻辑（子类实现）"""
        raise NotImplementedError

    def save_changes(self) -> None:
        """保存未提交的变更"""
        for event in self._changes:
            self.event_store.append(event)
        self._changes.clear()

    def load_from_history(self) -> None:
        """从历史事件重建状态"""
        events = self.event_store.get_events(self.aggregate_id)
        print(f"\n  📚 加载 {len(events)} 个历史事件...")
        for event in events:
            self.version = event.version
            self._apply(event)
        print(f"  ✅ 状态已重建 (版本: {self.version})")

    def load_from_snapshot(self) -> bool:
        """从快照加载"""
        snapshot = self.event_store.get_snapshot(self.aggregate_id)
        if snapshot:
            print(f"\n  📸 从快照加载...")
            self._load_from_snapshot_data(snapshot['state'])
            self.version = snapshot['event_count']
            print(f"  ✅ 快照已加载 (版本: {self.version})")
            return True
        return False


class User(AggregateRoot):
    """用户聚合根"""

    def __init__(self, user_id: str, event_store: EventStore):
        super().__init__(user_id, event_store)
        self.username = ""
        self.email = ""
        self.is_active = False
        self.login_count = 0
        self.orders = []

    def _apply(self, event: Event) -> None:
        """应用事件"""
        if event.event_type == EventType.USER_CREATED:
            self.username = event.data.get('username', '')
            self.email = event.data.get('email', '')
            self.is_active = True
        elif event.event_type == EventType.USER_UPDATED:
            if 'username' in event.data:
                self.username = event.data['username']
            if 'email' in event.data:
                self.email = event.data['email']
        elif event.event_type == EventType.USER_DELETED:
            self.is_active = False
        elif event.event_type == EventType.USER_LOGIN:
            self.login_count += 1
        elif event.event_type == EventType.USER_LOGOUT:
            pass  # 登出不需要更新状态
        elif event.event_type == EventType.ORDER_PLACED:
            self.orders.append(event.data.get('order_id'))
        elif event.event_type == EventType.ORDER_CANCELLED:
            order_id = event.data.get('order_id')
            if order_id in self.orders:
                self.orders.remove(order_id)

    def _load_from_snapshot_data(self, data: Dict) -> None:
        """从快照数据加载"""
        self.username = data.get('username', '')
        self.email = data.get('email', '')
        self.is_active = data.get('is_active', False)
        self.login_count = data.get('login_count', 0)
        self.orders = data.get('orders', []).copy()

    def to_snapshot_data(self) -> Dict:
        """转换为快照数据"""
        return {
            'username': self.username,
            'email': self.email,
            'is_active': self.is_active,
            'login_count': self.login_count,
            'orders': self.orders.copy()
        }


# ===== 定义 Agent =====
class EventSourcingAgent(RoutedAgent):
    """事件溯源 Agent - 管理聚合根"""

    def __init__(self, event_store: EventStore, description: str = "Event Sourcing Agent"):
        super().__init__(description)
        self.event_store = event_store
        self.users: Dict[str, User] = {}  # user_id -> User

    @message_handler
    async def handle_command(self, command: Command, ctx: MessageContext) -> None:
        """处理命令并生成事件"""

        print(f"\n  📨 收到命令: {command.command_type}")
        print(f"     聚合 ID: {command.aggregate_id}")

        # 获取或创建聚合根
        user = self.users.get(command.aggregate_id)
        if user is None:
            user = User(command.aggregate_id, self.event_store)
            self.users[command.aggregate_id] = user

        # 处理命令并生成事件
        event = await self._process_command(command, user)
        if event:
            user.apply_event(event)
            user.save_changes()
            print(f"  ✅ 事件已生成并存储: {event.event_type.value}")

    async def _process_command(self, command: Command, user: User) -> Optional[Event]:
        """处理命令，生成事件"""

        import uuid

        if command.command_type == "create_user":
            return Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_CREATED,
                aggregate_id=command.aggregate_id,
                data=command.data,
                timestamp=datetime.now().isoformat()
            )

        elif command.command_type == "update_user":
            return Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_UPDATED,
                aggregate_id=command.aggregate_id,
                data=command.data,
                timestamp=datetime.now().isoformat()
            )

        elif command.command_type == "login":
            return Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.USER_LOGIN,
                aggregate_id=command.aggregate_id,
                data={},
                timestamp=datetime.now().isoformat()
            )

        elif command.command_type == "place_order":
            return Event(
                event_id=str(uuid.uuid4()),
                event_type=EventType.ORDER_PLACED,
                aggregate_id=command.aggregate_id,
                data=command.data,
                timestamp=datetime.now().isoformat()
            )

        return None

    @message_handler
    async def handle_replay(self, message: str, ctx: MessageContext) -> None:
        """重放事件"""

        print(f"\n  🔄 重放所有事件...")

        # 清空当前状态
        self.users.clear()

        # 获取所有唯一的聚合 ID
        aggregate_ids = set(e.aggregate_id for e in self.event_store.events)

        for aggregate_id in aggregate_ids:
            user = User(aggregate_id, self.event_store)
            user.load_from_history()
            self.users[aggregate_id] = user

        print(f"  ✅ 重放完成，共 {len(self.users)} 个聚合")

    @message_handler
    async def handle_create_snapshot(self, message: str, ctx: MessageContext) -> None:
        """创建快照"""

        print(f"\n  📸 创建快照...")

        for user_id, user in self.users.items():
            snapshot_data = user.to_snapshot_data()
            self.event_store.save_snapshot(user_id, snapshot_data)

        print(f"  ✅ 已为 {len(self.users)} 个用户创建快照")

    @message_handler
    async def handle_query_state(self, message: str, ctx: MessageContext) -> None:
        """查询状态"""

        print(f"\n  📊 当前状态:")
        for user_id, user in self.users.items():
            print(f"\n  👤 用户: {user.username} (ID: {user_id})")
            print(f"     邮箱: {user.email}")
            print(f"     状态: {'活跃' if user.is_active else '非活跃'}")
            print(f"     登录次数: {user.login_count}")
            print(f"     订单数: {len(user.orders)}")
            if user.orders:
                print(f"     订单: {', '.join(user.orders)}")


# ===== 演示函数 =====
async def demo_basic_event_sourcing():
    """演示 1: 基本的事件溯源"""
    print_section("演示 1: 基本的事件溯源流程")

    event_store = EventStore()
    runtime = SingleThreadedAgentRuntime()

    await EventSourcingAgent.register(
        runtime,
        "event_sourcing",
        lambda: EventSourcingAgent(event_store)
    )
    await runtime.add_subscription(TypeSubscription("commands", "event_sourcing"))

    runtime.start()

    import uuid

    print("\n--- 创建用户 ---")
    await runtime.publish_message(
        Command(
            command_id=str(uuid.uuid4()),
            aggregate_id="user-001",
            command_type="create_user",
            data={"username": "张三", "email": "zhangsan@example.com"}
        ),
        TopicId("commands", "default")
    )

    await asyncio.sleep(0.2)

    print("\n--- 用户登录 ---")
    await runtime.publish_message(
        Command(
            command_id=str(uuid.uuid4()),
            aggregate_id="user-001",
            command_type="login",
            data={}
        ),
        TopicId("commands", "default")
    )

    await asyncio.sleep(0.2)

    print("\n--- 下单 ---")
    await runtime.publish_message(
        Command(
            command_id=str(uuid.uuid4()),
            aggregate_id="user-001",
            command_type="place_order",
            data={"order_id": "ORD-001", "amount": 100}
        ),
        TopicId("commands", "default")
    )

    await asyncio.sleep(0.2)

    print("\n--- 查询状态 ---")
    await runtime.publish_message(
        "query_state",
        TopicId("commands", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 每个命令生成一个事件")
    print("  - 事件被存储到事件存储")
    print("  - 当前状态通过应用事件得到")


async def demo_event_replay():
    """演示 2: 事件重放"""
    print_section("演示 2: 事件重放和状态重建")

    event_store = EventStore()
    runtime = SingleThreadedAgentRuntime()

    agent = EventSourcingAgent(event_store)
    await EventSourcingAgent.register(runtime, "event_sourcing", lambda: agent)
    await runtime.add_subscription(TypeSubscription("commands", "event_sourcing"))

    runtime.start()

    import uuid

    print("\n--- 阶段 1: 生成事件 ---")
    for i in range(3):
        await runtime.publish_message(
            Command(
                command_id=str(uuid.uuid4()),
                aggregate_id="user-001",
                command_type="login",
                data={}
            ),
            TopicId("commands", "default")
        )
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.3)

    print(f"\n📊 事件存储中的事件数: {len(event_store.events)}")

    print("\n--- 阶段 2: 清空当前状态 ---")
    agent.users.clear()
    print("  当前状态已清空")

    print("\n--- 阶段 3: 重放事件重建状态 ---")
    await runtime.publish_message(
        "replay",
        TopicId("commands", "default")
    )

    await asyncio.sleep(0.3)

    print("\n--- 阶段 4: 查询重建后的状态 ---")
    await runtime.publish_message(
        "query_state",
        TopicId("commands", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 事件是唯一的事实来源")
    print("  - 状态可以通过重放事件重建")
    print("  - 这提供了完整的审计轨迹")


async def demo_snapshot_and_restore():
    """演示 3: 快照和恢复"""
    print_section("演示 3: 快照和状态恢复")

    event_store = EventStore()
    runtime = SingleThreadedAgentRuntime()

    agent = EventSourcingAgent(event_store)
    await EventSourcingAgent.register(runtime, "event_sourcing", lambda: agent)
    await runtime.add_subscription(TypeSubscription("commands", "event_sourcing"))

    runtime.start()

    import uuid

    print("\n--- 阶段 1: 创建用户并生成事件 ---")
    await runtime.publish_message(
        Command(
            command_id=str(uuid.uuid4()),
            aggregate_id="user-001",
            command_type="create_user",
            data={"username": "李四", "email": "lisi@example.com"}
        ),
        TopicId("commands", "default")
    )

    for i in range(5):
        await runtime.publish_message(
            Command(
                command_id=str(uuid.uuid4()),
                aggregate_id="user-001",
                command_type="login",
                data={}
            ),
            TopicId("commands", "default")
        )
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.3)

    print(f"\n📊 当前事件数: {len(event_store.events)}")

    print("\n--- 阶段 2: 创建快照 ---")
    await runtime.publish_message(
        "create_snapshot",
        TopicId("commands", "default")
    )

    await asyncio.sleep(0.3)

    print("\n--- 阶段 3: 清空状态 ---")
    agent.users.clear()
    print("  状态已清空")

    print("\n--- 阶段 4: 从快照恢复 ---")
    for user_id, snapshot in event_store.snapshots.items():
        user = User(user_id, event_store)
        if user.load_from_snapshot():
            agent.users[user_id] = user
            print(f"  ✅ 用户 {user_id} 已从快照恢复")

    print("\n--- 阶段 5: 查询恢复后的状态 ---")
    await runtime.publish_message(
        "query_state",
        TopicId("commands", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 快照保存特定时间点的状态")
    print("  - 加载快照后，只重放快照之后的事件")
    print("  - 这可以加速大聚合根的加载")


async def demo_multiple_aggregates():
    """演示 4: 多个聚合"""
    print_section("演示 4: 管理多个聚合")

    event_store = EventStore()
    runtime = SingleThreadedAgentRuntime()

    await EventSourcingAgent.register(
        runtime,
        "event_sourcing",
        lambda: EventSourcingAgent(event_store)
    )
    await runtime.add_subscription(TypeSubscription("commands", "event_sourcing"))

    runtime.start()

    import uuid

    print("\n--- 创建多个用户 ---")
    users_data = [
        ("user-001", {"username": "张三", "email": "zhangsan@example.com"}),
        ("user-002", {"username": "李四", "email": "lisi@example.com"}),
        ("user-003", {"username": "王五", "email": "wangwu@example.com"}),
    ]

    for user_id, data in users_data:
        await runtime.publish_message(
            Command(
                command_id=str(uuid.uuid4()),
                aggregate_id=user_id,
                command_type="create_user",
                data=data
            ),
            TopicId("commands", "default")
        )
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.3)

    print("\n--- 为不同用户执行操作 ---")
    for i, user_id in enumerate(["user-001", "user-002", "user-001", "user-003"]):
        await runtime.publish_message(
            Command(
                command_id=str(uuid.uuid4()),
                aggregate_id=user_id,
                command_type="login",
                data={}
            ),
            TopicId("commands", "default")
        )
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.3)

    print("\n--- 查询所有用户状态 ---")
    await runtime.publish_message(
        "query_state",
        TopicId("commands", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 事件存储可以管理多个聚合")
    print("  - 每个聚合有独立的事件流")
    print("  - 聚合之间保持隔离")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 事件溯源 (Event Sourcing)         ║
        ║           Events as the Single Source of Truth                   ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本的事件溯源
        await demo_basic_event_sourcing()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 事件重放
        await demo_event_replay()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 快照和恢复
        await demo_snapshot_and_restore()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 多个聚合
        await demo_multiple_aggregates()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")
        print("\n下一步:")
        print("  1. 查看 demo_18_distributed_runtime.py 了解分布式运行时")
        print("  2. 查看文档了解更复杂的事件溯源场景")
        print("  3. 实际应用中考虑事件版本和迁移")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
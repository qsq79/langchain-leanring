"""
Demo 04: 消息类型定义和验证

本演示展示如何:
1. 定义结构化的消息类型
2. 使用 dataclass 定义消息
3. 实现消息验证
4. 处理复杂消息结构
5. 实现消息序列化

运行方式:
    python demo_04_message_types.py

前置要求:
    - 已完成 demo_01_quickstart.py
    - 理解基本的 Python 类型系统

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
import json
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, Literal
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


# ===== 消息类型定义 =====

class MessageType(str, Enum):
    """消息类型枚举"""
    TEXT = "text"
    COMMAND = "command"
    EVENT = "event"
    RESPONSE = "response"
    ERROR = "error"


@dataclass
class BaseMessage:
    """消息基类"""
    message_type: MessageType
    timestamp: str
    source: str

    def to_dict(self) -> dict:
        """转换为字典"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为 JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class TextMessage(BaseMessage):
    """文本消息"""
    content: str
    recipient: Optional[str] = None

    def __str__(self):
        return f"[{self.source}] {self.content}"


@dataclass
class CommandMessage(BaseMessage):
    """命令消息"""
    command: str
    args: Dict[str, Any]
    timeout: int = 30

    def validate(self) -> bool:
        """验证命令格式"""
        return bool(self.command) and isinstance(self.args, dict)


@dataclass
class EventMessage(BaseMessage):
    """事件消息"""
    event_type: str
    event_data: Dict[str, Any]
    priority: Literal["low", "normal", "high", "urgent"] = "normal"

    def get_urgency_score(self) -> int:
        """获取紧急程度分数"""
        scores = {"low": 1, "normal": 2, "high": 3, "urgent": 4}
        return scores.get(self.priority, 2)


@dataclass
class ResponseMessage(BaseMessage):
    """响应消息"""
    request_id: str
    success: bool
    result: Any
    error: Optional[str] = None


@dataclass
class TaskMessage(BaseMessage):
    """任务消息"""
    task_id: str
    task_type: str
    payload: Dict[str, Any]
    dependencies: List[str] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


@dataclass
class OrderMessage(BaseMessage):
    """订单消息 - 复杂结构示例"""
    order_id: str
    customer_id: str
    items: List[Dict[str, Any]]
    total_amount: float
    shipping_address: Dict[str, str]
    payment_info: Dict[str, str]

    def validate(self) -> tuple[bool, Optional[str]]:
        """验证订单消息"""
        if not self.order_id:
            return False, "订单 ID 不能为空"
        if not self.customer_id:
            return False, "客户 ID 不能为空"
        if not self.items:
            return False, "订单商品不能为空"
        if self.total_amount <= 0:
            return False, "订单金额必须大于 0"
        return True, None


# ===== 消息验证器 =====
class MessageValidator:
    """消息验证器"""

    @staticmethod
    def validate_message(message: Any) -> tuple[bool, Optional[str]]:
        """验证消息"""
        # 检查是否是已知消息类型
        if isinstance(message, BaseMessage):
            return True, None

        # 检查是否有特定验证方法
        if hasattr(message, 'validate'):
            return message.validate()

        return False, f"未知消息类型: {type(message)}"


# ===== 定义 Agent =====
class MessageHandlerAgent(RoutedAgent):
    """消息处理 Agent - 演示不同消息类型的处理"""

    def __init__(self, description: str = "Message Handler"):
        super().__init__(description)
        self.stats = {
            "text": 0,
            "command": 0,
            "event": 0,
            "response": 0,
            "task": 0,
            "order": 0,
        }

    @message_handler
    async def handle_text_message(self, message: TextMessage, ctx: MessageContext) -> None:
        """处理文本消息"""
        self.stats["text"] += 1
        print(f"\n💬 收到文本消息 #{self.stats['text']}")
        print(f"   内容: {message.content}")
        print(f"   来源: {message.source}")
        print(f"   时间: {message.timestamp}")

    @message_handler
    async def handle_command_message(self, message: CommandMessage, ctx: MessageContext) -> None:
        """处理命令消息"""
        self.stats["command"] += 1

        # 验证命令
        is_valid, error = message.validate()
        if not is_valid:
            print(f"❌ 无效的命令: {error}")
            return

        print(f"\n🎯 执行命令 #{self.stats['command']}")
        print(f"   命令: {message.command}")
        print(f"   参数: {json.dumps(message.args, ensure_ascii=False)}")
        print(f"   超时: {message.timeout}秒")
        print(f"   ✅ 命令已执行")

    @message_handler
    async def handle_event_message(self, message: EventMessage, ctx: MessageContext) -> None:
        """处理事件消息"""
        self.stats["event"] += 1

        urgency = message.get_urgency_score()
        urgency_icons = {1: "🟢", 2: "🟡", 3: "🟠", 4: "🔴"}

        print(f"\n⚡ 收到事件 #{self.stats['event']}")
        print(f"   类型: {message.event_type}")
        print(f"   优先级: {message.priority} {urgency_icons.get(urgency, '')}")
        print(f"   数据: {json.dumps(message.event_data, ensure_ascii=False)}")

    @message_handler
    async def handle_response_message(self, message: ResponseMessage, ctx: MessageContext) -> None:
        """处理响应消息"""
        self.stats["response"] += 1

        status = "✅" if message.success else "❌"
        print(f"\n📨 收到响应 #{self.stats['response']}")
        print(f"   请求 ID: {message.request_id}")
        print(f"   状态: {status}")
        if message.success:
            print(f"   结果: {message.result}")
        else:
            print(f"   错误: {message.error}")

    @message_handler
    async def handle_task_message(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务消息"""
        self.stats["task"] += 1

        print(f"\n📋 收到任务 #{self.stats['task']}")
        print(f"   任务 ID: {message.task_id}")
        print(f"   类型: {message.task_type}")
        print(f"   依赖: {message.dependencies or '无'}")
        print(f"   负载: {json.dumps(message.payload, ensure_ascii=False)}")

    @message_handler
    async def handle_order_message(self, message: OrderMessage, ctx: MessageContext) -> None:
        """处理订单消息"""
        self.stats["order"] += 1

        # 验证订单
        is_valid, error = message.validate()
        if not is_valid:
            print(f"❌ 订单验证失败: {error}")
            return

        print(f"\n🛒 收到订单 #{self.stats['order']}")
        print(f"   订单 ID: {message.order_id}")
        print(f"   客户: {message.customer_id}")
        print(f"   金额: ¥{message.total_amount:.2f}")
        print(f"   商品数: {len(message.items)}")
        print(f"   地址: {message.shipping_address['city']}, {message.shipping_address['address']}")
        print(f"   ✅ 订单已处理")

    async def print_stats(self):
        """打印统计信息"""
        print(f"\n📊 消息统计:")
        total = sum(self.stats.values())
        for msg_type, count in self.stats.items():
            if count > 0:
                percentage = (count / total * 100) if total > 0 else 0
                print(f"   {msg_type}: {count} ({percentage:.1f}%)")


class MessageRouterAgent(RoutedAgent):
    """消息路由 Agent - 演示消息分发"""

    @message_handler
    async def route_message(self, message: BaseMessage, ctx: MessageContext) -> None:
        """路由消息到不同的处理器"""

        # 根据消息类型路由
        if message.message_type == MessageType.TEXT:
            print(f"📬 路由到文本处理器")
        elif message.message_type == MessageType.COMMAND:
            print(f"📬 路由到命令执行器")
        elif message.message_type == MessageType.EVENT:
            print(f"📬 路由到事件处理器")
        else:
            print(f"📬 路由到默认处理器")


# ===== 演示函数 =====
async def demo_basic_message_types():
    """演示 1: 基本消息类型"""
    print_section("演示 1: 基本消息类型")

    runtime = SingleThreadedAgentRuntime()
    await MessageHandlerAgent.register(runtime, "handler", lambda: MessageHandlerAgent())
    await runtime.add_subscription(TypeSubscription("messages", "handler"))
    runtime.start()

    # 创建不同类型的消息
    from datetime import datetime

    messages = [
        TextMessage(
            message_type=MessageType.TEXT,
            timestamp=datetime.now().isoformat(),
            source="user",
            content="Hello, AutoGen!"
        ),
        CommandMessage(
            message_type=MessageType.COMMAND,
            timestamp=datetime.now().isoformat(),
            source="system",
            command="restart",
            args={"force": True, "timeout": 60}
        ),
        EventMessage(
            message_type=MessageType.EVENT,
            timestamp=datetime.now().isoformat(),
            source="sensor",
            event_type="temperature_alert",
            event_data={"temperature": 85, "threshold": 80},
            priority="high"
        ),
    ]

    print("\n--- 发送不同类型的消息 ---")
    for msg in messages:
        topic_type = f"msg_{msg.message_type.value}"
        await runtime.publish_message(msg, TopicId("messages", "default"))
        await asyncio.sleep(0.1)

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_complex_messages():
    """演示 2: 复杂消息结构"""
    print_section("演示 2: 复杂消息结构")

    runtime = SingleThreadedAgentRuntime()
    await MessageHandlerAgent.register(runtime, "handler", lambda: MessageHandlerAgent())
    await runtime.add_subscription(TypeSubscription("complex", "handler"))
    runtime.start()

    from datetime import datetime

    # 任务消息
    task = TaskMessage(
        message_type=MessageType.TEXT,
        timestamp=datetime.now().isoformat(),
        source="scheduler",
        task_id="TASK-2025-001",
        task_type="data_processing",
        payload={
            "input_file": "/data/input.csv",
            "output_format": "json",
            "batch_size": 1000
        },
        dependencies=["TASK-2025-000"]
    )

    # 订单消息
    order = OrderMessage(
        message_type=MessageType.EVENT,
        timestamp=datetime.now().isoformat(),
        source="ecommerce",
        order_id="ORD-2025-001",
        customer_id="CUST-001",
        items=[
            {"product_id": "P001", "name": "iPhone 15 Pro", "quantity": 1, "price": 7999},
            {"product_id": "P002", "name": "AirPods Pro", "quantity": 2, "price": 1999}
        ],
        total_amount=9997.0,
        shipping_address={
            "name": "张三",
            "phone": "13800138000",
            "city": "北京市",
            "address": "朝阳区xxx街道xxx号"
        },
        payment_info={
            "method": "wechat_pay",
            "transaction_id": "TXN-2025-001"
        }
    )

    print("\n--- 发送复杂消息 ---")
    await runtime.publish_message(task, TopicId("complex", "default"))
    await asyncio.sleep(0.2)

    await runtime.publish_message(order, TopicId("complex", "default"))
    await asyncio.sleep(0.2)

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_message_validation():
    """演示 3: 消息验证"""
    print_section("演示 3: 消息验证")

    runtime = SingleThreadedAgentRuntime()
    await MessageHandlerAgent.register(runtime, "validator", lambda: MessageHandlerAgent())
    await runtime.add_subscription(TypeSubscription("validation", "validator"))
    runtime.start()

    from datetime import datetime

    # 有效消息
    valid_order = OrderMessage(
        message_type=MessageType.EVENT,
        timestamp=datetime.now().isoformat(),
        source="store",
        order_id="ORD-001",
        customer_id="CUST-001",
        items=[{"product": "item1", "qty": 1}],
        total_amount=100.0,
        shipping_address={"city": "北京"},
        payment_info={"method": "alipay"}
    )

    # 无效消息
    invalid_order = OrderMessage(
        message_type=MessageType.EVENT,
        timestamp=datetime.now().isoformat(),
        source="store",
        order_id="",  # 空订单 ID
        customer_id="CUST-002",
        items=[],
        total_amount=-50,  # 负金额
        shipping_address={},
        payment_info={}
    )

    print("\n--- 发送有效消息 ---")
    await runtime.publish_message(valid_order, TopicId("validation", "valid"))
    await asyncio.sleep(0.1)

    print("\n--- 发送无效消息 ---")
    await runtime.publish_message(invalid_order, TopicId("validation", "invalid"))
    await asyncio.sleep(0.1)

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_message_serialization():
    """演示 4: 消息序列化"""
    print_section("演示 4: 消息序列化")

    from datetime import datetime

    message = TextMessage(
        message_type=MessageType.TEXT,
        timestamp=datetime.now().isoformat(),
        source="user",
        content="Hello, AutoGen!"
    )

    print("\n--- 原始消息 ---")
    print(f"   类型: {type(message)}")
    print(f"   内容: {message}")

    print("\n--- 转换为字典 ---")
    msg_dict = message.to_dict()
    print(f"   {json.dumps(msg_dict, ensure_ascii=False, indent=2)}")

    print("\n--- 转换为 JSON ---")
    msg_json = message.to_json()
    print(f"   {msg_json}")

    print("\n--- 从 JSON 反序列化 ---")
    restored = TextMessage(**json.loads(msg_json))
    print(f"   内容: {restored.content}")
    print(f"   来源: {restored.source}")

    print("\n✅ 消息可以安全地序列化和反序列化")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 消息类型定义和验证                     ║
        ║           Structured Message Types                           ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本消息类型
        await demo_basic_message_types()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 复杂消息
        await demo_complex_messages()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 消息验证
        await demo_message_validation()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 序列化
        await demo_message_serialization()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. 使用 dataclass 定义结构化消息")
        print("  2. 消息应该有明确的类型和用途")
        print("  3. 实现消息验证确保数据完整性")
        print("  4. 支持消息序列化用于存储和传输")
        print("  5. Agent 根据 @message_handler 自动路由消息")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

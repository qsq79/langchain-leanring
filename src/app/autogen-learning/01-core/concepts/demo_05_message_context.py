"""
Demo 05: 消息上下文 (MessageContext) 深入解析

本演示展示如何:
1. 理解 MessageContext 的作用
2. 访问消息的元数据
3. 使用 topic_id 进行消息路由
4. 实现 request-response 模式
5. 追踪消息链路

运行方式:
    python demo_05_message_context.py

前置要求:
    - 已完成 demo_01_quickstart.py
    - 已完成 demo_02_topic_subscription.py
    - 理解 Topic 和 Subscription 概念

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
from datetime import datetime

from autogen_core import (
    AgentId,
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
class RequestMessage:
    """请求消息"""
    request_id: str
    query: str
    sender: str
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class ResponseMessage:
    """响应消息"""
    request_id: str
    answer: str
    responder: str
    success: bool
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TracedMessage:
    """带追踪信息的消息"""
    content: str
    trace_id: str
    parent_id: Optional[str] = None
    metadata: dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


# ===== 定义 Agent =====
class ContextAwareAgent(RoutedAgent):
    """上下文感知 Agent - 演示如何使用 MessageContext"""

    def __init__(self, description: str = "Context Aware Agent"):
        super().__init__(description)
        self.message_log = []

    @message_handler
    async def handle_request(self, message: RequestMessage, ctx: MessageContext) -> None:
        """处理请求，并记录上下文信息"""

        # 记录消息和上下文
        log_entry = {
            "message": message,
            "topic_id": ctx.topic_id,
            "sender_id": ctx.sender_id,
            "is_reply": ctx.is_reply,
        }
        self.message_log.append(log_entry)

        print(f"\n📨 [{self.id.key}] 收到请求")
        print(f"   请求 ID: {message.request_id}")
        print(f"   查询内容: {message.query}")
        print(f"   发送者: {message.sender}")

        # 打印上下文信息
        print(f"\n   📍 消息上下文:")
        print(f"      Topic ID: {ctx.topic_id}")
        print(f"      Topic Type: {ctx.topic_id.type if ctx.topic_id else 'N/A'}")
        print(f"      Topic Source: {ctx.topic_id.source if ctx.topic_id else 'N/A'}")
        print(f"      Sender ID: {ctx.sender_id}")
        print(f"      Is Reply: {ctx.is_reply}")

        # 发送响应到同一个 topic
        if ctx.topic_id:
            response = ResponseMessage(
                request_id=message.request_id,
                answer=f"回答: {message.query}",
                responder=str(self.id.key),
                success=True
            )

            print(f"\n   📤 发送响应到 topic: {ctx.topic_id}")
            await self.publish_message(response, ctx.topic_id)

    @message_handler
    async def handle_response(self, message: ResponseMessage, ctx: MessageContext) -> None:
        """处理响应消息"""

        print(f"\n✉️  [{self.id.key}] 收到响应")
        print(f"   请求 ID: {message.request_id}")
        print(f"   回答: {message.answer}")
        print(f"   响应者: {message.responder}")
        print(f"   状态: {'成功' if message.success else '失败'}")

        print(f"\n   📍 上下文信息:")
        print(f"      这是回复: {ctx.is_reply}")
        print(f"      Sender ID: {ctx.sender_id}")


class TraceAgent(RoutedAgent):
    """消息追踪 Agent - 演示消息链路追踪"""

    def __init__(self, description: str = "Trace Agent"):
        super().__init__(description)
        self.trace_history = {}

    @message_handler
    async def handle_traced_message(self, message: TracedMessage, ctx: MessageContext) -> None:
        """处理带追踪信息的消息"""

        # 记录追踪信息
        trace_info = {
            "trace_id": message.trace_id,
            "parent_id": message.parent_id,
            "topic_id": str(ctx.topic_id) if ctx.topic_id else None,
            "sender_id": str(ctx.sender_id) if ctx.sender_id else None,
            "current_agent": str(self.id),
            "timestamp": datetime.now().isoformat(),
        }

        if message.trace_id not in self.trace_history:
            self.trace_history[message.trace_id] = []

        self.trace_history[message.trace_id].append(trace_info)

        # 打印追踪链路
        print(f"\n🔗 消息追踪链路:")
        print(f"   Trace ID: {message.trace_id}")
        print(f"   Parent ID: {message.parent_id or 'None (根消息)'}")
        print(f"   当前位置: {self.id.key}")
        print(f"   来源 Topic: {ctx.topic_id}")
        print(f"   发送者: {ctx.sender_id}")

        # 打印完整链路
        history = self.trace_history[message.trace_id]
        print(f"\n   📍 完整链路 ({len(history)} 个节点):")
        for i, node in enumerate(history, 1):
            print(f"      {i}. {node['current_agent']} "
                  f"(from: {node['sender_id']}, "
                  f"topic: {node['topic_id']})")


class RequestResponseAgent(RoutedAgent):
    """请求-响应 Agent - 演示双向通信"""

    def __init__(self, description: str = "Request-Response Agent"):
        super().__init__(description)
        self.pending_requests = {}

    @message_handler
    async def handle_request(self, message: RequestMessage, ctx: MessageContext) -> None:
        """处理请求并发送响应"""

        print(f"\n📨 [{self.id.key}] 处理请求")
        print(f"   请求: {message.query}")
        print(f"   来自: {ctx.sender_id}")
        print(f"   Topic: {ctx.topic_id}")

        # 模拟处理
        await asyncio.sleep(0.1)

        # 发送响应回原 topic
        if ctx.topic_id:
            response = ResponseMessage(
                request_id=message.request_id,
                answer=f"处理结果: {message.query}",
                responder=str(self.id.key),
                success=True
            )

            print(f"\n   📤 发送响应...")
            await self.publish_message(response, ctx.topic_id)

    @message_handler
    async def handle_response(self, message: ResponseMessage, ctx: MessageContext) -> None:
        """处理响应"""

        print(f"\n✅ [{self.id.key}] 收到响应")
        print(f"   请求 ID: {message.request_id}")
        print(f"   结果: {message.answer}")
        print(f"   来自: {ctx.sender_id}")

        # 标记请求完成
        self.pending_requests[message.request_id] = message


class RoutingAgent(RoutedAgent):
    """路由 Agent - 演示基于上下文的路由决策"""

    @message_handler
    async def route_message(self, message: RequestMessage, ctx: MessageContext) -> None:
        """根据上下文路由消息"""

        print(f"\n🔀 [{self.id.key}] 路由决策")

        # 检查上下文信息
        if ctx.is_reply:
            print(f"   决策: 这是回复消息，转发给响应处理器")
        else:
            print(f"   决策: 这是新请求，转发给请求处理器")

        # 根据 topic source 决定
        if ctx.topic_id and ctx.topic_id.source == "urgent":
            print(f"   ⚠️  紧急消息，优先处理")
        else:
            print(f"   📋 普通消息，正常处理")

        # 打印完整上下文
        print(f"\n   📍 完整上下文:")
        print(f"      Topic: {ctx.topic_id}")
        print(f"      Sender: {ctx.sender_id}")
        print(f"      Is Reply: {ctx.is_reply}")


# ===== 演示函数 =====
async def demo_basic_context():
    """演示 1: 基本的上下文信息"""
    print_section("演示 1: 基本的 MessageContext 信息")

    runtime = SingleThreadedAgentRuntime()

    await ContextAwareAgent.register(runtime, "context_agent", lambda: ContextAwareAgent())
    await runtime.add_subscription(TypeSubscription("requests", "context_agent"))

    runtime.start()

    print("\n--- 发送请求消息 ---")
    request = RequestMessage(
        request_id="REQ-001",
        query="什么是 AutoGen?",
        sender="user"
    )

    await runtime.publish_message(request, TopicId("requests", "default"))

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_request_response():
    """演示 2: 请求-响应模式"""
    print_section("演示 2: 请求-响应模式")

    runtime = SingleThreadedAgentRuntime()

    await RequestResponseAgent.register(runtime, "rr_agent", lambda: RequestResponseAgent())
    await runtime.add_subscription(TypeSubscription("rr_topic", "rr_agent"))

    runtime.start()

    print("\n--- 发送请求 ---")
    request = RequestMessage(
        request_id="REQ-002",
        query="计算 2 + 2",
        sender="client"
    )

    await runtime.publish_message(request, TopicId("rr_topic", "session_1"))

    print("\n--- 等待响应 ---")
    await asyncio.sleep(0.5)

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  1. 请求发送到 topic")
    print("  2. Agent 处理请求")
    print("  3. 响应发送回同一个 topic")
    print("  4. 请求-响应配对通过 request_id")


async def demo_message_tracing():
    """演示 3: 消息链路追踪"""
    print_section("演示 3: 消息链路追踪")

    runtime = SingleThreadedAgentRuntime()

    await TraceAgent.register(runtime, "tracer", lambda: TraceAgent())
    await runtime.add_subscription(TypeSubscription("trace", "tracer"))

    runtime.start()

    print("\n--- 发送根消息 ---")
    root_msg = TracedMessage(
        content="根消息",
        trace_id="TRACE-001",
        parent_id=None
    )

    await runtime.publish_message(root_msg, TopicId("trace", "step1"))
    await asyncio.sleep(0.2)

    print("\n--- 发送子消息 ---")
    child_msg = TracedMessage(
        content="子消息",
        trace_id="TRACE-002",
        parent_id="TRACE-001"
    )

    await runtime.publish_message(child_msg, TopicId("trace", "step2"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  1. 每个消息都有 trace_id 和 parent_id")
    print("  2. 通过 MessageContext 获取发送者和 topic 信息")
    print("  3. 可以重建完整的消息链路")


async def demo_context_based_routing():
    """演示 4: 基于上下文的路由"""
    print_section("演示 4: 基于上下文的路由决策")

    runtime = SingleThreadedAgentRuntime()

    await RoutingAgent.register(runtime, "router", lambda: RoutingAgent())
    await runtime.add_subscription(TypeSubscription("routing", "router"))

    runtime.start()

    print("\n--- 发送普通消息 ---")
    await runtime.publish_message(
        RequestMessage("REQ-001", "普通请求", "user"),
        TopicId("routing", "normal")
    )
    await asyncio.sleep(0.2)

    print("\n--- 发送紧急消息 ---")
    await runtime.publish_message(
        RequestMessage("REQ-002", "紧急请求", "admin"),
        TopicId("routing", "urgent")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  1. Agent 根据 topic.source 判断消息优先级")
    print("  2. 上下文信息影响路由和处理逻辑")


async def demo_multi_hop_communication():
    """演示 5: 多跳通信"""
    print_section("演示 5: 多跳通信 (消息经过多个 Agent)")

    runtime = SingleThreadedAgentRuntime()

    # Agent 1: 接收原始请求
    class Agent1(RoutedAgent):
        @message_handler
        async def handle(self, message: RequestMessage, ctx: MessageContext) -> None:
            print(f"\n📍 [Agent 1] 收到请求")
            print(f"   来源: {ctx.sender_id}")
            print(f"   Topic: {ctx.topic_id}")

            # 转发到 Agent 2
            if ctx.topic_id:
                new_topic = TopicId("agent2", ctx.topic_id.source)
                print(f"   → 转发到: {new_topic}")
                await self.publish_message(message, new_topic)

    # Agent 2: 处理并转发
    class Agent2(RoutedAgent):
        @message_handler
        async def handle(self, message: RequestMessage, ctx: MessageContext) -> None:
            print(f"\n📍 [Agent 2] 收到请求")
            print(f"   来自: {ctx.sender_id}")
            print(f"   Topic: {ctx.topic_id}")

            # 转发到 Agent 3
            if ctx.topic_id:
                new_topic = TopicId("agent3", ctx.topic_id.source)
                print(f"   → 转发到: {new_topic}")
                await self.publish_message(message, new_topic)

    # Agent 3: 最终处理
    class Agent3(RoutedAgent):
        @message_handler
        async def handle(self, message: RequestMessage, ctx: MessageContext) -> None:
            print(f"\n📍 [Agent 3] 最终处理")
            print(f"   来自: {ctx.sender_id}")
            print(f"   Topic: {ctx.topic_id}")
            print(f"   ✅ 处理完成")

    # 注册所有 Agent
    await Agent1.register(runtime, "agent1", lambda: Agent1())
    await Agent2.register(runtime, "agent2", lambda: Agent2())
    await Agent3.register(runtime, "agent3", lambda: Agent3())

    await runtime.add_subscription(TypeSubscription("agent1", "agent1"))
    await runtime.add_subscription(TypeSubscription("agent2", "agent2"))
    await runtime.add_subscription(TypeSubscription("agent3", "agent3"))

    runtime.start()

    print("\n--- 发起多跳请求 ---")
    request = RequestMessage(
        request_id="MULTI-001",
        query="多跳测试",
        sender="client"
    )

    # Agent 1 -> Agent 2 -> Agent 3
    await runtime.publish_message(request, TopicId("agent1", "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  1. 消息经过多个 Agent")
    print("  2. 每个 Agent 的 MessageContext 都不同")
    print("  3. sender_id 反映了上一跳的发送者")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - MessageContext 深入解析               ║
        ║           Understanding Message Context                       ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本上下文
        await demo_basic_context()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 请求-响应
        await demo_request_response()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 消息追踪
        await demo_message_tracing()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 上下文路由
        await demo_context_based_routing()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 多跳通信
        await demo_multi_hop_communication()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. MessageContext 提供消息的元数据")
        print("  2. topic_id: 消息来自哪个 Topic")
        print("  3. sender_id: 消息的发送者 Agent")
        print("  4. is_reply: 是否是回复消息")
        print("  5. 可以用于实现请求-响应、追踪、路由等模式")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

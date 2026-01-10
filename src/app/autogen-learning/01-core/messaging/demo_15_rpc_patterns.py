"""
Demo 15: RPC 调用模式 (Remote Procedure Call)

本演示展示如何:
1. 实现请求-响应模式
2. 同步和异步 RPC 调用
3. 处理 RPC 超时
4. 实现双向通信
5. 构建 RPC 客户端和服务端

运行方式:
    python demo_15_rpc_patterns.py

前置要求:
    - 已完成 demo_13_direct_messaging.py
    - 理解直接消息和广播消息

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
from typing import Any, Optional, Dict
from datetime import datetime
import uuid

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
class RPCRequest:
    """RPC 请求"""
    request_id: str
    method: str
    params: Dict[str, Any]
    caller: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class RPCResponse:
    """RPC 响应"""
    request_id: str
    result: Any
    error: Optional[str] = None
    responder: str = None
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class RPCNotification:
    """RPC 通知（无需响应）"""
    method: str
    params: Dict[str, Any]


# ===== 定义 Agent =====
class RPCServerAgent(RoutedAgent):
    """RPC 服务端 Agent"""

    def __init__(self, name: str, description: str = "RPC Server"):
        super().__init__(description)
        self.name = name
        self.methods = {
            "add": self._add,
            "multiply": self._multiply,
            "get_info": self._get_info,
            "slow_operation": self._slow_operation,
        }

    def _add(self, a: float, b: float) -> float:
        """加法"""
        return a + b

    def _multiply(self, a: float, b: float) -> float:
        """乘法"""
        return a * b

    def _get_info(self) -> Dict[str, Any]:
        """获取服务信息"""
        return {
            "name": self.name,
            "methods": list(self.methods.keys()),
            "status": "running"
        }

    async def _slow_operation(self, delay: float) -> str:
        """慢速操作"""
        await asyncio.sleep(delay)
        return f"操作完成 (耗时 {delay} 秒)"

    @message_handler
    async def handle_request(self, request: RPCRequest, ctx: MessageContext) -> None:
        """处理 RPC 请求"""

        print(f"\n  📡 [{self.name}] 收到 RPC 请求")
        print(f"     请求 ID: {request.request_id}")
        print(f"     方法: {request.method}")
        print(f"     参数: {request.params}")
        print(f"     调用者: {request.caller}")

        # 检查方法是否存在
        if request.method not in self.methods:
            error_response = RPCResponse(
                request_id=request.request_id,
                result=None,
                error=f"未知方法: {request.method}",
                responder=self.name
            )

            if ctx.topic_id:
                await self.publish_message(error_response, ctx.topic_id)
            return

        # 调用方法
        try:
            method = self.methods[request.method]

            # 判断是否是协程
            if asyncio.iscoroutinefunction(method):
                result = await method(**request.params)
            else:
                result = method(**request.params)

            # 发送响应
            response = RPCResponse(
                request_id=request.request_id,
                result=result,
                responder=self.name
            )

            print(f"\n  ✅ [{self.name}] 返回结果: {result}")

            if ctx.topic_id:
                await self.publish_message(response, ctx.topic_id)

        except Exception as e:
            # 错误响应
            error_response = RPCResponse(
                request_id=request.request_id,
                result=None,
                error=str(e),
                responder=self.name
            )

            print(f"\n  ❌ [{self.name}] 执行出错: {e}")

            if ctx.topic_id:
                await self.publish_message(error_response, ctx.topic_id)


class RPCClientAgent(RoutedAgent):
    """RPC 客户端 Agent"""

    def __init__(self, name: str, description: str = "RPC Client"):
        super().__init__(description)
        self.name = name
        self.pending_requests = {}  # request_id -> Future

    @message_handler
    async def handle_response(self, response: RPCResponse, ctx: MessageContext) -> None:
        """处理 RPC 响应"""

        print(f"\n  📥 [{self.name}] 收到 RPC 响应")
        print(f"     请求 ID: {response.request_id}")

        if response.request_id in self.pending_requests:
            future = self.pending_requests[response.request_id]
            future.set_result(response)
            print(f"     ✓ 请求已完成")
        else:
            print(f"     ⚠️  未知请求 ID")

    async def call_method(self, method: str, params: Dict[str, Any], server_id: AgentId) -> Any:
        """调用远程方法"""

        request_id = str(uuid.uuid4())

        # 创建 Future 等待响应
        future = asyncio.Future()
        self.pending_requests[request_id] = future

        # 创建请求
        request = RPCRequest(
            request_id=request_id,
            method=method,
            params=params,
            caller=self.name
        )

        print(f"\n  📤 [{self.name}] 发起 RPC 调用")
        print(f"     方法: {method}")
        print(f"     参数: {params}")
        print(f"     目标: {server_id}")

        # 发送请求
        await self.publish_message(request, recipient_id=server_id)

        # 等待响应
        try:
            response = await asyncio.wait_for(future, timeout=5.0)

            if response.error:
                raise Exception(response.error)

            return response.result
        finally:
            # 清理
            del self.pending_requests[request_id]


class TimeoutAgent(RoutedAgent):
    """测试超时的 Agent"""

    def __init__(self, description: str = "Timeout Agent"):
        super().__init__(description)
        self.delay = 0.0

    @message_handler
    async def handle_request(self, request: RPCRequest, ctx: MessageContext) -> None:
        """处理请求（可能很慢）"""

        print(f"\n  ⏳ [TimeoutAgent] 收到请求: {request.method}")
        print(f"     延迟: {self.delay} 秒")

        await asyncio.sleep(self.delay)

        response = RPCResponse(
            request_id=request.request_id,
            result=f"完成 (延迟 {self.delay} 秒)"
        )

        if ctx.topic_id:
            await self.publish_message(response, ctx.topic_id)


# ===== 演示函数 =====
async def demo_basic_rpc():
    """演示 1: 基本 RPC 调用"""
    print_section("演示 1: 基本的请求-响应模式")

    runtime = SingleThreadedAgentRuntime()

    # 注册服务端
    await RPCServerAgent.register(runtime, "server", lambda: RPCServerAgent("计算服务"))
    await runtime.add_subscription(TypeSubscription("rpc", "server"))

    # 注册客户端
    await RPCClientAgent.register(runtime, "client", lambda: RPCClientAgent("客户端"))
    await runtime.add_subscription(TypeSubscription("rpc_responses", "client"))

    runtime.start()

    print("\n--- 客户端调用 RPC 方法 ---")

    # 注意: 在实际应用中，客户端需要通过特定机制发送请求
    # 这里简化为直接发布消息

    request = RPCRequest(
        request_id="req-001",
        method="add",
        params={"a": 10, "b": 20},
        caller="客户端"
    )

    await runtime.publish_message(request, TopicId("rpc", "default"))

    await asyncio.sleep(0.5)

    print("\n💡 说明:")
    print("  - 客户端发送 RPC 请求")
    print("  - 服务端处理并返回结果")
    print("  - 实现了远程过程调用")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_multiple_calls():
    """演示 2: 多个 RPC 调用"""
    print_section("演示 2: 多个 RPC 方法调用")

    runtime = SingleThreadedAgentRuntime()

    await RPCServerAgent.register(runtime, "server", lambda: RPCServerAgent("多方法服务"))
    await runtime.add_subscription(TypeSubscription("rpc_channel", "server"))

    runtime.start()

    print("\n--- 调用不同的方法 ---")

    calls = [
        ("add", {"a": 5, "b": 3}),
        ("multiply", {"a": 4, "b": 7}),
        ("get_info", {}),
    ]

    for method, params in calls:
        request = RPCRequest(
            request_id=f"req-{uuid.uuid4().hex[:8]}",
            method=method,
            params=params,
            caller="测试客户端"
        )

        print(f"\n调用: {method}({params})")

        await runtime.publish_message(request, TopicId("rpc_channel", "default"))
        await asyncio.sleep(0.2)

    print("\n💡 RPC 支持多个方法")
    print("  - 每个请求指定方法名和参数")
    print("  - 服务端路由到对应方法")
    print("  - 返回执行结果")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_async_operations():
    """演示 3: 异步操作"""
    print_section("演示 3: 异步 RPC 操作")

    runtime = SingleThreadedAgentRuntime()

    await RPCServerAgent.register(runtime, "async_server", lambda: RPCServerAgent("异步服务"))
    await runtime.add_subscription(TypeSubscription("async_rpc", "async_server"))

    runtime.start()

    print("\n--- 调用慢速操作 ---")

    request = RPCRequest(
        request_id="slow-req-001",
        method="slow_operation",
        params={"delay": 1.0},
        caller="异步客户端"
    )

    print(f"发起异步调用，预计耗时 1.0 秒")
    await runtime.publish_message(request, TopicId("async_rpc", "default"))

    await asyncio.sleep(1.5)

    print("\n💡 异步 RPC 特点:")
    print("  - 服务端可以执行异步操作")
    print("  - 不会阻塞其他请求")
    print("  - 适合 I/O 密集型操作")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_error_handling():
    """演示 4: RPC 错误处理"""
    print_section("演示 4: RPC 错误处理")

    runtime = SingleThreadedAgentRuntime()

    await RPCServerAgent.register(runtime, "error_server", lambda: RPCServerAgent("错误处理服务"))
    await runtime.add_subscription(TypeSubscription("error_rpc", "error_server"))

    runtime.start()

    print("\n--- 调用存在的方法 ---")
    valid_request = RPCRequest(
        request_id="valid-001",
        method="add",
        params={"a": 1, "b": 2},
        caller="客户端"
    )

    await runtime.publish_message(valid_request, TopicId("error_rpc", "default"))
    await asyncio.sleep(0.2)

    print("\n--- 调用不存在的方法 ---")
    invalid_request = RPCRequest(
        request_id="invalid-001",
        method="nonexistent_method",
        params={},
        caller="客户端"
    )

    await runtime.publish_message(invalid_request, TopicId("error_rpc", "default"))
    await asyncio.sleep(0.2)

    print("\n💡 错误处理:")
    print("  - 服务端检查方法存在性")
    print("  - 返回错误响应")
    print("  - 客户端处理错误")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_rpc_timeout():
    """演示 5: RPC 超时"""
    print_section("演示 5: RPC 超时处理")

    runtime = SingleThreadedAgentRuntime()

    timeout_agent = TimeoutAgent()
    timeout_agent.delay = 3.0  # 3秒延迟

    await TimeoutAgent.register(runtime, "timeout_server", lambda: timeout_agent)
    await runtime.add_subscription(TypeSubscription("timeout_channel", "timeout_server"))

    runtime.start()

    print("\n--- 发起超时请求 ---")
    request = RPCRequest(
        request_id="timeout-001",
        method="handle_request",
        params={},
        caller="客户端"
    )

    print(f"服务端延迟: {timeout_agent.delay} 秒")
    print(f"客户端超时: 5.0 秒")

    await runtime.publish_message(request, TopicId("timeout_channel", "default"))

    # 等待超时
    try:
        await asyncio.wait_for(
            runtime.stop_when_idle(),
            timeout=2.0  # 比服务端快
        )
        print("✓ 在超时前完成")
    except asyncio.TimeoutError:
        print("⏰ 客户端超时")

    runtime.stop()

    print("\n💡 超时机制:")
    print("  - 客户端设置等待超时")
    print("  - 避免无限等待")
    print("  - 需要处理超时异常")


async def demo_notification():
    """演示 6: RPC 通知（无需响应）"""
    print_section("演示 6: RPC 通知模式")

    runtime = SingleThreadedAgentRuntime()

    # 通知接收 Agent
    class NotificationReceiver(RoutedAgent):
        def __init__(self):
            super().__init__("通知接收器")
            self.notifications = []

        @message_handler
        async def handle_notification(self, notification: RPCNotification, ctx: MessageContext) -> None:
            self.notifications.append(notification)
            print(f"\n  🔔 收到通知")
            print(f"     方法: {notification.method}")
            print(f"     参数: {notification.params}")

    await NotificationReceiver.register(runtime, "receiver", lambda: NotificationReceiver())
    await runtime.add_subscription(TypeSubscription("notifications", "receiver"))

    runtime.start()

    print("\n--- 发送通知 ---")
    notifications = [
        RPCNotification("user_joined", {"user_id": "123"}),
        RPCNotification("user_left", {"user_id": "456"}),
        RPCNotification("system_alert", {"level": "warning"}),
    ]

    for notif in notifications:
        await runtime.publish_message(notif, TopicId("notifications", "default"))
        await asyncio.sleep(0.1)

    print("\n💡 通知特点:")
    print("  - 单向通信")
    print("  - 不需要响应")
    print("  - 适合事件通知")

    await runtime.stop_when_idle()
    runtime.stop()


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - RPC 调用模式                          ║
        ║           Remote Procedure Call Patterns                    ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本 RPC
        await demo_basic_rpc()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 多个调用
        await demo_multiple_calls()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 异步操作
        await demo_async_operations()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 错误处理
        await demo_error_handling()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 超时
        await demo_rpc_timeout()

        print("\n" + "=" * 80 + "\n")

        # 演示 6: 通知
        await demo_notification()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. RPC 实现远程过程调用模式")
        print("  2. 包含请求和响应两部分")
        print("  3. 支持同步和异步操作")
        print("  4. 需要处理错误和超时")
        print("  5. 可以实现单向通知")
        print("  6. 适合客户端-服务端架构")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

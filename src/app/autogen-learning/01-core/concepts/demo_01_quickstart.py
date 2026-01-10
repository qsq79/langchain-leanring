"""
Demo 01: AutoGen Core API 快速开始

本演示展示如何:
1. 创建一个简单的 RoutedAgent
2. 注册 Agent 到 Runtime
3. 发送和接收消息
4. 使用 Topic 和 Subscription

运行方式:
    python demo_01_quickstart.py

前置要求:
    - 已安装 Python 3.10+
    - 已安装 autogen-core>=0.4.0

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/quickstart.html
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
from typing import List

from autogen_core import (
    AgentId,
    AgentRuntime,
    MessageHandler,
    RoutedAgent,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,

    message_handler,
)

from common.utils import print_banner, print_section, print_agent_info, print_message

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义消息类型 =====
class UserMessage:
    """用户消息"""

    def __init__(self, content: str, user_name: str = "User"):
        self.content = content
        self.user_name = user_name

    def __str__(self):
        return f"{self.user_name}: {self.content}"


class GreetingMessage:
    """问候消息"""

    def __init__(self, greeting: str):
        self.greeting = greeting

    def __str__(self):
        return self.greeting


# ===== 定义 Agent =====
class EchoAgent(RoutedAgent):
    """简单的 Echo Agent

    这个 Agent 会将接收到的消息原样返回
    """

    def __init__(self, description: str = "Echo Agent") -> None:
        super().__init__(description)
        self.message_count = 0

    @message_handler
    async def handle_user_message(self, message: UserMessage, ctx) -> None:
        """处理用户消息"""
        self.message_count += 1
        print_message(
            self.id.type,
            f"收到消息 (第 {self.message_count} 条): {message.content}",
            "INFO",
        )

        # Echo 回去
        print_message(self.id.type, f"Echo: {message.content}", "SUCCESS")


class GreeterAgent(RoutedAgent):
    """问候 Agent

    这个 Agent 会发送问候消息
    """

    def __init__(self, description: str = "Greeter Agent") -> None:
        super().__init__(description)

    @message_handler
    async def handle_greeting(self, message: GreetingMessage, ctx) -> None:
        """处理问候消息"""
        print_message(self.id.type, f"收到问候: {message.greeting}", "INFO")

        # 发布响应到同一个 topic
        if ctx.topic_id:
            response = UserMessage(f"你好! 收到你的问候: '{message.greeting}'", self.id.type)
            await self.publish_message(response, ctx.topic_id)


# ===== 演示函数 =====
async def demo_basic_agent():
    """演示 1: 基本 Agent 使用"""
    print_section("演示 1: 创建简单的 Echo Agent")

    # 创建 Runtime
    runtime = SingleThreadedAgentRuntime()
    print_message("System", "✓ Runtime 创建成功", "SUCCESS")

    # 注册 EchoAgent
    await EchoAgent.register(runtime, "echo_agent", lambda: EchoAgent("Echo Agent"))
    print_message("System", "✓ EchoAgent 注册成功", "SUCCESS")

    # 添加订阅
    await runtime.add_subscription(
        TypeSubscription(topic_type="user_messages", agent_type="echo_agent")
    )
    print_message("System", "✓ 订阅添加成功", "SUCCESS")

    # 启动 Runtime
    runtime.start()
    print_message("System", "✓ Runtime 已启动", "SUCCESS")

    # 发布消息
    print("\n--- 发送消息 ---\n")

    await runtime.publish_message(
        UserMessage("Hello, AutoGen!"),
        TopicId("user_messages", "default"),
    )

    await runtime.publish_message(
        UserMessage("这是一个测试消息"),
        TopicId("user_messages", "default"),
    )

    # 等待消息处理完成
    await runtime.stop_when_idle()
    print_message("System", "✓ 所有消息已处理", "SUCCESS")

    # 停止 Runtime
    runtime.stop()
    print_message("System", "✓ Runtime 已停止", "SUCCESS")


async def demo_multiple_agents():
    """演示 2: 多个 Agent 协作"""
    print_section("演示 2: 多个 Agent 协作 - Greeter 模式")

    # 创建 Runtime
    runtime = SingleThreadedAgentRuntime()
    print_message("System", "✓ Runtime 创建成功", "SUCCESS")

    # 注册多个 Agent
    await GreeterAgent.register(runtime, "greeter", lambda: GreeterAgent("Greeter"))
    await EchoAgent.register(runtime, "echo", lambda: EchoAgent("Echo"))
    print_message("System", "✓ 多个 Agent 注册成功", "SUCCESS")

    # 添加订阅 - 两个 Agent 订阅同一个 topic
    await runtime.add_subscription(TypeSubscription("greetings", "greeter"))
    await runtime.add_subscription(TypeSubscription("greetings", "echo"))
    print_message("System", "✓ 订阅添加成功 (两个 Agent 订阅同一个 topic)", "SUCCESS")

    # 启动 Runtime
    runtime.start()
    print_message("System", "✓ Runtime 已启动", "SUCCESS")

    # 发布问候消息
    print("\n--- 发送问候消息 ---\n")

    await runtime.publish_message(
        GreetingMessage("Hello, World!"),
        TopicId("greetings", "default"),
    )

    # 等待处理完成
    await runtime.stop_when_idle()
    print_message("System", "✓ 所有消息已处理", "SUCCESS")

    # 停止 Runtime
    runtime.stop()


async def demo_direct_messaging():
    """演示 3: 直接消息传递"""
    print_section("演示 3: 直接消息传递 (Agent 对 Agent)")

    # 创建 Runtime
    runtime = SingleThreadedAgentRuntime()

    # 注册 Agent
    await EchoAgent.register(runtime, "receiver", lambda: EchoAgent("Receiver Agent"))

    # 启动
    runtime.start()

    # 获取 receiver agent 的 ID
    receiver_id = AgentId("receiver", key="default")
    print(f"\n📦 目标 Agent ID: {receiver_id}\n")

    # 注意: 直接消息传递需要使用不同的方式
    # 这里展示基本概念，实际使用时需要通过 Runtime 的消息传递 API
    print_message("System", "直接消息传递需要特殊处理，详见后续示例", "INFO")

    # 清理
    await runtime.stop_when_idle()
    runtime.stop()


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ Core API - 快速开始演示                  ║
        ║           Event-Driven Agent Communication                     ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本 Agent
        await demo_basic_agent()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 多个 Agent
        await demo_multiple_agents()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 直接消息
        await demo_direct_messaging()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")
        print("\n下一步:")
        print("  1. 查看 demo_02_topic_subscription.py 了解 Topic 和 Subscription")
        print("  2. 查看 demo_03_agent_lifecycle.py 了解 Agent 生命周期")
        print("  3. 阅读官方文档: https://microsoft.github.io/autogen/stable/")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    # 运行主函数
    asyncio.run(main())

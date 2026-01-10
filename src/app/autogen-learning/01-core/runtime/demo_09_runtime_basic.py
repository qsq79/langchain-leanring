"""
Demo 09: Runtime 基础和生命周期

本演示展示如何:
1. 创建 SingleThreadedAgentRuntime
2. 理解 Runtime 的生命周期
3. 配置 Runtime 参数
4. 管理 Runtime 启动和停止
5. 处理 Runtime 错误

运行方式:
    python demo_09_runtime_basic.py

前置要求:
    - 已完成 demo_01_quickstart.py
    - 理解基本的 Runtime 使用

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/runtime.html
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
import signal
from typing import Optional

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


# ===== 定义 Agent =====
class SimpleAgent(RoutedAgent):
    """简单的测试 Agent"""

    def __init__(self, name: str, description: str = "Simple Agent"):
        super().__init__(description)
        self.name = name
        self.message_count = 0

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """处理消息"""
        self.message_count += 1
        print(f"  [{self.name}] 收到消息 #{self.message_count}: {message}")


class LifecycleAgent(RoutedAgent):
    """生命周期感知 Agent"""

    def __init__(self, name: str, description: str = "Lifecycle Agent"):
        super().__init__(description)
        self.name = name
        self.runtime_start_time: Optional[float] = None
        self.runtime_stop_time: Optional[float] = None

    @message_handler
    async def handle_status(self, message: str, ctx: MessageContext) -> None:
        """处理状态查询"""
        if message == "status":
            status = {
                "name": self.name,
                "messages_processed": self.message_count,
                "runtime_active": self.runtime_start_time is not None,
            }
            print(f"\n  [{self.name}] 状态: {status}")


# ===== 演示函数 =====
async def demo_runtime_creation():
    """演示 1: Runtime 创建和基本使用"""
    print_section("演示 1: Runtime 创建和基本使用")

    print("\n--- 创建 Runtime ---")
    runtime = SingleThreadedAgentRuntime()
    print("✓ Runtime 创建成功")
    print(f"  类型: {type(runtime)}")
    print(f"  状态: 已创建 (未启动)")

    print("\n--- 注册 Agent ---")
    await SimpleAgent.register(runtime, "agent", lambda: SimpleAgent("测试Agent"))
    print("✓ Agent 注册成功")

    print("\n--- 添加订阅 ---")
    await runtime.add_subscription(TypeSubscription("messages", "agent"))
    print("✓ 订阅添加成功")

    print("\n--- 启动 Runtime ---")
    runtime.start()
    print("✓ Runtime 已启动")

    print("\n--- 发布消息 ---")
    await runtime.publish_message("Hello, Runtime!", TopicId("messages", "default"))
    print("✓ 消息已发布")

    print("\n--- 等待处理完成 ---")
    await runtime.stop_when_idle()
    print("✓ 所有消息已处理")

    print("\n--- 停止 Runtime ---")
    runtime.stop()
    print("✓ Runtime 已停止")


async def demo_runtime_lifecycle():
    """演示 2: Runtime 完整生命周期"""
    print_section("演示 2: Runtime 完整生命周期")

    print("\n📋 Runtime 生命周期阶段:")
    print("  1. 创建 (Created)")
    print("  2. 注册 Agents (Registering)")
    print("  3. 添加订阅 (Subscribing)")
    print("  4. 启动 (Starting)")
    print("  5. 运行 (Running)")
    print("  6. 停止 (Stopping)")

    print("\n--- 阶段 1: 创建 Runtime ---")
    runtime = SingleThreadedAgentRuntime()
    print("  ✓ Runtime 实例已创建")

    print("\n--- 阶段 2: 注册 Agent ---")
    await SimpleAgent.register(runtime, "lifecycle_agent", lambda: SimpleAgent("生命周期Agent"))
    print("  ✓ Agent 已注册")

    print("\n--- 阶段 3: 添加订阅 ---")
    await runtime.add_subscription(TypeSubscription("lifecycle", "lifecycle_agent"))
    print("  ✓ 订阅已添加")

    print("\n--- 阶段 4: 启动 Runtime ---")
    runtime.start()
    print("  ✓ Runtime 已启动，开始处理消息")

    print("\n--- 阶段 5: Runtime 运行中 ---")
    for i in range(3):
        await runtime.publish_message(
            f"消息 {i+1}",
            TopicId("lifecycle", "default")
        )
        await asyncio.sleep(0.1)
    print("  ✓ 消息处理中...")

    print("\n--- 阶段 6: 等待空闲并停止 ---")
    await runtime.stop_when_idle()
    print("  ✓ Runtime 进入空闲状态")

    runtime.stop()
    print("  ✓ Runtime 已停止")

    print("\n✓ 生命周期完成")


async def demo_multiple_runtimes():
    """演示 3: 多个 Runtime 实例"""
    print_section("演示 3: 多个 Runtime 实例")

    print("\n--- 创建 Runtime 1 ---")
    runtime1 = SingleThreadedAgentRuntime()
    await SimpleAgent.register(runtime1, "agent1", lambda: SimpleAgent("Runtime1-Agent"))
    await runtime1.add_subscription(TypeSubscription("r1", "agent1"))
    runtime1.start()
    print("✓ Runtime 1 已启动")

    print("\n--- 创建 Runtime 2 ---")
    runtime2 = SingleThreadedAgentRuntime()
    await SimpleAgent.register(runtime2, "agent2", lambda: SimpleAgent("Runtime2-Agent"))
    await runtime2.add_subscription(TypeSubscription("r2", "agent2"))
    runtime2.start()
    print("✓ Runtime 2 已启动")

    print("\n--- 并发运行 ---")
    await runtime1.publish_message("来自 Runtime 1", TopicId("r1", "default"))
    await runtime2.publish_message("来自 Runtime 2", TopicId("r2", "default"))

    await asyncio.sleep(0.1)

    # 清理
    await runtime1.stop_when_idle()
    runtime1.stop()
    await runtime2.stop_when_idle()
    runtime2.stop()

    print("\n✓ 两个 Runtime 都已完成")


async def demo_runtime_configuration():
    """演示 4: Runtime 配置和选项"""
    print_section("演示 4: Runtime 配置选项")

    print("\n💡 SingleThreadedAgentRuntime 配置说明:")
    print("  - 单线程事件循环")
    print("  - 异步消息处理")
    print("  - 适合单机应用")
    print("  - 不需要额外配置参数")

    runtime = SingleThreadedAgentRuntime()

    # 注册多个 Agent
    await SimpleAgent.register(runtime, "worker1", lambda: SimpleAgent("工作进程1"))
    await SimpleAgent.register(runtime, "worker2", lambda: SimpleAgent("工作进程2"))
    await SimpleAgent.register(runtime, "monitor", lambda: SimpleAgent("监控器"))

    # 配置订阅
    await runtime.add_subscription(TypeSubscription("work", "worker1"))
    await runtime.add_subscription(TypeSubscription("work", "worker2"))
    await runtime.add_subscription(TypeSubscription("monitoring", "monitor"))

    runtime.start()

    print("\n--- 测试配置 ---")
    print("\n发送工作负载:")
    for i in range(2):
        await runtime.publish_message(
            f"任务 {i+1}",
            TopicId("work", "default")
        )
        await asyncio.sleep(0.1)

    print("\n发送监控消息:")
    await runtime.publish_message(
        "状态检查",
        TopicId("monitoring", "default")
    )

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n✓ 配置测试完成")


async def demo_error_handling():
    """演示 5: Runtime 错误处理"""
    print_section("演示 5: Runtime 错误处理")

    runtime = SingleThreadedAgentRuntime()
    await SimpleAgent.register(runtime, "error_agent", lambda: SimpleAgent("错误处理器"))
    await runtime.add_subscription(TypeSubscription("errors", "error_agent"))

    runtime.start()

    print("\n--- 正常消息 ---")
    await runtime.publish_message("正常消息", TopicId("errors", "default"))
    await asyncio.sleep(0.1)

    print("\n--- 测试异常处理 ---")
    try:
        # 尝试发布到未注册的 topic
        await runtime.publish_message(
            "测试消息",
            TopicId("nonexistent", "source")
        )
        print("  ⚠️  消息发送到无订阅者的 topic")
        print("  ℹ️  不会报错，但消息不会被处理")
    except Exception as e:
        print(f"  ❌ 捕获异常: {e}")

    print("\n--- 清理 ---")
    await runtime.stop_when_idle()
    runtime.stop()

    print("\n✓ 错误处理演示完成")


async def demo_graceful_shutdown():
    """演示 6: 优雅关闭"""
    print_section("演示 6: Runtime 优雅关闭")

    runtime = SingleThreadedAgentRuntime()
    await SimpleAgent.register(runtime, "shutdown_agent", lambda: SimpleAgent("关闭测试"))
    await runtime.add_subscription(TypeSubscription("shutdown", "shutdown_agent"))

    runtime.start()

    print("\n--- 发送消息 ---")
    for i in range(5):
        await runtime.publish_message(
            f"消息 {i+1}",
            TopicId("shutdown", "default")
        )
        print(f"  已发送: 消息 {i+1}")

    print("\n--- 调用 stop_when_idle ---")
    print("  等待所有消息处理完成...")
    await runtime.stop_when_idle()
    print("  ✓ 所有消息已处理")

    print("\n--- 停止 Runtime ---")
    runtime.stop()
    print("  ✓ Runtime 已优雅关闭")

    print("\n💡 stop_when_idle 的作用:")
    print("  - 阻塞直到消息队列为空")
    print("  - 确保所有消息都被处理")
    print("  - 防止消息丢失")


async def demo_runtime_state():
    """演示 7: Runtime 状态查询"""
    print_section("演示 7: Runtime 状态查询")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- Runtime 状态信息 ---")
    print(f"  类型: {type(runtime).__name__}")
    print(f"  是否启动: {getattr(runtime, '_started', False)}")

    await SimpleAgent.register(runtime, "state_agent", lambda: SimpleAgent("状态Agent"))
    await runtime.add_subscription(TypeSubscription("state", "state_agent"))

    print("\n--- 启动前 ---")
    print("  Runtime 状态: 未启动")

    runtime.start()
    print("\n--- 启动后 ---")
    print("  Runtime 状态: 运行中")

    print("\n--- 处理消息 ---")
    await runtime.publish_message("状态查询", TopicId("state", "default"))
    await asyncio.sleep(0.1)

    print("\n--- 停止后 ---")
    await runtime.stop_when_idle()
    runtime.stop()
    print("  Runtime 状态: 已停止")

    print("\n✓ 状态查询完成")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - Runtime 基础和生命周期                 ║
        ║           Understanding Runtime Management                    ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本创建
        await demo_runtime_creation()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 完整生命周期
        await demo_runtime_lifecycle()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 多个 Runtime
        await demo_multiple_runtimes()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 配置
        await demo_runtime_configuration()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 错误处理
        await demo_error_handling()

        print("\n" + "=" * 80 + "\n")

        # 演示 6: 优雅关闭
        await demo_graceful_shutdown()

        print("\n" + "=" * 80 + "\n")

        # 演示 7: 状态查询
        await demo_runtime_state()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. Runtime 生命周期: 创建 → 注册 → 启动 → 运行 → 停止")
        print("  2. 使用 start() 启动 Runtime")
        print("  3. 使用 stop_when_idle() 等待消息处理完成")
        print("  4. 使用 stop() 停止 Runtime")
        print("  5. 可以创建多个独立的 Runtime 实例")
        print("  6. 单线程 Runtime 适合单机应用")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

"""
Demo 12: Runtime 优雅关闭

本演示展示如何:
1. 使用 stop_when_idle() 等待消息处理完成
2. 实现超时关闭机制
3. 清理 Agent 资源
4. 处理关闭时的错误
5. 实现优雅关闭模式

运行方式:
    python demo_12_shutdown_idle.py

前置要求:
    - 已完成 demo_09_runtime_basic.py
    - 已完成 demo_11_message_delivery.py

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
from typing import Optional

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


# ===== 定义 Agent =====

class WorkerAgent(RoutedAgent):
    """工作 Agent - 模拟耗时任务"""

    def __init__(self, name: str, work_time: float = 0.5, description: str = "Worker Agent"):
        super().__init__(description)
        self.name = name
        self.work_time = work_time
        self.tasks_completed = 0
        self.is_busy = False

    @message_handler
    async def handle_work(self, message: str, ctx: MessageContext) -> None:
        """处理工作任务"""

        self.is_busy = True
        print(f"\n  🔨 [{self.name}] 开始任务")
        print(f"     任务: {message}")
        print(f"     预计耗时: {self.work_time}秒")

        # 模拟耗时工作
        await asyncio.sleep(self.work_time)

        self.tasks_completed += 1
        self.is_busy = False

        print(f"  ✅ [{self.name}] 任务完成 (已完成 {self.tasks_completed} 个)")


class SlowAgent(RoutedAgent):
    """慢速 Agent - 模拟处理慢的情况"""

    def __init__(self, description: str = "Slow Agent"):
        super().__init__(description)
        self.processing_time = 2.0  # 2秒处理时间

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """慢速处理消息"""

        print(f"\n  🐌 [慢速Agent] 开始处理")
        print(f"     消息: {message}")

        # 模拟慢速处理
        await asyncio.sleep(self.processing_time)

        print(f"  ✅ [慢速Agent] 处理完成 (耗时 {self.processing_time}秒)")


class CleanupAgent(RoutedAgent):
    """需要清理的 Agent"""

    def __init__(self, name: str, description: str = "Cleanup Agent"):
        super().__init__(description)
        self.name = name
        self.resources = []
        self.cleaned_up = False

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """处理消息"""

        # 模拟分配资源
        self.resources.append(f"resource-for-{message}")
        print(f"\n  🔧 [{self.name}] 分配资源: {message}")

    async def cleanup(self):
        """清理资源"""
        print(f"\n  🧹 [{self.name}] 清理 {len(self.resources)} 个资源")
        self.resources.clear()
        self.cleaned_up = True
        print(f"  ✅ [{self.name}] 清理完成")


class InfiniteAgent(RoutedAgent):
    """永不空闲的 Agent - 演示超时问题"""

    def __init__(self, description: str = "Infinite Agent"):
        super().__init__(description)
        self.running = True

    @message_handler
    async def handle_start(self, message: str, ctx: MessageContext) -> None:
        """开始无限循环"""

        print(f"\n  ♾️  [无限Agent] 开始运行...")
        while self.running:
            await asyncio.sleep(0.5)
            print(f"     仍在运行...")

    @message_handler
    async def handle_stop(self, message: str, ctx: MessageContext) -> None:
        """停止运行"""

        print(f"\n  🛑 [无限Agent] 收到停止信号")
        self.running = False


# ===== 演示函数 =====
async def demo_basic_shutdown():
    """演示 1: 基本的优雅关闭"""
    print_section("演示 1: 基本的优雅关闭")

    runtime = SingleThreadedAgentRuntime()

    await WorkerAgent.register(runtime, "worker", lambda: WorkerAgent("工作进程", 0.3))
    await runtime.add_subscription(TypeSubscription("tasks", "worker"))

    runtime.start()

    print("\n--- 发送任务 ---")
    for i in range(3):
        await runtime.publish_message(
            f"任务 {i+1}",
            TopicId("tasks", "default")
        )
        await asyncio.sleep(0.1)

    print("\n--- 调用 stop_when_idle ---")
    print("等待所有任务完成...")
    await runtime.stop_when_idle()
    print("✓ 所有任务已完成")

    runtime.stop()
    print("✓ Runtime 已停止")


async def demo_immediate_shutdown():
    """演示 2: 立即停止（不等待）"""
    print_section("演示 2: 立即停止 vs 优雅关闭")

    runtime = SingleThreadedAgentRuntime()

    await SlowAgent.register(runtime, "slow", lambda: SlowAgent())
    await runtime.add_subscription(TypeSubscription("slow", "slow"))

    runtime.start()

    print("\n--- 发送消息给慢速 Agent ---")
    await runtime.publish_message("慢速任务", TopicId("slow", "default"))

    print("\n--- 立即调用 stop() ---")
    print("⚠️  注意: 这会中断正在处理的消息")

    await asyncio.sleep(0.5)  # 等待一点时间
    runtime.stop()
    print("✓ Runtime 已立即停止")

    print("\n💡 说明:")
    print("  - stop() 会立即停止 Runtime")
    print("  - 可能会丢失正在处理的消息")
    print("  - 应该优先使用 stop_when_idle()")


async def demo_timeout_shutdown():
    """演示 3: 超时关闭机制"""
    print_section("演示 3: 超时关闭")

    runtime = SingleThreadedAgentRuntime()

    await SlowAgent.register(runtime, "slow", lambda: SlowAgent())
    await runtime.add_subscription(TypeSubscription("slow", "slow"))

    runtime.start()

    print("\n--- 发送慢速任务 ---")
    await runtime.publish_message("慢速任务", TopicId("slow", "default"))

    print("\n--- 带超时的等待 ---")
    timeout = 1.0  # 1秒超时
    print(f"设置超时: {timeout}秒")

    try:
        # 使用 asyncio.wait_for 实现超时
        await asyncio.wait_for(
            runtime.stop_when_idle(),
            timeout=timeout
        )
        print("✓ 所有消息在超时前完成")
    except asyncio.TimeoutError:
        print(f"⏰ 超时! 等待超过 {timeout} 秒")
        print("强制停止 Runtime")
        runtime.stop()

    print("\n💡 超时机制:")
    print("  - 防止无限等待")
    print("  - 适合有严格时间要求的场景")
    print("  - 需要处理超时异常")


async def demo_cleanup():
    """演示 4: 清理资源"""
    print_section("演示 4: Agent 资源清理")

    runtime = SingleThreadedAgentRuntime()

    agent = CleanupAgent("清理Agent")
    await CleanupAgent.register(runtime, "cleanup", lambda: agent)
    await runtime.add_subscription(TypeSubscription("cleanup", "cleanup"))

    runtime.start()

    print("\n--- 分配资源 ---")
    await runtime.publish_message("资源1", TopicId("cleanup", "default"))
    await runtime.publish_message("资源2", TopicId("cleanup", "default"))
    await asyncio.sleep(0.1)

    print("\n--- 关闭并清理 ---")
    await runtime.stop_when_idle()
    runtime.stop()

    # 手动调用清理
    await agent.cleanup()

    print("\n✓ 资源已清理")
    print(f"  清理状态: {agent.cleaned_up}")


async def demo_shutdown_patterns():
    """演示 5: 优雅关闭模式"""
    print_section("演示 5: 最佳关闭模式")

    print("\n💡 模式 1: 标准关闭")
    print("  适用于: 大多数场景")
    print("  步骤:")
    print("    1. 停止发布新消息")
    print("    2. 调用 stop_when_idle()")
    print("    3. 调用 stop()")

    print("\n💡 模式 2: 超时关闭")
    print("  适用于: 有时间限制的场景")
    print("  步骤:")
    print("    1. 使用 asyncio.wait_for()")
    print("    2. 设置合理超时")
    print("    3. 处理超时异常")

    print("\n💡 模式 3: 强制关闭")
    print("  适用于: 紧急情况")
    print("  步骤:")
    print("    1. 直接调用 stop()")
    print("    2. 可能丢失消息")

    print("\n💡 模式 4: 分阶段关闭")
    print("  适用于: 复杂系统")
    print("  步骤:")
    print("    1. 发送关闭信号")
    print("    2. 等待 Agent 响应")
    print("    3. 清理资源")
    print("    4. 调用 stop()")


async def demo_multiple_runtimes_shutdown():
    """演示 6: 多个 Runtime 的关闭"""
    print_section("演示 6: 多个 Runtime 的协调关闭")

    # 创建多个 Runtime
    runtimes = []
    agents = []

    for i in range(3):
        runtime = SingleThreadedAgentRuntime()
        agent = WorkerAgent(f"Worker-{i+1}", 0.2)

        await WorkerAgent.register(runtime, f"worker{i+1}", lambda: agent)
        await runtime.add_subscription(TypeSubscription(f"work{i+1}", f"worker{i+1}"))

        runtime.start()
        runtimes.append(runtime)
        agents.append(agent)

        # 发送任务
        await runtime.publish_message(
            f"Runtime {i+1} 的任务",
            TopicId(f"work{i+1}", "default")
        )

    print(f"\n✓ 创建了 {len(runtimes)} 个 Runtime")

    print("\n--- 协调关闭所有 Runtime ---")
    for i, runtime in enumerate(runtimes, 1):
        print(f"\n关闭 Runtime {i}/{len(runtimes)}:")
        await runtime.stop_when_idle()
        runtime.stop()
        print(f"  ✓ Runtime {i} 已关闭")

    print("\n✓ 所有 Runtime 已关闭")


async def demo_error_during_shutdown():
    """演示 7: 关闭时的错误处理"""
    print_section("演示 7: 关闭时的错误处理")

    runtime = SingleThreadedAgentRuntime()

    # 定义一个会出错的 Agent
    class ErrorAgent(RoutedAgent):
        @message_handler
        async def handle_message(self, message: str, ctx: MessageContext) -> None:
            print(f"\n  [错误Agent] 收到消息: {message}")
            if message == "error":
                print(f"  ❌ 抛出异常")
                raise ValueError("模拟的错误")
            print(f"  ✅ 正常处理")

    await ErrorAgent.register(runtime, "error", lambda: ErrorAgent())
    await runtime.add_subscription(TypeSubscription("error", "error"))

    runtime.start()

    print("\n--- 发送正常消息 ---")
    await runtime.publish_message("正常", TopicId("error", "default"))
    await asyncio.sleep(0.1)

    print("\n--- 发送错误消息 ---")
    await runtime.publish_message("error", TopicId("error", "default"))
    await asyncio.sleep(0.1)

    print("\n--- 尝试关闭 ---")
    try:
        await runtime.stop_when_idle()
        runtime.stop()
        print("✓ Runtime 已关闭")
    except Exception as e:
        print(f"❌ 关闭时出错: {e}")
        print("  需要适当的错误处理")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - Runtime 优雅关闭                       ║
        ║           Graceful Runtime Shutdown                           ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本关闭
        await demo_basic_shutdown()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 立即停止
        await demo_immediate_shutdown()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 超时
        await demo_timeout_shutdown()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 清理
        await demo_cleanup()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 关闭模式
        await demo_shutdown_patterns()

        print("\n" + "=" * 80 + "\n")

        # 演示 6: 多 Runtime
        await demo_multiple_runtimes_shutdown()

        print("\n" + "=" * 80 + "\n")

        # 演示 7: 错误处理
        await demo_error_during_shutdown()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. stop_when_idle() 等待所有消息处理完成")
        print("  2. stop() 立即停止 Runtime")
        print("  3. 可以使用 asyncio.wait_for() 实现超时")
        print("  4. 应该在关闭前清理 Agent 资源")
        print("  5. 需要处理关闭时的异常")
        print("  6. 多 Runtime 需要协调关闭")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

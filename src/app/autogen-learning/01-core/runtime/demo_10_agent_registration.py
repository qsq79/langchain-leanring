"""
Demo 10: Agent 注册机制

本演示展示如何:
1. 使用 Agent.register() 方法
2. 理解 Agent 类型和命名
3. 使用工厂函数创建 Agent
4. 处理重复注册
5. 动态注册和注销

运行方式:
    python demo_10_agent_registration.py

前置要求:
    - 已完成 demo_09_runtime_basic.py
    - 理解 Runtime 的基本使用

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
from typing import Dict, List

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
class ConfigurableAgent(RoutedAgent):
    """可配置的 Agent - 演示工厂函数"""

    def __init__(self, name: str, config: Dict = None, description: str = "Configurable Agent"):
        super().__init__(description)
        self.name = name
        self.config = config or {}
        self.message_count = 0

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """处理消息"""
        self.message_count += 1
        print(f"  [{self.name}] 处理消息 #{self.message_count}: {message}")
        if self.config:
            print(f"    配置: {self.config}")


class CountingAgent(RoutedAgent):
    """计数 Agent - 演示实例计数"""

    instance_count = 0

    def __init__(self, instance_id: int, description: str = "Counting Agent"):
        super().__init__(description)
        self.instance_id = instance_id
        CountingAgent.instance_count += 1

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """处理消息"""
        print(f"  [实例 #{self.instance_id}] (总数: {CountingAgent.instance_count})")
        print(f"    收到: {message}")


class DynamicAgent(RoutedAgent):
    """动态 Agent - 支持动态注册"""

    def __init__(self, agent_type: str, description: str = "Dynamic Agent"):
        super().__init__(description)
        self.agent_type = agent_type

    @message_handler
    async def handle_message(self, message: str, ctx: MessageContext) -> None:
        """处理消息"""
        print(f"  [{self.agent_type}] {message}")


# ===== 演示函数 =====
async def demo_basic_registration():
    """演示 1: 基本注册流程"""
    print_section("演示 1: 基本 Agent 注册")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- 注册 Agent ---")
    print("步骤:")
    print("  1. 调用 AgentClass.register()")
    print("  2. 传入 runtime 实例")
    print("  3. 指定 agent_type (字符串标识)")
    print("  4. 提供工厂函数")

    await ConfigurableAgent.register(
        runtime,
        "my_agent",  # agent_type
        lambda: ConfigurableAgent("MyAgent", {"version": "1.0"})
    )

    print("\n✓ Agent 注册成功")
    print("  agent_type: 'my_agent'")
    print("  完全限定名: 'ConfigurableAgent'")

    await runtime.add_subscription(TypeSubscription("messages", "my_agent"))
    runtime.start()

    print("\n--- 使用已注册的 Agent ---")
    await runtime.publish_message("Hello!", TopicId("messages", "default"))

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_factory_functions():
    """演示 2: 使用工厂函数"""
    print_section("演示 2: 工厂函数创建 Agent")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- 简单工厂函数 ---")
    await ConfigurableAgent.register(
        runtime,
        "simple",
        lambda: ConfigurableAgent("SimpleAgent")
    )
    print("✓ 简单工厂注册完成")

    print("\n--- 带参数的工厂函数 ---")
    await ConfigurableAgent.register(
        runtime,
        "configured",
        lambda: ConfigurableAgent(
            "ConfiguredAgent",
            {"debug": True, "log_level": "INFO"}
        )
    )
    print("✓ 配置工厂注册完成")

    print("\n--- 使用闭包的工厂函数 ---")
    def create_agent_with_id(agent_id: int):
        """闭包工厂函数"""
        return ConfigurableAgent(
            f"Agent-{agent_id}",
            {"id": agent_id}
        )

    await ConfigurableAgent.register(
        runtime,
        "closure_agent",
        lambda: create_agent_with_id(42)
    )
    print("✓ 闭包工厂注册完成")

    # 添加订阅并测试
    await runtime.add_subscription(TypeSubscription("test", "simple"))
    await runtime.add_subscription(TypeSubscription("test", "configured"))
    await runtime.add_subscription(TypeSubscription("test", "closure_agent"))

    runtime.start()

    print("\n--- 测试不同的工厂函数 ---")
    await runtime.publish_message("测试简单工厂", TopicId("test", "default"))
    await asyncio.sleep(0.1)
    await runtime.publish_message("测试配置工厂", TopicId("test", "default"))
    await asyncio.sleep(0.1)
    await runtime.publish_message("测试闭包工厂", TopicId("test", "default"))

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_naming_conventions():
    """演示 3: Agent 命名规范"""
    print_section("演示 3: Agent 类型命名规范")

    runtime = SingleThreadedAgentRuntime()

    print("\n💡 命名建议:")
    print("  - 使用小写字母")
    print("  - 使用下划线分隔单词")
    print("  - 描述性名称")
    print("  - 避免 Python 关键字")

    # 良好的命名
    good_names = [
        "order_processor",
        "notification_service",
        "data_analyzer",
        "chat_bot",
    ]

    print("\n--- 注册示例 (良好命名) ---")
    for name in good_names:
        await ConfigurableAgent.register(
            runtime,
            name,
            lambda n=name: ConfigurableAgent(n.title())
        )
        await runtime.add_subscription(TypeSubscription("msg", name))
        print(f"  ✓ 已注册: '{name}'")

    runtime.start()

    print("\n--- 测试 ---")
    for name in good_names:
        await runtime.publish_message(
            f"发送给 {name}",
            TopicId("msg", "default")
        )
        await asyncio.sleep(0.1)

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_multiple_instances():
    """演示 4: 注册多个 Agent 类型"""
    print_section("演示 4: 注册多个 Agent 类型")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- 注册多个不同类型的 Agent ---")
    agent_types = [
        ("processor", "处理器"),
        ("validator", "验证器"),
        ("logger", "日志器"),
    ]

    for agent_type, display_name in agent_types:
        await ConfigurableAgent.register(
            runtime,
            agent_type,
            lambda: ConfigurableAgent(display_name)
        )
        await runtime.add_subscription(TypeSubscription("work", agent_type))
        print(f"  ✓ 注册: {agent_type} ({display_name})")

    runtime.start()

    print("\n--- 广播消息到所有 Agent ---")
    await runtime.publish_message(
        "处理这个任务",
        TopicId("work", "default")
    )

    await asyncio.sleep(0.2)

    print("\n💡 观察:")
    print("  - 所有订阅 'work' topic 的 Agent 都收到了消息")
    print("  - 每个 agent_type 都有独立的 Agent 实例")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_instance_per_key():
    """演示 5: 每个 key 创建实例"""
    print_section("演示 5: 每个 key 创建独立的 Agent 实例")

    runtime = SingleThreadedAgentRuntime()

    print("\n--- 注册 Agent ---")
    await CountingAgent.register(
        runtime,
        "counter",
        lambda: CountingAgent(0)  # 初始 ID
    )
    await runtime.add_subscription(TypeSubscription("count", "counter"))

    runtime.start()

    print("\n--- 发送到不同的 key (source) ---")
    print("每个不同的 source 会创建新的 Agent 实例\n")

    sources = ["session_a", "session_b", "session_c"]
    for source in sources:
        print(f"发送到: {source}")
        await runtime.publish_message(
            f"来自 {source} 的消息",
            TopicId("count", source)
        )
        await asyncio.sleep(0.1)

    print(f"\n总实例数: {CountingAgent.instance_count}")
    print("💡 每个不同的 source 创建独立实例")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_dynamic_registration():
    """演示 6: 动态注册 Agent"""
    print_section("演示 6: 动态注册和注销")

    runtime = SingleThreadedAgentRuntime()
    runtime.start()

    print("\n--- 运行时注册 Agent ---")
    agent_type = "dynamic_agent"

    # 动态注册
    await DynamicAgent.register(
        runtime,
        agent_type,
        lambda: DynamicAgent(agent_type)
    )
    await runtime.add_subscription(TypeSubscription("dynamic", agent_type))
    print(f"✓ 运行时注册: {agent_type}")

    # 使用 Agent
    await runtime.publish_message(
        "消息 1",
        TopicId("dynamic", "default")
    )
    await asyncio.sleep(0.1)

    print("\n💡 注意:")
    print("  - Runtime 启动后仍可注册 Agent")
    print("  - 新注册的 Agent 立即可用")
    print("  - 适合动态扩展场景")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_registration_best_practices():
    """演示 7: 注册最佳实践"""
    print_section("演示 7: Agent 注册最佳实践")

    runtime = SingleThreadedAgentRuntime()

    print("\n✓ 最佳实践 1: 启动前完成所有注册")
    print("  优点: 避免竞态条件，性能更好")

    # 批量注册
    agents_to_register = [
        ("agent1", lambda: ConfigurableAgent("Agent1")),
        ("agent2", lambda: ConfigurableAgent("Agent2")),
        ("agent3", lambda: ConfigurableAgent("Agent3")),
    ]

    for agent_type, factory in agents_to_register:
        await ConfigurableAgent.register(runtime, agent_type, factory)
        await runtime.add_subscription(TypeSubscription("batch", agent_type))

    print("  ✓ 批量注册完成")

    print("\n✓ 最佳实践 2: 使用一致的命名规范")
    print("  例子: <功能>_<类型> (如: order_processor, notification_sender)")

    print("\n✓ 最佳实践 3: 工厂函数应该简洁")
    print("  避免在工厂函数中执行耗时操作")

    print("\n✓ 最佳实践 4: 考虑 Agent 生命周期")
    print("  - 短生命周期: 简单工厂")
    print("  - 长生命周期: 复杂初始化")

    runtime.start()

    # 测试批量注册的 Agent
    await runtime.publish_message("批量测试", TopicId("batch", "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n✓ 最佳实践演示完成")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - Agent 注册机制                         ║
        ║           Understanding Agent Registration                    ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本注册
        await demo_basic_registration()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 工厂函数
        await demo_factory_functions()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 命名规范
        await demo_naming_conventions()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 多个类型
        await demo_multiple_instances()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 实例管理
        await demo_instance_per_key()

        print("\n" + "=" * 80 + "\n")

        # 演示 6: 动态注册
        await demo_dynamic_registration()

        print("\n" + "=" * 80 + "\n")

        # 演示 7: 最佳实践
        await demo_registration_best_practices()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. 使用 AgentClass.register() 注册 Agent")
        print("  2. agent_type 是 Agent 的唯一标识")
        print("  3. 工厂函数负责创建 Agent 实例")
        print("  4. 每个 key 可以创建独立的 Agent 实例")
        print("  5. 支持运行时动态注册")
        print("  6. 建议在启动前完成所有注册")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

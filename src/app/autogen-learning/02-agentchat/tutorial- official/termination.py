"""
AutoGen AgentChat Tutorial - Termination Conditions

本示例展示如何:
1. 使用内置终止条件 (MaxMessageTermination, TextMentionTermination)
2. 组合终止条件 (AND/OR)
3. 创建自定义终止条件
4. 使用 TokenUsageTermination, TimeoutTermination
5. 使用 ExternalTermination

基于官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Sequence

# 添加项目根目录到 Python 路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TerminatedException, TerminationCondition
from autogen_agentchat.conditions import (
    ExternalTermination,
    MaxMessageTermination,
    TextMentionTermination,
    TokenUsageTermination,
    TimeoutTermination,
)
from autogen_agentchat.messages import BaseAgentEvent, BaseChatMessage, StopMessage, ToolCallExecutionEvent
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import Component
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
from pydantic import BaseModel
from typing_extensions import Self

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示 1: 基本终止条件 =====
async def demo_basic_termination():
    """演示 1: 使用 MaxMessageTermination 和 TextMentionTermination"""
    print("=" * 80)
    print("演示 1: 基本终止条件")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=1,
    )

    # 创建主 Agent
    primary_agent = AssistantAgent(
        "primary",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    # 创建评论 Agent
    critic_agent = AssistantAgent(
        "critic",
        model_client=model_client,
        system_message="Provide constructive feedback for every message. Respond with 'APPROVE' to when your feedbacks are addressed.",
    )

    # 使用 MaxMessageTermination
    max_msg_termination = MaxMessageTermination(max_messages=3)
    round_robin_team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=max_msg_termination)

    print("📝 使用 MaxMessageTermination (最多 3 条消息):")
    result = await round_robin_team.run(task="Write a unique, Haiku about the weather in Paris")

    print(f"\n🛑 停止原因: {result.stop_reason}")
    print(f"📊 消息数量: {len(result.messages)}")

    # 继续对话（终止条件会自动重置）
    print("\n📝 继续对话:")
    result = await round_robin_team.run()

    print(f"\n🛑 停止原因: {result.stop_reason}")
    print(f"📊 消息数量: {len(result.messages)}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 组合终止条件 =====
async def demo_combined_termination():
    """演示 2: 使用 AND 和 OR 运算符组合终止条件"""
    print("=" * 80)
    print("演示 2: 组合终止条件")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=1,
    )

    primary_agent = AssistantAgent(
        "primary",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    critic_agent = AssistantAgent(
        "critic",
        model_client=model_client,
        system_message="Provide constructive feedback. Respond with 'APPROVE' to when your feedbacks are addressed.",
    )

    # 使用 OR 运算符组合条件
    max_msg_termination = MaxMessageTermination(max_messages=10)
    text_termination = TextMentionTermination("APPROVE")
    combined_termination = max_msg_termination | text_termination  # 任意一个条件满足即停止

    round_robin_team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=combined_termination)

    print("📝 使用 OR 组合条件 (最多 10 条消息或包含 'APPROVE'):")
    result = await Console(round_robin_team.run_stream(task="Write a unique, Haiku about the weather in Paris"))

    print(f"\n🛑 停止原因: {result.stop_reason}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: Token 使用和超时终止 =====
async def demo_token_timeout_termination():
    """演示 3: 使用 TokenUsageTermination 和 TimeoutTermination"""
    print("=" * 80)
    print("演示 3: Token 使用和超时终止")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    # Token 使用终止
    token_termination = TokenUsageTermination(max_total_token=1000)
    team = RoundRobinGroupChat([agent], termination_condition=token_termination)

    print("📝 使用 TokenUsageTermination (最多 1000 tokens):")
    result = await team.run(task="Count from 1 to 100")

    print(f"\n🛑 停止原因: {result.stop_reason}")

    # 超时终止
    timeout_termination = TimeoutTermination(timeout_seconds=5)
    team = RoundRobinGroupChat([agent], termination_condition=timeout_termination)

    print("\n📝 使用 TimeoutTermination (最多 5 秒):")
    result = await team.run(task="What is the meaning of life?")

    print(f"\n🛑 停止原因: {result.stop_reason}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 4: 外部终止 =====
async def demo_external_termination():
    """演示 4: 使用 ExternalTermination 从外部控制终止"""
    print("=" * 80)
    print("演示 4: 外部终止")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant. Keep writing.",
    )

    # 创建外部终止条件
    external_termination = ExternalTermination()
    team = RoundRobinGroupChat([agent], termination_condition=external_termination)

    # 创建一个异步任务来运行团队
    async def run_team():
        """运行团队并收集所有消息"""
        messages = []
        async for message in team.run_stream(task="Write a long essay about AI"):
            messages.append(message)
        return messages[-1]  # 返回最后一个消息（TaskResult）

    # 在后台运行团队
    run = asyncio.create_task(run_team())

    # 等待一段时间
    await asyncio.sleep(0.5)

    # 从外部停止
    print("\n⚠️  从外部停止团队...")
    external_termination.set()

    # 等待团队完成
    result = await run

    print(f"\n🛑 停止原因: {result.stop_reason}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 5: 自定义终止条件 =====
class FunctionCallTerminationConfig(BaseModel):
    """自定义终止条件的配置"""

    function_name: str


class FunctionCallTermination(TerminationCondition, Component[FunctionCallTerminationConfig]):
    """当特定函数调用被执行时终止对话"""

    component_config_schema = FunctionCallTerminationConfig
    component_provider_override = "autogen_agentchat.conditions.FunctionCallTermination"

    def __init__(self, function_name: str) -> None:
        self._terminated = False
        self._function_name = function_name

    @property
    def terminated(self) -> bool:
        return self._terminated

    async def __call__(self, messages: Sequence[BaseAgentEvent | BaseChatMessage]) -> StopMessage | None:
        if self._terminated:
            raise TerminatedException("Termination condition has already been reached")
        for message in messages:
            if isinstance(message, ToolCallExecutionEvent):
                for execution in message.content:
                    if execution.name == self._function_name:
                        self._terminated = True
                        return StopMessage(
                            content=f"Function '{self._function_name}' was executed.",
                            source="FunctionCallTermination",
                        )
        return None

    async def reset(self) -> None:
        self._terminated = False

    def _to_config(self) -> FunctionCallTerminationConfig:
        return FunctionCallTerminationConfig(function_name=self._function_name)

    @classmethod
    def _from_config(cls, config: FunctionCallTerminationConfig) -> Self:
        return cls(function_name=config.function_name)


async def demo_custom_termination():
    """演示 5: 创建自定义终止条件"""
    print("=" * 80)
    print("演示 5: 自定义终止条件")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=1,
    )

    # 定义批准函数
    def approve() -> str:
        """批准消息"""
        return "Approved"

    # 创建 Agent
    primary_agent = AssistantAgent(
        "primary",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    critic_agent = AssistantAgent(
        "critic",
        model_client=model_client,
        tools=[approve],
        system_message="Provide constructive feedback. Use the approve tool to approve when all feedbacks are addressed.",
    )

    # 创建自定义终止条件
    function_call_termination = FunctionCallTermination(function_name="approve")
    round_robin_team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=function_call_termination)

    print("📝 使用自定义 FunctionCallTermination:")
    result = await Console(
        round_robin_team.run_stream(task="Write a unique, Haiku about the weather in Paris")
    )

    print(f"\n🛑 停止原因: {result.stop_reason}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Termination Conditions")
    print("=" * 80 + "\n")

    try:
        # 演示 1: 基本终止条件
        await demo_basic_termination()

        # 演示 2: 组合终止条件
        await demo_combined_termination()

        # 演示 3: Token 和超时终止
        await demo_token_timeout_termination()

        # 演示 4: 外部终止
        await demo_external_termination()

        # 演示 5: 自定义终止条件
        await demo_custom_termination()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

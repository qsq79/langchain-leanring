"""
AutoGen AgentChat Tutorial - Teams

本示例展示如何:
1. 创建多 Agent 团队 (RoundRobinGroupChat)
2. 使用终止条件 (TextMentionTermination)
3. 运行团队并获取结果
4. 流式输出团队消息
5. 重置和恢复团队
6. 停止和终止团队
7. 单 Agent 团队 (工具循环)

基于官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.base import TaskResult
from autogen_agentchat.conditions import ExternalTermination, TextMentionTermination, TextMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示 1: 创建和运行团队 =====
async def demo_create_and_run_team():
    """演示 1: 创建多 Agent 团队并运行"""
    print("=" * 80)
    print("演示 1: 创建和运行多 Agent 团队")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 创建模型客户端
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
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
        system_message="Provide constructive feedback. Respond with 'APPROVE' to when your feedbacks are addressed.",
    )

    # 定义终止条件：当检测到 'APPROVE' 时停止
    text_termination = TextMentionTermination("APPROVE")

    # 创建团队
    team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=text_termination)

    # 运行团队
    result = await team.run(task="Write a short poem about the fall season.")

    print("📊 消息历史:")
    for message in result.messages:
        print(f"  {message.source}: {message.content[:100]}...")

    print(f"\n🛑 停止原因: {result.stop_reason}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 流式输出团队消息 =====
async def demo_streaming_team():
    """演示 2: 流式输出团队消息"""
    print("=" * 80)
    print("演示 2: 流式输出团队消息")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
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

    text_termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=text_termination)

    # 使用 Console 流式输出
    await team.reset()  # 重置团队以进行新任务
    await Console(team.run_stream(task="Write a short poem about the fall season."))

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: 停止团队 =====
async def demo_stopping_team():
    """演示 3: 使用外部终止条件停止团队"""
    print("=" * 80)
    print("演示 3: 停止团队")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
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

    # 创建外部终止条件
    external_termination = ExternalTermination()
    text_termination = TextMentionTermination("APPROVE")

    # 组合终止条件
    team = RoundRobinGroupChat(
        [primary_agent, critic_agent],
        termination_condition=external_termination | text_termination,  # 使用位或运算符组合条件
    )

    # 在后台任务中运行团队
    run = asyncio.create_task(Console(team.run_stream(task="Write a short poem about the fall season.")))

    # 等待一段时间
    await asyncio.sleep(0.1)

    # 停止团队
    print("\n⚠️  正在停止团队...")
    external_termination.set()

    # 等待团队完成
    await run

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 4: 恢复团队 =====
async def demo_resuming_team():
    """演示 4: 恢复团队以继续任务"""
    print("=" * 80)
    print("演示 4: 恢复团队")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
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

    text_termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat([primary_agent, critic_agent], termination_condition=text_termination)

    # 运行团队
    print("第一次运行:")
    await Console(team.run_stream(task="Write a short poem about the fall season."))

    # 恢复团队继续上一个任务（不提供新任务）
    print("\n恢复团队继续:")
    await Console(team.run_stream())

    # 使用新任务恢复团队
    print("\n使用新任务恢复:")
    await Console(team.run_stream(task="将这首诗用中文唐诗风格写一遍。"))

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 5: 取消团队运行 =====
async def demo_aborting_team():
    """演示 5: 取消团队运行"""
    print("=" * 80)
    print("演示 5: 取消团队运行")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    primary_agent = AssistantAgent(
        "primary",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    critic_agent = AssistantAgent(
        "critic",
        model_client=model_client,
        system_message="Provide constructive feedback.",
    )

    team = RoundRobinGroupChat([primary_agent, critic_agent])

    # 创建取消令牌
    cancellation_token = CancellationToken()

    # 使用另一个协程运行团队
    run = asyncio.create_task(
        team.run(
            task="Translate the poem to Spanish.",
            cancellation_token=cancellation_token,
        )
    )

    # 取消运行
    cancellation_token.cancel()

    try:
        result = await run  # 这将引发 CancelledError
    except asyncio.CancelledError:
        print("⚠️  任务已取消")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 6: 单 Agent 团队 =====
async def demo_single_agent_team():
    """演示 6: 单 Agent 团队（工具循环）"""
    print("=" * 80)
    print("演示 6: 单 Agent 团队")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        parallel_tool_calls=False,  # 禁用并行工具调用
    )

    # 创建递增数字的工具
    def increment_number(number: int) -> int:
        """将数字递增 1"""
        return number + 1

    # 创建使用 increment_number 函数的 Agent
    looped_assistant = AssistantAgent(
        "looped_assistant",
        model_client=model_client,
        tools=[increment_number],  # 注册工具
        system_message="You are a helpful AI assistant, use the tool to increment the number.",
    )

    # 终止条件：当 Agent 响应文本消息时停止任务
    termination_condition = TextMessageTermination("looped_assistant")

    # 创建团队
    team = RoundRobinGroupChat(
        [looped_assistant],
        termination_condition=termination_condition,
    )

    # 运行团队
    result = await team.run(task="Increment the number 5 to 10.")

    print("📊 消息数量:", len(result.messages))
    print("🛑 停止原因:", result.stop_reason)
    print("📝 最后一条消息:", result.messages[-1].content)

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Teams")
    print("=" * 80 + "\n")

    try:
        # 演示 1: 创建和运行团队
        await demo_create_and_run_team()

        # 演示 2: 流式输出
        await demo_streaming_team()

        # 演示 3: 停止团队
        await demo_stopping_team()

        # 演示 4: 恢复团队
        await demo_resuming_team()

        # 演示 5: 取消团队
        await demo_aborting_team()

        # 演示 6: 单 Agent 团队
        await demo_single_agent_team()

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

"""
AutoGen AgentChat Tutorial - Human-in-the-Loop

本示例展示如何:
1. 在团队运行期间提供反馈 (UserProxyAgent)
2. 使用 max_turns 控制交互
3. 使用 HandoffTermination
4. 在运行终止后提供反馈

基于官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html
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

from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.base import Handoff
from autogen_agentchat.conditions import HandoffTermination, TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示 1: 使用 UserProxyAgent 在运行期间提供反馈 =====
async def demo_user_proxy_during_run():
    """演示 1: 在团队运行期间使用 UserProxyAgent 获取用户反馈"""
    print("=" * 80)
    print("演示 1: 使用 UserProxyAgent 在运行期间提供反馈")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 创建 Agent
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    assistant = AssistantAgent("assistant", model_client=model_client)

    # 创建 UserProxyAgent - 使用 input() 获取用户输入
    user_proxy = UserProxyAgent("user_proxy", input_func=input)

    # 创建终止条件：当用户说 "APPROVE" 时停止
    termination = TextMentionTermination("APPROVE")

    # 创建团队
    team = RoundRobinGroupChat([assistant, user_proxy], termination_condition=termination)

    print("📝 请提供反馈 (输入 'APPROVE' 批准):")
    # 运行对话并流式输出到控制台
    result = await Console(team.run_stream(task="Write a 4-line poem about the ocean."))

    print(f"\n🛑 停止原因: {result.stop_reason}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 使用 Max Turns 控制交互 =====
async def demo_max_turns():
    """演示 2: 使用 max_turns 参数控制团队停止"""
    print("=" * 80)
    print("演示 2: 使用 Max Turns 控制交互")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    assistant = AssistantAgent("assistant", model_client=model_client)

    # 创建团队，设置 max_turns=1，这样每次只运行一个 Agent
    team = RoundRobinGroupChat([assistant], max_turns=1)

    task = "Write a 4-line poem about the ocean."

    print("📝 交互式对话 (输入 'exit' 退出):")
    while True:
        # 运行对话并流式输出到控制台
        result = await Console(team.run_stream(task=task))

        print(f"\n🛑 停止原因: {result.stop_reason}")

        # 获取用户反馈
        task = input("\nEnter your feedback (type 'exit' to leave): ")
        if task.lower().strip() == "exit":
            break

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: 使用 HandoffTermination =====
async def demo_handoff_termination():
    """演示 3: 使用 HandoffTermination 让 Agent 主动请求用户帮助"""
    print("=" * 80)
    print("演示 3: 使用 HandoffTermination")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建一个懒惰的 AssistantAgent，当无法完成任务时移交给用户
    lazy_agent = AssistantAgent(
        "lazy_assistant",
        model_client=model_client,
        handoffs=[Handoff(target="user", message="Transfer to user.")],
        system_message="If you cannot complete the task, transfer to user. Otherwise, when finished, respond with 'TERMINATE'.",
    )

    # 创建终止条件
    handoff_termination = HandoffTermination(target="user")
    text_termination = TextMentionTermination("TERMINATE")

    # 创建团队
    lazy_agent_team = RoundRobinGroupChat(
        [lazy_agent], termination_condition=handoff_termination | text_termination
    )

    print("📝 第一次运行 (Agent 无法完成，请求用户帮助):")
    task = "What is the weather in New York?"
    result = await Console(lazy_agent_team.run_stream(task=task), output_stats=True)

    print(f"\n🛑 停止原因: {result.stop_reason}")

    print("\n📝 提供信息后继续:")
    result = await Console(lazy_agent_team.run_stream(task="The weather in New York is sunny."))

    print(f"\n🛑 停止原因: {result.stop_reason}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 4: 自定义输入函数 =====
async def demo_custom_input_function():
    """演示 4: 为 UserProxyAgent 提供自定义输入函数"""
    print("=" * 80)
    print("演示 4: 自定义输入函数")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 自定义输入函数
    def custom_input(prompt: str) -> str:
        """自定义输入函数，可以添加前缀或其他逻辑"""
        print(f"\n[系统请求输入]: {prompt}")
        user_input = input("您的输入: ")
        return user_input

    assistant = AssistantAgent("assistant", model_client=model_client)
    user_proxy = UserProxyAgent("user_proxy", input_func=custom_input)

    termination = TextMentionTermination("APPROVE")
    team = RoundRobinGroupChat([assistant, user_proxy], termination_condition=termination)

    print("📝 使用自定义输入函数:")
    result = await Console(team.run_stream(task="Write a short poem about spring."))

    print(f"\n🛑 停止原因: {result.stop_reason}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Human-in-the-Loop")
    print("=" * 80 + "\n")

    try:
        # 演示 1: UserProxyAgent 在运行期间
        # 注意：此演示需要用户交互
        print("⚠️  演示 1 需要用户交互，跳过...")
        # await demo_user_proxy_during_run()

        # 演示 2: Max Turns
        print("⚠️  演示 2 需要用户交互，跳过...")
        # await demo_max_turns()

        # 演示 3: HandoffTermination
        await demo_handoff_termination()

        # 演示 4: 自定义输入函数
        print("⚠️  演示 4 需要用户交互，跳过...")
        # await demo_custom_input_function()

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

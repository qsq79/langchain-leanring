"""
AutoGen AgentChat Tutorial - Agents

本示例展示如何:
1. 创建 AssistantAgent
2. 使用工具 (Tools)
3. 运行 agent 并获取结果
4. 流式输出消息

基于官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/agents.html
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
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义工具 =====
# Define a tool that searches the web for information.
# For simplicity, we will use a mock function here that returns a static string.
async def web_search(query: str) -> str:
    """Find information on the web"""
    return "AutoGen is a programming framework for building multi-agent applications."


# ===== 演示 1: 基本 Agent 使用 =====
async def demo_basic_agent():
    """演示 1: 创建并运行基本的 AssistantAgent"""
    print("=" * 80)
    print("演示 1: 基本 AssistantAgent")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # Create an agent that uses the OpenAI GPT-4o model.
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=[web_search],
        system_message="Use tools to solve tasks.",
    )

    # Use asyncio.run(agent.run(...)) when running in a script.
    result = await agent.run(task="Find information on AutoGen")
    print("📊 消息历史:")
    for message in result.messages:
        print(f"  {message.source}: {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 流式输出 =====
async def demo_streaming():
    """演示 2: 使用 Console 流式输出消息"""
    print("=" * 80)
    print("演示 2: 流式输出消息")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        tools=[web_search],
        system_message="Use tools to solve tasks.",
    )

    async def assistant_run_stream() -> None:
        # Option 1: read each message from the stream.
        # async for message in agent.run_stream(task="Find information on AutoGen"):
        #     print(message)

        # Option 2: use Console to print all messages as they appear.
        await Console(
            agent.run_stream(task="Find information on AutoGen"),
            output_stats=True,  # Enable stats printing.
        )

    # Use asyncio.run(assistant_run_stream()) when running in a script.
    await assistant_run_stream()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: 多次工具迭代 =====
async def demo_tool_iterations():
    """演示 3: 配置多次工具迭代"""
    print("=" * 80)
    print("演示 3: 多次工具迭代")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 禁用并行工具调用
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        parallel_tool_calls=False,  # Disable parallel tool calls
    )

    agent = AssistantAgent(
        name="assistant_loop",
        model_client=model_client,
        tools=[web_search],
        system_message="Use tools to solve tasks.",
        max_tool_iterations=10,  # At most 10 iterations of tool calls
    )

    result = await agent.run(task="Search for AutoGen and summarize what you find")
    print("📊 最终响应:")
    print(f"  {result.messages[-1].content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Agents")
    print("=" * 80 + "\n")

    try:
        # 演示 1: 基本使用
        await demo_basic_agent()

        # 演示 2: 流式输出
        await demo_streaming()

        # 演示 3: 工具迭代
        await demo_tool_iterations()

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

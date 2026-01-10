"""
AutoGen AgentChat Tutorial - Models

本示例展示如何:
1. 使用不同的模型客户端 (OpenAI, Azure OpenAI)
2. 配置模型参数 (temperature, max_tokens, etc.)
3. 使用多模型
4. 处理模型错误和重试

基于官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html
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
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示 1: 基本 OpenAI 模型配置 =====
async def demo_basic_model_config():
    """演示 1: 配置基本的 OpenAI 模型客户端"""
    print("=" * 80)
    print("演示 1: 基本 OpenAI 模型配置")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 创建 OpenAI 模型客户端
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=0.7,
        max_tokens=500,
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    print("📝 使用基本模型配置:")
    result = await agent.run(task="Say hello in 3 different languages")

    print(f"\n📊 响应:")
    print(f"{result.messages[-1].content}")

    # 显示模型使用信息
    if hasattr(result.messages[-1], 'models_usage') and result.messages[-1].models_usage:
        print(f"\n📈 Token 使用:")
        print(f"  提示 tokens: {result.messages[-1].models_usage.prompt_tokens}")
        print(f"  完成 tokens: {result.messages[-1].models_usage.completion_tokens}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 不同的温度设置 =====
async def demo_temperature_settings():
    """演示 2: 使用不同的温度设置"""
    print("=" * 80)
    print("演示 2: 温度设置对比")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    task = "Write a short creative story about a robot"

    # 低温度 (更确定性)
    print("📝 低温度 (0.1) - 更确定性:")
    model_client_low = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=0.1,
    )

    agent_low = AssistantAgent("assistant_low", model_client=model_client_low)
    result_low = await agent_low.run(task=task)
    print(f"{result_low.messages[-1].content[:200]}...")

    await model_client_low.close()

    # 高温度 (更随机性)
    print("\n📝 高温度 (1.0) - 更随机性:")
    model_client_high = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=1.0,
    )

    agent_high = AssistantAgent("assistant_high", model_client=model_client_high)
    result_high = await agent_high.run(task=task)
    print(f"{result_high.messages[-1].content[:200]}...")

    await model_client_high.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: 使用多个模型 =====
async def demo_multiple_models():
    """演示 3: 在团队中使用多个模型"""
    print("=" * 80)
    print("演示 3: 使用多个模型")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 创建两个使用相同模型但不同配置的 Agent
    creative_agent = AssistantAgent(
        "creative_writer",
        model_client=OpenAIChatCompletionClient(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
            temperature=0.9,
        ),
        system_message="You are a creative writer. Be imaginative and expressive.",
    )

    critical_agent = AssistantAgent(
        "critic",
        model_client=OpenAIChatCompletionClient(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
            temperature=0.3,
        ),
        system_message="You are a critical editor. Provide constructive feedback.",
    )

    team = RoundRobinGroupChat(
        [creative_agent, critical_agent],
        termination_condition=MaxMessageTermination(max_messages=3),
    )

    print("📝 使用多模型团队:")
    result = await team.run(task="Write a haiku about programming")

    print(f"\n📊 对话:")
    for message in result.messages:
        if message.source != "user":
            print(f"\n{message.source}:")
            print(f"{message.content[:200]}...")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 4: 模型参数配置 =====
async def demo_model_parameters():
    """演示 4: 配置各种模型参数"""
    print("=" * 80)
    print("演示 4: 模型参数配置")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 配置多个参数
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
        temperature=0.7,
        max_tokens=150,
        top_p=0.9,
        frequency_penalty=0.5,
        presence_penalty=0.5,
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant. Be concise.",
    )

    print("📝 使用自定义参数:")
    print("  - Temperature: 0.7")
    print("  - Max Tokens: 150")
    print("  - Top P: 0.9")
    print("  - Frequency Penalty: 0.5")
    print("  - Presence Penalty: 0.5")

    result = await agent.run(task="What is artificial intelligence? Keep it brief.")

    print(f"\n📊 响应:")
    print(f"{result.messages[-1].content}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Models")
    print("=" * 80 + "\n")

    try:
        # 演示 1: 基本模型配置
        await demo_basic_model_config()

        # 演示 2: 温度设置
        await demo_temperature_settings()

        # 演示 3: 多模型
        await demo_multiple_models()

        # 演示 4: 模型参数
        await demo_model_parameters()

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

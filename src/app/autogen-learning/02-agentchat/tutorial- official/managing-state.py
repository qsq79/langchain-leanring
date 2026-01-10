"""
AutoGen AgentChat Tutorial - Managing State

本示例展示如何:
1. 保存和加载团队状态
2. 序列化和反序列化团队
3. 使用团队状态进行会话恢复
4. 管理团队生命周期

基于官方文档: https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import MaxMessageTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示 1: 基本状态管理 =====
async def demo_basic_state():
    """演示 1: 团队的基本状态管理"""
    print("=" * 80)
    print("演示 1: 基本状态管理")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    team = RoundRobinGroupChat([agent], termination_condition=MaxMessageTermination(max_messages=2))

    print("📝 第一次运行:")
    result = await team.run(task="Say hello")

    print(f"消息数量: {len(result.messages)}")
    print(f"最后一条消息: {result.messages[-1].content}")

    # 团队保持状态，可以继续运行
    print("\n📝 第二次运行 (继续之前的对话):")
    result = await team.run(task="What is my name?")

    print(f"消息数量: {len(result.messages)}")
    print(f"最后一条消息: {result.messages[-1].content}")

    # 重置团队状态
    print("\n📝 重置团队:")
    await team.reset()

    print("📝 重置后运行:")
    result = await team.run(task="What is my name?")

    print(f"消息数量: {len(result.messages)}")
    print(f"最后一条消息: {result.messages[-1].content}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 保存和恢复状态 =====
async def demo_save_restore_state():
    """演示 2: 保存和恢复团队状态"""
    print("=" * 80)
    print("演示 2: 保存和恢复状态")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant. Remember my name is Alice.",
    )

    team = RoundRobinGroupChat([agent], termination_condition=MaxMessageTermination(max_messages=2))

    print("📝 初始运行:")
    result = await team.run(task="My name is Alice. Remember that.")

    print(f"消息数量: {len(result.messages)}")

    # 保存状态到文件
    state_file = Path("/tmp/autogen_team_state.json")

    # 注意: AutoGen 0.4+ 使用不同的状态保存机制
    # 这里演示基本的消息历史保存
    print(f"\n💾 保存消息历史到: {state_file}")

    messages_data = [
        {
            "source": msg.source,
            "content": msg.content,
            "type": type(msg).__name__,
        }
        for msg in result.messages
    ]

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(messages_data, f, indent=2, ensure_ascii=False)

    print(f"✅ 已保存 {len(messages_data)} 条消息")

    # 从文件恢复状态
    print("\n📂 从文件恢复消息历史:")
    with open(state_file, "r", encoding="utf-8") as f:
        restored_messages = json.load(f)

    print(f"✅ 已恢复 {len(restored_messages)} 条消息")
    for msg in restored_messages:
        print(f"  {msg['source']}: {msg['content'][:50]}...")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: 多轮会话状态 =====
async def demo_multi_turn_state():
    """演示 3: 多轮会话中的状态管理"""
    print("=" * 80)
    print("演示 3: 多轮会话状态")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant. Keep track of user information.",
    )

    team = RoundRobinGroupChat([agent], termination_condition=MaxMessageTermination(max_messages=2))

    conversations = [
        "My name is Bob and I like Python.",
        "What is my name?",
        "What programming language do I like?",
    ]

    for i, task in enumerate(conversations, 1):
        print(f"\n📝 第 {i} 轮:")
        print(f"任务: {task}")
        result = await team.run(task=task)
        print(f"响应: {result.messages[-1].content[:100]}...")
        print(f"累计消息数: {len(result.messages)}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 4: 状态重置和清理 =====
async def demo_state_reset():
    """演示 4: 重置和清理团队状态"""
    print("=" * 80)
    print("演示 4: 状态重置和清理")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant.",
    )

    team = RoundRobinGroupChat([agent], termination_condition=MaxMessageTermination(max_messages=2))

    print("📝 第一次运行:")
    result = await team.run(task="My favorite color is blue.")
    print(f"消息数: {len(result.messages)}")

    print("\n🔄 重置团队:")
    await team.reset()

    print("📝 重置后运行:")
    result = await team.run(task="What is my favorite color?")
    print(f"消息数: {len(result.messages)}")
    print(f"响应: {result.messages[-1].content[:100]}...")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Managing State")
    print("=" * 80 + "\n")

    try:
        # 演示 1: 基本状态管理
        await demo_basic_state()

        # 演示 2: 保存和恢复状态
        await demo_save_restore_state()

        # 演示 3: 多轮会话状态
        await demo_multi_turn_state()

        # 演示 4: 状态重置
        await demo_state_reset()

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

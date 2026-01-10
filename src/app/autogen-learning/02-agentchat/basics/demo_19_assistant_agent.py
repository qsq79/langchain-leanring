"""
Demo 19: AssistantAgent - 通用助手 Agent

本演示展示如何:
1. 使用 AssistantAgent 创建通用助手
2. 配置模型客户端
3. 进行多轮对话
4. 处理复杂任务
5. 管理对话上下文

运行方式:
    # 方式1: 从 autogen-learning 目录运行（推荐）
    cd /path/to/autogen-learning
    python -m 02-agentchat.basics.demo_19_assistant_agent

    # 方式2: 直接运行脚本文件
    python demo_19_assistant_agent.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 AgentChat 基础概念

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/quickstart.html
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 这样可以直接运行脚本文件，而不需要从特定目录运行
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # 从 basics/ 目录向上三级到 autogen-learning/
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示函数 =====
async def demo_basic_assistant():
    """演示 1: 基本的 AssistantAgent"""
    print("=" * 80)
    print("演示 1: 基本的 AssistantAgent")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 创建模型客户端 - 显式设置 base_url 避免编码问题
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建 AssistantAgent
    assistant = AssistantAgent(
        name="assistant",
        model_client=model_client,
        description="一个乐于助人的 AI 助手，可以回答各种问题并提供帮助。"
    )

    print("📋 Agent 信息:")
    print(f"   名称: {assistant.name}")
    print(f"   模型: {settings.openai_model}")
    print(f"   描述: {assistant.description}")
    print()

    # 运行助手
    print("💬 开始对话...")
    print()

    result = await assistant.run(
        task="你好！请简单介绍一下你自己。"
    )

    # 打印结果
    print("📊 对话结果:")
    for message in result.messages:
        print(f"\n{message.source}: {message.content}")
    
    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_turn_conversation():
    """演示 2: 多轮对话"""
    print("=" * 80)
    print("演示 2: 多轮对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    assistant = AssistantAgent(
        name="multi_turn_assistant",
        model_client=model_client,
        description="一个可以进行多轮对话的智能助手。"
    )

    print("💬 开始多轮对话...")
    print()

    # 在 AutoGen 0.4+ 中，通过连续调用 run 来实现多轮对话
    # 第一轮
    print("👤 用户: 我想学习 Python 编程")
    result1 = await assistant.run(task="我想学习 Python 编程")
    print(f"🤖 助手: {result1.messages[-1].content}\n")

    # 第二轮
    print("👤 用户: Python 有哪些主要特性？")
    result2 = await assistant.run(
        task="Python 有哪些主要特性？",
    )
    print(f"🤖 助手: {result2.messages[-1].content}\n")

    # 第三轮
    print("👤 用户: 请详细说明 Python 的三个主要特性，并为每个特性举一个简单的例子。")
    result3 = await assistant.run(
        task="请详细说明 Python 的三个主要特性，并为每个特性举一个简单的例子。",
    )

    # 打印完整对话
    print("\n📊 完整对话历史:")
    all_messages = result1.messages + result2.messages[1:] + result3.messages[1:]
    for i, message in enumerate(all_messages, 1):
        role_icon = "👤" if message.source == "user" else "🤖"
        print(f"\n{i}. [{role_icon}] {message.source}:")
        print(f"   {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_complex_task():
    """演示 3: 处理复杂任务"""
    print("=" * 80)
    print("演示 3: 处理复杂任务")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    assistant = AssistantAgent(
        name="task_assistant",
        model_client=model_client,
        description="一个擅长处理复杂任务的助手，擅长分析和规划。"
    )

    print("🎯 复杂任务:")
    print("   创建一个简单的 Python 类，包含以下功能:")
    print("   1. 初始化方法")
    print("   2. 添加数据的方法")
    print("   3. 计算平均值的方法")
    print("   4. 显示所有数据的方法")
    print()

    result = await assistant.run(
        task="""请创建一个名为 DataAnalyzer 的 Python 类，它应该：
1. 有一个构造函数接受数据列表
2. 有一个 add_data() 方法用于添加新数据
3. 有一个 get_average() 方法返回平均值
4. 有一个 show_all() 方法打印所有数据

请提供完整的代码，并包含一个使用示例。"""
    )

    print("📊 结果:")
    for message in result.messages:
        print(f"\n🤖 助手:")
        # 简化输出，只显示关键部分
        lines = message.content.split('\n')
        for line in lines[:20]:  # 只显示前 20 行
            print(f"   {line}")
        if len(lines) > 20:
            print(f"   ... (还有 {len(lines) - 20} 行)")
    
    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_different_personalities():
    """演示 4: 不同人格的助手"""
    print("=" * 80)
    print("演示 4: 不同人格的 AssistantAgent")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建三个不同人格的助手
    formal_assistant = AssistantAgent(
        name="formal_assistant",
        model_client=model_client,
        description="你是一个正式、专业的助手，使用礼貌和正式的语言。"
    )

    casual_assistant = AssistantAgent(
        name="casual_assistant",
        model_client=model_client,
        description="你是一个友好、随意的助手，使用轻松和非正式的语言。"
    )

    technical_assistant = AssistantAgent(
        name="technical_assistant",
        model_client=model_client,
        description="你是一个技术专家助手，专注于提供详细的技术解释和代码示例。"
    )

    # 相同的问题，不同的助手
    question = "什么是机器学习？"

    assistants = [
        ("正式助手", formal_assistant),
        ("随意助手", casual_assistant),
        ("技术专家", technical_assistant)
    ]

    for name, assistant in assistants:
        print(f"\n{'─' * 40}")
        print(f"💬 {name}")
        print(f"{'─' * 40}\n")

        result = await assistant.run(task=question)
        
        # 显示回答
        for message in result.messages:
            print(f"{message.content[:200]}...")  # 只显示前 200 字符

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_context_awareness():
    """演示 5: 上下文感知"""
    print("=" * 80)
    print("演示 5: 上下文感知对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    assistant = AssistantAgent(
        name="context_assistant",
        model_client=model_client,
        description="一个能够记住对话上下文的智能助手。"
    )

    print("💬 上下文感知对话:")
    print()

    # 在 AutoGen 0.4+ 中，Agent 本身不维护上下文
    # 这里演示简单的多轮对话
    conversation = [
        "我的名字叫小明",
        "我最喜欢的颜色是什么？",  # 这应该回答"我不知道"
        "我最喜欢的颜色是蓝色",
        "现在我最喜欢的颜色是什么？",  # 这应该回答"蓝色"
    ]

    for question in conversation:
        print(f"👤 用户: {question}")

        result = await assistant.run(task=question)

        # 获取助手的回答
        assistant_message = result.messages[-1]
        print(f"🤖 助手: {assistant_message.content}")
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - AssistantAgent 演示              ║
║           High-Level Agent API - General Assistant         ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print("=" * 80 + "\n")

    try:
        # 检查 API Key
        settings = get_settings()
        if not settings.openai_api_key:
            print("❌ 错误: 未配置 OPENAI_API_KEY")
            print("   请在 .env 文件中设置 OPENAI_API_KEY")
            return

        # 演示 1: 基本助手
        await demo_basic_assistant()

        # 演示 2: 多轮对话
        await demo_multi_turn_conversation()

        # 演示 3: 复杂任务
        await demo_complex_task()

        # 演示 4: 不同人格
        await demo_different_personalities()

        # 演示 5: 上下文感知
        await demo_context_awareness()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n下一步:")
        print("  1. 查看 demo_20_coding_agent.py 学习代码生成")
        print("  2. 查看 demo_21_text_chat_agent.py 学习文本对话")
        print("  3. 查看 docs/ 目录了解更多 AgentChat 用法")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
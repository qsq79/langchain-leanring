"""
Demo 21: TextChatAgent - 文本对话 Agent

本演示展示如何:
1. 创建专注文本对话的 Agent
2. 处理自然语言交互
3. 上下文管理和记忆
4. 对话风格定制
5. 多轮对话优化

运行方式:
    # 方式1: 从 autogen-learning 目录运行（推荐）
    cd /path/to/autogen-learning
    python -m 02-agentchat.basics.demo_21_text_chat_agent

    # 方式2: 直接运行脚本文件
    python demo_21_text_chat_agent.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 AssistantAgent 基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/chat.html
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
async def demo_basic_conversation():
    """演示 1: 基本对话"""
    print("=" * 80)
    print("演示 1: 基本文本对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    chat_agent = AssistantAgent(
        name="chat_agent",
        model_client=model_client,
        description="你是一个友好的对话伙伴，喜欢与用户交流各种话题。"
    )

    print("💬 开始对话...")
    print()

    # 多轮对话示例
    questions = [
        "你好！今天天气怎么样？",
        "能给我推荐一本书吗？",
        "那这本书是关于什么的？"
    ]

    for question in questions:
        print(f"👤 用户: {question}")

        result = await chat_agent.run(task=question)

        # 获取最后一条回复
        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content}")
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_role_playing():
    """演示 2: 角色扮演对话"""
    print("=" * 80)
    print("演示 2: 角色扮演对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建不同角色的对话 Agent
    characters = {
        "古代诗人": AssistantAgent(
            name="poet",
            model_client=model_client,
            description="你是一位古代诗人，说话优雅，喜欢用诗词来表达，用古典文风对话。"
        ),
        "现代极客": AssistantAgent(
            name="geek",
            model_client=model_client,
            description="你是一个科技极客，喜欢用技术术语和网络流行语，关注最新科技动态。"
        ),
        "心理咨询师": AssistantAgent(
            name="counselor",
            model_client=model_client,
            description="你是一位温暖专业的心理咨询师，擅长倾听和理解，给出建议和鼓励。"
        )
    }

    # 同一个话题，不同角色的回应
    topic = "最近工作压力很大，感觉很疲惫"

    for role_name, agent in characters.items():
        print(f"\n{'─' * 40}")
        print(f"💬 {role_name}的回应")
        print(f"{'─' * 40}\n")

        result = await agent.run(task=topic)
        
        for message in result.messages:
            print(f"{message.content[:400]}...")
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_context_awareness():
    """演示 3: 上下文感知能力"""
    print("=" * 80)
    print("演示 3: 上下文感知对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    chat_agent = AssistantAgent(
        name="context_agent",
        model_client=model_client,
        description="你是一个擅长记住对话上下文的助手，能够根据历史对话提供连贯的回答。"
    )

    print("💬 上下文感知测试:")
    print()

    # 构建一个需要上下文的对话序列
    scenario = [
        ("我计划去日本旅行", None),
        ("东京有哪些必去的景点？", None),
        ("那京都呢？", "应该推荐京都的景点"),
        ("这些地方大概需要几天时间？", "应该根据东京和京都的景点来估算时间"),
        ("预算大概多少？", "应该根据旅行天数和日本消费水平来估算")
    ]

    for question, expectation in scenario:
        print(f"👤 用户: {question}")

        result = await chat_agent.run(task=question)

        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content}")

        if expectation:
            print(f"💡 期望: {expectation}")
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_conversation_style():
    """演示 4: 对话风格定制"""
    print("=" * 80)
    print("演示 4: 不同对话风格")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建不同风格的对话 Agent
    styles = {
        "简洁风格": AssistantAgent(
            name="concise",
            model_client=model_client,
            description="你是一个简洁的助手，用最少的文字回答问题，直击要点，不啰嗦。"
        ),
        "详细风格": AssistantAgent(
            name="detailed",
            model_client=model_client,
            description="你是一个详细的助手，会提供全面、深入的解释，包括背景知识和例子。"
        ),
        "幽默风格": AssistantAgent(
            name="humorous",
            model_client=model_client,
            description="你是一个幽默风趣的助手，喜欢用轻松诙谐的方式回答问题，适当加入幽默元素。"
        )
    }

    question = "什么是人工智能？"

    for style_name, agent in styles.items():
        print(f"\n{'─' * 40}")
        print(f"💬 {style_name}")
        print(f"{'─' * 40}\n")

        result = await agent.run(task=question)
        
        for message in result.messages:
            print(f"{message.content[:300]}...")
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_emotional_intelligence():
    """演示 5: 情感智能"""
    print("=" * 80)
    print("演示 5: 情感智能对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    empathetic_agent = AssistantAgent(
        name="empathy_agent",
        model_client=model_client,
        description="""你是一个富有同理心的助手，能够:
- 识别用户的情绪状态
- 给予恰当的情感支持
- 在提供信息的同时关心用户的感受
- 用温暖和理解的语言沟通"""
    )

    print("💬 情感支持对话:")
    print()

    emotional_scenarios = [
        "我今天考试不及格，感觉很沮丧",
        "虽然失败了，但我决定再试一次",
        "有什么建议能帮助我下次做得更好？"
    ]

    for scenario in emotional_scenarios:
        print(f"👤 用户: {scenario}")

        result = await empathetic_agent.run(task=scenario)

        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content}")
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
║          AutoGen 0.4+ - TextChatAgent 演示               ║
║           Natural Language Conversation                      ║
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

        # 演示 1: 基本对话
        await demo_basic_conversation()

        # 演示 2: 角色扮演
        await demo_role_playing()

        # 演示 3: 上下文感知
        await demo_context_awareness()

        # 演示 4: 对话风格
        await demo_conversation_style()

        # 演示 5: 情感智能
        await demo_emotional_intelligence()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n下一步:")
        print("  1. 查看 demo_22_user_proxy_agent.py 学习用户代理")
        print("  2. 查看 conversations/ 目录学习对话管理")
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
"""
AutoGen AgentChat Tutorial - Messages

本示例展示如何:
1. 创建 Agent-Agent 消息 (TextMessage, MultiModalMessage)
2. 理解内部事件 (ToolCallRequestEvent, ToolCallExecutionEvent)
3. 使用消息进行 Agent 通信
4. 处理多模态消息 (文本 + 图像)

基于官方文档: https://microsoft.github.io/autogen/0.4.6/user-guide/agentchat-user-guide/tutorial/messages.html
"""

import asyncio
import os
import sys
from io import BytesIO
from pathlib import Path

# 添加项目根目录到 Python 路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import requests
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import MultiModalMessage, TextMessage
from autogen_core import Image as AGImage
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
from PIL import Image

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示 1: 创建文本消息 =====
async def demo_text_message():
    """演示 1: 创建和使用 TextMessage"""
    print("=" * 80)
    print("演示 1: TextMessage - 文本消息")
    print("=" * 80 + "\n")

    # 创建文本消息
    # TextMessage 接受字符串内容和字符串来源
    text_message = TextMessage(content="Hello, world!", source="User")

    print("📝 创建的 TextMessage:")
    print(f"  Content: {text_message.content}")
    print(f"  Source: {text_message.source}")
    print(f"  Type: {type(text_message).__name__}")

    # 获取配置
    settings = get_settings()

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
    )

    agent = AssistantAgent("assistant", model_client=model_client, system_message="You are a helpful AI assistant.")

    # 将 TextMessage 作为任务传递给团队
    print("\n📝 将 TextMessage 作为任务传递给 Agent:")
    result = await agent.run(task=text_message)

    print(f"\n📊 Agent 的响应:")
    print(f"{result.messages[-1].content}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 2: 创建多模态消息 =====
async def demo_multimodal_message():
    """演示 2: 创建和使用 MultiModalMessage"""
    print("=" * 80)
    print("演示 2: MultiModalMessage - 多模态消息")
    print("=" * 80 + "\n")

    print("📝 下载图像...")
    # 从 URL 获取图像
    response = requests.get("https://picsum.photos/300/200")
    pil_image = Image.open(BytesIO(response.content))

    # 将 PIL 图像转换为 AutoGen Image 对象
    img = AGImage(pil_image)

    print(f"📝 图像信息:")
    print(f"  尺寸: {pil_image.size}")
    print(f"  模式: {pil_image.mode}")

    # 创建多模态消息
    # MultiModalMessage 接受字符串或 Image 对象的列表
    multi_modal_message = MultiModalMessage(
        content=["Can you describe the content of this image?", img], source="User"
    )

    print(f"\n📝 创建的 MultiModalMessage:")
    print(f"  Content items: {len(multi_modal_message.content)}")
    print(f"  Source: {multi_modal_message.source}")
    print(f"  Type: {type(multi_modal_message).__name__}")

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
        system_message="You are a helpful AI assistant. Describe images in detail.",
    )

    # 将 MultiModalMessage 作为任务传递给团队
    print("\n📝 将 MultiModalMessage 作为任务传递给 Agent:")
    result = await agent.run(task=multi_modal_message)

    print(f"\n📊 Agent 的响应:")
    print(f"{result.messages[-1].content}")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 3: 内部事件 =====
async def demo_internal_events():
    """演示 3: 理解和使用内部事件"""
    print("=" * 80)
    print("演示 3: Internal Events - 内部事件")
    print("=" * 80 + "\n")

    # 获取配置
    settings = get_settings()

    # 定义一个工具
    def get_weather(location: str) -> str:
        """获取指定位置的天气信息"""
        return f"The weather in {location} is sunny and 25°C."

    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None,
    )

    agent = AssistantAgent(
        "assistant",
        model_client=model_client,
        tools=[get_weather],
        system_message="You are a helpful AI assistant. Use tools when needed.",
    )

    print("📝 Agent 使用工具时会产生内部事件:")
    print("  - ToolCallRequestEvent: 工具调用请求事件")
    print("  - ToolCallExecutionEvent: 工具调用执行事件")

    result = await agent.run(task="What is the weather in Paris?")

    print(f"\n📊 消息历史 (包括内部事件):")
    for i, message in enumerate(result.messages, 1):
        message_type = type(message).__name__
        print(f"\n{i}. 类型: {message_type}")
        print(f"   来源: {message.source}")

        # 显示不同类型消息的特定信息
        if message_type == "ToolCallRequestEvent":
            print(f"   内容: 工具调用请求")
            if hasattr(message, "content"):
                for call in message.content:
                    print(f"     - 工具名: {call.name}")
                    print(f"       参数: {call.arguments}")

        elif message_type == "ToolCallExecutionEvent":
            print(f"   内容: 工具调用执行结果")
            if hasattr(message, "content"):
                for execution in message.content:
                    print(f"     - 工具名: {execution.name}")
                    print(f"       结果: {execution.content}")

        elif message_type == "ToolCallSummaryMessage":
            print(f"   内容: {message.content}")

        elif message_type == "TextMessage":
            content_preview = str(message.content)[:100]
            print(f"   内容: {content_preview}...")

    await model_client.close()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 演示 4: 消息类型总结 =====
async def demo_message_types_summary():
    """演示 4: AutoGen 消息类型总结"""
    print("=" * 80)
    print("演示 4: AutoGen 消息类型总结")
    print("=" * 80 + "\n")

    print("📚 Agent-Agent Messages (ChatMessage):")
    print("  这些消息用于 Agent 之间的通信")
    print("  - TextMessage: 纯文本消息")
    print("  - MultiModalMessage: 多模态消息 (文本 + 图像等)")

    print("\n📚 Internal Events (AgentEvent):")
    print("  这些消息是 Agent 内部的事件和信息")
    print("  - ToolCallRequestEvent: 工具调用请求")
    print("  - ToolCallExecutionEvent: 工具调用执行结果")
    print("  - ToolCallSummaryMessage: 工具调用摘要")

    print("\n📚 消息使用场景:")
    print("  1. 通过 on_messages 方法直接传递给 Agent")
    print("  2. 作为任务传递给团队的 run() 方法")
    print("  3. 包含在 Agent 的响应中")
    print("  4. 内部事件通常在 Response 的 inner_messages 字段中")

    print("\n📚 创建消息示例:")
    print("  # 文本消息")
    print('  text_message = TextMessage(content="Hello", source="User")')

    print("\n  # 多模态消息")
    print("  multi_modal_message = MultiModalMessage(")
    print('      content=["Describe this", image],')
    print('      source="User"')
    print("  )")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - Messages")
    print("=" * 80 + "\n")

    try:
        # 演示 1: TextMessage
        await demo_text_message()

        # 演示 2: MultiModalMessage
        await demo_multimodal_message()

        # 演示 3: Internal Events
        await demo_internal_events()

        # 演示 4: 消息类型总结
        await demo_message_types_summary()

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

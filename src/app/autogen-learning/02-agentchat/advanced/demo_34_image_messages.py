"""
Demo 34: 图像消息 - 多模态交互

本演示展示如何:
1. 处理图像输入
2. 视觉理解
3. 图文结合对话
4. 多模态工具使用
5. 视觉-文本混合输出

运行方式:
    python demo_34_image_messages.py

前置要求:
    - 已配置 OPENAI_API_KEY（需要支持 Vision 的模型）
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解记忆管理和人工交互基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/multimodal.html
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
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示函数 =====
async def demo_image_description():
    """演示 1: 图像描述"""
    print("=" * 80)
    print("演示 1: 图像描述和分析")

    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建视觉 Agent
    vision_agent = AssistantAgent(
        name="vision_agent",
        model_client=model_client,
        description="你是一个视觉理解助手，可以描述和分析图像内容。"
    )

    print("💬 图像描述测试")
    print()

    # 模拟图像输入（实际中会传递真实的图像数据）
    image_scenarios = [
        {
            "description": "一张风景照片",
            "features": ["山脉", "蓝天", "绿色树木", "清澈的湖泊"]
        },
        {
            "description": "一张城市街道照片",
            "features": ["现代化建筑", "繁忙的交通", "行人", "商店招牌"]
        },
        {
            "description": "一张产品照片",
            "features": ["包装精美的产品", "白色背景", "品牌标志", "产品名称"]
        }
    ]

    for i, scenario in enumerate(image_scenarios, 1):
        print(f"\n{'─' * 40}")
        print(f"场景 {i}: {scenario['description']}")
        print(f"{'─' * 40}\n")

        # 构建图像描述任务
        task = f"""我有一张图片，内容是：{scenario['description']}
        图片中包含以下特征：{', '.join(scenario['features'])}

请：
1. 详细描述这张图片
2. 识别图片中的主要元素
3. 分析图片的风格和氛围
4. 提供任何有趣的观察"""

        print(f"👤 任务:")
        print(task[:200] + "...")
        print()

        result = await vision_agent.run(task=task)

        print(f"🤖 Agent 分析:")
        for message in result.messages:
            # 限制输出长度
            content = message.content[:300] + "..." if len(message.content) > 300 else message.content
            print(f"{content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_text_with_image():
    """演示 2: 图文结合对话"""
    print("=" * 80)
    print("演示 2: 图文结合对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建多模态 Agent
    multimodal_agent = AssistantAgent(
        name="multimodal_agent",
        model_client=model_client,
        description="你是一个多模态助手，可以同时处理文本和图像输入。"
    )

    print("💬 图文结合测试")
    print()

    # 测试场景
    test_cases = [
        {
            "image": "一张显示复杂数据图表的图片",
            "text": "请分析这个图表中的数据趋势"
        },
        {
            "image": "一张包含多个步骤的流程图",
            "text": "总结这个流程图的关键步骤"
        },
        {
            "image": "一张代码编辑器界面截图",
            "text": "指出代码中的潜在问题和改进建议"
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 40}")
        print(f"测试 {i}: {test_case['image']}")
        print(f"{'─' * 40}\n")

        task = f"""图像描述：{test_case['image']}
文本问题：{test_case['text']}

请结合图像和文本回答问题。"""
        
        print(f"👤 任务:")
        print(task[:150] + "...")
        print()

        result = await multimodal_agent.run(task=task)

        print(f"🤖 Agent 响应:")
        for message in result.messages:
            content = message.content[:250] + "..." if len(message.content) > 250 else message.content
            print(f"{content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_comparison_analysis():
    """演示 3: 图像比较分析"""
    print("=" * 80)
    print("演示 3: 图像比较分析")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建分析 Agent
    analyst_agent = AssistantAgent(
        name="analyst_agent",
        model_client=model_client,
        description="你是一个图像分析专家，擅长比较和分析多张图片。"
    )

    print("💬 图像比较测试")
    print()

    # 模拟多张图像
    image_sets = [
        {
            "set": "产品照片对比",
            "images": [
                "产品 A 的照片（正面视角）",
                "产品 A 的照片（侧面视角）",
                "产品 B 的照片（正面视角）"
            ]
        },
        {
            "set": "前后对比照片",
            "images": [
                "修复前的状态照片",
                "修复后的状态照片"
            ]
        }
    ]

    for i, image_set in enumerate(image_sets, 1):
        print(f"\n{'─' * 40}")
        print(f"图像集 {i}: {image_set['set']}")
        print(f"{'─' * 40}\n")

        task = f"""分析以下多张图片：
{chr(10).join([f"{j+1}. {img}" for j, img in enumerate(image_set['images'], 1)])}

请：
1. 比较图片之间的相似性和差异
2. 识别关键变化
3. 提供分析和总结
4. 给出可能的结论"""

        print(f"👤 任务:")
        print(task[:150] + "...")
        print()

        result = await analyst_agent.run(task=task)

        print(f"🤖 Agent 分析:")
        for message in result.messages:
            content = message.content[:300] + "..." if len(message.content) > 300 else message.content
            print(f"{content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_visual_qa():
    """演示 4: 视觉问答"""
    print("=" * 80)
    print("演示 4: 视觉问答")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建问答 Agent
    qa_agent = AssistantAgent(
        name="visual_qa_agent",
        model_client=model_client,
        description="你是一个视觉问答专家，能够基于图像回答相关问题。"
    )

    print("💬 视觉问答测试")
    print()

    # 问答场景
    qa_scenarios = [
        {
            "image": "一张包含多种水果的图片",
            "questions": ["图片中有几种水果？", "它们分别是什么？", "主要是什么颜色？"]
        },
        {
            "image": "一张办公室布局图",
            "questions": ["桌椅如何排列？", "有几个工作站？", "有什么办公设备？"]
        },
        {
            "image": "一张交通标志图",
            "questions": ["这是什么标志？", "它的含义是什么？", "在什么场景下使用？"]
        }
    ]

    for i, scenario in enumerate(qa_scenarios, 1):
        print(f"\n{'─' * 40}")
        print(f"场景 {i}: {scenario['image']}")
        print(f"{'─' * 40}\n")

        # 构建问答任务
        questions_text = "\n".join([
            f"{j+1}. {q}" for j, q in enumerate(scenario['questions'], 1)
        ])

        task = f"""图像描述：{scenario['image']}

请回答以下问题：
{questions_text}"""

        print(f"👤 任务:")
        print(task[:200] + "...")
        print()

        result = await qa_agent.run(task=task)

        print(f"🤖 Agent 答案:")
        for message in result.messages:
            content = message.content[:300] + "..." if len(message.content) > 300 else message.content
            print(f"{content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_document_understanding():
    """演示 5: 文档理解"""
    print("=" * 80)
    print("演示 5: 文档理解")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建文档理解 Agent
    doc_agent = AssistantAgent(
        name="doc_understanding_agent",
        model_client=model_client,
        description="你是一个文档理解专家，可以读取和分析文档图片。"
    )

    print("💬 文档理解测试")
    print()

    # 文档场景
    document_scenarios = [
        {
            "type": "发票",
            "image": "一张发票的扫描图片",
            "info": "需要提取：发票号码、日期、金额、项目"
        },
        {
            "type": "表格",
            "image": "一张复杂数据表格图片",
            "info": "需要提取：表格结构、数据内容、关键信息"
        },
        {
            "type": "图表",
            "image": "一张包含多个图表的图片",
            "info": "需要提取：每个图表的类型、数据趋势、结论"
        }
    ]

    for i, doc_scenario in enumerate(document_scenarios, 1):
        print(f"\n{'─' * 40}")
        print(f"场景 {i}: {doc_scenario['type']}文档")
        print(f"{'─' * 40}\n")

        task = f"""文档类型：{doc_scenario['type']}
文档描述：{doc_scenario['image']}

需要提取的信息：
{doc_scenario['info']}

请仔细分析文档并提取所需信息。"""

        print(f"👤 任务:")
        print(task[:150] + "...")
        print()

        result = await doc_agent.run(task=task)

        print(f"🤖 Agent 分析:")
        for message in result.messages:
            content = message.content[:300] + "..." if len(message.content) > 300 else message.content
            print(f"{content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔══════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - 图像消息演示              ║
║           Multimodal Image Messages                    ║
║                                                                ║
╚══════════════════════════════════════════════════════╝
    """)
    print("=" * 80 + "\n")

    try:
        # 检查 API Key
        settings = get_settings()
        if not settings.openai_api_key:
            print("❌ 错误: 未配置 OPENAI_API_KEY")
            print("   请在 .env 文件中设置 OPENAI_API_KEY")
            return

        # 演示 1: 图像描述
        await demo_image_description()

        # 演示 2: 图文结合
        await demo_text_with_image()

        # 演示 3: 图像比较
        await demo_comparison_analysis()

        # 演示 4: 视觉问答
        await demo_visual_qa()

        # 演示 5: 文档理解
        await demo_document_understanding()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 多模态处理结合了视觉和文本输入")
        print("  ✓ 视觉理解可以分析图像内容和特征")
        print("  ✓ 图文结合提供了更丰富的交互方式")
        print("  ✓ 图像比较可以发现差异和变化")
        print("  ✓ 视觉问答可以实现图片问答功能")
        print("  ✓ 文档理解可以提取结构化信息")
        print()
        print("注意事项:")
        print("  - 需要支持 Vision 的模型（如 GPT-4V）")
        print("  - 图像数据通过消息类型传递")
        print("  - 可以与其他功能（记忆、工具）结合使用")
        print()
        print("下一步:")
        print("  1. 查看 03-extensions/ 学习扩展功能")
        print("  2. 查看 04-integration/ 学习集成案例")
        print("  3. 查看 examples/ 目录学习实际应用")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
"""
Demo 23: 简单对话 - 两个 Agent 之间的基本交互

本演示展示如何:
1. 在两个 Agent 之间建立对话
2. 管理消息的传递
3. 维护对话历史
4. 处理简单的交互场景

运行方式:
    python demo_23_simple_conversation.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 AssistantAgent 基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/conversation.html
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
async def demo_two_agent_conversation():
    """演示 1: 两个 Agent 的简单对话"""
    print("=" * 80)
    print("演示 1: 两个 Agent 的简单对话")

    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建两个不同角色的 Agent
    teacher = AssistantAgent(
        name="teacher",
        model_client=model_client,
        description="你是一位知识渊博的老师，擅长用简单易懂的方式解释复杂的概念。"
    )

    student = AssistantAgent(
        name="student",
        model_client=model_client,
        description="你是一位好奇的学生，喜欢提问，并且会根据老师的回答继续深入学习。"
    )

    print("💬 对话场景: 学生向老师提问")
    print()

    # 学生提出问题
    initial_question = "老师，你能简单解释一下什么是机器学习吗？"
    print(f"👥 {student.name}: {initial_question}")
    print()

    # 老师回答
    teacher_result = await teacher.run(task=initial_question)
    teacher_answer = teacher_result.messages[-1].content
    print(f"👥 {teacher.name}: {teacher_answer[:300]}...")
    print()

    # 学生根据回答继续提问
    followup_question = f"谢谢老师！基于你的解释，我想知道：机器学习和传统的编程有什么区别？"
    print(f"👥 {student.name}: {followup_question}")
    print()

    # 老师再次回答
    teacher_result2 = await teacher.run(
        task=followup_question,
        conversation_history=[
            {"role": "user", "content": initial_question},
            {"role": "assistant", "content": teacher_answer},
            {"role": "user", "content": followup_question}
        ]
    )
    teacher_answer2 = teacher_result2.messages[-1].content
    print(f"👥 {teacher.name}: {teacher_answer2[:300]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_expert_consultation():
    """演示 2: 专家咨询对话"""
    print("=" * 80)
    print("演示 2: 专家咨询对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同领域的专家
    business_expert = AssistantAgent(
        name="business_expert",
        model_client=model_client,
        description="你是一位商业分析师，擅长从商业角度分析问题和提供商业建议。"
    )

    technical_expert = AssistantAgent(
        name="technical_expert",
        model_client=model_client,
        description="你是一位技术专家，擅长从技术角度评估方案并提供技术建议。"
    )

    print("💬 场景: 商业产品评估")
    print()

    # 商业专家提出问题
    business_question = "我们计划开发一个 AI 客服系统。从商业角度来看，有哪些关键成功因素？"
    print(f"👥 {business_expert.name}: {business_question}")
    print()

    # 商业专家回答自己的问题（模拟商业分析）
    business_result = await business_expert.run(task=business_question)
    business_answer = business_result.messages[-1].content
    print(f"👥 {business_expert.name} (分析): {business_answer[:400]}...")
    print()

    # 技术专家从技术角度评估
    technical_question = f"从技术角度评估这个 AI 客服系统：{business_question}"
    print(f"👥 {technical_expert.name}: {technical_question}")
    print()

    technical_result = await technical_expert.run(task=technical_question)
    technical_answer = technical_result.messages[-1].content
    print(f"👥 {technical_expert.name} (分析): {technical_answer[:400]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_collaborative_problem_solving():
    """演示 3: 协作问题解决"""
    print("=" * 80)
    print("演示 3: 协作问题解决")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建协作的 Agent
    analyst = AssistantAgent(
        name="analyst",
        model_client=model_client,
        description="你是一位分析师，擅长分析问题、收集信息和提出建议。"
    )

    planner = AssistantAgent(
        name="planner",
        model_client=model_client,
        description="你是一位规划师，擅长制定计划、安排步骤和协调资源。"
    )

    print("💬 协作场景: 活动策划")
    print()

    # 分析师分析需求
    analyst_task = "我们需要策划一个团队建设活动，有 20 人参加，预算 5000 元，时长 1 天。请分析关键需求。"
    print(f"👥 {analyst.name}: {analyst_task}")
    print()

    analyst_result = await analyst.run(task=analyst_task)
    analyst_output = analyst_result.messages[-1].content
    print(f"👥 {analyst.name} (分析结果): {analyst_output[:300]}...")
    print()

    # 规划师根据分析制定计划
    planner_task = f"""基于以下分析，制定详细的执行计划：
{analyst_output[:500]}...

请提供：
1. 具体的活动安排
2. 时间分配
3. 预算分解
4. 注意事项
"""
    print(f"👥 {planner.name}: 开始制定计划...")
    print()

    planner_result = await planner.run(task=planner_task)
    planner_output = planner_result.messages[-1].content
    print(f"👥 {planner.name} (计划): {planner_output[:400]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_feedback_loop():
    """演示 4: 反馈循环对话"""
    print("=" * 80)
    print("演示 4: 反馈循环对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建反馈循环的 Agent
    writer = AssistantAgent(
        name="writer",
        model_client=model_client,
        description="你是一位内容创作者，根据反馈改进你的作品。"
    )

    reviewer = AssistantAgent(
        name="reviewer",
        model_client=model_client,
        description="你是一位内容审查员，提供建设性的反馈和改进建议。"
    )

    print("💬 反馈循环场景: 文章创作与审查")
    print()

    # 创作者创建初稿
    writer_task = "写一段关于'人工智能在医疗领域的应用'的简介，大约 100 字。"
    print(f"👥 {writer.name}: {writer_task}")
    print()

    writer_result = await writer.run(task=writer_task)
    first_draft = writer_result.messages[-1].content
    print(f"👥 {writer.name} (初稿): {first_draft}")
    print()

    # 审查者提供反馈
    reviewer_task = f"请审查以下内容并提供改进建议：\n{first_draft}"
    print(f"👥 {reviewer.name}: 开始审查...")
    print()

    reviewer_result = await reviewer.run(task=reviewer_task)
    feedback = reviewer_result.messages[-1].content
    print(f"👥 {reviewer.name} (反馈): {feedback[:300]}...")
    print()

    # 创作者根据反馈修改
    revision_task = f"根据以下反馈改进你的初稿：\n{feedback}\n\n原初稿：\n{first_draft}"
    print(f"👥 {writer.name}: 根据反馈修改...")
    print()

    revision_result = await writer.run(task=revision_task)
    revised_draft = revision_result.messages[-1].content
    print(f"👥 {writer.name} (修改稿): {revised_draft}")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_cross_domain_collaboration():
    """演示 5: 跨领域协作"""
    print("=" * 80)
    print("演示 5: 跨领域协作对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同领域的专家
    designer = AssistantAgent(
        name="designer",
        model_client=model_client,
        description="你是一位设计师，关注用户体验、界面美感和交互设计。"
    )

    developer = AssistantAgent(
        name="developer",
        model_client=model_client,
        description="你是一位开发者，关注技术实现、性能优化和代码质量。"
    )

    print("💬 跨领域场景: 移动应用设计")
    print()

    # 设计师提出设计想法
    design_idea = """我设计了一个移动应用的主界面：
- 使用全屏背景图片
- 大量的动画效果
- 玻璃拟态设计风格
- 多个浮动按钮

从用户体验角度看，这样能提供沉浸式体验。"""
    print(f"👥 {designer.name}: {design_idea[:200]}...")
    print()

    # 开发者从技术角度评估
    dev_assessment = """从技术实现角度评估这个设计：
1. 全屏背景可能影响性能
2. 大量动画会增加资源消耗
3. 玻璃拟态在不同设备上兼容性问题
4. 浮动按钮可能遮挡内容

建议优化方案。"""
    print(f"👥 {developer.name}: {dev_assessment[:200]}...")
    print()

    # 开发者提供具体建议
    developer_task = f"基于设计师的上述想法，提供具体的技术优化建议"
    developer_result = await developer.run(task=developer_task)
    dev_suggestions = developer_result.messages[-1].content
    print(f"👥 {developer.name} (建议): {dev_suggestions[:400]}...")
    print()

    # 设计师根据建议调整
    designer_task = f"根据开发者的以下建议调整设计：\n{dev_suggestions[:500]}..."
    designer_result = await designer.run(task=designer_task)
    adjusted_design = designer_result.messages[-1].content
    print(f"👥 {designer.name} (调整后): {adjusted_design[:400]}...")
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
║          AutoGen 0.4+ - 简单对话演示                   ║
║           Multi-Agent Basic Conversations                    ║
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

        # 演示 1: 两个 Agent 的简单对话
        await demo_two_agent_conversation()

        # 演示 2: 专家咨询对话
        await demo_expert_consultation()

        # 演示 3: 协作问题解决
        await demo_collaborative_problem_solving()

        # 演示 4: 反馈循环
        await demo_feedback_loop()

        # 演示 5: 跨领域协作
        await demo_cross_domain_collaboration()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 两个或多个 Agent 可以通过消息进行对话")
        print("  ✓ 每个可以有不同的角色和专业领域")
        print("  ✓ 对话历史可以传递以保持上下文")
        print("  ✓ 可以实现协作、反馈循环等复杂交互模式")
        print()
        print("下一步:")
        print("  1. 查看 demo_24_sequential_conversation.py 学习序列对话")
        print("  2. 查看 demo_25_conversation_termination.py 学习终止控制")
        print("  3. 查看 teams/ 目录学习团队协作")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
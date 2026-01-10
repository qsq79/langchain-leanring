"""
Demo 24: 序列对话 - 链式对话模式

本演示展示如何:
1. 实现链式对话流程
2. 将一个 Agent 的输出作为另一个 Agent 的输入
3. 处理多步骤任务
4. 管理复杂的对话依赖关系
5. 实现流水线式处理

运行方式:
    python demo_24_sequential_conversation.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解简单对话基础

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
async def demo_basic_sequential():
    """演示 1: 基本序列对话"""
    print("=" * 80)
    print("演示 1: 基本序列对话")

    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建三个不同角色的 Agent
    researcher = AssistantAgent(
        name="researcher",
        model_client=model_client,
        description="你是一位研究员，擅长收集和整理信息。"
    )

    analyzer = AssistantAgent(
        name="analyzer",
        model_client=model_client,
        description="你是一位分析师，擅长分析和总结信息。"
    )

    presenter = AssistantAgent(
        name="presenter",
        model_client=model_client,
        description="你是一位展示专家，擅长用清晰易懂的方式呈现信息。"
    )

    print("💬 序列流程: 研究 -> 分析 -> 展示")
    print()

    # 步骤 1: 研究员收集信息
    research_task = "收集关于'气候变化对农业影响'的 3 个关键点"
    print(f"步骤 1 - {researcher.name}: {research_task}")
    
    research_result = await researcher.run(task=research_task)
    research_output = research_result.messages[-1].content
    print(f"结果: {research_output[:200]}...")
    print()

    # 步骤 2: 分析师分析研究结果
    analysis_task = f"""分析以下研究内容，并提供深入见解：
{research_output}

请总结：
1. 主要发现
2. 潜在影响
3. 应对措施建议
"""
    print(f"步骤 2 - {analyzer.name}: 分析研究内容...")
    
    analysis_result = await analyzer.run(task=analysis_task)
    analysis_output = analysis_result.messages[-1].content
    print(f"结果: {analysis_output[:200]}...")
    print()

    # 步骤 3: 展示专家呈现最终报告
    presentation_task = f"""将以下分析内容整理成一份简明扼要的报告，面向普通读者：
{analysis_output}

要求：
1. 使用简单的语言
2. 突出重点
3. 结构清晰
"""
    print(f"步骤 3 - {presenter.name}: 整理最终报告...")
    
    presentation_result = await presenter.run(task=presentation_task)
    final_output = presentation_result.messages[-1].content
    print(f"最终结果: {final_output[:300]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_pipeline_processing():
    """演示 2: 流水线处理"""
    print("=" * 80)
    print("演示 2: 流水线处理模式")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建流水线 Agent
    collector = AssistantAgent(
        name="collector",
        model_client=model_client,
        description="你负责收集原始数据和用户需求。"
    )

    validator = AssistantAgent(
        name="validator",
        model_client=model_client,
        description="你负责验证数据的完整性和合理性。"
    )

    processor = AssistantAgent(
        name="processor",
        model_client=model_client,
        description="你负责处理数据并生成输出结果。"
    )

    quality_checker = AssistantAgent(
        name="quality_checker",
        model_client=model_client,
        description="你负责检查输出质量，确保符合标准。"
    )

    print("💬 流水线: 收集 -> 验证 -> 处理 -> 质检")
    print()

    # 原始输入
    user_request = "我需要一份关于'远程工作效率'的调查报告模板"
    print(f"输入: {user_request}")
    print()

    # 阶段 1: 收集
    collect_result = await collector.run(
        task=f"收集以下需求的关键信息：{user_request}"
    )
    collected_data = collect_result.messages[-1].content
    print(f"阶段 1 - 收集: {collected_data[:150]}...")
    print()

    # 阶段 2: 验证
    validate_result = await validator.run(
        task=f"验证以下收集的信息是否完整和合理：\n{collected_data}"
    )
    validation_result = validate_result.messages[-1].content
    print(f"阶段 2 - 验证: {validation_result[:150]}...")
    print()

    # 阶段 3: 处理
    process_result = await processor.run(
        task=f"""基于以下信息生成调查报告模板：
收集信息：{collected_data}
验证结果：{validation_result}

请创建一个完整的调查报告模板。"""
    )
    processed_output = process_result.messages[-1].content
    print(f"阶段 3 - 处理: {processed_output[:150]}...")
    print()

    # 阶段 4: 质检
    check_result = await quality_checker.run(
        task=f"""检查以下模板的质量：
{processed_output[:500]}

评估：
1. 结构是否合理
2. 问题是否全面
3. 是否符合调查报告标准
"""
    )
    quality_report = check_result.messages[-1].content
    print(f"阶段 4 - 质检: {quality_report[:200]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_feedback_enhanced_sequential():
    """演示 3: 带反馈的序列对话"""
    print("=" * 80)
    print("演示 3: 带反馈的序列对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建带反馈机制的 Agent
    planner = AssistantAgent(
        name="planner",
        model_client=model_client,
        description="你负责制定计划和方案。"
    )

    reviewer = AssistantAgent(
        name="reviewer",
        model_client=model_client,
        description="你负责审查计划并提供改进建议。"
    )

    finalizer = AssistantAgent(
        name="finalizer",
        model_client=model_client,
        description="你负责根据反馈完善最终方案。"
    )

    print("💬 带反馈流程: 计划 -> 审查 -> 改进 -> 最终")
    print()

    # 迭代 1: 初始计划
    plan_task = "制定一个'新产品发布会'的执行计划"
    print(f"迭代 1 - {planner.name}: 制定初始计划...")
    
    plan_result = await planner.run(task=plan_task)
    initial_plan = plan_result.messages[-1].content
    print(f"初始计划: {initial_plan[:200]}...")
    print()

    # 迭代 2: 审查
    review_task = f"""审查以下计划并提供改进建议：
{initial_plan}

重点关注：
1. 时间安排是否合理
2. 资源分配是否充足
3. 风险是否考虑充分
"""
    print(f"迭代 2 - {reviewer.name}: 审查计划...")
    
    review_result = await reviewer.run(task=review_task)
    review_feedback = review_result.messages[-1].content
    print(f"审查反馈: {review_feedback[:200]}...")
    print()

    # 迭代 3: 根据反馈改进
    improve_task = f"""根据以下反馈改进计划：
原始计划：{initial_plan}
反馈建议：{review_feedback}

请提供改进后的完整计划。"""
    print(f"迭代 3 - {finalizer.name}: 根据反馈改进计划...")
    
    improved_result = await finalizer.run(task=improve_task)
    improved_plan = improved_result.messages[-1].content
    print(f"改进计划: {improved_plan[:200]}...")
    print()

    # 迭代 4: 最终审查
    final_review_task = f"对改进后的计划进行最终审查：\n{improved_plan}"
    print(f"迭代 4 - {reviewer.name}: 最终审查...")
    
    final_review_result = await reviewer.run(task=final_review_task)
    final_assessment = final_review_result.messages[-1].content
    print(f"最终评估: {final_assessment[:200]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_branch_sequential():
    """演示 4: 多分支序列对话"""
    print("=" * 80)
    print("演示 4: 多分支序列对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同领域的专家
    business_analyst = AssistantAgent(
        name="business_analyst",
        model_client=model_client,
        description="你从商业角度分析问题和提供解决方案。"
    )

    technical_expert = AssistantAgent(
        name="technical_expert",
        model_client=model_client,
        description="你从技术角度分析问题和提供解决方案。"
    )

    user_experience_designer = AssistantAgent(
        name="ux_designer",
        model_client=model_client,
        description="你从用户体验角度分析问题和提供解决方案。"
    )

    integrator = AssistantAgent(
        name="integrator",
        model_client=model_client,
        description="你整合不同角度的意见，提供综合建议。"
    )

    print("💬 多分支流程: 问题分析 -> (商业/技术/UX并行) -> 整合")
    print()

    # 共同的问题
    problem = "开发一个移动端健康管理应用"
    print(f"问题: {problem}")
    print()

    # 分支 1: 商业分析
    print(f"分支 1 - {business_analyst.name}: 商业分析...")
    business_result = await business_analyst.run(
        task=f"从商业角度分析开发{problem}的可行性和市场机会"
    )
    business_analysis = business_result.messages[-1].content
    print(f"商业分析: {business_analysis[:150]}...")
    print()

    # 分支 2: 技术分析
    print(f"分支 2 - {technical_expert.name}: 技术分析...")
    technical_result = await technical_expert.run(
        task=f"从技术角度分析开发{problem}的技术挑战和实现方案"
    )
    technical_analysis = technical_result.messages[-1].content
    print(f"技术分析: {technical_analysis[:150]}...")
    print()

    # 分支 3: UX 分析
    print(f"分支 3 - {user_experience_designer.name}: UX 分析...")
    ux_result = await user_experience_designer.run(
        task=f"从用户体验角度分析{problem}的设计需求和用户期望"
    )
    ux_analysis = ux_result.messages[-1].content
    print(f"UX 分析: {ux_analysis[:150]}...")
    print()

    # 整合
    print(f"{integrator.name}: 整合所有分析...")
    integration_task = f"""整合以下三个角度的分析，提供综合建议：

商业分析：
{business_analysis[:300]}

技术分析：
{technical_analysis[:300]}

UX 分析：
{ux_analysis[:300]}

请提供：
1. 优先级排序
2. 关键成功因素
3. 实施建议
"""
    integration_result = await integrator.run(task=integration_task)
    final_recommendation = integration_result.messages[-1].content
    print(f"综合建议: {final_recommendation[:300]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_sequential_with_context_accumulation():
    """演示 5: 上下文累积的序列对话"""
    print("=" * 80)
    print("演示 5: 上下文累积的序列对话")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建累积上下文的 Agent
    information_gatherer = AssistantAgent(
        name="information_gatherer",
        model_client=model_client,
        description="你负责收集初始信息。"
    )

    context_builder = AssistantAgent(
        name="context_builder",
        model_client=model_client,
        description="你负责构建上下文和场景。"
    )

    solution_generator = AssistantAgent(
        name="solution_generator",
        model_client=model_client,
        description="你负责基于完整上下文生成解决方案。"
    )

    print("💬 上下文累积: 信息收集 -> 上下文构建 -> 方案生成")
    print()

    # 累积的上下文
    accumulated_context = []

    # 步骤 1: 收集基础信息
    info_task = "收集关于'企业数字化转型'的背景信息、挑战和机遇"
    print(f"步骤 1 - {information_gatherer.name}: 收集基础信息...")
    
    info_result = await information_gatherer.run(task=info_task)
    info_output = info_result.messages[-1].content
    accumulated_context.append(f"基础信息：{info_output}")
    print(f"收集结果: {info_output[:150]}...")
    print()

    # 步骤 2: 构建场景
    context_task = f"""基于以下信息构建详细的转型场景：
{info_output}

请描述：
1. 具体的转型场景
2. 涉及的业务流程
3. 关键利益相关者
"""
    print(f"步骤 2 - {context_builder.name}: 构建场景...")
    
    context_result = await context_builder.run(task=context_task)
    context_output = context_result.messages[-1].content
    accumulated_context.append(f"场景描述：{context_output}")
    print(f"场景描述: {context_output[:150]}...")
    print()

    # 步骤 3: 生成方案（使用累积的上下文）
    solution_task = f"""基于完整的上下文信息生成数字化转型方案：

{accumulated_context[0]}

{accumulated_context[1]}

请提供：
1. 分阶段实施计划
2. 资源配置建议
3. 风险管控措施
4. 成功评估指标
"""
    print(f"步骤 3 - {solution_generator.name}: 生成完整方案...")
    
    solution_result = await solution_generator.run(task=solution_task)
    final_solution = solution_result.messages[-1].content
    print(f"最终方案: {final_solution[:300]}...")
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
║          AutoGen 0.4+ - 序列对话演示                   ║
║           Sequential Conversation Patterns                   ║
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

        # 演示 1: 基本序列对话
        await demo_basic_sequential()

        # 演示 2: 流水线处理
        await demo_pipeline_processing()

        # 演示 3: 带反馈的序列对话
        await demo_feedback_enhanced_sequential()

        # 演示 4: 多分支序列对话
        await demo_multi_branch_sequential()

        # 演示 5: 上下文累积
        await demo_sequential_with_context_accumulation()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 序列对话可以实现链式处理流程")
        print("  ✓ 每个 Agent 的输出可以作为下一个 Agent 的输入")
        print("  ✓ 可以实现流水线式的自动化处理")
        print("  ✓ 支持反馈循环和迭代改进")
        print("  ✓ 可以累积和传递上下文信息")
        print()
        print("下一步:")
        print("  1. 查看 demo_25_conversation_termination.py 学习终止控制")
        print("  2. 查看 teams/ 目录学习团队协作")
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
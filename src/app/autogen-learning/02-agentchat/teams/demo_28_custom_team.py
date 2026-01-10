"""
Demo 28: 自定义团队 - 自定义协作模式

本演示展示如何:
1. 创建自定义团队逻辑
2. 实现复杂的工作流程
3. 集成特定的业务规则
4. 灵活控制 Agent 交互
5. 实现自定义终止条件

运行方式:
    python demo_28_custom_team.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 RoundRobin 和 Selector 团队

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html
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


class CustomTeam:
    """自定义团队类，实现特定的工作流程"""
    
    def __init__(self, name: str, workflow: dict):
        self.name = name

        self.workflow = workflow  # 定义工作流程的字典
    
    async def execute_workflow(self, task: str):
        """执行自定义工作流程"""
        print(f"\n{'=' * 60}")
        print(f"📋 自定义团队: {self.name}")
        print(f"   任务: {task}")
        print('=' * 60 + "\n")
        
        context = {"task": task, "results": {}}
        
        # 按工作流程步骤执行
        for step_name, step_config in self.workflow.items():
            print(f"\n📍 步骤: {step_name}")
            agent = step_config["agent"]
            
            result = await agent.run(
                task=self._build_step_task(step_config, context),
                conversation_history=context.get("conversation_history", [])
            )
            
            output = result.messages[-1].content
            print(f"{agent.name}: {output[:200]}...")
            
            context["results"][step_name] = output
            context["conversation_history"] = context.get("conversation_history", [])
            context["conversation_history"].append({"role": "assistant", "content": output})
        
        return context
    
    def _build_step_task(self, step_config: dict, context: dict) -> str:
        """构建步骤任务"""
        task_template = step_config.get("task", "{task}")
        return task_template.format(**context)


# ===== 演示函数 =====
async def demo_pipeline_workflow():
    """演示 1: 流水线工作流"""
    print("=" * 80)
    print("演示 1: 流水线工作流")
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
        description="你负责收集和整理信息。"
    )

    analyzer = AssistantAgent(
        name="analyzer",
        model_client=model_client,
        description="你负责分析信息和提供见解。"
    )

    reporter = AssistantAgent(
        name="reporter",
        model_client=model_client,
        description="你负责生成最终报告和总结。"
    )

    # 定义流水线工作流程
    workflow = {
        "收集": {
            "agent": collector,
            "task": "收集关于 '{task}' 的关键信息"
        },
        "分析": {
            "agent": analyzer,
            "task": "基于收集的信息，分析 '{task}' 的主要方面:\n{results[收集]}"
        },
        "报告": {
            "agent": reporter,
            "task": "基于分析结果，生成关于 '{task}' 的综合报告:\n{results[分析]}"
        }
    }

    # 创建自定义团队
    pipeline_team = CustomTeam(
        name="数据处理流水线",
        workflow=workflow
    )

    # 执行工作流
    result = await pipeline_team.execute_workflow("人工智能在医疗领域的应用")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_review_loop_workflow():
    """演示 2: 审查循环工作流"""
    print("=" * 80)
    print("演示 2: 审查循环工作流")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建审查循环 Agent
    creator = AssistantAgent(
        name="creator",
        model_client=model_client,
        description="你负责创建和生成内容。"
    )

    reviewer = AssistantAgent(
        name="reviewer",
        model_client=model_client,
        description="你负责审查内容并提供改进建议。"
    )

    finalizer = AssistantAgent(
        name="finalizer",
        model_client=model_client,
        description="你负责根据反馈完善最终版本。"
    )

    # 定义审查循环工作流程
    task = "创建一个产品发布会策划方案"
    
    print(f"💬 任务: {task}")
    print()

    # 步骤 1: 创建
    print("📍 步骤 1: 创建初始版本")
    create_result = await creator.run(
        task=f"为以下任务创建初步方案：{task}"
    )
    initial_version = create_result.messages[-1].content
    print(f"{creator.name}: {initial_version[:200]}...")
    print()

    # 步骤 2: 审查
    print("📍 步骤 2: 审查方案")
    review_result = await reviewer.run(
        task=f"审查以下方案并提供改进建议：\n{initial_version}"
    )
    feedback = review_result.messages[-1].content
    print(f"{reviewer.name}: {feedback[:200]}...")
    print()

    # 步骤 3: 完善
    print("📍 步骤 3: 根据反馈完善")
    finalize_result = await finalizer.run(
        task=f"根据以下反馈完善方案：\n反馈：{feedback}\n\n原方案：{initial_version}"
    )
    final_version = finalize_result.messages[-1].content
    print(f"{finalizer.name}: {final_version[:200]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_branching_workflow():
    """演示 3: 分支工作流"""
    print("=" * 80)
    print("演示 3: 分支工作流")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建决策和执行 Agent
    decider = AssistantAgent(
        name="decider",
        model_client=model_client,
        description="你负责分析任务并决定执行路径。"
    )

    technical_agent = AssistantAgent(
        name="technical_agent",
        model_client=model_client,
        description="你是技术专家，处理技术相关的问题。"
    )

    business_agent = AssistantAgent(
        name="business_agent",
        model_client=model_client,
        description="你是商业专家，处理商业相关的问题。"
    )

    integrator = AssistantAgent(
        name="integrator",
        model_client=model_client,
        description="你负责整合不同路径的结果。"
    )

    # 任务和分支决策
    task = "开发一个新功能的实施方案"
    
    print(f"💬 任务: {task}")
    print()

    # 步骤 1: 决策
    print("📍 步骤 1: 分析任务类型")
    decide_result = await decider.run(
        task=f"分析以下任务，判断是更偏向技术问题还是商业问题：{task}\n只回答'技术'或'商业'"
    )
    decision = decide_result.messages[-1].content.strip()
    print(f"{decider.name}: 决策路径 = {decision}")
    print()

    # 步骤 2: 根据决策分支
    print(f"📍 步骤 2: 执行{decision}路径")
    if "技术" in decision:
        execute_result = await technical_agent.run(task=task)
        branch_result = execute_result.messages[-1].content
        print(f"{technical_agent.name}: {branch_result[:200]}...")
    else:
        execute_result = await business_agent.run(task=task)
        branch_result = execute_result.messages[-1].content
        print(f"{business_agent.name}: {branch_result[:200]}...")
    print()

    # 步骤 3: 整合
    print("📍 步骤 3: 整合结果")
    integrate_result = await integrator.run(
        task=f"整合以下执行结果，提供完整的实施方案：\n{branch_result}"
    )
    final_result = integrate_result.messages[-1].content
    print(f"{integrator.name}: {final_result[:200]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_approval_workflow():
    """演示 4: 审批工作流"""
    print("=" * 80)
    print("演示 4: 审批工作流")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建审批流程 Agent
    requester = AssistantAgent(
        name="requester",
        model_client=model_client,
        description="你负责提交请求和提案。"
    )

    validator = AssistantAgent(
        name="validator",
        model_client=model_client,
        description="你负责验证请求的合理性和完整性。"
    )

    approver = AssistantAgent(
        name="approver",
        model_client=model_client,
        description="你负责批准或拒绝请求，并说明理由。"
    )

    # 审批流程
    request = "申请增加项目预算 50,000 元用于购买新设备"
    
    print(f"💬 请求: {request}")
    print()

    # 步骤 1: 提交请求
    print("📍 步骤 1: 提交请求")
    request_result = await requester.run(
        task=f"详细说明以下请求的理由和预期收益：{request}"
    )
    request_detail = request_result.messages[-1].content
    print(f"{requester.name}: {request_detail[:200]}...")
    print()

    # 步骤 2: 验证
    print("📍 步骤 2: 验证请求")
    validate_result = await validator.run(
        task=f"验证以下请求是否合理和完整：\n{request_detail}\n给出验证结论（通过/不通过）和理由"
    )
    validation = validate_result.messages[-1].content
    print(f"{validator.name}: {validation[:200]}...")
    print()

    # 步骤 3: 审批
    print("📍 步骤 3: 审批决策")
    approve_result = await approver.run(
        task=f"基于验证结果，决定是否批准请求：\n验证：{validation}\n原请求：{request_detail}\n请给出批准/拒绝的决策和详细理由"
    )
    approval = approve_result.messages[-1].content
    print(f"{approver.name}: {approval[:200]}...")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_iterative_workflow():
    """演示 5: 迭代改进工作流"""
    print("=" * 80)
    print("演示 5: 迭代改进工作流")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建迭代改进 Agent
    planner = AssistantAgent(
        name="planner",
        model_client=model_client,
        description="你负责制定计划。"
    )

    evaluator = AssistantAgent(
        name="evaluator",
        model_client=model_client,
        description="你负责评估计划的优缺点。"
    )

    improver = AssistantAgent(
        name="improver",
        model_client=model_client,
        description="你负责根据评估改进计划。"
    )

    # 迭代改进流程
    task = "制定一个团队培训计划"
    max_iterations = 2
    current_plan = ""
    
    print(f"💬 任务: {task}")
    print(f"   最大迭代次数: {max_iterations}")
    print()

    for iteration in range(1, max_iterations + 1):
        print(f"\n{'─' * 60}")
        print(f"🔄 迭代 {iteration}")
        print(f"{'─' * 60}")
        
        if iteration == 1:
            # 第一次迭代：制定计划
            print("\n📍 制定初始计划")
            plan_result = await planner.run(task=task)
            current_plan = plan_result.messages[-1].content
            print(f"{planner.name}: {current_plan[:200]}...")
        else:
            # 后续迭代：改进计划
            print("\n📍 改进计划")
            improve_result = await improver.run(
                task=f"根据评估结果改进计划：\n评估：{evaluation}\n\n当前计划：{current_plan}"
            )
            current_plan = improve_result.messages[-1].content
            print(f"{improver.name}: {current_plan[:200]}...")
        
        # 评估计划
        print("\n📍 评估计划")
        eval_result = await evaluator.run(
            task=f"评估以下计划的优缺点：\n{current_plan}"
        )
        evaluation = eval_result.messages[-1].content
        print(f"{evaluator.name}: {evaluation[:200]}...")

    print(f"\n{'─' * 60}")
    print("✅ 迭代完成")
    print("最终计划:")
    print(current_plan[:300] + "..." if len(current_plan) > 300 else current_plan)
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
║          AutoGen 0.4+ - 自定义团队演示              ║
║           Custom Team Workflows                          ║
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

        # 演示 1: 流水线工作流
        await demo_pipeline_workflow()

        # 演示 2: 审查循环工作流
        await demo_review_loop_workflow()

        # 演示 3: 分支工作流
        await demo_branching_workflow()

        # 演示 4: 审批工作流
        await demo_approval_workflow()

        # 演示 5: 迭代改进工作流
        await demo_iterative_workflow()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 自定义团队可以实现任何业务工作流程")
        print("  ✓ 可以灵活控制 Agent 的交互顺序")
        print("  ✓ 支持复杂的逻辑和条件分支")
        print("  ✓ 可以集成特定的业务规则和审批流程")
        print("  ✓ 适合企业级应用和特定场景")
        print()
        print("下一步:")
        print("  1. 查看 tools/ 目录学习工具使用")
        print("  2. 查看 advanced/ 目录学习高级特性")
        print("  3. 查看 03-extensions/ 学习扩展功能")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
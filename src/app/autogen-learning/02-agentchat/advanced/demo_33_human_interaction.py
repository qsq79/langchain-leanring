"""
Demo 33: 人工交互 - 人在循环中的作用

本演示展示如何:
1. 实现人工确认机制
2. 人工干预和修正
3. 人类专家知识集成
4. 人工反馈收集
5. 逐步人工控制

运行方式:
    python demo_33_human_interaction.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解记忆管理基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-loop.html
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
from typing import Dict, List, Any, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 人工交互类 =====
class HumanInLoopManager:
    """人工交互管理器"""
    

    def __init__(self):
        self.pending_approvals: List[Dict[str, Any]] = []
        self.human_feedback: List[Dict[str, Any]] = []
        self.intervention_log: List[Dict[str, Any]] = []
    
    def request_approval(self, action: str, details: Dict[str, Any]) -> bool:
        """请求人工批准"""
        approval_request = {
            "action": action,
            "details": details,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.pending_approvals.append(approval_request)
        
        print(f"\n📋 请求批准:")
        print(f"   操作: {action}")
        print(f"   详情: {details}")
        print(f"   模拟批准: 是")
        
        # 模拟人工批准
        return True
    
    def record_human_feedback(self, context: str, feedback: str) -> None:
        """记录人工反馈"""
        feedback_record = {
            "context": context,
            "feedback": feedback,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.human_feedback.append(feedback_record)
        
        print(f"\n💬 人工反馈记录:")
        print(f"   上下文: {context}")
        print(f"   反馈: {feedback}")
    
    def trigger_intervention(self, situation: str, action: str) -> None:
        """触发人工干预"""
        intervention = {
            "situation": situation,
            "action": action,
            "timestamp": asyncio.get_event_loop().time()
        }
        self.intervention_log.append(intervention)
        
        print(f"\n⚠️  人工干预:")
        print(f"   情况: {situation}")
        print(f"   采取行动: {action}")


# ===== 演示函数 =====
async def demo_approval_workflow():
    """演示 1: 批准工作流"""
    print("=" * 80)
    print("演示 1: 人工批准工作流")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    human_manager = HumanInLoopManager()

    # 创建需要人工批准的 Agent
    approval_agent = AssistantAgent(
        name="approval_agent",
        model_client=model_client,
        description="""你是一个需要人工批准的助手。对于重要操作，你会：
1. 明确说明需要批准的操作
2. 详细说明操作的影响和风险
3. 等待批准（在演示中，我们假设获得批准）
4. 只在获得批准后执行"""
    )

    print("💬 批准测试")
    print()

    # 测试需要批准的操作
    approval_tests = [
        ("发送重要邮件", {
            "recipient": "重要客户",
            "subject": "合同更新",
            "importance": "high"
        }),
        ("修改数据库", {
            "database": "production",
            "operation": "delete",
            "table": "users",
            "risk": "critical"
        }),
        ("发布新版本", {
            "version": "2.0.0",
            "changes": ["breaking changes"],
            "impact": "all users"
        })
    ]

    for i, (action, details) in enumerate(approval_tests, 1):
        print(f"\n{'─' * 40}")
        print(f"测试 {i}: {action}")
        print(f"{'─' * 40}\n")

        task = f"""请求执行以下操作：{action}
详情：
{details}

请：
1. 说明操作的重要性
2. 分析潜在风险
3. 提供执行建议
4. 明确表示需要批准（在演示中假设已批准）"""

        result = await approval_agent.run(task=task)

        print(f"🤖 Agent 响应:")
        for message in result.messages:
            print(f"{message.content[:200]}...")

        # 模拟人工批准
        human_manager.request_approval(action, details)

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_intervention_scenario():
    """演示 2: 人工干预场景"""
    print("=" * 80)
    print("演示 2: 人工干预场景")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    human_manager = HumanInLoopManager()

    # 创建 Agent
    intervention_agent = AssistantAgent(
        name="intervention_agent",
        model_client=model_client,
        description="""你是一个允许人工干预的助手。当遇到复杂或不确定的情况时：
1. 识别需要人工介入的时刻
2. 清晰描述问题和挑战
3. 提供多个可能的解决方案
4. 等待人工指导（演示中假设收到）"""
    )

    print("💬 干预测试")
    print()

    # 测试需要人工干预的场景
    intervention_scenarios = [
        "处理涉及大额交易的客户请求，不确定是否批准",
        "检测到可疑的登录活动，需要安全专家判断",
        "客户报告严重 bug，需要紧急技术支持",
        "收到复杂的法律合规问题咨询"
    ]

    for i, scenario in enumerate(intervention_scenarios, 1):
        print(f"\n{'─' * 40}")
        print(f"场景 {i}: {scenario}")
        print(f"{'─' * 40}\n")

        task = f"""处理以下情况：{scenario}

请：
1. 评估情况的严重性
2. 识别需要的专业知识
3. 建议可能的解决方案
4. 明确指出何时需要人工干预"""

        result = await intervention_agent.run(task=task)

        print(f"🤖 Agent 响应:")
        for message in result.messages:
            print(f"{message.content[:200]}...")

        # 模拟人工干预
        human_manager.trigger_intervention(scenario, "人工已介入处理")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_collaborative_problem_solving():
    """演示 3: 协作问题解决"""
    print("=" * 80)
    print("演示 3: AI 与人工协作解决问题")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    human_manager = HumanInLoopManager()

    # 创建协作 Agent
    collab_agent = AssistantAgent(
        name="collab_agent",
        model_client=model_client,
        description="""你是一个与人工协作的 AI 助手。你的角色是：
1. 提供初步分析和建议
2. 向人类专家学习
3. 根据人工反馈改进方案
4. 总结共同协作的成果"""
    )

    print("💬 协作问题解决")
    print()

    # 复杂问题场景
    problem_solving = [
        {
            "problem": "系统性能突然下降，需要诊断原因",
            "human_expertise": "系统架构和性能调优经验"
        },
        {
            "problem": "客户报告数据不一致问题，需要根源分析",
            "human_expertise": "数据完整性和审计流程知识"
        },
        {
            "problem": "新产品功能收到负面反馈，需要改进方案",
            "human_expertise": "用户体验和产品管理经验"
        }
    ]

    for i, problem_data in enumerate(problem_solving, 1):
        print(f"\n{'─' * 40}")
        print(f"问题 {i}: {problem_data['problem']}")
        print(f"{'─' * 40}\n")

        task = f"""解决以下问题：{problem_data['problem']}

你是 AI 助手，需要与人类专家协作。人类专家在以下领域有经验：{problem_data['human_expertise']}

请：
1. 提供你的初步分析
2. 识别需要人工专业知识的地方
3. 提出综合解决方案
4. 请求人工专家的反馈（演示中假设已收到）"""

        result = await collab_agent.run(task=task)

        print(f"🤖 Agent 响应:")
        for message in result.messages:
            print(f"{message.content[:200]}...")

        # 模拟人工反馈
        human_manager.record_human_feedback(
            context=problem_data['problem'],
            feedback=f"人类专家：分析合理，建议可行。{i}"
        )

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_feedback_loop():
    """演示 4: 反馈循环"""
    print("=" * 80)
    print("演示 4: 反馈循环改进")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    human_manager = HumanInLoopManager()

    # 创建反馈 Agent
    feedback_agent = AssistantAgent(
        name="feedback_agent",
        model_client=model_client,
        description="""你是一个根据人工反馈持续改进的助手。你会：
1. 接受初始任务
2. 提供初步解决方案
3. 等待人工反馈
4. 根据反馈改进方案
5. 循环直到满意"""
    )

    print("💬 反馈循环测试")
    print()

    # 需要迭代改进的任务
    iterative_tasks = [
        {
            "task": "设计一个用户注册流程",
            "feedbacks": [
                "太复杂了，简化步骤",
                "密码要求不明确",
                "缺少邮箱验证说明"
            ]
        },
        {
            "task": "创建 API 文档",
            "feedbacks": [
                "示例代码需要更多注释",
                "错误处理部分不够详细",
                "缺少使用示例"
            ]
        }
    ]

    for task_data in iterative_tasks:
        print(f"\n{'─' * 40}")
        print(f"任务: {task_data['task']}")
        print(f"{'─' * 40}\n")

        current_solution = ""
        
        for iteration, feedback in enumerate(task_data['feedbacks'], 1):
            print(f"\n📝 迭代 {iteration}")
            print(f"反馈: {feedback}")
            print()

            task_with_context = f"""任务：{task_data['task']}
当前方案：
{current_solution if current_solution else "（这是第一次尝试）"}

收到人工反馈：{feedback}

请根据反馈改进方案，提供新的版本。"""

            result = await feedback_agent.run(task=task_with_context)
            
            last_message = result.messages[-1]
            current_solution = last_message.content
            print(f"🤖 新方案:")
            print(f"{current_solution[:150]}...")
            
            # 记录反馈
            human_manager.record_human_feedback(
                context=f"迭代 {iteration}",
                feedback=feedback
            )

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_gradual_handover():
    """演示 5: 逐步人工交接"""
    print("=" * 80)
    print("演示 5: 逐步人工交接")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    human_manager = HumanInLoopManager()

    # 创建交接 Agent
    handover_agent = AssistantAgent(
        name="handover_agent",
        model_client=model_client,
        description="""你是一个支持逐步人工交接的助手。当需要人工介入时：
1. 识别交接的时机
2. 准备完整的上下文信息
3. 创建交接文档
4. 逐步将责任转移给人工
5. 提供后续支持指导"""
    )

    print("💬 逐步交接测试")
    print()

    # 交接场景
    handover_scenarios = [
        "处理高价值客户的退款请求，需要人工审核",
        "客户报告账户安全问题，需要人工验证身份",
        "收到复杂的商业咨询，需要人工专家判断",
        "检测到可能的欺诈行为，需要人工调查"
    ]

    for i, scenario in enumerate(handover_scenarios, 1):
        print(f"\n{'─' * 40}")
        print(f"场景 {i}: {scenario}")
        print(f"{'─' * 40}\n")

        task = f"""处理以下情况，并在必要时进行人工交接：{scenario}

请：
1. 评估是否真的需要人工介入
2. 如果需要，准备完整的上下文
3. 创建清晰的交接文档
4. 列出人工需要注意的关键点
5. 提供交接后的支持建议"""

        result = await handover_agent.run(task=task)

        print(f"🤖 Agent 响应:")
        for message in result.messages:
            content = message.content[:300] + "..." if len(message.content) > 300 else message.content
            print(f"{content}")

        # 记录交接
        human_manager.trigger_intervention(
            situation=scenario,
            action=f"场景 {i} 已交接给人工专家"
        )

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - 人工交互演示             ║
║           Human-in-the-Loop Interaction              ║
║                                                                ║
╚════════════════════════════════════════════════════════════╝
    """)
    print("=" * 80 + "\n")

    try:
        # 检查 API Key
        settings = get_settings()
        if not settings.openai_api_key:
            print("❌ 错误: 未配置 OPENAI_API_KEY")
            print("   请在 .env 文件中设置 OPENAI_API_KEY")
            return

        # 演示 1: 批准工作流
        await demo_approval_workflow()

        # 演示 2: 人工干预
        await demo_intervention_scenario()

        # 演示 3: 协作问题解决
        await demo_collaborative_problem_solving()

        # 演示 4: 反馈循环
        await demo_feedback_loop()

        # 演示 5: 逐步交接
        await demo_gradual_handover()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 人工批准机制确保关键操作的安全性")
        print("  ✓ 人工干预可以处理复杂和不确定的情况")
        print("  ✓ AI 和人工协作可以发挥各自优势")
        print("  ✓ 反馈循环持续改进方案质量")
        print("  ✓ 逐步交接保证责任的平稳转移")
        print()
        print("下一步:")
        print("  1. 查看 demo_34_image_messages.py 学习多模态")
        print("  2. 查看 03-extensions/ 学习扩展功能")
        print("  3. 查看 04-integration/ 学习集成案例")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
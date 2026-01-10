"""
Demo 25: 对话终止 - 控制对话的结束

本演示展示如何:
1. 设置最大轮次限制
2. 基于条件的终止
3. 目标达成检测
4. 手动终止控制
5. 异常处理和超时

运行方式:
    python demo_25_conversation_termination.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解序列对话基础

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
async def demo_max_turns_termination():
    """演示 1: 最大轮次终止"""
    print("=" * 80)
    print("演示 1: 最大轮次终止")

    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建两个对话 Agent
    agent_a = AssistantAgent(
        name="agent_a",
        model_client=model_client,
        description="你负责开始话题并引导对话。"
    )

    agent_b = AssistantAgent(
        name="agent_b",
        model_client=model_client,
        description="你负责回应并深入讨论话题。"
    )

    print("💬 场景: 最大 3 轮对话")
    print()

    topic = "讨论人工智能的未来发展趋势"
    max_turns = 3

    conversation_history = []

    for turn in range(1, max_turns + 1):
        print(f"\n─ 轮次 {turn} ─")
        print()

        # Agent A 发言
        if turn == 1:
            task = topic
        else:
            task = f"继续对话，针对{agent_b.name}的观点进行深入讨论"
        
        result_a = await agent_a.run(
            task=task,
            conversation_history=conversation_history
        )
        message_a = result_a.messages[-1].content
        print(f"{agent_a.name}: {message_a[:150]}...")
        conversation_history.append({"role": "assistant", "content": message_a})

        # Agent B 回应
        if turn < max_turns:
            result_b = await agent_b.run(
                task="回应上述观点并提出你的看法",
                conversation_history=conversation_history
            )
            message_b = result_b.messages[-1].content
            print(f"{agent_b.name}: {message_b[:150]}...")
            conversation_history.append({"role": "assistant", "content": message_b})

    print(f"\n✅ 对话在第 {max_turns} 轮后终止")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_condition_based_termination():
    """演示 2: 基于条件的终止"""
    print("=" * 80)
    print("演示 2: 基于条件的终止")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建对话 Agent
    solver = AssistantAgent(
        name="solver",
        model_client=model_client,
        description="你负责解决问题，当找到满意答案时明确说明'问题已解决'。"
    )

    print("💬 场景: 求解数学问题，直到找到答案")
    print()

    problem = "找出所有满足 x² - 5x + 6 = 0 的实数解"
    
    conversation_history = []
    max_attempts = 5
    solved = False
    attempt = 0

    while attempt < max_attempts and not solved:
        attempt += 1
        print(f"\n─ 尝试 {attempt} ─")
        print()

        # 求解器尝试求解
        result = await solver.run(
            task=f"请求解以下问题：{problem}\n如果你已经找到答案，请明确说明'问题已解决'。",
            conversation_history=conversation_history
        )
        
        answer = result.messages[-1].content
        print(f"Solver: {answer[:200]}...")
        conversation_history.append({"role": "assistant", "content": answer})

        # 检查是否解决
        if "问题已解决" in answer or "解答" in answer:
            solved = True
            print("\n✅ 检测到条件满足，对话终止")
            break

        if attempt >= max_attempts:
            print(f"\n⚠️  达到最大尝试次数 ({max_attempts})，对话终止")
            break

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_goal_achievement():
    """演示 3: 目标达成终止"""
    print("=" * 80)
    print("演示 3: 目标达成检测")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建协作 Agent
    planner = AssistantAgent(
        name="planner",
        model_client=model_client,
        description="你负责制定计划，当计划完整时说明'计划完成'。"
    )

    executor = AssistantAgent(
        name="executor",
        model_client=model_client,
        description="你负责执行计划，当所有任务完成时说明'任务完成'。"
    )

    print("💬 场景: 项目计划与执行")
    print()

    goal = "完成一个网站开发项目"
    conversation_history = []

    # 阶段 1: 制定计划
    print("\n阶段 1: 制定计划")
    print()

    plan_attempts = 0
    plan_complete = False

    while plan_attempts < 3 and not plan_complete:
        plan_attempts += 1
        print(f"计划制定尝试 {plan_attempts}...")

        plan_result = await planner.run(
            task=f"为'{goal}'制定详细的执行计划。如果计划完整，请说明'计划完成'。",
            conversation_history=conversation_history
        )
        
        plan = plan_result.messages[-1].content
        print(f"Planner: {plan[:150]}...")
        conversation_history.append({"role": "assistant", "content": plan})

        if "计划完成" in plan:
            plan_complete = True
            print("✅ 计划制定完成")
            break

    # 阶段 2: 执行计划
    if plan_complete:
        print("\n阶段 2: 执行计划")
        print()

        exec_attempts = 0
        task_complete = False

        while exec_attempts < 3 and not task_complete:
            exec_attempts += 1
            print(f"执行尝试 {exec_attempts}...")

            exec_result = await executor.run(
                task=f"根据以下计划执行任务：\n{plan}\n如果所有任务完成，请说明'任务完成'。",
                conversation_history=conversation_history
            )
            
            exec_report = exec_result.messages[-1].content
            print(f"Executor: {exec_report[:150]}...")
            conversation_history.append({"role": "assistant", "content": exec_report})

            if "任务完成" in exec_report:
                task_complete = True
                print("✅ 所有任务完成")
                break

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_manual_termination():
    """演示 4: 手动终止控制"""
    print("=" * 80)
    print("演示 4: 手动终止控制")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建对话 Agent
    interviewer = AssistantAgent(
        name="interviewer",
        model_client=model_client,
        description="你是一位面试官，负责提问。"
    )

    candidate = AssistantAgent(
        name="candidate",
        model_client=model_client,
        description="你是一位求职者，负责回答问题。"
    )

    print("💬 场景: 模拟面试，随时可以手动终止")
    print()

    conversation_history = []
    questions = [
        "请简单介绍一下你自己",
        "你有什么技术特长？",
        "你为什么想要这个职位？"
    ]

    print("提示: 在实际应用中，可以设置键盘中断或其他机制来手动终止对话")
    print()

    # 模拟手动控制
    continue_interview = True

    for i, question in enumerate(questions[:2], 1):  # 限制只问 2 个问题
        if not continue_interview:
            print("\n⚠️  面试被手动终止")
            break

        print(f"\n─ 面试问题 {i} ─")
        print()

        # 面试官提问
        result_q = await interviewer.run(
            task=f"向求职者提问：{question}",
            conversation_history=conversation_history
        )
        q_content = result_q.messages[-1].content
        print(f"Interviewer: {q_content}")
        conversation_history.append({"role": "assistant", "content": q_content})

        # 求职者回答
        result_a = await candidate.run(
            task="回答面试官的问题",
            conversation_history=conversation_history
        )
        a_content = result_a.messages[-1].content
        print(f"Candidate: {a_content[:150]}...")
        conversation_history.append({"role": "assistant", "content": a_content})

        # 模拟手动决策
        if i == 2:
            print("\n💡 模拟: 面试官决定终止面试")
            continue_interview = False

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_timeout_and_error_handling():
    """演示 5: 超时和错误处理"""
    print("=" * 80)
    print("演示 5: 超时和错误处理")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建带容错的 Agent
    robust_agent = AssistantAgent(
        name="robust_agent",
        model_client=model_client,
        description="你是一个健壮的 Agent，能够优雅地处理错误和超时。"
    )

    print("💬 场景: 带超时和错误处理的对话")
    print()

    # 模拟超时场景
    print("\n─ 模拟超时场景 ─")
    print()

    try:
        # 设置超时时间（5秒）
        print("设置 5 秒超时...")
        result = await asyncio.wait_for(
            robust_agent.run(task="快速回答: 1+1=?"),
            timeout=5.0
        )
        answer = result.messages[-1].content
        print(f"✅ 正常完成: {answer}")
    except asyncio.TimeoutError:
        print("⚠️  超时: 操作在指定时间内未完成")
    except Exception as e:
        print(f"❌ 错误: {e}")

    # 模拟错误处理
    print("\n─ 模拟错误处理 ─")
    print()

    try:
        error_task = "这是一个测试错误处理的请求，请优雅地处理并恢复"
        print(f"任务: {error_task}")
        
        result = await robust_agent.run(
            task=f"如果遇到错误，请说明错误原因并提供解决方案：{error_task}"
        )
        response = result.messages[-1].content
        print(f"响应: {response[:200]}...")
        
        if "错误" in response or "error" in response.lower():
            print("✅ Agent 成功处理了错误场景")
            
    except Exception as e:
        print(f"❌ 捕获异常: {e}")
        print("✅ 异常被成功捕获并处理")

    # 重试机制
    print("\n─ 模拟重试机制 ─")
    print()

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            print(f"尝试 {attempt}/{max_retries}...")
            
            result = await robust_agent.run(
                task=f"尝试回答这个问题：今天天气如何？（模拟第 {attempt} 次尝试）"
            )
            answer = result.messages[-1].content
            print(f"✅ 成功: {answer[:100]}...")
            break
            
        except Exception as e:
            print(f"⚠️  尝试 {attempt} 失败: {e}")
            if attempt == max_retries:
                print("❌ 达到最大重试次数，放弃")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - 对话终止演示                   ║
║           Conversation Termination Control                  ║
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

        # 演示 1: 最大轮次终止
        await demo_max_turns_termination()

        # 演示 2: 基于条件的终止
        await demo_condition_based_termination()

        # 演示 3: 目标达成检测
        await demo_goal_achievement()

        # 演示 4: 手动终止控制
        await demo_manual_termination()

        # 演示 5: 超时和错误处理
        await demo_timeout_and_error_handling()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 最大轮次限制可以防止无限循环")
        print("  ✓ 基于条件的终止可以实现智能控制")
        print("  ✓ 目标达成检测可以自动化判断完成")
        print("  ✓ 手动终止提供了灵活性")
        print("  ✓ 超时和错误处理确保系统的健壮性")
        print()
        print("下一步:")
        print("  1. 查看 teams/ 目录学习团队协作")
        print("  2. 查看 tools/ 目录学习工具使用")
        print("  3. 查看 advanced/ 目录学习高级特性")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
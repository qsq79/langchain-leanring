"""
Demo 22: UserProxyAgent - 用户代理 Agent

本演示展示如何:
1. 使用 UserProxyAgent 代表用户
2. 人类确认流程
3. 代码执行批准
4. 工具使用授权
5. 安全交互机制

运行方式:
    # 方式1: 从 autogen-learning 目录运行（推荐）
    cd /path/to/autogen-learning
    python -m 02-agentchat.basics.demo_22_user_proxy_agent

    # 方式2: 直接运行脚本文件
    python demo_22_user_proxy_agent.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 AssistantAgent 基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/user-proxy.html
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
async def demo_user_proxy_concept():
    """演示 1: UserProxyAgent 概念"""
    print("=" * 80)
    print("演示 1: UserProxyAgent 概念理解")
    print("=" * 80 + "\n")

    print("📚 UserProxyAgent 概念:")
    print()
    print("UserProxyAgent 是 AutoGen 中代表人类用户的 Agent，主要特点:")
    print()
    print("1. 人类确认机制:")
    print("   - 在执行重要操作前需要人类批准")
    print("   - 防止 AI 做出不可逆或有害的决策")
    print()
    print("2. 代码执行控制:")
    print("   - AI 生成的代码需要人类审查后才能执行")
    print("   - 确保代码安全性和正确性")
    print()
    print("3. 工具使用授权:")
    print("   - 控制对敏感工具的访问")
    print("   - 人类决定是否允许执行某些操作")
    print()
    print("4. 安全交互:")
    print("   - 在人机协作中保持人类控制权")
    print("   - 适合需要人类监督的场景")
    print()
    print("注意: AutoGen 0.4+ 中，UserProxyAgent 的功能通过以下方式实现:")
    print("   - 使用 AssistantAgent 配置为代理模式")
    print("   - 通过中间件或工具来实现确认流程")
    print("   - 自定义工作流控制来模拟人类确认")
    print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_assistant_with_approval():
    """演示 2: 需要批准的助手"""
    print("=" * 80)
    print("演示 2: 需要批准的决策助手")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建一个需要人类批准的助手
    approval_assistant = AssistantAgent(
        name="approval_assistant",
        model_client=model_client,
        description="""你是一个需要人类批准的决策助手。对于任何行动建议，你应该:
1. 明确说明建议的行动
2. 解释为什么采取这个行动
3. 列出潜在的风险
4. 等待人类批准（在演示中，我们假设批准）
5. 只在获得批准后执行

对于需要批准的操作，请在回复中明确标注 "需要批准:" """
    )

    print("💬 场景: 邮件发送决策")
    print()

    task = """我需要给客户发送一封重要的道歉邮件。请帮我:
1. 起草邮件内容
2. 说明发送建议
3. 列出发送的注意事项
4. 告诉我是否需要批准"""

    print(f"👤 用户: {task}")
    print()

    result = await approval_assistant.run(task=task)

    for message in result.messages:
        print(f"🤖 助手:\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_code_review_workflow():
    """演示 3: 代码审查工作流"""
    print("=" * 80)
    print("演示 3: 代码审查工作流")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建代码助手
    code_assistant = AssistantAgent(
        name="code_assistant",
        model_client=model_client,
        description="""你是一个代码助手，在工作流中模拟 UserProxy 的审查流程:
1. 首先生成代码
2. 提供代码审查检查点
3. 在检查点暂停并说明需要审查的内容
4. 列出审查要点
5. 在获得"批准"后继续（在演示中，我们模拟批准流程）"""
    )

    print("💬 代码生成与审查工作流")
    print()

    task = """请创建一个函数来验证电子邮件地址的有效性。

工作流程:
1. 先编写函数代码
2. 停下来说明代码的关键部分
3. 列出需要审查的安全考虑
4. 说明测试用例建议
5. 等待审查（在演示中，你假设审查通过并总结）"""

    print(f"👤 用户: {task}")
    print()

    result = await code_assistant.run(task=task)

    for message in result.messages:
        print(f"🤖 助手:\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_sensitive_operation_control():
    """演示 4: 敏感操作控制"""
    print("=" * 80)
    print("演示 4: 敏感操作控制")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建安全助手
    security_assistant = AssistantAgent(
        name="security_assistant",
        model_client=model_client,
        description="""你是一个注重安全的助手，对于敏感操作会要求确认:
1. 识别操作是否敏感
2. 如果是敏感操作，明确标注并解释原因
3. 提供操作的详细说明
4. 说明潜在影响
5. 请求人类确认
6. 只在确认后继续（演示中假设获得确认）"""
    )

    print("💬 敏感操作场景")
    print()

    sensitive_tasks = [
        "请删除所有临时文件",
        "请修改系统配置文件",
        "请发送批量邮件给所有用户"
    ]

    for task in sensitive_tasks:
        print(f"\n{'─' * 40}")
        print(f"👤 用户: {task}")
        print(f"{'─' * 40}\n")

        result = await security_assistant.run(task=task)

        for message in result.messages:
            # 限制输出长度
            content = message.content[:500] + "..." if len(message.content) > 500 else message.content
            print(f"🤖 助手:\n{content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_step_approval():
    """演示 5: 多步骤批准流程"""
    print("=" * 80)
    print("演示 5: 多步骤批准流程")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建工作流助手
    workflow_assistant = AssistantAgent(
        name="workflow_assistant",
        model_client=model_client,
        description="""你是一个工作流助手，处理需要多步批准的任务:
1. 将任务分解为多个步骤
2. 对每个步骤明确标注"需要批准"
3. 说明每一步的目的和风险
4. 等待批准（演示中假设批准）
5. 继续下一步
6. 最后总结整个流程"""
    )

    print("💬 多步骤工作流: 部署新功能")
    print()

    task = """我需要部署一个新的数据分析功能到生产环境。请规划一个完整的部署流程，
包括代码审查、测试、备份、部署和验证，每个步骤都需要我的批准。"""

    print(f"👤 用户: {task}")
    print()

    result = await workflow_assistant.run(task=task)

    for message in result.messages:
        print(f"🤖 助手:\n{message.content}")

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
║          AutoGen 0.4+ - UserProxyAgent 演示            ║
║           Human-in-the-Loop Patterns                       ║
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

        # 演示 1: UserProxyAgent 概念
        await demo_user_proxy_concept()

        # 演示 2: 需要批准的助手
        await demo_assistant_with_approval()

        # 演示 3: 代码审查工作流
        await demo_code_review_workflow()

        # 演示 4: 敏感操作控制
        await demo_sensitive_operation_control()

        # 演示 5: 多步骤批准流程
        await demo_multi_step_approval()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n重要提示:")
        print("  在实际应用中，UserProxyAgent 的功能通常通过以下方式实现:")
        print("  1. 使用中间件拦截和确认操作")
        print("  2. 通过工具授权机制控制执行")
        print("  3. 使用事件驱动的架构实现批准流程")
        print("  4. 在多 Agent 系统中配置审批 Agent")
        print()
        print("下一步:")
        print("  1. 查看 conversations/ 目录学习对话管理")
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
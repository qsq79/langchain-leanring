"""
Demo 27: Selector 团队 - 选择式协作

本演示展示如何:
1. 创建选择式团队
2. 根据任务智能选择 Agent
3. 基于描述匹配最合适的专家
4. 实现高效的任务分发
5. 整合专业领域的输出

运行方式:
    python demo_27_selector_team.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 RoundRobin 团队基础

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


class SelectorTeam:
    """模拟 Selector 团队类"""
    
    def __init__(self, name: str, agents: list, selector_agent: AssistantAgent):
        self.name = name

        self.agents = agents
        self.selector = selector_agent
    
    async def select_agent(self, task: str) -> AssistantAgent:
        """选择最合适的 Agent"""
        # 构建选择提示
        agent_descriptions = "\n".join([
            f"{i+1}. {agent.name}: {agent.description}"
            for i, agent in enumerate(self.agents)
        ])
        
        selection_prompt = f"""给定以下任务和可用的专家，请选择最合适的专家。

任务: {task}

可用专家:
{agent_descriptions}

请只回复被选中的专家名称（数字或名称），不要添加其他内容。"""
        
        result = await self.selector.run(task=selection_prompt)
        selected = result.messages[-1].content.strip()
        
        # 尝试按名称或索引匹配
        for agent in self.agents:
            if agent.name.lower() in selected.lower() or str(self.agents.index(agent) + 1) in selected:
                return agent
        
        # 默认返回第一个
        return self.agents[0]
    
    async def execute(self, task: str):
        """执行任务"""
        print(f"\n{'=' * 60}")
        print(f"📋 团队执行: {self.name}")
        print(f"   任务: {task}")
        print('=' * 60 + "\n")
        
        # 选择最合适的 Agent
        print("🔍 正在选择最合适的专家...")
        selected_agent = await self.select_agent(task)
        print(f"✅ 选中专家: {selected_agent.name}")
        print()
        
        # 执行任务
        print(f"{selected_agent.name} 处理中...")
        result = await selected_agent.run(task=task)
        output = result.messages[-1].content
        
        print(f"\n结果:")
        print(output)
        
        return output


# ===== 演示函数 =====
async def demo_basic_selector():
    """演示 1: 基本选择团队"""
    print("=" * 80)
    print("演示 1: 基本选择团队")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同领域的专家
    code_expert = AssistantAgent(
        name="code_expert",
        model_client=model_client,
        description="你是一位编程专家，擅长处理代码相关的问题、调试和算法实现。"
    )

    design_expert = AssistantAgent(
        name="design_expert",
        model_client=model_client,
        description="你是一位设计专家，擅长UI/UX设计、视觉设计和用户体验优化。"
    )

    business_expert = AssistantAgent(
        name="business_expert",
        model_client=model_client,
        description="你是一位商业专家，擅长市场分析、商业策略和商业模式设计。"
    )

    # 创建选择器
    selector = AssistantAgent(
        name="selector",
        model_client=model_client,
        description="你是一个任务选择器，负责根据任务内容选择最合适的专家。"
    )

    # 创建 Selector 团队
    team = SelectorTeam(
        name="专业服务团队",
        agents=[code_expert, design_expert, business_expert],
        selector_agent=selector
    )

    # 测试不同类型的任务
    tasks = [
        "帮我写一个 Python 函数来排序数组",
        "设计一个电商网站的主页布局",
        "分析一个新产品的市场机会"
    ]

    for task in tasks:
        await team.execute(task)
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_support_system():
    """演示 2: 客户支持系统"""
    print("=" * 80)
    print("演示 2: 客户支持系统")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同类型支持专家
    technical_support = AssistantAgent(
        name="technical_support",
        model_client=model_client,
        description="你是技术支持专家，处理技术问题、故障排除和系统问题。"
    )

    billing_support = AssistantAgent(
        name="billing_support",
        model_client=model_client,
        description="你是账单支持专家，处理计费、退款和账户问题。"
    )

    general_support = AssistantAgent(
        name="general_support",
        model_client=model_client,
        description="你是通用支持专家，处理一般咨询、产品信息和建议。"
    )

    # 创建选择器
    selector = AssistantAgent(
        name="support_router",
        model_client=model_client,
        description="你是客户支持路由器，根据客户问题类型分配给合适的支持专家。"
    )

    # 创建支持团队
    support_team = SelectorTeam(
        name="客户支持中心",
        agents=[technical_support, billing_support, general_support],
        selector_agent=selector
    )

    # 模拟客户查询
    customer_queries = [
        "我无法登录我的账户",
        "这个月的服务费为什么这么高？",
        "你们的软件有哪些功能？"
    ]

    for query in customer_queries:
        await support_team.execute(query)
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_content_creation():
    """演示 3: 内容创作系统"""
    print("=" * 80)
    print("演示 3: 内容创作系统")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同类型的内容创作者
    technical_writer = AssistantAgent(
        name="technical_writer",
        model_client=model_client,
        description="你是技术文档作者，擅长撰写技术文档、API 说明和教程。"
    )

    marketing_copy = AssistantAgent(
        name="marketing_copy",
        model_client=model_client,
        description="你是营销文案作者，擅长撰写广告文案、宣传语和营销材料。"
    )

    blog_writer = AssistantAgent(
        name="blog_writer",
        model_client=model_client,
        description="你是博客作者，擅长撰写博客文章、观点文章和评论。"
    )

    # 创建选择器
    selector = AssistantAgent(
        name="content_router",
        model_client=model_client,
        description="你是内容路由器，根据内容需求选择合适的内容创作者。"
    )

    # 创建内容团队
    content_team = SelectorTeam(
        name="内容创作中心",
        agents=[technical_writer, marketing_copy, blog_writer],
        selector_agent=selector
    )

    # 内容创作请求
    content_requests = [
        "写一篇 RESTful API 的使用指南",
        "为我们的新产品写一段吸引人的宣传语",
        "写一篇关于远程工作效率的博客文章"
    ]

    for request in content_requests:
        await content_team.execute(request)
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_domain_consultation():
    """演示 4: 多领域咨询系统"""
    print("=" * 80)
    print("演示 4: 多领域咨询系统")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同领域顾问
    legal_consultant = AssistantAgent(
        name="legal_consultant",
        model_client=model_client,
        description="你是法律顾问，提供法律咨询、合同审查和合规建议。"
    )

    financial_advisor = AssistantAgent(
        name="financial_advisor",
        model_client=model_client,
        description="你是财务顾问，提供财务规划、投资建议和税务咨询。"
    )

    hr_consultant = AssistantAgent(
        name="hr_consultant",
        model_client=model_client,
        description="你是人力资源顾问，提供招聘、员工关系和组织发展建议。"
    )

    # 创建选择器
    selector = AssistantAgent(
        name="consultation_router",
        model_client=model_client,
        description="你是咨询路由器，根据咨询问题类型分配给合适的顾问。"
    )

    # 创建咨询团队
    consultation_team = SelectorTeam(
        name="专业咨询中心",
        agents=[legal_consultant, financial_advisor, hr_consultant],
        selector_agent=selector
    )

    # 咨询请求
    consultation_questions = [
        "如何合法地保护我的知识产权？",
        "如何为公司制定财务预算？",
        "如何提高员工满意度和保留率？"
    ]

    for question in consultation_questions:
        await consultation_team.execute(question)
        print()

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_specialized_tasks():
    """演示 5: 专业化任务处理"""
    print("=" * 80)
    print("演示 5: 专业化任务处理")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建专业化处理 Agent
    data_analyst = AssistantAgent(
        name="data_analyst",
        model_client=model_client,
        description="你是数据分析师，擅长数据分析、统计和数据可视化。"
    )

    research_scientist = AssistantAgent(
        name="research_scientist",
        model_client=model_client,
        description="你是研究科学家，擅长科学研究、实验设计和学术写作。"
    )

    project_manager = AssistantAgent(
        name="project_manager",
        model_client=model_client,
        description="你是项目经理，擅长项目管理、资源规划和进度跟踪。"
    )

    # 创建选择器
    selector = AssistantAgent(
        name="task_router",
        model_client=model_client,
        description="你是任务路由器，根据任务类型分配给最合适的专家。"
    )

    # 创建专业团队
    professional_team = SelectorTeam(
        name="专业服务中心",
        agents=[data_analyst, research_scientist, project_manager],
        selector_agent=selector
    )

    # 专业化任务
    specialized_tasks = [
        "分析这组销售数据的趋势",
        "设计一个科学实验来验证假设",
        "制定一个软件开发项目的里程碑计划"
    ]

    for task in specialized_tasks:
        await professional_team.execute(task)
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
║          AutoGen 0.4+ - Selector 团队演示                ║
║           Selector Team Collaboration                     ║
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

        # 演示 1: 基本选择团队
        await demo_basic_selector()

        # 演示 2: 客户支持系统
        await demo_support_system()

        # 演示 3: 内容创作系统
        await demo_content_creation()

        # 演示 4: 多领域咨询系统
        await demo_multi_domain_consultation()

        # 演示 5: 专业化任务处理
        await demo_specialized_tasks()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ Selector 模式根据任务智能选择最合适的 Agent")
        print("  ✓ 基于描述匹配可以实现精准的任务分发")
        print("  ✓ 提高了效率和响应质量")
        print("  ✓ 适合专业分工和专家咨询场景")
        print("  ✓ 可以跳过不相关的 Agent，节省资源")
        print()
        print("下一步:")
        print("  1. 查看 demo_28_custom_team.py 学习自定义团队")
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
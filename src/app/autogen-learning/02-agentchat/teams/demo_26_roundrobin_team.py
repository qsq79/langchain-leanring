"""
Demo 26: RoundRobin 团队 - 轮询式协作

本演示展示如何:
1. 创建轮询式团队
2. 管理 Agent 的顺序发言
3. 实现公平的讨论机制
4. 收集多角度的意见
5. 整合团队输出

运行方式:
    python demo_26_roundrobin_team.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解基础对话和序列对话

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


class RoundRobinTeam:
    """模拟 RoundRobin 团队类"""
    
    def __init__(self, name: str, agents: list):
        self.name = name

        self.agents = agents
        self.current_index = 0
    
    def next_agent(self):
        """获取下一个发言的 Agent"""
        agent = self.agents[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.agents)
        return agent
    
    async def discuss(self, topic: str, max_rounds: int = 2):
        """进行团队讨论"""
        print(f"\n{'=' * 60}")
        print(f"📋 团队讨论: {self.name}")
        print(f"   主题: {topic}")
        print(f"   参与者: {[agent.name for agent in self.agents]}")
        print(f"   最大轮次: {max_rounds}")
        print('=' * 60 + "\n")
        
        conversation_history = []
        
        for round_num in range(1, max_rounds + 1):
            print(f"\n── 第 {round_num} 轮 ──")
            
            for i, agent in enumerate(self.agents):
                print(f"\n{agent.name} 发言:")
                
                # 根据轮次和角色调整任务
                if round_num == 1:
                    task = f"对于'{topic}'，请从你的专业角度提出观点。"
                else:
                    task = f"基于前面的讨论，继续深入关于'{topic}'的讨论，提出补充观点或建议。"
                
                result = await agent.run(
                    task=task,
                    conversation_history=conversation_history
                )
                
                message = result.messages[-1].content
                print(f"{message[:200]}...")
                
                conversation_history.append({"role": "assistant", "content": message})
        
        return conversation_history


# ===== 演示函数 =====
async def demo_basic_roundrobin():
    """演示 1: 基本轮询团队"""
    print("=" * 80)
    print("演示 1: 基本轮询团队")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同角度的 Agent
    optimist = AssistantAgent(
        name="optimist",
        model_client=model_client,
        description="你是一个乐观主义者，总是看到事物积极的一面和机会。"
    )

    realist = AssistantAgent(
        name="realist",
        model_client=model_client,
        description="你是一个现实主义者，客观分析事物的优点和缺点。"
    )

    critic = AssistantAgent(
        name="critic",
        model_client=model_client,
        description="你是一个批评者，关注潜在的问题和风险。"
    )

    # 创建 RoundRobin 团队
    team = RoundRobinTeam(
        name="讨论小组",
        agents=[optimist, realist, critic]
    )

    # 进行讨论
    topic = "人工智能在教育中的应用"
    discussion = await team.discuss(topic=topic, max_rounds=2)

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_expert_panel():
    """演示 2: 专家小组讨论"""
    print("=" * 80)
    print("演示 2: 专家小组讨论")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同领域的专家
    tech_expert = AssistantAgent(
        name="tech_expert",
        model_client=model_client,
        description="你是一位技术专家，从技术和工程角度分析问题。"
    )

    business_expert = AssistantAgent(
        name="business_expert",
        model_client=model_client,
        description="你是一位商业专家，从市场和商业价值角度分析问题。"
    )

    design_expert = AssistantAgent(
        name="design_expert",
        model_client=model_client,
        description="你是一位设计专家，从用户体验和美学角度分析问题。"
    )

    # 创建专家团队
    expert_panel = RoundRobinTeam(
        name="专家评审团",
        agents=[tech_expert, business_expert, design_expert]
    )

    # 专家讨论
    topic = "开发一个智能家居移动应用"
    await expert_panel.discuss(topic=topic, max_rounds=2)

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_stakeholder_meeting():
    """演示 3: 利益相关者会议"""
    print("=" * 80)
    print("演示 3: 利益相关者会议")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同的利益相关者
    product_manager = AssistantAgent(
        name="product_manager",
        model_client=model_client,
        description="你是产品经理，关注产品功能和用户需求。"
    )

    developer = AssistantAgent(
        name="developer",
        model_client=model_client,
        description="你是开发者，关注技术实现和开发效率。"
    )

    customer_support = AssistantAgent(
        name="customer_support",
        model_client=model_client,
        description="你是客服代表，关注用户体验和客户反馈。"
    )

    # 创建会议团队
    meeting = RoundRobinTeam(
        name="项目会议",
        agents=[product_manager, developer, customer_support]
    )

    # 会议讨论
    topic = "改进用户反馈机制"
    await meeting.discuss(topic=topic, max_rounds=2)

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_brainstorming_session():
    """演示 4: 头脑风暴会议"""
    print("=" * 80)
    print("演示 4: 头脑风暴会议")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同思维模式的 Agent
    creative_thinker = AssistantAgent(
        name="creative_thinker",
        model_client=model_client,
        description="你是创意思考者，喜欢提出创新和大胆的想法。"
    )

    practical_thinker = AssistantAgent(
        name="practical_thinker",
        model_client=model_client,
        description="你是实用思考者，关注可行性和实施难度。"
    )

    analyst = AssistantAgent(
        name="analyst",
        model_client=model_client,
        description="你是分析师，喜欢分析数据、成本和收益。"
    )

    # 创建头脑风暴团队
    brainstorm_team = RoundRobinTeam(
        name="创意风暴",
        agents=[creative_thinker, practical_thinker, analyst]
    )

    # 头脑风暴
    topic = "提高员工工作效率的新方法"
    await brainstorm_team.discuss(topic=topic, max_rounds=2)

    print("=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_decision_making():
    """演示 5: 团队决策"""
    print("=" * 80)
    print("演示 5: 团队决策讨论")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建不同视角的决策者
    strategic_advisor = AssistantAgent(
        name="strategic_advisor",
        model_client=model_client,
        description="你是战略顾问，关注长期影响和战略一致性。"
    )

    financial_advisor = AssistantAgent(
        name="financial_advisor",
        model_client=model_client,
        description="你是财务顾问，关注成本、预算和投资回报。"
    )

    risk_manager = AssistantAgent(
        name="risk_manager",
        model_client=model_client,
        description="你是风险经理，关注潜在风险和缓解措施。"
    )

    # 创建决策团队
    decision_team = RoundRobinTeam(
        name="决策委员会",
        agents=[strategic_advisor, financial_advisor, risk_manager]
    )

    # 决策讨论
    topic = "是否应该将业务扩展到新市场"
    await decision_team.discuss(topic=topic, max_rounds=2)

    print("\n" + "=" * 80)
    print("💡 决策建议:")
    print("   基于以上讨论，可以总结各方观点:")
    print("   1. 战略角度的考虑")
    print("   2. 财务角度的评估")
    print("   3. 风险角度的分析")
    print("   4. 综合建议")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - RoundRobin 团队演示              ║
║           Round Robin Team Collaboration                    ║
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

        # 演示 1: 基本轮询团队
        await demo_basic_roundrobin()

        # 演示 2: 专家小组
        await demo_expert_panel()

        # 演示 3: 利益相关者会议
        await demo_stakeholder_meeting()

        # 演示 4: 头脑风暴
        await demo_brainstorming_session()

        # 演示 5: 团队决策
        await demo_decision_making()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ RoundRobin 模式确保每个 Agent 都有发言机会")
        print("  ✓ 公平的轮询机制适用于需要全面讨论的场景")
        print("  ✓ 可以收集多角度、多专业的意见")
        print("  ✓ 适合头脑风暴、决策讨论等场景")
        print("  ✓ 通过多轮讨论可以深入探讨问题")
        print()
        print("下一步:")
        print("  1. 查看 demo_27_selector_team.py 学习选择式团队")
        print("  2. 查看 demo_28_custom_team.py 学习自定义团队")
        print("  3. 查看 tools/ 目录学习工具使用")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
"""
Demo 32: 记忆管理 - 上下文持久化

本演示展示如何:
1. 实现短期记忆（会话记忆）
2. 实现长期记忆（持久化存储）
3. 记忆检索和相关性
4. 记忆摘要和压缩
5. 多轮对话中的上下文保持

运行方式:
    python demo_32_memory_management.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解基础 Agent 使用

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/memory.html
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
from typing import List, Dict, Any, Optional
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 记忆系统类 =====
class MemoryStore:
    """记忆存储基类"""
    

    def __init__(self):
        self.memories: List[Dict[str, Any]] = []
    
    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加记忆"""
        memory = {
            "content": content,
            "timestamp": asyncio.get_event_loop().time(),
            "metadata": metadata or {}
        }
        self.memories.append(memory)
        return memory
    
    def search_memories(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """搜索相关记忆"""
        # 简单的关键词匹配
        query_lower = query.lower()
        keywords = query_lower.split()
        
        scored = []
        for memory in self.memories:
            content_lower = memory["content"].lower()
            score = sum(1 for keyword in keywords if keyword in content_lower)
            if score > 0:
                scored.append((score, memory))
        
        # 按相关性排序
        scored.sort(key=lambda x: x[0], reverse=True)
        
        return [m[1] for m in scored[:limit]]
    
    def get_recent_memories(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近的记忆"""
        return self.memories[-limit:] if len(self.memories) > limit else self.memories
    
    def summarize_memories(self) -> str:
        """摘要所有记忆"""
        if not self.memories:
            return "没有记忆"
        
        contents = [m["content"] for m in self.memories]
        all_text = " | ".join(contents)
        
        # 简单摘要：取前 200 字符
        if len(all_text) > 200:
            summary = all_text[:200] + "..."
        else:
            summary = all_text
        
        return summary


class ShortTermMemory(MemoryStore):
    """短期记忆 - 会话级别"""
    
    def __init__(self, max_size: int = 20):
        super().__init__()
        self.max_size = max_size
    
    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加记忆，超出限制时删除最旧的"""
        memory = super().add_memory(content, metadata)
        
        # 超出限制时删除最旧的
        if len(self.memories) > self.max_size:
            self.memories = self.memories[-self.max_size:]
        
        return memory
    
    def clear(self):
        """清空短期记忆"""
        self.memories = []


class LongTermMemory(MemoryStore):
    """长期记忆 - 持久化级别"""
    
    def __init__(self, max_size: int = 100):
        super().__init__()
        self.max_size = max_size
    
    def add_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """添加重要记忆到长期存储"""
        # 只添加带重要标记的记忆
        if metadata and metadata.get("important", False):
            memory = super().add_memory(content, metadata)
            
            # 超出限制时删除最旧的
            if len(self.memories) > self.max_size:
                self.memories = self.memories[-self.max_size:]
            
            return memory
        return None
    
    def clear(self):
        """清空长期记忆"""
        self.memories = []


# ===== 演示函数 =====
async def demo_short_term_memory():
    """演示 1: 短期记忆使用"""
    print("=" * 80)
    print("演示 1: 短期记忆（会话记忆）")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建短期记忆
    short_memory = ShortTermMemory(max_size=10)

    # 创建使用记忆的 Agent
    agent = AssistantAgent(
        name="memory_agent",
        model_client=model_client,
        description="你是一个有记忆的助手，可以记住对话中的重要信息。"
    )

    print("💬 多轮对话测试")
    print()

    # 模拟多轮对话
    conversation = [
        "我的名字是小明",
        "我最喜欢的颜色是蓝色",
        "我住在北京",
        "我的工作是什么？"  # 应该基于记忆回答不知道
    ]

    for message in conversation:
        # 添加到记忆
        short_memory.add_memory(message, metadata={"type": "user_input"})
        
        print(f"👤 用户: {message}")
        
        # 构建上下文
        context = f"对话历史:\n" + "\n".join([
            f"- {m['content']}" for m in short_memory.get_recent_memories(5)
        ])
        
        # Agent 处理
        result = await agent.run(task=message)
        
        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content[:150]}...")
        print()

    print("📊 记忆摘要:")
    print(short_memory.summarize_memories())

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_long_term_memory():
    """演示 2: 长期记忆和检索"""
    print("=" * 80)
    print("演示 2: 长期记忆和检索")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建长期记忆
    long_memory = LongTermMemory(max_size=20)

    # 创建使用长期记忆的 Agent
    agent = AssistantAgent(
        name="long_term_agent",
        model_client=model_client,
        description="你是一个有长期记忆的助手，可以记住重要的用户信息。"
    )

    # 添加一些初始记忆
    long_memory.add_memory(
        "用户是一名软件工程师，有5年经验",
        metadata={"important": True, "category": "work"}
    )
    long_memory.add_memory(
        "用户最近在学习 AutoGen 框架",
        metadata={"important": True, "category": "learning"}
    )
    long_memory.add_memory(
        "用户对 AI 助手系统很感兴趣",
        metadata={"important": True, "category": "interest"}
    )

    print("💬 记忆检索测试")
    print()
    print("📊 当前长期记忆:")
    for memory in long_memory.memories:
        print(f"   - {memory['content']}")
    print()

    # 测试检索
    queries = [
        "用户有什么工作经验？",
        "用户在学什么？",
        "用户对什么感兴趣？"
    ]

    for query in queries:
        print(f"👤 用户: {query}")
        
        # 搜索相关记忆
        relevant_memories = long_memory.search_memories(query, limit=3)
        
        if relevant_memories:
            context = "相关记忆:\n" + "\n".join([
                f"- {m['content']}" for m in relevant_memories
            ])
        else:
            context = "没有找到相关记忆"
        
        # Agent 处理
        result = await agent.run(task=f"{query}\n\n{context}")
        
        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content[:150]}...")
        print()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_memory_summary():
    """演示 3: 记忆摘要和压缩"""
    print("=" * 80)
    print("演示 3: 记忆摘要和压缩")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建记忆
    memory = MemoryStore()

    # 添加大量记忆
    long_text = """
    人工智能是计算机科学的一个重要分支，它企图了解智能的实质，
    并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
    该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
    机器学习是人工智能的核心技术之一，它使计算机能够在不需要明确编程的情况下学习。
    深度学习是机器学习的一个子集，它使用多层神经网络来学习数据的表示。
    """
    
    memory.add_memory(long_text, metadata={"category": "definition"})
    memory.add_memory(
        "Python 是一种高级编程语言，以其清晰的语法和代码可读性而闻名。",
        metadata={"category": "language"}
    )
    memory.add_memory(
        "AutoGen 是微软开发的多智能体框架，用于构建 AI 应用。",
        metadata={"category": "framework"}
    )

    # 创建摘要 Agent
    summarizer = AssistantAgent(
        name="summarizer",
        model_client=model_client,
        description="你是一个摘要助手，擅长总结和压缩信息。"
    )

    print("💬 记忆摘要测试")
    print()

    # 获取所有记忆
    all_memories = memory.get_recent_memories(limit=10)
    
    # 生成摘要
    summary_task = f"""请将以下记忆内容摘要为一个简洁的总结：
{chr(10).join([f"{i+1}. {m['content'][:100]}..." for i, m in enumerate(all_memories)])}

要求：
1. 突出关键信息
2. 控制在 200 字以内
3. 使用清晰的列表格式"""
    
    print(f"👤 任务: {summary_task[:100]}...")
    print()

    result = await summarizer.run(task=summary_task)
    
    print("📊 摘要结果:")
    last_message = result.messages[-1]
    print(f"{last_message.content[:300]}...")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_hybrid_memory():
    """演示 4: 混合记忆系统"""
    print("=" * 80)
    print("演示 4: 混合记忆系统")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建混合记忆系统
    short_term = ShortTermMemory(max_size=5)
    long_term = LongTermMemory(max_size=10)

    # 创建使用混合记忆的 Agent
    agent = AssistantAgent(
        name="hybrid_memory_agent",
        model_client=model_client,
        description="你是一个有混合记忆系统的助手，同时使用短期和长期记忆。"
    )

    print("💬 混合记忆测试")
    print()

    # 会话 1: 添加重要信息到长期记忆
    session1 = [
        "我叫李华，是一名数据科学家",
        "我的专业是数据分析和机器学习",
        "我住在上海"
    ]

    for message in session1:
        print(f"👤 用户: {message}")
        
        # 同时添加到两种记忆
        short_term.add_memory(message)
        long_term.add_memory(message, metadata={"important": True})
        
        result = await agent.run(task=message)
        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content[:100]}...")
        print()

    print("\n─ 新会话开始 ─\n")

    # 会话 2: 使用短期记忆
    session2 = [
        "我最近在做什么项目？",  # 应该检索长期记忆
        "今天天气怎么样？"
    ]

    for message in session2:
        print(f"👤 用户: {message}")
        
        short_term.add_memory(message)
        
        # 构建上下文（包括短期和长期记忆）
        short_term_context = short_term.summarize_memories()
        long_term_context = "\n".join([
            f"- {m['content']}" for m in long_term.get_recent_memories(5)
        ])
        
        full_context = f"近期对话:\n{short_term_context}\n\n长期记忆:\n{long_term_context}"
        
        result = await agent.run(task=f"{message}\n\n{full_context}")
        last_message = result.messages[-1]
        print(f"🤖 助手: {last_message.content[:100]}...")
        print()

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_memory_efficiency():
    """演示 5: 记忆效率优化"""
    print("=" * 80)
    print("演示 5: 记忆效率优化")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建限制大小的记忆
    memory = ShortTermMemory(max_size=3)

    # 创建效率 Agent
    agent = AssistantAgent(
        name="efficient_agent",
        model_client=model_client,
        description="你是一个高效助手，专注于最重要和最新的信息。"
    )

    print("💬 记忆效率测试")
    print()

    # 快速添加多个记忆
    for i in range(5):
        memory.add_memory(f"消息 {i+1}")

    print(f"📊 记忆状态:")
    print(f"   总记忆数: {len(memory.memories)}")
    print(f"   最近3条: {[m['content'] for m in memory.get_recent_memories(3)]}")
    print()

    # 测试检索
    query = "最新的消息是什么？"
    print(f"👤 用户: {query}")
    print()

    # 只传递最近的记忆
    recent_memories = memory.get_recent_memories(3)
    context = "最近的对话:\n" + "\n".join([
        f"- {m['content']}" for m in recent_memories
    ])

    result = await agent.run(task=f"{query}\n\n{context}")
    
    last_message = result.messages[-1]
    print(f"🤖 助手: {last_message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔════════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - 记忆管理演示               ║
║           Memory Management & Context Persistence          ║
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

        # 演示 1: 短期记忆
        await demo_short_term_memory()

        # 演示 2: 长期记忆
        await demo_long_term_memory()

        # 演示 3: 记忆摘要
        await demo_memory_summary()

        # 演示 4: 混合记忆
        await demo_hybrid_memory()

        # 演示 5: 记忆效率
        await demo_memory_efficiency()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 短期记忆用于会话级别的临时存储")
        print("  ✓ 长期记忆用于持久化存储重要信息")
        print("  ✓ 可以实现记忆检索和相关性匹配")
        print("  ✓ 记忆摘要和压缩可以减少 token 使用")
        print("  ✓ 混合记忆系统结合短期和长期存储")
        print()
        print("下一步:")
        print("  1. 查看 demo_33_human_interaction.py 学习人工交互")
        print("  2. 查看 demo_34_image_messages.py 学习多模态")
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
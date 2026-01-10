# AutoGen Advanced Topics - 官方文档参考

本文档列出了 AutoGen AgentChat 的高级主题及其对应的官方文档链接。

## 📚 已实现的 Demo 文件

### 02-agentchat/advanced 目录

1. **demo_32_memory_management.py** - 内存管理
   - 已包含基于官方文档的示例
   - 涵盖 ListMemory 和 ChromaDBVectorMemory

2. **demo_33_human_interaction.py** - 人机交互
   - 已包含基于官方文档的示例
   - 涵盖 UserProxyAgent 和交互模式

3. **demo_34_image_messages.py** - 图像消息处理
   - 多模态输入处理
   - 图像理解和分析

### 01-core/advanced 目录

1. **demo_16_multitenancy.py** - 多租户
2. **demo_17_event_sourcing.py** - 事件溯源
3. **demo_18_distributed_runtime.py** - 分布式运行时

## 📖 官方文档资源

### 核心 Advanced 主题

#### 1. Human-in-the-Loop (人机交互)
**官方文档**: [Human-in-the-Loop — AutoGen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html)

**主要内容**:
- 在团队运行期间提供反馈 (UserProxyAgent)
- 在运行终止后提供反馈
- 使用 max_turns 控制交互
- 使用 Termination Conditions (HandoffTermination, TextMentionTermination)

**关键代码示例**:
```python
from autogen_agentchat.agents import AssistantAgent, UserProxyAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_agentchat.ui import Console
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(model="gpt-4o-mini")
assistant = AssistantAgent("assistant", model_client=model_client)
user_proxy = UserProxyAgent("user_proxy", input_func=input)

termination = TextMentionTermination("APPROVE")
team = RoundRobinGroupChat([assistant, user_proxy], termination_condition=termination)

await Console(team.run_stream(task="Write a 4-line poem about the ocean."))
```

#### 2. Memory and RAG (内存和检索增强生成)
**官方文档**: [Memory and RAG — AutoGen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/memory.html)

**主要内容**:
- Memory 协议 (query, update_context, add, clear, close)
- ListMemory 示例
- ChromaDBVectorMemory (向量数据库)
- RedisMemory
- RAG Agent 实现
- Mem0Memory

**关键代码示例**:
```python
from autogen_agentchat.agents import AssistantAgent
from autogen_core.memory import ListMemory, MemoryContent, MemoryMimeType
from autogen_ext.models.openai import OpenAIChatCompletionClient

# 初始化内存
user_memory = ListMemory()
await user_memory.add(MemoryContent(
    content="The weather should be in metric units",
    mime_type=MemoryMimeType.TEXT
))

# 创建带内存的 Agent
assistant_agent = AssistantAgent(
    name="assistant_agent",
    model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    memory=[user_memory],
)
```

#### 3. Termination Conditions (终止条件)
**官方文档**: [Termination — AutoGen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html)

**主要内容**:
- 内置终止条件
  - MaxMessageTermination
  - TextMentionTermination
  - TokenUsageTermination
  - TimeoutTermination
  - HandoffTermination
  - SourceMatchTermination
  - ExternalTermination
  - TextMessageTermination
  - FunctionCallTermination
  - FunctionalTermination
- 组合终止条件 (AND/OR)
- 自定义终止条件

#### 4. Teams (团队协作)
**官方文档**: [Teams — AutoGen](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html)

**主要内容**:
- RoundRobinGroupChat
- SelectorGroupChat
- MagenticOneGroupChat
- Swarm
- 观察团队行为
- 重置团队
- 停止团队
- 恢复团队
- 单Agent团队

## 🔧 如何从官方文档创建新示例

### 步骤 1: 获取官方文档
使用 webReader 工具或直接访问官方文档:
```bash
# 使用 curl 获取文档
curl -s https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/<topic>.html
```

### 步骤 2: 提取代码示例
官方文档中的代码示例通常在代码块中:
```
```python
from autogen_agentchat.agents import AssistantAgent
...
```
```

### 步骤 3: 创建 Demo 文件
使用以下模板创建新的 demo 文件:

```python
"""
AutoGen AgentChat Tutorial - <Topic Name>

本示例展示如何:
1. <Feature 1>
2. <Feature 2>
3. <Feature 3>

基于官方文档: <Official URL>
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.agents import AssistantAgent
# ... 其他导入

# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 演示函数 =====
async def demo_basic_<feature>():
    """演示: <Description>"""
    print("=" * 80)
    print("演示: <Title>")
    print("=" * 80 + "\n")

    settings = get_settings()
    # ... 实现代码

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("AutoGen AgentChat Tutorial - <Topic>")
    print("=" * 80 + "\n")

    try:
        await demo_basic_<feature>()
        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
```

### 步骤 4: 添加路径和编码修复
所有 demo 文件都需要包含:
1. 路径设置代码 (sys.path)
2. 编码环境变量 (PYTHONIOENCODING)
3. 配置管理 (from common.config import get_settings)
4. base_url 设置 (如果使用 OpenAI)

## 📋 待创建的 Tutorial 文件

以下 tutorial 目录的文件需要从官方文档创建:

- [x] agents.py - ✅ 已完成
- [ ] teams.py - 基于 [Teams 官方文档](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html)
- [ ] termination.py - 基于 [Termination 官方文档](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/termination.html)
- [ ] human-in-the-loop.py - 基于 [Human-in-the-Loop 官方文档](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/human-in-the-loop.html)
- [ ] managing-state.py - 基于 [Managing State 官方文档](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/state.html)
- [ ] messages.py - 基于 [Messages 官方文档](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/messages.html)
- [ ] models.py - 基于 [Models 官方文档](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/models.html)

## 🔗 相关资源

- [AutoGen GitHub Repository](https://github.com/microsoft/autogen)
- [AutoGen Official Documentation](https://microsoft.github.io/autogen/stable/)
- [AutoGen AgentChat User Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html)

## 📝 注意事项

1. 所有 demo 文件都应包含路径设置和编码修复
2. 使用 `get_settings()` 获取配置而不是硬编码 API Key
3. 添加适当的中文注释说明
4. 确保代码可以在 Python 3.10+ 环境中运行
5. 测试每个 demo 确保可以正常运行

---

**更新日期**: 2025-01-09
**AutoGen 版本**: 0.4+

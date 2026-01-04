# LangChain 1.x 核心组件学习项目 (2025更新版)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://python.org)
[![LangChain 1.0](https://img.shields.io/badge/langchain-1.0+-orange.svg)](https://python.langchain.com/)
[![LangGraph](https://img.shields.io/badge/langgraph-1.0+-green.svg)](https://python.langchain.com/)

一个全面的 LangChain 1.x 学习项目，包含所有核心组件的详细示例和最佳实践。
**更新日期：2025年1月 | 当前版本: LangChain 1.2.0 + LangGraph 1.0.5**

## 📚 项目概述

本项目提供了 LangChain 1.x 框架的完整学习路径，从基础概念到高级应用，涵盖了所有主要组件的使用方法。

> **最新更新（2025年1月）**：项目已优化以反映 LangChain 1.2.0 的 API。重点展示 LCEL (LangChain Expression Language) 的正确用法，并清理了所有已弃用的代码模式。详见 [OPTIMIZATION_SUMMARY_2025.md](./OPTIMIZATION_SUMMARY_2025.md)

### 🎯 核心变化

1. **LCEL 是构建链的标准方式** - 使用 pipe operator (`|`) 组合组件
2. **移除了所有已弃用的 Chain 类** - `LLMChain`, `SequentialChain`, `RouterChain` 等
3. **推荐使用 `@tool` 装饰器** - 简化工具定义 (06-agents)
4. **结构化输出支持 Pydantic v2** - 使用 `with_structured_output()`

### 🎯 学习目标
- 掌握 LCEL (LangChain Expression Language) - **构建链的标准方式**
- 理解何时使用 LCEL vs Agent
- 学会使用 `with_structured_output()` 和 Pydantic v2
- 掌握 `@tool` 装饰器定义工具
- 了解异步处理和性能优化技巧

### 📖 学习路径

```
推荐学习路径：

1. 01-models - 模型基础
   ↓
2. 02-prompts - 提示词管理
   ↓
3. 03-chains - LCEL 链式调用 ⚡ 已更新
   ↓
4. 06-agents - Agent 和工具使用 ⚡ 已更新
   ↓
5. 其他高级组件 (07-tools, 08-callbacks, etc.)

注意: 03-chains 和 06-agents 已根据 LangChain 1.2.0 API 更新
```

## 🏗️ 项目结构

```
langchain1.x/
├── 01-models/          # ✅ Models 组件 (LLM, Chat Models, Embeddings)
├── 02-prompts/         # ✅ Prompts 组件 (Templates, Selectors, Parsers)
├── 03-chains/          # ⚡ 已更新 - LCEL vs create_agent() 对比
├── 04-indexes/         # ⚠️ Indexes 组件 (待检查)
├── 05-memory/          # ⚠️ Memory 组件 (待检查)
├── 06-agents/          # ⚡ 已更新 - create_agent() API
├── 07-tools/           # ⚠️ Tools 组件 (待检查)
├── 08-callbacks/       # ⚠️ Callbacks 组件 (待检查)
├── 09-structured-output/ # ⚠️ 结构化输出 (待检查)
├── requirements.txt    # ✅ 依赖列表 (已更新)
├── OPTIMIZATION_SUMMARY_2025.md # ⚡ 最新优化总结
├── LANGCHAIN_1X_MIGRATION_GUIDE.md # ⚡ 迁移指南
└── README.md          # ⚡ 已更新
```

### 标记说明
- ✅ **已完成** - 符合 LangChain 1.0+ 标准
- ⚡ **已更新** - 2025年1月最新优化
- ⚠️ **待检查** - 需要验证是否符合最新标准

## 🚀 LangChain 1.0+ 新特性（2025更新）

### 1. 统一的Agent抽象 (`create_agent`)

**新的标准方式构建agents** - 替代旧的 chains:

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from pydantic import BaseModel

class ResponseFormat(BaseModel):
    summary: str
    sentiment: str

# 使用 create_agent API
agent = create_agent(
    model="gpt-4o-mini",
    tools=[tool1, tool2],
    system_prompt="你是一个有用的助手",  # 注意: system_prompt 不是 prompt
    response_format=ResponseFormat,  # 结构化输出
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "Analyze this text"}]
})
```

**关键参数**:
- ✅ `system_prompt` (不是 `prompt`) - 系统提示词
- ✅ `model` - 字符串或模型实例
- ✅ `tools` - 使用 `@tool` 装饰器定义
- ✅ `response_format` - Pydantic v2 结构化输出
- ✅ `checkpointer` - 记忆持久化
- ✅ `middleware` - 动态提示修改

### 2. LangGraph原生集成
所有agents现在基于LangGraph构建：

```python
from langgraph.graph import StateGraph, MessagesState
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-4o-mini")

# 使用StateGraph构建自定义agent
workflow = StateGraph(MessagesState)
workflow.add_node("agent", agent_node)
workflow.add_edge("__start__", "agent")
app = workflow.compile()
```

### 3. 改进的结构化输出（Pydantic v2支持）
`with_structured_output()` 现在支持更多策略：

```python
from pydantic import BaseModel, Field

class MovieDetails(BaseModel):
    title: str
    year: int
    rating: float

# 使用ProviderStrategy（原生结构化输出）
structured_model = model.with_structured_output(MovieDetails)

result = structured_model.invoke("Tell me about Inception")
# 返回验证后的Pydantic对象
```

### 4. Model Profiles
聊天模型现在暴露其功能：

```python
model = ChatOpenAI(model="gpt-4o")
print(model.profile)
# 显示模型支持的功能（流式、工具调用、结构化输出等）
```

### 5. LCEL仍然适用
对于简单任务，LCEL仍然推荐使用：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

chain = ChatPromptTemplate.from_template("Tell me about {topic}") | ChatOpenAI() | StrOutputParser()
result = chain.invoke({"topic": "AI"})
```

## 📖 学习路径

### 第一阶段：基础组件
1. **[Models](01-models/)** - 学习 LLM、Chat Models 和 Embeddings
2. **[Prompts](02-prompts/)** - 掌握提示模板和输出解析器
3. **[Chains](03-chains/)** - 理解 LCEL 和链式组合

### 第二阶段：数据与检索
4. **[Indexes](04-indexes/)** - 学习文档处理和向量存储
5. **[Memory](05-memory/)** - 掌握对话记忆机制

### 第三阶段：智能应用（重要更新）
6. **[Agents](06-agents/)** - 使用 `create_agent()` 和 LangGraph 构建agents
7. **[Tools](07-tools/)** - 集成外部工具和 API
8. **[Callbacks](08-callbacks/)** - 实现监控和回调机制

> **⚠️ 重要提示**：传统的 `LLMChain`, `SequentialChain`, `RouterChain` 等已在 v1.0 中移除。请使用 LCEL 或 `create_agent()`。

## 🛠️ 环境配置

### 1. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 或者安装特定模块的依赖
pip install -r 01-models/requirements.txt
```

### 2. 配置 API 密钥

```bash
# 设置 OpenAI API 密钥
export OPENAI_API_KEY="your-api-key"

# 或者创建 .env 文件
echo "OPENAI_API_KEY=your-api-key" > .env
```

### 3. 运行示例

```bash
# 运行基础示例
python 01-models/basic_example.py

# 运行高级示例
python 01-models/advanced_example.py
```

## 📋 核心概念

### Models 组件
- **LLMs**: 文本生成模型
- **Chat Models**: 对话式模型，支持多轮交互
- **Embeddings**: 文本向量化，用于语义搜索

### Prompts 组件
- **Prompt Templates**: 可重用的提示模板
- **Example Selectors**: 动态示例选择
- **Output Parsers**: 结构化输出解析

### Chains 组件
- **LCEL**: LangChain Expression Language
- **Runnable**: 可组合的组件接口
- **Parallel**: 并行处理

### Indexes 组件
- **Document Loaders**: 文档加载器
- **Text Splitters**: 文本分割器
- **Vector Stores**: 向量数据库

## 🏆 最佳实践（2025更新）

### 1. 使用 `create_agent()` 而非旧的Chains
```python
# ✅ 推荐 (LangChain 1.0+)
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o-mini",
    tools=tools,
    response_format=OutputSchema
)

# ❌ 已移除
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
```

### 2. LCEL用于简单任务
```python
# ✅ 推荐 - 用于简单的prompt-model-parser链
chain = prompt | llm | output_parser
result = chain.invoke({"input": "Hello"})

# 对于复杂逻辑，使用LangGraph
```

### 3. 异步处理
```python
# ✅ 推荐
async def process_batch():
    tasks = [agent.ainvoke({"messages": [("user", item)]}) for item in items]
    return await asyncio.gather(*tasks)
```

### 4. 结构化输出
```python
# ✅ 推荐 - 使用Pydantic v2
from pydantic import BaseModel, Field

class Output(BaseModel):
    summary: str = Field(description="摘要")
    score: float = Field(description="评分", ge=0, le=10)

structured_model = model.with_structured_output(Output)
result = structured_model.invoke("Analyze this...")
```

### 5. 流式处理
```python
# ✅ 推荐 - Agent支持流式输出
for chunk in agent.stream({"messages": [("user", "Hello")]}):
    print(chunk)

# 异步流式
async for chunk in agent.astream({"messages": [("user", "Hello")]}):
    print(chunk)
```

### 6. 错误处理
```python
from langchain_core.exceptions import LangChainException

try:
    result = await agent.ainvoke({"messages": messages})
except LangChainException as e:
    logger.error(f"Agent execution failed: {e}")
```

## 🔧 开发工具

### 测试
```bash
# 运行测试
pytest

# 运行异步测试
pytest --asyncio-mode=auto
```

### 代码检查
```bash
# 语法检查
python -m py_compile your_file.py

# 类型检查
mypy your_file.py
```

## 📊 版本对比

| 特性 | LangChain 0.x | LangChain 1.0+ (2025) |
|------|---------------|---------------------|
| Agent构建 | LLMChain, SequentialChain | `create_agent()` + LangGraph |
| 异步支持 | 有限 | 原生支持所有组件 |
| 类型安全 | 基础 (Pydantic v1) | 完善 (Pydantic v2) |
| 结构化输出 | 输出解析器 | `with_structured_output()` |
| 流式处理 | 基础 | 增强流式 + 自动流式 |
| 状态管理 | Memory组件 | LangGraph StateGraph |
| 性能 | 中等 | 优化 (并发、批处理) |
| 可维护性 | 中等 | 优秀 (统一抽象) |
| 学习曲线 | 陡峭 | 平缓 (简化API) |

## 🔗 相关资源

### 官方文档
- [LangChain 官方文档](https://python.langchain.com/)
- [LCEL 指南](https://python.langchain.com/docs/concepts/lcel/)
- [LangGraph 文档](https://python.langchain.com/docs/langgraph/)
- [LangChain 1.0 迁移指南](./LANGCHAIN_1X_MIGRATION_GUIDE.md)
- [LangGraph 1.0 迁移指南](https://python.langchain.com/docs/versions/migrating_agents/)

### 社区资源
- [LangChain Discord](https://discord.gg/langchain)
- [GitHub Discussions](https://github.com/langchain-ai/langchain/discussions)
- [示例项目](https://github.com/langchain-ai/langchain/tree/master/examples)

### 学习资料
- [LangChain Cookbooks](https://python.langchain.com/docs/integrations/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [LLM 应用开发指南](https://github.com/e2b-dev/awesome-llm-apps)

## 🤝 贡献指南

欢迎贡献代码和建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangChain 团队](https://github.com/langchain-ai) 提供的出色框架
- 所有贡献者的努力和支持
- OpenAI 提供的强大模型

---

💡 **开始学习**: 从 [01-models](01-models/) 开始你的 LangChain 1.x 之旅！

如有问题，请查看 [FAQ](./FAQ.md) 或在 [Issues](https://github.com/your-repo/issues) 中提问。
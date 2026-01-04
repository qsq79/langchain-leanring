# LangChain Chains 学习指南 (LangChain 1.0+ 版本)

**重要更新 (2025)**: LangChain 1.0+ 引入了 `create_agent()` API,这是一个统一的高级接口,已经集成了提示词、模型、工具、记忆和结构化输出。对于大多数使用场景,**推荐使用 `create_agent()` 而不是手动构建链**。

本指南将帮助您理解:
- 何时使用 `create_agent()` (推荐)
- 何时使用 LCEL (LangChain Expression Language)
- 何时使用 LangGraph Graph API

## 📋 核心知识点

### 1. 三种 API 的选择指南

#### 1.1 `create_agent()` - 推荐(大多数场景)

**使用场景**:
- ✅ 需要使用工具(tools)的智能体
- ✅ 需要对话记忆(memory)
- ✅ 需要结构化输出
- ✅ 需要自主规划和执行
- ✅ 生产环境的 Agent 应用

**示例**:
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    """执行数学计算"""
    return str(eval(expression))

# 使用 create_agent 创建智能体
agent = create_agent(
    model="gpt-4o-mini",
    tools=[calculator],
    system_prompt="你是一个有用的数学助手",
)

result = agent.invoke({
    "messages": [{"role": "user", "content": "计算 25 * 4"}]
})
```

#### 1.2 LCEL (LangChain Expression Language) - 简单链

**使用场景**:
- ✅ 简单的 prompt → model → parser 流程
- ✅ **不需要**使用工具
- ✅ **不需要**对话记忆
- ✅ 快速原型和简单任务
- ✅ 需要精细控制每个步骤

**示例**:
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 使用 LCEL 构建简单链
llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template("解释: {topic}")
chain = prompt | llm | StrOutputParser()

result = chain.invoke({"topic": "量子计算"})
```

#### 1.3 LangGraph Graph API - 复杂工作流

**使用场景**:
- ✅ 复杂的多步骤工作流
- ✅ 需要显式的状态管理
- ✅ 复杂的条件分支和循环
- ✅ 需要可视化工作流
- ✅ 自定义执行逻辑

**示例**:
```python
from langgraph.graph import StateGraph
from typing import TypedDict

class AgentState(TypedDict):
    messages: list
    step_count: int

def call_llm(state):
    # LLM 节点逻辑
    pass

def should_continue(state):
    # 条件路由逻辑
    return "continue" if state["step_count"] < 3 else "end"

# 使用 Graph API 构建复杂工作流
workflow = StateGraph(AgentState)
workflow.add_node("llm", call_llm)
workflow.add_conditional_edges("llm", should_continue)
app = workflow.compile()
```

### 2. 对比表

| 特性 | create_agent() | LCEL | LangGraph Graph API |
|-----|----------------|------|---------------------|
| **适用场景** | Agent 应用 | 简单链 | 复杂工作流 |
| **工具支持** | ✅ 原生支持 | ❌ 需要手动实现 | ✅ 原生支持 |
| **记忆管理** | ✅ 内置 checkpointer | ❌ 需要手动实现 | ✅ 状态管理 |
| **结构化输出** | ✅ response_format | ✅ with_structured_output() | ✅ 自定义 |
| **学习曲线** | 低 | 低 | 中-高 |
| **代码量** | 最少 | 少 | 多 |
| **灵活性** | 中 | 中 | 高 |
| **生产就绪** | ✅ | ✅ | ✅ |

## 🎯 常见面试题

### 基础概念题

**Q1: LangChain 1.0+ 中应该使用 `create_agent()` 还是 LCEL?**

**A1:**
- **使用 `create_agent()`** 当你需要:
  - 使用工具(tools)让 LLM 执行操作
  - 对话记忆和状态管理
  - 结构化输出
  - Agent 自主规划能力

- **使用 LCEL** 当你需要:
  - 简单的 prompt → model 流程
  - 不需要工具和记忆
  - 更精细的步骤控制
  - 快速原型验证

- **使用 LangGraph Graph API** 当你需要:
  - 复杂的多步骤工作流
  - 显式的状态管理和可视化
  - 自定义的执行逻辑和错误处理

**Q2: `create_agent()` 相比手动构建链有什么优势?**

**A2:**
- **统一接口**: 一个函数处理所有 Agent 相关配置
- **内置功能**: 自动处理工具调用、记忆管理、流式输出
- **生产就绪**: 基于稳定的 LangGraph 运行时
- **更少代码**: 不需要手动组合 prompt、model、parser
- **类型安全**: 支持 Pydantic v2 的结构化输出
- **易于扩展**: 支持中间件、子 Agent、人工干预

### 技术实现题

**Q3: 如何实现一个简单的问答助手?**

**A3: 使用 `create_agent()` (推荐)**
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

qa_agent = create_agent(
    model="gpt-4o-mini",
    tools=[],  # 不需要工具
    system_prompt="你是一个专业的问答助手。请简洁准确地回答问题。",
)

response = qa_agent.invoke({
    "messages": [{"role": "user", "content": "什么是 LangChain?"}]
})
print(response["messages"][-1].content)
```

**或者使用 LCEL (更轻量)**
```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(model="gpt-4o-mini")
prompt = ChatPromptTemplate.from_template(
    "你是一个专业的问答助手。请简洁准确地回答问题。\n\n问题: {question}"
)
qa_chain = prompt | llm | StrOutputParser()

response = qa_chain.invoke({"question": "什么是 LangChain?"})
print(response)
```

**Q4: 如何实现一个带记忆的对话 Agent?**

**A4:**
```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver

# 创建带记忆的 Agent
memory = MemorySaver()

chat_agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt="你是一个友好的聊天助手",
    checkpointer=memory,  # 添加记忆
)

# 使用 thread_id 保持会话
config = {"configurable": {"thread_id": "user-123"}}

# 第一轮对话
response1 = chat_agent.invoke(
    {"messages": [{"role": "user", "content": "我叫张三"}]},
    config
)

# 第二轮对话 - Agent 记住了之前的对话
response2 = chat_agent.invoke(
    {"messages": [{"role": "user", "content": "我叫什么名字?"}]},
    config
)
print(response2["messages"][-1].content)  # 输出: 你叫张三
```

**Q5: 如何实现结构化输出?**

**A5: 使用 `create_agent()` 的 `response_format`**
```python
from pydantic import BaseModel, Field
from typing import List
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

class AnalysisResult(BaseModel):
    """分析结果的结构化输出"""
    summary: str = Field(description="问题总结")
    key_points: List[str] = Field(description="关键点列表")
    confidence: float = Field(description="置信度 (0-1)")

analysis_agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt="你是一个专业的文本分析助手",
    response_format=AnalysisResult,  # 结构化输出
)

response = analysis_agent.invoke({
    "messages": [{"role": "user", "content": "分析这段文本: ..."}]
})

# 访问结构化输出
result = response.structuredResponse
print(f"总结: {result.summary}")
print(f"关键点: {result.key_points}")
print(f"置信度: {result.confidence}")
```

## 🏗️ 迁移指南

### 从旧式 Chain 迁移到 `create_agent()`

#### ❌ 旧方式 (已弃用)
```python
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(
    template="回答: {question}",
    input_variables=["question"]
)
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(question="什么是 AI?")
```

#### ✅ 新方式 (推荐)
```python
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt="回答用户的问题",
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "什么是 AI?"}]
})
```

### 从 LCEL 迁移到 `create_agent()`

#### 使用 LCEL (仍然有效)
```python
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"question": "什么是 AI?"})
```

#### 迁移到 `create_agent()` (如果需要更多功能)
```python
agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt=prompt.template,
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "什么是 AI?"}]
})
```

## 💡 最佳实践

### 1. 选择正确的 API

```python
# ✅ 正确: 使用 create_agent() 构建 Agent
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o-mini",
    tools=[search_tool, calculator],
    system_prompt="你是一个研究助理",
)

# ✅ 正确: 使用 LCEL 构建简单链
from langchain_core.output_parsers import StrOutputParser

simple_chain = prompt | llm | StrOutputParser()

# ✅ 正确: 使用 Graph API 构建复杂工作流
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)
# ... 添加节点和边
```

### 2. 使用 Pydantic v2 定义结构化输出

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class TaskResult(BaseModel):
    """任务结果的结构化输出"""
    task_id: str = Field(description="任务ID")
    status: str = Field(description="状态: success/failed/pending")
    result: Optional[str] = Field(default=None, description="执行结果")
    error: Optional[str] = Field(default=None, description="错误信息")

agent = create_agent(
    model="gpt-4o-mini",
    tools=[task_executor],
    system_prompt="执行任务并返回结构化结果",
    response_format=TaskResult,
)
```

### 3. 添加记忆支持

```python
from langgraph.checkpoint.memory import MemorySaver

# 内存存储 (开发环境)
memory = MemorySaver()

# 生产环境使用持久化存储
# from langgraph.checkpoint.postgres import PostgresSaver
# memory = PostgresSaver.from_conn_string("postgresql://...")

agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt="你是一个有记忆的助手",
    checkpointer=memory,
)

# 使用 thread_id 保持会话
config = {"configurable": {"thread_id": "session-123"}}
response = agent.invoke(
    {"messages": [{"role": "user", "content": "你好"}]},
    config
)
```

### 4. 使用中间件动态修改提示

```python
from langchain_core.middleware import dynamic_prompt

@dynamic_prompt
def add_context(request):
    """根据请求动态添加上下文"""
    user_id = request.config.get("context", {}).get("user_id")
    if user_id == "premium":
        return "\n\n这是一个高级用户,提供更详细的服务。"
    return "\n\n这是一个标准用户,提供简洁的服务。"

agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt="你是一个有用的助手",  # 基础提示
    middleware=[add_context],  # 动态修改
)

# 高级用户获得更详细的服务
response = agent.invoke(
    {"messages": [{"role": "user", "content": "解释量子计算"}]},
    {"config": {"context": {"user_id": "premium"}}}
)
```

## 📚 相关资源

- [LangChain Agents 官方文档](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph Graph API 文档](https://docs.langchain.com/oss/python/langgraph)
- [LCEL 指南](https://python.langchain.com/docs/expression_language/)
- [迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1)

---

💡 **学习建议**:
1. **优先学习 `create_agent()`** - 这是大多数应用的推荐方式
2. **掌握 LCEL** - 用于构建简单链和快速原型
3. **了解 Graph API** - 当需要构建复杂工作流时使用
4. **查看示例** - 参考 06-agents 和 03-chains 目录下的示例代码

# LangChain 1.x 目录优化总结 (2025)

## 📌 优化概述

本次优化基于 LangChain 1.0+ 最新 API,重点关注 `create_agent()` 统一接口的应用,并清理了所有已弃用的代码模式。

**优化日期**: 2025年1月
**主要变更**: 从手动构建链迁移到 `create_agent()` API
**影响范围**: 03-chains, 06-agents 目录

---

## 🎯 核心变更

### 1. 主要发现: `create_agent()` 是新的推荐方式

根据 LangChain 官方最新文档,`create_agent()` 现在是构建大多数应用的推荐方式:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o-mini",
    tools=[tool1, tool2],
    system_prompt="你是一个有用的助手",  # 注意: system_prompt 不是 prompt
    response_format=OutputSchema,  # 可选: 结构化输出
    checkpointer=MemorySaver(),  # 可选: 记忆管理
    middleware=[...],  # 可选: 中间件
)
```

**关键参数变化**:
- ✅ `system_prompt` (新) - 替代旧的 `prompt` 参数
- ✅ `model` - 可以是字符串或模型实例
- ✅ `tools` - 使用 `@tool` 装饰器定义的工具
- ✅ `response_format` - 结构化输出 (Pydantic v2)
- ✅ `checkpointer` - 记忆持久化
- ✅ `middleware` - 动态提示修改

---

## 📂 目录变更详情

### 03-chains (Chains 组件)

#### ✅ 已更新文件

**1. README.md** - 完全重写
- ✅ 添加了三种 API 的选择指南:
  - `create_agent()` - 推荐 (大多数场景)
  - LCEL - 简单链
  - LangGraph Graph API - 复杂工作流
- ✅ 添加了详细的对比表
- ✅ 添加了迁移指南 (从旧 API 到新 API)
- ✅ 添加了最佳实践示例

**2. basic_example.py** - 更新
- ✅ 添加了文件头说明,解释何时使用 LCEL vs `create_agent()`
- ✅ 添加了 `compare_apis_example()` 函数,对比两种方式
- ✅ 保留了所有 LCEL 示例 (仍然适用于简单链)
- ✅ 添加了清晰的注释说明各 API 的适用场景

**3. advanced_example.py** - 完全重写
- ✅ 移除了所有已弃用的 `LLMChain` 导入
- ✅ 移除了所有自定义 Chain 类 (CustomChain, ConditionalChain 等)
- ✅ 改用现代的 LCEL 模式:
  - 自定义 `Runnable` 类
  - `RunnableLambda` 包装器
  - `RunnableParallel` 并行处理
- ✅ 添加了高级示例:
  - 自定义 Runnable
  - 重试机制
  - 并行处理
  - 动态路由
  - 批处理
  - 流式输出
  - 错误处理
  - 复杂管道
  - 结构化输出

#### 📊 关键改进

| 旧方式 (已弃用) | 新方式 (推荐) |
|---------------|--------------|
| `LLMChain(llm=llm, prompt=prompt)` | `create_agent(model, tools, system_prompt)` |
| `SequentialChain([...])` | LCEL: `step1 | step2 | step3` |
| `RouterChain` | `RunnableLambda(route_function)` |
| 自定义 `Chain` 类 | 自定义 `Runnable` 类 |

---

### 06-agents (Agents 组件)

#### ✅ 已更新文件 (之前完成)

**1. README.md** - 完全重写
- ✅ 更新为 `create_agent()` API 文档
- ✅ 添加 `system_prompt` 参数说明
- ✅ 添加 `response_format` 结构化输出示例
- ✅ 添加中间件 (middleware) 用法
- ✅ 添加记忆管理 (checkpointer) 示例

**2. basic_example.py** - 完全重写
- ✅ 使用 `create_agent()` API
- ✅ 使用 `@tool` 装饰器
- ✅ 演示工具调用和结构化输出

---

## 🔄 API 迁移对照表

### 从旧 Chains 到新 API

#### ❌ 旧方式 (已弃用)
```python
from langchain.chains import LLMChain, SequentialChain
from langchain.prompts import PromptTemplate

prompt = PromptTemplate(template="回答: {question}")
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

### 从旧 Agent 到新 Agent

#### ❌ 旧方式 (已弃用)
```python
from langchain.agents import create_react_agent, AgentExecutor

agent = create_react_agent(llm, tools, prompt)
executor = AgentExecutor(agent=agent, tools=tools)
result = executor.invoke({"input": "question"})
```

#### ✅ 新方式 (推荐)
```python
from langchain.agents import create_agent

agent = create_agent(
    model="gpt-4o-mini",
    tools=tools,
    system_prompt="你是一个有用的助手",
)
result = agent.invoke({
    "messages": [{"role": "user", "content": "question"}]
})
```

---

## 📋 何时使用哪个 API?

### 使用 `create_agent()` 当你需要:

- ✅ 使用工具 (tools) 让 LLM 执行操作
- ✅ 对话记忆和状态管理
- ✅ 结构化输出 (response_format)
- ✅ Agent 自主规划能力
- ✅ 生产环境的智能体应用

**示例**: 聊天机器人、研究助理、数据分析 Agent

### 使用 LCEL 当你需要:

- ✅ 简单的 prompt → model 流程
- ✅ 不需要工具和记忆
- ✅ 更精细的步骤控制
- ✅ 快速原型验证

**示例**: 文本总结、格式转换、简单分类

### 使用 LangGraph Graph API 当你需要:

- ✅ 复杂的多步骤工作流
- ✅ 显式的状态管理和可视化
- ✅ 复杂的条件分支和循环
- ✅ 自定义的执行逻辑

**示例**: 多阶段审批流程、复杂决策树、自定义工作流引擎

---

## 🎓 学习路径建议

### 1. 初学者路径

```
01-models (模型基础)
   ↓
02-prompts (提示词管理) - ✅ 仍然相关
   ↓
03-chains (LCEL 基础) - ✅ 已更新
   ↓
06-agents (create_agent) - ✅ 已更新
   ↓
05-memory (记忆管理)
```

### 2. 进阶开发者路径

```
03-chains (LCEL 高级) - ✅ 已完全重写
   ↓
06-agents (高级 Agent) - ✅ 已更新
   ↓
07-tools (自定义工具)
   ↓
08-callbacks (回调机制)
   ↓
09-structured-output (结构化输出)
```

---

## 📁 未变更目录

以下目录未做重大变更,因为它们使用的 API 仍然有效:

- **01-models**: ✅ 模型 API 仍然有效
- **02-prompts**: ✅ Prompt 模板 API 仍然有效
- **04-indexes**: ⚠️ 需要检查 (向量存储集成)
- **05-memory**: ⚠️ 需要检查 (记忆组件)
- **07-tools**: ⚠️ 需要检查 (工具定义)
- **08-callbacks**: ⚠️ 需要检查 (回调系统)
- **09-structured-output**: ⚠️ 需要检查 (结构化输出)

---

## 🔧 技术细节

### Pydantic v2 迁移

所有示例都已更新为使用 Pydantic v2:

```python
# Pydantic v2
from pydantic import BaseModel, Field

class MyOutput(BaseModel):
    name: str = Field(description="名称")
    value: int = Field(description="数值")

# 使用 with_structured_output()
structured_llm = llm.with_structured_output(MyOutput)

# 或在 create_agent 中使用
agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    response_format=MyOutput,
)
```

### system_prompt vs prompt

**重要变更**: 参数名从 `prompt` 改为 `system_prompt`

```python
# ❌ 旧方式
agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    prompt="你是一个助手",  # 已弃用
)

# ✅ 新方式
agent = create_agent(
    model="gpt-4o-mini",
    tools=[],
    system_prompt="你是一个助手",  # 新参数名
)
```

---

## ✅ 完成清单

### 03-chains
- [x] 更新 README.md - 添加 API 选择指南
- [x] 更新 basic_example.py - 添加 API 对比
- [x] 完全重写 advanced_example.py - 移除已弃用的 Chain 类
- [x] 所有代码符合 LangChain 1.0+ 标准
- [x] 添加清晰的注释说明何时使用各 API

### 06-agents
- [x] 更新 README.md - 使用 `create_agent()` API
- [x] 更新 basic_example.py - 使用新 API
- [x] 添加 `system_prompt` 参数说明
- [x] 添加结构化输出示例
- [x] 添加记忆管理示例

### 其他目录
- [ ] 04-indexes - 需要检查向量存储集成
- [ ] 05-memory - 需要检查记忆组件
- [ ] 07-tools - 需要检查工具定义
- [ ] 08-callbacks - 需要检查回调系统
- [ ] 09-structured-output - 需要检查结构化输出

---

## 📚 参考资源

### 官方文档
- [LangChain Agents](https://docs.langchain.com/oss/python/langchain/agents)
- [LangGraph Graph API](https://docs.langchain.com/oss/python/langgraph)
- [LCEL 指南](https://python.langchain.com/docs/expression_language/)
- [迁移指南](https://docs.langchain.com/oss/python/migrate/langchain-v1)

### 内部文档
- [LANGCHAIN_1X_MIGRATION_GUIDE.md](./LANGCHAIN_1X_MIGRATION_GUIDE.md) - 完整迁移指南
- [UPDATE_SUMMARY_2025.md](./UPDATE_SUMMARY_2025.md) - 快速参考
- [03-chains/README.md](./03-chains/README.md) - Chains 组件详细指南
- [06-agents/README.md](./06-agents/README.md) - Agents 组件详细指南

---

## 🎯 下一步建议

### 立即行动
1. ✅ **学习 `create_agent()` API** - 这是大多数应用的推荐方式
2. ✅ **掌握 LCEL** - 用于构建简单链
3. ✅ **了解 Graph API** - 当需要复杂工作流时

### 后续优化
1. 检查 04-09 目录是否符合 LangChain 1.0+ 标准
2. 添加更多实际应用场景的示例
3. 添加性能优化最佳实践
4. 添加测试用例

---

## 📝 总结

本次优化重点关注:

1. **统一 API**: `create_agent()` 现在是构建大多数应用的推荐方式
2. **清理弃用代码**: 移除所有 `LLMChain`, `SequentialChain` 等已弃用的类
3. **清晰指导**: 明确说明何时使用哪个 API
4. **最佳实践**: 展示正确的使用模式和反模式

**关键要点**:
- ✅ 使用 `create_agent()` 构建 Agent 应用 (大多数场景)
- ✅ 使用 LCEL 构建简单链 (不需要工具的场景)
- ✅ 使用 LangGraph Graph API 构建复杂工作流
- ✅ 使用 `system_prompt` 而不是 `prompt`
- ✅ 使用 Pydantic v2 进行结构化输出

---

**最后更新**: 2025-01-03
**维护者**: Claude Code
**版本**: 1.0

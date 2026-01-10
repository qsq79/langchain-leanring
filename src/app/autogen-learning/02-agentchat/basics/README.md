# AgentChat API - 基础 Agent (Basics)

本目录包含 AgentChat API 基础 Agent 类型的演示代码。

## 目录

- [demo_19_assistant_agent.py](./demo_19_assistant_agent.py) - AssistantAgent 通用助手
- [demo_20_coding_agent.py](./demo_20_coding_agent.py) - CodingAgent 代码生成
- [demo_21_text_chat_agent.py](./demo_21_text_chat_agent.py) - TextChatAgent 文本对话
- [demo_22_user_proxy.py](./demo_22_user_proxy.py) - UserProxyAgent 用户代理

## 学习目标

通过这些示例，你将学会：

1. ✅ 使用 AssistantAgent 创建通用助手
2. ✅ 使用 CodingAgent 进行代码生成和执行
3. ✅ 使用 TextChatAgent 进行文本对话
4. ✅ 使用 UserProxyAgent 实现人在回路
5. ✅ 配置模型客户端
6. ✅ 管理对话历史

## Agent 类型对比

| Agent 类型 | 用途 | 特点 |
|-----------|------|------|
| **AssistantAgent** | 通用助手 | 使用 LLM 生成响应，支持多轮对话 |
| **CodingAgent** | 代码生成 | 专门用于编程任务，支持代码执行 |
| **TextChatAgent** | 文本对话 | 轻量级对话，适合简单问答 |
| **UserProxyAgent** | 用户代理 | 人在回路，需要人工确认 |

## 快速开始

### 安装依赖

```bash
cd src/app/autogen-learning
pip install -r requirements.txt
```

### 配置 API Key

```bash
cp .env.example .env
# 编辑 .env 文件，添加 OPENAI_API_KEY
```

### 运行示例

```bash
# Assistant Agent
python 02-agentchat/basics/demo_19_assistant_agent.py

# Coding Agent
python 02-agentchat/basics/demo_20_coding_agent.py
```

## 核心概念

### 模型客户端

AgentChat 需要模型客户端来与 LLM 交互：

```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

model_client = OpenAIChatCompletionClient(
    model="gpt-4o",
    api_key="your-api-key"
)
```

### Agent 配置

```python
from autogen_agentchat.agents import AssistantAgent

assistant = AssistantAgent(
    name="assistant",
    model_client=model_client,
    description="一个乐于助人的助手"
)
```

### 运行 Agent

```python
result = await assistant.run(
    task="解释什么是人工智能",
    max_turns=5
)

print(result.messages)
```

## 选择合适的 Agent

### AssistantAgent

**适用场景**:
- 通用问答
- 对话式交互
- 文本生成
- 翻译和总结

**优势**:
- 功能全面
- 易于使用
- 支持复杂任务

### CodingAgent

**适用场景**:
- 代码生成
- 代码审查
- Bug 修复
- 算法实现

**优势**:
- 专门优化的代码生成
- 支持代码执行
- 更好的代码格式化

### UserProxyAgent

**适用场景**:
- 需要人工干预
- 安全性要求高
- 调试和测试
- 人机协作

**优势**:
- 完全的人工控制
- 安全可靠
- 适合关键决策

## 相关文档

- [官方文档 - Agents](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/quickstart.html)
- [官方文档 - Model Client](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/using-llms.html)
- [前序: Core API](../../01-core/)
- [后续: Conversations](../conversations/)

继续学习：[demo_19_assistant_agent.py](./demo_19_assistant_agent.py) →
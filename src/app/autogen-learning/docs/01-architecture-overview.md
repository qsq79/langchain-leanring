# AutoGen 架构总览

本文档详细介绍 AutoGen 0.4+ 的架构设计和核心概念。

## 目录

- [架构演进](#架构演进)
- [分层架构](#分层架构)
- [Core API](#core-api)
- [AgentChat API](#agentchat-api)
- [Extensions 生态](#extensions-生态)
- [设计理念](#设计理念)
- [与其他框架对比](#与其他框架对比)

---

## 架构演进

### AutoGen 0.2 → 0.4 的变化

AutoGen 0.4 是一次**完全重新设计**，主要变化：

| 特性 | AutoGen 0.2 | AutoGen 0.4 |
|------|-------------|-------------|
| **架构** | 单一层次 | 分层架构 (Core + AgentChat) |
| **通信模式** | 直接函数调用 | 事件驱动的发布-订阅 |
| **类型安全** | 部分类型提示 | 完整的类型支持 |
| **异步模型** | 混合同步/异步 | 完全异步 |
| **扩展性** | 有限 | 模块化可扩展 |
| **分布式** | 不支持 | 原生支持 |
| **跨语言** | 仅 Python | Python + .NET |

### 重新设计的原因

1. **可扩展性**: 0.2 版本难以支持大规模分布式系统
2. **灵活性**: 需要更细粒度的控制能力
3. **类型安全**: 提高代码质量和可维护性
4. **生态系统**: 支持社区扩展和第三方集成

---

## 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                     Applications                        │
│  (Magentic-One, 自定义应用, 第三方解决方案)             │
├─────────────────────────────────────────────────────────┤
│                  AgentChat API                          │
│  高层抽象：快速构建对话式多 Agent 应用                  │
│  - AssistantAgent, CodingAgent, TextChatAgent          │
│  - Team: RoundRobinGroupChat, SelectorGroupChat        │
│  - 工具调用、记忆管理                                    │
├─────────────────────────────────────────────────────────┤
│                   Core API                              │
│  底层抽象：事件驱动的 Actor 框架                        │
│  - RoutedAgent, 生命周期管理                            │
│  - Topic, Subscription, 消息路由                        │
│  - Runtime: 单线程/分布式                                │
├─────────────────────────────────────────────────────────┤
│                  Extensions                             │
│  生态扩展：LLM、工具、存储、协议等                      │
│  - Models: OpenAI, Azure, Anthropic                     │
│  - Code Executors: Docker, 命令行                       │
│  - Tools: 文件, Web, MCP                                │
│  - Storage: 向量数据库, 云存储                           │
└─────────────────────────────────────────────────────────┘
```

### 层次职责

1. **Applications**: 最终用户应用
2. **AgentChat**: 快速开发接口 (替代 0.2)
3. **Core**: 核心运行时和消息传递
4. **Extensions**: 外部集成和扩展

---

## Core API

### 核心概念

#### 1. Actor 模型

AutoGen Core 基于 [Actor 模型](https://en.wikipedia.org/wiki/Actor_model)，每个 Agent 是一个独立的 Actor：

```python
from autogen_core import RoutedAgent, message_handler

class MyAgent(RoutedAgent):
    @message_handler
    async def handle_message(self, message: str, ctx) -> None:
        # 处理消息
        pass
```

**特点**:
- 每个 Agent 有独立的状态
- 通过异步消息通信
- 消息处理是串行的（单线程）

#### 2. Topic 和 Subscription

**Topic** 定义消息的范围：

```python
from autogen_core import TopicId

# Topic = (type, source)
topic = TopicId(type="order_created", source="client_a")
# Topic ID: "order_created/client_a"
```

**Subscription** 将 Topic 映射到 Agent：

```python
from autogen_core import TypeSubscription

# 订阅：所有 order_created 类型的消息
subscription = TypeSubscription(
    topic_type="order_created",
    agent_type="notification_agent"
)
```

**路由规则**:
- 发布到 `("order_created", "client_a")`
- 路由到 `("notification_agent", "client_a")`
- Runtime 自动创建或复用 Agent 实例

#### 3. Runtime

**SingleThreadedAgentRuntime**:

```python
from autogen_core import SingleThreadedAgentRuntime

runtime = SingleThreadedAgentRuntime()

# 注册 Agent
await MyAgent.register(runtime, "my_agent", lambda: MyAgent())

# 添加订阅
await runtime.add_subscription(
    TypeSubscription("my_topic", "my_agent")
)

# 启动
runtime.start()

# 发布消息
await runtime.publish_message(message, TopicId("my_topic", "default"))

# 等待完成
await runtime.stop_when_idle()
```

**特点**:
- 单线程事件循环
- 异步消息传递
- 适合单机应用

**GrpcWorkerAgentRuntime** (分布式):

```python
from autogen_core import GrpcWorkerAgentRuntime

runtime = GrpcWorkerAgentRuntime(host="localhost", port=50051)
# 支持跨进程、跨语言通信
```

#### 4. 消息传递模式

**直接消息** (1对1):
```python
# Agent 直接发送给另一个 Agent
await agent.send_message(message, recipient_id)
```

**广播消息** (1对多):
```python
# 发布到 Topic，所有订阅者接收
await runtime.publish_message(message, topic_id)
```

### Core API 适用场景

✅ **适合**:
- 需要精细控制消息流
- 构建自定义协议
- 分布式系统
- 高性能要求

❌ **不适合**:
- 快速原型开发
- 简单对话应用 (使用 AgentChat)

---

## AgentChat API

### 设计目标

AgentChat 是**高层抽象**，设计目标：

1. **易用性**: 5 分钟构建第一个多 Agent 应用
2. **向后兼容**: 类似 0.2 的使用体验
3. **渐进式**: 可以深入使用 Core API

### 核心组件

#### 1. Agent 类型

**AssistantAgent**:
```python
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

agent = AssistantAgent(
    name="assistant",
    model_client=OpenAIChatCompletionClient(model="gpt-4o")
)

response = await agent.run(task="Write a hello world program")
```

**CodingAgent**:
```python
from autogen_agentchat.agents import CodingAgent

coding_agent = CodingAgent(
    name="coder",
    model_client=OpenAIChatCompletionClient(model="gpt-4o")
)
```

**UserProxyAgent**:
```python
from autogen_agentchat.agents import UserProxyAgent

user_proxy = UserProxyAgent(name="user")
```

#### 2. Team 协作

**RoundRobinGroupChat**:
```python
from autogen_agentchat.teams import RoundRobinGroupChat

team = RoundRobinGroupChat(
    participants=[agent1, agent2, agent3],
    max_turns=10
)

result = await team.run(task="Solve this problem")
```

**SelectorGroupChat**:
```python
from autogen_agentchat.teams import SelectorGroupChat

team = SelectorGroupChat(
    participants=[agent1, agent2, agent3],
    model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    selector_prompt="Choose the best agent for the task"
)
```

#### 3. 工具调用

```python
from autogen_agentchat.agents import AssistantAgent

# 定义工具
async def get_weather(location: str) -> str:
    return f"Weather in {location}: Sunny"

# 创建带工具的 Agent
agent = AssistantAgent(
    name="weather_bot",
    model_client=OpenAIChatCompletionClient(model="gpt-4o"),
    tools=[get_weather]
)
```

### AgentChat 适用场景

✅ **适合**:
- 快速原型开发
- 对话式应用
- 常见的多 Agent 模式
- 从 0.2 迁移

❌ **不适合**:
- 需要自定义消息协议
- 复杂的事件驱动流程
- 分布式部署

---

## Extensions 生态

### 架构设计

Extensions 是**插件化架构**，每个 Extension 实现特定接口：

```
Core API 接口
    ↑
    | 实现
    |
Extensions
    ├── Models (LLM 接口)
    ├── Code Executors (代码执行)
    ├── Tools (工具)
    ├── Storage (存储)
    └── Protocols (协议)
```

### 核心 Extensions

#### 1. Models (LLM 集成)

**OpenAI**:
```python
from autogen_ext.models.openai import OpenAIChatCompletionClient

client = OpenAIChatCompletionClient(model="gpt-4o")
```

**Azure OpenAI**:
```python
from autogen_ext.models.azure import AzureOpenAIChatCompletionClient

client = AzureOpenAIChatCompletionClient(
    endpoint="...",
    api_key="...",
    deployment_name="gpt-4"
)
```

**Anthropic**:
```python
from autogen_ext.models.anthropic import AnthropicChatCompletionClient

client = AnthropicChatCompletionClient(model="claude-3-opus-20240229")
```

#### 2. Code Executors (代码执行)

**命令行执行器**:
```python
from autogen_ext.code_executors import CommandLineCodeExecutor

executor = CommandLineCodeExecutor()
```

**Docker 执行器**:
```python
from autogen_ext.code_executors import DockerCommandLineCodeExecutor

executor = DockerCommandLineCodeExecutor()
```

#### 3. MCP (Model Context Protocol)

```python
from autogen_ext.tools import McpWorkbench

workbench = McpWorkbench()
# 连接 MCP 服务器，使用外部工具
```

### 社区 Extensions

AutoGen 支持**第三方 Extensions**：

```python
# 社区扩展示例
pip install autogen-langchain  # 假设的社区扩展
```

---

## 设计理念

### 1. 分层抽象

- **Core**: 底层控制，最大灵活性
- **AgentChat**: 高层抽象，快速开发
- **用户选择**: 根据需求选择合适的层次

### 2. 可组合性

所有组件都是可组合的：

```python
# 组合不同的模型、工具、Agent
agent = AssistantAgent(
    model_client=AzureOpenAIChatCompletionClient(...),
    tools=[custom_tool_1, custom_tool_2],
    memory=custom_memory
)
```

### 3. 类型安全

完整的类型支持：

```python
from typing import TypedDict
from autogen_core import Message

class UserMessage(TypedDict):
    content: str
    user_id: str

# 类型检查
async def handle(message: UserMessage) -> None:
    ...
```

### 4. 可观测性

内置 OpenTelemetry 支持：

```python
from autogen_core import enable_telemetry

enable_telemetry()
# 自动追踪所有 Agent 交互
```

---

## 与其他框架对比

### vs LangChain

| 特性 | AutoGen | LangChain |
|------|---------|-----------|
| **焦点** | 多 Agent 协作 | LLM 应用开发 |
| **Agent 通信** | 发布-订阅 | 链式调用 |
| **工具** | 内置丰富 | 生态系统庞大 |
| **学习曲线** | 较陡 | 较平缓 |

**选择 AutoGen**: 复杂的多 Agent 协作
**选择 LangChain**: 单 Agent + 工具调用

### vs CrewAI

| 特性 | AutoGen | CrewAI |
|------|---------|--------|
| **架构** | 事件驱动 | 角色基 |
| **灵活性** | 高 | 中 |
| **易用性** | 中 | 高 |

**选择 AutoGen**: 需要自定义控制
**选择 CrewAI**: 快速团队协作

### vs Semantic Kernel

| 特性 | AutoGen | Semantic Kernel |
|------|---------|-----------------|
| **语言** | Python, .NET | 多语言 |
| **企业级** | 是 | 是 (微软) |
| **Agent** | 多 Agent | 单/多 |

**选择 AutoGen**: 纯 Python 开发
**选择 Semantic Kernel**: 跨语言需求

---

## 总结

### 关键要点

1. **分层架构**: Core (底层) + AgentChat (高层)
2. **事件驱动**: 基于 Topic/Subscription 的消息传递
3. **可扩展**: Extensions 插件化生态
4. **类型安全**: 完整的类型提示支持
5. **分布式**: 原生支持跨进程部署

### 选择指南

- **学习 Core API**: 深入理解框架，构建自定义系统
- **使用 AgentChat**: 快速开发，从 0.2 迁移
- **结合使用**: AgentChat 构建 + Core 扩展

### 下一步

- [学习路径建议](./02-learning-path.md)
- [Core API 示例](../01-core/concepts/demo_01_quickstart.py)
- [AgentChat 示例](../02-agentchat/basics/demo_19_assistant_agent.py)

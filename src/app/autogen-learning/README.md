# AutoGen 0.4+ 学习项目

> 系统性学习 AutoGen 0.4+ 框架的示例代码和实践指南

## 项目简介

本项目基于 AutoGen 官方分层架构设计，提供系统性的学习路径，帮助开发者从零开始掌握 AutoGen 0.4+ 框架。

## 官方架构

```
┌─────────────────────────────────────────────────────┐
│                   Applications                      │
│            (Magentic-One, 自定义应用)               │
├─────────────────────────────────────────────────────┤
│              AgentChat API (高层)                   │
│     构建对话式多 Agent 应用 (替代 v0.2)             │
├─────────────────────────────────────────────────────┤
│               Core API (底层)                       │
│       事件驱动的 Actor 框架、发布-订阅             │
├─────────────────────────────────────────────────────┤
│              Extensions (扩展)                      │
│   LLM、代码执行、MCP、向量数据库、工具等           │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```
autogen-learning/
├── README.md                    # 本文件
├── requirements.txt             # 项目依赖
├── pyproject.toml              # 项目配置
├── .env.example                # 环境变量示例
│
├── docs/                       # 详细文档
│   ├── 00-project-setup.md    # 环境配置指南
│   ├── 01-architecture-overview.md   # 架构总览
│   └── 02-learning-path.md    # 学习路径
│
├── 01-core/                    # Core API - 事件驱动基础
│   ├── concepts/               # 核心概念
│   ├── agents/                 # Agent 类型
│   ├── runtime/                # 运行时管理
│   ├── messaging/              # 消息传递模式
│   └── advanced/               # 高级特性
│
├── 02-agentchat/              # AgentChat API - 高层应用
│   ├── basics/                 # 基础 Agent
│   ├── conversations/          # 对话管理
│   ├── teams/                  # 团队协作
│   ├── tools/                  # 工具调用
│   └── advanced/               # 高级主题
│
├── 03-extensions/             # Extensions - 生态扩展
│   ├── models/                 # 模型集成
│   ├── code-executors/         # 代码执行器
│   ├── tools/                  # 工具生态
│   ├── mcp/                    # Model Context Protocol
│   └── storage/                # 存储集成
│
├── 04-integration/            # 综合集成案例
│   ├── simple-cases/           # 简单案例
│   ├── multi-agent-systems/    # 多 Agent 系统
│   └── advanced-systems/       # 高级系统
│
├── 05-studio/                 # AutoGen Studio
│
├── common/                    # 公共模块
│   ├── config/                 # 配置管理
│   ├── utils/                  # 工具函数
│   └── types/                  # 类型定义
│
├── tests/                     # 测试目录
└── examples/                  # 额外示例
```

## 快速开始

### 1. 环境要求

- Python 3.10 或更高版本

### 2. 创建虚拟环境

```bash
# 进入项目目录
cd src/app/autogen-learning

# 创建虚拟环境
python -m venv .venv

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
.venv\Scripts\activate     # Windows
```

### 3. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 或安装完整依赖（包括可选扩展）
pip install -r requirements-full.txt
```

### 4. 配置环境变量

```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，填入你的 API keys
# 至少需要配置 OPENAI_API_KEY
```

### 5. 运行第一个示例

```bash
# 运行 Core API 快速开始示例
python 01-core/concepts/demo_01_quickstart.py
```

## 学习路径

### 阶段 1: Core API 基础 (2-3 周)

学习事件驱动架构和发布-订阅模式

```bash
# 按顺序运行示例
python 01-core/concepts/demo_01_quickstart.py
python 01-core/concepts/demo_02_topic_subscription.py
python 01-core/concepts/demo_03_agent_lifecycle.py
# ... 更多示例
```

### 阶段 2: AgentChat API (2-3 周)

掌握高层 API 快速构建应用

```bash
python 02-agentchat/basics/demo_19_assistant_agent.py
python 02-agentchat/conversations/demo_23_simple_conversation.py
# ... 更多示例
```

### 阶段 3: Extensions 生态 (3-4 周)

掌握各种扩展和集成

### 阶段 4: 综合案例 (持续)

构建完整的多 Agent 系统

## 运行测试

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_core/

# 运行并显示覆盖率
pytest --cov=01-core --cov-report=html
```

## 核心概念

### 1. Topic 和 Subscription

AutoGen Core 使用发布-订阅模式实现 Agent 间通信：

```python
from autogen_core import TopicId, TypeSubscription

# Topic = (type, source)
topic = TopicId(type="order_created", source="client_a")

# 订阅：将 topic 映射到 agent
subscription = TypeSubscription(
    topic_type="order_created",
    agent_type="notification_agent"
)
```

### 2. Agent 类型

- **RoutedAgent**: 支持发布-订阅的 Agent 基类
- **直接消息**: 一对一的消息传递
- **广播消息**: 一对多的消息传递

### 3. 运行时

- **SingleThreadedAgentRuntime**: 单线程运行时
- **GrpcWorkerAgentRuntime**: 分布式运行时

## 依赖说明

### 核心依赖

```txt
autogen-core>=0.4.0          # Core API
autogen-agentchat>=0.4.0     # AgentChat API
autogen-ext[openai]>=0.4.0   # OpenAI 扩展
```

### 可选依赖

```txt
autogen-ext[azure]           # Azure OpenAI
autogen-ext[docker]          # Docker 代码执行
autogen-ext[mcp]             # Model Context Protocol
```

## 官方资源

- [AutoGen 官方文档](https://microsoft.github.io/autogen/stable/)
- [Core User Guide](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/index.html)
- [AgentChat User Guide](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html)
- [GitHub Repository](https://github.com/microsoft/autogen)

## 版本

- **v2.0.0** (2025-01-07): 基于官方架构重新设计

## 许可证

本项目仅用于学习目的。

## 贡献

欢迎提交 Issue 和 Pull Request！

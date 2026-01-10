# AgentChat API - 高层抽象

本目录包含 AutoGen AgentChat API 的演示代码，AgentChat 是高层 API，用于快速构建对话式多 Agent 应用。

## 目录

- [basics/](./basics/) - 基础 Agent
- [conversations/](./conversations/) - 对话管理
- [teams/](./teams/) - 团队协作
- [tools/](./tools/) - 工具调用
- [advanced/](./advanced/) - 高级主题

## 学习目标

通过这些示例，你将学会：

1. ✅ 使用 AssistantAgent 快速创建助手
2. ✅ 使用 CodingAgent 进行代码生成
3. ✅ 管理对话流程和上下文
4. ✅ 构建多 Agent 团队
5. ✅ 集成工具到 Agent
6. ✅ 实现人在回路
7. ✅ 处理复杂的多 Agent 协作

## 核心概念

### Agent 类型

**AssistantAgent**:
- 通用的助手 Agent
- 使用 LLM 生成响应
- 适合问答和对话

**CodingAgent**:
- 专门的代码生成 Agent
- 支持代码执行
- 适合编程任务

**UserProxyAgent**:
- 用户代理 Agent
- 人在回路交互
- 人工干预和决策

### Team 模式

**RoundRobinGroupChat**:
- Agent 轮流发言
- 顺序对话
- 适合结构化讨论

**SelectorGroupChat**:
- 智能选择发言者
- 基于 LLM 决策
- 适合动态协作

## 快速开始

### 基础示例

```bash
# Assistant Agent
python 02-agentchat/basics/demo_19_assistant_agent.py

# Coding Agent
python 02-agentchat/basics/demo_20_coding_agent.py
```

### 对话示例

```bash
# 简单对话
python 02-agentchat/conversations/demo_23_simple_conversation.py

# 顺序对话
python 02-agentchat/conversations/demo_24_sequential.py
```

### 团队示例

```bash
# RoundRobin 模式
python 02-agentchat/teams/demo_26_roundrobin_chat.py

# Selector 模式
python 02-agentchat/teams/demo_27_selector_chat.py
```

## 与 Core API 的区别

| 特性 | Core API | AgentChat API |
|------|----------|---------------|
| 抽象层次 | 底层 API | 高层 API |
| 使用场景 | 精细控制、自定义协议 | 快速开发、对话应用 |
| 通信方式 | Topic/Subscription | 直接消息传递 |
| 学习曲线 | 较陡 | 平缓 |
| 灵活性 | 高 | 中等 |

## 何时使用 AgentChat

✅ **适合**:
- 对话式应用
- 快速原型开发
- 简单的多 Agent 协作
- 不需要细粒度控制

❌ **不适合**:
- 自定义通信协议
- 需要精细控制消息流
- 分布式部署
- 复杂的事件驱动架构

## 学习路径

1. **开始**: [basics/](./basics/)
   - 学习基础 Agent 类型
   - 理解 Agent 配置

2. **进阶**: [conversations/](./conversations/)
   - 管理对话流程
   - 实现终止条件

3. **深入**: [teams/](./teams/)
   - 构建多 Agent 团队
   - 实现协作模式

4. **高级**: [tools/](./tools/) 和 [advanced/](./advanced/)
   - 集成工具
   - 人在回路
   - 记忆管理

## 相关文档

- [官方文档 - AgentChat](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/index.html)
- [前序: Core API](../01-core/)
- [后续: Extensions](../03-extensions/)

继续学习：[basics/](./basics/) →
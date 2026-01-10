# Core API - Agents (智能体)

本目录包含 AutoGen Core API Agent 相关的演示代码。

## 目录

- [demo_06_routed_agent.py](./demo_06_routed_agent.py) - RoutedAgent 深入
- [demo_07_default_subscription.py](./demo_07_default_subscription.py) - 默认订阅
- [demo_08_agent_state.py](./demo_08_agent_state.py) - Agent 状态管理

## 学习目标

通过这些示例，你将学会：

1. ✅ 深入理解 RoutedAgent 的使用
2. ✅ 掌握多个 @message_handler 的处理
3. ✅ 使用 DefaultSubscription 简化配置
4. ✅ 实现 Agent 状态管理
5. ✅ 理解 Agent 生命周期和状态持久化

## 核心概念

### RoutedAgent

`RoutedAgent` 是 AutoGen Core 的核心 Agent 基类：

```python
from autogen_core import RoutedAgent, message_handler

class MyAgent(RoutedAgent):
    @message_handler
    async def handle_message_type1(self, message: MessageType1, ctx) -> None:
        # 处理 MessageType1
        pass
    
    @message_handler
    async def handle_message_type2(self, message: MessageType2, ctx) -> None:
        # 处理 MessageType2
        pass
```

**特点**：
- 支持多个消息处理器
- 自动根据消息类型路由
- 每个处理器独立处理
- 异步执行

### Subscription 类型

**TypeSubscription**:
```python
await runtime.add_subscription(
    TypeSubscription(topic_type="my_topic", agent_type="my_agent")
)
```
- 订阅特定 topic type
- 自动映射 source 到 agent key

**DefaultSubscription**:
```python
await runtime.add_subscription(
    DefaultSubscription(agent_type="my_agent")
)
```
- 订阅默认 topic ("default", "default")
- 简化常用场景配置

### Agent 状态

Agent 可以维护内部状态：

```python
class StatefulAgent(RoutedAgent):
    def __init__(self):
        super().__init__()
        self.state = {
            "messages_processed": 0,
            "last_activity": None
        }
    
    @message_handler
    async def handle_message(self, message: str, ctx) -> None:
        self.state["messages_processed"] += 1
        # 处理消息
```

**状态管理原则**：
- 单线程保证状态一致性
- 避免共享状态（除非必要）
- 考虑状态持久化需求
- 使用数据类简化状态定义

## 快速开始

### 运行示例

```bash
# RoutedAgent 深入
python 01-core/agents/demo_06_routed_agent.py

# 默认订阅
python 01-core/agents/demo_07_default_subscription.py

# Agent 状态管理
python 01-core/agents/demo_08_agent_state.py
```

## 学习路径

1. **开始**: [demo_06_routed_agent.py](./demo_06_routed_agent.py)
   - 学习如何创建多处理器 Agent
   - 理解消息类型匹配

2. **进阶**: [demo_07_default_subscription.py](./demo_07_default_subscription.py)
   - 掌握默认订阅机制
   - 对比不同订阅类型

3. **深入**: [demo_08_agent_state.py](./demo_08_agent_state.py)
   - 实现有状态的 Agent
   - 学习状态持久化

## 相关文档

- [官方文档 - Agents](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/agents.html)
- [前序: Concepts](../concepts/)
- [后序: Runtime](../runtime/)

继续学习：[demo_06_routed_agent.py](./demo_06_routed_agent.py) →
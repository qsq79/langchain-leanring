# Core API - 核心概念

本目录包含 AutoGen Core API 的基础概念演示代码。

## 目录

- [demo_01_quickstart.py](./demo_01_quickstart.py) - 快速开始
- [demo_02_topic_subscription.py](./demo_02_topic_subscription.py) - Topic 和 Subscription
- [demo_03_agent_lifecycle.py](./demo_03_agent_lifecycle.py) - Agent 生命周期
- [demo_04_message_types.py](./demo_04_message_types.py) - 消息类型定义
- [demo_05_message_context.py](./demo_05_message_context.py) - 消息上下文

## 学习目标

通过这些示例，你将学会：

1. ✅ 创建和配置 RoutedAgent
2. ✅ 理解 Topic 和 Subscription 机制
3. ✅ 掌握消息传递流程
4. ✅ 理解 Agent 生命周期管理
5. ✅ 使用 MessageContext 获取上下文信息

## 快速开始

### 运行第一个示例

```bash
# 确保在项目根目录
cd src/app/autogen-learning

# 运行快速开始示例
python 01-core/concepts/demo_01_quickstart.py
```

### 预期输出

```
╔════════════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ Core API - 快速开始演示                  ║
║           Event-Driven Agent Communication                     ║
║                                                                ║
╚════════════════════════════════════════════════════════════════╝

================================================================================
演示 1: 创建简单的 Echo Agent
================================================================================

💬 [System] ✓ Runtime 创建成功
💬 [System] ✓ EchoAgent 注册成功
💬 [System] ✓ 订阅添加成功
💬 [System] ✓ Runtime 已启动

--- 发送消息 ---

💬 [echo_agent] 收到消息 (第 1 条): Hello, AutoGen!
💬 [echo_agent] Echo: Hello, AutoGen!
💬 [echo_agent] 收到消息 (第 2 条): 这是一个测试消息
💬 [echo_agent] Echo: 这是一个测试消息
💬 [System] ✓ 所有消息已处理
💬 [System] ✓ Runtime 已停止
```

## 核心概念

### 1. RoutedAgent

`RoutedAgent` 是支持发布-订阅模式的 Agent 基类：

```python
from autogen_core import RoutedAgent, message_handler

class MyAgent(RoutedAgent):
    @message_handler
    async def handle_message(self, message: MyMessageType, ctx) -> None:
        # 处理消息
        pass
```

**关键特性**：
- 使用 `@message_handler` 装饰器定义消息处理方法
- 自动路由匹配类型的消息到对应处理方法
- 支持异步消息处理

### 2. Runtime

`SingleThreadedAgentRuntime` 是 AutoGen 的核心运行时：

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

# 停止
runtime.stop()
```

**Runtime 生命周期**：
1. 创建 Runtime 实例
2. 注册 Agent 类型
3. 添加订阅关系
4. 启动 Runtime (`start()`)
5. 发布消息
6. 等待空闲 (`stop_when_idle()`)
7. 停止 Runtime (`stop()`)

### 3. Topic 和 Subscription

**Topic** 定义消息的范围：

```python
from autogen_core import TopicId

# Topic = (type, source)
topic = TopicId(type="user_messages", source="default")
# Topic ID: "user_messages/default"
```

**Subscription** 将 Topic 映射到 Agent：

```python
from autogen_core import TypeSubscription

# 订阅：所有 "user_messages" 类型的消息由 echo_agent 处理
subscription = TypeSubscription(
    topic_type="user_messages",
    agent_type="echo_agent"
)

await runtime.add_subscription(subscription)
```

**消息路由规则**：
- 发布到 `("user_messages", "default")`
- 路由到 `("echo_agent", "default")`
- Runtime 自动创建或复用 Agent 实例

### 4. 消息类型

消息是普通的 Python 类：

```python
class UserMessage:
    def __init__(self, content: str, user_name: str = "User"):
        self.content = content
        self.user_name = user_name

    def __str__(self):
        return f"{self.user_name}: {self.content}"
```

**消息类型要求**：
- 可以是任何 Python 类
- 通常使用 dataclass 或普通类
- `@message_handler` 根据类型匹配

### 5. 消息发布

发布消息到 Topic：

```python
await runtime.publish_message(
    UserMessage("Hello, AutoGen!"),
    TopicId("user_messages", "default")
)
```

**发布流程**：
1. 创建消息实例
2. 指定目标 Topic
3. Runtime 查找订阅该 Topic 的 Agent
4. 将消息传递给所有匹配的 Agent
5. Agent 的 `@message_handler` 处理消息

## 进阶学习

### 下一步

1. **Topic 和 Subscription 深入**: [demo_02_topic_subscription.py](./demo_02_topic_subscription.py)
   - TypeSubscription vs DefaultSubscription
   - 多租户架构
   - Topic Source 的使用

2. **Agent 生命周期**: [demo_03_agent_lifecycle.py](./demo_03_agent_lifecycle.py)
   - Agent 初始化
   - Agent 状态管理
   - Agent 清理

3. **消息类型系统**: [demo_04_message_types.py](./demo_04_message_types.py)
   - 类型化消息
   - 消息验证
   - 消息序列化

### 修改示例

尝试修改示例代码：

**练习 1**: 添加新的消息类型

```python
class ImageMessage:
    def __init__(self, url: str, caption: str = ""):
        self.url = url
        self.caption = caption

# 在 EchoAgent 中添加处理方法
@message_handler
async def handle_image(self, message: ImageMessage, ctx) -> None:
    print(f"收到图片: {message.url}")
```

**练习 2**: 创建新的 Agent

```python
class ReverseAgent(RoutedAgent):
    """反转消息内容的 Agent"""

    @message_handler
    async def handle_user_message(self, message: UserMessage, ctx) -> None:
        reversed_content = message.content[::-1]
        print(f"反转: {reversed_content}")
```

**练习 3**: 多 Topic 订阅

```python
# 让一个 Agent 订阅多个 Topic
await runtime.add_subscription(TypeSubscription("messages", "agent"))
await runtime.add_subscription(TypeSubscription("notifications", "agent"))
await runtime.add_subscription(TypeSubscription("alerts", "agent"))
```

## 常见问题

### Q: 为什么消息没有被处理？

**A**: 检查以下几点：
1. Runtime 是否已启动 (`runtime.start()`)
2. Agent 是否已注册
3. Subscription 是否已添加
4. Topic ID 是否匹配

### Q: 如何调试消息流？

**A**: 在 message_handler 中添加日志：

```python
@message_handler
async def handle_message(self, message, ctx) -> None:
    print(f"DEBUG: 收到消息: {message}")
    print(f"DEBUG: 来自 topic: {ctx.topic_id}")
    print(f"DEBUG: 发送者: {ctx.sender_id}")
```

### Q: Agent 可以发送消息给自己吗？

**A**: 可以，通过发布到同一个 Topic：

```python
await self.publish_message(
    NewMessage(...),
    ctx.topic_id  # 发布到同一个 topic
)
```

## 相关文档

- [官方 Quick Start](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/quickstart.html)
- [Topic 和 Subscription](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/topic-and-subscription.html)
- [Agent 类型](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/agents.html)
- [消息传递](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/message-passing.html)

## 进阶主题

- 分布式 Runtime (GrpcWorkerAgentRuntime)
- 直接消息传递
- RPC 模式
- 错误处理和重试
- 性能优化

继续学习：[demo_02_topic_subscription.py](./demo_02_topic_subscription.py) →

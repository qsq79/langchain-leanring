# AutoGen 发布-订阅模式学习示例

本目录包含 AutoGen 0.4+ 发布-订阅模式的学习示例代码，演示如何使用事件驱动架构实现 Agent 之间的通信。

## 📚 目录

- [概述](#概述)
- [核心概念](#核心概念)
- [演示场景](#演示场景)
- [运行示例](#运行示例)
- [代码结构](#代码结构)
- [与现有实现的对比](#与现有实现的对比)
- [学习资源](#学习资源)

---

## 概述

### 什么是发布-订阅模式？

发布-订阅模式（Publish-Subscribe Pattern）是一种消息传递模式，其中：
- **发布者（Publisher）**：发送消息的 Agent，不需要知道谁会接收消息
- **订阅者（Subscriber）**：接收消息的 Agent，订阅感兴趣的主题
- **主题（Topic）**：消息的类别，定义消息的范围

### AutoGen 0.4+ 的事件驱动架构

AutoGen 0.4 是一个全新的重新设计版本，引入了基于事件的异步编程模型：

- **Topic（主题）**：由 `Topic Type` 和 `Topic Source` 组成
- **Subscription（订阅）**：将 Topic 映射到 Agent ID
- **Broadcast（广播）**：一对多的消息传递方式
- **Direct Messaging（直接消息）**：一对一的消息传递方式

---

## 核心概念

### 1. Topic（主题）

Topic 定义广播消息的范围，包含两个部分：

```python
Topic = (Topic Type, Topic Source)
```

- **Topic Type（主题类型）**：通常由应用代码定义，标记消息的类型
  - 例如：`"order_created"`, `"logistics_update"`, `"payment_received"`

- **Topic Source（主题源）**：在主题类型内唯一标识一个主题
  - 例如：`"client_a"`, `"session_123"`, `"github.com/repo/issues/1"`

**Topic ID 字符串格式**：`topic_type/topic_source`

**示例**：
```python
# 创建 Topic
from autogen_core import TopicId

# 订单创建事件（单租户）
topic1 = TopicId(type="order_created", source="default")
# Topic ID: "order_created/default"

# 物流更新事件（多租户 - 客户隔离）
topic2 = TopicId(type="logistics_update", source="client_a")
# Topic ID: "logistics_update/client_a"
```

### 2. Subscription（订阅）

订阅将 Topic 映射到 Agent ID。AutoGen 支持两种类型的订阅：

#### 2.1 Type-Based Subscription（基于类型的订阅）

**推荐使用**，是数据无关的、可移植的订阅方式。

```python
from autogen_core import TypeSubscription

# 订阅：所有 order_created 类型的消息都由 order_agent 处理
subscription = TypeSubscription(
    topic_type="order_created",
    agent_type="order_agent"
)
```

**工作原理**：
- 任何匹配 `topic_type` 的 Topic 都会映射到该 Agent
- Agent 的 key 会被设置为 `topic_source` 的值
- 运行时会自动创建或复用 Agent 实例

**示例**：
```python
# 发布消息到 topic: ("order_created", "session_123")
# 运行时将消息路由到 agent: ("order_agent", "session_123")

# 发布消息到 topic: ("order_created", "session_456")
# 运行时将消息路由到 agent: ("order_agent", "session_456")
```

#### 2.2 Default Subscription（默认订阅）

使用默认的主题类型和源。

```python
from autogen_core._default_subscription import DefaultSubscription

# 所有发布到默认主题的消息都会被接收
subscription = DefaultSubscription(agent_type="notification_agent")
```

### 3. RoutedAgent（路由 Agent）

`RoutedAgent` 是支持发布-订阅模式的 Agent 基类。

```python
from autogen_core import RoutedAgent, message_handler, MessageContext

class MyAgent(RoutedAgent):
    def __init__(self, description: str) -> None:
        super().__init__(description)

    @message_handler
    async def handle_message(self, message: MyMessageType, ctx: MessageContext) -> None:
        # 处理消息
        print(f"收到消息: {message}")

        # 可以发布响应到同一个 Topic
        if ctx.topic_id:
            await self.publish_message(
                message=ResponseMessage("OK"),
                topic_id=ctx.topic_id
            )
```

**关键特性**：
- 使用 `@message_handler` 装饰器定义消息处理方法
- 通过 `MessageContext` 获取 Topic 信息
- 可以发布响应消息到相同的 Topic

### 4. Runtime（运行时）

`SingleThreadedAgentRuntime` 是 AutoGen 的核心运行时。

```python
from autogen_core import SingleThreadedAgentRuntime

# 创建运行时
runtime = SingleThreadedAgentRuntime()

# 注册 Agent 类型
await MyAgent.register(
    runtime=runtime,
    type="my_agent",
    factory=lambda: MyAgent("My Agent Description")
)

# 添加订阅
await runtime.add_subscription(
    TypeSubscription(topic_type="my_topic", agent_type="my_agent")
)

# 启动运行时
runtime.start()

# 发布消息
await runtime.publish_message(
    MyMessage(content="Hello"),
    topic_id=TopicId(type="my_topic", source="default")
)

# 等待消息处理完成
await runtime.stop_when_idle()
```

---

## 演示场景

### 场景 1：单租户，多主题

**文件**：`pubsub_demo.py` - `demo_single_tenant_multiple_topics()`

**描述**：
- 单个租户（一个客户或应用）
- 使用多个不同的主题类型来区分不同的事件
- 不同的 Agent 订阅不同的主题

**适用场景**：
- 单用户应用
- 命令行工具
- 需要将不同类型的消息路由到专门的 Agent

**示例**：
```python
# 通知 Agent 订阅所有事件
await runtime.add_subscription(
    TypeSubscription(topic_type="order_created", agent_type="notification_agent")
)
await runtime.add_subscription(
    TypeSubscription(topic_type="order_shipped", agent_type="notification_agent")
)

# 库存 Agent 只订阅订单创建事件
await runtime.add_subscription(
    TypeSubscription(topic_type="order_created", agent_type="inventory_agent")
)
```

**执行流程**：
```
发布订单创建事件 → order_created/default
    ↓
    ├─→ NotificationAgent (发送通知)
    └─→ InventoryAgent (更新库存)

发布订单发货事件 → order_shipped/default
    ↓
    └─→ NotificationAgent (发送发货通知)
```

### 场景 2：多租户

**文件**：`pubsub_demo.py` - `demo_multi_tenant()`

**描述**：
- 多个租户（多个客户或用户会话）
- 每个租户有独立的事件流
- 使用 `topic_source` 来隔离不同租户的事件

**适用场景**：
- 多用户 SaaS 应用
- 客户数据隔离
- 并发处理多个会话

**示例**：
```python
# 租户 A 发布消息
await runtime.publish_message(
    OrderCreatedEvent(...),
    topic_id=TopicId(type="order_created", source="client_a")
)
# 路由到: notification_agent/client_a

# 租户 B 发布消息
await runtime.publish_message(
    OrderCreatedEvent(...),
    topic_id=TopicId(type="order_created", source="client_b")
)
# 路由到: notification_agent/client_b
```

**执行流程**：
```
租户 A (client_a):
    发布订单创建事件 → order_created/client_a
        ↓
        └─→ NotificationAgent (client_a 实例)

租户 B (client_b):
    发布订单创建事件 → order_created/client_b
        ↓
        └─→ NotificationAgent (client_b 实例)  # 不同的实例，数据隔离
```

---

## 运行示例

### 前置要求

确保已安装 AutoGen 0.4+：

```bash
pip install autogen-core>=0.4.0
```

### 运行演示

```bash
# 进入项目目录
cd /Users/quan/langchain-leanring/src/app/multi-agent-customer-system

# 运行发布-订阅演示
python app/autogen/pubsub_demo.py
```

### 预期输出

```
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║          AutoGen 0.4+ 发布-订阅模式演示                                       ║
║     Event-Driven Agent Communication with Publish-Subscribe                   ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝

================================================================================
场景 1: 单租户，多主题 - 事件驱动 Agent 通信
================================================================================

--------------------------------------------------------------------------------
发布事件 1: 订单创建
--------------------------------------------------------------------------------

📧 [notification_agent:default] 收到订单创建事件
   订单号: ORD20250106001
   客户: 张三
   金额: ¥2999.0
   商品: iPhone 15 Pro, 手机壳, 贴膜
   ✅ 已发送订单创建通知

📊 [inventory_agent:default] 收到订单创建事件，更新库存
   订单号: ORD20250106001
   🔻 扣减库存: iPhone 15 Pro
   🔻 扣减库存: 手机壳
   🔻 扣减库存: 贴膜
   ✅ 库存更新完成

📈 [analytics_agent:default] 分析订单创建事件
   订单号: ORD20250106001
   分析: 高价值订单
```

---

## 代码结构

```
app/autogen/
├── pubsub_demo.py          # 发布-订阅模式演示代码
└── README.md               # 本文档
```

### pubsub_demo.py 文件结构

```python
# 1. 定义事件类型（Event Types）
class EventType(str, Enum):
    ORDER_CREATED = "order_created"
    ORDER_SHIPPED = "order_shipped"
    LOGISTICS_UPDATE = "logistics_update"

# 2. 定义消息类型（Message Types）
@dataclass
class OrderCreatedEvent:
    order_id: str
    customer_name: str
    amount: float
    items: List[str]

# 3. 定义 Agent 类（订阅者）
class NotificationAgent(RoutedAgent):
    @message_handler
    async def on_order_created(self, message: OrderCreatedEvent, ctx: MessageContext):
        # 处理订单创建事件
        pass

# 4. 演示场景
async def demo_single_tenant_multiple_topics():
    # 场景 1: 单租户，多主题
    pass

async def demo_multi_tenant():
    # 场景 2: 多租户
    pass

# 5. 主函数
async def main():
    await demo_single_tenant_multiple_topics()
    await demo_multi_tenant()
```

---

## 与现有实现的对比

### 当前实现（直接函数调用）

**文件**：`agents/agent_manager.py`

```python
class AgentManager:
    async def process_query(self, user_query: str, order_id: str):
        # 1. 意图识别
        recommended_agents = await hybrid_intent_parser.parse(user_query)

        # 2. 直接调用 Agent 函数
        tasks = []
        for agent_name in recommended_agents:
            if agent_name == 'order_agent':
                tasks.append(self.order_agent.process_request(query_request))
            elif agent_name == 'logistics_agent':
                tasks.append(self.logistics_agent.process_request(query_request))

        # 3. 并行执行
        results = await asyncio.gather(*tasks)

        # 4. 汇总结果
        summary = await self.summary_agent.summarize_results(...)
```

**特点**：
- ✅ 简单直接，易于理解
- ✅ 适合小规模、固定流程的场景
- ❌ 紧耦合：AgentManager 必须知道所有 Agent 的接口
- ❌ 难以扩展：添加新 Agent 需要修改 AgentManager
- ❌ 缺乏灵活性：无法动态路由

### 发布-订阅模式（事件驱动）

**文件**：`app/autogen/pubsub_demo.py`

```python
runtime = SingleThreadedAgentRuntime()

# 订阅：声明式配置
await runtime.add_subscription(
    TypeSubscription(topic_type="order_created", agent_type="notification_agent")
)

# 发布：松耦合
await runtime.publish_message(
    OrderCreatedEvent(...),
    topic_id=TopicId(type="order_created", source="client_a")
)

# 运行时自动路由到正确的 Agent
```

**特点**：
- ✅ 松耦合：发布者不需要知道谁会接收消息
- ✅ 易扩展：添加新 Agent 只需注册和订阅
- ✅ 动态路由：运行时自动创建 Agent 实例
- ✅ 天然支持多租户：使用 topic source 隔离
- ❌ 复杂度较高：需要理解 Topic 和 Subscription 概念
- ❌ 调试相对困难：消息流不是显式的

### 何时使用哪种模式？

#### 使用直接函数调用（当前实现）：
- 简单的、固定的业务流程
- Agent 数量少且固定
- 不需要动态路由或多租户隔离
- 快速原型开发

#### 使用发布-订阅模式：
- 复杂的事件驱动工作流
- 需要动态添加或移除 Agent
- 多租户、多会话场景
- 需要 Agent 之间松耦合
- 大规模、可扩展的分布式系统

---

## 学习资源

### 官方文档

1. **Topic and Subscription - AutoGen**
   - URL: https://microsoft.github.io/autogen/0.4.6//user-guide/core-user-guide/core-concepts/topic-and-subscription.html
   - 描述：AutoGen 0.4 的核心概念详解

2. **Topic and Subscription Example Scenarios**
   - URL: https://microsoft.github.io/autogen/stable//user-guide/core-user-guide/cookbook/topic-subscription-scenarios.html
   - 描述：包含 4 个详细的发布-订阅场景示例

3. **AutoGen 0.4 Launch Announcement**
   - URL: https://devblogs.microsoft.com/autogen/autogen-reimagined-launching-autogen-0-4/
   - 描述：AutoGen 0.4 官方发布博客（2025年1月17日）

4. **从 v0.2 迁移到 v0.4 的指南**
   - URL: https://microsoft.github.io/autogen/stable//user-guide/agentchat-user-guide/migration-guide.html
   - 描述：帮助从旧版本迁移到新版本

### 相关概念

- **Event-Driven Architecture（事件驱动架构）**
- **Publish-Subscribe Pattern（发布-订阅模式）**
- **Actor Model（Actor 模型）**
- **Message Queue（消息队列）**

---

## 总结

本演示展示了 AutoGen 0.4+ 的发布-订阅模式的核心概念：

1. **Topic（主题）**：定义消息的范围
2. **Subscription（订阅）**：将 Topic 映射到 Agent
3. **Type-Based Subscription（基于类型的订阅）**：推荐使用，数据无关
4. **多租户支持**：通过 topic source 实现

**关键要点**：
- 发布-订阅模式实现了 Agent 之间的松耦合
- 适合事件驱动和动态工作流
- AutoGen 0.4 是一个全新的重新设计版本
- 当前项目的直接函数调用模式更适合固定流程的场景

**下一步**：
- 尝试修改演示代码，添加新的 Agent 和事件类型
- 实现一个多租户、多主题的完整场景
- 探索 AutoGen 0.4 的其他特性（如 Team、GroupChat 等）

---

**版本**：v1.0.0
**日期**：2025-01-06
**作者**：AutoGen 学习项目

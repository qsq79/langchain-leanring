# Core API - Runtime (运行时)

本目录包含 AutoGen Core API Runtime 相关的演示代码。

## 目录

- [demo_09_runtime_basic.py](./demo_09_runtime_basic.py) - Runtime 基础
- [demo_10_agent_registration.py](./demo_10_agent_registration.py) - Agent 注册
- [demo_11_message_delivery.py](./demo_11_message_delivery.py) - 消息传递机制
- [demo_12_shutdown_idle.py](./demo_12_shutdown_idle.py) - 优雅关闭

## 学习目标

通过这些示例，你将学会：

1. ✅ 创建和配置 Runtime
2. ✅ 理解 Runtime 生命周期
3. ✅ 掌握 Agent 注册机制
4. ✅ 理解消息传递保证
5. ✅ 实现优雅关闭

## 核心概念

### Runtime

`SingleThreadedAgentRuntime` 是 AutoGen 的核心运行时，负责：
- 管理 Agent 生命周期
- 路由消息
- 执行消息处理器
- 管理订阅关系

### 生命周期

```python
runtime = SingleThreadedAgentRuntime()  # 1. 创建
await Agent.register(runtime, ...)       # 2. 注册 Agent
await runtime.add_subscription(...)     # 3. 添加订阅
runtime.start()                          # 4. 启动
await runtime.publish_message(...)      # 5. 发布消息
await runtime.stop_when_idle()          # 6. 等待完成
runtime.stop()                           # 7. 停止
```

## 快速开始

### 运行示例

```bash
# Runtime 基础
python 01-core/runtime/demo_09_runtime_basic.py

# Agent 注册
python 01-core/runtime/demo_10_agent_registration.py
```

## 相关文档

- [官方文档 - Runtime](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/runtime.html)
- [前序: Concepts](../concepts/)
- [前序: Agents](../agents/)

继续学习：[demo_09_runtime_basic.py](./demo_09_runtime_basic.py) →

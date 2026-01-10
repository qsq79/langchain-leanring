# Core API - Messaging (消息传递)

本目录包含 AutoGen Core API 消息传递相关的演示代码。

## 目录

- [demo_13_direct_messaging.py](./demo_13_direct_messaging.py) - 直接消息 (1对1)
- [demo_14_broadcast.py](./demo_14_broadcast.py) - 广播消息 (1对多)
- [demo_15_rpc_patterns.py](./demo_15_rpc_patterns.py) - RPC 调用模式

## 学习目标

通过这些示例，你将学会：

1. ✅ Agent 间的点对点通信
2. ✅ 使用 AgentId 直接发送消息
3. ✅ 实现一对多的广播消息
4. ✅ 实现请求-响应的 RPC 模式
5. ✅ 理解不同消息传递模式的适用场景

## 核心概念

### Direct Messaging (直接消息)

Agent 之间的点对点通信：
- 使用 `AgentId` 指定接收者
- 消息直接发送给特定 Agent
- 适合私有通信和定向请求

### Broadcast Messaging (广播消息)

一对多的消息传递：
- 使用 Topic 进行广播
- 所有订阅该 Topic 的 Agent 都会收到
- 适合通知和事件分发

### RPC Patterns (RPC 模式)

远程过程调用模式：
- 发送请求并等待响应
- 实现同步/异步调用
- 支持双向通信

## 快速开始

### 运行示例

```bash
# 直接消息
python 01-core/messaging/demo_13_direct_messaging.py

# 广播消息
python 01-core/messaging/demo_14_broadcast.py

# RPC 模式
python 01-core/messaging/demo_15_rpc_patterns.py
```

## 相关文档

- [官方文档 - 消息传递](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/message-passing.html)
- [前序: Runtime](../runtime/)
- [后续: Advanced](../advanced/)

继续学习：[demo_13_direct_messaging.py](./demo_13_direct_messaging.py) →

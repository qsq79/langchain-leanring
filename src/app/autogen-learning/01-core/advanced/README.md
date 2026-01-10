# Core API - Advanced (高级特性)

本目录包含 AutoGen Core API 高级特性的演示代码。

## 目录

- [demo_16_multitenancy.py](./demo_16_multitenancy.py) - 多租户架构
- [demo_17_event_sourcing.py](./demo_17_event_sourcing.py) - 事件溯源
- [demo_18_distributed_runtime.py](./demo_18_distributed_runtime.py) - 分布式运行时

## 学习目标

通过这些示例，你将学会：

1. ✅ 实现多租户架构
2. ✅ 使用 Topic Source 隔离租户
3. ✅ 实现事件溯源模式
4. ✅ 构建可追溯的事件系统
5. ✅ 理解分布式 Runtime
6. ✅ 实现跨进程通信

## 核心概念

### 多租户架构

使用 `topic_source` 实现租户隔离：
- 每个租户独立的事件流
- 数据完全隔离
- 共享 Agent 代码

### 事件溯源

记录所有状态变更事件：
- 完整的事件历史
- 状态可重放
- 审计追踪

### 分布式 Runtime

跨进程的 Agent 通信：
- gRPC 通信
- 跨语言支持
- 分布式部署

## 快速开始

### 运行示例

```bash
# 多租户架构
python 01-core/advanced/demo_16_multitenancy.py

# 事件溯源
python 01-core/advanced/demo_17_event_sourcing.py

# 分布式 Runtime
python 01-core/advanced/demo_18_distributed_runtime.py
```

## 相关文档

- [官方文档 - 高级主题](https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/)
- [前序: Messaging](../messaging/)
- [后续: AgentChat](../../02-agentchat/)

继续学习：[demo_16_multitenancy.py](./demo_16_multitenancy.py) →

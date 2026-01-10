"""
Demo 16: 多租户架构 (Multi-Tenancy)

本演示展示如何:
1. 使用 Topic Source 实现租户隔离
2. 管理多租户配置
3. 实现租户级别的数据隔离
4. 处理租户上下文传递
5. 构建多租户应用

运行方式:
    python demo_16_multitenancy.py

前置要求:
    - 已完成 demo_02_topic_subscription.py
    - 理解 Topic 和 Subscription 机制

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/cookbook/topic-subscription-scenarios.html
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 这样可以直接运行脚本文件，而不需要从特定目录运行
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # 向上 3 级到 autogen-learning/
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

from autogen_core import (
    AgentId,
    SingleThreadedAgentRuntime,
    TopicId,
    TypeSubscription,
    message_handler,

    RoutedAgent,
    MessageContext,
)

from common.utils import print_banner, print_section, print_message
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 定义消息类型 =====
@dataclass
class TenantEvent:
    """租户事件"""
    tenant_id: str
    event_type: str
    data: Dict
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class TenantConfig:
    """租户配置"""
    tenant_id: str
    tenant_name: str
    settings: Dict = field(default_factory=dict)
    enabled: bool = True


@dataclass
class TenantRequest:
    """租户请求"""
    tenant_id: str
    request_type: str
    params: Dict


# ===== 定义 Agent =====
class TenantAwareAgent(RoutedAgent):
    """租户感知 Agent - 处理多租户请求"""

    def __init__(self, name: str, description: str = "Tenant Aware Agent"):
        super().__init__(description)
        self.name = name
        self.tenant_stats: Dict[str, int] = {}  # tenant_id -> request_count

    @message_handler
    async def handle_tenant_event(self, event: TenantEvent, ctx: MessageContext) -> None:
        """处理租户事件"""

        # 从 topic source 获取租户 ID
        tenant_id = ctx.topic_id.source if ctx.topic_id else "unknown"

        # 验证租户
        if event.tenant_id != tenant_id:
            print(f"\n  ⚠️  [{self.name}] 租户 ID 不匹配")
            print(f"     事件租户: {event.tenant_id}")
            print(f"     Topic 租户: {tenant_id}")
            return

        # 更新统计
        self.tenant_stats[tenant_id] = self.tenant_stats.get(tenant_id, 0) + 1

        print(f"\n  🏢 [{self.name}] 处理租户事件")
        print(f"     租户: {event.tenant_id}")
        print(f"     事件: {event.event_type}")
        print(f"     数据: {event.data}")
        print(f"     该租户请求计数: {self.tenant_stats[tenant_id]}")


class IsolatedAgent(RoutedAgent):
    """隔离 Agent - 每个租户独立实例"""

    def __init__(self, tenant_id: str, description: str = "Isolated Agent"):
        super().__init__(description)
        self.tenant_id = tenant_id
        self.data_store: List[str] = []

    @message_handler
    async def handle_request(self, request: TenantRequest, ctx: MessageContext) -> None:
        """处理租户请求"""

        print(f"\n  🔒 [隔离Agent-{self.tenant_id}] 处理请求")
        print(f"     租户: {request.tenant_id}")
        print(f"     类型: {request.request_type}")
        print(f"     参数: {request.params}")

        # 存储数据（租户隔离）
        self.data_store.append(f"{request.request_type}:{request.params}")
        print(f"     ✓ 数据已存储 (租户隔离)")
        print(f"     总数据项: {len(self.data_store)}")


class ConfigManagerAgent(RoutedAgent):
    """配置管理 Agent"""

    def __init__(self, description: str = "Config Manager"):
        super().__init__(description)
        self.tenant_configs: Dict[str, TenantConfig] = {}

    @message_handler
    async def handle_config_update(self, config: TenantConfig, ctx: MessageContext) -> None:
        """更新租户配置"""

        print(f"\n  ⚙️  [配置管理] 更新租户配置")
        print(f"     租户: {config.tenant_id}")
        print(f"     名称: {config.tenant_name}")
        print(f"     启用: {config.enabled}")

        self.tenant_configs[config.tenant_id] = config
        print(f"     ✓ 配置已保存")

    @message_handler
    async def handle_config_query(self, message: TenantRequest, ctx: MessageContext) -> None:
        """查询租户配置"""

        tenant_id = message.params.get("tenant_id")
        config = self.tenant_configs.get(tenant_id)

        print(f"\n  🔍 [配置管理] 租户配置查询")
        print(f"     租户: {tenant_id}")

        if config:
            print(f"     名称: {config.tenant_name}")
            print(f"     设置: {config.settings}")
            print(f"     状态: {'启用' if config.enabled else '禁用'}")
        else:
            print(f"     ⚠️  租户不存在")


class CrossTenantAgent(RoutedAgent):
    """跨租户 Agent - 处理跨租户操作"""

    def __init__(self, description: str = "Cross Tenant Agent"):
        super().__init__(description)

    @message_handler
    async def handle_cross_tenant_event(self, event: TenantEvent, ctx: MessageContext) -> None:
        """处理跨租户事件"""

        source_tenant = ctx.topic_id.source if ctx.topic_id else "unknown"

        print(f"\n  🔄 [跨租户] 处理跨租户事件")
        print(f"     源租户: {source_tenant}")
        print(f"     目标租户: {event.tenant_id}")
        print(f"     事件类型: {event.event_type}")

        # 跨租户数据访问需要特殊权限
        if source_tenant != event.tenant_id:
            print(f"     ⚠️  跨租户访问需要权限验证")
            print(f"     权限检查: {'✅ 通过' if self._check_permission(source_tenant, event.tenant_id) else '❌ 拒绝'}")

    def _check_permission(self, source: str, target: str) -> bool:
        """检查跨租户权限"""
        # 简化实现：某些租户有跨租户访问权限
        privileged_tenants = ["admin", "system"]
        return source in privileged_tenants


# ===== 演示函数 =====
async def demo_basic_multitenancy():
    """演示 1: 基本的多租户隔离"""
    print_section("演示 1: 使用 Topic Source 实现租户隔离")

    runtime = SingleThreadedAgentRuntime()

    # 注册租户感知 Agent
    await TenantAwareAgent.register(runtime, "tenant_handler", lambda: TenantAwareAgent("租户处理器"))
    await runtime.add_subscription(TypeSubscription("tenant_events", "tenant_handler"))

    runtime.start()

    print("\n--- 租户 A 发送事件 ---")
    await runtime.publish_message(
        TenantEvent(
            tenant_id="client_a",
            event_type="user_action",
            data={"action": "click", "page": "home"}
        ),
        TopicId("tenant_events", "client_a")  # source = 租户 ID
    )

    await asyncio.sleep(0.2)

    print("\n--- 租户 B 发送事件 ---")
    await runtime.publish_message(
        TenantEvent(
            tenant_id="client_b",
            event_type="user_action",
            data={"action": "search", "query": "product"}
        ),
        TopicId("tenant_events", "client_b")  # 不同的 source
    )

    await asyncio.sleep(0.2)

    print("\n💡 观察结果:")
    print("  - 每个租户有独立的消息流")
    print("  - Topic Source 用于区分租户")
    print("  - 数据完全隔离")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_isolated_agents():
    """演示 2: 租户隔离的 Agent 实例"""
    print_section("演示 2: 每个租户独立的 Agent 实例")

    runtime = SingleThreadedAgentRuntime()

    # 注册 Agent，使用 TypeSubscription
    # Runtime 会为每个 source 创建独立的 Agent 实例
    await IsolatedAgent.register(runtime, "isolated", lambda: IsolatedAgent("默认"))
    await runtime.add_subscription(TypeSubscription("tenant_requests", "isolated"))

    runtime.start()

    print("\n--- 租户 A 发送请求 ---")
    await runtime.publish_message(
        TenantRequest(
            tenant_id="client_a",
            request_type="create_order",
            params={"product": "iPhone", "quantity": 1}
        ),
        TopicId("tenant_requests", "client_a")
    )

    await asyncio.sleep(0.2)

    print("\n--- 租户 B 发送请求 ---")
    await runtime.publish_message(
        TenantRequest(
            tenant_id="client_b",
            request_type="create_order",
            params={"product": "MacBook", "quantity": 2}
        ),
        TopicId("tenant_requests", "client_b")
    )

    await asyncio.sleep(0.2)

    print("\n--- 租户 C 发送请求 ---")
    await runtime.publish_message(
        TenantRequest(
            tenant_id="client_c",
            request_type="create_order",
            params={"product": "AirPods", "quantity": 5}
        ),
        TopicId("tenant_requests", "client_c")
    )

    await asyncio.sleep(0.2)

    print("\n💡 TypeSubscription 的魔力:")
    print("  - 一个 Agent 类型定义")
    print("  - 多个 source → 多个 Agent 实例")
    print("  - 每个 instance.key = source")
    print("  - 数据自动隔离")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_tenant_configuration():
    """演示 3: 租户配置管理"""
    print_section("演示 3: 租户配置管理")

    runtime = SingleThreadedAgentRuntime()

    await ConfigManagerAgent.register(runtime, "config_mgr", lambda: ConfigManagerAgent())
    await TenantAwareAgent.register(runtime, "processor", lambda: TenantAwareAgent("处理器"))

    await runtime.add_subscription(TypeSubscription("config", "config_mgr"))
    await runtime.add_subscription(TypeSubscription("tenant_events", "processor"))

    runtime.start()

    print("\n--- 创建租户配置 ---")

    # 租户 A 配置
    config_a = TenantConfig(
        tenant_id="client_a",
        tenant_name="客户 A 公司",
        settings={"max_requests": 1000, "features": ["analytics", "reporting"]},
        enabled=True
    )

    await runtime.publish_message(config_a, TopicId("config", "default"))
    await asyncio.sleep(0.1)

    # 租户 B 配置
    config_b = TenantConfig(
        tenant_id="client_b",
        tenant_name="客户 B 公司",
        settings={"max_requests": 500, "features": ["basic"]},
        enabled=True
    )

    await runtime.publish_message(config_b, TopicId("config", "default"))
    await asyncio.sleep(0.1)

    print("\n--- 查询租户配置 ---")
    await runtime.publish_message(
        TenantRequest("config_mgr", "query", {"tenant_id": "client_a"}),
        TopicId("config", "default")
    )

    await asyncio.sleep(0.3)

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_multi_topic_per_tenant():
    """演示 4: 每个租户多个 Topic"""
    print_section("演示 4: 多 Topic 多租户架构")

    runtime = SingleThreadedAgentRuntime()

    await TenantAwareAgent.register(runtime, "multi_topic_agent", lambda: TenantAwareAgent("多TopicAgent"))
    await runtime.add_subscription(TypeSubscription("orders", "multi_topic_agent"))
    await runtime.add_subscription(TypeSubscription("shipments", "multi_topic_agent"))
    await runtime.add_subscription(TypeSubscription("payments", "multi_topic_agent"))

    runtime.start()

    print("\n--- 租户 A 的不同业务事件 ---")

    # 订单事件
    await runtime.publish_message(
        TenantEvent("client_a", "order_created", {"order_id": "ORD-A-001", "amount": 1000}),
        TopicId("orders", "client_a")
    )
    await asyncio.sleep(0.1)

    # 物流事件
    await runtime.publish_message(
        TenantEvent("client_a", "shipment_created", {"shipment_id": "SHP-A-001"}),
        TopicId("shipments", "client_a")
    )
    await asyncio.sleep(0.1)

    # 支付事件
    await runtime.publish_message(
        TenantEvent("client_a", "payment_received", {"payment_id": "PAY-A-001", "amount": 1000}),
        TopicId("payments", "client_a")
    )

    await asyncio.sleep(0.2)

    print("\n💡 说明:")
    print("  - 一个租户可以有多个 Topic Type")
    print("  - 所有 Topic 都使用相同的 source (租户 ID)")
    print("  - Agent 订阅多个 Topic Type")
    print("  - 实现了业务功能的多租户支持")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_cross_tenant_operations():
    """演示 5: 跨租户操作"""
    print_section("演示 5: 跨租户操作和权限")

    runtime = SingleThreadedAgentRuntime()

    await CrossTenantAgent.register(runtime, "cross_tenant", lambda: CrossTenantAgent())
    await runtime.add_subscription(TypeSubscription("cross_tenant", "cross_tenant"))

    runtime.start()

    print("\n--- 租户 A 请求访问租户 B 的数据 ---")

    cross_tenant_event = TenantEvent(
        tenant_id="client_b",  # 目标租户
        event_type="data_access",
        data={"requested_by": "client_a", "resource": "analytics"}
    )

    print(f"请求者: client_a")
    print(f"目标租户: client_b")
    print(f"事件类型: 数据访问")

    await runtime.publish_message(
        cross_tenant_event,
        TopicId("cross_tenant", "client_a")  # source = 请求租户
    )

    await asyncio.sleep(0.3)

    print("\n💡 跨租户访问注意事项:")
    print("  - 需要权限验证")
    print("  - 审计日志记录")
    print("  - 数据隔离策略")
    print("  - 最小权限原则")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_tenant_lifecycle():
    """演示 6: 租户生命周期管理"""
    print_section("演示 6: 租户生命周期管理")

    runtime = SingleThreadedAgentRuntime()

    await ConfigManagerAgent.register(runtime, "lifecycle_mgr", lambda: ConfigManagerAgent())
    await TenantAwareAgent.register(runtime, "processor", lambda: TenantAwareAgent("生命周期处理器"))

    await runtime.add_subscription(TypeSubscription("lifecycle", "lifecycle_mgr"))
    await runtime.add_subscription(TypeSubscription("events", "processor"))

    runtime.start()

    print("\n--- 租户生命周期阶段 ---")

    stages = [
        ("创建租户", "create", {"tenant_id": "new_client", "tenant_name": "新客户"}),
        ("配置租户", "configure", {"tenant_id": "new_client", "enabled": True}),
        ("使用中", "active", {"tenant_id": "new_client", "feature": "analytics"}),
        ("暂停租户", "suspend", {"tenant_id": "new_client", "enabled": False}),
        ("恢复租户", "resume", {"tenant_id": "new_client", "enabled": True}),
        ("删除租户", "delete", {"tenant_id": "new_client"}),
    ]

    for stage_name, action, params in stages:
        print(f"\n{stage_name}...")

        config = TenantConfig(**params)
        await runtime.publish_message(config, TopicId("lifecycle", "default"))

        # 触发事件
        await runtime.publish_message(
            TenantEvent(params.get("tenant_id"), action, params),
            TopicId("events", params.get("tenant_id"))
        )

        await asyncio.sleep(0.1)

    await asyncio.sleep(0.3)
    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 租户生命周期:")
    print("  创建 → 配置 → 使用 → 暂停 → 恢复 → 删除")
    print("  每个阶段都有对应的配置和事件")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 多租户架构                           ║
        ║           Multi-Tenancy with Topic Source                    ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 基本隔离
        await demo_basic_multitenancy()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 隔离实例
        await demo_isolated_agents()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 配置管理
        await demo_tenant_configuration()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 多 Topic
        await demo_multi_topic_per_tenant()

        print("\n" + "=" * 80 + "\n")

        # 演示 5: 跨租户
        await demo_cross_tenant_operations()

        print("\n" + "=" * 80 + "\n")

        # 演示 6: 生命周期
        await demo_tenant_lifecycle()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")

        print("\n关键要点:")
        print("  1. 使用 Topic Source 实现租户隔离")
        print("  2. TypeSubscription 自动为每个 source 创建 Agent 实例")
        print("  3. 租户配置可以动态管理")
        print("  4. 支持跨租户操作（需要权限控制）")
        print("  5. 完整的租户生命周期管理")
        print("  6. 适合 SaaS 和多用户应用")
        print("=" * 80 + "\n")

    except Exception as e:
        print_message("System", f"✗ 发生错误: {e}", "ERROR")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

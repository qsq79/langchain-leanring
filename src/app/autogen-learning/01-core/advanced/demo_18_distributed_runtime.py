"""
Demo 18: 分布式运行时 (Distributed Runtime)

本演示展示如何:
1. 理解分布式运行时的概念
2. 使用 GrpcWorkerAgentRuntime
3. 实现跨进程通信
4. 理解分布式架构的优势
5. 部署和管理分布式 Agent

注意: 本演示为概念性演示，实际分布式部署需要更复杂的配置。

运行方式:
    python demo_18_distributed_runtime.py

前置要求:
    - 已完成 demo_09_runtime_basic.py
    - 理解基本 Runtime 概念

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/core-user-guide/core-concepts/runtime.html
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
import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime

from autogen_core import (
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
class TaskMessage:
    """任务消息"""
    task_id: str
    task_type: str
    payload: Dict
    sender: str
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ResultMessage:
    """结果消息"""
    task_id: str
    result: Dict
    worker_id: str
    success: bool
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class WorkerStatusMessage:
    """工作节点状态消息"""
    worker_id: str
    status: str
    load: int
    capabilities: List[str]
    timestamp: str = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


# ===== 定义 Agent =====
class WorkerAgent(RoutedAgent):
    """工作节点 Agent - 模拟分布式工作节点"""

    def __init__(
        self,
        worker_id: str,
        capabilities: List[str],
        max_concurrent: int = 3,
        description: str = "Worker Agent"
    ):
        super().__init__(description)
        self.worker_id = worker_id
        self.capabilities = capabilities
        self.max_concurrent = max_concurrent
        self.current_load = 0
        self.completed_tasks = 0
        self.failed_tasks = 0

        print(f"  🔧 [{self.worker_id}] 工作节点初始化")
        print(f"     能力: {', '.join(capabilities)}")
        print(f"     最大并发: {max_concurrent}")

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """处理任务"""

        # 检查是否具备处理能力
        if message.task_type not in self.capabilities:
            print(f"\n  ⚠️  [{self.worker_id}] 不支持任务类型: {message.task_type}")
            return

        # 检查负载
        if self.current_load >= self.max_concurrent:
            print(f"\n  ⏸️  [{self.worker_id}] 已达到最大负载")
            return

        # 处理任务
        self.current_load += 1

        print(f"\n  🔨 [{self.worker_id}] 处理任务")
        print(f"     任务 ID: {message.task_id}")
        print(f"     类型: {message.task_type}")
        print(f"     发送者: {message.sender}")
        print(f"     当前负载: {self.current_load}/{self.max_concurrent}")

        # 模拟处理
        await asyncio.sleep(0.5)

        # 生成结果
        result_data = {
            "worker_id": self.worker_id,
            "processed_at": datetime.now().isoformat(),
            "status": "completed",
            "output": f"Task {message.task_id} processed by {self.worker_id}"
        }

        result = ResultMessage(
            task_id=message.task_id,
            result=result_data,
            worker_id=self.worker_id,
            success=True
        )

        # 发送结果
        if ctx.topic_id:
            await self.publish_message(result, ctx.topic_id)

        # 更新状态
        self.completed_tasks += 1
        self.current_load -= 1

        print(f"  ✅ [{self.worker_id}] 任务完成")
        print(f"     累计完成: {self.completed_tasks}")


class CoordinatorAgent(RoutedAgent):
    """协调器 Agent - 管理分布式任务分配"""

    def __init__(self, description: str = "Coordinator Agent"):
        super().__init__(description)
        self.workers: Dict[str, Dict] = {}  # worker_id -> status
        self.pending_tasks: List[TaskMessage] = []
        self.completed_tasks: List[ResultMessage] = []

    @message_handler
    async def handle_worker_status(self, message: WorkerStatusMessage, ctx: MessageContext) -> None:
        """处理工作节点状态"""

        self.workers[message.worker_id] = {
            "status": message.status,
            "load": message.load,
            "capabilities": message.capabilities,
            "last_seen": datetime.now()
        }

        print(f"\n  📊 [协调器] 更新工作节点状态")
        print(f"     节点: {message.worker_id}")
        print(f"     状态: {message.status}")
        print(f"     负载: {message.load}")
        print(f"     能力: {', '.join(message.capabilities)}")

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """接收任务并分配"""

        print(f"\n  📨 [协调器] 收到任务")
        print(f"     任务 ID: {message.task_id}")
        print(f"     类型: {message.task_type}")

        # 尝试分配任务
        assigned = False
        for worker_id, status in self.workers.items():
            if (status["status"] == "ready" and 
                status["load"] < 3 and
                message.task_type in status["capabilities"]):
                
                # 分配给该工作节点
                assigned = True
                print(f"  🎯 [协调器] 分配给: {worker_id}")
                
                # 转发任务（在真实分布式环境中，这会通过 RPC 调用）
                if ctx.topic_id:
                    await self.publish_message(message, ctx.topic_id)
                break

        if not assigned:
            print(f"  ⚠️  [协调器] 无法分配任务")
            print(f"     原因: 没有可用的工作节点")
            self.pending_tasks.append(message)

    @message_handler
    async def handle_result(self, message: ResultMessage, ctx: MessageContext) -> None:
        """处理任务结果"""

        self.completed_tasks.append(message)

        print(f"\n  📥 [协调器] 收到任务结果")
        print(f"     任务 ID: {message.task_id}")
        print(f"     工作节点: {message.worker_id}")
        print(f"     状态: {'成功' if message.success else '失败'}")

        # 更新工作节点负载
        if message.worker_id in self.workers:
            self.workers[message.worker_id]["load"] -= 1

    @message_handler
    async def handle_status_query(self, message: str, ctx: MessageContext) -> None:
        """查询系统状态"""

        print(f"\n  📊 [协调器] 系统状态")
        print(f"\n     工作节点: {len(self.workers)}")
        for worker_id, status in self.workers.items():
            print(f"\n     👤 {worker_id}:")
            print(f"        状态: {status['status']}")
            print(f"        负载: {status['load']}")
            print(f"        能力: {', '.join(status['capabilities'])}")

        print(f"\n     任务统计:")
        print(f"        已完成: {len(self.completed_tasks)}")
        print(f"        待处理: {len(self.pending_tasks)}")


class LoadBalancerAgent(RoutedAgent):
    """负载均衡 Agent - 智能任务分配"""

    def __init__(self, description: str = "Load Balancer Agent"):
        super().__init__(description)
        self.workers: Dict[str, Dict] = {}
        self.task_queue: List[TaskMessage] = []

    @message_handler
    async def handle_worker_status(self, message: WorkerStatusMessage, ctx: MessageContext) -> None:
        """更新工作节点状态"""

        self.workers[message.worker_id] = {
            "status": message.status,
            "load": message.load,
            "capabilities": message.capabilities,
            "last_seen": datetime.now()
        }

    @message_handler
    async def handle_task(self, message: TaskMessage, ctx: MessageContext) -> None:
        """智能分配任务"""

        print(f"\n  ⚖️  [负载均衡] 分配任务: {message.task_id}")

        # 找到负载最低的合适工作节点
        best_worker = None
        min_load = float('inf')

        for worker_id, status in self.workers.items():
            if (status["status"] == "ready" and
                message.task_type in status["capabilities"]):
                
                if status["load"] < min_load:
                    min_load = status["load"]
                    best_worker = worker_id

        if best_worker:
            print(f"  ✅ 分配给: {best_worker} (负载: {min_load})")
            # 转发任务
            if ctx.topic_id:
                await self.publish_message(message, ctx.topic_id)
        else:
            print(f"  ❌ 无可用节点")
            self.task_queue.append(message)


# ===== 演示函数 =====
async def demo_single_runtime_simulation():
    """演示 1: 模拟分布式系统（单 Runtime）"""
    print_section("演示 1: 模拟分布式系统")

    runtime = SingleThreadedAgentRuntime()

    # 注册工作节点
    print("\n--- 注册工作节点 ---")
    workers = [
        ("worker-1", ["compute", "analyze"]),
        ("worker-2", ["compute", "storage"]),
        ("worker-3", ["analyze", "network"]),
    ]

    for worker_id, capabilities in workers:
        await WorkerAgent.register(
            runtime,
            worker_id,
            lambda wid=worker_id, caps=capabilities: WorkerAgent(wid, caps)
        )
        await runtime.add_subscription(TypeSubscription("tasks", worker_id))
        print(f"  ✓ {worker_id}: {', '.join(capabilities)}")

    # 注册协调器
    await CoordinatorAgent.register(runtime, "coordinator", lambda: CoordinatorAgent())
    await runtime.add_subscription(TypeSubscription("tasks", "coordinator"))
    await runtime.add_subscription(TypeSubscription("results", "coordinator"))
    await runtime.add_subscription(TypeSubscription("status", "coordinator"))

    runtime.start()

    # 工作节点报告状态
    print("\n--- 工作节点报告状态 ---")
    for worker_id, _ in workers:
        status = WorkerStatusMessage(
            worker_id=worker_id,
            status="ready",
            load=0,
            capabilities=[]
        )
        await runtime.publish_message(status, TopicId("status", "default"))

    await asyncio.sleep(0.2)

    # 发送任务
    print("\n--- 发送任务 ---")
    tasks = [
        ("task-1", "compute"),
        ("task-2", "analyze"),
        ("task-3", "storage"),
    ]

    for task_id, task_type in tasks:
        task = TaskMessage(
            task_id=task_id,
            task_type=task_type,
            payload={"data": f"Data for {task_id}"},
            sender="client"
        )
        await runtime.publish_message(task, TopicId("tasks", "default"))
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.5)

    # 查询状态
    print("\n--- 查询系统状态 ---")
    await runtime.publish_message("query_status", TopicId("status", "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 模拟了多个工作节点")
    print("  - 协调器分配任务给合适的节点")
    print("  - 工作节点根据能力处理任务")


async def demo_load_balancing():
    """演示 2: 负载均衡"""
    print_section("演示 2: 智能负载均衡")

    runtime = SingleThreadedAgentRuntime()

    # 注册工作节点（不同负载）
    print("\n--- 注册工作节点 ---")
    workers = [
        ("worker-1", ["compute"], 1),  # 已处理 1 个任务
        ("worker-2", ["compute"], 0),  # 空闲
        ("worker-3", ["compute"], 2),  # 已处理 2 个任务
    ]

    for worker_id, capabilities, initial_load in workers:
        agent = WorkerAgent(worker_id, capabilities)
        await WorkerAgent.register(runtime, worker_id, lambda: agent)
        await runtime.add_subscription(TypeSubscription("tasks", worker_id))
        print(f"  ✓ {worker_id}: 初始负载 {initial_load}")

    # 注册负载均衡器
    await LoadBalancerAgent.register(runtime, "balancer", lambda: LoadBalancerAgent())
    await runtime.add_subscription(TypeSubscription("tasks", "balancer"))
    await runtime.add_subscription(TypeSubscription("status", "balancer"))

    runtime.start()

    # 工作节点报告初始状态
    print("\n--- 工作节点报告状态 ---")
    for worker_id, _, load in workers:
        status = WorkerStatusMessage(
            worker_id=worker_id,
            status="ready",
            load=load,
            capabilities=["compute"]
        )
        await runtime.publish_message(status, TopicId("status", "default"))

    await asyncio.sleep(0.2)

    # 发送多个相同类型的任务
    print("\n--- 发送多个计算任务 ---")
    for i in range(3):
        task = TaskMessage(
            task_id=f"task-{i+1}",
            task_type="compute",
            payload={"value": i*10},
            sender="client"
        )
        await runtime.publish_message(task, TopicId("tasks", "default"))
        await asyncio.sleep(0.1)

    await asyncio.sleep(0.8)

    print("\n💡 观察:")
    print("  - 任务应该分配给负载最低的节点")
    print("  - 负载均衡器智能选择工作节点")
    print("  - 避免某些节点过载")

    await runtime.stop_when_idle()
    runtime.stop()


async def demo_distributed_concepts():
    """演示 3: 分布式概念"""
    print_section("演示 3: 分布式架构概念")

    print("\n📐 分布式架构组件:")
    print("\n  1. 协调器 (Coordinator)")
    print("     - 接收外部任务")
    print("     - 监控工作节点状态")
    print("     - 分配任务给合适的节点")
    print("     - 收集和处理结果")

    print("\n  2. 工作节点 (Workers)")
    print("     - 独立的进程或机器")
    print("     - 处理分配的任务")
    print("     - 报告状态和能力")
    print("     - 返回结果")

    print("\n  3. 消息传递")
    print("     - gRPC 或其他协议")
    print("     - 跨网络通信")
    print("     - 可靠性和重试")

    print("\n  4. 服务发现")
    print("     - 节点注册")
    print("     - 健康检查")
    print("     - 故障转移")

    print("\n🎯 分布式优势:")
    print("\n  ✅ 可扩展性")
    print("     - 水平扩展：添加更多节点")
    print("     - 垂直扩展：提升单个节点能力")
    print("     - 弹性伸缩：根据负载自动调整")

    print("\n  ✅ 可靠性")
    print("     - 单点故障容错")
    print("     - 数据冗余")
    print("     - 故障转移")

    print("\n  ✅ 性能")
    print("     - 并行处理")
    print("     - 就近访问")
    print("     - 负载均衡")

    print("\n⚠️  分布式挑战:")
    print("\n  ⚙️  复杂性")
    print("     - 网络延迟")
    print("     - 一致性保证")
    print("     - 分布式事务")

    print("\n  🔒 安全性")
    print("     - 通信加密")
    print("     - 身份验证")
    print("     - 访问控制")

    print("\n  📊 监控和调试")
    print("     - 分布式追踪")
    print("     - 日志聚合")
    print("     - 性能监控")


async def demo_worker_capabilities():
    """演示 4: 工作节点能力匹配"""
    print_section("演示 4: 工作节点能力匹配")

    runtime = SingleThreadedAgentRuntime()

    # 注册不同能力的工作节点
    print("\n--- 注册不同能力的工作节点 ---")
    workers = [
        ("compute-worker", ["compute", "math"], "计算节点"),
        ("storage-worker", ["storage", "database"], "存储节点"),
        ("network-worker", ["network", "http"], "网络节点"),
        ("all-round-worker", ["compute", "storage", "network"], "全能节点"),
    ]

    for worker_id, capabilities, desc in workers:
        await WorkerAgent.register(
            runtime,
            worker_id,
            lambda wid=worker_id, caps=capabilities: WorkerAgent(wid, caps)
        )
        await runtime.add_subscription(TypeSubscription("tasks", worker_id))
        print(f"  ✓ {worker_id}: {desc}")
        print(f"      能力: {', '.join(capabilities)}")

    # 注册协调器
    await CoordinatorAgent.register(runtime, "coordinator", lambda: CoordinatorAgent())
    await runtime.add_subscription(TypeSubscription("tasks", "coordinator"))
    await runtime.add_subscription(TypeSubscription("results", "coordinator"))
    await runtime.add_subscription(TypeSubscription("status", "coordinator"))

    runtime.start()

    # 报告状态
    print("\n--- 工作节点报告能力 ---")
    for worker_id, capabilities, _ in workers:
        status = WorkerStatusMessage(
            worker_id=worker_id,
            status="ready",
            load=0,
            capabilities=capabilities
        )
        await runtime.publish_message(status, TopicId("status", "default"))

    await asyncio.sleep(0.2)

    # 发送不同类型的任务
    print("\n--- 发送不同类型的任务 ---")
    tasks = [
        ("task-1", "compute", "计算密集型任务"),
        ("task-2", "storage", "存储任务"),
        ("task-3", "network", "网络请求"),
        ("task-4", "math", "数学计算任务"),
    ]

    for task_id, task_type, desc in tasks:
        task = TaskMessage(
            task_id=task_id,
            task_type=task_type,
            payload={"description": desc},
            sender="client"
        )
        await runtime.publish_message(task, TopicId("tasks", "default"))
        print(f"\n  📨 发送: {desc} (类型: {task_type})")
        await asyncio.sleep(0.15)

    await asyncio.sleep(0.8)

    # 查询状态
    print("\n--- 查询状态 ---")
    await runtime.publish_message("query_status", TopicId("status", "default"))

    await runtime.stop_when_idle()
    runtime.stop()

    print("\n💡 说明:")
    print("  - 任务根据类型分配给具备相应能力的节点")
    print("  - 全能节点可以作为后备")
    print("  - 提高了系统效率和资源利用率")


# ===== 主函数 =====
async def main() -> None:
    """主函数"""
    print_banner(
        """
        ╔════════════════════════════════════════════════════════════════╗
        ║                                                                ║
        ║          AutoGen 0.4+ - 分布式运行时演示                  ║
        ║           Distributed Architecture Concepts                     ║
        ║                                                                ║
        ╚════════════════════════════════════════════════════════════════╝
        """
    )

    try:
        # 演示 1: 模拟分布式系统
        await demo_single_runtime_simulation()

        print("\n" + "=" * 80 + "\n")

        # 演示 2: 负载均衡
        await demo_load_balancing()

        print("\n" + "=" * 80 + "\n")

        # 演示 3: 分布式概念
        await demo_distributed_concepts()

        print("\n" + "=" * 80 + "\n")

        # 演示 4: 能力匹配
        await demo_worker_capabilities()

        print("\n" + "=" * 80)
        print_message("System", "✓ 所有演示完成!", "SUCCESS")
        print("\n下一步:")
        print("  1. 查看 02-agentchat/ 目录学习高层 API")
        print("  2. 了解 GrpcWorkerAgentRuntime 的实际部署")
        print("  3. 研究分布式系统的最佳实践")
        print("  4. 学习服务发现和负载均衡算法")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
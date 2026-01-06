#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 能力注册表
集中管理所有 Agent 的描述、工具和能力信息
实现企业级可维护的动态 Agent 注册机制
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class AgentCapability:
    """Agent 能力描述"""
    name: str                          # Agent 名称
    description: str                    # Agent 描述
    tools: List[str] = field(default_factory=list)  # 可用工具列表
    use_cases: List[str] = field(default_factory=list)  # 适用场景
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "name": self.name,
            "description": self.description,
            "tools": self.tools,
            "use_cases": self.use_cases
        }


class AgentRegistry:
    """Agent 能力注册表 - 企业级实现"""
    
    # 预定义的 Agent 能力
    _capabilities: Dict[str, AgentCapability] = {
        "order_agent": AgentCapability(
            name="order_agent",
            description=(
                "订单查询专家。负责查询和管理订单相关信息，"
                "包括订单状态、支付状态、发货状态、订单金额和商品信息。"
                "该 Agent 可以处理所有订单相关的查询和操作。"
            ),
            tools=[
                "query_order_tool",           # 查询订单详情
                "generate_order_summary"      # 生成订单摘要
            ],
            use_cases=[
                "查询订单状态",
                "查看订单详情",
                "查询支付状态",
                "订单发货状态",
                "订单退款",
                "订单取消",
                "订单金额查询",
                "商品信息查询"
            ]
        ),
        
        "logistics_agent": AgentCapability(
            name="logistics_agent",
            description=(
                "物流查询专家。负责查询和跟踪订单的物流信息，"
                "包括物流状态、当前位置、预计送达时间和完整的物流轨迹。"
                "该 Agent 可以处理所有物流配送相关的查询。"
            ),
            tools=[
                "query_logistics_tool",        # 查询物流信息
                "generate_logistics_summary"   # 生成物流摘要
            ],
            use_cases=[
                "查询物流状态",
                "查看物流轨迹",
                "快递位置查询",
                "配送状态",
                "送达时间查询",
                "物流异常查询",
                "快递员信息",
                "配送延迟处理"
            ]
        ),
        
        "summary_agent": AgentCapability(
            name="summary_agent",
            description=(
                "结果汇总专家。负责汇总多个 Agent 的查询结果，"
                "并生成统一的用户友好的回复。不参与查询路由。"
            ),
            tools=[
                "summarize_results"           # 汇总结果
            ],
            use_cases=[
                "汇总订单和物流信息",
                "生成综合回复",
                "多维度信息整合",
                "用户友好的回复生成"
            ]
        )
    }
    
    @classmethod
    def register_agent(cls, capability: AgentCapability):
        """
        注册新的 Agent（支持动态扩展现有系统）
        
        Args:
            capability: Agent 能力描述
            
        Raises:
            ValueError: 如果 Agent 名称已存在
        """
        if capability.name in cls._capabilities:
            raise ValueError(f"Agent '{capability.name}' already registered")
        
        cls._capabilities[capability.name] = capability
        logger.info(f"注册新 Agent: {capability.name}")
    
    @classmethod
    def update_agent(cls, capability: AgentCapability):
        """
        更新已存在的 Agent 能力信息
        
        Args:
            capability: Agent 能力描述
            
        Raises:
            ValueError: 如果 Agent 名称不存在
        """
        if capability.name not in cls._capabilities:
            raise ValueError(f"Agent '{capability.name}' not found")
        
        cls._capabilities[capability.name] = capability
        logger.info(f"更新 Agent: {capability.name}")
    
    @classmethod
    def get_agent_capability(cls, agent_name: str) -> AgentCapability:
        """
        获取指定 Agent 的能力描述
        
        Args:
            agent_name: Agent 名称
            
        Returns:
            Agent 能力描述，不存在则返回 None
        """
        return cls._capabilities.get(agent_name)
    
    @classmethod
    def get_all_agents(cls) -> Dict[str, AgentCapability]:
        """
        获取所有 Agent 的能力描述
        
        Returns:
            所有 Agent 能力描述字典
        """
        return cls._capabilities.copy()
    
    @classmethod
    def get_agents_for_prompt(cls) -> str:
        """
        生成用于 LLM 提示词的 Agent 描述文本
        
        Returns:
            格式化的 Agent 描述文本（英文，适合 LLM）
        """
        prompt_parts = ["Available Agents and Their Capabilities:"]
        
        # 只返回可路由的 Agent（排除 summary_agent）
        for agent_name, capability in cls._capabilities.items():
            if agent_name == "summary_agent":
                continue
            
            prompt_parts.append(f"\n### {capability.name}")
            prompt_parts.append(f"**Description**: {capability.description}")
            prompt_parts.append(f"**Tools**: {', '.join(capability.tools)}")
            prompt_parts.append(f"**Use Cases**: {', '.join(capability.use_cases)}")
        
        return "\n".join(prompt_parts)
    
    @classmethod
    def get_routable_agents(cls) -> List[str]:
        """
        获取所有可路由的 Agent 名称列表（排除 summary_agent）
        
        Returns:
            Agent 名称列表
        """
        return [name for name in cls._capabilities.keys() if name != "summary_agent"]
    
    @classmethod
    def get_agent_names(cls) -> List[str]:
        """
        获取所有 Agent 名称列表（包括所有 Agent）
        
        Returns:
            Agent 名称列表
        """
        return list(cls._capabilities.keys())
    
    @classmethod
    def validate_agent_exists(cls, agent_name: str) -> bool:
        """
        验证 Agent 是否存在
        
        Args:
            agent_name: Agent 名称
            
        Returns:
            Agent 是否存在
        """
        return agent_name in cls._capabilities
    
    @classmethod
    def get_capabilities_dict(cls) -> Dict[str, Dict[str, Any]]:
        """
        获取所有 Agent 能力的字典格式（用于配置文件或 API）
        
        Returns:
            Agent 能力字典
        """
        return {
            name: capability.to_dict()
            for name, capability in cls._capabilities.items()
        }
    
    @classmethod
    def print_registry(cls):
        """打印注册表信息（用于调试）"""
        print("\n" + "=" * 60)
        print("📋 Agent Registry")
        print("=" * 60)
        
        for name, capability in cls._capabilities.items():
            print(f"\n🤖 Agent: {name}")
            print(f"   描述: {capability.description}")
            print(f"   工具: {', '.join(capability.tools)}")
            print(f"   场景: {', '.join(capability.use_cases[:3])}...")
        
        print("\n" + "=" * 60)
        print(f"总共: {len(cls._capabilities)} 个 Agent")
        print("=" * 60 + "\n")


# 便捷函数
def get_agent_info(agent_name: str) -> AgentCapability:
    """获取 Agent 能力信息的便捷函数"""
    return AgentRegistry.get_agent_capability(agent_name)


def get_routable_agent_names() -> List[str]:
    """获取可路由 Agent 名称的便捷函数"""
    return AgentRegistry.get_routable_agents()


def get_all_agent_names() -> List[str]:
    """获取所有 Agent 名称的便捷函数"""
    return AgentRegistry.get_agent_names()


def register_new_agent(name: str, description: str, tools: List[str], 
                      use_cases: List[str]) -> bool:
    """
    注册新 Agent 的便捷函数
    
    Args:
        name: Agent 名称
        description: Agent 描述
        tools: 工具列表
        use_cases: 使用场景列表
        
    Returns:
        是否注册成功
    """
    try:
        capability = AgentCapability(
            name=name,
            description=description,
            tools=tools,
            use_cases=use_cases
        )
        AgentRegistry.register_agent(capability)
        return True
    except Exception as e:
        logger.error(f"注册 Agent 失败: {e}")
        return False


# 初始化时打印注册表
if __name__ == "__main__":
    AgentRegistry.print_registry()
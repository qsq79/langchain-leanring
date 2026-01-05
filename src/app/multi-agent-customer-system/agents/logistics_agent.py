#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物流查询智能体（Agent B）- 基于 AutoGen
负责查询物流跟踪信息
"""

from typing import Dict, Any

from autogen_agentchat.agents import AssistantAgent
from core.logger import get_logger
from config.settings import settings
from tools.autogen_tools import (
    query_logistics_tool,
    generate_logistics_summary,
    get_model_client
)

logger = get_logger(__name__)


class LogisticsAgent:
    """物流查询智能体 - 基于 AutoGen"""

    def __init__(self, name: str = "logistics_agent"):
        """
        初始化物流查询智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.role = "物流查询专家"
        self.description = (
            "你是物流查询专家，专门负责查询和跟踪订单的物流信息。"
            "你可以查询物流状态、当前位置、预计送达时间和完整的物流轨迹。"
            "当用户询问物流、配送、快递相关的任何问题时，使用提供的工具函数查询物流信息。"
        )
        
        # 创建 AutoGen AssistantAgent
        model_client = get_model_client(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE,
            model=settings.MODEL_NAME
        )
        
        self.agent = AssistantAgent(
            name=self.name,
            system_message=self.description,
            model_client=model_client,
            tools=[query_logistics_tool, generate_logistics_summary]
        )

        logger.info(f"{self.name} 初始化完成 - {self.role} (基于 AutoGen)")

    async def query_logistics(self, order_id: str) -> Dict[str, Any]:
        """
        查询物流信息

        Args:
            order_id: 订单编号

        Returns:
            物流查询结果
        """
        logger.info(f"[{self.name}] 开始查询物流: {order_id}")

        try:
            # 直接调用工具函数获取数据
            tool_result = query_logistics_tool(order_id)

            # 构建结果
            result = {
                "success": tool_result.get("success", False),
                "order_id": order_id,
                "logistics_info": tool_result.get("logistics_info"),
                "error": tool_result.get("error"),
                "agent": self.name,
                "agent_role": self.role
            }

            logger.info(f"[{self.name}] 物流查询完成: {order_id}, 成功: {result['success']}")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] 物流查询异常: {e}")
            return {
                "success": False,
                "order_id": order_id,
                "error": f"查询失败: {str(e)}",
                "logistics_info": None,
                "agent": self.name
            }

    def _parse_logistics_response(self, order_id: str, response: Any) -> Dict[str, Any]:
        """
        解析 AutoGen 智能体的响应
        
        Args:
            order_id: 订单编号
            response: AutoGen 响应
            
        Returns:
            解析后的结果字典
        """
        # 调用工具函数获取实际数据
        tool_result = query_logistics_tool(order_id)
        
        if not tool_result.get("success"):
            return {
                "success": False,
                "order_id": order_id,
                "error": tool_result.get("error", "查询失败"),
                "logistics_info": None,
                "agent_response": str(response) if response else None,
                "agent": self.name
            }
        
        # 生成摘要（如果 AutoGen 返回了摘要就用其返回值，否则重新生成）
        if isinstance(response, dict) and response.get("summary"):
            logistics_summary = response["summary"]
        else:
            logistics_summary = generate_logistics_summary(tool_result["logistics_info"])
        
        return {
            "success": True,
            "order_id": order_id,
            "logistics_info": tool_result["logistics_info"],
            "agent_summary": logistics_summary,
            "agent_response": str(response) if response else None,
            "agent": self.name,
            "agent_role": self.role
        }

    async def process_request(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理查询请求
        
        Args:
            query: 查询请求字典
            
        Returns:
            处理结果字典
        """
        order_id = query.get("order_id")
        
        if not order_id:
            logger.warning(f"[{self.name}] 请求错误：缺少订单编号")
            return {
                "agent": self.name,
                "success": False,
                "error": "缺少订单编号"
            }
        
        # 查询物流
        result = await self.query_logistics(order_id)
        
        logger.info(f"[{self.name}] 处理请求完成: {order_id}")
        return result

    def get_info(self) -> Dict[str, str]:
        """获取智能体信息"""
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description,
            "type": "AutoGen AssistantAgent"
        }

    def get_autogen_agent(self):
        """获取底层的 AutoGen 智能体对象"""
        return self.agent
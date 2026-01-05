#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单查询智能体（Agent A）- 基于 AutoGen
负责查询订单状态信息
"""

from typing import Dict, Any

from autogen_agentchat.agents import AssistantAgent
from core.logger import get_logger
from config.settings import settings
from tools.autogen_tools import (
    query_order_tool,
    generate_order_summary,
    get_model_client
)

logger = get_logger(__name__)


class OrderAgent:
    """订单查询智能体 - 基于 AutoGen"""

    def __init__(self, name: str = "order_agent"):
        """
        初始化订单查询智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.role = "订单查询专家"
        self.description = (
            "你是订单查询专家，专门负责查询和管理订单相关信息。"
            "你可以查询订单状态、支付状态、发货状态、订单金额和商品信息。"
            "当用户询问订单相关的任何问题时，使用提供的工具函数查询订单信息。"
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
            tools=[query_order_tool, generate_order_summary]
        )

        logger.info(f"{self.name} 初始化完成 - {self.role} (基于 AutoGen)")

    async def query_order(self, order_id: str) -> Dict[str, Any]:
        """
        查询订单信息

        Args:
            order_id: 订单编号

        Returns:
            订单查询结果
        """
        logger.info(f"[{self.name}] 开始查询订单: {order_id}")

        try:
            # 直接调用工具函数获取数据
            tool_result = query_order_tool(order_id)

            # 构建结果
            result = {
                "success": tool_result.get("success", False),
                "order_id": order_id,
                "order_info": tool_result.get("order_info"),
                "error": tool_result.get("error"),
                "agent": self.name,
                "agent_role": self.role
            }

            logger.info(f"[{self.name}] 订单查询完成: {order_id}, 成功: {result['success']}")
            return result

        except Exception as e:
            logger.error(f"[{self.name}] 订单查询异常: {e}")
            return {
                "success": False,
                "order_id": order_id,
                "error": f"查询失败: {str(e)}",
                "order_info": None,
                "agent": self.name
            }

    def _parse_order_response(self, order_id: str, response: Any) -> Dict[str, Any]:
        """
        解析 AutoGen 智能体的响应
        
        Args:
            order_id: 订单编号
            response: AutoGen 响应
            
        Returns:
            解析后的结果字典
        """
        # 调用工具函数获取实际数据
        tool_result = query_order_tool(order_id)
        
        if not tool_result.get("success"):
            return {
                "success": False,
                "order_id": order_id,
                "error": tool_result.get("error", "查询失败"),
                "order_info": None,
                "agent_response": str(response) if response else None,
                "agent": self.name
            }
        
        # 生成摘要（如果 AutoGen 返回了摘要就用其返回值，否则重新生成）
        if isinstance(response, dict) and response.get("summary"):
            order_summary = response["summary"]
        else:
            order_summary = generate_order_summary(tool_result["order_info"])
        
        return {
            "success": True,
            "order_id": order_id,
            "order_info": tool_result["order_info"],
            "agent_summary": order_summary,
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
        
        # 查询订单
        result = await self.query_order(order_id)
        
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
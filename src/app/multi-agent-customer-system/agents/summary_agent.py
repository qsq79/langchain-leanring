#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果汇总智能体（Agent C）- 基于 AutoGen
负责整合订单和物流信息，生成用户友好的自然语言回复
"""

from typing import Dict, Any, Optional
from datetime import datetime

from autogen_agentchat.agents import AssistantAgent
from core.logger import get_logger, log_agent_action, log_agent_message
from config.settings import settings
from tools.autogen_tools import (
    generate_order_summary,
    generate_logistics_summary,
    get_model_client
)

logger = get_logger(__name__)


class SummaryAgent:
    """结果汇总智能体 - 基于 AutoGen"""

    def __init__(self, name: str = "summary_agent"):
        """
        初始化结果汇总智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.role = "结果汇总专家"
        self.description = (
            "你是结果汇总专家，负责整合订单查询智能体和物流查询智能体的结果。"
            "你需要分析用户的问题，并根据查询结果生成清晰、友好、专业的回复。"
            "你应该根据用户的查询意图，决定提供哪些信息（订单信息、物流信息或两者都提供）。"
            "使用提供的工具函数来生成订单和物流信息的摘要。"
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
            tools=[generate_order_summary, generate_logistics_summary]
        )

        logger.info(f"{self.name} 初始化完成 - {self.role} (基于 AutoGen)")

    async def summarize_results_autogen(
        self,
        user_query: str,
        order_result: Optional[Dict[str, Any]],
        logistics_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        使用 AutoGen 框架生成回复

        Args:
            user_query: 用户原始查询
            order_result: 订单查询结果
            logistics_result: 物流查询结果

        Returns:
            自然语言回复
        """
        log_agent_action(self.name, "使用模板生成回复")

        try:
            # 构建回复消息（使用模板而不是 AutoGen）
            message = self._build_response_message(user_query, order_result, logistics_result)

            log_agent_action(self.name, "回复生成成功")
            return message

        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            return "抱歉，生成回复时出现了问题，请稍后再试。"

    def _build_response_message(
        self,
        user_query: str,
        order_result: Optional[Dict[str, Any]],
        logistics_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        构建回复消息（使用模板）

        Args:
            user_query: 用户查询
            order_result: 订单结果
            logistics_result: 物流结果

        Returns:
            消息字符串
        """
        # 收集信息
        info_parts = []

        # 处理订单信息
        if order_result:
            if order_result.get('success'):
                order_info = order_result.get('order_info', {})
                info_parts.append(f"📦 订单编号: {order_info.get('order_id', 'N/A')}")
                info_parts.append(f"📊 订单状态: {order_info.get('order_status', 'N/A')}")
                info_parts.append(f"💰 支付状态: {order_info.get('payment_status', 'N/A')}")
                info_parts.append(f"🚚 发货状态: {order_info.get('shipping_status', 'N/A')}")
                info_parts.append(f"💵 订单金额: ¥{order_info.get('total_amount', 0.00):.2f}")

                # 添加商品信息
                items = order_info.get('items', [])
                if items:
                    info_parts.append(f"\n📝 商品清单:")
                    for item in items:
                        info_parts.append(f"   - {item.get('product_name', 'N/A')} x {item.get('quantity', 0)}")
            else:
                info_parts.append(f"❌ 订单查询失败: {order_result.get('error', '未知错误')}")

        # 处理物流信息
        if logistics_result:
            if logistics_result.get('success'):
                logistics_info = logistics_result.get('logistics_info', {})
                if info_parts:
                    info_parts.append("\n")
                info_parts.append(f"🚚 物流状态: {logistics_info.get('logistics_status', 'N/A')}")

                current_location = logistics_info.get('current_location', 'N/A')
                if current_location and current_location != 'N/A':
                    info_parts.append(f"📍 当前位置: {current_location}")

                estimated_delivery = logistics_info.get('estimated_delivery', 'N/A')
                if estimated_delivery and estimated_delivery != 'N/A':
                    info_parts.append(f"📅 预计送达: {estimated_delivery}")

                # 添加物流轨迹
                tracking_history = logistics_info.get('tracking_history', [])
                if tracking_history:
                    info_parts.append(f"\n📋 最近物流更新:")
                    for track in tracking_history[-3:]:  # 只显示最近3条
                        info_parts.append(f"   {track.get('time', 'N/A')} - {track.get('status', 'N/A')}")
            else:
                if info_parts:
                    info_parts.append("\n")
                info_parts.append(f"❌ 物流查询失败: {logistics_result.get('error', '未知错误')}")

        # 构建完整回复
        if not info_parts:
            return "抱歉，没有找到相关信息。请检查订单编号是否正确。"

        response = "\n".join(info_parts)
        return response

    async def summarize_results(
        self,
        user_query: str,
        order_result: Optional[Dict[str, Any]] = None,
        logistics_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        汇总查询结果并生成回复
        
        Args:
            user_query: 用户原始查询
            order_result: 订单查询结果
            logistics_result: 物流查询结果
            
        Returns:
            汇总结果字典
        """
        log_agent_action(self.name, "开始汇总结果")
        
        # 从订单查询智能体接收结果
        if order_result:
            log_agent_message(
                "订单查询智能体",
                self.name,
                "RESULT_RECEIVE",
                f"接收订单查询结果: {order_result.get('order_id', 'N/A')}"
            )
        
        # 从物流查询智能体接收结果
        if logistics_result:
            log_agent_message(
                "物流查询智能体",
                self.name,
                "RESULT_RECEIVE",
                f"接收物流查询结果: {logistics_result.get('order_id', 'N/A')}"
            )
        
        # 生成回复
        try:
            response = await self.summarize_results_autogen(
                user_query, order_result, logistics_result
            )
            
            log_agent_action(self.name, "汇总完成，生成回复成功")
            
            return {
                "agent": self.name,
                "agent_role": self.role,
                "success": True,
                "order_result": order_result,
                "logistics_result": logistics_result,
                "response": response,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成回复失败: {e}")
            error_response = "抱歉，生成回复时出现了问题，请稍后再试。"
            
            return {
                "agent": self.name,
                "agent_role": self.role,
                "success": False,
                "order_result": order_result,
                "logistics_result": logistics_result,
                "response": error_response,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }

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
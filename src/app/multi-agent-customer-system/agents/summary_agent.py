#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果汇总智能体（Agent C）
负责整合订单和物流信息，生成用户友好的自然语言回复
"""

from typing import Dict, Any, Optional
from datetime import datetime

from core.logger import get_logger, log_agent_action, log_agent_message
from config.settings import settings

logger = get_logger(__name__)


class SummaryAgent:
    """结果汇总智能体"""

    def __init__(self, name: str = "Agent C"):
        """
        初始化结果汇总智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.role = "结果汇总智能体"
        self.description = "负责整合订单和物流信息，生成用户友好的自然语言回复"
        
        # 初始化 OpenAI 客户端（如果需要使用）
        self.use_openai = bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY != "your-openai-api-key-here")
        
        if self.use_openai:
            try:
                import openai
                self.client = openai.AsyncOpenAI(
                    api_key=settings.OPENAI_API_KEY,
                    base_url=settings.OPENAI_API_BASE
                )
                logger.info(f"{self.name} 初始化完成 - 使用 OpenAI API")
            except (ImportError, Exception) as e:
                logger.warning(f"OpenAI 初始化失败: {e}，将使用规则生成回复")
                self.use_openai = False
        else:
            logger.info(f"{self.name} 初始化完成 - 使用规则生成回复")

    async def generate_response_openai(
        self,
        user_query: str,
        order_result: Optional[Dict[str, Any]],
        logistics_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        使用 OpenAI API 生成回复
        
        Args:
            user_query: 用户原始查询
            order_result: 订单查询结果
            logistics_result: 物流查询结果
            
        Returns:
            自然语言回复
        """
        log_agent_action(self.name, "使用 OpenAI API 生成回复")
        
        try:
            # 构建提示词
            prompt = self._build_prompt(user_query, order_result, logistics_result)
            
            # 调用 OpenAI API
            response = await self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": "你是一个专业的客服助手，负责整合订单和物流信息，向用户提供清晰、友好的回复。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS
            )
            
            reply = response.choices[0].message.content.strip()
            
            log_agent_action(self.name, "OpenAI API 生成成功")
            return reply
            
        except Exception as e:
            logger.error(f"OpenAI API 调用失败: {e}")
            log_agent_action(self.name, "OpenAI API 失败，回退到规则生成")
            # 回退到规则生成
            return self._generate_response_rule_based(user_query, order_result, logistics_result)

    def _build_prompt(
        self,
        user_query: str,
        order_result: Optional[Dict[str, Any]],
        logistics_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        构建 OpenAI API 提示词
        
        Args:
            user_query: 用户查询
            order_result: 订单结果
            logistics_result: 物流结果
            
        Returns:
            提示词字符串
        """
        prompt_parts = [
            f"用户查询: {user_query}\n"
        ]
        
        if order_result and order_result.get('success'):
            order_info = order_result.get('order_info', {})
            order_summary = order_result.get('agent_summary', '')
            prompt_parts.append(f"\n订单信息:\n{order_summary}\n")
        else:
            prompt_parts.append("\n订单信息: 查询失败或无相关信息\n")
        
        if logistics_result and logistics_result.get('success'):
            logistics_info = logistics_result.get('logistics_info', {})
            logistics_summary = logistics_result.get('agent_summary', '')
            prompt_parts.append(f"\n物流信息:\n{logistics_summary}\n")
        else:
            prompt_parts.append("\n物流信息: 查询失败或无相关信息\n")
        
        prompt_parts.append(
            "\n请基于以上信息，生成一个清晰、友好、专业的回复，直接回答用户的问题。"
        )
        
        return ''.join(prompt_parts)

    def _generate_response_rule_based(
        self,
        user_query: str,
        order_result: Optional[Dict[str, Any]],
        logistics_result: Optional[Dict[str, Any]]
    ) -> str:
        """
        基于规则生成回复
        
        Args:
            user_query: 用户查询
            order_result: 订单结果
            logistics_result: 物流结果
            
        Returns:
            自然语言回复
        """
        log_agent_action(self.name, "使用规则生成回复")
        
        # 提取订单编号
        order_id = None
        if order_result:
            order_id = order_result.get('order_id')
        elif logistics_result:
            order_id = logistics_result.get('order_id')
        
        if order_id:
            reply_parts = [f"关于订单 {order_id}：\n\n"]
        else:
            reply_parts = ["查询结果：\n\n"]
        
        # 添加订单信息
        if order_result and order_result.get('success'):
            order_info = order_result.get('order_info', {})
            order_status = order_info.get('order_status', '未知')
            payment_status = order_info.get('payment_status', '未知')
            shipping_status = order_info.get('shipping_status', '未知')
            
            reply_parts.append(
                f"📦 订单状态：{order_status}\n"
                f"💳 支付状态：{payment_status}\n"
                f"🚚 发货状态：{shipping_status}\n"
            )
            
            # 根据订单状态提供建议
            if "待发货" in order_status and "已支付" in payment_status:
                reply_parts.append("\n您的订单已完成支付，商家正在准备发货中，请您耐心等待。\n")
            elif "待支付" in payment_status:
                reply_parts.append("\n您的订单尚未支付，请尽快完成支付以便商家发货。\n")
            elif "已取消" in order_status:
                reply_parts.append("\n您的订单已取消。\n")
            elif "已完成" in order_status:
                reply_parts.append("\n您的订单已完成。\n")
        elif order_result:
            reply_parts.append(f"❌ 订单查询失败：{order_result.get('error', '未知错误')}\n")
        else:
            reply_parts.append("❌ 未查询到订单信息\n")
        
        # 添加物流信息
        if logistics_result and logistics_result.get('success'):
            logistics_info = logistics_result.get('logistics_info', {})
            logistics_status = logistics_info.get('logistics_status', '未知')
            current_location = logistics_info.get('current_location', '未知')
            estimated_delivery = logistics_info.get('estimated_delivery', '未知')
            
            if current_location and current_location != '未知':
                reply_parts.append(
                    f"\n🚄 物流状态：{logistics_status}\n"
                    f"📍 当前位置：{current_location}\n"
                )
                
                if estimated_delivery and estimated_delivery != '未知':
                    reply_parts.append(f"⏰ 预计送达：{estimated_delivery}\n")
                
                # 添加物流轨迹
                tracking_history = logistics_info.get('tracking_history', [])
                if len(tracking_history) > 1:
                    latest = tracking_history[-1]
                    reply_parts.append(
                        f"\n最新更新：{latest.get('time', '')} - {latest.get('status', '')} @ {latest.get('location', '')}\n"
                    )
            elif logistics_status == "未发货":
                reply_parts.append(f"\n📭 物流状态：{logistics_status}\n订单尚未发货，暂无物流信息。\n")
            else:
                reply_parts.append(f"\n📭 物流状态：{logistics_status}\n")
        elif logistics_result:
            reply_parts.append(f"❌ 物流查询失败：{logistics_result.get('error', '未知错误')}\n")
        else:
            # 如果不是物流相关查询，可能不需要物流信息
            if "物流" in user_query or "快递" in user_query or "配送" in user_query:
                reply_parts.append("❌ 未查询到物流信息\n")
        
        # 如果都查询失败
        if (not order_result or not order_result.get('success')) and \
           (not logistics_result or not logistics_result.get('success')):
            reply_parts.append("\n无法获取到相关信息，请检查订单编号是否正确或稍后再试。\n")
        
        return ''.join(reply_parts)

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
            if self.use_openai:
                response = await self.generate_response_openai(
                    user_query, order_result, logistics_result
                )
            else:
                response = self._generate_response_rule_based(
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
            "use_openai": str(self.use_openai)
        }
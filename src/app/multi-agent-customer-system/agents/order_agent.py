#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单查询智能体（Agent A）
负责查询订单状态信息
"""

import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass

from core.logger import get_logger, log_agent_action, log_agent_message
from services.mock_data import order_data
from services.retry_mechanism import RetryMechanism
from config.settings import settings

logger = get_logger(__name__)


@dataclass
class OrderQueryResult:
    """订单查询结果"""
    success: bool
    order_id: str
    order_info: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    retry_attempts: int = 0


class OrderAgent:
    """订单查询智能体"""

    def __init__(self, name: str = "Agent A"):
        """
        初始化订单查询智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.role = "订单查询智能体"
        self.description = "负责查询订单的详细状态信息"
        self.retry_mechanism = RetryMechanism()
        
        logger.info(f"{self.name} 初始化完成 - {self.role}")

    async def query_order(self, order_id: str) -> OrderQueryResult:
        """
        查询订单信息
        
        Args:
            order_id: 订单编号
            
        Returns:
            订单查询结果
        """
        log_agent_action(self.name, "开始查询订单", f"订单编号: {order_id}")
        
        try:
            # 记录向数据存储发送请求
            log_agent_message(
                self.name,
                "数据存储",
                "DATA_REQUEST",
                f"查询订单 {order_id}"
            )
            
            # 获取订单数据（带重试机制）
            async def fetch_order():
                order_info = order_data.get_order(order_id)
                if order_info is None:
                    logger.warning(f"订单不存在: {order_id}")
                    raise ValueError(f"订单不存在: {order_id}")
                return order_info
            
            order_info = await self.retry_mechanism.async_execute_with_retry(fetch_order)
            
            # 记录数据存储响应
            if settings.SHOW_API_LOGS:
                log_agent_message(
                    "数据存储",
                    self.name,
                    "DATA_RESPONSE",
                    f"成功获取订单信息: {order_id}"
                )
            
            log_agent_action(self.name, "查询成功", f"订单 {order_id}")
            
            return OrderQueryResult(
                success=True,
                order_id=order_id,
                order_info=order_info
            )
            
        except ValueError as e:
            log_agent_action(self.name, "查询失败", f"订单不存在: {order_id}")
            return OrderQueryResult(
                success=False,
                order_id=order_id,
                order_info=None,
                error_message=str(e)
            )
            
        except Exception as e:
            log_agent_action(self.name, "查询失败", f"未知错误: {str(e)}")
            return OrderQueryResult(
                success=False,
                order_id=order_id,
                order_info=None,
                error_message=f"查询失败: {str(e)}"
            )

    def get_order_summary(self, order_info: Dict[str, Any]) -> str:
        """
        生成订单信息摘要
        
        Args:
            order_info: 订单信息字典
            
        Returns:
            订单摘要字符串
        """
        if not order_info:
            return "无订单信息"
        
        summary = f"""订单信息摘要:
- 订单编号: {order_info.get('order_id', 'N/A')}
- 创建时间: {order_info.get('created_time', 'N/A')}
- 订单状态: {order_info.get('order_status', 'N/A')}
- 支付状态: {order_info.get('payment_status', 'N/A')}
- 发货状态: {order_info.get('shipping_status', 'N/A')}
- 订单金额: ¥{order_info.get('total_amount', 0.00):.2f}
- 商品数量: {len(order_info.get('items', []))} 件"""
        
        return summary

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
            log_agent_action(self.name, "请求错误", "缺少订单编号")
            return {
                "agent": self.name,
                "success": False,
                "error": "缺少订单编号"
            }
        
        # 查询订单
        result = await self.query_order(order_id)
        
        # 准备响应
        response = {
            "agent": self.name,
            "agent_role": self.role,
            "success": result.success,
            "order_id": result.order_id,
            "order_info": result.order_info,
            "error": result.error_message,
            "agent_summary": self.get_order_summary(result.order_info) if result.success else None
        }
        
        # 记录向结果汇总智能体发送结果
        log_agent_message(
            self.name,
            "结果汇总智能体",
            "RESULT_SEND",
            f"发送订单查询结果: {order_id}"
        )
        
        return response

    def get_info(self) -> Dict[str, str]:
        """获取智能体信息"""
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description
        }
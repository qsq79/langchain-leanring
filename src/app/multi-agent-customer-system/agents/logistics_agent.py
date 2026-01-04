#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物流查询智能体（Agent B）
负责查询物流跟踪信息
"""

import httpx
from typing import Dict, Any, Optional
from dataclasses import dataclass

from core.logger import get_logger, log_agent_action, log_agent_message
from services.mock_data import logistics_data
from services.retry_mechanism import RetryMechanism
from config.settings import settings

logger = get_logger(__name__)


@dataclass
class LogisticsQueryResult:
    """物流查询结果"""
    success: bool
    order_id: str
    logistics_info: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    retry_attempts: int = 0


class LogisticsAgent:
    """物流查询智能体"""

    def __init__(self, name: str = "Agent B"):
        """
        初始化物流查询智能体
        
        Args:
            name: 智能体名称
        """
        self.name = name
        self.role = "物流查询智能体"
        self.description = "负责查询订单的物流跟踪信息"
        self.retry_mechanism = RetryMechanism()
        
        logger.info(f"{self.name} 初始化完成 - {self.role}")

    async def query_logistics(self, order_id: str) -> LogisticsQueryResult:
        """
        查询物流信息
        
        Args:
            order_id: 订单编号
            
        Returns:
            物流查询结果
        """
        log_agent_action(self.name, "开始查询物流", f"订单编号: {order_id}")
        
        try:
            # 记录向数据存储发送请求
            log_agent_message(
                self.name,
                "数据存储",
                "DATA_REQUEST",
                f"查询物流 {order_id}"
            )
            
            # 获取物流数据（带重试机制）
            async def fetch_logistics():
                logistics_info = logistics_data.get_logistics(order_id)
                if logistics_info is None:
                    logger.warning(f"物流信息不存在: {order_id}")
                    raise ValueError(f"物流信息不存在: {order_id}")
                return logistics_info
            
            logistics_info = await self.retry_mechanism.async_execute_with_retry(fetch_logistics)
            
            # 记录数据存储响应
            if settings.SHOW_API_LOGS:
                log_agent_message(
                    "数据存储",
                    self.name,
                    "DATA_RESPONSE",
                    f"成功获取物流信息: {order_id}"
                )
            
            log_agent_action(self.name, "查询成功", f"物流 {order_id}")
            
            return LogisticsQueryResult(
                success=True,
                order_id=order_id,
                logistics_info=logistics_info
            )
            
        except ValueError as e:
            log_agent_action(self.name, "查询失败", f"物流信息不存在: {order_id}")
            return LogisticsQueryResult(
                success=False,
                order_id=order_id,
                logistics_info=None,
                error_message=str(e)
            )
            
        except Exception as e:
            log_agent_action(self.name, "查询失败", f"未知错误: {str(e)}")
            return LogisticsQueryResult(
                success=False,
                order_id=order_id,
                logistics_info=None,
                error_message=f"查询失败: {str(e)}"
            )

    def get_logistics_summary(self, logistics_info: Dict[str, Any]) -> str:
        """
        生成物流信息摘要
        
        Args:
            logistics_info: 物流信息字典
            
        Returns:
            物流摘要字符串
        """
        if not logistics_info:
            return "无物流信息"
        
        summary = f"""物流信息摘要:
- 订单编号: {logistics_info.get('order_id', 'N/A')}
- 物流状态: {logistics_info.get('logistics_status', 'N/A')}
- 当前位置: {logistics_info.get('current_location', 'N/A')}
- 预计送达: {logistics_info.get('estimated_delivery', 'N/A')}
- 物流轨迹: {len(logistics_info.get('tracking_history', []))} 条记录"""
        
        # 添加最近的物流轨迹
        tracking_history = logistics_info.get('tracking_history', [])
        if tracking_history:
            latest = tracking_history[-1]
            summary += f"\n- 最新状态: {latest.get('time', 'N/A')} - {latest.get('status', 'N/A')} @ {latest.get('location', 'N/A')}"
        
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
        
        # 查询物流
        result = await self.query_logistics(order_id)
        
        # 准备响应
        response = {
            "agent": self.name,
            "agent_role": self.role,
            "success": result.success,
            "order_id": result.order_id,
            "logistics_info": result.logistics_info,
            "error": result.error_message,
            "agent_summary": self.get_logistics_summary(result.logistics_info) if result.success else None
        }
        
        # 记录向结果汇总智能体发送结果
        log_agent_message(
            self.name,
            "结果汇总智能体",
            "RESULT_SEND",
            f"发送物流查询结果: {order_id}"
        )
        
        return response

    def get_info(self) -> Dict[str, str]:
        """获取智能体信息"""
        return {
            "name": self.name,
            "role": self.role,
            "description": self.description
        }
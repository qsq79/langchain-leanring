#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AutoGen 智能体工具函数
为 AutoGen 智能体提供可调用的工具函数
"""

from typing import Dict, Any, Optional
import asyncio

from core.logger import get_logger
from services.mock_data import order_data, logistics_data
from autogen_ext.models.openai import OpenAIChatCompletionClient

logger = get_logger(__name__)


def query_order_tool(order_id: str) -> Dict[str, Any]:
    """
    查询订单信息的工具函数
    
    Args:
        order_id: 订单编号
        
    Returns:
        订单信息字典
    """
    logger.info(f"[ Tool ] 查询订单: {order_id}")
    
    try:
        order_info = order_data.get_order(order_id)
        
        if order_info is None:
            logger.warning(f"[ Tool ] 订单不存在: {order_id}")
            return {
                "success": False,
                "order_id": order_id,
                "error": f"订单 {order_id} 不存在",
                "order_info": None
            }
        
        logger.info(f"[ Tool ] 订单查询成功: {order_id}")
        return {
            "success": True,
            "order_id": order_id,
            "error": None,
            "order_info": order_info
        }
        
    except Exception as e:
        logger.error(f"[ Tool ] 订单查询异常: {e}")
        return {
            "success": False,
            "order_id": order_id,
            "error": f"查询失败: {str(e)}",
            "order_info": None
        }


def query_logistics_tool(order_id: str) -> Dict[str, Any]:
    """
    查询物流信息的工具函数
    
    Args:
        order_id: 订单编号
        
    Returns:
        物流信息字典
    """
    logger.info(f"[ Tool ] 查询物流: {order_id}")
    
    try:
        logistics_info = logistics_data.get_logistics(order_id)
        
        if logistics_info is None:
            logger.warning(f"[ Tool ] 物流信息不存在: {order_id}")
            return {
                "success": False,
                "order_id": order_id,
                "error": f"订单 {order_id} 的物流信息不存在",
                "logistics_info": None
            }
        
        logger.info(f"[ Tool ] 物流查询成功: {order_id}")
        return {
            "success": True,
            "order_id": order_id,
            "error": None,
            "logistics_info": logistics_info
        }
        
    except Exception as e:
        logger.error(f"[ Tool ] 物流查询异常: {e}")
        return {
            "success": False,
            "order_id": order_id,
            "error": f"查询失败: {str(e)}",
            "logistics_info": None
        }


def get_all_orders_tool() -> Dict[str, Any]:
    """
    获取所有订单信息的工具函数
    
    Returns:
        所有订单信息列表
    """
    logger.info("[ Tool ] 获取所有订单")
    
    try:
        all_orders = order_data.get_all_orders()
        
        logger.info(f"[ Tool ] 成功获取 {len(all_orders)} 个订单")
        return {
            "success": True,
            "count": len(all_orders),
            "orders": all_orders,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"[ Tool ] 获取所有订单异常: {e}")
        return {
            "success": False,
            "count": 0,
            "orders": [],
            "error": f"获取失败: {str(e)}"
        }


def generate_order_summary(order_info: Dict[str, Any]) -> str:
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


def generate_logistics_summary(logistics_info: Dict[str, Any]) -> str:
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


# 为不同智能体定义的工具集
ORDER_AGENT_TOOLS = [query_order_tool]
LOGISTICS_AGENT_TOOLS = [query_logistics_tool]
SUMMARY_AGENT_TOOLS = [generate_order_summary, generate_logistics_summary]


def get_model_client(api_key: str, base_url: str, model: str = "gpt-4"):
    """
    获取 AutoGen 的 Model Client
    
    Args:
        api_key: OpenAI API 密钥
        base_url: OpenAI API 基础 URL
        model: 模型名称
        
    Returns:
        Model Client 对象
    """
    return OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
        base_url=base_url,
        temperature=0.7,
        max_tokens=2000,
    )
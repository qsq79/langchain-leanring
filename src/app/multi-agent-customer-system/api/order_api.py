#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单查询 API 服务
使用 FastAPI 实现模拟的内部系统接口
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from core.logger import get_logger
from services.mock_data import order_data
from services.retry_mechanism import RetryMechanism

logger = get_logger(__name__)

# 创建 FastAPI 应用
order_app = FastAPI(title="订单查询 API", version="1.0.0")

# 初始化重试机制
retry_mechanism = RetryMechanism()


class OrderResponse(BaseModel):
    """订单响应模型"""
    order_id: str
    created_time: str
    order_status: str
    payment_status: str
    shipping_status: str
    total_amount: float
    items: list


@order_app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "order-api", "timestamp": datetime.now().isoformat()}


@order_app.get("/api/v1/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str):
    """
    获取订单信息
    
    Args:
        order_id: 订单编号
        
    Returns:
        订单详细信息
    """
    logger.info(f"[订单API] 查询订单: {order_id}")
    
    try:
        # 使用重试机制获取订单数据
        async def fetch_order():
            order_info = order_data.get_order(order_id)
            if order_info is None:
                logger.warning(f"订单不存在: {order_id}")
                raise ValueError(f"订单不存在: {order_id}")
            return OrderResponse(**order_info)
        
        order = await retry_mechanism.async_execute_with_retry(fetch_order)
        logger.info(f"[订单API] 成功获取订单: {order_id}")
        return order
        
    except ValueError as e:
        # 订单不存在，不重试
        logger.error(f"[订单API] 订单不存在: {order_id}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        logger.error(f"[订单API] 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询订单失败: {str(e)}")


@order_app.get("/api/v1/orders")
async def list_orders():
    """
    获取所有订单列表
    
    Returns:
        所有订单信息列表
    """
    logger.info("[订单API] 获取所有订单列表")
    
    try:
        orders = order_data.get_all_orders()
        logger.info(f"[订单API] 成功获取 {len(orders)} 个订单")
        return {"orders": orders, "count": len(orders)}
        
    except Exception as e:
        logger.error(f"[订单API] 获取订单列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取订单列表失败: {str(e)}")
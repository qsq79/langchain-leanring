#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
物流查询 API 服务
使用 FastAPI 实现模拟的内部系统接口
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.logger import get_logger
from services.mock_data import logistics_data
from services.retry_mechanism import RetryMechanism

logger = get_logger(__name__)

# 创建 FastAPI 应用
logistics_app = FastAPI(title="物流查询 API", version="1.0.0")

# 初始化重试机制
retry_mechanism = RetryMechanism()


class TrackingHistoryItem(BaseModel):
    """物流轨迹项"""
    time: str
    status: str
    location: str


class LogisticsResponse(BaseModel):
    """物流响应模型"""
    order_id: str
    logistics_status: str = Field(..., description="物流状态")
    current_location: str = Field(None, description="当前位置")
    estimated_delivery: str = Field(None, description="预计送达时间")
    tracking_history: list[TrackingHistoryItem] = Field(..., description="物流跟踪历史")


@logistics_app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "service": "logistics-api", "timestamp": datetime.now().isoformat()}


@logistics_app.get("/api/v1/logistics/{order_id}", response_model=LogisticsResponse)
async def get_logistics(order_id: str):
    """
    获取物流信息
    
    Args:
        order_id: 订单编号
        
    Returns:
        物流详细信息
    """
    logger.info(f"[物流API] 查询物流: {order_id}")
    
    try:
        # 使用重试机制获取物流数据
        async def fetch_logistics():
            logistics_info = logistics_data.get_logistics(order_id)
            if logistics_info is None:
                logger.warning(f"物流信息不存在: {order_id}")
                raise ValueError(f"物流信息不存在: {order_id}")
            return LogisticsResponse(**logistics_info)
        
        logistics = await retry_mechanism.async_execute_with_retry(fetch_logistics)
        logger.info(f"[物流API] 成功获取物流信息: {order_id}")
        return logistics
        
    except ValueError as e:
        # 物流信息不存在，不重试
        logger.error(f"[物流API] 物流信息不存在: {order_id}")
        raise HTTPException(status_code=404, detail=str(e))
        
    except Exception as e:
        logger.error(f"[物流API] 查询失败: {e}")
        raise HTTPException(status_code=500, detail=f"查询物流信息失败: {str(e)}")


@logistics_app.get("/api/v1/logistics")
async def list_logistics():
    """
    获取所有物流信息列表
    
    Returns:
        所有物流信息列表
    """
    logger.info("[物流API] 获取所有物流信息列表")
    
    try:
        logistics_list = logistics_data.get_all_logistics()
        logger.info(f"[物流API] 成功获取 {len(logistics_list)} 条物流信息")
        return {"logistics": logistics_list, "count": len(logistics_list)}
        
    except Exception as e:
        logger.error(f"[物流API] 获取物流列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取物流列表失败: {str(e)}")
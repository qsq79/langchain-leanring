#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一 API 服务器
整合订单查询和物流查询 API
"""

import sys
import asyncio
from pathlib import Path
import uvicorn
from fastapi import FastAPI
from contextlib import asynccontextmanager

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
from api.order_api import order_app
from api.logistics_api import logistics_app
from config.settings import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("=" * 60)
    logger.info("启动多智能体客服系统 API 服务")
    logger.info("=" * 60)
    yield
    logger.info("关闭多智能体客服系统 API 服务")


# 创建主应用
app = FastAPI(
    title="多智能体客服系统 API",
    description="提供订单查询和物流查询的模拟内部系统接口",
    version="1.0.0",
    lifespan=lifespan
)

# 挂载子应用
app.mount("/orders", order_app)
app.mount("/logistics", logistics_app)


@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "多智能体客服系统 API",
        "version": "1.0.0",
        "endpoints": {
            "orders": "/orders",
            "logistics": "/logistics",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """健康检查"""
    return {
        "status": "ok",
        "service": "multi-agent-customer-system",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    """直接运行此文件时启动服务器"""
    import uvicorn
    
    logger.info("=" * 60)
    logger.info("启动 FastAPI 服务器")
    logger.info(f"监听地址: {settings.API_HOST}:{settings.API_PORT}")
    logger.info(f"API 文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    logger.info("=" * 60)
    
    uvicorn.run(
        "server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
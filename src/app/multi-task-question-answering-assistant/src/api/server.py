#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI Web 服务
提供 RESTful API 接口
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, constr
from typing import Optional, Dict, Any
import uvicorn

from src.core.logger import logger
from src.config.settings import settings
from src.agents.qa_agent import create_qa_agent


# ========== 请求/响应模型 ==========

class QueryRequest(BaseModel):
    """查询请求模型"""
    query: constr(min_length=1, max_length=2000) = Field(
        ...,
        description="用户问题",
        examples=["北京今天天气怎么样？"]
    )
    session_id: Optional[str] = Field(
        None,
        description="会话ID，用于多轮对话"
    )


class QueryResponse(BaseModel):
    """查询响应模型"""
    answer: str = Field(..., description="AI回答")
    model: str = Field(..., description="使用的模型")
    tools_used: list[str] = Field(default_factory=list, description="使用的工具")
    session_id: Optional[str] = Field(None, description="会话ID")


class SystemInfo(BaseModel):
    """系统信息"""
    app_name: str = Field(..., description="应用名称")
    version: str = Field(..., description="版本号")
    model: str = Field(..., description="使用的模型")
    tools: list[str] = Field(..., description="可用工具")


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(None, description="详细说明")


# ========== FastAPI 应用 ==========

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 LangChain 1.x 的多任务智能问答助手 API"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应该限制具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局 Agent 实例
qa_agent = None


@app.on_event("startup")
async def startup_event():
    """应用启动事件"""
    global qa_agent

    logger.info("=" * 60)
    logger.info(f"启动 {settings.APP_NAME} API 服务")
    logger.info("=" * 60)

    try:
        # 创建 Agent
        qa_agent = create_qa_agent()

        agent_info = qa_agent.get_agent_info()
        logger.info(f"✅ Agent 初始化成功")
        logger.info(f"   模型: {agent_info['model']}")
        logger.info(f"   工具: {', '.join(agent_info['tools'])}")

    except Exception as e:
        logger.error(f"❌ Agent 初始化失败: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭事件"""
    logger.info("关闭 API 服务...")


# ========== API 路由 ==========

@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        "message": f"欢迎使用 {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/info", response_model=SystemInfo)
async def get_system_info():
    """获取系统信息"""
    if not qa_agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent 未初始化"
        )

    agent_info = qa_agent.get_agent_info()
    return SystemInfo(
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        model=agent_info["model"],
        tools=agent_info["tools"]
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    问答接口

    Args:
        request: 查询请求

    Returns:
        QueryResponse: 查询响应
    """
    if not qa_agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent 未初始化"
        )

    try:
        logger.info(f"收到查询: {request.query}")

        # 调用 Agent
        response = await qa_agent.ainvoke(request.query)

        # 解析响应
        answer = response.get("output", "抱歉，我没有理解您的问题。")

        logger.info(f"查询成功: {request.query[:50]}...")

        return QueryResponse(
            answer=answer,
            model=qa_agent.model_name,
            session_id=request.session_id
        )

    except Exception as e:
        logger.error(f"查询失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询处理失败: {str(e)}"
        )


@app.get("/tools")
async def list_tools():
    """列出可用工具"""
    if not qa_agent:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent 未初始化"
        )

    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in qa_agent.tools
        ]
    }


# ========== 主函数 ==========

def start_server(host: str = "0.0.0.0", port: int = 8000, reload: bool = False):
    """
    启动 FastAPI 服务器

    Args:
        host: 监听地址
        port: 监听端口
        reload: 是否自动重载（开发模式）
    """
    logger.info(f"启动服务器: http://{host}:{port}")

    uvicorn.run(
        "src.api.server:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    # 开发模式启动
    start_server(reload=True)

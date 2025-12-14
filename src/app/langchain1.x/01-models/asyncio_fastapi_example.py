#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
asyncio 和 FastAPI 的关系示例
展示 asyncio 基础和 FastAPI 如何使用 asyncio
"""

import asyncio
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
import time
from typing import List

# 设置环境变量（复用之前的配置）
import os
import sys
from dotenv import load_dotenv
import re

os.environ['PYTHONIOENCODING'] = 'utf-8'
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def clean_env_value(value: str) -> str:
    """清理环境变量中的Unicode字符"""
    return re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb"\'\u0060\u00b4]', '', value).strip()

# 设置清理后的环境变量
api_key = clean_env_value(os.getenv("OPENAI_API_KEY", ""))
api_base = clean_env_value(os.getenv("OPENAI_API_BASE", ""))

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
if api_base:
    os.environ["OPENAI_BASE_URL"] = api_base

# ===================================================================
# 1. asyncio 基础示例
# ===================================================================

async def basic_asyncio_example():
    """asyncio 基础使用"""
    print("=== asyncio 基础示例 ===")

    async def say_after(delay, what):
        await asyncio.sleep(delay)
        print(f"{what} (等待了 {delay} 秒)")

    # 顺序执行
    print("顺序执行:")
    start_time = time.time()
    await say_after(1, "Hello")
    await say_after(1, "World")
    sequential_time = time.time() - start_time
    print(f"顺序执行总时间: {sequential_time:.2f}秒\n")

    # 并发执行
    print("并发执行:")
    start_time = time.time()
    task1 = asyncio.create_task(say_after(1, "Hello"))
    task2 = asyncio.create_task(say_after(1, "World"))
    await task1
    await task2
    concurrent_time = time.time() - start_time
    print(f"并发执行总时间: {concurrent_time:.2f}秒\n")

async def langchain_asyncio_example():
    """LangChain 中的 asyncio 使用"""
    print("=== LangChain 异步调用示例 ===")

    # 创建模型
    model = init_chat_model("gpt-3.5-turbo")

    questions = [
        "什么是Python？",
        "什么是JavaScript？",
        "什么是异步编程？"
    ]

    # 顺序调用（同步方式）
    print("顺序调用:")
    start_time = time.time()
    for question in questions:
        response = model.invoke([HumanMessage(content=question)])
        print(f"Q: {question}")
        print(f"A: {response.content[:50]}...")
        print()
    sequential_time = time.time() - start_time
    print(f"顺序调用总时间: {sequential_time:.2f}秒\n")

    # 并发调用（异步方式）
    print("并发调用:")
    start_time = time.time()

    # 创建异步任务
    tasks = [
        model.ainvoke([HumanMessage(content=q)])
        for q in questions
    ]

    # 并发执行所有任务
    results = await asyncio.gather(*tasks)

    for question, result in zip(questions, results):
        print(f"Q: {question}")
        print(f"A: {result.content[:50]}...")
        print()

    concurrent_time = time.time() - start_time
    print(f"并发调用总时间: {concurrent_time:.2f}秒")
    print(f"并发比顺序快 {sequential_time/concurrent_time:.1f}倍\n")

# ===================================================================
# 2. FastAPI 集成示例
# ===================================================================

# 注意：这个示例需要安装 fastapi 和 uvicorn
# pip install fastapi "uvicorn[standard]"

try:
    from fastapi import FastAPI
    from pydantic import BaseModel
    from typing import Optional

    # 定义请求/响应模型
    class ChatRequest(BaseModel):
        message: str
        model: Optional[str] = "gpt-3.5-turbo"

    class ChatResponse(BaseModel):
        response: str
        model: str
        processing_time: float

    # 创建 FastAPI 应用
    app = FastAPI(title="LangChain Chat API", version="1.0.0")

    # 全局模型实例（生产环境建议使用依赖注入）
    model = init_chat_model("gpt-3.5-turbo")

    @app.get("/")
    async def root():
        """根路径"""
        return {"message": "LangChain Chat API", "version": "1.0.0"}

    @app.post("/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """聊天接口 - 异步处理"""
        start_time = time.time()

        # 使用异步调用
        response = await model.ainvoke([
            HumanMessage(content=request.message)
        ])

        processing_time = time.time() - start_time

        return ChatResponse(
            response=response.content,
            model=request.model,
            processing_time=processing_time
        )

    @app.post("/chat/batch")
    async def chat_batch(messages: List[str]):
        """批量聊天接口 - 展示并发处理优势"""
        start_time = time.time()

        # 创建异步任务
        tasks = [
            model.ainvoke([HumanMessage(content=msg)])
            for msg in messages
        ]

        # 并发执行
        results = await asyncio.gather(*tasks)

        processing_time = time.time() - start_time

        return {
            "responses": [result.content for result in results],
            "count": len(messages),
            "processing_time": processing_time,
            "average_time": processing_time / len(messages)
        }

    FASTAPI_AVAILABLE = True

except ImportError:
    print("注意: FastAPI 未安装，跳过 FastAPI 示例")
    print("安装命令: pip install fastapi 'uvicorn[standard]'\n")
    FASTAPI_AVAILABLE = False

# ===================================================================
# 3. 性能对比示例
# ===================================================================

async def performance_comparison():
    """性能对比：同步 vs 异步"""
    print("=== 性能对比：同步 vs 异步 ===")

    model = init_chat_model("gpt-3.5-turbo")
    message = [HumanMessage(content="请用一句话解释什么是人工智能。")]

    # 测试次数
    test_count = 5

    # 同步测试
    print(f"同步调用 {test_count} 次:")
    start_time = time.time()
    for i in range(test_count):
        response = model.invoke(message)
        print(f"  第{i+1}次: {response.content[:30]}...")
    sync_time = time.time() - start_time
    print(f"同步总时间: {sync_time:.2f}秒\n")

    # 异步测试
    print(f"异步调用 {test_count} 次:")
    start_time = time.time()

    tasks = [model.ainvoke(message) for _ in range(test_count)]
    results = await asyncio.gather(*tasks)

    for i, result in enumerate(results):
        print(f"  第{i+1}次: {result.content[:30]}...")

    async_time = time.time() - start_time
    print(f"异步总时间: {async_time:.2f}秒")
    print(f"异步比同步快 {sync_time/async_time:.1f}倍\n")

# ===================================================================
# 4. 实际应用场景示例
# ===================================================================

async def real_world_scenarios():
    """实际应用场景"""
    print("=== 实际应用场景 ===")

    model = init_chat_model("gpt-3.5-turbo")

    # 场景1: 并发处理用户请求
    print("场景1: 并发处理用户请求")
    user_requests = [
        "推荐一部科幻电影",
        "解释量子计算",
        "如何学习编程",
        "健康饮食建议",
        "旅行攻略推荐"
    ]

    async def process_user_request(user_id: int, request: str):
        """处理单个用户请求"""
        response = await model.ainvoke([
            HumanMessage(content=f"用户{user_id}的请求: {request}")
        ])
        return f"用户{user_id}: {response.content[:50]}..."

    start_time = time.time()
    tasks = [
        process_user_request(i, req)
        for i, req in enumerate(user_requests, 1)
    ]
    results = await asyncio.gather(*tasks)
    processing_time = time.time() - start_time

    for result in results:
        print(f"  {result}")
    print(f"处理{len(user_requests)}个用户请求用时: {processing_time:.2f}秒\n")

    # 场景2: 文档分析
    print("场景2: 并发分析多个文档")
    documents = [
        "技术文档: API使用指南",
        "产品文档: 功能介绍",
        "法律文档: 用户协议",
        "营销文档: 产品宣传",
        "培训文档: 新手教程"
    ]

    async def analyze_document(doc: str):
        """分析单个文档"""
        analysis = await model.ainvoke([
            HumanMessage(content=f"请简要分析这个文档的主要内容: {doc}")
        ])
        return f"文档分析: {analysis.content[:60]}..."

    start_time = time.time()
    analysis_tasks = [analyze_document(doc) for doc in documents]
    analysis_results = await asyncio.gather(*analysis_tasks)
    analysis_time = time.time() - start_time

    for result in analysis_results:
        print(f"  {result}")
    print(f"分析{len(documents)}个文档用时: {analysis_time:.2f}秒\n")

# ===================================================================
# 5. 最佳实践建议
# ===================================================================

def best_practices():
    """最佳实践建议"""
    print("=== 最佳实践建议 ===")

    advice = [
        "1. 使用 asyncio 的场景:",
        "   - 需要处理大量 I/O 操作（网络请求、数据库查询）",
        "   - 需要并发处理多个任务",
        "   - 构建 Web API 服务",
        "",
        "2. FastAPI 的优势:",
        "   - 内置异步支持，性能优秀",
        "   - 自动生成 API 文档",
        "   - 类型提示和数据验证",
        "   - 易于与 LangChain 集成",
        "",
        "3. LangChain 异步使用:",
        "   - 所有调用都有对应的异步版本 (invoke -> ainvoke)",
        "   - 使用 asyncio.gather() 进行并发处理",
        "   - 在 FastAPI 中直接使用 async/await",
        "",
        "4. 性能优化:",
        "   - 避免在异步代码中同步阻塞",
        "   - 合理设置并发数量",
        "   - 使用连接池和缓存",
        "",
        "5. 错误处理:",
        "   - 在异步函数中使用 try/except",
        "   - 考虑使用超时和重试机制",
        "   - 监控异步任务的执行状态"
    ]

    for line in advice:
        print(line)
    print()

async def main():
    """主函数"""
    print("asyncio 和 FastAPI 关系示例")
    print("=" * 50)
    print("展示 asyncio 基础和在 LangChain 中的应用")
    print("=" * 50)
    print()

    try:
        # 基础 asyncio 示例
        await basic_asyncio_example()

        # LangChain 异步示例
        await langchain_asyncio_example()

        # 性能对比
        await performance_comparison()

        # 实际应用场景
        await real_world_scenarios()

        # 最佳实践
        best_practices()

        # FastAPI 说明
        if FASTAPI_AVAILABLE:
            print("FastAPI 示例代码已准备就绪!")
            print("要启动 API 服务，请运行:")
            print("uvicorn asyncio_fastapi_example:app --reload")
            print()
            print("API 端点:")
            print("- GET /")
            print("- POST /chat")
            print("- POST /chat/batch")
            print()
        else:
            print("要体验 FastAPI 示例，请先安装:")
            print("pip install fastapi 'uvicorn[standard]'")
            print()

    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索工具模块
集成 Tavily AI 搜索引擎
"""

from typing import List, Dict, Any
from langchain_core.tools import tool

from src.core.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """
    使用 Tavily 搜索引擎搜索网络信息

    Args:
        query: 搜索查询关键词
        max_results: 返回结果数量，默认5条，最多10条

    Returns:
        str: 搜索结果摘要，包含标题、摘要和链接

    Examples:
        >>> search_web("LangChain教程")
        "找到5条关于'LangChain教程'的搜索结果: ..."
    """
    try:
        logger.info(f"网络搜索: {query} (最多{max_results}条结果)")

        # 如果没有配置 Tavily API Key，返回模拟数据
        if not settings.TAVILY_API_KEY or settings.TAVILY_API_KEY == "your-tavily-api-key-here":
            logger.warning(f"未配置Tavily API Key，使用模拟搜索: {query}")
            return _mock_search(query, max_results)

        # 调用 Tavily Search API
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=settings.TAVILY_API_KEY)

            # 执行搜索
            response = client.search(
                query=query,
                max_results=max_results,
                search_depth="basic",  # basic 或 advanced
                include_answer=False,
                include_raw_content=False
            )

            # 格式化结果
            if response.get("results"):
                results = []
                results.append(f"找到 {len(response['results'])} 条关于 '{query}' 的搜索结果:\n")

                for i, item in enumerate(response["results"][:max_results], 1):
                    title = item.get("title", "无标题")
                    content = item.get("content", "")[:150]  # 限制摘要长度
                    url = item.get("url", "")

                    results.append(
                        f"{i}. {title}\n"
                        f"   摘要: {content}...\n"
                        f"   链接: {url}\n"
                    )

                logger.info(f"搜索成功: {query}, 返回{len(response['results'])}条结果")
                return "\n".join(results)
            else:
                logger.warning(f"搜索无结果: {query}")
                return f"未找到关于 '{query}' 的相关信息"

        except ImportError:
            logger.error("未安装 tavily-python 库，请运行: pip install tavily-python")
            return _mock_search(query, max_results)

    except Exception as e:
        logger.error(f"搜索失败: {e}")
        return f"搜索 '{query}' 时出错: {str(e)}"


@tool
def search_news(query: str, days: int = 7) -> str:
    """
    搜索最新新闻

    Args:
        query: 新闻关键词
        days: 搜索最近几天的新闻，默认7天

    Returns:
        str: 新闻搜索结果
    """
    try:
        logger.info(f"新闻搜索: {query} (最近{days}天)")

        if not settings.TAVILY_API_KEY:
            return _mock_news_search(query, days)

        from tavily import TavilyClient

        client = TavilyClient(api_key=settings.TAVILY_API_KEY)

        # 搜索新闻（使用 topic 参数）
        response = client.search(
            query=query,
            max_results=5,
            topic="news",  # 搜索新闻
            days=days
        )

        if response.get("results"):
            results = [f"找到 {len(response['results'])} 条关于 '{query}' 的新闻:\n"]

            for i, item in enumerate(response["results"], 1):
                title = item.get("title", "无标题")
                content = item.get("content", "")[:200]
                url = item.get("url", "")
                date = item.get("publishedDate", "未知日期")

                results.append(
                    f"{i}. {title}\n"
                    f"   时间: {date}\n"
                    f"   摘要: {content}...\n"
                    f"   链接: {url}\n"
                )

            logger.info(f"新闻搜索成功: {query}")
            return "\n".join(results)
        else:
            return f"未找到关于 '{query}' 的相关新闻"

    except Exception as e:
        logger.error(f"新闻搜索失败: {e}")
        return _mock_news_search(query, days)


def _mock_search(query: str, max_results: int = 5) -> str:
    """模拟搜索结果（用于测试）"""
    mock_results = [
        {
            "title": f"{query} - 官方文档",
            "content": f"关于 {query} 的详细介绍和使用指南，包含完整的示例代码和最佳实践。",
            "url": "https://example.com/docs"
        },
        {
            "title": f"{query} 快速入门教程",
            "content": f"{query} 的快速入门指南，适合初学者，包含实战案例。",
            "url": "https://example.com/tutorial"
        },
        {
            "title": f"{query} 在企业中的应用",
            "content": f"深入了解 {query} 在企业级项目中的实际应用和架构设计。",
            "url": "https://example.com/blog"
        }
    ]

    results = [f"找到 {min(max_results, len(mock_results))} 条关于 '{query}' 的搜索结果（模拟数据）:\n"]

    for i, item in enumerate(mock_results[:max_results], 1):
        results.append(
            f"{i}. {item['title']}\n"
            f"   摘要: {item['content']}\n"
            f"   链接: {item['url']}\n"
        )

    return "\n".join(results)


def _mock_news_search(query: str, days: int) -> str:
    """模拟新闻搜索"""
    from datetime import datetime, timedelta

    mock_news = [
        {
            "title": f"{query} 最新技术进展",
            "date": (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d"),
            "content": f"关于 {query} 的最新技术突破和行业动态..."
        },
        {
            "title": f"{query} 在行业中的应用案例",
            "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "content": f"多家企业开始采用 {query} 技术提升效率..."
        }
    ]

    results = [f"找到 {len(mock_news)} 条关于 '{query}' 的新闻（模拟数据）:\n"]

    for i, item in enumerate(mock_news, 1):
        results.append(
            f"{i}. {item['title']}\n"
            f"   时间: {item['date']}\n"
            f"   摘要: {item['content']}\n"
        )

    return "\n".join(results)


if __name__ == "__main__":
    # 测试搜索工具
    print("=" * 60)
    print("搜索工具测试")
    print("=" * 60)

    print("\n1. 网络搜索:")
    print(search_web.invoke({"query": "LangChain教程", "max_results": 3}))

    print("\n2. 新闻搜索:")
    print(search_news.invoke({"query": "人工智能", "days": 7}))

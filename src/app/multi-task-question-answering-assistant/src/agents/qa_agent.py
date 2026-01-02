#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QA Agent 实现
使用 LangChain 1.x 的 create_agent() API
"""

from typing import List, Any, Dict
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_core.tools import BaseTool

from src.core.logger import get_logger
from src.config.settings import settings
from src.tools.weather_tools import get_weather, get_weather_forecast
from src.tools.search_tools import search_web, search_news

logger = get_logger(__name__)


class QAAgent:
    """问答 Agent 系统类"""

    def __init__(self, model_name: str = None):
        """
        初始化 QA Agent

        Args:
            model_name: 模型名称，默认使用配置文件中的模型
        """
        self.model_name = model_name or settings.MODEL_NAME
        self.agent = None
        self.tools = []

        logger.info(f"初始化 QA Agent - 模型: {self.model_name}")

        self._setup_agent()

    def _setup_agent(self):
        """设置 Agent"""
        try:
            # 1. 准备工具
            self.tools = [
                get_weather,
                get_weather_forecast,
                search_web,
                search_news
            ]
            logger.info(f"加载工具: {[tool.name for tool in self.tools]}")

            # 2. 初始化模型
            logger.info(f"初始化模型: {self.model_name}")

            # 设置 OpenAI API 配置（清理 Unicode 字符）
            import os
            import re

            def clean_env_value(value: str) -> str:
                """清理环境变量中的Unicode字符"""
                return re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb"\'\u0060\u00b4]', '', value).strip()

            # 清理并设置 API Key
            api_key = clean_env_value(settings.OPENAI_API_KEY)
            os.environ["OPENAI_API_KEY"] = api_key

            # 清理并设置 API Base（如果不是默认值）
            if settings.OPENAI_API_BASE != "https://api.openai.com/v1":
                api_base = clean_env_value(settings.OPENAI_API_BASE)
                os.environ["OPENAI_BASE_URL"] = api_base

            llm = init_chat_model(
                self.model_name,
                temperature=settings.MODEL_TEMPERATURE,
                max_tokens=settings.MODEL_MAX_TOKENS
            )

            # 3. 创建 Agent（LangChain 1.x 方式）
            system_prompt = """你是一个智能助手，可以帮助用户回答各种问题。

你有以下工具可以使用：
1. get_weather - 查询指定城市的实时天气
2. get_weather_forecast - 查询指定城市的天气预报
3. search_web - 搜索网络信息
4. search_news - 搜索最新新闻

使用指南：
- 当用户询问天气时，使用天气工具
- 当用户需要搜索信息时，使用搜索工具
- 当用户问简单问题时，可以直接回答
- 始终保持友好和专业的态度
- 如果工具调用失败，向用户说明情况

请根据用户的问题选择合适的工具，或者直接回答。"""

            self.agent = create_agent(
                model=llm,
                tools=self.tools,
                system_prompt=system_prompt
            )

            logger.info("✅ QA Agent 创建成功 (LangChain 1.x)")

        except Exception as e:
            logger.error(f"Agent 创建失败: {e}")
            raise

    def invoke(self, user_input: str) -> Dict[str, Any]:
        """
        同步调用 Agent

        Args:
            user_input: 用户输入

        Returns:
            Agent 响应结果
        """
        try:
            logger.info(f"用户输入: {user_input}")

            # LangChain 1.x 标准化消息格式
            messages = [{
                "role": "user",
                "content": user_input
            }]

            response = self.agent.invoke({"messages": messages})

            logger.info(f"Agent 响应: {response}")
            return response

        except Exception as e:
            logger.error(f"Agent 调用失败: {e}")
            return {
                "output": f"抱歉，处理您的问题时出错: {str(e)}"
            }

    async def ainvoke(self, user_input: str) -> Dict[str, Any]:
        """
        异步调用 Agent

        Args:
            user_input: 用户输入

        Returns:
            Agent 响应结果
        """
        try:
            logger.info(f"[异步] 用户输入: {user_input}")

            messages = [{
                "role": "user",
                "content": user_input
            }]

            response = await self.agent.ainvoke({"messages": messages})

            logger.info(f"[异步] Agent 响应: {response}")
            return response

        except Exception as e:
            logger.error(f"[异步] Agent 调用失败: {e}")
            return {
                "output": f"抱歉，处理您的问题时出错: {str(e)}"
            }

    def get_tool_names(self) -> List[str]:
        """获取可用工具列表"""
        return [tool.name for tool in self.tools]

    def get_agent_info(self) -> Dict[str, Any]:
        """获取 Agent 信息"""
        return {
            "model": self.model_name,
            "tools": self.get_tool_names(),
            "temperature": settings.MODEL_TEMPERATURE,
            "max_tokens": settings.MODEL_MAX_TOKENS
        }


def create_qa_agent(model_name: str = None) -> QAAgent:
    """
    创建 QA Agent 实例的工厂函数

    Args:
        model_name: 模型名称，默认使用配置

    Returns:
        QAAgent 实例
    """
    return QAAgent(model_name)


if __name__ == "__main__":
    # 测试 Agent
    print("=" * 60)
    print("QA Agent 测试")
    print("=" * 60)

    # 创建 Agent
    agent = create_qa_agent()

    print("\nAgent 信息:")
    import json
    print(json.dumps(agent.get_agent_info(), indent=2, ensure_ascii=False))

    # 测试查询
    test_queries = [
        "你好，请介绍一下你自己",
        "北京今天天气怎么样？",
        "搜索一下 LangChain 的最新教程"
    ]

    for query in test_queries:
        print(f"\n{'=' * 60}")
        print(f"问题: {query}")
        print(f"{'=' * 60}")

        try:
            response = agent.invoke(query)
            print(f"\n回答:\n{response.get('output', '无响应')}")
        except Exception as e:
            print(f"\n错误: {e}")

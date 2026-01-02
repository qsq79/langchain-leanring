#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Agents 组件基础示例 (LangChain 1.0+ 版本)
演示如何使用新的 create_agent() API 构建agents

在 LangChain 1.0+ 中：
- 使用 create_agent() 替代旧的 AgentExecutor + create_react_agent
- 使用 langgraph 构建复杂的工作流
- 使用 @tool 装饰器定义工具
- 支持结构化输出和原生异步
"""

import os
import sys
from typing import List
from pydantic import BaseModel, Field

# LangChain 1.0+ 导入
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_all_configs

# 从环境变量加载所有API配置
setup_all_configs()


# ============================================================================
# 工具定义 (使用 @tool 装饰器)
# ============================================================================

@tool
def calculator(expression: str) -> str:
    """执行数学计算，输入应该是一个数学表达式，例如 '2 + 2' 或 '10 * 5'"""
    try:
        result = eval(expression)
        return f"计算结果: {result}"
    except Exception as e:
        return f"计算错误: {str(e)}"


@tool
def greeting(name: str) -> str:
    """生成问候语，输入是人名"""
    return f"你好，{name}！很高兴见到你。"


@tool
def get_current_time() -> str:
    """获取当前时间（模拟）"""
    from datetime import datetime
    now = datetime.now()
    return f"当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')}"


@tool
def search_wikipedia(query: str) -> str:
    """在Wikipedia中搜索信息（模拟）"""
    # 这是一个模拟的工具，实际使用时可以接入真实的Wikipedia API
    return f"Wikipedia搜索结果关于 '{query}': 这是一个模拟的搜索结果。实际使用时可以接入真实的API。"


# ============================================================================
# 基础Agent示例
# ============================================================================

def basic_agent_example():
    """基础Agent示例 - 使用 create_agent()"""
    print("=== 基础Agent示例 ===\n")

    # 定义工具列表
    tools = [calculator, greeting, get_current_time]

    # 创建agent (LangChain 1.0+ 新API)
    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools,
    )

    # 测试问题
    questions = [
        "你好，我是小明",
        "现在几点了？",
        "帮我计算 123 * 456",
        "计算 100 除以 5"
    ]

    for question in questions:
        print(f"用户: {question}")
        try:
            # 调用agent
            result = agent.invoke({
                "messages": [("user", question)]
            })

            # 提取最后一条消息
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                print(f"Agent: {last_message.content}\n")
            else:
                print(f"Agent: {last_message}\n")

        except Exception as e:
            print(f"执行失败: {e}\n")
        print("-" * 60)


# ============================================================================
# 带结构化输出的Agent示例
# ============================================================================

class AnalysisResult(BaseModel):
    """分析结果的结构化输出"""
    summary: str = Field(description="对话摘要")
    calculations: List[str] = Field(description="执行的所有计算")
    sentiment: str = Field(description="对话的情感倾向")


def structured_output_agent_example():
    """带结构化输出的Agent示例"""
    print("=== 带结构化输出的Agent示例 ===\n")

    tools = [calculator, greeting, get_current_time]

    # 创建带结构化输出的agent
    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools,
        response_format=AnalysisResult  # 添加结构化输出
    )

    # 测试对话
    messages = [
        ("user", "你好，我是张三"),
        ("user", "帮我计算 25 * 4"),
        ("user", "再计算 100 + 200"),
        ("user", "请总结我们的对话")
    ]

    for role, content in messages:
        print(f"{role.capitalize()}: {content}")

    print("\n--- Agent响应 ---")

    try:
        result = agent.invoke({
            "messages": messages
        })

        # 获取messages
        messages_result = result["messages"]
        print("对话历史:")
        for msg in messages_result[-3:]:  # 打印最后3条消息
            if hasattr(msg, 'content'):
                print(f"  {msg.content[:100]}...")

        # 获取结构化响应
        if "structured_response" in result:
            structured = result["structured_response"]
            print("\n结构化分析结果:")
            print(f"  摘要: {structured.summary}")
            print(f"  计算列表: {', '.join(structured.calculations)}")
            print(f"  情感倾向: {structured.sentiment}")

    except Exception as e:
        print(f"执行失败: {e}")
        import traceback
        traceback.print_exc()

    print()


# ============================================================================
# 异步Agent示例
# ============================================================================

import asyncio


async def async_agent_example():
    """异步Agent示例"""
    print("=== 异步Agent示例 ===\n")

    tools = [calculator, greeting]

    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools
    )

    # 并发处理多个问题
    questions = [
        "你好，我是Alice",
        "计算 50 * 2",
        "你好，我是Bob",
        "计算 30 + 40"
    ]

    print(f"并发处理 {len(questions)} 个问题...\n")

    # 创建异步任务
    async def process_question(q: str):
        try:
            result = await agent.ainvoke({
                "messages": [("user", q)]
            })
            last_message = result["messages"][-1]
            content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            return q, content
        except Exception as e:
            return q, f"错误: {e}"

    # 并发执行
    tasks = [process_question(q) for q in questions]
    results = await asyncio.gather(*tasks)

    # 打印结果
    for question, answer in results:
        print(f"问题: {question}")
        print(f"回答: {answer}")
        print("-" * 40)

    print()


# ============================================================================
# 流式输出Agent示例
# ============================================================================

def streaming_agent_example():
    """流式输出Agent示例"""
    print("=== 流式输出Agent示例 ===\n")

    tools = [calculator, greeting]

    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools
    )

    question = "你好，我是小红，然后帮我计算 15 * 8"
    print(f"用户: {question}\n")
    print("Agent流式响应:")

    try:
        # 流式输出
        for chunk in agent.stream({
            "messages": [("user", question)]
        }):
            # chunk包含更新的状态
            if "messages" in chunk:
                messages = chunk["messages"]
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content') and last_message.content:
                        # 只打印新增的内容
                        print(last_message.content, end="", flush=True)

        print("\n")

    except Exception as e:
        print(f"流式输出失败: {e}")
        import traceback
        traceback.print_exc()

    print()


# ============================================================================
# 复杂工具Agent示例
# ============================================================================

@tool
def analyze_text(text: str, aspect: str = "overall") -> str:
    """分析文本的特定方面

    Args:
        text: 要分析的文本
        aspect: 分析方面，可选值: overall, sentiment, keywords, length
    """
    if aspect == "sentiment":
        return f"文本情感分析: '{text}' 的情感倾向似乎是积极的。"
    elif aspect == "keywords":
        return f"关键词提取: 从 '{text}' 中提取了关键词。"
    elif aspect == "length":
        return f"文本长度: '{text}' 有 {len(text)} 个字符。"
    else:
        return f"综合分析: '{text}' 是一个有意义的文本。"


def complex_tools_agent_example():
    """复杂工具Agent示例"""
    print("=== 复杂工具Agent示例 ===\n")

    tools = [calculator, analyze_text, greeting]

    agent = create_agent(
        model="gpt-4o-mini",
        tools=tools
    )

    questions = [
        '分析文本 "今天天气真好" 的情感',
        '分析文本 "LangChain是一个强大的框架" 的长度',
        '计算 20 * 30'
    ]

    for question in questions:
        print(f"用户: {question}")
        try:
            result = agent.invoke({
                "messages": [("user", question)]
            })

            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                print(f"Agent: {last_message.content}\n")

        except Exception as e:
            print(f"执行失败: {e}\n")

    print()


# ============================================================================
# 主函数
# ============================================================================

def main():
    """主函数，运行所有示例"""
    print("LangChain Agents 组件基础示例 (LangChain 1.0+ 版本)")
    print("=" * 70)
    print()
    print("重要变化:")
    print("- 使用 create_agent() 替代旧的 AgentExecutor")
    print("- 使用 @tool 装饰器定义工具")
    print("- 支持结构化输出 (response_format)")
    print("- 原生异步支持")
    print("- 增强的流式处理")
    print("=" * 70)
    print()

    try:
        # 1. 基础Agent示例
        basic_agent_example()

        # 2. 结构化输出Agent示例
        structured_output_agent_example()

        # 3. 异步Agent示例
        print("运行异步示例...")
        asyncio.run(async_agent_example())

        # 4. 流式输出Agent示例
        streaming_agent_example()

        # 5. 复杂工具Agent示例
        complex_tools_agent_example()

    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

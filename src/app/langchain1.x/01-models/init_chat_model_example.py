#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain init_chat_model 示例 (LangChain 1.x 推荐方式)
演示使用 init_chat_model 统一初始化各种模型的方法

这是 LangChain 1.x 中推荐的模型初始化方式：
- 更简洁的API
- 统一的模型初始化方法
- 自动从环境变量读取配置
- 支持多种模型提供商
"""

import os
import sys
import asyncio
from typing import List
from dotenv import load_dotenv

# 设置编码
os.environ['PYTHONIOENCODING'] = 'utf-8'

# 加载环境变量
load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

# 清理环境变量中的特殊字符
def clean_env_value(value: str) -> str:
    """清理环境变量中的Unicode字符"""
    import re
    return re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb"\'\u0060\u00b4]', '', value).strip()

# 设置清理后的环境变量
api_key = clean_env_value(os.getenv("OPENAI_API_KEY", ""))
api_base = clean_env_value(os.getenv("OPENAI_API_BASE", ""))

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
if api_base:
    os.environ["OPENAI_BASE_URL"] = api_base

# LangChain 1.x 新的统一模型初始化方式
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

def basic_init_chat_model_example():
    """基础 init_chat_model 使用示例"""
    print("=== 基础 init_chat_model 示例 ===")

    # 最简单的使用方式 - 自动从环境变量读取配置
    model = init_chat_model("gpt-4")

    message = HumanMessage(content="请简单介绍一下你自己。")
    response = model.invoke([message])

    print(f"用户: 请简单介绍一下你自己。")
    print(f"AI: {response.content}")
    print()

def different_providers_example():
    """不同模型提供商示例"""
    print("=== 不同模型提供商示例 ===")

    providers = [
        ("gpt-4", "OpenAI GPT-4"),
        ("gpt-3.5-turbo", "OpenAI GPT-3.5 Turbo"),
        ("claude-3-sonnet", "Anthropic Claude-3 Sonnet"),  # 如果配置了Anthropic API
    ]

    for model_name, description in providers:
        try:
            print(f"测试 {description}...")
            model = init_chat_model(model_name)

            message = HumanMessage(content=f"你是{description}，请用一句话介绍你的特点。")
            response = model.invoke([message])

            print(f"回复: {response.content[:100]}...")
            print("✓ 成功")
            print()
        except Exception as e:
            print(f"✗ 失败: {e}")
            print()

def model_with_parameters_example():
    """带参数的模型初始化示例"""
    print("=== 带参数的模型初始化示例 ===")

    # 使用参数初始化模型
    model = init_chat_model(
        "gpt-4",
        temperature=0.7,
        max_tokens=150,
        model_kwargs={
            "top_p": 0.9,
            "frequency_penalty": 0.1
        }
    )

    message = HumanMessage(content="请写一个简短的故事，关于一只会说话的猫。")
    response = model.invoke([message])

    print(f"用户: 请写一个简短的故事，关于一只会说话的猫。")
    print(f"AI: {response.content}")
    print()

def streaming_example():
    """流式输出示例"""
    print("=== 流式输出示例 ===")

    model = init_chat_model("gpt-3.5-turbo", streaming=True)

    message = HumanMessage(content="请详细解释一下什么是机器学习。")
    print("AI回复（流式输出）: ")

    # 流式输出
    for chunk in model.stream([message]):
        print(chunk.content, end="", flush=True)
    print("\n")

def async_example():
    """异步调用示例"""
    print("=== 异步调用示例 ===")

    async def process_questions():
        model = init_chat_model("gpt-3.5-turbo")

        questions = [
            "什么是Python？",
            "什么是JavaScript？",
            "什么是Go语言？"
        ]

        print("并发处理多个问题...")
        start_time = asyncio.get_event_loop().time()

        # 创建异步任务
        tasks = [
            model.ainvoke([HumanMessage(content=q)])
            for q in questions
        ]

        # 并发执行
        results = await asyncio.gather(*tasks)

        total_time = asyncio.get_event_loop().time() - start_time
        print(f"总耗时: {total_time:.2f}秒")
        print()

        for question, result in zip(questions, results):
            print(f"Q: {question}")
            print(f"A: {result.content[:100]}...")
            print()

    asyncio.run(process_questions())

def conversation_example():
    """多轮对话示例"""
    print("=== 多轮对话示例 ===")

    model = init_chat_model("gpt-4")

    # 构建对话历史
    conversation = [
        SystemMessage(content="你是一个专业的程序员，擅长解释技术概念。"),
        HumanMessage(content="请解释什么是RESTful API。")
    ]

    # 第一轮对话
    response1 = model.invoke(conversation)
    conversation.append(response1)

    print("用户: 请解释什么是RESTful API。")
    print(f"AI: {response1.content[:200]}...")
    print()

    # 第二轮对话（基于上下文）
    conversation.append(HumanMessage(content="能给我一个具体的例子吗？"))
    response2 = model.invoke(conversation)

    print("用户: 能给我一个具体的例子吗？")
    print(f"AI: {response2.content}")
    print()

def batch_processing_example():
    """批量处理示例"""
    print("=== 批量处理示例 ===")

    model = init_chat_model("gpt-3.5-turbo", temperature=0.3)

    # 批量消息
    batch_messages = [
        [HumanMessage(content="请解释什么是HTML。")],
        [HumanMessage(content="请解释什么是CSS。")],
        [HumanMessage(content="请解释什么是JavaScript。")]
    ]

    print("批量处理多个问题...")
    results = model.batch(batch_messages)

    topics = ["HTML", "CSS", "JavaScript"]
    for topic, result in zip(topics, results):
        print(f"{topic}: {result.content[:100]}...")
        print()

def structured_output_example():
    """结构化输出示例"""
    print("=== 结构化输出示例 ===")

    try:
        from langchain_core.output_parsers import JsonOutputParser
        from pydantic import BaseModel, Field
        from typing import List

        # 定义输出结构
        class TechConcept(BaseModel):
            name: str = Field(description="技术概念名称")
            category: str = Field(description="技术分类")
            description: str = Field(description="概念描述")
            use_cases: List[str] = Field(description="使用场景")

        # 创建模型和解析器
        model = init_chat_model("gpt-4", temperature=0.3)
        parser = JsonOutputParser(pydantic_object=TechConcept)

        # 构建prompt
        system_message = SystemMessage(content=f"""
        你是一个技术专家。请用JSON格式回答问题。
        格式说明：{parser.get_format_instructions()}
        """)

        human_message = HumanMessage(content="请详细解释什么是容器化技术（Docker）。")

        # 调用模型
        response = model.invoke([system_message, human_message])

        # 解析输出
        try:
            parsed_result = parser.parse(response.content)

            print("技术概念分析:")
            print(f"名称: {parsed_result['name']}")
            print(f"分类: {parsed_result['category']}")
            print(f"描述: {parsed_result['description']}")
            print(f"使用场景: {', '.join(parsed_result['use_cases'])}")

        except Exception as parse_error:
            print(f"解析JSON失败，显示原始回复: {parse_error}")
            print(f"原始回复: {response.content}")

    except ImportError:
        print("缺少必要的依赖，使用普通模式...")
        model = init_chat_model("gpt-4")
        message = HumanMessage(content="请详细解释什么是容器化技术（Docker）。")
        response = model.invoke([message])
        print(f"AI回复: {response.content}")

    print()

def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    # 测试不同的错误情况
    test_cases = [
        ("invalid-model-name", "无效模型名称"),
        ("gpt-4", "有效模型但可能API限制"),
    ]

    for model_name, description in test_cases:
        try:
            print(f"测试 {description}: {model_name}")
            model = init_chat_model(model_name)

            message = HumanMessage(content="测试消息")
            response = model.invoke([message])

            print("✓ 成功")
            print(f"回复: {response.content[:50]}...")

        except Exception as e:
            print(f"✗ 失败: {type(e).__name__}: {e}")

        print()

def performance_comparison_example():
    """性能对比示例"""
    print("=== 性能对比示例 ===")

    import time

    models_to_test = [
        ("gpt-3.5-turbo", "GPT-3.5 Turbo"),
        ("gpt-4", "GPT-4")
    ]

    test_message = [HumanMessage(content="请用一句话介绍人工智能。")]

    for model_name, display_name in models_to_test:
        try:
            print(f"测试 {display_name}...")

            model = init_chat_model(model_name)

            # 测试响应时间
            start_time = time.time()
            response = model.invoke(test_message)
            end_time = time.time()

            response_time = end_time - start_time
            response_length = len(response.content)

            print(f"响应时间: {response_time:.2f}秒")
            print(f"回复长度: {response_length}字符")
            print(f"回复内容: {response.content[:100]}...")
            print("✓ 测试完成")

        except Exception as e:
            print(f"✗ 测试失败: {e}")

        print()

def main():
    """主函数，运行所有示例"""
    print("LangChain init_chat_model 示例 (LangChain 1.x 推荐方式)")
    print("=" * 70)
    print("init_chat_model 是 LangChain 1.x 中推荐的统一模型初始化方式")
    print("支持自动从环境变量读取配置，简化模型创建过程")
    print("=" * 70)
    print()

    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 错误: 未找到 OPENAI_API_KEY 环境变量")
        print("请确保在 .env 文件中设置了正确的 API Key")
        return

    print(f"✅ API Key: {os.getenv('OPENAI_API_KEY', '')[:10]}...")
    if os.getenv("OPENAI_BASE_URL"):
        print(f"✅ API Base: {os.getenv('OPENAI_BASE_URL')}")
    print()

    try:
        # 运行各种示例
        basic_init_chat_model_example()
        different_providers_example()
        model_with_parameters_example()
        streaming_example()
        async_example()
        conversation_example()
        batch_processing_example()
        structured_output_example()
        error_handling_example()
        performance_comparison_example()

    except Exception as e:
        print(f"❌ 运行示例时出错: {e}")
        print("请检查网络连接和API配置")

if __name__ == "__main__":
    main()
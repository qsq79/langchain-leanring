#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Chains 组件高级示例 (LangChain 1.0+ 版本)
演示 LCEL 的高级用法和最佳实践

**重要更新 (2025)**:
- 本文件展示 LCEL 的高级用法和自定义模式
- 对于生产环境的 Agent 应用,推荐使用 `create_agent()` (见 06-agents)
- LangGraph Graph API 适用于更复杂的工作流

**本文件涵盖**:
- 自定义 Runnable (Custom Runnable)
- 错误处理和重试机制
- 并行和批处理优化
- 流式输出和异步处理
- 动态路由和条件链
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Callable
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import (
    Runnable,
    RunnableConfig,
    RunnablePassthrough,
    RunnableParallel,
    RunnableLambda,
)
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()


# ==================== 自定义 Runnable ====================

class TextLengthValidator(Runnable):
    """文本长度验证的自定义 Runnable"""

    def __init__(self, max_length: int = 1000):
        self.max_length = max_length

    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        text = input.get("text", "")
        if len(text) > self.max_length:
            return {
                **input,
                "text": text[:self.max_length],
                "truncated": True,
                "original_length": len(text)
            }
        return {**input, "truncated": False}

    async def ainvoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        # 异步版本
        return self.invoke(input, config)


class RetryRunnable(Runnable):
    """带重试机制的 Runnable 包装器"""

    def __init__(self, base_runnable: Runnable, max_retries: int = 3, delay: float = 1.0):
        self.base_runnable = base_runnable
        self.max_retries = max_retries
        self.delay = delay

    def invoke(self, input: Any, config: Optional[RunnableConfig] = None) -> Any:
        last_exception = None

        for attempt in range(self.max_retries):
            try:
                print(f"  尝试 #{attempt + 1}")
                return self.base_runnable.invoke(input, config)
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    print(f"  失败: {e}, {self.delay}秒后重试...")
                    time.sleep(self.delay)
                    self.delay *= 2  # 指数退避

        raise last_exception


# ==================== 示例函数 ====================

def custom_runnable_example():
    """自定义 Runnable 示例"""
    print("=== 自定义 Runnable 示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_template("总结以下文本: {text}")
    chain = prompt | llm | StrOutputParser()

    # 添加自定义验证器
    validator = TextLengthValidator(max_length=200)
    full_chain = validator | chain

    # 测试文本长度限制
    short_text = "这是一个短文本。"
    long_text = "这是一个非常长的文本..." * 100

    print("短文本测试:")
    result = full_chain.invoke({"text": short_text})
    print(f"结果: {result[:100]}...")
    print(f"被截断: {result.get('truncated', False)}")

    print("\n长文本测试:")
    result = full_chain.invoke({"text": long_text})
    print(f"原始长度: {result.get('original_length', len(long_text))}")
    print(f"结果: {result[:100]}...")
    print()


def retry_mechanism_example():
    """重试机制示例"""
    print("=== 重试机制示例 (模拟失败场景) ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_template("回答: {question}")
    base_chain = prompt | llm | StrOutputParser()

    # 包装重试机制
    retry_chain = RetryRunnable(base_chain, max_retries=2, delay=0.5)

    # 正常执行
    print("正常执行:")
    result = retry_chain.invoke({"question": "什么是AI?"})
    print(f"结果: {result[:100]}...")
    print()


def parallel_processing_example():
    """并行处理示例"""
    print("=== 并行处理示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 定义不同的处理任务
    summary_prompt = ChatPromptTemplate.from_template("一句话总结: {text}")
    sentiment_prompt = ChatPromptTemplate.from_template("分析情感(积极/消极/中性): {text}")
    keywords_prompt = ChatPromptTemplate.from_template("提取3个关键词: {text}")

    # 使用 RunnableParallel 并行执行
    parallel_chain = RunnableParallel(
        summary=summary_prompt | llm | StrOutputParser(),
        sentiment=sentiment_prompt | llm | StrOutputParser(),
        keywords=keywords_prompt | llm | StrOutputParser(),
    )

    text = "LangChain是一个强大的框架,让开发AI应用变得更加简单和高效。"

    print(f"原文: {text}\n")
    start_time = time.time()
    result = parallel_chain.invoke({"text": text})
    elapsed = time.time() - start_time

    print(f"并行处理耗时: {elapsed:.2f}秒")
    print(f"总结: {result['summary']}")
    print(f"情感: {result['sentiment']}")
    print(f"关键词: {result['keywords']}")
    print()


def dynamic_routing_example():
    """动态路由示例"""
    print("=== 动态路由示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 定义不同领域的提示
    tech_prompt = ChatPromptTemplate.from_template(
        "作为技术专家,回答: {input}"
    )
    business_prompt = ChatPromptTemplate.from_template(
        "作为商业顾问,回答: {input}"
    )
    general_prompt = ChatPromptTemplate.from_template(
        "回答: {input}"
    )

    # 创建不同的链
    tech_chain = tech_prompt | llm | StrOutputParser()
    business_chain = business_prompt | llm | StrOutputParser()
    general_chain = general_prompt | llm | StrOutputParser()

    # 路由函数
    def route_function(inputs: Dict[str, Any]) -> Runnable:
        """根据输入内容路由到不同的链"""
        text = inputs.get("input", "").lower()

        if any(word in text for word in ["编程", "代码", "算法", "ai", "技术"]):
            return tech_chain
        elif any(word in text for word in ["商业", "市场", "销售", "盈利"]):
            return business_chain
        else:
            return general_chain

    # 创建路由链
    router_chain = RunnableLambda(route_function)

    # 测试不同的输入
    test_inputs = [
        "Python中的列表推导式是什么?",
        "如何提高产品销售?",
        "今天天气怎么样?"
    ]

    for test_input in test_inputs:
        print(f"\n问题: {test_input}")
        chain = router_chain.invoke({"input": test_input})
        result = chain.invoke({"input": test_input})
        print(f"回答: {result[:80]}...")
    print()


def batch_processing_example():
    """批处理示例"""
    print("=== 批处理示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_template("简要解释: {concept}")
    chain = prompt | llm | StrOutputParser()

    # 批量处理多个输入
    concepts = [
        {"concept": "机器学习"},
        {"concept": "深度学习"},
        {"concept": "神经网络"},
        {"concept": "自然语言处理"}
    ]

    print("批量处理多个概念:")
    start_time = time.time()
    results = chain.batch(concepts)
    elapsed = time.time() - start_time

    for concept, result in zip(concepts, results):
        print(f"\n{concept['concept']}: {result[:60]}...")

    print(f"\n总耗时: {elapsed:.2f}秒")
    print()


async def async_processing_example():
    """异步处理示例"""
    print("=== 异步处理示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_template("解释: {topic}")
    chain = prompt | llm | StrOutputParser()

    # 异步处理多个任务
    topics = [
        {"topic": "量子计算"},
        {"topic": "区块链"},
        {"topic": "虚拟现实"}
    ]

    print("异步并行处理:")
    start_time = time.time()

    # 并行执行异步任务
    tasks = [chain.ainvoke(topic) for topic in topics]
    results = await asyncio.gather(*tasks)

    elapsed = time.time() - start_time

    for topic, result in zip(topics, results):
        print(f"\n{topic['topic']}: {result[:60]}...")

    print(f"\n总耗时: {elapsed:.2f}秒")
    print()


def streaming_example():
    """流式输出示例"""
    print("=== 流式输出示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7, streaming=True)
    prompt = ChatPromptTemplate.from_template("详细解释什么是{topic}")
    chain = prompt | llm | StrOutputParser()

    topic = "人工智能"
    print(f"问题: 详细解释什么是{topic}\n")
    print("回答 (流式输出):")

    for chunk in chain.stream({"topic": topic}):
        print(chunk, end="", flush=True)

    print("\n")


def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_template("解释: {term}")
    chain = prompt | llm | StrOutputParser()

    # 使用 @run_in_executor 包装可能失败的操作
    def safe_invoke(inputs: Dict[str, Any]) -> str:
        try:
            return chain.invoke(inputs)
        except Exception as e:
            return f"处理失败: {str(e)}"

    safe_chain = RunnableLambda(safe_invoke)

    # 正常执行
    result1 = safe_chain.invoke({"term": "机器学习"})
    print(f"正常结果: {result1[:60]}...")

    # 模拟错误输入 (使用空字符串可能导致错误)
    result2 = safe_chain.invoke({"term": ""})
    print(f"错误处理: {result2}")
    print()


def complex_pipeline_example():
    """复杂管道示例"""
    print("=== 复杂管道示例 ===")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 步骤1: 文本预处理
    def preprocess(inputs: Dict[str, Any]) -> Dict[str, Any]:
        text = inputs.get("text", "")
        return {
            **inputs,
            "word_count": len(text.split()),
            "char_count": len(text)
        }

    # 步骤2: 并行分析
    summary_prompt = ChatPromptTemplate.from_template(
        "总结这段文字(约{word_count}字): {text}"
    )
    sentiment_prompt = ChatPromptTemplate.from_template(
        "分析情感: {text}"
    )

    # 步骤3: 综合结果
    def synthesize(inputs: Dict[str, Any]) -> str:
        return f"""
总结: {inputs['summary']}
情感分析: {inputs['sentiment']}
统计: {inputs['word_count']} 词, {inputs['char_count']} 字
        """.strip()

    # 构建完整管道
    pipeline = (
        RunnableLambda(preprocess)
        | RunnableParallel(
            summary=summary_prompt | llm | StrOutputParser(),
            sentiment=sentiment_prompt | llm | StrOutputParser(),
        )
        | RunnableLambda(synthesize)
    )

    text = "LangChain让开发AI应用变得简单而强大。它提供了丰富的工具和抽象,帮助开发者快速构建智能应用。"

    print(f"原文: {text}\n")
    result = pipeline.invoke({"text": text})
    print(result)
    print()


def structured_output_example():
    """结构化输出示例 (LCEL 方式)"""
    print("=== 结构化输出示例 (LCEL) ===")

    from pydantic import BaseModel, Field
    from typing import List

    class AnalysisResult(BaseModel):
        """分析结果的结构化输出"""
        summary: str = Field(description="内容总结")
        key_points: List[str] = Field(description="关键点列表")
        sentiment: str = Field(description="情感倾向")

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)

    # 方式1: 使用 with_structured_output()
    structured_llm = llm.with_structured_output(AnalysisResult)

    prompt = ChatPromptTemplate.from_template("分析以下文本: {text}")
    chain = prompt | structured_llm

    text = "LangChain是一个强大的AI应用开发框架,提供了丰富的工具和抽象。它让构建智能应用变得更加简单。"

    print(f"文本: {text}\n")
    result = chain.invoke({"text": text})

    print("结构化输出结果:")
    print(f"总结: {result.summary}")
    print(f"关键点: {', '.join(result.key_points)}")
    print(f"情感: {result.sentiment}")
    print()

    print("注意: 对于需要工具的 Agent 应用,推荐使用 create_agent() 的 response_format 参数")
    print("见 06-agents 目录的示例")
    print()


def main():
    """主函数,运行所有高级示例"""
    print("LangChain Chains 组件高级示例 (LangChain 1.0+ 版本)")
    print("=" * 60)
    print("本示例展示 LCEL 的高级用法和自定义模式")
    print("对于生产环境的 Agent 应用,推荐使用 create_agent() (见 06-agents)")
    print("=" * 60)
    print()

    try:
        # 自定义 Runnable
        custom_runnable_example()

        # 重试机制
        retry_mechanism_example()

        # 并行处理
        parallel_processing_example()

        # 动态路由
        dynamic_routing_example()

        # 批处理
        batch_processing_example()

        # 流式输出
        streaming_example()

        # 错误处理
        error_handling_example()

        # 复杂管道
        complex_pipeline_example()

        # 结构化输出
        structured_output_example()

        # 异步处理
        print("运行异步示例...")
        asyncio.run(async_processing_example())

    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")


if __name__ == "__main__":
    main()

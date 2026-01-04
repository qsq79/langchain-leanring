#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Chains 组件基础示例 (LangChain 1.0+ 版本)
演示 LCEL (LangChain Expression Language) 的使用场景和最佳实践

**重要说明**:
- LCEL (pipe operator |) 是 LangChain 1.0+ 构建链的标准方式
- 本文件展示 LCEL 的各种用法和模式
- LCEL 适用于简单的 prompt → model → parser 流程
- 对于需要使用工具的 Agent 应用,请参考 06-agents 目录

**何时使用 LCEL**:
- ✅ 简单的 prompt → model → parser 流程
- ✅ 不需要使用工具(tools)
- ✅ 快速原型和简单任务
- ✅ 需要精细控制每个步骤

**何时使用 Agent (06-agents)**:
- ✅ 需要使用工具的智能体
- ✅ 需要对话记忆和状态管理
- ✅ 需要自主规划和执行能力
"""

import os
import sys
import asyncio
from typing import Dict, List, Any, Optional
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

def basic_lcel_chain_example():
    """基础 LCEL Chain 示例 - 替代 LLMChain"""
    print("=== 基础 LCEL Chain 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

    # 创建Prompt模板
    prompt = PromptTemplate(
        template="请用中文回答以下问题：{question}",
        input_variables=["question"]
    )

    # 使用LCEL创建chain (替代传统的LLMChain)
    # prompt | llm | StrOutputParser() 是 LangChain 1.x 的标准写法
    chain = prompt | llm | StrOutputParser()

    # 执行Chain
    question = "什么是人工智能？"
    result = chain.invoke({"question": question})

    print(f"问题: {question}")
    print(f"回答: {result}")
    print()

    # 批量执行
    questions = [
        {"question": "什么是机器学习？"},
        {"question": "什么是深度学习？"},
        {"question": "什么是神经网络？"}
    ]

    # 使用 batch 方法批量处理
    results = chain.batch(questions)

    print("批量执行结果:")
    for i, (q, r) in enumerate(zip(questions, results), 1):
        print(f"{i}. 问题: {q['question']}")
        print(f"   回答: {r}")
    print()

def sequential_chain_lcel_example():
    """顺序链 LCEL 示例 - 替代 SimpleSequentialChain"""
    print("=== 顺序链 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

    # 创建两个步骤的prompts
    outline_prompt = PromptTemplate(
        template="请为以下主题生成一个3句话的故事大纲：{topic}",
        input_variables=["topic"]
    )

    expansion_prompt = PromptTemplate(
        template="根据以下大纲，写一个完整的故事：{outline}",
        input_variables=["outline"]
    )

    # 方法1: 使用 RunnablePassthrough.assign 进行顺序处理
    story_chain = (
        {"outline": outline_prompt | llm | StrOutputParser()}
        | RunnablePassthrough.assign(story=expansion_prompt | llm | StrOutputParser())
        | (lambda x: x["story"])
    )

    # 执行Chain
    topic = "一个程序员发现了一个能修复所有bug的AI"
    result = story_chain.invoke({"topic": topic})

    print(f"主题: {topic}")
    print("=" * 50)
    print(f"完整故事: {result}")
    print()

def complex_sequential_chain_example():
    """复杂顺序链 LCEL 示例 - 替代 SequentialChain"""
    print("=== 复杂顺序链 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

    # 定义各个处理步骤的prompts
    analysis_prompt = PromptTemplate(
        template="分析以下问题的主要概念：{question}",
        input_variables=["question"]
    )

    explanation_prompt = PromptTemplate(
        template="基于以下分析，请详细解释这些概念：{analysis}",
        input_variables=["analysis"]
    )

    examples_prompt = PromptTemplate(
        template="为以下解释提供3个实际应用示例：{explanation}",
        input_variables=["explanation"]
    )

    # 创建各个处理步骤的链
    analysis_chain = analysis_prompt | llm | StrOutputParser()
    explanation_chain = explanation_prompt | llm | StrOutputParser()
    examples_chain = examples_prompt | llm | StrOutputParser()

    # 使用LCEL创建复杂顺序链
    overall_chain = (
        RunnablePassthrough.assign(analysis=analysis_chain)
        | RunnablePassthrough.assign(explanation=lambda x: explanation_chain.invoke({"analysis": x["analysis"]}))
        | RunnablePassthrough.assign(examples=lambda x: examples_chain.invoke({"explanation": x["explanation"]}))
    )

    # 执行Chain
    question = "什么是机器学习中的监督学习？"
    result = overall_chain.invoke({"question": question})

    print(f"原始问题: {question}")
    print("=" * 50)
    print(f"概念分析: {result['analysis']}")
    print("=" * 50)
    print(f"详细解释: {result['explanation']}")
    print("=" * 50)
    print(f"应用示例: {result['examples']}")
    print()

def transform_chain_lcel_example():
    """转换链 LCEL 示例 - 替代 TransformChain"""
    print("=== 转换链 LCEL 示例 ===")

    # 定义转换函数
    def text_analyzer(text: str) -> Dict[str, Any]:
        """分析文本的统计信息"""
        word_count = len(text.split())
        char_count = len(text.strip())
        return {
            "original_text": text,
            "word_count": word_count,
            "char_count": char_count
        }

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)

    # 创建分析链
    analysis_chain = RunnableLambda(lambda x: text_analyzer(x["text"]))

    # 创建总结prompt
    summary_prompt = PromptTemplate(
        template="请总结以下文本（字数：{word_count}，字符数：{char_count}）：\n{original_text}",
        input_variables=["original_text", "word_count", "char_count"]
    )

    summary_chain = summary_prompt | llm | StrOutputParser()

    # 组合分析链和总结链
    overall_chain = analysis_chain | summary_chain

    # 执行Chain
    text = """
    人工智能（AI）是计算机科学的一个分支，它致力于创造能够执行通常需要人类智能的任务的机器。
    这些任务包括学习、推理、问题解决、感知和语言理解。AI技术已经广泛应用于各个领域，
    从自动驾驶汽车到医疗诊断，从金融分析到创意艺术。
    """

    result = overall_chain.invoke({"text": text})

    print(f"原文: {text}")
    print(f"总结: {result}")
    print()

def parallel_chain_lcel_example():
    """并行链 LCEL 示例 - 使用 RunnableParallel"""
    print("=== 并行链 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

    # 定义不同处理任务的prompts
    summary_prompt = PromptTemplate(
        template="请总结以下文本的主要内容：{text}",
        input_variables=["text"]
    )

    keywords_prompt = PromptTemplate(
        template="请从以下文本中提取5个关键词：{text}",
        input_variables=["text"]
    )

    sentiment_prompt = PromptTemplate(
        template="请分析以下文本的情感倾向（积极/消极/中性）：{text}",
        input_variables=["text"]
    )

    # 使用RunnableParallel创建并行链
    parallel_chain = RunnableParallel(
        summary=summary_prompt | llm | StrOutputParser(),
        keywords=keywords_prompt | llm | StrOutputParser(),
        sentiment=sentiment_prompt | llm | StrOutputParser()
    )

    # 执行Chain
    text = """
    人工智能（AI）正在改变我们的生活方式。从智能手机助手到自动驾驶汽车，
    AI技术让许多日常任务变得更加便捷。虽然有人担心AI会导致失业，
    但我认为它为人类创造了新的机会和可能性。我们应该积极拥抱这项技术。
    """

    result = parallel_chain.invoke({"text": text})

    print(f"原文: {text}")
    print("=" * 50)
    print(f"总结: {result['summary']}")
    print(f"关键词: {result['keywords']}")
    print(f"情感倾向: {result['sentiment']}")
    print()

def router_chain_lcel_example():
    """路由链 LCEL 示例 - 替代 RouterChain"""
    print("=== 路由链 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)

    # 定义不同类型的Prompt模板
    physics_prompt = PromptTemplate(
        template="你是一个物理学专家。请用通俗易懂的语言回答以下物理问题：{input}",
        input_variables=["input"]
    )

    math_prompt = PromptTemplate(
        template="你是一个数学专家。请用清晰简洁的方式回答以下数学问题：{input}",
        input_variables=["input"]
    )

    chemistry_prompt = PromptTemplate(
        template="你是一个化学专家。请用专业的角度回答以下化学问题：{input}",
        input_variables=["input"]
    )

    general_prompt = PromptTemplate(
        template="请回答以下问题：{input}",
        input_variables=["input"]
    )

    # 创建专门的chains
    physics_chain = physics_prompt | llm | StrOutputParser()
    math_chain = math_prompt | llm | StrOutputParser()
    chemistry_chain = chemistry_prompt | llm | StrOutputParser()
    general_chain = general_prompt | llm | StrOutputParser()

    # 路由函数
    def route_function(x):
        """根据输入内容路由到不同的专家链"""
        question = x["input"].lower()

        if any(word in question for word in ["物理", "力", "运动", "能量", "牛顿", "电", "光", "热"]):
            return physics_chain
        elif any(word in question for word in ["数学", "方程", "计算", "公式", "函数", "几何", "代数"]):
            return math_chain
        elif any(word in question for word in ["化学", "分子", "原子", "反应", "元素", "化合物"]):
            return chemistry_chain
        else:
            return general_chain

    # 创建路由链
    router_chain = (
        RunnableLambda(lambda x: {"chain": route_function(x), "input": x["input"]})
        | RunnableLambda(lambda x: x["chain"].invoke({"input": x["input"]}))
    )

    # 测试不同类型的问题
    test_questions = [
        "什么是牛顿第二定律？",
        "如何解二次方程？",
        "水的化学式是什么？",
        "为什么天空是蓝色的？",
        "今天天气怎么样？"
    ]

    for question in test_questions:
        print(f"问题: {question}")
        result = router_chain.invoke({"input": question})
        print(f"回答: {result}")
        print("-" * 50)

def chat_lcel_example():
    """聊天模型 LCEL 示例"""
    print("=== 聊天模型 LCEL 示例 ===")

    # 创建Chat模型
    chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    # 创建聊天提示模板
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的{role}，具有{experience}经验。请以专业且友好的方式回答问题。"),
        ("human", "{question}")
    ])

    # 使用LCEL创建聊天链
    chat_chain = chat_prompt | chat_model | StrOutputParser()

    # 测试不同角色
    test_cases = [
        {
            "role": "Python编程专家",
            "experience": "5年Python开发经验",
            "question": "Python中的装饰器有什么用途？"
        },
        {
            "role": "数据科学家",
            "experience": "专注于机器学习",
            "question": "如何处理数据集中的缺失值？"
        },
        {
            "role": "产品经理",
            "experience": "熟悉敏捷开发",
            "question": "如何进行有效的用户需求分析？"
        }
    ]

    for case in test_cases:
        result = chat_chain.invoke(case)
        print(f"角色: {case['role']}")
        print(f"经验: {case['experience']}")
        print(f"问题: {case['question']}")
        print(f"回答: {result}")
        print("=" * 50)

def stream_chain_example():
    """流式输出 LCEL 示例"""
    print("=== 流式输出 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7, streaming=True)

    # 创建prompt和chain
    prompt = PromptTemplate(
        template="请详细介绍什么是{topic}，包括定义、特点和应用：",
        input_variables=["topic"]
    )

    chain = prompt | llm | StrOutputParser()

    # 流式执行
    topic = "人工智能"
    print(f"问题: 请详细介绍什么是{topic}")

    print("回答（流式输出）:")
    for chunk in chain.stream({"topic": topic}):
        print(chunk, end="", flush=True)
    print("\n")

async def async_lcel_example():
    """异步 LCEL 示例"""
    print("=== 异步 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)

    # 创建prompt
    prompt = PromptTemplate(
        template="请简要回答：{question}",
        input_variables=["question"]
    )

    # 创建异步链
    async_chain = prompt | llm | StrOutputParser()

    # 准备多个问题
    questions = [
        {"question": "什么是机器学习？"},
        {"question": "什么是深度学习？"},
        {"question": "什么是神经网络？"}
    ]

    # 并行执行异步任务
    tasks = [async_chain.ainvoke(q) for q in questions]
    results = await asyncio.gather(*tasks)

    print("异步并行处理结果:")
    for i, (q, r) in enumerate(zip(questions, results), 1):
        print(f"{i}. 问题: {q['question']}")
        print(f"   回答: {r}")
    print()

def conditional_chain_example():
    """条件链 LCEL 示例"""
    print("=== 条件链 LCEL 示例 ===")

    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)

    # 定义不同条件的prompts
    simple_prompt = PromptTemplate(
        template="请简单回答：{question}",
        input_variables=["question"]
    )

    detailed_prompt = PromptTemplate(
        template="请详细回答，包含背景信息和示例：{question}",
        input_variables=["question"]
    )

    # 创建简单的和详细的chains
    simple_chain = simple_prompt | llm | StrOutputParser()
    detailed_chain = detailed_prompt | llm | StrOutputParser()

    # 条件函数
    def should_be_detailed(x):
        """根据问题复杂度决定使用简单还是详细回答"""
        question = x["question"]
        detailed_keywords = ["详细", "解释", "为什么", "如何", "原理"]
        return any(keyword in question for keyword in detailed_keywords)

    # 条件路由
    def conditional_route(x):
        if should_be_detailed(x):
            return detailed_chain.invoke(x)
        else:
            return simple_chain.invoke(x)

    # 创建条件链
    conditional_chain = RunnableLambda(conditional_route)

    # 测试问题
    test_questions = [
        {"question": "什么是AI？"},
        {"question": "请详细解释机器学习的原理"},
        {"question": "Python是什么？"},
        {"question": "为什么深度学习需要大量数据？"}
    ]

    for q in test_questions:
        result = conditional_chain.invoke(q)
        print(f"问题: {q['question']}")
        print(f"回答: {result}")
        print("-" * 50)

def compare_apis_example():
    """对比不同 LCEL 模式的使用"""
    print("=== LCEL 不同模式对比示例 ===")

    # 方式1: 基础 LCEL 链
    print("方式1: 基础 LCEL - prompt | model | parser")
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    prompt = ChatPromptTemplate.from_template(
        "你是一个专业的问答助手。请简洁准确地回答问题。\n\n问题: {question}"
    )
    chain = prompt | llm | StrOutputParser()

    response = chain.invoke({"question": "什么是人工智能?"})
    print(f"基础 LCEL 回答: {response[:100]}...")

    # 方式2: 带自定义处理的 LCEL
    print("\n方式2: 带自定义函数的 LCEL")
    def format_response(response):
        return f"【回答】{response}"

    enhanced_chain = prompt | llm | StrOutputParser() | format_response
    response = enhanced_chain.invoke({"question": "什么是深度学习?"})
    print(f"增强 LCEL 回答: {response[:100]}...")

    # 方式3: 并行处理
    print("\n方式3: 并行处理多个任务")
    parallel_chain = RunnableParallel(
        ai=prompt | llm | StrOutputParser(),
        ml=ChatPromptTemplate.from_template("简洁解释机器学习: {question}") | llm | StrOutputParser(),
    )

    results = parallel_chain.invoke({"question": "人工智能"})
    print(f"AI 回答: {results['ai'][:80]}...")
    print(f"ML 回答: {results['ml'][:80]}...")

    print("\n提示:")
    print("- 对于简单任务 → 使用基础 LCEL")
    print("- 对于自定义处理 → 添加 RunnableLambda")
    print("- 对于并行任务 → 使用 RunnableParallel")
    print("- 对于需要工具的应用 → 参考 06-agents 目录")
    print()


def main():
    """主函数，运行所有示例"""
    print("LangChain Chains 组件基础示例 (LangChain 1.0+ 版本)")
    print("=" * 60)
    print("本示例展示 LCEL (LangChain Expression Language) 的用法")
    print("LCEL 适用于简单的 prompt → model 流程")
    print("对于需要工具的 Agent 应用，请参考 06-agents 目录")
    print("=" * 60)
    print()

    try:
        # LCEL 模式对比示例
        compare_apis_example()

        # 基础LCEL链示例
        basic_lcel_chain_example()

        # 顺序链示例
        sequential_chain_lcel_example()
        complex_sequential_chain_example()

        # 转换链示例
        transform_chain_lcel_example()

        # 并行链示例
        parallel_chain_lcel_example()

        # 路由链示例
        router_chain_lcel_example()

        # 条件链示例
        conditional_chain_example()

        # 聊天模型示例
        chat_lcel_example()

        # 流式输出示例
        stream_chain_example()

        # 异步示例
        print("运行异步示例...")
        asyncio.run(async_lcel_example())

    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
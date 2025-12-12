#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Models 组件基础示例 (LangChain 1.x 版本)
演示LLM、Chat Models和Embeddings的基本使用方法

在 LangChain 1.x 中：
- 从 langchain 导入的部分组件已移至 langchain_core
- 部分导入路径发生变化
- 推荐使用新的流式API和异步API
"""

import os
import sys
from typing import List
import asyncio

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

# LangChain 1.x 兼容的导入
from langchain_openai import OpenAI, ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler
import numpy as np

def llm_basic_example():
    """LLM基础使用示例"""
    print("=== LLM基础示例 ===")

    try:
        # 在 LangChain 1.x 中，OpenAI 类仍然可用但可能受到 API 限制
        llm = OpenAI(
            model="gpt-3.5-turbo-instruct",
            temperature=0.7,
            max_tokens=100
        )

        # 简单文本生成
        prompt = "请用中文写一首关于春天的诗，要求4行，每行7个字。"
        response = llm.invoke(prompt)
        print(f"输入: {prompt}")
        print(f"输出: {response}")
        print()
    except Exception as e:
        print(f"LLM调用失败: {e}")
        print("尝试使用ChatOpenAI作为替代...")

        # 使用ChatOpenAI作为替代
        chat_model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=100
        )

        message = HumanMessage(content="请用中文写一首关于春天的诗，要求4行，每行7个字。")
        response = chat_model.invoke([message])
        print(f"输入: 请用中文写一首关于春天的诗，要求4行，每行7个字。")
        print(f"输出: {response.content}")
        print()

def llm_streaming_example():
    """LLM流式输出示例"""
    print("=== LLM流式输出示例 ===")

    try:
        # 使用流式LLM
        llm = OpenAI(
            model="gpt-3.5-turbo-instruct",
            streaming=True,
            callbacks=[StreamingStdOutCallbackHandler()],
            temperature=0.7
        )

        prompt = "请解释什么是人工智能，包括其主要特点和应用领域。"
        print(f"输入: {prompt}")
        print("流式输出: ")

        # 使用 LangChain 1.x 的流式API
        for chunk in llm.stream(prompt):
            print(chunk, end="", flush=True)
        print("\n")
    except Exception as e:
        print(f"LLM流式输出失败: {e}")
        print("尝试使用ChatOpenAI的流式输出...")

        # 使用ChatOpenAI的流式输出
        chat_model = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.7,
            max_tokens=200
        )

        message = HumanMessage(content="请简单解释什么是人工智能，包括其主要特点。")
        print(f"输入: 请简单解释什么是人工智能，包括其主要特点。")
        print("流式输出: ")

        # LangChain 1.x 支持的流式输出
        for chunk in chat_model.stream([message]):
            print(chunk.content, end="", flush=True)
        print("\n")

def llm_batch_example():
    """LLM批量处理示例"""
    print("=== LLM批量处理示例 ===")

    try:
        # 使用LLM进行批量处理
        llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)

        # 批量提示
        prompts = [
            "什么是机器学习？",
            "什么是深度学习？",
            "什么是神经网络？"
        ]

        # 使用 batch 方法进行批量处理（LangChain 1.x 推荐）
        results = llm.batch(prompts)

        for i, (prompt, result) in enumerate(zip(prompts, results), 1):
            print(f"问题{i}: {prompt}")
            print(f"答案{i}: {result.strip()}")
            print()
    except Exception as e:
        print(f"LLM批量处理失败: {e}")
        print("使用ChatOpenAI进行单独调用...")

        # 使用ChatOpenAI逐个处理
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

        prompts = [
            "什么是机器学习？",
            "什么是深度学习？",
            "什么是神经网络？"
        ]

        # 使用并发处理替代批量处理
        async def process_prompts():
            tasks = [chat_model.ainvoke([HumanMessage(content=prompt)]) for prompt in prompts]
            results = await asyncio.gather(*tasks)

            for i, (prompt, result) in enumerate(zip(prompts, results), 1):
                print(f"问题{i}: {prompt}")
                print(f"答案{i}: {result.content.strip()}")
                print()

        asyncio.run(process_prompts())

def chat_model_basic_example():
    """Chat Model基础使用示例"""
    print("=== Chat Model基础示例 ===")

    # 创建Chat Model实例
    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.7
    )

    # 构建消息列表
    messages = [
        SystemMessage(content="你是一个专业的Python编程助手。"),
        HumanMessage(content="请解释Python中的装饰器是什么，并给出一个简单的例子。")
    ]

    # 生成回复
    response = chat_model.invoke(messages)
    print("系统消息: 你是一个专业的Python编程助手。")
    print("用户消息: 请解释Python中的装饰器是什么，并给出一个简单的例子。")
    print("AI回复: ")
    print(response.content)
    print()

def chat_model_multi_turn_example():
    """Chat Model多轮对话示例"""
    print("=== Chat Model多轮对话示例 ===")

    chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

    # 对话历史
    conversation = [
        SystemMessage(content="你是一个历史知识专家。")
    ]

    # 第一轮对话
    conversation.append(HumanMessage(content="请简要介绍唐朝的历史。"))
    response1 = chat_model.invoke(conversation)
    conversation.append(response1)

    print("用户: 请简要介绍唐朝的历史。")
    print(f"AI: {response1.content}\n")

    # 第二轮对话（基于上下文）
    conversation.append(HumanMessage(content="那么唐朝最著名的皇帝是谁？"))
    response2 = chat_model.invoke(conversation)

    print("用户: 那么唐朝最著名的皇帝是谁？")
    print(f"AI: {response2.content}\n")

def chat_model_structured_output_example():
    """Chat Model结构化输出示例 (LangChain 1.x 新特性)"""
    print("=== Chat Model结构化输出示例 ===")

    try:
        from langchain_core.output_parsers import JsonOutputParser
        from langchain_core.pydantic_v1 import BaseModel, Field
        from typing import List

        # 定义输出结构
        class ProgrammingConcept(BaseModel):
            name: str = Field(description="编程概念名称")
            description: str = Field(description="概念描述")
            key_features: List[str] = Field(description="关键特性列表")
            example: str = Field(description="简单示例")

        # 创建解析器
        parser = JsonOutputParser(pydantic_object=ProgrammingConcept)

        # 创建Chat Model
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

        # 构建包含格式指令的prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一个编程专家，请用JSON格式回答问题。格式说明：{format_instructions}"),
            ("human", "请详细解释Python中的生成器（generator）概念。")
        ])

        # 创建链（使用 LCEL 风格）
        chain = prompt | chat_model | parser

        # 执行并获取结构化输出
        result = chain.invoke({
            "format_instructions": parser.get_format_instructions()
        })

        print("编程概念分析:")
        print(f"名称: {result['name']}")
        print(f"描述: {result['description']}")
        print(f"关键特性: {', '.join(result['key_features'])}")
        print(f"示例: {result['example']}")
        print()

    except Exception as e:
        print(f"结构化输出示例失败: {e}")
        print("使用普通对话模式...")

        # 回退到普通对话
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)
        messages = [
            SystemMessage(content="你是一个编程专家。"),
            HumanMessage(content="请详细解释Python中的生成器（generator）概念。")
        ]
        response = chat_model.invoke(messages)
        print(f"AI回复: {response.content}")
        print()

async def chat_model_async_example():
    """Chat Model异步调用示例"""
    print("=== Chat Model异步调用示例 ===")

    chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

    # 并发处理多个问题
    questions = [
        "什么是React框架的特点？",
        "什么是Vue框架的优势？",
        "什么是Angular框架的适用场景？"
    ]

    print("并发处理多个问题...")
    start_time = asyncio.get_event_loop().time()

    # 创建异步任务
    tasks = []
    for question in questions:
        messages = [HumanMessage(content=question)]
        task = chat_model.ainvoke(messages)
        tasks.append((question, task))

    # 并发执行
    results = await asyncio.gather(*[task for _, task in tasks])

    total_time = asyncio.get_event_loop().time() - start_time

    print(f"总耗时: {total_time:.2f}秒")
    print("结果:")
    for (question, _), result in zip(tasks, results):
        print(f"Q: {question}")
        print(f"A: {result.content.strip()[:100]}...")
        print()

def embeddings_basic_example():
    """Embeddings基础使用示例"""
    print("=== Embeddings基础示例 ===")

    try:
        # 尝试使用最新的 embedding 模型
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        print("使用 text-embedding-3-small 模型")
    except Exception as e:
        try:
            embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
            print("使用 text-embedding-ada-002 模型")
        except Exception as e2:
            print(f"Embeddings模型不可用: {e2}")
            return

    # 示例文本
    texts = [
        "人工智能是计算机科学的一个分支",
        "机器学习是人工智能的一个子领域",
        "深度学习是机器学习的一种方法",
        "今天天气很好，适合出去散步"
    ]

    # 生成嵌入向量
    print("正在生成嵌入向量...")
    embedding_vectors = embeddings.embed_documents(texts)

    # 显示向量信息
    for i, (text, vector) in enumerate(zip(texts, embedding_vectors)):
        print(f"文本{i+1}: {text}")
        print(f"向量维度: {len(vector)}")
        print(f"向量前5个值: {vector[:5]}")
        print()

    # 计算相似度
    def cosine_similarity(vec1, vec2):
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))

    # 比较文本相似度
    print("=== 文本相似度分析 ===")
    for i in range(len(texts)):
        for j in range(i+1, len(texts)):
            similarity = cosine_similarity(embedding_vectors[i], embedding_vectors[j])
            print(f"文本{i+1} vs 文本{j+1}: 相似度 = {similarity:.4f}")
            print(f"  '{texts[i]}'")
            print(f"  '{texts[j]}'")
            print()

def embeddings_async_example():
    """Embeddings异步处理示例"""
    print("=== Embeddings异步处理示例 ===")

    try:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    except Exception:
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

    # 大量文本集合
    texts = [
        f"这是第{i+1}个示例文本，用于演示异步嵌入向量生成。"
        for i in range(10)
    ]

    print("异步生成嵌入向量...")

    async def process_embeddings():
        # 并发生成嵌入向量
        tasks = [embeddings.aembed_query(text) for text in texts]
        vectors = await asyncio.gather(*tasks)

        for i, (text, vector) in enumerate(zip(texts, vectors)):
            print(f"文本{i+1}: 长度={len(text)}, 向量维度={len(vector)}")

    asyncio.run(process_embeddings())
    print()

def main():
    """主函数，运行所有示例"""
    print("LangChain Models 组件基础示例 (LangChain 1.x 版本)")
    print("=" * 60)
    print("注意：此版本兼容 LangChain 1.x 的新API和导入路径")
    print("=" * 60)
    print()

    try:
        # LLM示例
        llm_basic_example()
        llm_streaming_example()
        llm_batch_example()

        # Chat Model示例
        chat_model_basic_example()
        chat_model_multi_turn_example()
        chat_model_structured_output_example()

        # 异步Chat Model示例
        asyncio.run(chat_model_async_example())

        # Embeddings示例
        embeddings_basic_example()
        embeddings_async_example()

    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
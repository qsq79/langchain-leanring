#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Models 组件基础示例
演示LLM、Chat Models和Embeddings的基本使用方法
"""

import os
import sys
from typing import List
from langchain_openai import OpenAI, ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.callbacks import StreamingStdOutCallbackHandler
import numpy as np

# 添加utils目录到系统路径，以便导入配置加载器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

def llm_basic_example():
    """LLM基础使用示例"""
    print("=== LLM基础示例 ===")
    
    # 创建LLM实例
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

def llm_streaming_example():
    """LLM流式输出示例"""
    print("=== LLM流式输出示例 ===")
    
    # 创建支持流式输出的LLM
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        streaming=True,
        callbacks=[StreamingStdOutCallbackHandler()],
        temperature=0.7
    )
    
    prompt = "请解释什么是人工智能，包括其主要特点和应用领域。"
    print(f"输入: {prompt}")
    print("流式输出: ")
    
    # 流式生成
    for chunk in llm.stream(prompt):
        print(chunk.content, end="", flush=True)
    print("\n")

def llm_batch_example():
    """LLM批量处理示例"""
    print("=== LLM批量处理示例 ===")
    
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 批量提示
    prompts = [
        "什么是机器学习？",
        "什么是深度学习？",
        "什么是神经网络？"
    ]
    
    # 批量生成
    results = llm.generate(prompts)
    
    for i, (prompt, generation) in enumerate(zip(prompts, results.generations)):
        print(f"问题{i+1}: {prompt}")
        print(f"答案{i+1}: {generation[0].text.strip()}")
        print()

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

def embeddings_basic_example():
    """Embeddings基础使用示例"""
    print("=== Embeddings基础示例 ===")
    
    # 创建Embeddings实例
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    
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

def embeddings_search_example():
    """基于嵌入向量的语义搜索示例"""
    print("=== 语义搜索示例 ===")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    
    # 文档库
    documents = [
        "Python是一种高级编程语言，具有简洁易读的语法。",
        "JavaScript主要用于网页开发，可以实现动态效果。",
        "机器学习是人工智能的重要分支，能够从数据中学习模式。",
        "深度学习使用神经网络来模拟人脑的学习过程。",
        "自然语言处理帮助计算机理解和生成人类语言。"
    ]
    
    # 生成文档嵌入
    doc_embeddings = embeddings.embed_documents(documents)
    
    # 搜索查询
    query = "编程语言的特点"
    query_embedding = embeddings.embed_query(query)
    
    # 计算查询与所有文档的相似度
    def cosine_similarity(vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    similarities = []
    for i, doc_embedding in enumerate(doc_embeddings):
        similarity = cosine_similarity(query_embedding, doc_embedding)
        similarities.append((i, similarity, documents[i]))
    
    # 按相似度排序
    similarities.sort(key=lambda x: x[1], reverse=True)
    
    print(f"搜索查询: {query}")
    print("搜索结果（按相关度排序）:")
    for i, (doc_idx, similarity, doc) in enumerate(similarities):
        print(f"{i+1}. [相似度: {similarity:.4f}] {doc}")
    print()

def main():
    """主函数，运行所有示例"""
    print("LangChain Models 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # LLM示例
        llm_basic_example()
        llm_streaming_example()
        llm_batch_example()
        
        # Chat Model示例
        chat_model_basic_example()
        chat_model_multi_turn_example()
        
        # Embeddings示例
        embeddings_basic_example()
        embeddings_search_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
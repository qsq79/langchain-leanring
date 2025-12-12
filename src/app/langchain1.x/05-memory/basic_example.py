#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Memory 组件基础示例
演示各种Memory组件的基础使用方法
"""

import os
import sys
from typing import Dict, List, Any
from langchain_openai import OpenAI, ChatOpenAI
from langchain.memory import (
    ConversationBufferMemory,
    ConversationBufferWindowMemory,
    ConversationSummaryMemory,
    ConversationKGMemory
)
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain, ConversationChain
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_community.llms import OpenAI as CommunityOpenAI

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

def conversation_buffer_memory_example():
    """ConversationBufferMemory示例"""
    print("=== ConversationBufferMemory示例 ===")
    
    # 创建ConversationBufferMemory
    memory = ConversationBufferMemory()
    
    # 模拟对话
    conversations = [
        {"input": "你好，我想了解人工智能", "output": "你好！人工智能是计算机科学的一个分支，致力于创造能够模拟人类智能的机器。"},
        {"input": "机器学习和深度学习有什么区别？", "output": "机器学习是人工智能的子领域，而深度学习是机器学习的子集。深度学习使用多层神经网络，能够自动学习数据的复杂模式。"},
        {"input": "能推荐一些学习资源吗？", "output": "当然可以！你可以从Andrew Ng的机器学习课程开始，然后学习深度学习框架如TensorFlow或PyTorch。"}
    ]
    
    # 保存对话上下文
    for conv in conversations:
        memory.save_context(conv["input"], conv["output"])
    
    # 查看内存内容
    buffer = memory.buffer
    print("对话历史:")
    print(buffer)
    print()
    
    # 获取内存变量
    memory_variables = memory.load_memory_variables({})
    print("内存变量:")
    print(memory_variables)
    print()
    
    # 使用Memory与Chain集成
    llm = OpenAI(temperature=0.7)
    prompt = PromptTemplate(
        template="""你是一个AI助手。以下是与用户的历史对话：

{history}

用户当前问题：{input}

请基于历史对话回答用户的问题：""",
        input_variables=["history", "input"]
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory
    )
    
    # 测试对话连续性
    response = chain.invoke({"input": "刚才你提到的学习框架中，哪个更适合初学者？"})
    print("连续对话测试:")
    print(f"用户: 刚才你提到的学习框架中，哪个更适合初学者？")
    print(f"AI: {response['text']}")
    print()

def conversation_buffer_window_memory_example():
    """ConversationBufferWindowMemory示例"""
    print("=== ConversationBufferWindowMemory示例 ===")
    
    # 创建窗口Memory（只保留最近的2轮对话）
    memory = ConversationBufferWindowMemory(k=2)
    
    # 模拟多轮对话
    conversations = [
        {"input": "你好", "output": "你好！有什么可以帮助你的吗？"},
        {"input": "我想了解Python", "output": "Python是一种高级编程语言，语法简洁，适合初学者。"},
        {"input": "Python有什么特点？", "output": "Python具有简洁的语法、丰富的库支持和跨平台特性。"},
        {"input": "它适合做什么？", "output": "Python适合Web开发、数据分析、人工智能等多个领域。"},
        {"input": "学习难度大吗？", "output": "Python相对容易学习，是初学者的理想选择。"}
    ]
    
    # 保存所有对话
    for conv in conversations:
        memory.save_context(conv["input"], conv["output"])
        print(f"保存对话: {conv['input']} -> {conv['output'][:30]}...")
    
    # 查看窗口内存内容
    buffer = memory.buffer
    print(f"\n窗口内存内容（保留最近{memory.k}轮）:")
    print(buffer)
    print()
    
    # 测试窗口效果
    memory_variables = memory.load_memory_variables({})
    print("内存变量:")
    print(memory_variables)
    print()

def conversation_summary_memory_example():
    """ConversationSummaryMemory示例"""
    print("=== ConversationSummaryMemory示例 ===")
    
    # 创建摘要Memory
    llm = OpenAI(temperature=0.3)
    memory = ConversationSummaryMemory(llm=llm)
    
    # 模拟长对话
    conversations = [
        {"input": "我想学习机器学习，应该从哪里开始？", "output": "建议从数学基础开始，包括线性代数、概率统计和微积分。然后学习机器学习的基本概念，如监督学习、无监督学习等。"},
        {"input": "需要什么编程基础？", "output": "Python是机器学习的主要编程语言，建议先掌握Python基础，包括数据结构、函数、类等。同时了解NumPy、Pandas等数据处理库。"},
        {"input": "推荐一些学习资源", "output": "可以从Andrew Ng的Coursera机器学习课程开始，阅读《机器学习实战》这本书，实践Kaggle竞赛项目。"},
        {"input": "深度学习是什么？", "output": "深度学习是机器学习的一个分支，使用多层神经网络。它在图像识别、自然语言处理等领域表现出色。主要框架有TensorFlow和PyTorch。"},
        {"input": "学习路径建议", "output": "建议路径：1.掌握Python和数学基础 2.学习传统机器学习算法 3.深入深度学习理论 4.实践项目 5.选择专业方向如CV、NLP等"}
    ]
    
    # 保存对话并生成摘要
    for i, conv in enumerate(conversations):
        print(f"保存第 {i+1} 轮对话...")
        memory.save_context(conv["input"], conv["output"])
        
        # 查看当前摘要
        summary = memory.buffer
        print(f"当前摘要: {summary[:100]}...")
        print()
    
    # 查看最终摘要
    print("最终对话摘要:")
    print(memory.buffer)
    print()
    
    # 使用摘要Memory创建对话链
    prompt = PromptTemplate(
        template="""你是一个AI学习助手。以下是对话摘要：

{summary}

用户当前问题：{input}

请基于摘要信息回答用户的问题：""",
        input_variables=["summary", "input"]
    )
    
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory
    )
    
    # 测试基于摘要的回答
    response = chain.invoke({"input": "我应该选择TensorFlow还是PyTorch？"})
    print("基于摘要的连续对话:")
    print(f"用户: 我应该选择TensorFlow还是PyTorch？")
    print(f"AI: {response['text']}")
    print()

def conversation_kg_memory_example():
    """ConversationKGMemory示例"""
    print("=== ConversationKGMemory示例 ===")
    
    # 创建知识图谱Memory
    llm = OpenAI(temperature=0.3)
    memory = ConversationKGMemory(llm=llm)
    
    # 模拟对话（包含实体和关系）
    conversations = [
        {"input": "我想了解深度学习", "output": "深度学习是机器学习的一个分支，使用神经网络。"},
        {"input": "TensorFlow是什么？", "output": "TensorFlow是Google开发的深度学习框架。"},
        {"input": "PyTorch呢？", "output": "PyTorch是Facebook开发的深度学习框架，比TensorFlow更灵活。"},
        {"input": "它们有什么区别？", "output": "TensorFlow更适合生产环境，PyTorch更适合研究和原型开发。"}
    ]
    
    # 保存对话并构建知识图谱
    for conv in conversations:
        memory.save_context(conv["input"], conv["output"])
        print(f"保存对话: {conv['input']}")
    
    # 查看知识图谱
    print("\n知识图谱内容:")
    print(memory.knowledge_graph)
    print()
    
    # 查看内存变量
    memory_variables = memory.load_memory_variables({})
    print("内存变量:")
    print(memory_variables)
    print()

def conversation_chain_example():
    """ConversationChain示例"""
    print("=== ConversationChain示例 ===")
    
    # 创建不同类型的Memory
    buffer_memory = ConversationBufferMemory()
    window_memory = ConversationBufferWindowMemory(k=3)
    summary_memory = ConversationSummaryMemory(llm=OpenAI(temperature=0.3))
    
    # 创建ConversationChain
    llm = OpenAI(temperature=0.7)
    
    # 测试不同Memory的效果
    memories = [
        ("Buffer Memory", buffer_memory),
        ("Window Memory", window_memory),
        ("Summary Memory", summary_memory)
    ]
    
    for memory_name, memory in memories:
        print(f"--- 测试 {memory_name} ---")
        
        # 创建对话链
        conversation = ConversationChain(
            llm=llm,
            memory=memory,
            verbose=True
        )
        
        # 模拟对话
        test_conversations = [
            "你好，我想学习Python编程",
            "Python有哪些特点？",
            "适合做什么项目？",
            "推荐一些学习资源"
        ]
        
        for user_input in test_conversations:
            response = conversation.invoke({"input": user_input})
            print(f"用户: {user_input}")
            print(f"AI: {response['response']}")
            print()
        
        print(f"{memory_name} 内存内容:")
        print(memory.buffer if hasattr(memory, 'buffer') else "无buffer属性")
        print("=" * 50)
        print()

def memory_with_chat_model_example():
    """Memory与Chat Model集成示例"""
    print("=== Memory与Chat Model集成示例 ===")
    
    # 创建Chat模型和Memory
    chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    memory = ConversationBufferMemory(return_messages=True)
    
    # 创建Chat Prompt模板
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的AI助手，能够记住对话历史并提供连贯的回答。"),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}")
    ])
    
    # 创建Chain
    chain = LLMChain(
        llm=chat_model,
        prompt=prompt,
        memory=memory,
        verbose=True
    )
    
    # 模拟对话
    conversations = [
        "我叫张三，是一名软件工程师",
        "我最近在学习机器学习",
        "有什么好的入门建议吗？",
        "记得我的名字吗？"
    ]
    
    for user_input in conversations:
        response = chain.invoke({"input": user_input})
        print(f"用户: {user_input}")
        print(f"AI: {response['text']}")
        print()
    
    # 查看历史消息
    print("历史消息:")
    history = memory.chat_memory.messages
    for i, message in enumerate(history):
        print(f"{i+1}. {message.type}: {message.content}")
    print()

def memory_variables_example():
    """Memory变量管理示例"""
    print("=== Memory变量管理示例 ===")
    
    # 自定义Memory变量名
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        input_key="user_input",
        output_key="ai_response"
    )
    
    # 创建对应的Prompt模板
    prompt = PromptTemplate(
        template="""系统：你是一个友好的AI助手。

对话历史：
{chat_history}

用户输入：{user_input}

请根据历史对话回答用户的问题。你的回答：""",
        input_variables=["chat_history", "user_input"]
    )
    
    # 创建Chain
    llm = OpenAI(temperature=0.7)
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory
    )
    
    # 模拟对话
    conversations = [
        "我对人工智能很感兴趣",
        "人工智能的主要分支有哪些？",
        "哪个分支最值得学习？"
    ]
    
    for user_input in conversations:
        response = chain.invoke({"user_input": user_input})
        print(f"用户: {user_input}")
        print(f"AI: {response['text']}")
        print()
    
    # 查看自定义变量
    print("自定义Memory变量:")
    memory_vars = memory.load_memory_variables({})
    print(memory_vars)
    print()

def main():
    """主函数，运行所有示例"""
    print("LangChain Memory 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # 基础Memory示例
        conversation_buffer_memory_example()
        conversation_buffer_window_memory_example()
        conversation_summary_memory_example()
        conversation_kg_memory_example()
        
        # Chain集成示例
        conversation_chain_example()
        memory_with_chat_model_example()
        memory_variables_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
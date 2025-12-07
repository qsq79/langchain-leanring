#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Chains 组件基础示例
演示LLMChain、SequentialChain、RouterChain等基础Chain的使用方法
"""

import os
import sys
from typing import Dict, List, Any
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain, SimpleSequentialChain, SequentialChain, TransformChain
from langchain.chains.router import MultiPromptChain
from langchain.chains.router.llm_router import LLMRouterChain, RouterOutputParser
from langchain_core.messages import HumanMessage, SystemMessage

# 添加utils目录到系统路径，以便导入配置加载器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

def llm_chain_basic_example():
    """LLMChain基础示例"""
    print("=== LLMChain基础示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)
    
    # 创建Prompt模板
    prompt_template = PromptTemplate(
        template="请用中文回答以下问题：{question}",
        input_variables=["question"]
    )
    
    # 创建LLMChain
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template
    )
    
    # 执行Chain
    question = "什么是人工智能？"
    result = chain.invoke({"question": question})
    
    print(f"问题: {question}")
    print(f"回答: {result['text']}")
    print()
    
    # 批量执行
    questions = [
        "什么是机器学习？",
        "什么是深度学习？",
        "什么是神经网络？"
    ]
    
    results = chain.apply([{"question": q} for q in questions])
    
    print("批量执行结果:")
    for i, (q, r) in enumerate(zip(questions, results), 1):
        print(f"{i}. 问题: {q}")
        print(f"   回答: {r['text']}")
    print()

def simple_sequential_chain_example():
    """SimpleSequentialChain示例"""
    print("=== SimpleSequentialChain示例 ===")
    
    # 创建第一个Chain：生成故事大纲
    story_outline_prompt = PromptTemplate(
        template="请为以下主题生成一个3句话的故事大纲：{topic}",
        input_variables=["topic"]
    )
    
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)
    outline_chain = LLMChain(llm=llm, prompt=story_outline_prompt)
    
    # 创建第二个Chain：扩展故事
    story_expansion_prompt = PromptTemplate(
        template="根据以下大纲，写一个完整的故事：{outline}",
        input_variables=["outline"]
    )
    
    expansion_chain = LLMChain(llm=llm, prompt=story_expansion_prompt)
    
    # 创建SequentialChain
    story_chain = SimpleSequentialChain(
        chains=[outline_chain, expansion_chain],
        verbose=True
    )
    
    # 执行Chain
    topic = "一个程序员发现了一个能修复所有bug的AI"
    result = story_chain.invoke({"input": topic})
    
    print(f"主题: {topic}")
    print("=" * 50)
    print(f"完整故事: {result['output']}")
    print()

def sequential_chain_example():
    """SequentialChain示例"""
    print("=== SequentialChain示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)
    
    # 第一个Chain：问题分析
    analysis_prompt = PromptTemplate(
        template="分析以下问题的主要概念：{question}",
        input_variables=["question"]
    )
    analysis_chain = LLMChain(
        llm=llm,
        prompt=analysis_prompt,
        output_key="analysis"
    )
    
    # 第二个Chain：生成解释
    explanation_prompt = PromptTemplate(
        template="基于以下分析，请详细解释这些概念：{analysis}",
        input_variables=["analysis"]
    )
    explanation_chain = LLMChain(
        llm=llm,
        prompt=explanation_prompt,
        output_key="explanation"
    )
    
    # 第三个Chain：提供示例
    examples_prompt = PromptTemplate(
        template="为以下解释提供3个实际应用示例：{explanation}",
        input_variables=["explanation"]
    )
    examples_chain = LLMChain(
        llm=llm,
        prompt=examples_prompt,
        output_key="examples"
    )
    
    # 组合成SequentialChain
    overall_chain = SequentialChain(
        chains=[analysis_chain, explanation_chain, examples_chain],
        input_variables=["question"],
        output_variables=["analysis", "explanation", "examples"],
        verbose=True
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

def transform_chain_example():
    """TransformChain示例"""
    print("=== TransformChain示例 ===")
    
    # 定义转换函数
    def count_words(inputs: Dict[str, Any]) -> Dict[str, Any]:
        """统计文本的字数"""
        text = inputs["text"]
        word_count = len(text.split())
        char_count = len(text)
        return {
            "original_text": text,
            "word_count": word_count,
            "char_count": char_count
        }
    
    # 创建TransformChain
    transform_chain = TransformChain(
        input_variables=["text"],
        output_variables=["original_text", "word_count", "char_count"],
        transform=count_words
    )
    
    # 创建LLMChain
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    summary_prompt = PromptTemplate(
        template="请总结以下文本（字数：{word_count}，字符数：{char_count}）：\n{original_text}",
        input_variables=["original_text", "word_count", "char_count"]
    )
    summary_chain = LLMChain(llm=llm, prompt=summary_prompt)
    
    # 组合成SequentialChain
    overall_chain = SequentialChain(
        chains=[transform_chain, summary_chain],
        input_variables=["text"],
        output_variables=["word_count", "char_count", "text"],
        verbose=True
    )
    
    # 执行Chain
    text = """
    人工智能（AI）是计算机科学的一个分支，它致力于创造能够执行通常需要人类智能的任务的机器。
    这些任务包括学习、推理、问题解决、感知和语言理解。AI技术已经广泛应用于各个领域，
    从自动驾驶汽车到医疗诊断，从金融分析到创意艺术。
    """
    
    result = overall_chain.invoke({"text": text})
    
    print(f"原文: {text}")
    print(f"字数: {result['word_count']}")
    print(f"字符数: {result['char_count']}")
    print(f"总结: {result['text']}")
    print()

def router_chain_example():
    """RouterChain示例"""
    print("=== RouterChain示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 定义不同类型的Prompt模板
    physics_template = """你是一个物理学专家。请用通俗易懂的语言回答以下物理问题：
    问题：{input}
    回答："""
    
    math_template = """你是一个数学专家。请用清晰简洁的方式回答以下数学问题：
    问题：{input}
    回答："""
    
    chemistry_template = """你是一个化学专家。请用专业的角度回答以下化学问题：
    问题：{input}
    回答："""
    
    # 创建Prompt模板
    prompt_infos = [
        {
            "name": "physics",
            "description": "适合回答关于物理学的问题",
            "prompt_template": physics_template
        },
        {
            "name": "math", 
            "description": "适合回答关于数学的问题",
            "prompt_template": math_template
        },
        {
            "name": "chemistry",
            "description": "适合回答关于化学的问题", 
            "prompt_template": chemistry_template
        }
    ]
    
    # 创建目标Chain
    destination_chains = {}
    for p_info in prompt_infos:
        name = p_info["name"]
        prompt_template = p_info["prompt_template"]
        prompt = PromptTemplate(template=prompt_template, input_variables=["input"])
        chain = LLMChain(llm=llm, prompt=prompt)
        destination_chains[name] = chain
    
    # 创建默认Chain
    default_prompt = PromptTemplate.from_template(
        "请回答以下问题：{input}"
    )
    default_chain = LLMChain(llm=llm, prompt=default_prompt)
    
    # 创建RouterChain
    router_template = """根据用户的问题，将其分类为physics、math或chemistry中的一种。

    用户问题：{input}

    输出格式：
    {{
        "destination": "physics" 或 "math" 或 "chemistry",
        "next_inputs": {{"input": "原始问题"}}
    }}
    """
    
    router_prompt = PromptTemplate(
        template=router_template,
        input_variables=["input"],
        output_parser=RouterOutputParser()
    )
    
    router_chain = LLMRouterChain.from_llm(llm, router_prompt)
    
    # 创建MultiPromptChain
    chain = MultiPromptChain(
        router_chain=router_chain,
        destination_chains=destination_chains,
        default_chain=default_chain,
        verbose=True
    )
    
    # 测试不同类型的问题
    test_questions = [
        "什么是牛顿第二定律？",
        "如何解二次方程？",
        "水的化学式是什么？",
        "为什么天空是蓝色的？"  # 物理问题
    ]
    
    for question in test_questions:
        print(f"问题: {question}")
        result = chain.invoke({"input": question})
        print(f"回答: {result['text']}")
        print("-" * 50)

def chat_chain_example():
    """聊天Chain示例"""
    print("=== 聊天Chain示例 ===")
    
    # 创建Chat模型
    chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
    
    # 创建聊天提示模板
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", "你是一个专业的{role}，具有{experience}经验。请以专业且友好的方式回答问题。"),
        ("human", "{question}")
    ])
    
    # 创建LLMChain（使用Chat模型）
    chat_chain = LLMChain(
        llm=chat_model,
        prompt=chat_prompt
    )
    
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
        print(f"回答: {result['text']}")
        print("=" * 50)

def chain_with_memory_example():
    """带记忆的Chain示例"""
    print("=== 带记忆的Chain示例 ===")
    
    from langchain.memory import ConversationBufferMemory
    from langchain.prompts import PromptTemplate
    
    # 创建记忆组件
    memory = ConversationBufferMemory()
    
    # 创建带有记忆的Prompt模板
    template = """你是一个友好的AI助手。以下是与用户的历史对话：

    {history}
    
    用户：{input}
    AI："""
    
    prompt = PromptTemplate(
        template=template,
        input_variables=["input", "history"]
    )
    
    # 创建LLMChain，绑定记忆
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)
    conversation_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=memory,
        verbose=True
    )
    
    # 模拟多轮对话
    conversations = [
        "我叫张三，很高兴认识你！",
        "我喜欢编程，特别是Python。",
        "你能推荐一些Python学习资源吗？",
        "记得我的名字吗？"
    ]
    
    for user_input in conversations:
        print(f"用户: {user_input}")
        result = conversation_chain.predict(input=user_input)
        print(f"AI: {result}")
        print("-" * 30)

def main():
    """主函数，运行所有示例"""
    print("LangChain Chains 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # LLMChain示例
        llm_chain_basic_example()
        
        # SequentialChain示例
        simple_sequential_chain_example()
        sequential_chain_example()
        
        # TransformChain示例
        transform_chain_example()
        
        # RouterChain示例
        router_chain_example()
        
        # 聊天Chain示例
        chat_chain_example()
        
        # 带记忆的Chain示例
        chain_with_memory_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
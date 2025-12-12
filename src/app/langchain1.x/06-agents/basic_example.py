#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Agents 组件基础示例
演示各种Agent类型和基础使用方法
"""

import os
import sys
from typing import Dict, List, Any
from langchain_openai import ChatOpenAI, OpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import SystemMessage
from langchain_community.tools import Tool
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# Agent components in LangChain 1.x
from langchain_classic.agents import (
    create_react_agent,
    create_structured_chat_agent,
    create_openai_functions_agent,
    AgentExecutor,
    load_tools
)
from langchain import hub

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_all_configs

# 从环境变量加载所有API配置
setup_all_configs()

def simple_react_agent_example():
    """简单的ReAct Agent示例"""
    print("=== 简单的ReAct Agent示例 ===")
    
    # 创建LLM
    llm = OpenAI(temperature=0)
    
    # 创建基础工具
    tools = [
        Tool(
            name="Calculator",
            description="用于执行数学计算",
            func=lambda x: str(eval(x)),
            return_direct=True
        ),
        Tool(
            name="Greeting",
            description="生成问候语",
            func=lambda x: f"你好，{x}！很高兴见到你。",
            return_direct=True
        )
    ]
    
    # 创建ReAct提示模板
    prompt = PromptTemplate.from_template("""
你是一个有用的AI助手。你有以下工具可以使用：

{tools}

使用以下格式：
Question: 需要回答的问题
Thought: 你应该思考要做什么
Action: 要采取的行动，应该是 [{tool_names}] 中的一个
Action Input: 行动的输入
Observation: 行动的结果
... (这个 Thought/Action/Action Input/Observation 可以重复N次)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终答案

开始！

Question: {input}
Thought: {agent_scratchpad}
""")
    
    # 创建Agent
    agent = create_react_agent(llm, tools, prompt)
    
    # 创建执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5
    )
    
    # 测试Agent
    questions = [
        "向张三问好",
        "计算 123 * 456",
        "向李四问好并计算 100 + 200"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        try:
            result = agent_executor.invoke({"input": question})
            print(f"答案: {result['output']}")
        except Exception as e:
            print(f"执行失败: {e}")
        print("-" * 50)

def search_agent_example():
    """带搜索功能的Agent示例"""
    print("=== 带搜索功能的Agent示例 ===")
    
    try:
        # 加载搜索工具
        tools = load_tools(["serpapi"], llm=OpenAI(temperature=0))
        
        # 添加计算工具
        calculator_tool = Tool(
            name="Calculator",
            description="执行数学计算",
            func=lambda x: str(eval(x))
        )
        tools.append(calculator_tool)
        
        # 创建LLM
        llm = OpenAI(temperature=0)
        
        # 使用hub中的ReAct提示
        prompt = hub.pull("hwchase17/react")
        
        # 创建Agent
        agent = create_react_agent(llm, tools, prompt)
        
        # 创建执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10
        )
        
        # 测试搜索功能
        questions = [
            "今天北京天气怎么样？",
            "Python编程语言的创建者是谁？",
            "计算2024年减去1991年的差值"
        ]
        
        for question in questions:
            print(f"\n问题: {question}")
            try:
                result = agent_executor.invoke({"input": question})
                print(f"答案: {result['output']}")
            except Exception as e:
                print(f"执行失败: {e} (可能需要设置SERPAPI_API_KEY)")
            print("-" * 50)
            
    except Exception as e:
        print(f"搜索Agent示例失败: {e}")
        print("请确保已设置SERPAPI_API_KEY环境变量")

def wikipedia_agent_example():
    """Wikipedia搜索Agent示例"""
    print("=== Wikipedia搜索Agent示例 ===")
    
    try:
        # 创建Wikipedia工具
        api_wrapper = WikipediaAPIWrapper(
            top_k_results=1,
            doc_content_chars_max=2000
        )
        wiki_tool = WikipediaQueryRun(api_wrapper=api_wrapper)
        
        # 创建工具列表
        tools = [wiki_tool]
        
        # 创建LLM
        llm = OpenAI(temperature=0)
        
        # 创建ReAct提示
        prompt = PromptTemplate.from_template("""
你是一个研究助手，可以使用Wikipedia查询信息。你有以下工具：

{tools}

使用以下格式：
Question: 需要回答的问题
Thought: 我需要搜索相关信息
Action: Wikipedia
Action Input: 搜索关键词
Observation: 搜索结果
Thought: 基于搜索结果回答问题
Final Answer: 最终答案

开始！

Question: {input}
Thought: {agent_scratchpad}
""")
        
        # 创建Agent
        agent = create_react_agent(llm, tools, prompt)
        
        # 创建执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5
        )
        
        # 测试Wikipedia搜索
        questions = [
            "什么是量子计算？",
            "爱因斯坦的相对论是什么？",
            "机器学习的主要分支有哪些？"
        ]
        
        for question in questions:
            print(f"\n问题: {question}")
            try:
                result = agent_executor.invoke({"input": question})
                print(f"答案: {result['output']}")
            except Exception as e:
                print(f"执行失败: {e}")
            print("-" * 50)
            
    except Exception as e:
        print(f"Wikipedia Agent示例失败: {e}")

def conversational_agent_example():
    """对话Agent示例"""
    print("=== 对话Agent示例 ===")
    
    # 创建LLM
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    
    # 创建工具
    tools = [
        Tool(
            name="CurrentTime",
            description="获取当前时间",
            func=lambda x: "当前时间：2024年1月1日 12:00:00"
        ),
        Tool(
            name="Calculator",
            description="执行数学计算",
            func=lambda x: str(eval(x))
        )
    ]
    
    # 创建对话提示
    prompt = PromptTemplate.from_template("""
你是一个友好的AI助手。你有以下工具可以使用：

{tools}

请以自然的方式与用户对话，在需要时使用工具。

工具名称：{tool_names}

Question: {input}
Thought: {agent_scratchpad}
""")
    
    # 创建Agent
    agent = create_react_agent(llm, tools, prompt)
    
    # 创建执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5
    )
    
    # 模拟多轮对话
    conversations = [
        "你好，我想了解一下AI",
        "现在几点了？",
        "帮我计算 25 * 4",
        "刚才的计算结果是多少？"
    ]
    
    for user_input in conversations:
        print(f"\n用户: {user_input}")
        try:
            result = agent_executor.invoke({"input": user_input})
            print(f"助手: {result['output']}")
        except Exception as e:
            print(f"执行失败: {e}")
        print("-" * 30)

def structured_chat_agent_example():
    """结构化聊天Agent示例"""
    print("=== 结构化聊天Agent示例 ===")
    
    try:
        # 创建LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
        # 创建工具
        tools = [
            Tool(
                name="get_weather",
                description="获取指定城市的天气信息",
                func=lambda city: f"{city}今天天气晴朗，温度25°C"
            ),
            Tool(
                name="calculate_tip",
                description="计算小费",
                func=lambda amount: f"账单{amount}元，建议小费{float(amount) * 0.15:.2f}元"
            )
        ]
        
        # 创建结构化聊天提示
        from langchain import hub
        prompt = hub.pull("hwchase17/structured-chat-agent")
        
        # 创建Agent
        agent = create_structured_chat_agent(llm, tools, prompt)
        
        # 创建执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5
        )
        
        # 测试结构化Agent
        questions = [
            "北京今天天气怎么样？",
            "账单是100元，应该给多少小费？",
            "上海天气如何，如果是50元账单小费多少？"
        ]
        
        for question in questions:
            print(f"\n问题: {question}")
            try:
                result = agent_executor.invoke({"input": question})
                print(f"答案: {result['output']}")
            except Exception as e:
                print(f"执行失败: {e}")
            print("-" * 50)
            
    except Exception as e:
        print(f"结构化聊天Agent示例失败: {e}")

def openai_functions_agent_example():
    """OpenAI Functions Agent示例"""
    print("=== OpenAI Functions Agent示例 ===")
    
    try:
        # 创建LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
        
        # 创建工具
        tools = [
            Tool(
                name="get_user_info",
                description="获取用户信息",
                func=lambda user_id: f"用户{user_id}：张三，年龄25，软件工程师"
            ),
            Tool(
                name="calculate_loan",
                description="计算贷款信息",
                func=lambda x: "贷款计算：月供2000元，总利息5000元"
            )
        ]
        
        # 创建OpenAI Functions提示
        from langchain import hub
        prompt = hub.pull("hwchase17/openai-functions-agent")
        
        # 创建Agent
        agent = create_openai_functions_agent(llm, tools, prompt)
        
        # 创建执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5
        )
        
        # 测试Functions Agent
        questions = [
            "获取用户123的信息",
            "计算一个贷款方案",
            "用户123的贷款方案是什么？"
        ]
        
        for question in questions:
            print(f"\n问题: {question}")
            try:
                result = agent_executor.invoke({"input": question})
                print(f"答案: {result['output']}")
            except Exception as e:
                print(f"执行失败: {e}")
            print("-" * 50)
            
    except Exception as e:
        print(f"OpenAI Functions Agent示例失败: {e}")

def custom_tool_agent_example():
    """自定义工具Agent示例"""
    print("=== 自定义工具Agent示例 ===")
    
    # 自定义工具
    def text_analyzer(text: str) -> str:
        """文本分析工具"""
        word_count = len(text.split())
        char_count = len(text)
        return f"文本分析：{word_count}个词，{char_count}个字符"
    
    def password_generator(length: int = 12) -> str:
        """密码生成工具"""
        import random
        import string
        chars = string.ascii_letters + string.digits + "!@#$%"
        password = ''.join(random.choice(chars) for _ in range(length))
        return f"生成的密码：{password}"
    
    # 创建工具列表
    tools = [
        Tool(
            name="text_analyzer",
            description="分析文本的词数和字符数",
            func=text_analyzer
        ),
        Tool(
            name="password_generator",
            description="生成安全密码，默认长度12位",
            func=password_generator
        )
    ]
    
    # 创建LLM
    llm = OpenAI(temperature=0)
    
    # 创建提示
    prompt = PromptTemplate.from_template("""
你是一个文本处理助手。你有以下工具：

{tools}

使用以下格式：
Question: 用户的问题
Thought: 思考如何回答
Action: 选择工具
Action Input: 工具输入
Observation: 工具输出
Thought: 基于结果给出最终答案
Final Answer: 最终答案

开始！

Question: {input}
Thought: {agent_scratchpad}
""")
    
    # 创建Agent
    agent = create_react_agent(llm, tools, prompt)
    
    # 创建执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5
    )
    
    # 测试自定义工具
    questions = [
        "分析这段文本：'LangChain是一个强大的AI开发框架'",
        "生成一个16位的密码",
        "分析刚才生成的密码"
    ]
    
    for question in questions:
        print(f"\n问题: {question}")
        try:
            result = agent_executor.invoke({"input": question})
            print(f"答案: {result['output']}")
        except Exception as e:
            print(f"执行失败: {e}")
        print("-" * 50)

def main():
    """主函数，运行所有示例"""
    print("LangChain Agents 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # 基础Agent示例
        simple_react_agent_example()
        
        # 功能Agent示例
        search_agent_example()
        wikipedia_agent_example()
        
        # 高级Agent示例
        conversational_agent_example()
        structured_chat_agent_example()
        openai_functions_agent_example()
        
        # 自定义工具示例
        custom_tool_agent_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY等环境变量")

if __name__ == "__main__":
    main()
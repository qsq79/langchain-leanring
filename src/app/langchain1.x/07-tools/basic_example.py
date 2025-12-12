#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Tools 组件基础示例
演示各种内置工具和基础自定义工具的使用方法
"""

import os
import sys
import time
from typing import Dict, List, Any, Optional
from langchain_openai import OpenAI
from langchain_community.tools import (
    WikipediaQueryRun,
    DuckDuckGoSearchRun,
    ShellTool,
    PythonREPLTool
)
from langchain_community.utilities import WikipediaAPIWrapper
from pydantic import BaseModel, Field
from langchain_core.prompts import PromptTemplate

# Tool components in LangChain 1.x
from langchain_classic.tools import Tool, tool
from langchain_classic.agents import create_react_agent, AgentExecutor

import requests
import json
import math

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

def simple_function_tool_example():
    """简单函数工具示例"""
    print("=== 简单函数工具示例 ===")
    
    # 定义简单函数
    def greet_person(name: str, age: int = 25) -> str:
        """问候函数"""
        return f"你好，{name}！你{age}岁，很高兴认识你！"
    
    def calculate_area(length: float, width: float) -> str:
        """计算矩形面积"""
        area = length * width
        return f"矩形面积：{area:.2f} 平方单位"
    
    def format_time(timestamp: Optional[float] = None) -> str:
        """格式化时间"""
        if timestamp is None:
            timestamp = time.time()
        
        time_struct = time.localtime(timestamp)
        formatted_time = time.strftime("%Y-%m-%d %H:%M:%S", time_struct)
        return f"当前时间：{formatted_time}"
    
    # 创建工具
    tools = [
        Tool(
            name="Greeting",
            description="向指定的人问好，参数：name（姓名），age（年龄，默认25）",
            func=greet_person
        ),
        Tool(
            name="CalculateArea",
            description="计算矩形面积，参数：length（长度），width（宽度）",
            func=calculate_area
        ),
        Tool(
            name="FormatTime",
            description="格式化时间戳为可读格式，参数：timestamp（可选的时间戳）",
            func=format_time
        )
    ]
    
    # 测试工具
    print("测试自定义函数工具：")
    
    # 测试问候工具
    greet_result = tools[0].func("张三", 30)
    print(f"问候结果: {greet_result}")
    
    # 测试面积计算工具
    area_result = tools[1].func(5.5, 3.2)
    print(f"面积计算: {area_result}")
    
    # 测试时间格式化工具
    time_result = tools[2].func()
    print(f"时间格式化: {time_result}")
    print()

def decorator_tool_example():
    """装饰器工具示例"""
    print("=== 装饰器工具示例 ===")
    
    # 使用@tool装饰器创建工具
    @tool
    def get_weather(city: str) -> str:
        """获取指定城市的天气信息
        
        Args:
            city: 城市名称
            
        Returns:
            天气信息字符串
        """
        # 模拟天气数据
        weather_data = {
            "北京": "晴天，温度25°C",
            "上海": "多云，温度28°C",
            "广州": "阵雨，温度30°C",
            "深圳": "晴天，温度29°C"
        }
        
        return weather_data.get(city, f"无法获取{city}的天气信息")
    
    @tool
    def calculate_compound_interest(principal: float, rate: float, years: int) -> str:
        """计算复利
        
        Args:
            principal: 本金金额
            rate: 年利率（百分比）
            years: 投资年数
            
        Returns:
            复利计算结果
        """
        amount = principal * (1 + rate/100) ** years
        interest = amount - principal
        
        return f"本金{principal}元，年利率{rate}%，投资{years}年后，本息合计{amount:.2f}元，利息{interest:.2f}元"
    
    @tool
    def analyze_text(text: str) -> str:
        """分析文本统计信息
        
        Args:
            text: 要分析的文本
            
        Returns:
            文本统计信息
        """
        word_count = len(text.split())
        char_count = len(text)
        char_count_no_spaces = len(text.replace(" ", ""))
        
        return f"文本分析：{word_count}个词，{char_count}个字符（含空格），{char_count_no_spaces}个字符（不含空格）"
    
    # 测试装饰器工具
    print("测试装饰器工具：")
    
    # 测试天气工具
    weather_result = get_weather("北京")
    print(f"天气查询: {weather_result}")
    
    # 测试复利计算
    interest_result = calculate_compound_interest(10000, 5, 3)
    print(f"复利计算: {interest_result}")
    
    # 测试文本分析
    text_result = analyze_text("LangChain是一个强大的AI开发框架，它简化了LLM应用的开发过程。")
    print(f"文本分析: {text_result}")
    print()

def pydantic_tool_example():
    """Pydantic工具示例"""
    print("=== Pydantic工具示例 ===")
    
    # 定义输入模型
    class BookSearchInput(BaseModel):
        """书籍搜索输入"""
        title: str = Field(description="书籍标题或关键词")
        author: Optional[str] = Field(default=None, description="作者姓名（可选）")
        max_results: int = Field(default=5, description="最大返回结果数")
    
    class LoanCalculatorInput(BaseModel):
        """贷款计算器输入"""
        principal: float = Field(description="贷款本金")
        annual_rate: float = Field(description="年利率（百分比）")
        loan_term: int = Field(description="贷款期限（月）")
        
    class TextAnalysisInput(BaseModel):
        """文本分析输入"""
        text: str = Field(description="要分析的文本")
        analysis_type: str = Field(description="分析类型：word_count, char_count, sentiment")
    
    # 创建工具
    def search_books(title: str, author: Optional[str] = None, max_results: int = 5) -> str:
        """搜索书籍信息"""
        # 模拟书籍数据库
        books_db = [
            {"title": "Python编程从入门到实践", "author": "Eric Matthes", "price": 89.00},
            {"title": "流畅的Python", "author": "Luciano Ramalho", "price": 128.00},
            {"title": "Python基础教程", "author": "Magnus Lie Hetland", "price": 69.00},
            {"title": "Python Cookbook", "author": "David Beazley", "price": 108.00}
        ]
        
        results = []
        for book in books_db:
            # 检查标题匹配
            if title.lower() in book["title"].lower():
                # 检查作者匹配（如果指定）
                if author is None or author.lower() in book["author"].lower():
                    results.append(book)
        
        # 限制结果数量
        results = results[:max_results]
        
        if not results:
            return f"未找到匹配的书籍：标题={title}，作者={author}"
        
        output = f"找到 {len(results)} 本书籍：\n"
        for i, book in enumerate(results, 1):
            output += f"{i}. 《{book['title']}》 - {book['author']}，价格：￥{book['price']}\n"
        
        return output
    
    def calculate_loan(principal: float, annual_rate: float, loan_term: int) -> str:
        """计算贷款月供"""
        monthly_rate = annual_rate / 100 / 12
        
        # 等额本息还款公式
        if monthly_rate == 0:
            monthly_payment = principal / loan_term
        else:
            monthly_payment = principal * monthly_rate * (1 + monthly_rate) ** loan_term / ((1 + monthly_rate) ** loan_term - 1)
        
        total_payment = monthly_payment * loan_term
        total_interest = total_payment - principal
        
        return f"贷款计算：\n本金：￥{principal:.2f}\n年利率：{annual_rate}%\n期限：{loan_term}个月\n月供：￥{monthly_payment:.2f}\n总利息：￥{total_interest:.2f}"
    
    def analyze_text_advanced(text: str, analysis_type: str) -> str:
        """高级文本分析"""
        if analysis_type == "word_count":
            words = text.split()
            return f"词数统计：{len(words)} 个词"
        elif analysis_type == "char_count":
            return f"字符统计：{len(text)} 个字符"
        elif analysis_type == "sentiment":
            # 简化的情感分析
            positive_words = ["好", "棒", "优秀", "喜欢", "推荐"]
            negative_words = ["差", "坏", "糟糕", "不满", "失望"]
            
            positive_count = sum(1 for word in positive_words if word in text)
            negative_count = sum(1 for word in negative_words if word in text)
            
            if positive_count > negative_count:
                return "情感分析：积极情感"
            elif negative_count > positive_count:
                return "情感分析：消极情感"
            else:
                return "情感分析：中性情感"
        else:
            return f"不支持的分析类型：{analysis_type}"
    
    # 使用Pydantic模型创建工具
    book_tool = Tool(
        name="SearchBooks",
        description="搜索书籍信息",
        func=search_books
    )
    
    loan_tool = Tool(
        name="CalculateLoan",
        description="计算贷款月供和总利息",
        func=calculate_loan
    )
    
    text_tool = Tool(
        name="AnalyzeTextAdvanced",
        description="高级文本分析",
        func=analyze_text_advanced
    )
    
    # 测试Pydantic工具
    print("测试Pydantic工具：")
    
    # 测试书籍搜索
    book_result = book_tool.func({"title": "Python", "max_results": 3})
    print(f"书籍搜索: {book_result}")
    
    # 测试贷款计算
    loan_result = loan_tool.func({"principal": 100000, "annual_rate": 4.9, "loan_term": 360})
    print(f"贷款计算: {loan_result}")
    
    # 测试高级文本分析
    text_result = text_tool.func({"text": "这本书真的很好，我非常喜欢，强烈推荐！", "analysis_type": "sentiment"})
    print(f"文本分析: {text_result}")
    print()

def built_in_tools_example():
    """内置工具示例"""
    print("=== 内置工具示例 ===")
    
    try:
        # Wikipedia搜索工具
        wikipedia = WikipediaQueryRun(
            api_wrapper=WikipediaAPIWrapper(
                top_k_results=2,
                doc_content_chars_max=1000
            )
        )
        
        # 测试Wikipedia搜索
        wiki_result = wikipedia.run("人工智能")
        print(f"Wikipedia搜索结果:\n{wiki_result[:200]}...\n")
        
    except Exception as e:
        print(f"Wikipedia工具失败: {e}")
    
    # 数学计算工具
    def safe_calculate(expression: str) -> str:
        """安全的数学计算"""
        try:
            # 只允许基本的数学运算
            allowed_chars = set("0123456789+-*/(). ")
            if not all(c in allowed_chars for c in expression):
                return "错误：表达式包含不允许的字符"
            
            result = eval(expression)
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"
    
    calculator_tool = Tool(
        name="SafeCalculator",
        description="安全的数学计算器，支持基本运算",
        func=safe_calculate
    )
    
    # 测试计算器
    calc_results = [
        calculator_tool.func("123 + 456"),
        calculator_tool.func("100 * 2.5"),
        calculator_tool.func("(50 + 30) * 2")
    ]
    
    print("计算器测试结果:")
    for result in calc_results:
        print(f"  {result}")
    
    print()

def agent_with_tools_example():
    """Agent使用工具示例"""
    print("=== Agent使用工具示例 ===")
    
    # 创建工具集合
    def get_stock_price(symbol: str) -> str:
        """获取股票价格"""
        # 模拟股票数据
        stock_data = {
            "AAPL": "Apple Inc. - $150.25",
            "GOOGL": "Alphabet Inc. - $2800.50",
            "MSFT": "Microsoft Corp. - $305.75",
            "TSLA": "Tesla Inc. - $250.80"
        }
        
        return stock_data.get(symbol.upper(), f"未找到股票代码：{symbol}")
    
    def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
        """货币转换"""
        # 模拟汇率数据
        exchange_rates = {
            "USD": {"CNY": 7.2, "EUR": 0.85, "JPY": 110.0},
            "CNY": {"USD": 0.14, "EUR": 0.12, "JPY": 15.3},
            "EUR": {"USD": 1.18, "CNY": 8.5, "JPY": 129.5}
        }
        
        try:
            if from_currency not in exchange_rates:
                return f"不支持的源货币：{from_currency}"
            
            if to_currency not in exchange_rates[from_currency]:
                return f"不支持的目标货币：{to_currency}"
            
            rate = exchange_rates[from_currency][to_currency]
            converted_amount = amount * rate
            
            return f"{amount} {from_currency} = {converted_amount:.2f} {to_currency}"
        except Exception as e:
            return f"货币转换失败：{str(e)}"
    
    def format_date(date_str: str, format_type: str = "standard") -> str:
        """日期格式化"""
        try:
            # 简化的日期格式化
            if format_type == "standard":
                return f"标准格式：{date_str}"
            elif format_type == "us":
                return f"美式格式：{date_str}"
            elif format_type == "european":
                return f"欧式格式：{date_str}"
            else:
                return f"不支持的格式类型：{format_type}"
        except Exception as e:
            return f"日期格式化失败：{str(e)}"
    
    # 创建工具列表
    tools = [
        Tool(
            name="GetStockPrice",
            description="获取股票价格，参数：symbol（股票代码）",
            func=get_stock_price
        ),
        Tool(
            name="ConvertCurrency",
            description="货币转换，参数：amount（金额），from_currency（源货币），to_currency（目标货币）",
            func=convert_currency
        ),
        Tool(
            name="FormatDate",
            description="日期格式化，参数：date_str（日期字符串），format_type（格式类型）",
            func=format_date
        )
    ]
    
    # 创建ReAct Agent
    llm = OpenAI(temperature=0)
    prompt = PromptTemplate.from_template("""
你是一个财务助手，可以查询股票价格和进行货币转换。

你有以下工具：
{tools}

工具名称：{tool_names}

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
    
    # 创建Agent和执行器
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5
    )
    
    # 测试Agent
    questions = [
        "查询Apple公司的股票价格",
        "将100美元转换为人民币",
        "查询Google股票价格并转换为欧元"
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
    print("LangChain Tools 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # 函数工具示例
        simple_function_tool_example()
        
        # 装饰器工具示例
        decorator_tool_example()
        
        # Pydantic工具示例
        pydantic_tool_example()
        
        # 内置工具示例
        built_in_tools_example()
        
        # Agent使用工具示例
        agent_with_tools_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
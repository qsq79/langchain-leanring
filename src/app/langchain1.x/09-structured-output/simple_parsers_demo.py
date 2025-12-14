#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 输出解析器简化演示
展示核心解析器的基本使用
"""

import os
import sys
import json
import re
from typing import List, Dict, Any

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../../../.env'))

def clean_env_value(value: str) -> str:
    """清理环境变量中的Unicode字符"""
    return re.sub(r'[\u201c\u201d\u201e\u201f\u00ab\u00bb"\'\u0060\u00b4]', '', value).strip()

# 设置清理后的环境变量
api_key = clean_env_value(os.getenv("OPENAI_API_KEY", ""))
api_base = clean_env_value(os.getenv("OPENAI_API_BASE", ""))

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
if api_base:
    os.environ["OPENAI_BASE_URL"] = api_base

# LangChain 导入
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import (
    StrOutputParser,
    JsonOutputParser,
    PydanticOutputParser,
    CommaSeparatedListOutputParser,
    BaseOutputParser
)
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

# 初始化模型
model = init_chat_model("gpt-3.5-turbo")

def demo_str_output_parser():
    """字符串输出解析器演示"""
    print("=== StrOutputParser 演示 ===")

    parser = StrOutputParser()

    prompt = ChatPromptTemplate.from_template("请简单回答：{question}")

    chain = prompt | model | parser
    result = chain.invoke({"question": "什么是LangChain？"})

    print(f"问题: 什么是LangChain？")
    print(f"答案: {result}")
    print(f"类型: {type(result)}")
    print()

def demo_json_output_parser():
    """JSON输出解析器演示"""
    print("=== JsonOutputParser 演示 ===")

    parser = JsonOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请用JSON格式介绍Python：
    {format_instructions}
    """)

    chain = prompt | model | parser
    result = chain.invoke({"format_instructions": parser.get_format_instructions()})

    print("JSON解析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"类型: {type(result)}")
    print()

def demo_pydantic_output_parser():
    """Pydantic输出解析器演示"""
    print("=== PydanticOutputParser 演示 ===")

    # 定义Pydantic模型
    class ProgrammingLanguage(BaseModel):
        name: str = Field(description="编程语言名称")
        year: int = Field(description="创建年份")
        creator: str = Field(description="创建者")
        features: List[str] = Field(description="主要特性")

    parser = PydanticOutputParser(pydantic_object=ProgrammingLanguage)

    prompt = ChatPromptTemplate.from_template("""
    请用JSON格式介绍Python：
    {format_instructions}
    """)

    chain = prompt | model | parser
    result = chain.invoke({"format_instructions": parser.get_format_instructions()})

    print("Pydantic解析结果:")
    print(f"名称: {result.name}")
    print(f"年份: {result.year}")
    print(f"创建者: {result.creator}")
    print(f"特性: {', '.join(result.features)}")
    print(f"类型: {type(result)}")
    print()

def demo_list_output_parser():
    """列表输出解析器演示"""
    print("=== CommaSeparatedListOutputParser 演示 ===")

    parser = CommaSeparatedListOutputParser()

    prompt = ChatPromptTemplate.from_template("请列出5种编程语言，用逗号分隔：")

    chain = prompt | model | parser
    result = chain.invoke({})

    print("逗号分隔列表解析结果:")
    print(f"结果: {result}")
    for i, item in enumerate(result, 1):
        print(f"  {i}. {item}")
    print(f"类型: {type(result)}")
    print()

def demo_custom_parser():
    """自定义解析器演示"""
    print("=== 自定义解析器演示 ===")

    class NumberedListParser(BaseOutputParser[List[str]]):
        def parse(self, text: str) -> List[str]:
            lines = text.strip().split('\n')
            result = []
            for line in lines:
                line = line.strip()
                # 匹配数字开头，如 "1. " 或 "1) "
                if line and line[0].isdigit():
                    # 移除数字编号和点/括号
                    clean_line = re.sub(r'^\d+[\.\)]\s*', '', line)
                    if clean_line:
                        result.append(clean_line.strip())
            return result

        def get_format_instructions(self) -> str:
            return "请使用编号列表格式，如：\n1. 第一个项目\n2. 第二个项目"

    parser = NumberedListParser()

    prompt = ChatPromptTemplate.from_template("""
    请用编号列表介绍学习Python的步骤：
    {format_instructions}
    """)

    chain = prompt | model | parser
    result = chain.invoke({"format_instructions": parser.get_format_instructions()})

    print("编号列表解析结果:")
    for i, item in enumerate(result, 1):
        print(f"  {i}. {item}")
    print()

def main():
    """主函数"""
    print("LangChain 输出解析器核心演示")
    print("=" * 50)
    print("展示最常用的输出解析器")
    print("=" * 50)
    print()

    try:
        demo_str_output_parser()
        demo_json_output_parser()
        demo_pydantic_output_parser()
        demo_list_output_parser()
        demo_custom_parser()

        print("✓ 所有演示完成！")
        print()
        print("核心要点：")
        print("1. StrOutputParser - 直接返回文本，最简单")
        print("2. JsonOutputParser - 解析JSON，支持嵌套结构")
        print("3. PydanticOutputParser - 强类型，自动验证")
        print("4. ListOutputParser - 解析列表数据")
        print("5. 自定义解析器 - 根据需求定制")

    except Exception as e:
        print(f"❌ 执行出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
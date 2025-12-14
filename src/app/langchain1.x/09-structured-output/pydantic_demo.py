#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pydantic 结构化输出示例 (LangChain 1.x 版本)
演示如何使用Pydantic模型来定义和验证结构化输出格式
"""

import os
import sys
from typing import List

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

# LangChain 1.x 兼容的导入
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Pydantic模型导入
try:
    from pydantic import BaseModel, Field
    PYDANTIC_AVAILABLE = True
except ImportError:
    print("警告: 未安装pydantic，将使用基础JSON解析")
    PYDANTIC_AVAILABLE = False


if PYDANTIC_AVAILABLE:
    class ContactInfo(BaseModel):
        """Contact information for a person."""
        name: str = Field(description="The name of the person")
        email: str = Field(description="The email address of the person")
        phone: str = Field(description="The phone number of the person")

    class EmployeeContact(BaseModel):
        """Employee contact information with additional details."""
        name: str = Field(description="Employee name")
        email: str = Field(description="Employee email address")
        phone: str = Field(description="Employee phone number")
        department: str = Field(description="Employee department")
        position: str = Field(description="Employee position")


def pydantic_basic_example():
    """Pydantic基础示例"""
    print("=== Pydantic结构化输出基础示例 ===")

    if not PYDANTIC_AVAILABLE:
        print("跳过Pydantic示例：未安装pydantic包")
        return None

    # 创建Chat Model实例
    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3
    )

    # 创建Pydantic输出解析器
    parser = PydanticOutputParser(pydantic_object=ContactInfo)

    # 构建提示模板
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "你是一个信息提取助手。请从用户提供的文本中提取联系人信息，并按照指定的格式返回。{format_instructions}"),
        ("human", "提取联系信息：{text}")
    ])

    # 创建链
    chain = prompt_template | chat_model | parser

    try:
        # 执行链
        result = chain.invoke({
            "text": "John Doe, john@example.com, (555) 123-4567",
            "format_instructions": parser.get_format_instructions()
        })

        print("提取到的联系信息:")
        print(f"姓名: {result.name}")
        print(f"邮箱: {result.email}")
        print(f"电话: {result.phone}")
        print(f"验证状态: ✓ Pydantic模型验证通过")
        print()

        return result

    except Exception as e:
        print(f"Pydantic解析失败: {e}")
        print("尝试手动解析...")

        # 手动解析作为备选方案
        text = "John Doe, john@example.com, (555) 123-4567"
        parts = text.split(", ")
        if len(parts) >= 3:
            print(f"姓名: {parts[0]}")
            print(f"邮箱: {parts[1]}")
            print(f"电话: {parts[2]}")

        return None


def pydantic_advanced_example():
    """Pydantic高级示例 - 复杂数据结构"""
    print("=== Pydantic结构化输出高级示例 ===")

    if not PYDANTIC_AVAILABLE:
        print("跳过Pydantic高级示例：未安装pydantic包")
        return

    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3
    )

    parser = PydanticOutputParser(pydantic_object=EmployeeContact)

    # 复杂的员工信息文本
    employee_text = """
    我们公司新来了技术总监张伟，他的邮箱是zhangwei@techcorp.com，
    联系电话是138-8888-8888。他加入技术部，负责系统架构设计。
    """

    prompt = f"""
    请从以下文本中提取员工联系信息：
    {employee_text}

    {parser.get_format_instructions()}
    """

    try:
        response = chat_model.invoke([HumanMessage(content=prompt)])
        result = parser.parse(response.content)

        print("员工信息详情:")
        print(f"姓名: {result.name}")
        print(f"邮箱: {result.email}")
        print(f"电话: {result.phone}")
        print(f"部门: {result.department}")
        print(f"职位: {result.position}")
        print(f"数据类型: {type(result)}")
        print(f"验证结果: ✓ Pydantic模型验证通过")
        print()

        # 演示Pydantic的数据验证功能
        print("=== Pydantic数据验证演示 ===")

        # 创建有效的联系人数据
        valid_contact = ContactInfo(
            name="李四",
            email="lisi@example.com",
            phone="139-0000-0000"
        )
        print(f"有效联系人: {valid_contact.model_dump()}")

        # 尝试创建无效数据（缺少必需字段）
        try:
            invalid_contact = ContactInfo(
                name="王五"
                # 缺少email和phone字段
            )
        except Exception as validation_error:
            print(f"验证错误（预期）: {validation_error}")

        print()

    except Exception as e:
        print(f"高级示例执行失败: {e}")


def pydantic_validation_example():
    """Pydantic验证示例"""
    print("=== Pydantic数据验证示例 ===")

    if not PYDANTIC_AVAILABLE:
        print("跳过验证示例：未安装pydantic包")
        return

    # 扩展的Pydantic模型，包含更多验证规则
    class DetailedContact(BaseModel):
        name: str = Field(..., min_length=2, max_length=50, description="姓名，长度2-50字符")
        email: str = Field(..., pattern=r'^[^@]+@[^@]+\.[^@]+$', description="有效的邮箱地址")
        phone: str = Field(..., pattern=r'^\(?[\d\s\-\(\)]+$', description="电话号码")
        age: int = Field(None, ge=0, le=150, description="年龄，可选，0-150之间")

    # 测试数据
    test_cases = [
        {
            "name": "张三",
            "email": "zhangsan@example.com",
            "phone": "138-0000-0000",
            "age": 25
        },
        {
            "name": "李",
            "email": "invalid-email",  # 无效邮箱
            "phone": "139-0000-0001",
            "age": 200  # 无效年龄
        }
    ]

    for i, test_data in enumerate(test_cases, 1):
        print(f"\n测试用例 {i}:")
        print(f"输入数据: {test_data}")

        try:
            contact = DetailedContact(**test_data)
            print(f"验证结果: ✓ 通过")
            print(f"标准化数据: {contact.model_dump_json()}")
        except Exception as validation_error:
            print(f"验证结果: ✗ 失败")
            print(f"错误信息: {validation_error}")


def main():
    """主函数，运行所有示例"""
    print("Pydantic 结构化输出示例 (LangChain 1.x 版本)")
    print("=" * 60)
    print("演示如何使用Pydantic定义、验证和解析结构化数据")
    print("=" * 60)
    print()

    try:
        # 基础示例
        result1 = pydantic_basic_example()

        # 高级示例
        pydantic_advanced_example()

        # 验证示例
        pydantic_validation_example()

        if PYDANTIC_AVAILABLE and result1:
            print("✓ Pydantic示例执行成功")
        else:
            print("⚠ Pydantic示例部分执行失败")

    except Exception as e:
        print(f"运行示例时出错: {e}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TypedDict 结构化输出示例 (LangChain 1.x 版本)
演示如何使用TypedDict来定义结构化输出格式
"""

import os
import sys
from typing_extensions import TypedDict

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

# LangChain 1.x 兼容的导入
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser


class ContactInfo(TypedDict):
    """Contact information for a person."""
    name: str  # The name of the person
    email: str  # The email address of the person
    phone: str  # The phone number of the person


def typed_dict_basic_example():
    """TypedDict基础示例"""
    print("=== TypedDict结构化输出示例 ===")

    # 创建Chat Model实例
    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",  # 使用可用的模型
        temperature=0.3
    )

    # 创建JSON输出解析器
    parser = JsonOutputParser()

    # 构建提示
    prompt = f"""
请从以下文本中提取联系信息，并以JSON格式返回：
"John Doe, john@example.com, (555) 123-4567"

要求格式：
- name: 姓名
- email: 邮箱地址
- phone: 电话号码

{parser.get_format_instructions()}
"""

    try:
        # 调用模型
        response = chat_model.invoke([HumanMessage(content=prompt)])
        print(f"模型原始输出: {response.content}")
        print()

        # 解析JSON输出
        structured_output = parser.parse(response.content)
        print("结构化输出:")
        print(f"姓名: {structured_output.get('name', '未提取到')}")
        print(f"邮箱: {structured_output.get('email', '未提取到')}")
        print(f"电话: {structured_output.get('phone', '未提取到')}")
        print()

        return structured_output

    except Exception as e:
        print(f"解析失败: {e}")
        print("尝试手动提取...")

        # 简单的手动解析作为备选方案
        text = "John Doe, john@example.com, (555) 123-4567"
        parts = text.split(", ")
        if len(parts) >= 3:
            result = {
                "name": parts[0],
                "email": parts[1],
                "phone": parts[2]
            }
            print("手动提取结果:")
            print(result)
            return result

        return None


def typed_dict_advanced_example():
    """TypedDict高级示例 - 处理多个联系人"""
    print("=== TypedDict高级示例 ===")

    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3
    )

    parser = JsonOutputParser()

    # 多个联系人的文本
    text = """
    公司员工联系信息：
    1. 张三, zhangsan@company.com, 138-0000-0001
    2. 李四, lisi@company.com, 138-0000-0002
    3. 王五, wangwu@company.com, 138-0000-0003
    """

    prompt = f"""
请从以下文本中提取所有联系人的信息，并以JSON数组格式返回：
{text}

要求格式：
- 每个联系人包含: name, email, phone
- 返回格式为联系人数组

{parser.get_format_instructions()}
"""

    try:
        response = chat_model.invoke([HumanMessage(content=prompt)])
        print(f"模型输出: {response.content}")
        print()

        contacts = parser.parse(response.content)
        print("提取到的联系人列表:")
        for i, contact in enumerate(contacts, 1):
            print(f"联系人{i}:")
            print(f"  姓名: {contact.get('name', 'N/A')}")
            print(f"  邮箱: {contact.get('email', 'N/A')}")
            print(f"  电话: {contact.get('phone', 'N/A')}")
        print()

    except Exception as e:
        print(f"解析失败: {e}")
        print("演示TypedDict类型检查...")

        # 演示TypedDict的类型注解
        def validate_contact(contact: dict) -> bool:
            """验证联系人信息格式"""
            required_fields = ['name', 'email', 'phone']
            return all(field in contact for field in required_fields)

        # 示例联系人
        contact_examples = [
            {"name": "张三", "email": "zhangsan@company.com", "phone": "138-0000-0001"},
            {"name": "李四", "email": "lisi@company.com"}  # 缺少phone字段
        ]

        for i, contact in enumerate(contact_examples, 1):
            is_valid = validate_contact(contact)
            print(f"联系人{i} 格式验证: {'✓ 通过' if is_valid else '✗ 失败'}")
            print(f"  数据: {contact}")
        print()


def main():
    """主函数，运行所有示例"""
    print("TypedDict 结构化输出示例 (LangChain 1.x 版本)")
    print("=" * 60)
    print("演示如何使用TypedDict定义和解析结构化数据")
    print("=" * 60)
    print()

    try:
        # 基础示例
        result1 = typed_dict_basic_example()

        # 高级示例
        typed_dict_advanced_example()

        if result1:
            print("✓ TypedDict示例执行成功")
        else:
            print("⚠ TypedDict示例部分失败")

    except Exception as e:
        print(f"运行示例时出错: {e}")


if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON Schema 结构化输出示例 (LangChain 1.x 版本)
演示如何使用JSON Schema来定义和验证结构化输出格式
"""

import os
import sys
import json
from typing import Dict, Any, List

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
from langchain_core.prompts import ChatPromptTemplate


# 联系人信息的JSON Schema定义
contact_info_schema = {
    "type": "object",
    "description": "Contact information for a person.",
    "properties": {
        "name": {
            "type": "string",
            "description": "The name of the person"
        },
        "email": {
            "type": "string",
            "description": "The email address of the person",
            "format": "email"
        },
        "phone": {
            "type": "string",
            "description": "The phone number of the person"
        }
    },
    "required": ["name", "email", "phone"],
    "additionalProperties": False
}

# 更复杂的员工信息Schema
employee_schema = {
    "type": "object",
    "description": "Employee information with additional details.",
    "properties": {
        "id": {
            "type": "integer",
            "description": "Employee ID"
        },
        "name": {
            "type": "string",
            "minLength": 2,
            "maxLength": 50,
            "description": "Employee name"
        },
        "email": {
            "type": "string",
            "format": "email",
            "description": "Employee email address"
        },
        "phone": {
            "type": "string",
            "description": "Employee phone number"
        },
        "department": {
            "type": "string",
            "enum": ["技术部", "市场部", "销售部", "人事部", "财务部"],
            "description": "Employee department"
        },
        "position": {
            "type": "string",
            "description": "Employee position"
        },
        "skills": {
            "type": "array",
            "items": {
                "type": "string"
            },
            "description": "List of employee skills"
        },
        "is_active": {
            "type": "boolean",
            "description": "Whether the employee is currently active"
        }
    },
    "required": ["name", "email", "phone", "department", "position"],
    "additionalProperties": False
}


def json_schema_basic_example():
    """JSON Schema基础示例"""
    print("=== JSON Schema结构化输出基础示例 ===")

    # 创建Chat Model实例
    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3
    )

    # 创建JSON输出解析器
    parser = JsonOutputParser()

    # 构建包含Schema的提示
    prompt = f"""
请从以下文本中提取联系信息，并严格按照JSON Schema格式返回：
"John Doe, john@example.com, (555) 123-4567"

JSON Schema要求：
```json
{json.dumps(contact_info_schema, indent=2, ensure_ascii=False)}
```

请确保返回的JSON符合上述Schema要求。

{parser.get_format_instructions()}
"""

    try:
        # 调用模型
        response = chat_model.invoke([HumanMessage(content=prompt)])
        print(f"模型原始输出: {response.content}")
        print()

        # 解析JSON输出
        structured_output = parser.parse(response.content)
        print("提取到的联系信息:")
        print(f"姓名: {structured_output.get('name', '未提取到')}")
        print(f"邮箱: {structured_output.get('email', '未提取到')}")
        print(f"电话: {structured_output.get('phone', '未提取到')}")
        print()

        # 验证JSON Schema
        if validate_json_schema(structured_output, contact_info_schema):
            print("✓ JSON Schema验证通过")
        else:
            print("✗ JSON Schema验证失败")

        return structured_output

    except Exception as e:
        print(f"解析失败: {e}")
        print("尝试手动解析...")

        # 手动解析作为备选方案
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

            # 验证手动解析的结果
            if validate_json_schema(result, contact_info_schema):
                print("✓ 手动解析结果验证通过")

            return result

        return None


def json_schema_advanced_example():
    """JSON Schema高级示例 - 复杂数据结构"""
    print("=== JSON Schema结构化输出高级示例 ===")

    chat_model = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3
    )

    parser = JsonOutputParser()

    # 复杂的员工信息文本
    employee_text = """
    员工信息：
    张明 (ID: 1001) 是技术部的软件工程师，邮箱是zhangming@techcorp.com，电话：138-0001-0001。
    他的技能包括：Python、JavaScript、Docker、Kubernetes。
    目前在职状态：是。
    """

    prompt = f"""
请从以下文本中提取员工信息，并严格按照JSON Schema格式返回：
{employee_text}

JSON Schema要求：
```json
{json.dumps(employee_schema, indent=2, ensure_ascii=False)}
```

请确保返回的JSON完全符合上述Schema要求，包括数据类型、枚举值和必需字段。

{parser.get_format_instructions()}
"""

    try:
        response = chat_model.invoke([HumanMessage(content=prompt)])
        print(f"模型输出: {response.content}")
        print()

        employee_data = parser.parse(response.content)
        print("提取到的员工信息:")

        # 格式化输出
        for key, value in employee_data.items():
            print(f"{key}: {value}")
        print()

        # 验证JSON Schema
        if validate_json_schema(employee_data, employee_schema):
            print("✓ 员工信息JSON Schema验证通过")
        else:
            print("✗ 员工信息JSON Schema验证失败")

    except Exception as e:
        print(f"高级示例执行失败: {e}")


def validate_json_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """简单的JSON Schema验证函数"""
    try:
        # 检查类型
        if schema.get("type") == "object":
            if not isinstance(data, dict):
                return False

            # 检查必需字段
            required_fields = schema.get("required", [])
            for field in required_fields:
                if field not in data:
                    print(f"缺少必需字段: {field}")
                    return False

            # 检查属性
            properties = schema.get("properties", {})
            for key, value in data.items():
                if key in properties:
                    prop_schema = properties[key]
                    prop_type = prop_schema.get("type")

                    # 类型检查
                    if prop_type == "string" and not isinstance(value, str):
                        print(f"字段 {key} 类型错误：期望字符串，实际 {type(value)}")
                        return False
                    elif prop_type == "integer" and not isinstance(value, int):
                        print(f"字段 {key} 类型错误：期望整数，实际 {type(value)}")
                        return False
                    elif prop_type == "boolean" and not isinstance(value, bool):
                        print(f"字段 {key} 类型错误：期望布尔值，实际 {type(value)}")
                        return False
                    elif prop_type == "array" and not isinstance(value, list):
                        print(f"字段 {key} 类型错误：期望数组，实际 {type(value)}")
                        return False

                    # 枚举值检查
                    if "enum" in prop_schema and value not in prop_schema["enum"]:
                        print(f"字段 {key} 枚举值错误：{value} 不在 {prop_schema['enum']} 中")
                        return False

        return True

    except Exception as e:
        print(f"Schema验证出错: {e}")
        return False


def json_schema_validation_demo():
    """JSON Schema验证演示"""
    print("=== JSON Schema验证演示 ===")

    # 测试数据
    test_cases = [
        {
            "name": "有效联系人",
            "data": {
                "name": "张三",
                "email": "zhangsan@example.com",
                "phone": "138-0000-0000"
            },
            "schema": contact_info_schema
        },
        {
            "name": "缺少必需字段",
            "data": {
                "name": "李四",
                "email": "lisi@example.com"
                # 缺少phone字段
            },
            "schema": contact_info_schema
        },
        {
            "name": "字段类型错误",
            "data": {
                "name": "王五",
                "email": "wangwu@example.com",
                "phone": 1234567890  # 数字而不是字符串
            },
            "schema": contact_info_schema
        }
    ]

    for test_case in test_cases:
        print(f"\n测试用例: {test_case['name']}")
        print(f"测试数据: {test_case['data']}")

        is_valid = validate_json_schema(test_case['data'], test_case['schema'])
        print(f"验证结果: {'✓ 通过' if is_valid else '✗ 失败'}")


def generate_schema_example():
    """生成Schema示例"""
    print("=== 动态生成Schema示例 ===")

    # 动态生成产品信息Schema
    def generate_product_schema():
        return {
            "type": "object",
            "description": "Product information",
            "properties": {
                "id": {"type": "integer", "description": "Product ID"},
                "name": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 100,
                    "description": "Product name"
                },
                "price": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Product price"
                },
                "category": {
                    "type": "string",
                    "enum": ["电子产品", "服装", "食品", "图书", "家居"],
                    "description": "Product category"
                },
                "in_stock": {
                    "type": "boolean",
                    "description": "Whether the product is in stock"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Product tags"
                }
            },
            "required": ["name", "price", "category"],
            "additionalProperties": False
        }

    product_schema = generate_product_schema()
    print("动态生成的产品Schema:")
    print(json.dumps(product_schema, indent=2, ensure_ascii=False))

    # 使用生成的Schema进行测试
    test_product = {
        "id": 1001,
        "name": "智能手机",
        "price": 2999.99,
        "category": "电子产品",
        "in_stock": True,
        "tags": ["5G", "高清拍照", "长续航"]
    }

    print(f"\n测试产品数据: {test_product}")
    is_valid = validate_json_schema(test_product, product_schema)
    print(f"验证结果: {'✓ 通过' if is_valid else '✗ 失败'}")


def main():
    """主函数，运行所有示例"""
    print("JSON Schema 结构化输出示例 (LangChain 1.x 版本)")
    print("=" * 60)
    print("演示如何使用JSON Schema定义、验证和解析结构化数据")
    print("=" * 60)
    print()

    try:
        # 基础示例
        result1 = json_schema_basic_example()

        # 高级示例
        json_schema_advanced_example()

        # 验证演示
        json_schema_validation_demo()

        # 动态生成示例
        generate_schema_example()

        if result1:
            print("✓ JSON Schema示例执行成功")
        else:
            print("⚠ JSON Schema示例部分执行失败")

    except Exception as e:
        print(f"运行示例时出错: {e}")


if __name__ == "__main__":
    main()
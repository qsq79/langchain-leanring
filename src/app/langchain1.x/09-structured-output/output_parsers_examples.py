#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain 输出解析器完整示例
演示各种输出解析器的实际使用方法和最佳实践
"""

import os
import sys
import json
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

# 设置环境变量（复用之前的配置）
import re
from dotenv import load_dotenv

os.environ['PYTHONIOENCODING'] = 'utf-8'
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
    SimpleJsonOutputParser,
    PydanticOutputParser,
    ListOutputParser,
    CommaSeparatedListOutputParser,
    NumberedListOutputParser,
    BaseOutputParser
)
from langchain_core.prompts import ChatPromptTemplate
# 注意：一些解析器可能在不同包中，需要根据实际安装情况导入
try:
    from langchain.output_parsers import (
        MarkdownListOutputParser,
        XMLOutputParser
    )
    LEGACY_PARSERS_AVAILABLE = True
except ImportError:
    print("注意: 某些解析器在新的LangChain版本中可能位于不同位置")
    LEGACY_PARSERS_AVAILABLE = False

# 创建替代的解析器
if not LEGACY_PARSERS_AVAILABLE:
    class MarkdownListOutputParser(BaseOutputParser):
        """简化的Markdown列表解析器"""
        def parse(self, text: str) -> List[str]:
            lines = text.strip().split('\n')
            result = []
            for line in lines:
                line = line.strip()
                if line.startswith(('-', '*', '+')):
                    result.append(line[1:].strip())
                elif line.startswith('1.'):
                    result.append(line[2:].strip())
            return result

        def get_format_instructions(self) -> str:
            return "请使用Markdown列表格式（- 项目）"

    class XMLOutputParser(BaseOutputParser):
        """简化的XML解析器"""
        def parse(self, text: str) -> Dict[str, Any]:
            # 简单的XML解析实现
            import re
            result = {}
            pattern = r'<(\w+)>(.*?)</\1>'
            matches = re.findall(pattern, text, re.DOTALL)
            for tag, content in matches:
                result[tag] = content.strip()
            return result

        def get_format_instructions(self) -> str:
            return "请使用XML格式，如<name>value</name>"

# 初始化模型
model = init_chat_model("gpt-3.5-turbo")

# ===================================================================
# 1. 基础文本解析器
# ===================================================================

def str_output_parser_example():
    """字符串输出解析器示例"""
    print("=== StrOutputParser 示例 ===")

    # 最简单的解析器 - 直接返回文本
    parser = StrOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请简单回答以下问题：
    {question}
    """)

    chain = prompt | model | parser
    result = chain.invoke({"question": "什么是LangChain？"})

    print(f"问题: 什么是LangChain？")
    print(f"答案: {result}")
    print(f"类型: {type(result)}")
    print()

# ===================================================================
# 2. JSON输出解析器
# ===================================================================

def json_output_parser_example():
    """JSON输出解析器示例"""
    print("=== JsonOutputParser 示例 ===")

    parser = JsonOutputParser()
    format_instructions = parser.get_format_instructions()

    prompt = ChatPromptTemplate.from_template("""
    请用JSON格式回答以下问题：

    问题：{question}

    {format_instructions}
    """)

    chain = prompt | model | parser
    result = chain.invoke({
        "question": "请介绍Python编程语言的3个主要特点",
        "format_instructions": format_instructions
    })

    print("JSON解析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"类型: {type(result)}")
    print()

def simple_json_output_parser_example():
    """简单JSON输出解析器示例"""
    print("=== SimpleJsonOutputParser 示例 ===")

    parser = SimpleJsonOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请用JSON格式回答：什么是AI？

    要求：包含definition和applications两个字段
    """)

    chain = prompt | model | parser
    result = chain.invoke({})

    print("简单JSON解析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

# ===================================================================
# 3. Pydantic输出解析器（强类型）
# ===================================================================

class ProgrammingLanguage(BaseModel):
    """编程语言模型"""
    name: str = Field(description="编程语言名称")
    year: int = Field(description="创建年份")
    creator: str = Field(description="创建者")
    features: List[str] = Field(description="主要特性列表")
    popularity_score: float = Field(description="流行度评分 (0-10)", ge=0, le=10)
    is_open_source: bool = Field(description="是否开源")

class Book(BaseModel):
    """书籍模型"""
    title: str = Field(description="书名")
    author: str = Field(description="作者")
    publication_year: int = Field(description="出版年份")
    genre: str = Field(description="类型")
    isbn: str = Field(description="ISBN编号")
    price: float = Field(description="价格")
    tags: List[str] = Field(description="标签")

def pydantic_output_parser_example():
    """Pydantic输出解析器示例"""
    print("=== PydanticOutputParser 示例 ===")

    # 创建解析器
    parser = PydanticOutputParser(pydantic_object=ProgrammingLanguage)

    prompt = ChatPromptTemplate.from_template("""
    请用JSON格式详细介绍一种编程语言：

    {query}

    {format_instructions}
    """)

    chain = prompt | model | parser
    result = chain.invoke({
        "query": "请详细介绍Python编程语言",
        "format_instructions": parser.get_format_instructions()
    })

    print("Pydantic解析结果（强类型对象）:")
    print(f"名称: {result.name}")
    print(f"创建年份: {result.year}")
    print(f"创建者: {result.creator}")
    print(f"特性: {', '.join(result.features)}")
    print(f"流行度: {result.popularity_score}/10")
    print(f"开源: {'是' if result.is_open_source else '否'}")
    print(f"类型: {type(result)}")
    print()

def multiple_pydantic_models_example():
    """多个Pydantic模型示例"""
    print("=== 多个Pydantic模型示例 ===")

    # 书籍解析器
    book_parser = PydanticOutputParser(pydantic_object=Book)

    book_prompt = ChatPromptTemplate.from_template("""
    请用JSON格式描述《Python编程：从入门到实践》这本书：

    {format_instructions}
    """)

    book_chain = book_prompt | model | book_parser
    book_result = book_chain.invoke({
        "format_instructions": book_parser.get_format_instructions()
    })

    print("书籍信息:")
    print(f"书名: {book_result.title}")
    print(f"作者: {book_result.author}")
    print(f"出版年份: {book_result.publication_year}")
    print(f"类型: {book_result.genre}")
    print(f"价格: ¥{book_result.price}")
    print(f"标签: {', '.join(book_result.tags)}")
    print()

# ===================================================================
# 4. 列表解析器
# ===================================================================

def list_output_parser_example():
    """列表输出解析器示例"""
    print("=== ListOutputParser 示例 ===")

    # 创建一个简单的列表解析器
    class SimpleListParser(BaseOutputParser[List[str]]):
        def parse(self, text: str) -> List[str]:
            # 尝试解析Python列表格式
            import ast
            try:
                return ast.literal_eval(text)
            except:
                # 如果解析失败，按行分割
                return [line.strip() for line in text.strip().split('\n') if line.strip()]

        def get_format_instructions(self) -> str:
            return "请输出Python列表格式，如：['项目1', '项目2', '项目3']"

    parser = SimpleListParser()

    prompt = ChatPromptTemplate.from_template("""
    请列出5种机器学习算法，用Python列表格式输出：
    """)

    chain = prompt | model | parser
    result = chain.invoke({})

    print("列表解析结果:")
    print(f"结果: {result}")
    print(f"类型: {type(result)}")
    print(f"元素数量: {len(result)}")
    print()

def comma_separated_list_parser_example():
    """逗号分隔列表解析器示例"""
    print("=== CommaSeparatedListOutputParser 示例 ===")

    parser = CommaSeparatedListOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请列出5种前端框架，用逗号分隔：
    """)

    chain = prompt | model | parser
    result = chain.invoke({})

    print("逗号分隔列表解析结果:")
    print(f"结果: {result}")
    for i, item in enumerate(result, 1):
        print(f"  {i}. {item}")
    print()

def numbered_list_parser_example():
    """编号列表解析器示例"""
    print("=== NumberedListOutputParser 示例 ===")

    parser = NumberedListOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请用编号列表格式介绍学习编程的步骤：
    """)

    chain = prompt | model | parser
    result = chain.invoke({})

    print("编号列表解析结果:")
    for i, item in enumerate(result, 1):
        print(f"  {i}. {item}")
    print()

def markdown_list_parser_example():
    """Markdown列表解析器示例"""
    print("=== MarkdownListOutputParser 示例 ===")

    parser = MarkdownListOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请用Markdown列表格式介绍Git的常用命令：
    """)

    chain = prompt | model | parser
    result = chain.invoke({})

    print("Markdown列表解析结果:")
    for i, item in enumerate(result, 1):
        print(f"  {i}. {item}")
    print()

# ===================================================================
# 5. XML输出解析器
# ===================================================================

def xml_output_parser_example():
    """XML输出解析器示例"""
    print("=== XMLOutputParser 示例 ===")

    parser = XMLOutputParser()

    prompt = ChatPromptTemplate.from_template("""
    请用XML格式描述一个学生信息：

    要求包含：姓名、年龄、年级、科目、成绩
    """)

    chain = prompt | model | parser
    result = chain.invoke({})

    print("XML解析结果:")
    print(f"结果: {result}")
    print(f"类型: {type(result)}")
    print()

# ===================================================================
# 6. 复杂综合示例
# ===================================================================

class Employee(BaseModel):
    """员工模型"""
    name: str = Field(description="姓名")
    position: str = Field(description="职位")
    department: str = Field(description="部门")
    skills: List[str] = Field(description="技能列表")
    experience_years: int = Field(description="工作年限")
    projects: List[str] = Field(description="参与项目")

class DepartmentAnalysis(BaseModel):
    """部门分析模型"""
    department_name: str = Field(description="部门名称")
    employee_count: int = Field(description="员工数量")
    average_experience: float = Field(description="平均工作经验")
    common_skills: List[str] = Field(description="常见技能")
    key_projects: List[str] = Field(description="重点项目")

def complex_parsing_example():
    """复杂解析示例"""
    print("=== 复杂综合解析示例 ===")

    # 员工信息解析
    employee_parser = PydanticOutputParser(pydantic_object=Employee)

    employee_prompt = ChatPromptTemplate.from_template("""
    请从以下文本中提取员工信息，并用JSON格式返回：

    文本：张三是一名高级软件工程师，在技术部工作，有5年工作经验。
    他精通Python、JavaScript和Docker，参与了电商平台和CRM系统的开发。

    {format_instructions}
    """)

    employee_chain = employee_prompt | model | employee_parser
    employee_result = employee_chain.invoke({
        "format_instructions": employee_parser.get_format_instructions()
    })

    print("员工信息解析结果:")
    print(f"姓名: {employee_result.name}")
    print(f"职位: {employee_result.position}")
    print(f"部门: {employee_result.department}")
    print(f"工作年限: {employee_result.experience_years}年")
    print(f"技能: {', '.join(employee_result.skills)}")
    print(f"项目: {', '.join(employee_result.projects)}")
    print()

# ===================================================================
# 7. 错误处理示例
# ===================================================================

class RobustJsonParser(JsonOutputParser):
    """健壮的JSON解析器"""

    def parse(self, text: str) -> Dict[str, Any]:
        """带错误恢复的JSON解析"""
        try:
            return super().parse(text)
        except Exception as e:
            print(f"标准JSON解析失败: {e}")
            print("尝试修复...")

            # 尝试常见的修复方法
            fixed_text = self._fix_json(text)
            return super().parse(fixed_text)

    def _fix_json(self, text: str) -> str:
        """修复常见的JSON格式问题"""
        # 移除markdown代码块标记
        text = text.replace('```json', '').replace('```', '')

        # 移除可能的引号问题
        text = text.strip()

        # 如果没有大括号，尝试包装
        if not text.startswith('{') and not text.startswith('['):
            text = f'{{"content": {json.dumps(text)}}}'

        return text

def error_handling_example():
    """错误处理示例"""
    print("=== 错误处理示例 ===")

    robust_parser = RobustJsonParser()

    prompt = ChatPromptTemplate.from_template("""
    请用JSON格式回答：什么是人工智能？

    注意：确保返回有效的JSON格式
    """)

    chain = prompt | model | robust_parser
    result = chain.invoke({})

    print("健壮解析结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    print()

# ===================================================================
# 8. 性能对比示例
# ===================================================================

def performance_comparison():
    """性能对比示例"""
    print("=== 性能对比示例 ===")

    import time

    # 测试文本
    test_text = """
    请用JSON格式介绍JavaScript：
    {
      "name": "JavaScript",
      "type": "编程语言",
      "year": 1995,
      "creator": "Brendan Eich",
      "features": ["动态类型", "解释执行", "事件驱动"]
    }
    """

    # 测试JsonOutputParser
    print("测试JsonOutputParser...")
    start_time = time.time()
    json_parser = JsonOutputParser()
    for _ in range(100):
        try:
            result = json_parser.parse(test_text)
        except:
            pass
    json_time = time.time() - start_time
    print(f"JsonOutputParser 100次解析耗时: {json_time:.4f}秒")

    # 测试SimpleJsonOutputParser
    print("测试SimpleJsonOutputParser...")
    start_time = time.time()
    simple_parser = SimpleJsonOutputParser()
    for _ in range(100):
        try:
            result = simple_parser.parse(test_text)
        except:
            pass
    simple_time = time.time() - start_time
    print(f"SimpleJsonOutputParser 100次解析耗时: {simple_time:.4f}秒")

    print(f"SimpleJsonParser 相对提升: {((json_time - simple_time) / json_time * 100):.1f}%")
    print()

# ===================================================================
# 9. 实际应用场景示例
# ===================================================================

class CustomerFeedback(BaseModel):
    """客户反馈模型"""
    customer_id: str = Field(description="客户ID")
    rating: int = Field(description="评分 (1-5)", ge=1, le=5)
    feedback_type: str = Field(description="反馈类型")
    summary: str = Field(description="反馈摘要")
    sentiment: str = Field(description="情感倾向")
    improvement_suggestions: List[str] = Field(description="改进建议")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "customer_id": "CUST_001",
                    "rating": 4,
                    "feedback_type": "产品功能",
                    "summary": "产品功能很好，但需要改进界面",
                    "sentiment": "中性",
                    "improvement_suggestions": ["简化界面", "增加用户引导"]
                }
            ]
        }
    }

def real_world_application():
    """实际应用场景示例"""
    print("=== 实际应用场景示例：客户反馈分析 ===")

    feedback_parser = PydanticOutputParser(pydantic_object=CustomerFeedback)

    feedback_text = """
    客户ID：CUST_12345

    我使用你们的产品已经3个月了，整体感觉不错！功能很强大，特别是数据分析功能，
    但是界面操作有些复杂，新手可能需要时间适应。客服响应很快，态度也很好。
    如果能简化操作流程就更好了。总体给4星评价！
    """

    prompt = ChatPromptTemplate.from_template("""
    请分析以下客户反馈，并用JSON格式提取关键信息：

    客户反馈：
    {feedback}

    {format_instructions}
    """)

    chain = prompt | model | feedback_parser
    result = chain.invoke({
        "feedback": feedback_text,
        "format_instructions": feedback_parser.get_format_instructions()
    })

    print("客户反馈分析结果:")
    print(f"客户ID: {result.customer_id}")
    print(f"评分: {result.rating}/5")
    print(f"反馈类型: {result.feedback_type}")
    print(f"摘要: {result.summary}")
    print(f"情感倾向: {result.sentiment}")
    print(f"改进建议:")
    for i, suggestion in enumerate(result.improvement_suggestions, 1):
        print(f"  {i}. {suggestion}")
    print()

# ===================================================================
# 10. 最佳实践总结
# ===================================================================

def best_practices_summary():
    """最佳实践总结"""
    print("=== 最佳实践总结 ===")

    practices = [
        "1. 解析器选择指南：",
        "   - 简单文本输出 → StrOutputParser",
        "   - 结构化数据 → JsonOutputParser",
        "   - 强类型需求 → PydanticOutputParser",
        "   - 列表数据 → 列表解析器系列",
        "",
        "2. 性能优化：",
        "   - 复用解析器实例，避免重复创建",
        "   - 简单场景使用SimpleJsonOutputParser",
        "   - 批量处理使用解析器的batch方法",
        "",
        "3. 错误处理：",
        "   - 实现自定义解析器处理特定错误",
        "   - 提供备选解析方案",
        "   - 记录解析失败的原因和频率",
        "",
        "4. 类型安全：",
        "   - 优先使用PydanticOutputParser",
        "   - 为Pydantic模型提供详细的字段描述",
        "   - 使用适当的验证规则和类型约束",
        "",
        "5. 格式说明：",
        "   - 始终包含格式说明（get_format_instructions()）",
        "   - 提供清晰的示例",
        "   - 明确指定必需字段和可选字段",
        "",
        "6. 组合使用：",
        "   - 可以链式组合多个解析器",
        "   - 使用RunnablePassthrough实现复杂处理",
        "   - 考虑使用并行解析提高效率"
    ]

    for practice in practices:
        print(practice)
    print()

# ===================================================================
# 主函数
# ===================================================================

def main():
    """主函数，运行所有示例"""
    print("LangChain 输出解析器完整示例")
    print("=" * 60)
    print("演示各种输出解析器的实际使用方法")
    print("=" * 60)
    print()

    try:
        # 1. 基础解析器
        str_output_parser_example()

        # 2. JSON解析器
        json_output_parser_example()
        simple_json_output_parser_example()

        # 3. Pydantic解析器
        pydantic_output_parser_example()
        multiple_pydantic_models_example()

        # 4. 列表解析器
        list_output_parser_example()
        comma_separated_list_parser_example()
        numbered_list_parser_example()
        markdown_list_parser_example()

        # 5. XML解析器
        xml_output_parser_example()

        # 6. 复杂综合示例
        complex_parsing_example()

        # 7. 错误处理
        error_handling_example()

        # 8. 性能对比
        performance_comparison()

        # 9. 实际应用
        real_world_application()

        # 10. 最佳实践
        best_practices_summary()

        print("✓ 所有示例执行完成！")

    except Exception as e:
        print(f"❌ 执行示例时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
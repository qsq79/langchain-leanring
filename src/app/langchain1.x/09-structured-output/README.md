# LangChain 结构化输出指南

## 📋 概述

结构化输出是构建可靠AI应用的关键技术。通过使用输出解析器，我们可以确保LLM输出的格式一致性和可预测性，将非结构化的文本转换为结构化的数据。

## 🗺️ 输出解析器体系

详细的结构化输出解析器体系请参考：
- **[`output_parsers_guide.md`](output_parsers_guide.md)** - 完整的解析器体系思维导图和详细说明

## 📁 示例文件

### 核心示例
- **[`simple_parsers_demo.py`](simple_parsers_demo.py)** - **推荐入门** - 核心解析器基础演示
- **[`output_parsers_examples.py`](output_parsers_examples.py)** - 完整的解析器示例（高级用法）
- **[`json_schema.py`](json_schema.py)** - JSON Schema 结构化输出示例

### 示例说明

#### [`simple_parsers_demo.py`](simple_parsers_demo.py)
适合快速学习，包含5个核心解析器：
- `StrOutputParser` - 最简单的文本输出
- `JsonOutputParser` - JSON格式解析
- `PydanticOutputParser` - 强类型解析器
- `CommaSeparatedListOutputParser` - 逗号分隔列表
- 自定义解析器 - 按需定制

#### [`output_parsers_examples.py`](output_parsers_examples.py)
完整功能演示，包含：
- 所有解析器类型详解
- 错误处理和恢复
- 性能对比
- 实际应用场景
- 最佳实践建议

## 🎯 解析器选择指南

| 场景 | 推荐解析器 | 示例文件 | 线路 |
|------|------------|----------|------|
| 简单文本输出 | `StrOutputParser` | simple_parsers_demo.py | 简单 |
| 结构化数据 | `JsonOutputParser` | simple_parsers_demo.py | 常用 |
| 强类型需求 | `PydanticOutputParser` | simple_parsers_demo.py | 推荐 |
| 列表数据 | `CommaSeparatedListOutputParser` | simple_parsers_demo.py | 实用 |
| 复杂结构 | 自定义解析器 | output_parsers_examples.py | 高级 |

## 🚀 快速开始

### 1. 基础使用
```python
# 最简单的解析器
from langchain_core.output_parsers import StrOutputParser
from langchain.chat_models import init_chat_model

model = init_chat_model("gpt-3.5-turbo")
parser = StrOutputParser()

chain = model | parser
result = chain.invoke("你好，请介绍一下你自己")
```

### 2. JSON解析
```python
# JSON输出解析
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
chain = model | parser

result = chain.invoke("请用JSON格式介绍Python")
# 返回：dict类型的结构化数据
```

### 3. 强类型解析
```python
# Pydantic强类型解析
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class Language(BaseModel):
    name: str = Field(description="语言名称")
    year: int = Field(description="创建年份")

parser = PydanticOutputParser(pydantic_object=Language)
chain = model | parser

result = chain.invoke("请用JSON格式介绍Python")
# 返回：Language对象，支持类型提示和验证
```

## 📚 学习路径

1. **入门**：运行 [`simple_parsers_demo.py`](simple_parsers_demo.py)，了解基础解析器
2. **进阶**：阅读 [`output_parsers_guide.md`](output_parsers_guide.md)，理解完整体系
3. **实践**：参考 [`json_schema.py`](json_schema.py)，学习实际应用
4. **深入**：探索 [`output_parsers_examples.py`](output_parsers_examples.py)，掌握高级技巧

## 🔧 实际应用

### 客户反馈分析
```python
class CustomerFeedback(BaseModel):
    customer_id: str
    rating: int  # 1-5分
    feedback_type: str
    summary: str
    sentiment: str  # 正面/中性/负面

parser = PydanticOutputParser(pydantic_object=CustomerFeedback)
# 自动解析客户反馈为结构化数据
```

### 数据提取
```python
# 从文本中提取结构化信息
parser = JsonOutputParser()
result = parser.invoke("请从邮件中提取：姓名、电话、邮箱、地址")
# 返回：{"name": "张三", "phone": "138...", "email": "...", "address": "..."}
```

## 📊 性能优化

- **解析器复用**：创建一次，多次使用
- **批量处理**：使用 `parser.parse_batch()`
- **错误处理**：实现健壮的解析逻辑
- **缓存结果**：相同查询结果可缓存

## ⚠️ 注意事项

1. **格式说明**：总是包含 `parser.get_format_instructions()`
2. **错误处理**：准备备选解析方案
3. **类型验证**：优先使用Pydantic获得安全保障
4. **测试覆盖**：为解析器编写单元测试

## 🔗 相关资源

- [LangChain Output Parsers 官方文档](https://python.langchain.com/docs/concepts/output_parsers/)
- [Pydantic 数据验证](https://pydantic-docs.helpmanual.io/)
- [JSON Schema 规范](https://json-schema.org/)
- [LangChain Expression Language](https://python.langchain.com/docs/concepts/lcel/)

---

💡 **提示**：建议从 [`simple_parsers_demo.py`](simple_parsers_demo.py) 开始学习，然后逐步深入到更复杂的解析器使用。
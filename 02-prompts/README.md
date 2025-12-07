# LangChain Prompts 组件学习指南

Prompts是LangChain框架中用于管理和优化提示词的核心组件。本指南将详细介绍Prompts组件的核心概念、使用方法和最佳实践。

## 📋 核心知识点

### 1. Prompt Templates（提示模板）

#### 1.1 基础Prompt Template
- **定义**：包含变量的可重用提示模板
- **特点**：支持变量替换、格式化输出
- **使用场景**：标准化提示格式、提高代码复用性

#### 1.2 Chat Prompt Template
- **定义**：专门为对话模型设计的提示模板
- **特点**：支持角色消息、系统提示、多轮对话
- **使用场景**：构建对话系统、角色扮演应用

#### 1.3 自定义Prompt Template
- **定义**：用户自定义的提示模板类
- **特点**：灵活的变量处理、自定义验证逻辑
- **使用场景**：复杂的提示工程需求

### 2. Example Selectors（示例选择器）

#### 2.1 基于相似度的选择器
- **LengthBasedExampleSelector**：基于长度的示例选择
- **SemanticSimilarityExampleSelector**：基于语义相似度的选择
- **MaxMarginalRelevanceExampleSelector**：基于最大边际相关性的选择

#### 2.2 选择策略
- **固定数量选择**：选择前N个最相关的示例
- **阈值选择**：选择相似度超过阈值的示例
- **多样性选择**：确保示例的多样性

### 3. Prompt Composition（提示组合）

#### 3.1 PipelinePromptTemplate
- **定义**：将多个提示模板串联组合
- **特点**：模块化设计、层次化组织
- **使用场景**：复杂的多步骤提示构建

#### 3.2 提示模板继承
- **定义**：基础模板的扩展和定制
- **特点**：代码复用、层次化设计
- **使用场景**：相关应用的提示模板管理

### 4. Output Parsers（输出解析器）

#### 4.1 基础解析器
- **StrOutputParser**：字符串输出解析
- **PydanticOutputParser**：结构化数据解析
- **JsonOutputParser**：JSON格式解析

#### 4.2 自定义解析器
- **定义**：用户定义的输出处理逻辑
- **特点**：灵活的数据转换、验证和格式化
- **使用场景**：特定的输出格式要求

## 🎯 常见面试题

### 基础概念题

**Q1: 什么是Prompt Template，它解决了什么问题？**

**A1:**
- **定义**：Prompt Template是包含变量的可重用提示模板，支持动态内容注入
- **解决的问题**：
  - **代码复用**：避免重复编写相似的提示词
  - **维护性**：集中管理提示逻辑，便于修改和优化
  - **一致性**：确保应用中使用统一的提示格式
  - **安全性**：通过参数化防止提示注入攻击
- **核心优势**：提高开发效率、降低维护成本、增强代码可读性

**Q2: Example Selector在Prompt工程中的作用是什么？**

**A2:**
- **作用**：智能选择最相关的示例来指导模型理解任务
- **核心功能**：
  - **上下文学习**：提供具体示例帮助模型理解任务要求
  - **相似度匹配**：基于语义相似度选择最相关的示例
  - **多样性保证**：确保选择集的多样性和代表性
- **应用场景**：Few-shot learning、任务示例展示、模型行为引导

### 技术实现题

**Q3: 如何实现一个自定义的Prompt Template？**

**A3:**
```python
from langchain_core.prompts import BasePromptTemplate
from pydantic import BaseModel, validator

class CustomPromptTemplate(BasePromptTemplate, BaseModel):
    """自定义提示模板示例"""
    
    template: str
    input_variables: list[str]
    custom_validator: str = "default"
    
    @validator("input_variables")
    def validate_input_variables(cls, v):
        if not v:
            raise ValueError("input_variables不能为空")
        return v
    
    def format(self, **kwargs) -> str:
        """格式化提示模板"""
        # 自定义验证逻辑
        for var in self.input_variables:
            if var not in kwargs:
                raise ValueError(f"缺少必需变量: {var}")
        
        # 自定义格式化逻辑
        formatted = self.template.format(**kwargs)
        
        if self.custom_validator == "uppercase":
            formatted = formatted.upper()
        elif self.custom_validator == "lowercase":
            formatted = formatted.lower()
            
        return formatted
    
    def _prompt_type(self) -> str:
        return "custom_prompt_template"
```

**Q4: 如何实现基于语义相似度的Example Selector？**

**A4:**
```python
from langchain_core.example_selectors.base import BaseExampleSelector
from langchain_openai import OpenAIEmbeddings
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class SemanticSimilaritySelector(BaseExampleSelector):
    """基于语义相似度的示例选择器"""
    
    def __init__(self, examples: list[dict], embeddings_model=None, k=3):
        self.examples = examples
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.k = k
        
        # 预计算所有示例的嵌入
        self.example_texts = [example["input"] for example in examples]
        self.example_embeddings = self.embeddings_model.embed_documents(self.example_texts)
    
    def add_example(self, example: dict) -> None:
        """添加新示例"""
        self.examples.append(example)
        text = example["input"]
        embedding = self.embeddings_model.embed_query(text)
        self.example_texts.append(text)
        self.example_embeddings.append(embedding)
    
    def select_examples(self, input_variables: dict[str, str]) -> list[dict]:
        """选择最相关的示例"""
        input_text = input_variables.get("input", "")
        input_embedding = self.embeddings_model.embed_query(input_text)
        
        # 计算相似度
        similarities = cosine_similarity(
            [input_embedding], 
            self.example_embeddings
        )[0]
        
        # 获取top-k最相似的示例索引
        top_indices = np.argsort(similarities)[-self.k:][::-1]
        
        # 返回选中的示例
        return [self.examples[i] for i in top_indices]
```

### 架构设计题

**Q5: LangChain的Prompt组件采用了什么设计模式？**

**A5:**
- **模板方法模式**：BasePromptTemplate定义算法骨架，子类实现具体格式化逻辑
- **策略模式**：不同的Example Selector实现不同的选择策略
- **工厂模式**：通过from_template等方法创建模板实例
- **组合模式**：PipelinePromptTemplate将多个模板组合成复杂结构
- **装饰器模式**：Output Parser对基础输出进行装饰和处理

## 🏗️ 设计思路和设计模式

### 1. 模板化设计

#### 1.1 变量替换机制
```python
from langchain_core.prompts import PromptTemplate

# 基础模板
template = """
请分析以下{subject}的特点：
背景：{background}
要求：{requirements}
分析：
"""

prompt = PromptTemplate(
    template=template,
    input_variables=["subject", "background", "requirements"]
)
```

#### 1.2 类型安全设计
```python
from pydantic import BaseModel, Field
from langchain_core.prompts import BasePromptTemplate

class TypedPromptTemplate(BasePromptTemplate, BaseModel):
    """类型安全的提示模板"""
    
    subject: str = Field(description="分析主题")
    background: str = Field(description="背景信息")
    requirements: str = Field(description="具体要求")
    
    def format(self, **kwargs) -> str:
        # Pydantic自动验证类型
        validated = self.__class__(**kwargs)
        return f"分析{validated.subject}，背景：{validated.background}，要求：{validated.requirements}"
```

### 2. 选择器架构

#### 2.1 策略模式实现
```python
from abc import ABC, abstractmethod

class SelectionStrategy(ABC):
    """选择策略抽象基类"""
    
    @abstractmethod
    def select(self, examples, query, k):
        pass

class SimilarityStrategy(SelectionStrategy):
    """相似度选择策略"""
    
    def select(self, examples, query, k):
        # 实现相似度选择逻辑
        pass

class DiversityStrategy(SelectionStrategy):
    """多样性选择策略"""
    
    def select(self, examples, query, k):
        # 实现多样性选择逻辑
        pass

class FlexibleExampleSelector(BaseExampleSelector):
    """支持策略切换的示例选择器"""
    
    def __init__(self, strategy: SelectionStrategy):
        self.strategy = strategy
    
    def set_strategy(self, strategy: SelectionStrategy):
        self.strategy = strategy
```

#### 2.2 缓存优化
```python
from functools import lru_cache
import hashlib

class CachedExampleSelector(BaseExampleSelector):
    """带缓存的示例选择器"""
    
    def __init__(self, base_selector):
        self.base_selector = base_selector
    
    @lru_cache(maxsize=128)
    def _get_cache_key(self, query_hash):
        return query_hash
    
    def select_examples(self, input_variables):
        query = input_variables.get("input", "")
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        # 检查缓存
        if self._get_cache_key(query_hash):
            return self._cached_result
        
        # 计算结果并缓存
        result = self.base_selector.select_examples(input_variables)
        self._cached_result = result
        return result
```

### 3. 组合模式设计

#### 3.1 Pipeline组合
```python
from langchain_core.prompts import PipelinePromptTemplate

# 定义子模板
introduction_template = PromptTemplate(
    template="你是一个{role}，专门处理{domain}相关的问题。",
    input_variables=["role", "domain"]
)

task_template = PromptTemplate(
    template="当前任务：{task}\n具体要求：{requirements}",
    input_variables=["task", "requirements"]
)

format_template = PromptTemplate(
    template="请按照{format}格式输出答案。",
    input_variables=["format"]
)

# 组合成完整模板
full_prompt = PipelinePromptTemplate(
    pipeline_prompts=[
        ("introduction", introduction_template),
        ("task", task_template),
        ("format", format_template)
    ],
    final_prompt="{introduction}\n{task}\n{format}"
)
```

#### 3.2 模板继承
```python
class BaseAnalysisPrompt(BasePromptTemplate):
    """分析任务基础模板"""
    
    def __init__(self, task_type: str):
        self.task_type = task_type
        super().__init__(
            template=f"请进行{task_type}分析：\n内容：{{content}}\n要求：{{requirements}}",
            input_variables=["content", "requirements"]
        )

class SentimentAnalysisPrompt(BaseAnalysisPrompt):
    """情感分析特化模板"""
    
    def __init__(self):
        super().__init__("情感")
        self.output_format = "正面/负面/中性"
    
    def format(self, **kwargs):
        base_prompt = super().format(**kwargs)
        return f"{base_prompt}\n输出格式：{self.output_format}"
```

## 🚀 最佳实践

### 1. 提示工程原则

1. **明确性原则**：提示要清晰明确，避免歧义
2. **具体性原则**：提供具体的示例和格式要求
3. **渐进性原则**：从简单到复杂逐步引导模型
4. **一致性原则**：保持提示格式和术语的一致性

### 2. 性能优化

```python
# 批量处理优化
def batch_format_prompts(template, inputs_list):
    """批量格式化提示"""
    return [template.format(**inputs) for inputs in inputs_list]

# 预编译模板
class CompiledPromptTemplate:
    def __init__(self, template):
        self.compiled = template.compile()
    
    def format(self, **kwargs):
        return self.compiled.substitute(**kwargs)
```

### 3. 错误处理和验证

```python
from pydantic import ValidationError

def safe_format_prompt(template, **kwargs):
    """安全的提示格式化"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        raise ValueError(f"缺少必需参数: {e}")
    except ValidationError as e:
        raise ValueError(f"参数验证失败: {e}")
```

## 📊 性能对比

| 组件类型 | 响应时间 | 内存使用 | 适用场景 | 复杂度 |
|---------|---------|---------|----------|--------|
| PromptTemplate | 快 | 低 | 简单模板替换 | 低 |
| ChatPromptTemplate | 中-快 | 中 | 对话场景 | 中 |
| PipelinePromptTemplate | 中 | 中-高 | 复杂组合场景 | 高 |
| CustomPromptTemplate | 可变 | 可变 | 特殊需求 | 高 |

## 🔗 相关资源

- [LangChain Prompts官方文档](https://python.langchain.com/docs/modules/model_io/prompts/)
- [Prompt工程指南](https://www.promptingguide.ai/)
- [OpenAI Prompt最佳实践](https://platform.openai.com/docs/guides/prompt-engineering)

---

💡 **学习建议**：建议从基础的PromptTemplate开始学习，然后掌握Example Selector的使用，最后学习如何设计复杂的组合模板和自定义模板。
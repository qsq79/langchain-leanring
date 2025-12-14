# LangChain Models 组件学习指南 (LangChain 1.x 版本)

Models是LangChain框架中最基础的组件，负责与各种语言模型进行交互。本指南将详细介绍Models组件在LangChain 1.x中的核心概念、使用方法和最佳实践。

## 📋 LangChain 1.x 核心变化

### 导入路径变化
- **从 langchain 到 langchain_core**: 基础接口和消息类已移至 `langchain_core`
- **专门包**: 提供商特定的包如 `langchain_openai`, `langchain_community`
- **模块化架构**: 核心功能与社区插件分离

### 新特性
- **异步支持**: 所有的模型都支持异步调用
- **LCEL兼容**: 与LangChain Expression Language完全兼容
- **改进的错误处理**: 更好的异常处理和重试机制

## 🎯 Models组件分类

### 1. LLMs (Large Language Models)

#### LangChain 1.x 中的变化
- 从 `langchain.llms` 移至 `langchain_openai.OpenAI`
- 推荐使用 `ChatOpenAI` 替代传统 LLM
- 增强的流式输出支持

```python
# LangChain 1.x 推荐写法
from langchain_openai import OpenAI

llm = OpenAI(
    model="gpt-3.5-turbo-instruct",
    temperature=0.7
)

# 支持流式输出
for chunk in llm.stream("写一首诗"):
    print(chunk, end="")

# 支持异步调用
result = await llm.ainvoke("Hello, world!")
```

### 2. Chat Models

#### LangChain 1.x 新特性
- 结构化输出支持
- 更好的异步流式输出
- 与 LCEL 完全兼容
- **统一模型初始化** (`init_chat_model`)

```python
# 方法1: 传统方式 (仍然支持)
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 创建聊天模型
chat_model = ChatOpenAI(model="gpt-3.5-turbo")

# 使用 LCEL 创建链
prompt = ChatPromptTemplate.from_template("请用中文回答：{question}")
chain = prompt | chat_model | StrOutputParser()

# 执行
result = chain.invoke({"question": "什么是AI？"})
```

#### init_chat_model - LangChain 1.x 推荐方式

```python
# 方法2: init_chat_model (推荐)
from langchain.chat_models import init_chat_model

# 最简单的初始化 - 自动从环境变量读取配置
model = init_chat_model("gpt-4")

# 带参数的初始化
model = init_chat_model(
    "gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=100
)

# 支持多种模型提供商
openai_model = init_chat_model("gpt-4")           # OpenAI
anthropic_model = init_chat_model("claude-3")     # Anthropic (需要 langchain-anthropic)
google_model = init_chat_model("gemini-pro")      # Google (需要 langchain-google-genai)

# 完全相同的调用方式
response = model.invoke([HumanMessage(content="你好！")])
```

#### 结构化输出 (新特性)
```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class Answer(BaseModel):
    summary: str = Field(description="回答摘要")
    details: List[str] = Field(description="详细要点")

parser = JsonOutputParser(pydantic_object=Answer)
chain = prompt | chat_model | parser
result = chain.invoke({"question": "什么是机器学习？"})
```

### 3. Text Embedding Models

#### LangChain 1.x 变化
- 支持最新的 embedding 模型
- 异步嵌入生成
- 更好的批处理支持

```python
# LangChain 1.x 推荐写法
from langchain_openai import OpenAIEmbeddings

# 使用最新模型
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# 异步嵌入生成
vector = await embeddings.aembed_query("查询文本")

# 批量异步处理
texts = ["文本1", "文本2", "文本3"]
tasks = [embeddings.aembed_query(text) for text in texts]
vectors = await asyncio.gather(*tasks)
```

## 🔧 核心接口设计

### 1. BaseLLM接口 (langchain_core)
```python
from langchain_core.language_models.llms import BaseLLM

class CustomLLM(BaseLLM):
    @property
    def _llm_type(self) -> str:
        return "custom_llm"

    def _call(
        self,
        prompt: str,
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> str:
        # 实现
        pass

    async def _acall(self, prompt: str, **kwargs) -> str:
        # 异步实现 (LangChain 1.x 新增)
        pass
```

### 2. BaseChatModel接口 (langchain_core)
```python
from langchain_core.language_models.chat_models import BaseChatModel

class CustomChatModel(BaseChatModel):
    def _generate(
        self,
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> ChatResult:
        # 实现
        pass

    async def _agenerate(
        self,
        messages: List[List[BaseMessage]],
        **kwargs: Any,
    ) -> ChatResult:
        # 异步实现 (LangChain 1.x 新增)
        pass
```

### 3. BaseEmbeddings接口 (langchain_core)
```python
from langchain_core.embeddings import Embeddings

class CustomEmbeddings(Embeddings):
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        # 实现
        pass

    def embed_query(self, text: str) -> List[float]:
        # 实现
        pass

    async def aembed_documents(self, texts: List[str]) -> List[List[float]]:
        # 异步实现 (LangChain 1.x 新增)
        pass

    async def aembed_query(self, text: str) -> List[float]:
        # 异步实现 (LangChain 1.x 新增)
        pass
```

## 🚀 LangChain 1.x 新特性

### 1. 异步支持
所有模型现在都支持异步操作：

```python
import asyncio
from langchain_openai import ChatOpenAI

chat_model = ChatOpenAI()

# 并发处理多个请求
async def process_questions():
    questions = ["问题1", "问题2", "问题3"]
    tasks = [chat_model.ainvoke([HumanMessage(content=q)]) for q in questions]
    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(process_questions())
```

### 2. 改进的流式输出
```python
# 同步流式
for chunk in chat_model.stream(messages):
    print(chunk.content, end="")

# 异步流式
async for chunk in chat_model.astream(messages):
    print(chunk.content, end="")
```

### 3. LCEL 集成
```python
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# 创建复杂的处理链
chain = (
    RunnablePassthrough.assign(
        embedding=lambda x: embeddings.embed_query(x["text"])
    ) | RunnableParallel({
        "summary": summary_prompt | chat_model | StrOutputParser(),
        "keywords": keywords_prompt | chat_model | StrOutputParser()
    })
)
```

## 🎯 常见面试题 (LangChain 1.x 版本)

### 基础概念题

**Q1: LangChain 1.x 中 Models 组件的主要变化是什么？**

**A1:**
- **导入路径变化**: 从 `langchain` 移至 `langchain_core` 和专门包
- **异步支持**: 所有模型都支持 `ainvoke()`, `astream()`, `abatch()` 等异步方法
- **LCEL兼容**: 完全支持 LangChain Expression Language
- **结构化输出**: Chat Models 支持原生结构化输出
- **改进的错误处理**: 更好的异常处理和重试机制

**Q2: 如何在 LangChain 1.x 中实现自定义LLM？**

**A2:**
```python
from langchain_core.language_models.llms import BaseLLM
from langchain_core.callbacks import CallbackManagerForLLMRun

class CustomLLM(BaseLLM):
    def _call(self, prompt: str, stop=None, run_manager=None, **kwargs):
        # 同步实现
        return response

    async def _acall(self, prompt: str, stop=None, run_manager=None, **kwargs):
        # 异步实现 (LangChain 1.x 新增)
        await asyncio.sleep(0.1)  # 模拟网络延迟
        return response

    @property
    def _llm_type(self) -> str:
        return "custom_llm"
```

### 技术实现题

**Q3: 如何在 LangChain 1.x 中实现结构化输出？**

**A3:**
```python
from langchain_core.output_parsers import JsonOutputParser, PydanticOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List

# 定义输出结构
class AnalysisResult(BaseModel):
    summary: str = Field(description="摘要")
    key_points: List[str] = Field(description="关键要点")
    sentiment: str = Field(description="情感倾向")

# 创建解析器
parser = JsonOutputParser(pydantic_object=AnalysisResult)

# 创建链
prompt = ChatPromptTemplate.from_template(
    "分析以下文本：{text}\n\n{format_instructions}"
)
chain = prompt | chat_model | parser

# 执行
result = chain.invoke({
    "text": "要分析的文本",
    "format_instructions": parser.get_format_instructions()
})
```

**Q4: 如何处理模型的异步调用和错误重试？**

**A4:**
```python
import asyncio
from functools import wraps
from langchain_core.exceptions import LangChainException

def retry_with_backoff(max_retries=3, backoff_factor=2.0):
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except LangChainException as e:
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(backoff_factor ** attempt)
        return async_wrapper
    return decorator

@retry_with_backoff()
async def robust_llm_call(prompt: str):
    return await chat_model.ainvoke([HumanMessage(content=prompt)])
```

### 架构设计题

**Q5: LangChain 1.x 的 Models 组件架构设计有什么改进？**

**A5:**
- **模块化分离**: 核心接口在 `langchain_core`，实现在专门包中
- **异步优先**: 从设计层面支持异步操作
- **LCEL集成**: 作为可运行组件完全集成到表达语言中
- **类型安全**: 更好的类型提示和验证
- **插件化**: 更容易添加新的模型提供商

## 🏗️ 最佳实践

### 1. 模型选择策略
```python
# LangChain 1.x 推荐的模型选择
def get_model(use_chat=True, use_async=False):
    if use_chat:
        return ChatOpenAI(model="gpt-3.5-turbo")
    else:
        return OpenAI(model="gpt-3.5-turbo-instruct")

# 批量处理优化
async def batch_process(texts):
    embeddings = OpenAIEmbeddings()
    tasks = [embeddings.aembed_query(text) for text in texts]
    return await asyncio.gather(*tasks)
```

### 2. 性能优化
```python
# 使用 LCEL 优化链式调用
optimized_chain = (
    RunnableParallel({
        "text": lambda x: x["input"],
        "embedding": embeddings | RunnableLambda(lambda e: e)
    })
    | RunnablePassthrough.assign(
        summary=summary_prompt | chat_model | StrOutputParser()
    )
)

# 异步批处理
async def process_batch(items):
    semaphore = asyncio.Semaphore(10)  # 限制并发数

    async def process_single(item):
        async with semaphore:
            return await chat_model.ainvoke(item)

    tasks = [process_single(item) for item in items]
    return await asyncio.gather(*tasks)
```

### 3. 错误处理和监控
```python
from langchain_core.callbacks import get_openai_callback

async def monitored_call(prompt):
    with get_openai_callback() as cb:
        try:
            result = await chat_model.ainvoke(prompt)
            print(f"Cost: ${cb.total_cost:.6f}")
            return result
        except Exception as e:
            print(f"Error: {e}")
            raise
```

## 📊 性能对比 (LangChain 1.x)

| 特性 | LangChain 0.x | LangChain 1.x |
|------|---------------|---------------|
| 异步支持 | 有限 | 原生支持 |
| 结构化输出 | 需要手动解析 | 原生支持 |
| LCEL集成 | 部分支持 | 完全支持 |
| 错误处理 | 基础 | 增强 |
| 类型安全 | 基础 | 完善 |
| 流式输出 | 支持 | 改进 |

## 🔗 相关资源

- [LangChain Models 官方文档](https://python.langchain.com/docs/modules/model_io/models/)
- [LangChain 1.x 迁移指南](https://python.langchain.com/docs/versions/migrating_to_lcel/)
- [OpenAI API 文档](https://platform.openai.com/docs/api-reference)
- [LangChain Expression Language 指南](https://python.langchain.com/docs/concepts/lcel/)

## 📁 示例文件

- [`basic_example.py`](basic_example.py) - 完整的基础示例，包含LLM、Chat Models和Embeddings
- [`advanced_example.py`](advanced_example.py) - 高级特性示例
- [`init_chat_model_example.py`](init_chat_model_example.py) - **新增** - init_chat_model统一初始化方式示例

### init_chat_model 示例文件特性

该示例展示了 LangChain 1.x 中推荐的模型初始化方式：

- **基础使用** - 最简单的模型初始化
- **多提供商支持** - OpenAI、Anthropic、Google等
- **参数配置** - temperature、max_tokens等
- **流式输出** - 实时响应流
- **异步调用** - 并发处理示例
- **多轮对话** - 对话历史管理
- **批量处理** - 高效批量调用
- **结构化输出** - JSON格式输出
- **错误处理** - 异常处理最佳实践
- **性能对比** - 不同模型性能对比

---

💡 **学习建议**：建议从基础的模型使用开始学习，然后掌握异步和LCEL的高级特性，最后尝试自定义模型实现。在 LangChain 1.x 中，**异步处理**、**LCEL**和**init_chat_model**是关键技能。
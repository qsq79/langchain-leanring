# LangChain 1.x 迁移指南

本指南帮助您从旧版本的 LangChain 迁移到 LangChain 1.x，了解主要的架构变化和新特性。

## 📋 核心变化概述

### 1. 模块化架构
LangChain 1.x 采用了更清晰的模块化架构：

- **langchain-core**: 核心接口和基础组件
- **langchain**: 保留的向后兼容组件
- **langchain-community**: 社区贡献的组件
- **langchain-openai**: OpenAI 特定的集成
- **langchain-text-splitters**: 文本分割器（独立包）

### 2. LangChain Expression Language (LCEL)
LCEL 是 LangChain 1.x 的核心特性，推荐使用 pipe operator (|) 来构建链：

```python
# 旧方式 (不推荐)
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)

# 新方式 (推荐)
from langchain_core.output_parsers import StrOutputParser
chain = prompt | llm | StrOutputParser()
```

### 3. 异步支持优先
所有组件现在都支持原生异步操作：

```python
# 同步调用
result = chain.invoke({"input": "Hello"})

# 异步调用
result = await chain.ainvoke({"input": "Hello"})

# 异步流式
async for chunk in chain.astream({"input": "Hello"}):
    print(chunk)
```

## 🔄 主要迁移路径

### Models 组件
```python
# 旧版本
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI

# 新版本
from langchain_openai import OpenAI, ChatOpenAI

# 新增特性
# 结构化输出
from langchain_core.output_parsers import JsonOutputParser
```

### Chains 组件
```python
# 旧版本 (已废弃)
from langchain.chains import LLMChain, SequentialChain, RouterChain

# 新版本 (LCEL)
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# 替代 LLMChain
chain = prompt | llm | output_parser

# 替代 SequentialChain
chain = step1 | step2 | step3

# 替代 RouterChain
def route_logic(x):
    if condition:
        return chain_a
    else:
        return chain_b

router_chain = RunnableLambda(route_logic)
```

### Prompts 组件
```python
# 基本保持不变，但导入路径可能变化
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
```

### Indexes 组件
```python
# 文本分割器
# 旧版本
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 新版本
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 检索链
# 旧版本
from langchain.chains import RetrievalQA

# 新版本 (LCEL)
retrieval_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)
```

### Memory 组件
```python
# 基本保持兼容，但推荐在 LCEL 中使用
from langchain.memory import ConversationBufferMemory

# 在 LCEL 中使用
chain = (
    RunnablePassthrough.assign(
        history=RunnableLambda(lambda x: load_memory(x["chat_history"]))
    )
    | prompt
    | llm
)
```

## 📝 代码示例对比

### 基础链构建
```python
# 旧版本
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.llms import OpenAI

prompt = PromptTemplate(template="Answer: {question}")
llm = OpenAI()
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run(question="What is AI?")

# 新版本 (LCEL)
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import OpenAI

prompt = PromptTemplate.from_template("Answer: {question}")
llm = OpenAI()
chain = prompt | llm | StrOutputParser()
result = chain.invoke({"question": "What is AI?"})
```

### 并行处理
```python
# 旧版本 (复杂)
from langchain.chains import TransformChain

def parallel_processing(inputs):
    # 手动实现并行逻辑
    pass

# 新版本 (简单)
from langchain_core.runnables import RunnableParallel

parallel_chain = RunnableParallel({
    "summary": summary_prompt | llm,
    "analysis": analysis_prompt | llm
})
```

### 异步处理
```python
# 旧版本 (有限支持)
# 需要手动管理异步

# 新版本 (原生支持)
async def process_batch(items):
    tasks = [chain.ainvoke(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results
```

## 🛠️ 实际迁移步骤

### 1. 更新依赖
```bash
pip install langchain>=0.1.0
pip install langchain-core>=0.1.0
pip install langchain-openai>=0.1.0
pip install langchain-community>=0.1.0
pip install langchain-text-splitters>=0.1.0
```

### 2. 更新导入语句
```python
# 批量替换
from langchain.llms import OpenAI → from langchain_openai import OpenAI
from langchain.chat_models import ChatOpenAI → from langchain_openai import ChatOpenAI
from langchain.prompts → from langchain_core.prompts
from langchain.text_splitter → from langchain_text_splitters
```

### 3. 重写 Chains
将所有基于类的链替换为 LCEL 表达式。

### 4. 添加异步支持
为性能关键部分添加异步操作。

### 5. 测试和验证
确保所有功能正常工作。

## ⚠️ 兼容性注意事项

### 不再推荐的组件
- `LLMChain` - 使用 LCEL 替代
- `SequentialChain` - 使用 pipe operator 替代
- `RouterChain` - 使用 `RunnableLambda` 替代
- `TransformChain` - 使用自定义可运行对象替代

### 可能需要调整的代码
- 缓存机制
- 回调处理
- 错误处理
- 流式输出

## 📚 推荐的最佳实践

### 1. 使用 LCEL
```python
# ✅ 推荐
chain = prompt | llm | output_parser

# ❌ 不推荐
chain = LLMChain(llm=llm, prompt=prompt)
```

### 2. 异步优先
```python
# ✅ 推荐
async def process_item(item):
    return await chain.ainvoke(item)

# ❌ 避免同步阻塞
def process_item(item):
    return chain.invoke(item)  # 在异步上下文中避免
```

### 3. 类型安全
```python
from typing import Dict, Any

def process_input(input_data: Dict[str, Any]) -> str:
    return chain.invoke(input_data)
```

### 4. 错误处理
```python
from langchain_core.exceptions import LangChainException

try:
    result = await chain.ainvoke(input_data)
except LangChainException as e:
    logger.error(f"Chain execution failed: {e}")
    raise
```

## 🔗 参考资源

- [LangChain 官方迁移指南](https://python.langchain.com/docs/versions/migrating_to_lcel/)
- [LCEL 文档](https://python.langchain.com/docs/concepts/lcel/)
- [LangChain 1.x 发布说明](https://python.langchain.com/docs/versions/)

---

💡 **提示**: 建议逐步迁移，先在新功能中使用 LCEL，然后逐步重构现有代码。
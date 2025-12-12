# LangChain 1.x 核心知识点

本文档总结了 LangChain 1.x 的核心知识点和最佳实践，基于实际代码修正经验编写。

## 📋 核心架构变化

### 1. 模块化架构

LangChain 1.x 采用了全新的模块化架构，将功能分散到专门的包中：

```python
# 核心接口和基础组件
from langchain_core import (
    prompts, messages, runnables, callbacks,
    outputs, exceptions
)

# OpenAI 特定集成
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings

# 社区贡献的组件
from langchain_community import (
    document_loaders, vectorstores, tools, utilities
)

# 文本分割器（独立包）
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
    CharacterTextSplitter
)

# 传统组件的向后兼容
from langchain_classic import (
    memory, chains, agents, tools
)
```

### 2. LangChain Expression Language (LCEL)

LCEL 是 LangChain 1.x 的核心创新，使用 pipe operator (`|`) 构建处理链：

```python
# 基础链构建
chain = prompt | llm | output_parser

# 复杂链组合
retrieval_chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | output_parser
)

# 并行处理
parallel_chain = RunnableParallel({
    "summary": summary_prompt | llm,
    "analysis": analysis_prompt | llm
})
```

## 🏗️ 组件详解

### Models 组件

#### LLM vs Chat Model
```python
# LLM - 文本输入输出
llm = OpenAI(model="gpt-3.5-turbo-instruct")
result = llm.invoke("What is AI?")

# Chat Model - 消息输入输出
chat_model = ChatOpenAI(model="gpt-3.5-turbo")
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is AI?")
]
result = chat_model.invoke(messages)
```

#### 异步支持
所有模型都支持原生异步操作：
```python
# 异步调用
result = await llm.ainvoke("Hello, world!")

# 异步流式
async for chunk in llm.astream("Tell me a story"):
    print(chunk, end="", flush=True)

# 批量异步处理
tasks = [llm.ainvoke(prompt) for prompt in prompts]
results = await asyncio.gather(*tasks)
```

#### 结构化输出
```python
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

class AnalysisResult(BaseModel):
    summary: str = Field(description="回答摘要")
    confidence: float = Field(description="置信度")

parser = JsonOutputParser(pydantic_object=AnalysisResult)
chain = prompt | chat_model | parser
result = chain.invoke({"text": "AI is a technology"})
```

### Prompts 组件

#### 模板类型
```python
# 基础提示模板
prompt = PromptTemplate(
    template="Answer: {question}",
    input_variables=["question"]
)

# 聊天提示模板
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])
)

# Few-shot 提示模板
few_shot_prompt = FewShotPromptTemplate(
    examples=examples,
    prefix="Here are some examples:",
    suffix="Now answer: {input}"
)
```

#### 输出解析器
```python
from langchain_core.output_parsers import (
    StrOutputParser, JsonOutputParser,
    PydanticOutputParser, ListOutputParser
)

parser = StrOutputParser()
chain = prompt | llm | parser
```

### Chains 组件（LCEL 方式）

#### 替代传统 Chain 类
```python
# ❌ 旧方式 (已废弃)
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)

# ✅ 新方式 (LCEL)
chain = prompt | llm | StrOutputParser()
```

#### 复杂处理模式
```python
# 顺序处理
chain = (
    RunnablePassthrough.assign(
        step1=step1_prompt | llm,
        step2=RunnablePassthrough.assign(
            step2=lambda x: step2_prompt.format(text=x["step1"])
        ) | llm
    )
    | RunnablePassthrough.assign(
        final=step3_prompt | llm
    )
)

# 条件处理
def route_logic(inputs):
    if inputs["difficulty"] == "hard":
        return detailed_chain
    else:
        return simple_chain

router = RunnableLambda(route_logic)
chain = router | other_components

# 错误处理和重试
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2))
def robust_llm_call(prompt):
    return llm.invoke(prompt)
```

### Memory 组件

#### 传统内存类型
```python
# 对话缓存内存
from langchain_classic.memory import ConversationBufferMemory

memory = ConversationBufferMemory(
    chat_history=[
        ("human", "Hello!"),
        ("ai", "Hi there!"),
        ("human", "What's your name?"),
        ("ai", "I'm a helpful assistant.")
    ]
)

# 窗口内存
from langchain_classic.memory import ConversationBufferWindowMemory
window_memory = ConversationBufferWindowMemory(k=2)

# 摘要内存
from langchain_classic.memory import ConversationSummaryMemory
summary_memory = ConversationSummaryMemory(llm=llm)

# 知识图谱内存
from langchain_community.memory.kg import ConversationKGMemory
```

#### 新的 ChatMessageHistory
```python
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_community.chat_message_histories import (
    ChatMessageHistory,
    FileChatMessageHistory
)

# 自定义历史管理
class InMemoryChatMessageHistory(BaseChatMessageHistory):
    def __init__(self):
        self.messages = []

    def add_user_message(self, message: str):
        self.messages.append(("user", message))

    def add_ai_message(self, message: str):
        self.messages.append(("ai", message))

    def clear(self):
        self.messages = []
```

### Indexes 组件

#### 文档加载器
```python
from langchain_community.document_loaders import (
    TextLoader, CSVLoader, JSONLoader, WebBaseLoader
)

# 文本文件
loader = TextLoader("document.txt")
documents = loader.load()

# CSV文件
csv_loader = CSVLoader("data.csv")
csv_docs = csv_loader.load()

# 网页
web_loader = WebBaseLoader("https://example.com")
web_docs = web_loader.load()
```

#### 文本分割器
```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 按字符分割
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len,
    separators=["\n\n", "\n", " ", ""]
)

chunks = text_splitter.split_documents(documents)
```

#### 向量存储
```python
from langchain_community.vectorstores import FAISS, Chroma
from langchain_openai import OpenAIEmbeddings

# FAISS 存储
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(documents, embeddings)

# 相似度搜索
results = vectorstore.similarity_search("Python programming", k=3)

# 创建检索器
retriever = vectorstore.as_retriever()
retrieved_docs = retriever.invoke("machine learning")
```

### Agents 组件

#### 智能体创建（推荐方式）
```python
from langchain_classic.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.tools import Tool

# 创建工具
tools = [
    Tool(
        name="calculator",
        description="Useful for math calculations",
        func=lambda x: str(eval(x))
    )
]

# 创建智能体
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("human", "{input}"),
    ("assistant", "{agent_scratchpad}"),
    ("tool_call", "{observation}"),
    ("final", "{final_answer}")
])

agent = create_openai_tools_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# 执行智能体
result = agent_executor.invoke({"input": "Calculate 2 + 2"})
```

### Tools 组件

#### 内置工具
```python
from langchain_community.tools import (
    WikipediaQueryRun, DuckDuckGoSearchRun,
    ShellTool, PythonREPLTool
)

# Wikipedia 搜索
wiki_tool = WikipediaQueryRun()

# DuckDuckGo 搜索
search_tool = DuckDuckGoSearchRun()

# Shell 工具（谨慎使用）
shell_tool = ShellTool()

# Python REPL 工具
python_tool = PythonREPLTool()
```

#### 自定义工具
```python
from langchain_classic.tools import tool
from pydantic import BaseModel, Field

@tool
def calculator(expression: str) -> str:
    """Performs basic math calculations."""
    try:
        return str(eval(expression))
    except:
        return "Calculation error"

# 使用 Pydantic 的工具
class WeatherInput(BaseModel):
    location: str = Field(description="City name")
    unit: str = Field(default="celsius", description="Temperature unit")

@tool
def get_weather(input: WeatherInput) -> str:
    """Get current weather information."""
    # 实际的天气API调用
    return f"Weather in {input.location}: 25°C {input.unit}"
```

### Callbacks 组件

#### 回调处理器
```python
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.outputs import LLMResult

class CustomCallbackHandler(BaseCallbackHandler):
    def on_llm_start(self, serialized: Dict[str, Any], **kwargs):
        print(f"LLM 开始: {serialized}")

    def on_llm_end(self, response: LLMResult, **kwargs):
        print(f"LLM 结束: {response.generations[0].text}")

    def on_chain_start(self, serialized: Dict[str, Any], **kwargs):
        print(f"Chain 开始: {serialized}")

    def on_chain_end(self, outputs: Dict[str, Any], **kwargs):
        print(f"Chain 结束: {outputs}")

# 使用回调
handler = CustomCallbackHandler()
chain = prompt | llm | output_parser
result = chain.invoke(
    {"question": "What is AI?"},
    callbacks=[handler]
)
```

#### 异步回调
```python
from langchain_core.callbacks import AsyncCallbackHandler

class AsyncCallbackHandler(AsyncCallbackHandler):
    async def on_llm_start(self, serialized, **kwargs):
        print(f"异步 LLM 开始")

    async def on_llm_end(self, response, **kwargs):
        print(f"异步 LLM 结束")

# 流式回调
class StreamingCallbackHandler(BaseCallbackHandler):
    def on_llm_new_token(self, token: str, **kwargs):
        print(token, end="", flush=True)
```

## 🔧 最佳实践

### 1. LCEL 链式组合
```python
# ✅ 推荐：使用 LCEL
chain = (
    {"context": retriever}
    | RunnablePassthrough.assign(
        answer=prompt | llm | StrOutputParser()
    )
)

# ❌ 避免：传统的 Chain 类
# chain = LLMChain(llm=llm, prompt=prompt)
```

### 2. 异步优先
```python
# ✅ 推荐：异步操作
async def process_batch():
    tasks = [chain.ainvoke(item) for item in items]
    results = await asyncio.gather(*tasks)
    return results

# ❌ 避免：同步阻塞（在异步上下文中）
def process_batch():
    results = []
    for item in items:
        results.append(chain.invoke(item))  # 阻塞操作
    return results
```

### 3. 类型安全
```python
from typing import Dict, Any, List

def process_input(input_data: Dict[str, Any]) -> str:
    """类型安全的处理函数"""
    return chain.invoke(input_data)
```

### 4. 错误处理
```python
from langchain_core.exceptions import LangChainException
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
@retry(wait=wait_exponential(multiplier=2))
def robust_chain_call(input_data: Dict[str, Any]) -> str:
    try:
        return chain.invoke(input_data)
    except LangChainException as e:
        logger.error(f"Chain 执行失败: {e}")
        raise
```

### 5. 资源管理
```python
# 缓存提高性能
from langchain_core.caches import InMemoryCache
from langchain_core.globals import set_llm_cache

set_llm_cache(InMemoryCache())

# 流式输出减少内存使用
for chunk in chain.stream(input_data):
    process_chunk(chunk)
```

## 📚 学习路径建议

### 初级阶段
1. **掌握 LCEL 基础**：学习 pipe operator 和基本组件
2. **异步编程**：理解 async/await 在 LangChain 中的应用
3. **错误处理**：学习如何优雅地处理异常

### 中级阶段
1. **复杂数据流**：使用 RunnablePassthrough、RunnableParallel
2. **自定义组件**：创建自己的工具、回调处理器
3. **性能优化**：缓存、批量处理、异步调用

### 高级阶段
1. **自定义 LLM**：实现自己的模型接口
2. **高级 Agent 架构**：复杂的智能体系统设计
3. **系统集成**：与外部服务的深度集成

## 🔗 参考资源

- [LangChain 官方文档](https://python.langchain.com/)
- [LCEL 指南](https://python.langchain.com/docs/concepts/lcel/)
- [LangChain 1.x 迁移指南](./LANGCHAIN_1X_MIGRATION_GUIDE.md)
- [示例代码仓库](https://github.com/langchain-ai/langchain/tree/master/examples)

---

💡 **核心要点**：LangChain 1.x 的核心是 **LCEL**（LangChain Expression Language）和**模块化架构**。掌握这两个概念，就能构建出强大、可维护的 LLM 应用。
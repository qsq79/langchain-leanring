# LangChain 1.x 核心组件学习项目

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://python.org)
[![LangChain 1.x](https://img.shields.io/badge/langchain-1.x-orange.svg)](https://python.langchain.com/)

一个全面的 LangChain 1.x 学习项目，包含所有核心组件的详细示例和最佳实践。

## 📚 项目概述

本项目提供了 LangChain 1.x 框架的完整学习路径，从基础概念到高级应用，涵盖了所有主要组件的使用方法。

### 🎯 学习目标
- 掌握 LangChain 1.x 的核心组件
- 理解 LangChain Expression Language (LCEL)
- 学会构建基于大语言模型的实际应用
- 了解异步处理和性能优化技巧

## 🏗️ 项目结构

```
langchain1.x/
├── 01-models/          # Models 组件 (LLM, Chat Models, Embeddings)
├── 02-prompts/         # Prompts 组件 (Templates, Selectors, Parsers)
├── 03-chains/          # Chains 组件 (LCEL, Sequential, Parallel)
├── 04-indexes/         # Indexes 组件 (Loaders, Splitters, VectorStores)
├── 05-memory/          # Memory 组件 (Buffer, Conversation, Summary)
├── 06-agents/          # Agents 组件 (Tools, Executers, ReAct)
├── 07-tools/           # Tools 组件 (Search, APIs, Custom Tools)
├── 08-callbacks/       # Callbacks 组件 (Handlers, Streaming, Monitoring)
├── requirements.txt    # 依赖列表
└── README.md          # 项目说明
```

## 🚀 LangChain 1.x 新特性

### 1. LangChain Expression Language (LCEL)
使用 pipe operator (`|`) 构建强大的链式组件：

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
llm = ChatOpenAI()
output_parser = StrOutputParser()

chain = prompt | llm | output_parser
result = chain.invoke({"topic": "programming"})
```

### 2. 原生异步支持
所有组件都支持异步操作，提高性能：

```python
import asyncio

async def process_multiple():
    tasks = [chain.ainvoke({"topic": topic}) for topic in topics]
    results = await asyncio.gather(*tasks)
    return results
```

### 3. 流式输出增强
更好的流式处理能力：

```python
for chunk in chain.stream({"topic": "AI"}):
    print(chunk, end="", flush=True)

# 异步流式
async for chunk in chain.astream({"topic": "AI"}):
    print(chunk, end="", flush=True)
```

### 4. 改进的类型安全
更好的类型提示和验证：

```python
from typing import Dict, Any
from langchain_core.runnables import Runnable

def create_chain() -> Runnable[Dict[str, Any], str]:
    return prompt | llm | output_parser
```

## 📖 学习路径

### 第一阶段：基础组件
1. **[Models](01-models/)** - 学习 LLM、Chat Models 和 Embeddings
2. **[Prompts](02-prompts/)** - 掌握提示模板和输出解析器
3. **[Chains](03-chains/)** - 理解 LCEL 和链式组合

### 第二阶段：数据与检索
4. **[Indexes](04-indexes/)** - 学习文档处理和向量存储
5. **[Memory](05-memory/)** - 掌握对话记忆机制

### 第三阶段：智能应用
6. **[Agents](06-agents/)** - 构建智能代理系统
7. **[Tools](07-tools/)** - 集成外部工具和 API
8. **[Callbacks](08-callbacks/)** - 实现监控和回调机制

## 🛠️ 环境配置

### 1. 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 或者安装特定模块的依赖
pip install -r 01-models/requirements.txt
```

### 2. 配置 API 密钥

```bash
# 设置 OpenAI API 密钥
export OPENAI_API_KEY="your-api-key"

# 或者创建 .env 文件
echo "OPENAI_API_KEY=your-api-key" > .env
```

### 3. 运行示例

```bash
# 运行基础示例
python 01-models/basic_example.py

# 运行高级示例
python 01-models/advanced_example.py
```

## 📋 核心概念

### Models 组件
- **LLMs**: 文本生成模型
- **Chat Models**: 对话式模型，支持多轮交互
- **Embeddings**: 文本向量化，用于语义搜索

### Prompts 组件
- **Prompt Templates**: 可重用的提示模板
- **Example Selectors**: 动态示例选择
- **Output Parsers**: 结构化输出解析

### Chains 组件
- **LCEL**: LangChain Expression Language
- **Runnable**: 可组合的组件接口
- **Parallel**: 并行处理

### Indexes 组件
- **Document Loaders**: 文档加载器
- **Text Splitters**: 文本分割器
- **Vector Stores**: 向量数据库

## 🏆 最佳实践

### 1. 使用 LCEL 构建链
```python
# ✅ 推荐
chain = prompt | llm | output_parser

# ❌ 不推荐
from langchain.chains import LLMChain
chain = LLMChain(llm=llm, prompt=prompt)
```

### 2. 异步处理
```python
# ✅ 推荐
async def process_batch():
    tasks = [chain.ainvoke(item) for item in items]
    return await asyncio.gather(*tasks)
```

### 3. 错误处理
```python
from langchain_core.exceptions import LangChainException

try:
    result = await chain.ainvoke(input_data)
except LangChainException as e:
    logger.error(f"Chain execution failed: {e}")
```

### 4. 流式处理
```python
# 实时输出
for chunk in chain.stream(input_data):
    print(chunk, end="", flush=True)
```

## 🔧 开发工具

### 测试
```bash
# 运行测试
pytest

# 运行异步测试
pytest --asyncio-mode=auto
```

### 代码检查
```bash
# 语法检查
python -m py_compile your_file.py

# 类型检查
mypy your_file.py
```

## 📊 性能对比

| 特性 | LangChain 0.x | LangChain 1.x |
|------|---------------|---------------|
| 链式组合 | 基于类 | LCEL (pipe operator) |
| 异步支持 | 有限 | 原生支持 |
| 类型安全 | 基础 | 完善 |
| 性能 | 中等 | 优化 |
| 可维护性 | 中等 | 优秀 |
| 学习曲线 | 陡峭 | 平缓 |

## 🔗 相关资源

### 官方文档
- [LangChain 官方文档](https://python.langchain.com/)
- [LCEL 指南](https://python.langchain.com/docs/concepts/lcel/)
- [迁移指南](./LANGCHAIN_1X_MIGRATION_GUIDE.md)

### 社区资源
- [LangChain Discord](https://discord.gg/langchain)
- [GitHub Discussions](https://github.com/langchain-ai/langchain/discussions)
- [示例项目](https://github.com/langchain-ai/langchain/tree/master/examples)

### 学习资料
- [LangChain Cookbooks](https://python.langchain.com/docs/integrations/)
- [Prompt Engineering Guide](https://www.promptingguide.ai/)
- [LLM 应用开发指南](https://github.com/e2b-dev/awesome-llm-apps)

## 🤝 贡献指南

欢迎贡献代码和建议！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [LangChain 团队](https://github.com/langchain-ai) 提供的出色框架
- 所有贡献者的努力和支持
- OpenAI 提供的强大模型

---

💡 **开始学习**: 从 [01-models](01-models/) 开始你的 LangChain 1.x 之旅！

如有问题，请查看 [FAQ](./FAQ.md) 或在 [Issues](https://github.com/your-repo/issues) 中提问。
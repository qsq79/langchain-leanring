# LangChain 1.x 核心组件学习示例

本项目提供了LangChain 1.x版本核心组件的详细学习示例，每个组件都有独立的文件夹和完整的学习文档。

## 📁 项目结构

```
langchain-learning/
├── 01-models/              # 模型组件（LLM、Chat Models、Embeddings）
├── 02-prompts/              # 提示组件（Prompt Templates、Example Selectors）
├── 03-chains/               # 链组件（LLMChain、SequentialChain等）
├── 04-indexes/              # 索引组件（Document Loaders、Text Splitters、VectorStores）
├── 05-memory/               # 记忆组件（ConversationBufferMemory等）
├── 06-agents/               # 代理组件（Agent Types、Tools、Agent Executor）
├── 07-tools/                # 工具组件（Built-in Tools、Custom Tools）
├── 08-callbacks/            # 回调组件（Streaming、Logging、Custom Callbacks）
└── README.md               # 项目说明文档
```

## 🎯 学习目标

通过本项目，您将深入理解LangChain 1.x的核心组件：
- 掌握每个组件的基本概念和使用方法
- 理解组件之间的协作关系
- 了解常见的设计模式和最佳实践
- 准备相关的技术面试

## 🚀 快速开始

每个组件文件夹都包含：
- `README.md` - 组件详细说明、知识点、面试题
- `basic_example.py` - 基础使用示例
- `advanced_example.py` - 高级应用示例
- `requirements.txt` - 依赖包列表

建议按照文件夹编号顺序进行学习，从基础的Models组件开始。

## 📚 学习路径

1. **Models** - 理解语言模型的基础使用
2. **Prompts** - 掌握提示工程技巧
3. **Chains** - 学习如何构建复杂的工作流
4. **Indexes** - 了解文档处理和向量存储
5. **Memory** - 掌握对话状态管理
6. **Agents** - 理解智能代理的工作原理
7. **Tools** - 学习如何扩展LangChain功能
8. **Callbacks** - 掌握事件处理和监控

## 🛠️ 环境要求

- Python 3.8+
- LangChain 1.x
- OpenAI API密钥（或其他LLM提供商）

## 📖 参考资料

- [LangChain官方文档](https://python.langchain.com/)
- [LangChain GitHub仓库](https://github.com/langchain-ai/langchain)
- [OpenAI API文档](https://platform.openai.com/docs)

---

💡 **提示**：每个组件的README都包含该组件的核心知识点、常见面试题和设计模式分析，建议仔细阅读。

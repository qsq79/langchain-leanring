#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Indexes 组件基础示例 (LangChain 1.x 版本)
演示Document Loaders、Text Splitters、VectorStores的基础使用方法

在 LangChain 1.x 中：
- text_splitter 已移至 langchain_text_splitters 包
- chains 需要使用 LCEL 方式替代传统的 RetrievalQA
- vectorstores 的导入路径可能有变化
"""

import os
import sys
import tempfile
from typing import List, Dict, Any
import asyncio

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

# LangChain 1.x 兼容的导入
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.document_loaders import TextLoader, CSVLoader, JSONLoader, WebBaseLoader
from langchain_community.vectorstores import FAISS, Chroma
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

# 导入 text splitters (LangChain 1.x 正确路径)
from langchain_text_splitters import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter
)
TEXT_SPLITTERS_AVAILABLE = True

def create_sample_documents():
    """创建示例文档"""
    # 创建临时文本文件
    sample_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
    它致力于创造能够执行通常需要人类智能的任务的机器。

    机器学习是人工智能的一个重要子领域。它使计算机能够在没有明确编程的情况下学习和改进。
    监督学习、无监督学习和强化学习是机器学习的三种主要类型。

    深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的学习过程。
    卷积神经网络（CNN）在图像识别中表现出色，
    而循环神经网络（RNN）则更适合处理序列数据。

    自然语言处理（NLP）是人工智能的另一个重要分支。
    它使计算机能够理解、解释和生成人类语言。
    现代的NLP系统通常基于Transformer架构。
    """

    return sample_text

def document_loader_example():
    """文档加载器示例"""
    print("=== 文档加载器示例 ===")

    # 创建临时文件
    sample_text = create_sample_documents()

    # 1. TextLoader 示例
    print("1. TextLoader 示例:")
    try:
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
            tmp_file.write(sample_text)
            tmp_file_path = tmp_file.name

        loader = TextLoader(tmp_file_path)
        documents = loader.load()

        print(f"加载了 {len(documents)} 个文档")
        print(f"第一个文档长度: {len(documents[0].page_content)} 字符")
        print(f"文档来源: {documents[0].metadata.get('source', '未知')}")
        print()

        # 清理临时文件
        os.unlink(tmp_file_path)
    except Exception as e:
        print(f"TextLoader 示例失败: {e}")

    # 2. 手动创建 Document 对象
    print("2. 手动创建 Document 对象:")
    try:
        # 将文本分割成多个文档
        paragraphs = [p.strip() for p in sample_text.split('\n\n') if p.strip()]
        documents = []

        for i, paragraph in enumerate(paragraphs):
            doc = Document(
                page_content=paragraph,
                metadata={"source": "手动创建", "paragraph_id": i + 1}
            )
            documents.append(doc)

        print(f"创建了 {len(documents)} 个文档")
        for i, doc in enumerate(documents[:3]):  # 只显示前3个
            print(f"文档 {i+1}: {doc.page_content[:100]}...")
        print()
    except Exception as e:
        print(f"手动创建文档示例失败: {e}")

def text_splitter_example():
    """文本分割器示例"""
    print("=== 文本分割器示例 ===")

    sample_text = create_sample_documents()
    document = Document(page_content=sample_text, metadata={"source": "示例"})

    # 1. CharacterTextSplitter
    print("1. CharacterTextSplitter:")
    try:
        char_splitter = CharacterTextSplitter(
            separator="\n",
            chunk_size=200,
            chunk_overlap=20,
            length_function=len
        )
        char_chunks = char_splitter.split_documents([document])
        print(f"分割为 {len(char_chunks)} 个块")
        for i, chunk in enumerate(char_chunks[:2]):
            print(f"块 {i+1}: {chunk.page_content[:100]}...")
        print()
    except Exception as e:
        print(f"CharacterTextSplitter 失败: {e}")

    # 2. RecursiveCharacterTextSplitter (推荐)
    print("2. RecursiveCharacterTextSplitter:")
    try:
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=300,
            chunk_overlap=50,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        recursive_chunks = recursive_splitter.split_documents([document])
        print(f"分割为 {len(recursive_chunks)} 个块")
        for i, chunk in enumerate(recursive_chunks[:3]):
            print(f"块 {i+1}: {chunk.page_content[:100]}...")
        print()
    except Exception as e:
        print(f"RecursiveCharacterTextSplitter 失败: {e}")

def vector_store_example():
    """向量存储示例"""
    print("=== 向量存储示例 ===")

    try:
        # 创建文档
        documents = [
            Document(
                page_content="Python是一种高级编程语言，具有简洁易读的语法。",
                metadata={"source": "编程文档", "category": "编程语言"}
            ),
            Document(
                page_content="机器学习是人工智能的一个子领域，专注于算法和统计模型。",
                metadata={"source": "AI文档", "category": "人工智能"}
            ),
            Document(
                page_content="深度学习使用多层神经网络来处理复杂的数据模式。",
                metadata={"source": "AI文档", "category": "人工智能"}
            )
        ]

        # 创建嵌入
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

        # 1. FAISS 向量存储
        print("1. FAISS 向量存储:")
        try:
            faiss_db = FAISS.from_documents(documents, embeddings)

            # 搜索相似文档
            query = "Python编程的特点"
            results = faiss_db.similarity_search(query, k=2)

            print(f"查询: {query}")
            print(f"找到 {len(results)} 个相似文档:")
            for i, doc in enumerate(results):
                print(f"  结果 {i+1}: {doc.page_content}")
                print(f"  元数据: {doc.metadata}")
            print()
        except Exception as e:
            print(f"FAISS 示例失败: {e}")

        # 2. Chroma 向量存储
        print("2. Chroma 向量存储:")
        try:
            import chromadb
            chroma_db = Chroma.from_documents(documents, embeddings)

            # 搜索相似文档
            query = "深度学习的应用"
            results = chroma_db.similarity_search(query, k=2)

            print(f"查询: {query}")
            print(f"找到 {len(results)} 个相似文档:")
            for i, doc in enumerate(results):
                print(f"  结果 {i+1}: {doc.page_content}")
                print(f"  元数据: {doc.metadata}")
            print()
        except ImportError:
            print("ChromaDB 不可用，跳过示例")
        except Exception as e:
            print(f"Chroma 示例失败: {e}")

    except Exception as e:
        print(f"向量存储示例失败: {e}")

def retrieval_chain_lcel_example():
    """检索链 LCEL 示例"""
    print("=== 检索链 LCEL 示例 ===")

    try:
        # 创建文档集合
        documents = [
            Document(
                page_content="LangChain是一个用于构建基于大语言模型应用程序的框架。",
                metadata={"source": "LangChain文档", "category": "框架"}
            ),
            Document(
                page_content="LCEL（LangChain Expression Language）是构建链的新方式。",
                metadata={"source": "LangChain文档", "category": "框架"}
            ),
            Document(
                page_content="向量搜索通过将文档转换为向量来查找相似内容。",
                metadata={"source": "检索文档", "category": "搜索"}
            ),
            Document(
                page_content="嵌入向量捕捉文本的语义信息。",
                metadata={"source": "检索文档", "category": "搜索"}
            )
        ]

        # 创建向量存储
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        vectorstore = FAISS.from_documents(documents, embeddings)

        # 创建检索器
        retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

        # 创建 LLM
        llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.3)

        # 创建提示模板
        prompt = ChatPromptTemplate.from_template("""
        基于以下上下文回答问题：

        上下文：
        {context}

        问题：{question}

        回答：
        """)

        # 使用 LCEL 创建检索链
        retrieval_chain = (
            {
                "context": retriever | (lambda docs: "\n".join([doc.page_content for doc in docs])),
                "question": RunnablePassthrough()
            }
            | prompt
            | llm
            | StrOutputParser()
        )

        # 测试查询
        queries = [
            "什么是LCEL？",
            "向量搜索的原理是什么？",
            "如何使用LangChain？"
        ]

        for query in queries:
            print(f"问题: {query}")
            result = retrieval_chain.invoke(query)
            print(f"回答: {result}")
            print("-" * 50)

    except Exception as e:
        print(f"检索链示例失败: {e}")

async def async_vector_search_example():
    """异步向量搜索示例"""
    print("=== 异步向量搜索示例 ===")

    try:
        # 创建文档集合
        documents = [
            Document(
                page_content="异步编程可以提高应用程序的性能和响应能力。",
                metadata={"source": "编程文档", "category": "并发"}
            ),
            Document(
                page_content="Python的asyncio库提供了异步编程的基础设施。",
                metadata={"source": "编程文档", "category": "并发"}
            ),
            Document(
                page_content="LangChain支持异步操作以提高性能。",
                metadata={"source": "LangChain文档", "category": "框架"}
            )
        ]

        # 创建嵌入
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")

        # 异步生成嵌入向量
        print("异步生成嵌入向量...")
        texts = [doc.page_content for doc in documents]
        embedding_tasks = [embeddings.aembed_query(text) for text in texts]
        vectors = await asyncio.gather(*embedding_tasks)

        print(f"生成了 {len(vectors)} 个嵌入向量")
        for i, vector in enumerate(vectors[:2]):
            print(f"向量 {i+1} 维度: {len(vector)}")

        # 创建向量存储
        vectorstore = FAISS.from_documents(documents, embeddings)

        # 异步搜索
        print("\n执行异步搜索:")
        queries = [
            "asyncio的作用",
            "异步编程的优势",
            "LangChain的异步支持"
        ]

        search_tasks = []
        for query in queries:
            task = asyncio.create_task(async_search_wrapper(vectorstore, query))
            search_tasks.append((query, task))

        for query, task in search_tasks:
            results = await task
            print(f"\n查询: {query}")
            for i, doc in enumerate(results):
                print(f"  结果 {i+1}: {doc.page_content[:80]}...")

    except Exception as e:
        print(f"异步向量搜索示例失败: {e}")

async def async_search_wrapper(vectorstore, query):
    """异步搜索包装器"""
    # FAISS 的搜索是同步的，但我们包装在异步函数中
    # 在实际应用中，可以使用支持异步的向量存储
    return vectorstore.similarity_search(query, k=2)

def document_metadata_filtering_example():
    """文档元数据过滤示例"""
    print("=== 文档元数据过滤示例 ===")

    try:
        # 创建带有不同元数据的文档
        documents = [
            Document(
                page_content="React是一个用于构建用户界面的JavaScript库。",
                metadata={"source": "前端文档", "category": "框架", "difficulty": "中等"}
            ),
            Document(
                page_content="Vue是一个渐进式JavaScript框架。",
                metadata={"source": "前端文档", "category": "框架", "difficulty": "简单"}
            ),
            Document(
                page_content="机器学习算法可以从数据中学习模式。",
                metadata={"source": "AI文档", "category": "人工智能", "difficulty": "困难"}
            ),
            Document(
                page_content="深度学习使用神经网络处理复杂任务。",
                metadata={"source": "AI文档", "category": "人工智能", "difficulty": "困难"}
            )
        ]

        # 创建向量存储
        embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
        vectorstore = FAISS.from_documents(documents, embeddings)

        # 使用 self_query 进行元数据过滤
        print("搜索 '难度为简单' 的文档:")
        simple_docs = [doc for doc in documents if doc.metadata.get("difficulty") == "简单"]
        for doc in simple_docs:
            print(f"  {doc.page_content} (难度: {doc.metadata.get('difficulty')})")

        print("\n搜索 '类别为框架' 的文档:")
        framework_docs = [doc for doc in documents if doc.metadata.get("category") == "框架"]
        for doc in framework_docs:
            print(f"  {doc.page_content} (类别: {doc.metadata.get('category')})")

        # 使用向量搜索结合元数据过滤
        print("\n向量搜索 + 元数据过滤:")
        query = "编程框架"
        results = vectorstore.similarity_search(query, k=4)

        filtered_results = [
            doc for doc in results
            if doc.metadata.get("category") == "框架"
        ]

        print(f"搜索 '{query}' 且类别为 '框架' 的结果:")
        for doc in filtered_results:
            print(f"  {doc.page_content}")
            print(f"  元数据: {doc.metadata}")

    except Exception as e:
        print(f"元数据过滤示例失败: {e}")

async def main():
    """主函数，运行所有示例"""
    print("LangChain Indexes 组件基础示例 (LangChain 1.x 版本)")
    print("=" * 60)
    print("注意：此版本兼容 LangChain 1.x 的新导入路径和LCEL方式")
    print("=" * 60)
    print()

    try:
        # 文档加载示例
        document_loader_example()

        # 文本分割示例
        text_splitter_example()

        # 向量存储示例
        vector_store_example()

        # 检索链 LCEL 示例
        retrieval_chain_lcel_example()

        # 异步向量搜索示例
        await async_vector_search_example()

        # 元数据过滤示例
        document_metadata_filtering_example()

    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    asyncio.run(main())
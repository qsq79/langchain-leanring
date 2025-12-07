#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Indexes 组件基础示例
演示Document Loaders、Text Splitters、VectorStores的基础使用方法
"""

import os
import sys
import tempfile
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import TextLoader, CSVLoader, JSONLoader, WebBaseLoader
from langchain_community.vectorstores import FAISS, Chroma
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
    TokenTextSplitter,
    MarkdownTextSplitter
)
from langchain_core.documents import Document
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI

# 添加utils目录到系统路径，以便导入配置加载器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

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
    
    # 创建临时文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
        f.write(sample_text)
        return f.name

def text_loader_example():
    """TextLoader示例"""
    print("=== TextLoader示例 ===")
    
    # 创建示例文档
    file_path = create_sample_documents()
    
    try:
        # 使用TextLoader加载文档
        loader = TextLoader(file_path, encoding='utf-8')
        documents = loader.load()
        
        print(f"加载的文档数量: {len(documents)}")
        print(f"文档内容预览:")
        print(documents[0].page_content[:200] + "...")
        print(f"元数据: {documents[0].metadata}")
        print()
        
    finally:
        # 清理临时文件
        os.unlink(file_path)

def csv_loader_example():
    """CSVLoader示例"""
    print("=== CSVLoader示例 ===")
    
    # 创建示例CSV数据
    csv_content = """name,age,department
张三,25,技术部
李四,30,市场部
王五,28,技术部
赵六,35,销售部
"""
    
    # 创建临时CSV文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(csv_content)
        csv_file_path = f.name
    
    try:
        # 使用CSVLoader加载文档
        loader = CSVLoader(file_path=csv_file_path, encoding='utf-8')
        documents = loader.load()
        
        print(f"加载的文档数量: {len(documents)}")
        print("前两个文档内容:")
        for i, doc in enumerate(documents[:2]):
            print(f"文档 {i+1}:")
            print(f"内容: {doc.page_content}")
            print(f"元数据: {doc.metadata}")
            print()
        
    finally:
        # 清理临时文件
        os.unlink(csv_file_path)

def json_loader_example():
    """JSONLoader示例"""
    print("=== JSONLoader示例 ===")
    
    # 创建示例JSON数据
    json_content = """{
    "employees": [
        {"name": "张三", "age": 25, "skills": ["Python", "Java", "SQL"]},
        {"name": "李四", "age": 30, "skills": ["JavaScript", "React", "Node.js"]},
        {"name": "王五", "age": 28, "skills": ["Python", "Django", "PostgreSQL"]}
    ]
}"""
    
    # 创建临时JSON文件
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
        f.write(json_content)
        json_file_path = f.name
    
    try:
        # 使用JSONLoader加载文档
        loader = JSONLoader(
            file_path=json_file_path,
            jq_schema='.employees[]',
            text_content=False,
            encoding='utf-8'
        )
        documents = loader.load()
        
        print(f"加载的文档数量: {len(documents)}")
        print("前两个文档内容:")
        for i, doc in enumerate(documents[:2]):
            print(f"文档 {i+1}:")
            print(f"内容: {doc.page_content}")
            print(f"元数据: {doc.metadata}")
            print()
        
    finally:
        # 清理临时文件
        os.unlink(json_file_path)

def web_loader_example():
    """WebBaseLoader示例"""
    print("=== WebBaseLoader示例 ===")
    
    try:
        # 使用WebBaseLoader加载网页内容
        loader = WebBaseLoader(
            ["https://www.python.org/about/"]
        )
        documents = loader.load()
        
        print(f"加载的文档数量: {len(documents)}")
        print(f"文档内容预览:")
        print(documents[0].page_content[:300] + "...")
        print(f"元数据: {documents[0].metadata}")
        print()
        
    except Exception as e:
        print(f"网页加载失败: {e}")
        print("这可能是由于网络连接问题或网站不可访问")
        print()

def character_text_splitter_example():
    """CharacterTextSplitter示例"""
    print("=== CharacterTextSplitter示例 ===")
    
    # 创建示例文本
    sample_text = """
    人工智能是计算机科学的一个分支。它致力于创造能够执行通常需要人类智能的任务的机器。
    机器学习是人工智能的一个重要子领域。它使计算机能够在没有明确编程的情况下学习和改进。
    深度学习是机器学习的一个子集。它使用多层神经网络来模拟人脑的学习过程。
    自然语言处理是人工智能的另一个重要分支。它使计算机能够理解、解释和生成人类语言。
    """
    
    # 创建CharacterTextSplitter
    splitter = CharacterTextSplitter(
        separator="。",
        chunk_size=100,
        chunk_overlap=20,
        length_function=len
    )
    
    # 分割文本
    chunks = splitter.split_text(sample_text)
    
    print(f"分割后的块数量: {len(chunks)}")
    print("分割结果:")
    for i, chunk in enumerate(chunks):
        print(f"块 {i+1}: {chunk.strip()}")
        print(f"长度: {len(chunk)}")
        print()
    
    # 分割文档
    document = Document(page_content=sample_text, metadata={"source": "example"})
    documents = splitter.split_documents([document])
    
    print(f"分割后的文档数量: {len(documents)}")
    print("第一个分割文档:")
    print(f"内容: {documents[0].page_content}")
    print(f"元数据: {documents[0].metadata}")
    print()

def recursive_character_text_splitter_example():
    """RecursiveCharacterTextSplitter示例"""
    print("=== RecursiveCharacterTextSplitter示例 ===")
    
    # 创建示例Markdown文本
    markdown_text = """
# 人工智能概述

## 定义
人工智能（AI）是计算机科学的一个分支。

## 主要分支

### 机器学习
机器学习是AI的核心技术之一。

#### 监督学习
监督学习使用标记数据进行训练。

#### 无监督学习
无监督学习从无标记数据中发现模式。

### 深度学习
深度学习使用多层神经网络。

## 应用领域
AI在医疗、金融、交通等领域有广泛应用。
"""
    
    # 创建RecursiveCharacterTextSplitter
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=100,
        chunk_overlap=20,
        separators=["\n\n", "\n", " ", ""]
    )
    
    # 分割文本
    chunks = splitter.split_text(markdown_text)
    
    print(f"分割后的块数量: {len(chunks)}")
    print("分割结果:")
    for i, chunk in enumerate(chunks):
        print(f"块 {i+1}:")
        print(chunk)
        print(f"长度: {len(chunk)}")
        print("-" * 50)

def token_text_splitter_example():
    """TokenTextSplitter示例"""
    print("=== TokenTextSplitter示例 ===")
    
    # 创建示例文本
    sample_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支。
    它致力于创造能够执行通常需要人类智能的任务的机器。
    机器学习是人工智能的一个重要子领域。
    深度学习是机器学习的一个子集。
    """
    
    try:
        # 创建TokenTextSplitter
        splitter = TokenTextSplitter(
            chunk_size=50,
            chunk_overlap=10
        )
        
        # 分割文本
        chunks = splitter.split_text(sample_text)
        
        print(f"分割后的块数量: {len(chunks)}")
        print("分割结果:")
        for i, chunk in enumerate(chunks):
            print(f"块 {i+1}: {chunk}")
            print("-" * 30)
        
    except Exception as e:
        print(f"TokenTextSplitter示例失败: {e}")
        print("这可能是因为需要安装tiktoken库")

def faiss_vector_store_example():
    """FAISS向量存储示例"""
    print("=== FAISS向量存储示例 ===")
    
    # 创建示例文档
    texts = [
        "人工智能是计算机科学的一个分支",
        "机器学习使计算机能够从数据中学习",
        "深度学习使用多层神经网络",
        "自然语言处理帮助计算机理解人类语言",
        "计算机视觉让机器能够识别图像"
    ]
    
    metadatas = [
        {"source": "AI_intro"},
        {"source": "ML_intro"},
        {"source": "DL_intro"},
        {"source": "NLP_intro"},
        {"source": "CV_intro"}
    ]
    
    try:
        # 创建嵌入模型
        embeddings = OpenAIEmbeddings()
        
        # 创建FAISS向量存储
        vector_store = FAISS.from_texts(texts, embeddings, metadatas)
        
        # 相似度搜索
        query = "什么是深度学习？"
        results = vector_store.similarity_search(query, k=3)
        
        print(f"查询: {query}")
        print("搜索结果:")
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content}")
            print(f"   元数据: {doc.metadata}")
        
        # 带分数的相似度搜索
        results_with_scores = vector_store.similarity_search_with_score(query, k=3)
        print("\n带分数的搜索结果:")
        for i, (doc, score) in enumerate(results_with_scores):
            print(f"{i+1}. {doc.page_content} (相似度: {score:.4f})")
        
        print()
        
    except Exception as e:
        print(f"FAISS示例失败: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

def chroma_vector_store_example():
    """Chroma向量存储示例"""
    print("=== Chroma向量存储示例 ===")
    
    # 创建示例文档
    documents = [
        Document(page_content="Python是一种高级编程语言", metadata={"source": "python", "type": "language"}),
        Document(page_content="JavaScript用于网页开发", metadata={"source": "javascript", "type": "language"}),
        Document(page_content="React是前端框架", metadata={"source": "react", "type": "framework"}),
        Document(page_content="Django是Python Web框架", metadata={"source": "django", "type": "framework"}),
        Document(page_content="Node.js运行在服务器上", metadata={"source": "nodejs", "type": "runtime"})
    ]
    
    try:
        # 创建嵌入模型
        embeddings = OpenAIEmbeddings()
        
        # 创建Chroma向量存储
        vector_store = Chroma.from_documents(documents, embeddings)
        
        # 相似度搜索
        query = "什么是Web开发"
        results = vector_store.similarity_search(query, k=3)
        
        print(f"查询: {query}")
        print("搜索结果:")
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content}")
            print(f"   元数据: {doc.metadata}")
        
        # 元数据过滤搜索
        print("\n元数据过滤搜索 (type=framework):")
        filtered_results = vector_store.similarity_search(
            query="开发技术", 
            filter={"type": "framework"},
            k=2
        )
        
        for i, doc in enumerate(filtered_results):
            print(f"{i+1}. {doc.page_content}")
            print(f"   元数据: {doc.metadata}")
        
        print()
        
    except Exception as e:
        print(f"Chroma示例失败: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

def retrieval_qa_example():
    """检索问答示例"""
    print("=== 检索问答示例 ===")
    
    # 创建知识库文档
    knowledge_base = [
        "Python是一种解释型、高级编程语言，具有简洁的语法。",
        "JavaScript是一种脚本语言，主要用于网页开发。",
        "React是Facebook开发的用于构建用户界面的JavaScript库。",
        "Django是Python的高级Web框架，鼓励快速开发和干净的设计。",
        "SQL是一种用于管理关系数据库的标准语言。"
    ]
    
    try:
        # 创建嵌入模型和向量存储
        embeddings = OpenAIEmbeddings()
        vector_store = FAISS.from_texts(knowledge_base, embeddings)
        
        # 创建检索器
        retriever = vector_store.as_retriever(search_kwargs={"k": 3})
        
        # 创建问答链
        qa_chain = RetrievalQA.from_chain_type(
            llm=ChatOpenAI(model="gpt-3.5-turbo", temperature=0),
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True
        )
        
        # 测试问答
        questions = [
            "Python有什么特点？",
            "React是用来做什么的？",
            "什么是Django？"
        ]
        
        for question in questions:
            print(f"问题: {question}")
            result = qa_chain.invoke({"query": question})
            
            print(f"回答: {result['result']}")
            print("相关文档:")
            for i, doc in enumerate(result['source_documents'], 1):
                print(f"  {i}. {doc.page_content}")
            print("-" * 50)
        
    except Exception as e:
        print(f"检索问答示例失败: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

def main():
    """主函数，运行所有示例"""
    print("LangChain Indexes 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # Document Loaders示例
        text_loader_example()
        csv_loader_example()
        json_loader_example()
        web_loader_example()
        
        # Text Splitters示例
        character_text_splitter_example()
        recursive_character_text_splitter_example()
        token_text_splitter_example()
        
        # Vector Stores示例
        faiss_vector_store_example()
        chroma_vector_store_example()
        
        # 检索问答示例
        retrieval_qa_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
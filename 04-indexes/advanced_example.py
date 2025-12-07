#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Indexes 组件高级示例
演示自定义文档加载器、高级文本分割器、向量存储优化等高级功能
"""

import os
import asyncio
import json
import time
from typing import List, Dict, Any, Optional, Iterator
from abc import ABC, abstractmethod
import numpy as np
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders.base import BaseLoader
from langchain_core.text_splitter import TextSplitter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS, Chroma
from langchain.retrievers import MultiQueryRetriever, ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain_openai import ChatOpenAI
import requests
from bs4 import BeautifulSoup
import tiktoken

# 设置API密钥（请替换为您的实际密钥）
os.environ["OPENAI_API_KEY"] = "your-openai-api-key-here"

class CustomWebLoader(BaseLoader):
    """自定义网页加载器"""
    
    def __init__(self, urls: List[str], extract_links: bool = False):
        self.urls = urls
        self.extract_links = extract_links
    
    def load(self) -> List[Document]:
        """加载所有网页内容"""
        documents = []
        for url in self.urls:
            documents.extend(self._load_single_url(url))
        return documents
    
    def _load_single_url(self, url: str) -> List[Document]:
        """加载单个URL"""
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # 解析HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 提取主要内容
            title = soup.find('title')
            title_text = title.get_text() if title else url
            
            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()
            
            # 提取文本内容
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = '\n'.join(chunk for chunk in chunks if chunk)
            
            # 创建文档
            doc = Document(
                page_content=text,
                metadata={
                    "source": url,
                    "title": title_text,
                    "extracted_at": time.time(),
                    "content_type": "html"
                }
            )
            
            return [doc]
            
        except Exception as e:
            print(f"加载URL失败 {url}: {e}")
            return []

class SemanticTextSplitter(TextSplitter):
    """基于语义的文本分割器"""
    
    def __init__(
        self,
        embeddings_model=None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        similarity_threshold: float = 0.7
    ):
        super().__init__(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.similarity_threshold = similarity_threshold
    
    def split_text(self, text: str) -> List[str]:
        """基于语义分割文本"""
        # 首先按段落分割
        paragraphs = text.split('\n\n')
        
        if len(paragraphs) <= 1:
            return [text]
        
        # 计算段落嵌入
        paragraph_embeddings = self.embeddings_model.embed_documents(paragraphs)
        
        # 基于相似度分组段落
        groups = self._group_by_similarity(paragraphs, paragraph_embeddings)
        
        # 合并组为最终分块
        chunks = self._merge_groups_to_chunks(groups)
        
        return chunks
    
    def _group_by_similarity(self, paragraphs: List[str], embeddings: List[List[float]]) -> List[List[str]]:
        """基于相似度分组段落"""
        groups = []
        current_group = [paragraphs[0]]
        
        for i in range(1, len(paragraphs)):
            # 计算与组内平均嵌入的相似度
            current_group_embeddings = embeddings[:len(current_group)]
            avg_embedding = np.mean(current_group_embeddings, axis=0)
            
            similarity = self._cosine_similarity(embeddings[i], avg_embedding)
            
            if similarity > self.similarity_threshold and len('\n'.join(current_group + [paragraphs[i]])) <= self.chunk_size:
                current_group.append(paragraphs[i])
            else:
                groups.append(current_group)
                current_group = [paragraphs[i]]
        
        if current_group:
            groups.append(current_group)
        
        return groups
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        vec1_np = np.array(vec1)
        vec2_np = np.array(vec2)
        
        dot_product = np.dot(vec1_np, vec2_np)
        norm1 = np.linalg.norm(vec1_np)
        norm2 = np.linalg.norm(vec2_np)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _merge_groups_to_chunks(self, groups: List[List[str]]) -> List[str]:
        """将组合并为最终分块"""
        chunks = []
        current_chunk = ""
        
        for group in groups:
            group_text = '\n\n'.join(group)
            
            if len(current_chunk) + len(group_text) <= self.chunk_size:
                current_chunk += ("\n\n" if current_chunk else "") + group_text
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = group_text
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """分割文档"""
        split_docs = []
        
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            
            for i, chunk in enumerate(chunks):
                new_doc = Document(
                    page_content=chunk,
                    metadata={
                        **doc.metadata,
                        "chunk_index": i,
                        "splitter_type": "semantic",
                        "total_chunks": len(chunks)
                    }
                )
                split_docs.append(new_doc)
        
        return split_docs

class AdvancedVectorStore:
    """高级向量存储管理器"""
    
    def __init__(self, embeddings_model=None, store_type="faiss"):
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.store_type = store_type
        self.vector_store = None
        self.documents = []
    
    def add_documents(self, documents: List[Document], batch_size: int = 100):
        """批量添加文档"""
        print(f"开始添加 {len(documents)} 个文档...")
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            print(f"处理批次 {i//batch_size + 1}/{(len(documents)-1)//batch_size + 1}")
            
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            
            if self.vector_store is None:
                # 初始化向量存储
                if self.store_type == "faiss":
                    self.vector_store = FAISS.from_texts(texts, self.embeddings_model, metadatas)
                elif self.store_type == "chroma":
                    self.vector_store = Chroma.from_texts(texts, self.embeddings_model, metadatas)
            else:
                # 添加到现有存储
                self.vector_store.add_texts(texts, metadatas)
            
            self.documents.extend(batch)
        
        print("文档添加完成")
    
    def similarity_search(self, query: str, k: int = 5, filter_dict: Optional[Dict] = None):
        """相似度搜索"""
        if self.vector_store is None:
            raise ValueError("向量存储为空，请先添加文档")
        
        if filter_dict and hasattr(self.vector_store, 'similarity_search'):
            return self.vector_store.similarity_search(query, k=k, filter=filter_dict)
        else:
            return self.vector_store.similarity_search(query, k=k)
    
    def search_with_scores(self, query: str, k: int = 5):
        """带分数的搜索"""
        if self.vector_store is None:
            raise ValueError("向量存储为空，请先添加文档")
        
        if hasattr(self.vector_store, 'similarity_search_with_score'):
            return self.vector_store.similarity_search_with_score(query, k=k)
        else:
            # 如果不支持带分数搜索，返回普通搜索结果
            results = self.vector_store.similarity_search(query, k=k)
            return [(doc, 0.0) for doc in results]
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "total_documents": len(self.documents),
            "store_type": self.store_type,
            "embeddings_model": type(self.embeddings_model).__name__
        }

class MultiSourceRetriever:
    """多源检索器"""
    
    def __init__(self, retrievers: Dict[str, Any], weights: Optional[Dict[str, float]] = None):
        self.retrievers = retrievers
        self.weights = weights or {name: 1.0 for name in retrievers.keys()}
    
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """从多个源检索文档"""
        all_results = {}
        
        # 从每个检索器获取结果
        for name, retriever in self.retrievers.items():
            try:
                results = retriever.get_relevant_documents(query)[:k]
                for doc in results:
                    doc_id = f"{name}_{hash(doc.page_content)}"
                    if doc_id not in all_results:
                        all_results[doc_id] = {
                            "document": doc,
                            "sources": [],
                            "total_score": 0.0
                        }
                    all_results[doc_id]["sources"].append(name)
                    all_results[doc_id]["total_score"] += self.weights.get(name, 1.0)
            except Exception as e:
                print(f"检索器 {name} 失败: {e}")
        
        # 按总分排序
        sorted_results = sorted(
            all_results.values(),
            key=lambda x: x["total_score"],
            reverse=True
        )
        
        # 添加来源信息到元数据
        final_results = []
        for result in sorted_results[:k]:
            doc = result["document"]
            doc.metadata["retrieval_sources"] = result["sources"]
            doc.metadata["retrieval_score"] = result["total_score"]
            final_results.append(doc)
        
        return final_results

class IncrementalIndexer:
    """增量索引器"""
    
    def __init__(self, vector_store_manager: AdvancedVectorStore):
        self.vector_store_manager = vector_store_manager
        self.processed_hashes = set()
    
    def add_documents_incremental(self, documents: List[Document]) -> Dict[str, int]:
        """增量添加文档，跳过重复文档"""
        new_docs = []
        skipped_count = 0
        
        for doc in documents:
            doc_hash = self._compute_document_hash(doc)
            
            if doc_hash not in self.processed_hashes:
                new_docs.append(doc)
                self.processed_hashes.add(doc_hash)
            else:
                skipped_count += 1
        
        if new_docs:
            self.vector_store_manager.add_documents(new_docs)
        
        return {
            "added": len(new_docs),
            "skipped": skipped_count,
            "total": len(documents)
        }
    
    def _compute_document_hash(self, doc: Document) -> str:
        """计算文档哈希值"""
        content = doc.page_content
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()

def custom_web_loader_example():
    """自定义网页加载器示例"""
    print("=== 自定义网页加载器示例 ===")
    
    try:
        # 创建自定义加载器
        urls = [
            "https://www.python.org/about/",
            "https://www.python.org/doc/"
        ]
        
        loader = CustomWebLoader(urls)
        documents = loader.load()
        
        print(f"加载的文档数量: {len(documents)}")
        for i, doc in enumerate(documents):
            print(f"文档 {i+1}:")
            print(f"标题: {doc.metadata.get('title', '无标题')}")
            print(f"来源: {doc.metadata['source']}")
            print(f"内容预览: {doc.page_content[:200]}...")
            print("-" * 50)
        
    except Exception as e:
        print(f"自定义网页加载器示例失败: {e}")
        print("这可能是由于网络连接问题")

def semantic_splitter_example():
    """语义分割器示例"""
    print("=== 语义分割器示例 ===")
    
    # 创建包含多个主题的文本
    sample_text = """
    人工智能（AI）是计算机科学的一个分支，它致力于创造能够执行通常需要人类智能的任务的机器。
    AI的主要目标是使计算机能够感知、推理、学习和决策。

    机器学习是人工智能的核心技术之一。它使计算机能够在没有明确编程的情况下学习和改进。
    监督学习使用标记数据进行训练，而无监督学习从无标记数据中发现模式。

    深度学习是机器学习的一个子集，它使用多层神经网络来模拟人脑的学习过程。
    卷积神经网络（CNN）在图像识别任务中表现出色，而循环神经网络（RNN）更适合处理序列数据。

    自然语言处理（NLP）是人工智能的另一个重要分支。它使计算机能够理解、解释和生成人类语言。
    现代的NLP系统通常基于Transformer架构，如BERT和GPT模型。
    """
    
    try:
        # 创建语义分割器
        splitter = SemanticTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            similarity_threshold=0.6
        )
        
        # 分割文本
        chunks = splitter.split_text(sample_text)
        
        print(f"分割后的块数量: {len(chunks)}")
        print("分割结果:")
        for i, chunk in enumerate(chunks):
            print(f"块 {i+1}:")
            print(chunk)
            print(f"长度: {len(chunk)}")
            print("-" * 50)
        
    except Exception as e:
        print(f"语义分割器示例失败: {e}")

def advanced_vector_store_example():
    """高级向量存储示例"""
    print("=== 高级向量存储示例 ===")
    
    # 创建示例文档
    documents = [
        Document(page_content="Python是一种高级编程语言，具有简洁的语法", 
                metadata={"source": "python_intro", "category": "programming"}),
        Document(page_content="JavaScript是用于网页开发的脚本语言", 
                metadata={"source": "javascript_intro", "category": "web"}),
        Document(page_content="React是Facebook开发的前端框架", 
                metadata={"source": "react_intro", "category": "framework"}),
        Document(page_content="Django是Python的Web开发框架", 
                metadata={"source": "django_intro", "category": "framework"}),
        Document(page_content="Node.js使JavaScript能在服务器端运行", 
                metadata={"source": "nodejs_intro", "category": "backend"}),
        Document(page_content="SQL是用于管理关系数据库的语言", 
                metadata={"source": "sql_intro", "category": "database"})
    ]
    
    try:
        # 创建高级向量存储管理器
        vector_manager = AdvancedVectorStore(store_type="faiss")
        
        # 添加文档
        vector_manager.add_documents(documents)
        
        # 获取统计信息
        stats = vector_manager.get_stats()
        print(f"向量存储统计: {stats}")
        
        # 相似度搜索
        query = "什么是前端开发？"
        results = vector_manager.similarity_search(query, k=3)
        
        print(f"\n查询: {query}")
        print("搜索结果:")
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content}")
            print(f"   元数据: {doc.metadata}")
        
        # 带分数的搜索
        print("\n带分数的搜索:")
        results_with_scores = vector_manager.search_with_scores(query, k=3)
        for i, (doc, score) in enumerate(results_with_scores):
            print(f"{i+1}. {doc.page_content} (相似度: {score:.4f})")
        
        # 元数据过滤搜索
        print("\n元数据过滤搜索 (category=framework):")
        filtered_results = vector_manager.similarity_search(
            query="开发技术", 
            filter_dict={"category": "framework"},
            k=2
        )
        
        for i, doc in enumerate(filtered_results):
            print(f"{i+1}. {doc.page_content}")
            print(f"   元数据: {doc.metadata}")
        
    except Exception as e:
        print(f"高级向量存储示例失败: {e}")

def multi_source_retriever_example():
    """多源检索器示例"""
    print("=== 多源检索器示例 ===")
    
    try:
        # 创建两个不同的向量存储
        programming_docs = [
            Document(page_content="Python是一种解释型编程语言", metadata={"source": "programming_db"}),
            Document(page_content="Java是一种面向对象的编程语言", metadata={"source": "programming_db"})
        ]
        
        web_docs = [
            Document(page_content="HTML是网页的标记语言", metadata={"source": "web_db"}),
            Document(page_content="CSS用于网页样式设计", metadata={"source": "web_db"})
        ]
        
        # 创建向量存储
        embeddings = OpenAIEmbeddings()
        
        programming_store = FAISS.from_documents(programming_docs, embeddings)
        web_store = FAISS.from_documents(web_docs, embeddings)
        
        # 创建检索器
        programming_retriever = programming_store.as_retriever()
        web_retriever = web_store.as_retriever()
        
        # 创建多源检索器
        multi_retriever = MultiSourceRetriever({
            "programming": programming_retriever,
            "web": web_retriever
        })
        
        # 检索测试
        queries = [
            "编程语言特点",
            "网页开发技术"
        ]
        
        for query in queries:
            print(f"查询: {query}")
            results = multi_retriever.retrieve(query, k=3)
            
            for i, doc in enumerate(results):
                print(f"{i+1}. {doc.page_content}")
                print(f"   来源: {doc.metadata.get('retrieval_sources', [])}")
                print(f"   分数: {doc.metadata.get('retrieval_score', 0):.2f}")
            print("-" * 50)
        
    except Exception as e:
        print(f"多源检索器示例失败: {e}")

def incremental_indexer_example():
    """增量索引器示例"""
    print("=== 增量索引器示例 ===")
    
    # 创建向量存储管理器
    vector_manager = AdvancedVectorStore(store_type="faiss")
    indexer = IncrementalIndexer(vector_manager)
    
    # 第一批文档
    batch1 = [
        Document(page_content="第一批文档1", metadata={"batch": 1}),
        Document(page_content="第一批文档2", metadata={"batch": 1})
    ]
    
    # 第二批文档（包含重复）
    batch2 = [
        Document(page_content="第二批文档1", metadata={"batch": 2}),
        Document(page_content="第一批文档1", metadata={"batch": 2}),  # 重复
        Document(page_content="第二批文档2", metadata={"batch": 2})
    ]
    
    # 第三批文档
    batch3 = [
        Document(page_content="第三批文档1", metadata={"batch": 3}),
        Document(page_content="第一批文档1", metadata={"batch": 3}),  # 重复
        Document(page_content="第三批文档2", metadata={"batch": 3})
    ]
    
    try:
        # 增量添加文档
        print("处理第一批文档:")
        result1 = indexer.add_documents_incremental(batch1)
        print(f"结果: {result1}")
        
        print("\n处理第二批文档:")
        result2 = indexer.add_documents_incremental(batch2)
        print(f"结果: {result2}")
        
        print("\n处理第三批文档:")
        result3 = indexer.add_documents_incremental(batch3)
        print(f"结果: {result3}")
        
        # 最终统计
        final_stats = vector_manager.get_stats()
        print(f"\n最终统计: {final_stats}")
        
        # 测试搜索
        print("\n搜索测试:")
        results = vector_manager.similarity_search("第一批", k=5)
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content} (批次: {doc.metadata.get('batch', 'unknown')})")
        
    except Exception as e:
        print(f"增量索引器示例失败: {e}")

async def async_document_processing_example():
    """异步文档处理示例"""
    print("=== 异步文档处理示例 ===")
    
    # 创建大量文档
    documents = []
    for i in range(20):
        doc = Document(
            page_content=f"这是第 {i+1} 个文档的内容，包含一些关于主题 {i%5+1} 的信息。",
            metadata={"doc_id": i+1, "topic": i%5+1}
        )
        documents.append(doc)
    
    try:
        # 创建向量存储管理器
        vector_manager = AdvancedVectorStore(store_type="faiss")
        
        # 异步批量处理
        print("开始异步批量处理...")
        start_time = time.time()
        
        # 分批处理
        batch_size = 5
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            print(f"处理批次 {i//batch_size + 1}")
            
            # 模拟异步处理
            await asyncio.sleep(0.1)  # 模拟处理时间
            vector_manager.add_documents(batch)
        
        end_time = time.time()
        print(f"处理完成，耗时: {end_time - start_time:.2f}秒")
        
        # 测试搜索
        print("\n搜索测试:")
        results = vector_manager.similarity_search("主题3", k=3)
        for i, doc in enumerate(results):
            print(f"{i+1}. {doc.page_content} (主题: {doc.metadata.get('topic', 'unknown')})")
        
    except Exception as e:
        print(f"异步文档处理示例失败: {e}")

def performance_comparison_example():
    """性能比较示例"""
    print("=== 性能比较示例 ===")
    
    # 创建测试文档
    documents = []
    for i in range(10):
        content = f"文档 {i+1} 的内容。" + "这是一个测试文档。" * 20
        doc = Document(
            page_content=content,
            metadata={"doc_id": i+1, "length": len(content)}
        )
        documents.append(doc)
    
    try:
        # 比较不同的分割器
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        print("比较分割器性能:")
        
        # 递归字符分割器
        recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50
        )
        
        start_time = time.time()
        recursive_chunks = recursive_splitter.split_documents(documents)
        recursive_time = time.time() - start_time
        
        # 语义分割器
        semantic_splitter = SemanticTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            similarity_threshold=0.7
        )
        
        start_time = time.time()
        semantic_chunks = semantic_splitter.split_documents(documents)
        semantic_time = time.time() - start_time
        
        print(f"递归分割器: {len(recursive_chunks)} 个分块, 耗时: {recursive_time:.3f}秒")
        print(f"语义分割器: {len(semantic_chunks)} 个分块, 耗时: {semantic_time:.3f}秒")
        print(f"性能比: {semantic_time/recursive_time:.2f}x")
        
        # 比较向量存储
        print("\n比较向量存储性能:")
        
        embeddings = OpenAIEmbeddings()
        test_query = "测试查询"
        
        # FAISS存储
        start_time = time.time()
        faiss_store = FAISS.from_documents(recursive_chunks[:5], embeddings)
        faiss_results = faiss_store.similarity_search(test_query, k=3)
        faiss_time = time.time() - start_time
        
        # Chroma存储
        start_time = time.time()
        chroma_store = Chroma.from_documents(recursive_chunks[:5], embeddings)
        chroma_results = chroma_store.similarity_search(test_query, k=3)
        chroma_time = time.time() - start_time
        
        print(f"FAISS存储: 搜索耗时 {faiss_time:.3f}秒")
        print(f"Chroma存储: 搜索耗时 {chroma_time:.3f}秒")
        print(f"性能比: {chroma_time/faiss_time:.2f}x")
        
    except Exception as e:
        print(f"性能比较示例失败: {e}")

def main():
    """主函数，运行所有高级示例"""
    print("LangChain Indexes 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 自定义加载器示例
        custom_web_loader_example()
        
        # 高级分割器示例
        semantic_splitter_example()
        
        # 高级向量存储示例
        advanced_vector_store_example()
        
        # 多源检索器示例
        multi_source_retriever_example()
        
        # 增量索引器示例
        incremental_indexer_example()
        
        # 异步处理示例
        asyncio.run(async_document_processing_example())
        
        # 性能比较示例
        performance_comparison_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
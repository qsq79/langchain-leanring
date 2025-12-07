#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Memory 组件高级示例
演示自定义Memory、异步Memory、持久化Memory等高级功能
"""

import os
import sys
import asyncio
import json
import time
import pickle
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.memory import BaseMemory
from langchain_core.chat_memory import BaseChatMemory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, get_buffer_string
from langchain.chains import LLMChain, ConversationChain
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.memory import (
    ConversationBufferMemory,
    VectorStoreRetrieverMemory,
    MongoDBChatMessageHistory,
    RedisChatMessageHistory
)
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import redis
from pymongo import MongoClient
import threading

# 添加utils目录到系统路径，以便导入配置加载器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class CustomMemory(BaseChatMemory):
    """自定义Memory组件示例"""
    
    def __init__(
        self,
        max_messages: int = 100,
        importance_threshold: float = 0.5,
        save_important_only: bool = False
    ):
        super().__init__()
        self.max_messages = max_messages
        self.importance_threshold = importance_threshold
        self.save_important_only = save_important_only
        self.importance_scores = {}
    
    @property
    def chat_memory(self):
        return self.messages
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """保存对话上下文"""
        # 添加输入消息
        if "input" in inputs:
            input_msg = HumanMessage(content=inputs["input"])
            self.messages.append(input_msg)
        
        # 添加输出消息
        if "output" in outputs:
            output_msg = AIMessage(content=outputs["output"])
            self.messages.append(output_msg)
        
        # 计算重要性分数
        if self.save_important_only:
            self._calculate_importance()
        
        # 限制消息数量
        if len(self.messages) > self.max_messages:
            self._trim_messages()
    
    def _calculate_importance(self):
        """计算消息的重要性"""
        # 简化的重要性计算逻辑
        for i, msg in enumerate(self.messages):
            content = msg.content
            
            # 基于内容长度和关键词计算重要性
            score = min(len(content) / 100, 1.0)
            
            # 检查重要关键词
            important_keywords = ["重要", "关键", "必须", "记住", "总结"]
            for keyword in important_keywords:
                if keyword in content:
                    score += 0.2
            
            self.importance_scores[i] = min(score, 1.0)
    
    def _trim_messages(self):
        """修剪消息，保留重要消息"""
        if not self.save_important_only:
            # 简单的FIFO修剪
            self.messages = self.messages[-self.max_messages:]
            return
        
        # 基于重要性的智能修剪
        if len(self.messages) <= self.max_messages:
            return
        
        # 按重要性排序，保留最重要的消息
        message_scores = []
        for i, msg in enumerate(self.messages):
            score = self.importance_scores.get(i, 0.0)
            message_scores.append((i, msg, score))
        
        # 按分数排序，保留高分数消息
        message_scores.sort(key=lambda x: x[2], reverse=True)
        
        # 保留最重要的消息并重新排序
        important_messages = []
        for i, msg, score in message_scores[:self.max_messages]:
            important_messages.append((i, msg))
        
        # 按原始顺序重新排列
        important_messages.sort(key=lambda x: x[0])
        self.messages = [msg for i, msg in important_messages]
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """加载记忆变量"""
        buffer_string = get_buffer_string(self.messages)
        return {
            "history": buffer_string,
            "message_count": len(self.messages),
            "important_messages": self._get_important_messages()
        }
    
    def _get_important_messages(self) -> str:
        """获取重要消息摘要"""
        if not self.importance_scores:
            return "无重要性评分"
        
        important_indices = [
            i for i, score in self.importance_scores.items()
            if score >= self.importance_threshold
        ]
        
        important_contents = [
            self.messages[i].content
            for i in important_indices
            if i < len(self.messages)
        ]
        
        return " | ".join(important_contents[:3])  # 限制输出长度
    
    def clear(self) -> None:
        """清空记忆"""
        self.messages.clear()
        self.importance_scores.clear()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "total_messages": len(self.messages),
            "max_messages": self.max_messages,
            "importance_threshold": self.importance_threshold,
            "save_important_only": self.save_important_only,
            "average_importance": sum(self.importance_scores.values()) / len(self.importance_scores) if self.importance_scores else 0
        }

class PersistentMemory(BaseChatMemory):
    """持久化Memory组件"""
    
    def __init__(self, storage_path: str = "memory.pkl", auto_save: bool = True):
        super().__init__()
        self.storage_path = storage_path
        self.auto_save = auto_save
        self.load_from_storage()
    
    @property
    def chat_memory(self):
        return self.messages
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """保存对话上下文"""
        # 添加消息
        if "input" in inputs:
            self.messages.append(HumanMessage(content=inputs["input"]))
        if "output" in outputs:
            self.messages.append(AIMessage(content=outputs["output"]))
        
        # 自动保存到存储
        if self.auto_save:
            self.save_to_storage()
    
    def save_to_storage(self):
        """保存到存储"""
        try:
            # 将消息转换为可序列化的格式
            serializable_messages = []
            for msg in self.messages:
                serializable_messages.append({
                    "type": msg.type,
                    "content": msg.content,
                    "additional_kwargs": getattr(msg, 'additional_kwargs', {})
                })
            
            # 保存到文件
            with open(self.storage_path, 'wb') as f:
                pickle.dump(serializable_messages, f)
                
        except Exception as e:
            print(f"保存Memory失败: {e}")
    
    def load_from_storage(self):
        """从存储加载"""
        try:
            if os.path.exists(self.storage_path):
                with open(self.storage_path, 'rb') as f:
                    serializable_messages = pickle.load(f)
                
                # 恢复消息
                self.messages = []
                for msg_data in serializable_messages:
                    if msg_data["type"] == "human":
                        msg = HumanMessage(content=msg_data["content"])
                    elif msg_data["type"] == "ai":
                        msg = AIMessage(content=msg_data["content"])
                    else:
                        continue
                    
                    if hasattr(msg, 'additional_kwargs'):
                        msg.additional_kwargs = msg_data.get("additional_kwargs", {})
                    
                    self.messages.append(msg)
                    
        except Exception as e:
            print(f"加载Memory失败: {e}")
            self.messages = []
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """加载记忆变量"""
        buffer_string = get_buffer_string(self.messages)
        return {"history": buffer_string}
    
    def clear(self) -> None:
        """清空记忆并删除存储文件"""
        self.messages.clear()
        if os.path.exists(self.storage_path):
            os.remove(self.storage_path)

class AsyncMemory(BaseChatMemory):
    """异步Memory组件"""
    
    def __init__(self, storage_backend=None):
        super().__init__()
        self.storage_backend = storage_backend
        self._lock = threading.Lock()
    
    @property
    def chat_memory(self):
        return self.messages
    
    async def asave_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """异步保存对话上下文"""
        with self._lock:
            # 添加消息
            if "input" in inputs:
                self.messages.append(HumanMessage(content=inputs["input"]))
            if "output" in outputs:
                self.messages.append(AIMessage(content=outputs["output"]))
            
            # 异步保存到后端
            if self.storage_backend:
                await self.storage_backend.async_save(self.messages)
    
    async def aload_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """异步加载记忆变量"""
        with self._lock:
            if self.storage_backend:
                messages = await self.storage_backend.async_load()
                self.messages = messages
            
            buffer_string = get_buffer_string(self.messages)
            return {"history": buffer_string}
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """同步保存方法（兼容性）"""
        return asyncio.run(self.asave_context(inputs, outputs))
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """同步加载方法（兼容性）"""
        return asyncio.run(self.aload_memory_variables(inputs))
    
    def clear(self) -> None:
        """清空记忆"""
        with self._lock:
            self.messages.clear()
            if self.storage_backend:
                asyncio.run(self.storage_backend.async_clear())

class VectorRetrieverMemory:
    """基于向量检索的Memory"""
    
    def __init__(
        self,
        embeddings_model=None,
        vector_store_path: str = "vector_memory.faiss",
        max_retrieved: int = 5
    ):
        self.embeddings_model = embeddings_model or OpenAIEmbeddings()
        self.vector_store_path = vector_store_path
        self.max_retrieved = max_retrieved
        self.vector_store = None
        self.load_vector_store()
    
    def load_vector_store(self):
        """加载向量存储"""
        try:
            if os.path.exists(self.vector_store_path):
                self.vector_store = FAISS.load_local(
                    self.vector_store_path,
                    self.embeddings_model,
                    allow_dangerous_deserialization=True
                )
        except Exception as e:
            print(f"加载向量存储失败: {e}")
            self.vector_store = None
    
    def save_vector_store(self):
        """保存向量存储"""
        if self.vector_store:
            self.vector_store.save_local(self.vector_store_path)
    
    def add_conversation(self, conversation_text: str, metadata: Dict[str, Any] = None):
        """添加对话到向量存储"""
        if not self.vector_store:
            # 初始化向量存储
            self.vector_store = FAISS.from_texts(
                [conversation_text],
                self.embeddings_model,
                metadatas=[metadata or {}]
            )
        else:
            # 添加到现有存储
            self.vector_store.add_texts(
                [conversation_text],
                metadatas=[metadata or {}]
            )
        
        self.save_vector_store()
    
    def search_relevant_conversations(self, query: str) -> List[str]:
        """搜索相关对话"""
        if not self.vector_store:
            return []
        
        results = self.vector_store.similarity_search(query, k=self.max_retrieved)
        return [doc.page_content for doc in results]

class MemoryManager:
    """Memory管理器"""
    
    def __init__(self):
        self.memories = {}
        self.active_memory = None
    
    def register_memory(self, name: str, memory: BaseMemory):
        """注册Memory组件"""
        self.memories[name] = memory
    
    def set_active_memory(self, name: str):
        """设置活跃的Memory"""
        if name not in self.memories:
            raise ValueError(f"未注册的Memory: {name}")
        self.active_memory = self.memories[name]
    
    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]):
        """保存到活跃的Memory"""
        if self.active_memory:
            self.active_memory.save_context(inputs, outputs)
    
    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """从活跃的Memory加载"""
        if self.active_memory:
            return self.active_memory.load_memory_variables(inputs)
        return {}
    
    def get_memory_stats(self, name: str) -> Dict[str, Any]:
        """获取Memory统计"""
        if name in self.memories and hasattr(self.memories[name], 'get_memory_stats'):
            return self.memories[name].get_memory_stats()
        return {"error": "Memory不支持统计功能"}

def custom_memory_example():
    """自定义Memory示例"""
    print("=== 自定义Memory示例 ===")
    
    # 创建自定义Memory
    custom_memory = CustomMemory(
        max_messages=10,
        importance_threshold=0.3,
        save_important_only=True
    )
    
    # 模拟对话
    conversations = [
        {"input": "你好", "output": "你好！有什么可以帮助你的吗？"},
        {"input": "记住这个重要的信息：会议时间是下午3点", "output": "好的，我记住了会议时间是下午3点。"},
        {"input": "明天天气怎么样？", "output": "明天会是晴天，温度25度。"},
        {"input": "关键是记住会议时间", "output": "是的，下午3点的会议很重要。"},
        {"input": "随便聊聊", "output": "好的，你想聊什么呢？"}
    ]
    
    # 保存对话
    for conv in conversations:
        custom_memory.save_context(conv["input"], conv["output"])
        print(f"保存: {conv['input']}")
    
    # 查看统计信息
    stats = custom_memory.get_memory_stats()
    print(f"\nMemory统计: {stats}")
    
    # 查看重要消息
    memory_vars = custom_memory.load_memory_variables({})
    print(f"\n重要消息: {memory_vars['important_messages']}")
    print()

def persistent_memory_example():
    """持久化Memory示例"""
    print("=== 持久化Memory示例 ===")
    
    # 创建持久化Memory
    persistent_memory = PersistentMemory(storage_path="test_memory.pkl")
    
    # 第一次对话
    print("第一次对话:")
    first_conversations = [
        {"input": "我叫张三", "output": "你好张三，很高兴认识你！"},
        {"input": "我是一名软件工程师", "output": "软件工程师是个很好的职业！"}
    ]
    
    for conv in first_conversations:
        persistent_memory.save_context(conv["input"], conv["output"])
        print(f"保存: {conv['input']} -> {conv['output']}")
    
    print("Memory已保存到文件")
    
    # 创建新的Memory实例（从文件加载）
    print("\n重新创建Memory实例:")
    new_memory = PersistentMemory(storage_path="test_memory.pkl")
    
    # 查看加载的历史
    memory_vars = new_memory.load_memory_variables({})
    print("从文件加载的对话历史:")
    print(memory_vars["history"])
    
    # 继续对话
    print("\n继续对话:")
    new_memory.save_context("我的专业是什么？", "你刚才提到你是一名软件工程师。")
    
    # 查看更新后的历史
    updated_vars = new_memory.load_memory_variables({})
    print("更新后的对话历史:")
    print(updated_vars["history"])
    
    # 清理测试文件
    if os.path.exists("test_memory.pkl"):
        os.remove("test_memory.pkl")
    print("\n测试文件已清理")
    print()

async def async_memory_example():
    """异步Memory示例"""
    print("=== 异步Memory示例 ===")
    
    # 创建异步Memory
    async_memory = AsyncMemory()
    
    # 模拟异步对话
    conversations = [
        {"input": "你好", "output": "你好！有什么可以帮助你的吗？"},
        {"input": "我想学习Python", "output": "Python是个很好的选择！"},
        {"input": "从哪里开始？", "output": "建议从基础语法开始学习。"}
    ]
    
    print("异步保存对话:")
    for conv in conversations:
        await async_memory.asave_context(conv["input"], conv["output"])
        print(f"异步保存: {conv['input']}")
        await asyncio.sleep(0.1)  # 模拟异步操作
    
    print("\n异步加载记忆:")
    memory_vars = await async_memory.aload_memory_variables({})
    print(memory_vars["history"])
    print()

def vector_retriever_memory_example():
    """向量检索Memory示例"""
    print("=== 向量检索Memory示例 ===")
    
    try:
        # 创建向量检索Memory
        vector_memory = VectorRetrieverMemory(
            vector_store_path="conversation_memory.faiss",
            max_retrieved=3
        )
        
        # 添加历史对话
        conversations = [
            {"text": "用户询问了Python的学习路径，我推荐了从基础开始", "topic": "Python学习"},
            {"text": "用户询问了机器学习算法，我介绍了监督学习和无监督学习", "topic": "机器学习"},
            {"text": "用户询问了Web开发框架，我推荐了React和Vue", "topic": "Web开发"},
            {"text": "用户询问了数据库选择，我比较了MySQL和PostgreSQL", "topic": "数据库"}
        ]
        
        for conv in conversations:
            vector_memory.add_conversation(
                conv["text"],
                {"topic": conv["topic"], "timestamp": time.time()}
            )
            print(f"添加对话: {conv['text'][:50]}...")
        
        # 搜索相关对话
        queries = [
            "Python编程",
            "机器学习算法",
            "Web框架",
            "数据库比较"
        ]
        
        for query in queries:
            print(f"\n查询: {query}")
            results = vector_memory.search_relevant_conversations(query)
            for i, result in enumerate(results, 1):
                print(f"{i}. {result}")
        
        # 清理测试文件
        if os.path.exists("conversation_memory.faiss"):
            os.remove("conversation_memory.faiss")
        
    except Exception as e:
        print(f"向量检索Memory示例失败: {e}")

def memory_manager_example():
    """Memory管理器示例"""
    print("=== Memory管理器示例 ===")
    
    # 创建Memory管理器
    manager = MemoryManager()
    
    # 注册不同类型的Memory
    buffer_memory = ConversationBufferMemory()
    custom_memory = CustomMemory(max_messages=5)
    
    manager.register_memory("buffer", buffer_memory)
    manager.register_memory("custom", custom_memory)
    
    # 设置活跃Memory并使用
    print("使用Buffer Memory:")
    manager.set_active_memory("buffer")
    
    buffer_conversations = [
        {"input": "你好", "output": "你好！"},
        {"input": "今天天气如何？", "output": "今天天气很好！"}
    ]
    
    for conv in buffer_conversations:
        manager.save_context(conv["input"], conv["output"])
    
    buffer_vars = manager.load_memory_variables({})
    print(f"Buffer Memory内容: {buffer_vars['history']}")
    
    # 切换到自定义Memory
    print("\n切换到Custom Memory:")
    manager.set_active_memory("custom")
    
    custom_conversations = [
        {"input": "记住这个重要信息", "output": "好的，我记住了这个重要信息。"},
        {"input": "随便说点什么", "output": "好的，这是一些随意的内容。"}
    ]
    
    for conv in custom_conversations:
        manager.save_context(conv["input"], conv["output"])
    
    custom_stats = manager.get_memory_stats("custom")
    print(f"Custom Memory统计: {custom_stats}")
    
    custom_vars = manager.load_memory_variables({})
    print(f"Custom Memory内容: {custom_vars.get('important_messages', '无重要消息')}")
    print()

def memory_with_chain_example():
    """Memory与Chain高级集成示例"""
    print("=== Memory与Chain高级集成示例 ===")
    
    # 创建自定义Memory
    custom_memory = CustomMemory(
        max_messages=8,
        importance_threshold=0.4,
        save_important_only=True
    )
    
    # 创建高级Prompt模板
    prompt = PromptTemplate(
        template="""你是一个专业的AI助手，能够记住重要的对话信息。

对话历史（包含重要信息）：
{history}

当前重要信息：
{important_messages}

用户当前问题：{input}

请基于历史对话和重要信息回答用户的问题：""",
        input_variables=["history", "important_messages", "input"]
    )
    
    # 创建Chain
    llm = OpenAI(temperature=0.7)
    chain = LLMChain(
        llm=llm,
        prompt=prompt,
        memory=custom_memory,
        verbose=True
    )
    
    # 模拟重要对话
    important_conversations = [
        {"input": "我叫张三，记住我的名字", "output": "好的张三，我记住了你的名字。"},
        {"input": "这个很重要：会议时间是明天下午3点", "output": "我记住了，明天下午3点有会议。"},
        {"input": "随便问问天气", "output": "今天天气不错，适合外出。"},
        {"input": "关键是要记住会议时间", "output": "是的，明天下午3点的会议很关键。"},
        {"input": "我的名字是什么？", "output": "根据我们的对话，你的名字是张三。"}
    ]
    
    print("进行重要对话测试:")
    for conv in important_conversations:
        print(f"\n用户: {conv['input']}")
        response = chain.invoke({"input": conv["input"]})
        print(f"AI: {response['text']}")
        
        # 显示Memory统计
        stats = custom_memory.get_memory_stats()
        print(f"Memory统计: 消息数={stats['total_messages']}, 平均重要性={stats['average_importance']:.2f}")
    
    print()

async def main():
    """主函数，运行所有高级示例"""
    print("LangChain Memory 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 自定义Memory示例
        custom_memory_example()
        
        # 持久化Memory示例
        persistent_memory_example()
        
        # 异步Memory示例
        await async_memory_example()
        
        # 向量检索Memory示例
        vector_retriever_memory_example()
        
        # Memory管理器示例
        memory_manager_example()
        
        # Memory与Chain高级集成
        memory_with_chain_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    asyncio.run(main())
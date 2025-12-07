#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Models 组件高级示例
演示自定义模型、异步调用、缓存、错误处理等高级功能
"""

import os
import sys
import asyncio
import time
from typing import List, Dict, Any, Optional
from functools import wraps
from langchain_openai import OpenAI, ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from langchain_core.language_models.llms import BaseLLM
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.embeddings import Embeddings
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.outputs import LLMResult, Generation, ChatResult, ChatGeneration
from langchain_core.callbacks import CallbackManagerForLLMRun, CallbackManagerForChatModelRun
from langchain_core.exceptions import LangChainException
from langchain.cache import InMemoryCache, GPTCache
from langchain.globals import set_llm_cache
import numpy as np
import requests
import json

# 添加utils目录到系统路径，以便导入配置加载器
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class CustomLLM(BaseLLM):
    """自定义LLM实现示例"""
    
    api_key: str
    base_url: str = "https://api.example.com/v1"
    model_name: str = "custom-model"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
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
        """调用自定义API"""
        try:
            # 模拟API调用
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "prompt": prompt,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens
            }
            
            if stop:
                data["stop"] = stop
            
            # 这里使用OpenAI作为示例，实际应该调用自定义API
            # response = requests.post(f"{self.base_url}/completions", headers=headers, json=data)
            # response.raise_for_status()
            # return response.json()["choices"][0]["text"]
            
            # 模拟响应
            return f"这是自定义模型的回复: {prompt[:50]}..."
            
        except Exception as e:
            raise LangChainException(f"Custom LLM调用失败: {str(e)}")
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> LLMResult:
        """批量生成"""
        generations = []
        for prompt in prompts:
            text = self._call(prompt, stop, run_manager, **kwargs)
            generations.append([Generation(text=text)])
        return LLMResult(generations=generations)

def retry_with_backoff(max_retries: int = 3, backoff_factor: float = 2.0):
    """重试装饰器，支持指数退避"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except LangChainException as e:
                    last_exception = e
                    if attempt == max_retries - 1:
                        break
                    
                    wait_time = backoff_factor ** attempt
                    print(f"调用失败，{wait_time}秒后重试... (尝试 {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
            
            raise last_exception
        return wrapper
    return decorator

class RobustLLM:
    """健壮的LLM包装器，包含错误处理和重试机制"""
    
    def __init__(self, llm: BaseLLM, max_retries: int = 3):
        self.llm = llm
        self.max_retries = max_retries
    
    @retry_with_backoff(max_retries=3)
    def invoke(self, prompt: str, **kwargs) -> str:
        """带重试的调用"""
        return self.llm.invoke(prompt, **kwargs)
    
    def batch_invoke(self, prompts: List[str], **kwargs) -> List[str]:
        """批量调用"""
        results = []
        for prompt in prompts:
            try:
                result = self.invoke(prompt, **kwargs)
                results.append(result)
            except Exception as e:
                print(f"批量调用失败: {prompt[:30]}... 错误: {e}")
                results.append(f"调用失败: {str(e)}")
        return results

def custom_llm_example():
    """自定义LLM示例"""
    print("=== 自定义LLM示例 ===")
    
    try:
        # 创建自定义LLM实例
        custom_llm = CustomLLM(
            api_key="your-custom-api-key",
            temperature=0.7,
            max_tokens=200
        )
        
        # 调用自定义LLM
        prompt = "请解释什么是量子计算？"
        response = custom_llm.invoke(prompt)
        
        print(f"输入: {prompt}")
        print(f"输出: {response}")
        print()
        
        # 批量调用
        prompts = [
            "什么是人工智能？",
            "什么是机器学习？"
        ]
        
        results = custom_llm.batch_invoke(prompts)
        for i, (prompt, result) in enumerate(zip(prompts, results)):
            print(f"批量{i+1}: {prompt}")
            print(f"结果{i+1}: {result}")
            print()
            
    except Exception as e:
        print(f"自定义LLM示例失败: {e}")

def error_handling_example():
    """错误处理和重试示例"""
    print("=== 错误处理和重试示例 ===")
    
    # 创建一个可能失败的LLM（使用无效的API密钥）
    problematic_llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.7,
        max_tokens=100,
        openai_api_key="invalid-key-for-demo"  # 故意使用无效密钥
    )
    
    # 使用健壮的LLM包装器
    robust_llm = RobustLLM(problematic_llm)
    
    try:
        # 尝试调用（会失败并重试）
        response = robust_llm.invoke("这是一个测试")
        print(f"响应: {response}")
    except Exception as e:
        print(f"最终失败: {e}")
    print()

def caching_example():
    """缓存机制示例"""
    print("=== 缓存机制示例 ===")
    
    # 设置内存缓存
    set_llm_cache(InMemoryCache())
    
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.3
    )
    
    prompt = "请用一句话解释什么是Python。"
    
    # 第一次调用（会真正调用API）
    print("第一次调用（无缓存）...")
    start_time = time.time()
    response1 = llm.invoke(prompt)
    first_call_time = time.time() - start_time
    print(f"响应: {response1}")
    print(f"耗时: {first_call_time:.2f}秒")
    print()
    
    # 第二次调用（从缓存获取）
    print("第二次调用（使用缓存）...")
    start_time = time.time()
    response2 = llm.invoke(prompt)
    second_call_time = time.time() - start_time
    print(f"响应: {response2}")
    print(f"耗时: {second_call_time:.2f}秒")
    print(f"速度提升: {(first_call_time - second_call_time):.2f}秒")
    print()

async def async_llm_example():
    """异步调用示例"""
    print("=== 异步调用示例 ===")
    
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.3
    )
    
    prompts = [
        "请解释什么是React框架。",
        "请解释什么是Vue框架。",
        "请解释什么是Angular框架。",
        "请解释什么是Svelte框架。"
    ]
    
    print("并发执行多个LLM调用...")
    start_time = time.time()
    
    # 创建异步任务
    tasks = [llm.ainvoke(prompt) for prompt in prompts]
    
    # 并发执行
    results = await asyncio.gather(*tasks)
    
    total_time = time.time() - start_time
    
    print(f"总耗时: {total_time:.2f}秒")
    print("结果:")
    for i, (prompt, result) in enumerate(zip(prompts, results)):
        print(f"{i+1}. {prompt[:30]}...")
        print(f"   {result.strip()}")
    print()

def token_cost_tracking_example():
    """Token和成本跟踪示例"""
    print("=== Token和成本跟踪示例 ===")
    
    from langchain_core.callbacks import get_openai_callback
    
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    prompts = [
        "请简要介绍人工智能的历史。",
        "请解释机器学习的基本概念。",
        "请列出深度学习的应用领域。"
    ]
    
    print("使用成本跟踪...")
    
    # 使用上下文管理器跟踪成本
    with get_openai_callback() as cb:
        for i, prompt in enumerate(prompts, 1):
            print(f"\n处理问题 {i}: {prompt}")
            response = llm.invoke(prompt)
            print(f"回答: {response.strip()}")
        
        print("\n=== 使用统计 ===")
        print(f"总Tokens: {cb.total_tokens}")
        print(f"提示Tokens: {cb.prompt_tokens}")
        print(f"完成Tokens: {cb.completion_tokens}")
        print(f"总成本: ${cb.total_cost:.6f}")
        print(f"成功调用次数: {cb.successful_requests}")
    print()

def semantic_similarity_advanced_example():
    """高级语义相似度分析示例"""
    print("=== 高级语义相似度分析 ===")
    
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002")
    
    # 文档集合
    documents = {
        "tech": [
            "Python是一种解释型、高级编程语言。",
            "JavaScript是一种用于网页开发的脚本语言。",
            "机器学习是人工智能的一个重要分支。"
        ],
        "nature": [
            "春天是万物复苏的季节。",
            "秋天是收获的季节，树叶变黄飘落。",
            "大海是地球上最大的水体，覆盖了大部分地表。"
        ],
        "philosophy": [
            "哲学是对存在和知识的根本研究。",
            "伦理学研究道德价值判断的标准。",
            "认识论探讨知识的本质和起源。"
        ]
    }
    
    # 查询文本
    queries = [
        "编程语言的特点",
        "季节变化",
        "道德和价值观"
    ]
    
    # 生成所有文档的嵌入
    all_embeddings = {}
    for category, docs in documents.items():
        print(f"生成 {category} 类别文档的嵌入...")
        all_embeddings[category] = embeddings.embed_documents(docs)
    
    # 为每个查询生成嵌入
    print("生成查询的嵌入...")
    query_embeddings = embeddings.embed_documents(queries)
    
    def cosine_similarity(vec1, vec2):
        """计算余弦相似度"""
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    # 分析查询与各类别的相似度
    for i, query in enumerate(queries):
        print(f"\n查询: '{query}'")
        
        query_embedding = query_embeddings[i]
        category_scores = {}
        
        for category, doc_embeddings in all_embeddings.items():
            # 计算查询与该类别所有文档的平均相似度
            similarities = [
                cosine_similarity(query_embedding, doc_embedding)
                for doc_embedding in doc_embeddings
            ]
            avg_similarity = np.mean(similarities)
            category_scores[category] = avg_similarity
        
        # 按相似度排序
        sorted_categories = sorted(category_scores.items(), key=lambda x: x[1], reverse=True)
        
        print("与各类别的相似度:")
        for category, score in sorted_categories:
            print(f"  {category}: {score:.4f}")
        
        # 找到最相关的文档
        best_category = sorted_categories[0][0]
        best_category_embeddings = all_embeddings[best_category]
        
        doc_similarities = [
            cosine_similarity(query_embedding, doc_embedding)
            for doc_embedding in best_category_embeddings
        ]
        
        best_doc_idx = np.argmax(doc_similarities)
        best_doc = documents[best_category][best_doc_idx]
        
        print(f"最相关的文档: '{best_doc}' (相似度: {doc_similarities[best_doc_idx]:.4f})")

def model_comparison_example():
    """模型性能对比示例"""
    print("=== 模型性能对比 ===")
    
    # 不同的模型配置
    models = {
        "gpt-3.5-turbo-instruct": OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3),
        # 注意：以下模型需要相应的API密钥
        # "gpt-4": OpenAI(model="gpt-4", temperature=0.3),
    }
    
    test_prompt = "请用50字以内解释什么是区块链技术。"
    
    results = {}
    
    for model_name, model in models.items():
        try:
            print(f"测试模型: {model_name}")
            
            # 测试响应时间
            start_time = time.time()
            response = model.invoke(test_prompt)
            end_time = time.time()
            
            results[model_name] = {
                "response": response.strip(),
                "response_time": end_time - start_time,
                "response_length": len(response.strip())
            }
            
            print(f"  响应: {response.strip()}")
            print(f"  响应时间: {results[model_name]['response_time']:.2f}秒")
            print(f"  响应长度: {results[model_name]['response_length']}字")
            print()
            
        except Exception as e:
            print(f"  模型 {model_name} 测试失败: {e}")
            print()
    
    # 输出对比结果
    print("=== 性能对比总结 ===")
    for model_name, result in results.items():
        print(f"{model_name}:")
        print(f"  响应时间: {result['response_time']:.2f}秒")
        print(f"  响应长度: {result['response_length']}字")
        print(f"  响应内容: {result['response']}")

async def main():
    """主函数，运行所有高级示例"""
    print("LangChain Models 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 同步示例
        custom_llm_example()
        error_handling_example()
        caching_example()
        
        # 异步示例
        await async_llm_example()
        
        # 分析示例
        token_cost_tracking_example()
        semantic_similarity_advanced_example()
        model_comparison_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    asyncio.run(main())
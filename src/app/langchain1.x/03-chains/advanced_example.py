#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Chains 组件高级示例
演示自定义Chain、并行处理、错误处理等高级功能
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.chains import Chain
from langchain_core.callbacks import CallbackManagerForChainRun
from langchain_core.runnables import RunnableParallel, RunnablePassthrough
from langchain_core.exceptions import LangChainException
import json
import logging

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CustomChain(Chain, BaseModel):
    """自定义Chain示例"""
    
    input_variables: List[str] = ["input_text"]
    output_variables: List[str] = ["processed_text"]
    processing_type: str = "uppercase"  # 处理类型：uppercase, lowercase, reverse
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """Chain的核心执行逻辑"""
        input_text = inputs["input_text"]
        
        if run_manager:
            run_manager.on_text(f"开始处理文本: {input_text}")
        
        # 自定义处理逻辑
        if self.processing_type == "uppercase":
            processed_text = input_text.upper()
        elif self.processing_type == "lowercase":
            processed_text = input_text.lower()
        elif self.processing_type == "reverse":
            processed_text = input_text[::-1]
        else:
            processed_text = input_text
        
        if run_manager:
            run_manager.on_text(f"处理完成: {processed_text}")
        
        return {"processed_text": processed_text}
    
    @property
    def _chain_type(self) -> str:
        return "custom_chain"

class ConditionalChain(Chain, BaseModel):
    """条件Chain示例"""
    
    input_variables: List[str] = ["input_text", "condition"]
    output_variables: List[str] = ["result"]
    true_chain: Chain
    false_chain: Chain
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """根据条件选择执行不同的Chain"""
        condition = inputs["condition"]
        
        if run_manager:
            run_manager.on_text(f"条件判断: {condition}")
        
        if condition:
            result = self.true_chain.invoke(inputs)
        else:
            result = self.false_chain.invoke(inputs)
        
        return {"result": result}
    
    @property
    def _chain_type(self) -> str:
        return "conditional_chain"

class RetryableChain(Chain, BaseModel):
    """可重试的Chain"""
    
    base_chain: Chain
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """带重试机制的执行"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if run_manager:
                    run_manager.on_text(f"尝试执行 (第 {attempt + 1} 次)")
                
                return self.base_chain.invoke(inputs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    if run_manager:
                        run_manager.on_text(f"执行失败，{self.retry_delay}秒后重试: {str(e)}")
                    time.sleep(self.retry_delay)
                    self.retry_delay *= 2  # 指数退避
                else:
                    if run_manager:
                        run_manager.on_text(f"所有重试都失败了: {str(e)}")
                    raise last_exception
    
    @property
    def _chain_type(self) -> str:
        return "retryable_chain"

class ParallelChain(Chain, BaseModel):
    """并行执行Chain"""
    
    chains: Dict[str, Chain]
    output_key: str = "results"
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """并行执行多个Chain"""
        if run_manager:
            run_manager.on_text("开始并行执行多个Chain")
        
        # 并行执行
        results = {}
        for name, chain in self.chains.items():
            try:
                result = chain.invoke(inputs)
                results[name] = result
            except Exception as e:
                if run_manager:
                    run_manager.on_text(f"Chain {name} 执行失败: {str(e)}")
                results[name] = {"error": str(e)}
        
        return {self.output_key: results}
    
    @property
    def _chain_type(self) -> str:
        return "parallel_chain"

class MetricsChain(Chain, BaseModel):
    """带指标收集的Chain"""
    
    base_chain: Chain
    metrics: Dict[str, Any] = {}
    
    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, Any]:
        """执行并收集指标"""
        start_time = time.time()
        
        try:
            result = self.base_chain.invoke(inputs)
            success = True
            error = None
        except Exception as e:
            success = False
            error = str(e)
            raise
        finally:
            end_time = time.time()
            
            # 收集指标
            self.metrics.update({
                "execution_time": end_time - start_time,
                "success": success,
                "error": error,
                "timestamp": end_time
            })
            
            if run_manager:
                run_manager.on_text(f"执行指标: {self.metrics}")
        
        return result
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取收集的指标"""
        return self.metrics.copy()
    
    @property
    def _chain_type(self) -> str:
        return "metrics_chain"

def custom_chain_example():
    """自定义Chain示例"""
    print("=== 自定义Chain示例 ===")
    
    # 创建不同类型的自定义Chain
    uppercase_chain = CustomChain(processing_type="uppercase")
    lowercase_chain = CustomChain(processing_type="lowercase")
    reverse_chain = CustomChain(processing_type="reverse")
    
    # 测试文本
    test_text = "Hello LangChain!"
    
    # 测试不同处理类型
    chains = [
        ("大写转换", uppercase_chain),
        ("小写转换", lowercase_chain),
        ("反转文本", reverse_chain)
    ]
    
    for name, chain in chains:
        result = chain.invoke({"input_text": test_text})
        print(f"{name}: {result['processed_text']}")
    print()

def conditional_chain_example():
    """条件Chain示例"""
    print("=== 条件Chain示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 创建两个不同的处理Chain
    positive_prompt = PromptTemplate(
        template="请用积极的方式回答：{input_text}",
        input_variables=["input_text"]
    )
    positive_chain = LLMChain(llm=llm, prompt=positive_prompt)
    
    negative_prompt = PromptTemplate(
        template="请用批判的方式分析：{input_text}",
        input_variables=["input_text"]
    )
    negative_chain = LLMChain(llm=llm, prompt=negative_prompt)
    
    # 创建条件Chain
    conditional_chain = ConditionalChain(
        true_chain=positive_chain,
        false_chain=negative_chain
    )
    
    # 测试不同的条件
    test_cases = [
        {"input_text": "人工智能的发展", "condition": True},
        {"input_text": "人工智能的风险", "condition": False}
    ]
    
    for case in test_cases:
        result = conditional_chain.invoke(case)
        print(f"输入: {case['input_text']}")
        print(f"条件: {case['condition']}")
        print(f"结果: {result['result']['text']}")
        print("-" * 50)
    print()

def retryable_chain_example():
    """可重试Chain示例"""
    print("=== 可重试Chain示例 ===")
    
    # 创建一个会失败的Chain（使用无效的API密钥）
    try:
        failing_llm = OpenAI(
            model="gpt-3.5-turbo-instruct",
            temperature=0.3,
            openai_api_key="invalid-key-for-demo"
        )
        
        prompt = PromptTemplate(
            template="请回答：{question}",
            input_variables=["question"]
        )
        
        failing_chain = LLMChain(llm=failing_llm, prompt=prompt)
        
        # 包装为可重试Chain
        retry_chain = RetryableChain(
            base_chain=failing_chain,
            max_retries=2,
            retry_delay=0.5
        )
        
        # 尝试执行（会失败并重试）
        try:
            result = retry_chain.invoke({"question": "什么是AI？"})
            print(f"成功执行: {result}")
        except Exception as e:
            print(f"最终失败: {e}")
            
    except Exception as e:
        print(f"重试示例失败: {e}")
    
    # 创建一个成功的重试示例
    print("\n成功的重试示例:")
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    prompt = PromptTemplate(
        template="请简要回答：{question}",
        input_variables=["question"]
    )
    successful_chain = LLMChain(llm=llm, prompt=prompt)
    retry_chain = RetryableChain(
        base_chain=successful_chain,
        max_retries=1,
        retry_delay=0.1
    )
    
    result = retry_chain.invoke({"question": "什么是Python？"})
    print(f"执行成功: {result['text']}")
    print()

def parallel_chain_example():
    """并行Chain示例"""
    print("=== 并行Chain示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 创建多个不同任务的Chain
    summary_prompt = PromptTemplate(
        template="请用一句话总结：{text}",
        input_variables=["text"]
    )
    summary_chain = LLMChain(llm=llm, prompt=summary_prompt)
    
    analysis_prompt = PromptTemplate(
        template="请分析以下内容的关键点：{text}",
        input_variables=["text"]
    )
    analysis_chain = LLMChain(llm=llm, prompt=analysis_prompt)
    
    translation_prompt = PromptTemplate(
        template="请将以下内容翻译成英文：{text}",
        input_variables=["text"]
    )
    translation_chain = LLMChain(llm=llm, prompt=translation_prompt)
    
    # 创建并行Chain
    parallel_chain = ParallelChain(chains={
        "summary": summary_chain,
        "analysis": analysis_chain,
        "translation": translation_chain
    })
    
    # 执行并行任务
    test_text = "人工智能正在改变我们的生活方式，从智能手机到自动驾驶汽车，AI技术无处不在。"
    
    start_time = time.time()
    result = parallel_chain.invoke({"text": test_text})
    end_time = time.time()
    
    print(f"原始文本: {test_text}")
    print(f"并行执行耗时: {end_time - start_time:.2f}秒")
    print("\n并行执行结果:")
    
    for task_name, task_result in result["results"].items():
        if "error" in task_result:
            print(f"{task_name}: 执行失败 - {task_result['error']}")
        else:
            print(f"{task_name}: {task_result['text']}")
    print()

def metrics_chain_example():
    """指标收集Chain示例"""
    print("=== 指标收集Chain示例 ===")
    
    # 创建LLM和基础Chain
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    prompt = PromptTemplate(
        template="请解释：{concept}",
        input_variables=["concept"]
    )
    base_chain = LLMChain(llm=llm, prompt=prompt)
    
    # 包装为带指标收集的Chain
    metrics_chain = MetricsChain(base_chain=base_chain)
    
    # 执行多个任务并收集指标
    concepts = ["机器学习", "深度学习", "神经网络", "自然语言处理"]
    
    for concept in concepts:
        result = metrics_chain.invoke({"concept": concept})
        print(f"概念: {concept}")
        print(f"解释: {result['text'][:100]}...")
        print(f"执行指标: {metrics_chain.get_metrics()}")
        print("-" * 50)
    print()

def chain_composition_example():
    """Chain组合示例"""
    print("=== Chain组合示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 创建自定义处理Chain
    preprocessing_chain = CustomChain(processing_type="lowercase")
    
    # 创建LLM处理Chain
    prompt = PromptTemplate(
        template="请分析以下文本：{processed_text}",
        input_variables=["processed_text"]
    )
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    
    # 创建后处理Chain
    postprocessing_chain = CustomChain(processing_type="uppercase")
    
    # 使用RunnableParallel进行组合
    parallel_chain = RunnableParallel({
        "preprocessed": preprocessing_chain,
        "analysis": llm_chain
    })
    
    # 测试组合Chain
    test_text = "Artificial Intelligence is Transforming the World"
    
    # 执行预处理和并行处理
    result1 = preprocessing_chain.invoke({"input_text": test_text})
    print(f"预处理结果: {result1['processed_text']}")
    
    # 执行并行处理
    result2 = parallel_chain.invoke({"input_text": test_text})
    print(f"并行处理结果:")
    print(f"  预处理: {result2['preprocessed']['processed_text']}")
    print(f"  分析: {result2['analysis']['text'][:100]}...")
    print()

async def async_chain_example():
    """异步Chain示例"""
    print("=== 异步Chain示例 ===")
    
    # 创建LLM实例
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 创建多个Chain
    chains = []
    for i in range(3):
        prompt = PromptTemplate(
            template=f"请解释概念{i+1}：{{concept}}",
            input_variables=["concept"]
        )
        chain = LLMChain(llm=llm, prompt=prompt)
        chains.append(chain)
    
    # 并行执行多个Chain
    concepts = ["机器学习", "深度学习", "神经网络"]
    
    start_time = time.time()
    
    # 创建异步任务
    tasks = [
        chain.ainvoke({"concept": concept})
        for chain, concept in zip(chains, concepts)
    ]
    
    # 等待所有任务完成
    results = await asyncio.gather(*tasks)
    
    end_time = time.time()
    
    print(f"异步并行执行耗时: {end_time - start_time:.2f}秒")
    print("执行结果:")
    
    for i, (concept, result) in enumerate(zip(concepts, results)):
        print(f"概念{i+1} ({concept}): {result['text'][:50]}...")
    print()

def chain_factory_example():
    """Chain工厂示例"""
    print("=== Chain工厂示例 ===")
    
    class ChainFactory:
        """Chain工厂类"""
        
        @staticmethod
        def create_analysis_chain(llm, analysis_type: str) -> Chain:
            """创建分析Chain"""
            templates = {
                "summary": "请总结以下内容：{text}",
                "analysis": "请分析以下内容：{text}",
                "critique": "请批判以下内容：{text}",
                "extension": "请扩展以下内容：{text}"
            }
            
            template = templates.get(analysis_type, templates["analysis"])
            prompt = PromptTemplate(template=template, input_variables=["text"])
            return LLMChain(llm=llm, prompt=prompt)
        
        @staticmethod
        def create_processing_chain(processing_type: str) -> Chain:
            """创建处理Chain"""
            return CustomChain(processing_type=processing_type)
        
        @staticmethod
        def create_resilient_chain(base_chain: Chain, max_retries: int = 3) -> Chain:
            """创建容错Chain"""
            return RetryableChain(base_chain=base_chain, max_retries=max_retries)
    
    # 使用工厂创建Chain
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 创建不同类型的分析Chain
    summary_chain = ChainFactory.create_analysis_chain(llm, "summary")
    analysis_chain = ChainFactory.create_analysis_chain(llm, "analysis")
    
    # 创建处理Chain
    uppercase_chain = ChainFactory.create_processing_chain("uppercase")
    
    # 创建容错Chain
    resilient_chain = ChainFactory.create_resilient_chain(analysis_chain, max_retries=2)
    
    # 测试工厂创建的Chain
    test_text = "人工智能技术正在快速发展"
    
    print("工厂创建的Chain测试:")
    
    # 测试分析Chain
    result1 = summary_chain.invoke({"text": test_text})
    print(f"总结Chain: {result1['text']}")
    
    # 测试处理Chain
    result2 = uppercase_chain.invoke({"input_text": test_text})
    print(f"处理Chain: {result2['processed_text']}")
    
    # 测试容错Chain
    result3 = resilient_chain.invoke({"text": test_text})
    print(f"容错Chain: {result3['text']}")
    print()

def main():
    """主函数，运行所有高级示例"""
    print("LangChain Chains 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 自定义Chain示例
        custom_chain_example()
        
        # 条件Chain示例
        conditional_chain_example()
        
        # 可重试Chain示例
        retryable_chain_example()
        
        # 并行Chain示例
        parallel_chain_example()
        
        # 指标收集Chain示例
        metrics_chain_example()
        
        # Chain组合示例
        chain_composition_example()
        
        # 异步Chain示例
        asyncio.run(async_chain_example())
        
        # Chain工厂示例
        chain_factory_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Tools 组件高级示例
演示异步工具、缓存工具、批量工具等高级功能
"""

import os
import sys
import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from langchain.tools import BaseTool
from langchain_core.callbacks import BaseCallbackHandler
import aiohttp
import requests
import pickle
from functools import lru_cache
import threading

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class AsyncAPITool(BaseTool):
    """异步API工具示例"""
    
    name: str = "async_api_call"
    description: str = "异步调用REST API"
    
    def _run(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> str:
        """同步执行（兼容性）"""
        return asyncio.run(self._arun(url, method, data))
    
    async def _arun(self, url: str, method: str = "GET", data: Optional[Dict] = None) -> str:
        """异步执行API调用"""
        try:
            async with aiohttp.ClientSession() as session:
                if method.upper() == "GET":
                    async with session.get(url) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            return f"API调用失败，状态码：{response.status}"
                
                elif method.upper() == "POST":
                    async with session.post(url, json=data) as response:
                        if response.status == 200:
                            return await response.text()
                        else:
                            return f"API调用失败，状态码：{response.status}"
                
                else:
                    return f"不支持的HTTP方法：{method}"
        
        except asyncio.TimeoutError:
            return "API调用超时"
        except Exception as e:
            return f"API调用异常：{str(e)}"

class CachedDataTool(BaseTool):
    """带缓存的数据工具"""
    
    name: str = "cached_data_query"
    description: str = "查询数据，支持缓存"
    cache_dir: str = "tool_cache"
    cache_ttl: int = 3600  # 缓存1小时
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _get_cache_key(self, query: str) -> str:
        """生成缓存键"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"{cache_key}.cache")
    
    def _load_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存加载数据"""
        cache_path = self._get_cache_path(cache_key)
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
                
                # 检查缓存是否过期
                if time.time() - cache_data['timestamp'] > self.cache_ttl:
                    os.remove(cache_path)
                    return None
                
                return cache_data['data']
        
        except Exception:
            # 缓存文件损坏，删除
            try:
                os.remove(cache_path)
            except:
                pass
            return None
    
    def _save_to_cache(self, cache_key: str, data: Any) -> None:
        """保存数据到缓存"""
        cache_path = self._get_cache_path(cache_key)
        
        try:
            cache_data = {
                'data': data,
                'timestamp': time.time()
            }
            
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
        
        except Exception as e:
            print(f"缓存保存失败: {e}")
    
    def _run(self, query: str, use_cache: bool = True) -> str:
        """执行查询（带缓存）"""
        if use_cache:
            cache_key = self._get_cache_key(query)
            cached_result = self._load_from_cache(cache_key)
            
            if cached_result is not None:
                return f"缓存结果：{cached_result}"
        
        # 缓存未命中，执行实际查询
        result = self._execute_query(query)
        
        # 保存到缓存
        if use_cache:
            self._save_to_cache(cache_key, result)
        
        return result
    
    def _execute_query(self, query: str) -> str:
        """执行实际查询逻辑"""
        # 模拟数据查询
        data_store = {
            "Python": "Python是一种高级编程语言，具有简洁的语法和丰富的库。",
            "机器学习": "机器学习是人工智能的子领域，让计算机从数据中学习。",
            "深度学习": "深度学习使用多层神经网络，在图像和NLP领域表现出色。",
            "LangChain": "LangChain是用于构建LLM应用的框架，提供了组件化的开发方式。"
        }
        
        for key in data_store:
            if key in query:
                return data_store[key]
        
        return f"未找到关于'{query}'的信息"
    
    def clear_cache(self) -> None:
        """清空缓存"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.cache'):
                    os.remove(os.path.join(self.cache_dir, filename))
        except Exception as e:
            print(f"清空缓存失败: {e}")

class BatchProcessingTool(BaseTool):
    """批量处理工具"""
    
    name: str = "batch_processor"
    description: str = "批量处理数据"
    batch_size: int = 10
    
    def _run(self, items: List[str], operation: str = "uppercase") -> str:
        """批量处理数据"""
        if not isinstance(items, list):
            return "输入必须是列表格式"
        
        results = []
        total_batches = (len(items) + self.batch_size - 1) // self.batch_size
        
        for i in range(0, len(items), self.batch_size):
            batch = items[i:i + self.batch_size]
            batch_num = i // self.batch_size + 1
            
            print(f"处理批次 {batch_num}/{total_batches}，包含 {len(batch)} 个项目")
            
            batch_results = self._process_batch(batch, operation)
            results.extend(batch_results)
            
            # 模拟处理时间
            time.sleep(0.5)
        
        return f"批量处理完成，共处理 {len(results)} 个项目"
    
    def _process_batch(self, batch: List[str], operation: str) -> List[str]:
        """处理单个批次"""
        results = []
        
        for item in batch:
            if operation == "uppercase":
                result = item.upper()
            elif operation == "lowercase":
                result = item.lower()
            elif operation == "length":
                result = f"{item} (长度: {len(item)})"
            elif operation == "hash":
                result = f"{item} (哈希: {hashlib.md5(item.encode()).hexdigest()[:8]})"
            else:
                result = f"不支持的操作: {operation}"
            
            results.append(result)
        
        return results

class RetryableTool(BaseTool):
    """可重试的工具"""
    
    name: str = "retryable_operation"
    description: str = "支持重试的操作"
    max_retries: int = 3
    retry_delay: float = 1.0
    backoff_factor: float = 2.0
    
    def _run(self, operation: str, data: Optional[str] = None) -> str:
        """带重试的执行"""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                print(f"尝试执行 '{operation}' (第 {attempt + 1} 次)")
                return self._execute_operation(operation, data)
            
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    wait_time = self.retry_delay * (self.backoff_factor ** attempt)
                    print(f"执行失败，{wait_time}秒后重试: {str(e)}")
                    time.sleep(wait_time)
                else:
                    print(f"所有重试都失败了: {str(e)}")
        
        raise last_exception
    
    def _execute_operation(self, operation: str, data: Optional[str] = None) -> str:
        """执行实际操作"""
        # 模拟随机失败
        import random
        
        if random.random() < 0.7:  # 70%的失败率
            raise Exception(f"模拟的操作失败: {operation}")
        
        if operation == "process_data":
            return f"数据处理完成: {data}"
        elif operation == "generate_report":
            return f"报告生成完成，包含数据: {data}"
        elif operation == "send_notification":
            return f"通知发送成功: {data}"
        else:
            return f"操作 '{operation}' 执行完成，数据: {data}"

class ToolCallbackHandler(BaseCallbackHandler):
    """工具回调处理器"""
    
    def __init__(self):
        self.events = []
        self.start_time = None
    
    def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> Any:
        """工具开始回调"""
        self.start_time = time.time()
        event = {
            "type": "tool_start",
            "tool": serialized.get("name", "unknown"),
            "input": input_str,
            "timestamp": self.start_time
        }
        self.events.append(event)
        print(f"工具开始: {event['tool']} - {input_str[:50]}...")
    
    def on_tool_end(self, output: str, **kwargs) -> Any:
        """工具结束回调"""
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        event = {
            "type": "tool_end",
            "output": output[:100],  # 限制输出长度
            "duration": duration,
            "timestamp": end_time
        }
        self.events.append(event)
        print(f"工具结束: 耗时 {duration:.2f}s - {output[:50]}...")
    
    def on_tool_error(self, error: Exception, **kwargs) -> Any:
        """工具错误回调"""
        event = {
            "type": "tool_error",
            "error": str(error),
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"工具错误: {str(error)}")
    
    def get_events(self) -> List[Dict[str, Any]]:
        """获取事件历史"""
        return self.events
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        tool_starts = [e for e in self.events if e["type"] == "tool_start"]
        tool_ends = [e for e in self.events if e["type"] == "tool_end"]
        tool_errors = [e for e in self.events if e["type"] == "tool_error"]
        
        total_duration = sum(e.get("duration", 0) for e in tool_ends)
        avg_duration = total_duration / len(tool_ends) if tool_ends else 0
        
        return {
            "total_calls": len(tool_starts),
            "successful_calls": len(tool_ends),
            "failed_calls": len(tool_errors),
            "total_duration": total_duration,
            "average_duration": avg_duration,
            "success_rate": len(tool_ends) / len(tool_starts) if tool_starts else 0
        }

class MultiModalTool(BaseTool):
    """多模态工具示例"""
    
    name: str = "multimodal_processor"
    description: str = "处理多模态数据"
    
    def _run(self, text: Optional[str] = None, 
             image_path: Optional[str] = None,
             processing_type: str = "extract_features") -> str:
        """处理多模态数据"""
        results = []
        
        if text:
            text_result = self._process_text(text, processing_type)
            results.append(f"文本处理: {text_result}")
        
        if image_path:
            image_result = self._process_image(image_path, processing_type)
            results.append(f"图像处理: {image_result}")
        
        if not results:
            return "未提供有效的输入数据"
        
        return " | ".join(results)
    
    def _process_text(self, text: str, processing_type: str) -> str:
        """处理文本"""
        if processing_type == "extract_features":
            words = len(text.split())
            chars = len(text)
            return f"提取特征: {words}词, {chars}字符"
        elif processing_type == "sentiment":
            # 简化的情感分析
            positive_words = ["好", "棒", "优秀", "喜欢"]
            negative_words = ["差", "坏", "糟糕", "失望"]
            
            pos_count = sum(1 for word in positive_words if word in text)
            neg_count = sum(1 for word in negative_words if word in text)
            
            if pos_count > neg_count:
                return "情感分析: 积极"
            elif neg_count > pos_count:
                return "情感分析: 消极"
            else:
                return "情感分析: 中性"
        else:
            return f"文本处理: {text[:50]}..."
    
    def _process_image(self, image_path: str, processing_type: str) -> str:
        """处理图像"""
        # 模拟图像处理
        if not os.path.exists(image_path):
            return f"图像文件不存在: {image_path}"
        
        if processing_type == "extract_features":
            file_size = os.path.getsize(image_path)
            return f"图像特征: 文件大小 {file_size} bytes"
        elif processing_type == "detect_objects":
            return "物体检测: 检测到模拟对象"
        else:
            return f"图像处理: {os.path.basename(image_path)}"

class StreamingTool(BaseTool):
    """流式输出工具"""
    
    name: str = "streaming_generator"
    description: str = "生成流式内容"
    
    def _run(self, prompt: str, max_tokens: int = 100) -> str:
        """同步执行（返回完整结果）"""
        result = ""
        for chunk in self._generate_chunks(prompt, max_tokens):
            result += chunk
            time.sleep(0.1)  # 模拟流式延迟
        return result
    
    def stream_generate(self, prompt: str, max_tokens: int = 100):
        """生成流式内容"""
        for chunk in self._generate_chunks(prompt, max_tokens):
            yield chunk
            time.sleep(0.1)
    
    def _generate_chunks(self, prompt: str, max_tokens: int) -> List[str]:
        """生成内容块"""
        # 模拟流式生成
        full_content = f"基于提示'{prompt}'生成的内容。这是一个示例响应，包含了详细的解释和相关信息。"
        
        # 分割为块
        chunk_size = 20
        chunks = [full_content[i:i+chunk_size] for i in range(0, len(full_content), chunk_size)]
        
        # 限制块数量
        return chunks[:max_tokens // chunk_size]

def async_tool_example():
    """异步工具示例"""
    print("=== 异步工具示例 ===")
    
    # 创建异步工具
    async_tool = AsyncAPITool()
    
    # 测试异步API调用
    test_calls = [
        {"url": "https://httpbin.org/get", "method": "GET"},
        {"url": "https://httpbin.org/post", "method": "POST", "data": {"key": "value"}},
        {"url": "https://httpbin.org/invalid", "method": "GET"}
    ]
    
    async def test_async_tools():
        tasks = []
        
        for call_data in test_calls:
            task = async_tool._arun(**call_data)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for i, result in enumerate(results):
            print(f"API调用 {i+1}: {result[:100]}...")
    
    # 运行异步测试
    asyncio.run(test_async_tools())
    print()

def cached_tool_example():
    """缓存工具示例"""
    print("=== 缓存工具示例 ===")
    
    # 创建缓存工具
    cached_tool = CachedDataTool()
    
    # 测试查询
    queries = [
        "Python编程语言",
        "机器学习算法",
        "Python编程语言",  # 重复查询，应该使用缓存
        "深度学习框架",
        "机器学习算法"   # 重复查询，应该使用缓存
    ]
    
    for query in queries:
        print(f"查询: {query}")
        result = cached_tool._run(query, use_cache=True)
        print(f"结果: {result}")
        print()
    
    # 显示缓存统计
    print("缓存统计:")
    cache_files = [f for f in os.listdir(cached_tool.cache_dir) if f.endswith('.cache')]
    print(f"缓存文件数: {len(cache_files)}")
    
    # 清空缓存
    cached_tool.clear_cache()
    print("缓存已清空")
    print()

def batch_tool_example():
    """批量处理工具示例"""
    print("=== 批量处理工具示例 ===")
    
    # 创建批量处理工具
    batch_tool = BatchProcessingTool(batch_size=3)
    
    # 测试数据
    test_data = [
        "Apple", "Banana", "Cherry", "Date", "Elderberry", "Fig", "Grape"
    ]
    
    # 测试不同操作
    operations = ["uppercase", "lowercase", "length", "hash"]
    
    for operation in operations:
        print(f"\n批量操作: {operation}")
        result = batch_tool._run(test_data, operation)
        print(f"结果: {result}")

def retryable_tool_example():
    """可重试工具示例"""
    print("=== 可重试工具示例 ===")
    
    # 创建可重试工具
    retry_tool = RetryableTool(max_retries=3, retry_delay=0.5)
    
    # 测试操作
    operations = [
        {"operation": "process_data", "data": "sample_data.txt"},
        {"operation": "generate_report", "data": "monthly_stats.csv"},
        {"operation": "send_notification", "data": "alert_message"},
        {"operation": "invalid_operation", "data": "test"}  # 这个会失败
    ]
    
    for op in operations:
        print(f"\n执行操作: {op['operation']}")
        try:
            result = retry_tool._run(**op)
            print(f"成功: {result}")
        except Exception as e:
            print(f"最终失败: {e}")

def tool_with_callbacks_example():
    """带回调的工具示例"""
    print("=== 带回调的工具示例 ===")
    
    # 创建回调处理器
    callback_handler = ToolCallbackHandler()
    
    # 创建测试工具
    def test_tool_func(input_data: str) -> str:
        time.sleep(1)  # 模拟处理时间
        return f"处理结果: {input_data.upper()}"
    
    test_tool = Tool(
        name="test_tool",
        description="测试工具",
        func=test_tool_func
    )
    
    # 模拟工具执行
    test_inputs = ["hello world", "langchain tools", "callback example"]
    
    for i, input_data in enumerate(test_inputs):
        print(f"\n执行 {i+1}: {input_data}")
        
        # 模拟工具开始
        callback_handler.on_tool_start(
            {"name": test_tool.name},
            input_data
        )
        
        try:
            # 模拟工具执行
            result = test_tool_func(input_data)
            
            # 模拟工具结束
            callback_handler.on_tool_end(result)
            
            print(f"结果: {result}")
            
        except Exception as e:
            # 模拟工具错误
            callback_handler.on_tool_error(e)
            print(f"错误: {e}")
    
    # 显示回调统计
    print("\n回调统计:")
    stats = callback_handler.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")

def multimodal_tool_example():
    """多模态工具示例"""
    print("=== 多模态工具示例 ===")
    
    # 创建多模态工具
    multimodal_tool = MultiModalTool()
    
    # 创建测试图像文件
    test_image_path = "test_image.txt"  # 创建文本文件模拟图像
    with open(test_image_path, 'w') as f:
        f.write("模拟的图像数据")
    
    try:
        # 测试不同输入组合
        test_cases = [
            {"text": "这是一个很好的产品", "processing_type": "sentiment"},
            {"image_path": test_image_path, "processing_type": "extract_features"},
            {"text": "产品描述", "image_path": test_image_path, "processing_type": "extract_features"}
        ]
        
        for i, case in enumerate(test_cases, 1):
            print(f"\n测试用例 {i}:")
            for key, value in case.items():
                print(f"  {key}: {value}")
            
            result = multimodal_tool._run(**case)
            print(f"结果: {result}")
    
    finally:
        # 清理测试文件
        if os.path.exists(test_image_path):
            os.remove(test_image_path)

def streaming_tool_example():
    """流式工具示例"""
    print("=== 流式工具示例 ===")
    
    # 创建流式工具
    streaming_tool = StreamingTool()
    
    # 测试提示
    prompt = "请介绍LangChain框架"
    
    print(f"提示: {prompt}")
    print("流式生成:")
    
    # 流式输出
    for chunk in streaming_tool.stream_generate(prompt, max_tokens=50):
        print(chunk, end='', flush=True)
    
    print("\n\n同步完整结果:")
    full_result = streaming_tool._run(prompt, max_tokens=50)
    print(full_result)

def main():
    """主函数，运行所有高级示例"""
    print("LangChain Tools 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 异步工具示例
        async_tool_example()
        
        # 缓存工具示例
        cached_tool_example()
        
        # 批量工具示例
        batch_tool_example()
        
        # 重试工具示例
        retryable_tool_example()
        
        # 回调示例
        tool_with_callbacks_example()
        
        # 多模态工具示例
        multimodal_tool_example()
        
        # 流式工具示例
        streaming_tool_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Callbacks 组件高级示例
演示异步Callbacks、自定义高级Callbacks、性能监控等高级功能
"""

import os
import sys
import asyncio
import time
import json
import threading
from typing import Dict, List, Any, Optional, Callable
from abc import ABC, abstractmethod
from langchain_core.callbacks import AsyncCallbackHandler, BaseCallbackHandler
from langchain_core.outputs import LLMResult
from langchain_openai import OpenAI, ChatOpenAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import aiofiles
import aiohttp
from collections import defaultdict, deque
import queue

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class AsyncMetricsCallbackHandler(AsyncCallbackHandler):
    """异步指标收集Callback Handler"""
    
    def __init__(self, output_file: str = "async_metrics.json"):
        super().__init__()
        self.output_file = output_file
        self.metrics = {
            "llm_calls": [],
            "chain_executions": [],
            "errors": []
        }
        self._lock = asyncio.Lock()
        self.start_times = {}
    
    async def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """异步处理LLM开始事件"""
        call_id = id(prompts[0]) if prompts else id(serialized)
        self.start_times[call_id] = time.time()
        
        metric = {
            "event": "llm_start",
            "model": serialized.get("name", "unknown"),
            "prompt_count": len(prompts),
            "total_prompt_length": sum(len(p) for p in prompts),
            "timestamp": self.start_times[call_id]
        }
        
        async with self._lock:
            self.metrics["llm_calls"].append(metric)
        
        print(f"[异步Callback] LLM开始 - 模型: {metric['model']}, 提示数: {metric['prompt_count']}")
    
    async def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """异步处理LLM结束事件"""
        # 查找对应的开始时间
        prompt = response.generations[0][0].text if response.generations else ""
        call_id = id(prompt)
        
        start_time = self.start_times.get(call_id, time.time())
        duration = time.time() - start_time
        
        if call_id in self.start_times:
            del self.start_times[call_id]
        
        metric = {
            "event": "llm_end",
            "duration": duration,
            "token_usage": response.llm_output.get("token_usage", {}),
            "generation_count": len(response.generations),
            "output_length": len(prompt),
            "timestamp": time.time()
        }
        
        async with self._lock:
            if self.metrics["llm_calls"]:
                # 找到对应的开始事件并添加结束信息
                for i, call in enumerate(reversed(self.metrics["llm_calls"])):
                    if call["event"] == "llm_start":
                        self.metrics["llm_calls"][-(i+1)].update(metric)
                        break
        
        await self._save_metrics_async()
        print(f"[异步Callback] LLM结束 - 耗时: {duration:.2f}s")
    
    async def on_chain_start(
        self, 
        serialized: Dict[str, Any], 
        inputs: Dict[str, Any], 
        **kwargs: Any
    ) -> None:
        """异步处理Chain开始事件"""
        execution_id = id(inputs)
        self.start_times[execution_id] = time.time()
        
        metric = {
            "event": "chain_start",
            "chain_type": serialized.get("name", "unknown"),
            "input_keys": list(inputs.keys()),
            "input_data": {k: str(v)[:50] + "..." if len(str(v)) > 50 else str(v) 
                           for k, v in inputs.items()},
            "timestamp": self.start_times[execution_id]
        }
        
        async with self._lock:
            self.metrics["chain_executions"].append(metric)
        
        print(f"[异步Callback] Chain开始 - 类型: {metric['chain_type']}")
    
    async def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """异步处理Chain结束事件"""
        execution_id = id(outputs)
        start_time = self.start_times.get(execution_id, time.time())
        duration = time.time() - start_time
        
        if execution_id in self.start_times:
            del self.start_times[execution_id]
        
        metric = {
            "event": "chain_end",
            "duration": duration,
            "output_keys": list(outputs.keys()),
            "output_data": {k: str(v)[:50] + "..." if len(str(v)) > 50 else str(v)
                           for k, v in outputs.items()},
            "timestamp": time.time()
        }
        
        async with self._lock:
            if self.metrics["chain_executions"]:
                # 找到对应的开始事件并添加结束信息
                for i, execution in enumerate(reversed(self.metrics["chain_executions"])):
                    if execution["event"] == "chain_start":
                        self.metrics["chain_executions"][-(i+1)].update(metric)
                        break
        
        await self._save_metrics_async()
        print(f"[异步Callback] Chain结束 - 耗时: {duration:.2f}s")
    
    async def on_error(
        self, 
        error: Exception, 
        **kwargs: Any
    ) -> None:
        """异步处理错误事件"""
        metric = {
            "event": "error",
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time()
        }
        
        async with self._lock:
            self.metrics["errors"].append(metric)
        
        await self._save_metrics_async()
        print(f"[异步Callback] 错误 - {metric['error_type']}: {metric['error_message']}")
    
    async def _save_metrics_async(self):
        """异步保存指标到文件"""
        try:
            async with aiofiles.open(self.output_file, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(self.metrics, indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"[异步Callback] 保存指标失败: {e}")
    
    async def get_metrics_async(self) -> Dict[str, Any]:
        """异步获取指标"""
        async with self._lock:
            return self.metrics.copy()

class EventFilterCallbackHandler(BaseCallbackHandler):
    """事件过滤Callback Handler"""
    
    def __init__(self, include_events: List[str] = None, exclude_events: List[str] = None):
        super().__init__()
        self.include_events = include_events or []
        self.exclude_events = exclude_events or []
        self.filtered_events = []
    
    def _should_process_event(self, event_name: str) -> bool:
        """判断是否应该处理事件"""
        if self.include_events and event_name not in self.include_events:
            return False
        
        if event_name in self.exclude_events:
            return False
        
        return True
    
    def _record_event(self, event_name: str, data: Dict[str, Any]):
        """记录事件"""
        if self._should_process_event(event_name):
            event = {
                "event": event_name,
                "timestamp": time.time(),
                "data": data
            }
            self.filtered_events.append(event)
            print(f"[过滤Callback] 记录事件: {event_name}")
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """处理LLM开始事件"""
        self._record_event("llm_start", {
            "model": serialized.get("name"),
            "prompt_count": len(prompts)
        })
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """处理LLM结束事件"""
        self._record_event("llm_end", {
            "token_usage": response.llm_output.get("token_usage", {}),
            "generation_count": len(response.generations)
        })
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """处理Chain开始事件"""
        self._record_event("chain_start", {
            "chain_type": serialized.get("name"),
            "input_keys": list(inputs.keys())
        })
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """处理Chain结束事件"""
        self._record_event("chain_end", {
            "output_keys": list(outputs.keys())
        })
    
    def get_filtered_events(self) -> List[Dict[str, Any]]:
        """获取过滤后的事件"""
        return self.filtered_events.copy()
    
    def get_event_statistics(self) -> Dict[str, Any]:
        """获取事件统计"""
        event_counts = defaultdict(int)
        
        for event in self.filtered_events:
            event_counts[event["event"]] += 1
        
        return {
            "total_events": len(self.filtered_events),
            "event_counts": dict(event_counts),
            "include_events": self.include_events,
            "exclude_events": self.exclude_events
        }

class PerformanceMonitorCallbackHandler(BaseCallbackHandler):
    """性能监控Callback Handler"""
    
    def __init__(self, sampling_rate: float = 1.0, max_memory_mb: int = 100):
        super().__init__()
        self.sampling_rate = sampling_rate  # 采样率
        self.max_memory_mb = max_memory_mb
        self.performance_data = deque(maxlen=10000)  # 限制内存使用
        self.memory_usage = 0
        self.start_times = {}
        self._lock = threading.Lock()
    
    def _should_sample(self) -> bool:
        """判断是否应该采样"""
        import random
        return random.random() < self.sampling_rate
    
    def _estimate_memory_usage(self, data: Dict[str, Any]) -> int:
        """估算数据内存使用量"""
        import sys
        return sys.getsizeof(data)
    
    def _add_performance_data(self, data: Dict[str, Any]):
        """添加性能数据"""
        with self._lock:
            # 检查内存限制
            data_size = self._estimate_memory_usage(data)
            
            # 如果内存使用超过限制，移除旧数据
            while (self.memory_usage + data_size > self.max_memory_mb * 1024 * 1024 
                   and self.performance_data):
                old_data = self.performance_data.popleft()
                self.memory_usage -= self._estimate_memory_usage(old_data)
            
            self.performance_data.append(data)
            self.memory_usage += data_size
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """监控LLM开始性能"""
        if not self._should_sample():
            return
        
        start_time = time.time()
        call_id = id(prompts[0]) if prompts else id(serialized)
        self.start_times[call_id] = start_time
        
        data = {
            "event": "llm_start",
            "timestamp": start_time,
            "model": serialized.get("name", "unknown"),
            "prompt_length": sum(len(p) for p in prompts)
        }
        
        self._add_performance_data(data)
        print(f"[性能监控] LLM开始 - 模型: {data['model']}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """监控LLM结束性能"""
        if not self._should_sample():
            return
        
        end_time = time.time()
        
        # 查找对应的开始时间
        prompt = response.generations[0][0].text if response.generations else ""
        call_id = id(prompt)
        start_time = self.start_times.get(call_id, end_time)
        
        if call_id in self.start_times:
            del self.start_times[call_id]
        
        duration = end_time - start_time
        tokens_per_second = 0
        token_usage = response.llm_output.get("token_usage", {})
        
        if duration > 0 and "total_tokens" in token_usage:
            tokens_per_second = token_usage["total_tokens"] / duration
        
        data = {
            "event": "llm_end",
            "timestamp": end_time,
            "duration": duration,
            "tokens_used": token_usage.get("total_tokens", 0),
            "tokens_per_second": tokens_per_second
        }
        
        self._add_performance_data(data)
        print(f"[性能监控] LLM结束 - 耗时: {duration:.2f}s, 速率: {tokens_per_second:.2f} tokens/s")
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """监控Chain开始性能"""
        if not self._should_sample():
            return
        
        start_time = time.time()
        execution_id = id(inputs)
        self.start_times[execution_id] = start_time
        
        data = {
            "event": "chain_start",
            "timestamp": start_time,
            "chain_type": serialized.get("name", "unknown"),
            "input_size": len(str(inputs))
        }
        
        self._add_performance_data(data)
        print(f"[性能监控] Chain开始 - 类型: {data['chain_type']}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """监控Chain结束性能"""
        if not self._should_sample():
            return
        
        end_time = time.time()
        execution_id = id(outputs)
        start_time = self.start_times.get(execution_id, end_time)
        
        if execution_id in self.start_times:
            del self.start_times[execution_id]
        
        duration = end_time - start_time
        throughput = 0
        
        if duration > 0:
            throughput = len(str(outputs)) / duration
        
        data = {
            "event": "chain_end",
            "timestamp": end_time,
            "duration": duration,
            "output_size": len(str(outputs)),
            "throughput": throughput
        }
        
        self._add_performance_data(data)
        print(f"[性能监控] Chain结束 - 耗时: {duration:.2f}s, 吞吐量: {throughput:.2f} chars/s")
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """获取性能摘要"""
        if not self.performance_data:
            return {"message": "无性能数据"}
        
        # 分析LLM性能
        llm_events = [e for e in self.performance_data if "llm_end" in e["event"]]
        llm_durations = [e.get("duration", 0) for e in llm_events]
        llm_throughputs = [e.get("tokens_per_second", 0) for e in llm_events]
        
        # 分析Chain性能
        chain_events = [e for e in self.performance_data if "chain_end" in e["event"]]
        chain_durations = [e.get("duration", 0) for e in chain_events]
        
        summary = {
            "total_samples": len(self.performance_data),
            "memory_usage_mb": self.memory_usage / (1024 * 1024),
            "sampling_rate": self.sampling_rate,
            "llm_performance": {
                "total_calls": len(llm_events),
                "avg_duration": sum(llm_durations) / len(llm_durations) if llm_durations else 0,
                "max_duration": max(llm_durations) if llm_durations else 0,
                "avg_tokens_per_second": sum(llm_throughputs) / len(llm_throughputs) if llm_throughputs else 0
            },
            "chain_performance": {
                "total_executions": len(chain_events),
                "avg_duration": sum(chain_durations) / len(chain_durations) if chain_durations else 0,
                "max_duration": max(chain_durations) if chain_durations else 0
            }
        }
        
        return summary

class SecurityCallbackHandler(BaseCallbackHandler):
    """安全检查Callback Handler"""
    
    def __init__(self, max_prompt_length: int = 10000, blocked_words: List[str] = None):
        super().__init__()
        self.max_prompt_length = max_prompt_length
        self.blocked_words = blocked_words or [
            "password", "token", "secret", "key", "credential"
        ]
        self.security_violations = []
        self._lock = threading.Lock()
    
    def _check_prompt_security(self, prompts: List[str]) -> Optional[str]:
        """检查提示的安全性"""
        for prompt in prompts:
            # 检查长度限制
            if len(prompt) > self.max_prompt_length:
                return f"提示长度超过限制 ({len(prompt)} > {self.max_prompt_length})"
            
            # 检查敏感词汇
            prompt_lower = prompt.lower()
            for word in self.blocked_words:
                if word in prompt_lower:
                    return f"提示包含敏感词汇: {word}"
        
        return None
    
    def _check_output_security(self, output: str) -> Optional[str]:
        """检查输出的安全性"""
        if not output:
            return None
        
        # 检查是否包含可能泄露的信息
        sensitive_patterns = [
            "api_key", "secret", "password", "token"
        ]
        
        output_lower = output.lower()
        for pattern in sensitive_patterns:
            if pattern in output_lower:
                return f"输出可能包含敏感信息: {pattern}"
        
        return None
    
    def _record_security_violation(self, violation_type: str, details: str, context: Dict[str, Any]):
        """记录安全违规"""
        with self._lock:
            violation = {
                "timestamp": time.time(),
                "violation_type": violation_type,
                "details": details,
                "context": context
            }
            self.security_violations.append(violation)
        
        print(f"[安全检查] {violation_type}: {details}")
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """检查LLM开始时的安全性"""
        security_issue = self._check_prompt_security(prompts)
        
        if security_issue:
            self._record_security_violation(
                "prompt_security",
                security_issue,
                {"model": serialized.get("name"), "prompts": prompts}
            )
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """检查LLM结束时的安全性"""
        if response.generations:
            for generation in response.generations:
                if generation and len(generation) > 0:
                    output = generation[0].text
                    security_issue = self._check_output_security(output)
                    
                    if security_issue:
                        self._record_security_violation(
                            "output_security",
                            security_issue,
                            {"output_length": len(output)}
                        )
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """检查Chain开始时的安全性"""
        # 检查输入数据的安全性
        for key, value in inputs.items():
            if isinstance(value, str):
                security_issue = self._check_prompt_security([value])
                if security_issue:
                    self._record_security_violation(
                        "input_security",
                        f"输入 '{key}' 存在安全问题: {security_issue}",
                        {"chain_type": serialized.get("name")}
                    )
    
    def get_security_report(self) -> Dict[str, Any]:
        """获取安全报告"""
        violation_types = defaultdict(int)
        
        for violation in self.security_violations:
            violation_types[violation["violation_type"]] += 1
        
        return {
            "total_violations": len(self.security_violations),
            "violation_types": dict(violation_types),
            "blocked_words": self.blocked_words,
            "max_prompt_length": self.max_prompt_length,
            "recent_violations": self.security_violations[-10:]  # 最近10个违规
        }

class BatchProcessingCallbackHandler(BaseCallbackHandler):
    """批量处理Callback Handler"""
    
    def __init__(self, batch_size: int = 100, flush_interval: float = 5.0):
        super().__init__()
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.event_batch = []
        self.last_flush = time.time()
        self._lock = threading.Lock()
    
    def _add_to_batch(self, event_data: Dict[str, Any]):
        """添加事件到批次"""
        with self._lock:
            self.event_batch.append(event_data)
            
            # 检查是否需要刷新
            current_time = time.time()
            if (len(self.event_batch) >= self.batch_size or 
                current_time - self.last_flush >= self.flush_interval):
                self._flush_batch()
                self.last_flush = current_time
    
    def _flush_batch(self):
        """刷新批次到存储"""
        if not self.event_batch:
            return
        
        try:
            # 这里可以实现具体的批量存储逻辑
            # 例如：写入数据库、发送到监控系统等
            batch_data = {
                "batch_size": len(self.event_batch),
                "timestamp": time.time(),
                "events": self.event_batch.copy()
            }
            
            # 模拟批量处理
            print(f"[批量处理] 刷新批次 - 事件数: {len(self.event_batch)}")
            
            # 保存到文件
            filename = f"batch_events_{int(time.time())}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(batch_data, f, indent=2, ensure_ascii=False)
            
            # 清空批次
            self.event_batch.clear()
            
        except Exception as e:
            print(f"[批量处理] 批次刷新失败: {e}")
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """批量处理LLM开始事件"""
        event_data = {
            "event": "llm_start",
            "timestamp": time.time(),
            "model": serialized.get("name", "unknown"),
            "prompt_count": len(prompts)
        }
        
        self._add_to_batch(event_data)
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """批量处理LLM结束事件"""
        event_data = {
            "event": "llm_end",
            "timestamp": time.time(),
            "token_usage": response.llm_output.get("token_usage", {}),
            "generation_count": len(response.generations)
        }
        
        self._add_to_batch(event_data)
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """批量处理Chain开始事件"""
        event_data = {
            "event": "chain_start",
            "timestamp": time.time(),
            "chain_type": serialized.get("name", "unknown"),
            "input_keys": list(inputs.keys())
        }
        
        self._add_to_batch(event_data)
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """批量处理Chain结束事件"""
        event_data = {
            "event": "chain_end",
            "timestamp": time.time(),
            "output_keys": list(outputs.keys())
        }
        
        self._add_to_batch(event_data)
    
    def force_flush(self):
        """强制刷新批次"""
        with self._lock:
            self._flush_batch()
    
    def get_batch_status(self) -> Dict[str, Any]:
        """获取批次状态"""
        with self._lock:
            return {
                "current_batch_size": len(self.event_batch),
                "max_batch_size": self.batch_size,
                "last_flush": self.last_flush,
                "time_since_last_flush": time.time() - self.last_flush
            }

async def async_callback_example():
    """异步Callback示例"""
    print("=== 异步Callback示例 ===")
    
    # 创建异步指标处理器
    async_handler = AsyncMetricsCallbackHandler()
    
    # 创建LLM
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.7,
        callbacks=[async_handler]
    )
    
    # 测试异步回调
    prompts = [
        "请解释什么是机器学习。",
        "请介绍深度学习的基本概念。",
        "请说明人工智能的主要应用领域。"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n测试 {i}: {prompt}")
        
        # 异步调用LLM
        response = await llm.agenerate([prompt])
        print(f"响应 {i}: {response.generations[0][0].text[:50]}...")
    
    # 获取异步指标
    metrics = await async_handler.get_metrics_async()
    print(f"\n异步指标摘要:")
    print(f"LLM调用数: {len(metrics['llm_calls'])}")
    print(f"Chain执行数: {len(metrics['chain_executions'])}")
    print(f"错误数: {len(metrics['errors'])}")

def event_filter_callback_example():
    """事件过滤Callback示例"""
    print("=== 事件过滤Callback示例 ===")
    
    # 创建只包含LLM事件的过滤器
    llm_filter = EventFilterCallbackHandler(include_events=["llm_start", "llm_end"])
    
    # 创建排除LLM事件的过滤器
    chain_filter = EventFilterCallbackHandler(exclude_events=["llm_start", "llm_end"])
    
    # 创建LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 测试LLM过滤器
    print("测试LLM事件过滤器:")
    response = llm.invoke("请介绍LangChain框架。", callbacks=[llm_filter])
    print(f"过滤的事件数: {len(llm_filter.get_filtered_events())}")
    
    # 测试Chain过滤器
    print("\n测试Chain事件过滤器:")
    chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(template="{input}", input_variables=["input"])
    )
    
    result = chain.invoke({"input": "请介绍LangChain框架。"}, callbacks=[chain_filter])
    print(f"过滤的事件数: {len(chain_filter.get_filtered_events())}")
    
    # 显示过滤统计
    print(f"\nLLM过滤器统计: {llm_filter.get_event_statistics()}")
    print(f"Chain过滤器统计: {chain_filter.get_event_statistics()}")

def performance_monitor_callback_example():
    """性能监控Callback示例"""
    print("=== 性能监控Callback示例 ===")
    
    # 创建性能监控处理器（10%采样率）
    perf_monitor = PerformanceMonitorCallbackHandler(sampling_rate=0.1)
    
    # 创建LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 执行多个调用来测试性能监控
    print("执行多个LLM调用以测试性能监控...")
    
    for i in range(5):
        prompt = f"这是第{i+1}次调用，请简要回答：什么是人工智能？"
        response = llm.invoke(prompt, callbacks=[perf_monitor])
        print(f"调用 {i+1} 完成")
    
    # 获取性能摘要
    summary = perf_monitor.get_performance_summary()
    print(f"\n性能监控摘要:")
    print(json.dumps(summary, indent=2, ensure_ascii=False))

def security_callback_example():
    """安全检查Callback示例"""
    print("=== 安全检查Callback示例 ===")
    
    # 创建安全检查处理器
    security_handler = SecurityCallbackHandler(
        max_prompt_length=50,  # 设置较小的限制用于演示
        blocked_words=["敏感", "密码", "secret"]
    )
    
    # 创建LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 测试正常提示
    print("测试正常提示:")
    response1 = llm.invoke("请介绍机器学习。", callbacks=[security_handler])
    print(f"响应1: {response1[:50]}...")
    
    # 测试过长的提示
    print("\n测试过长的提示:")
    long_prompt = "请详细解释" + "很长的内容。" * 10
    response2 = llm.invoke(long_prompt, callbacks=[security_handler])
    print(f"响应2: {response2[:50]}...")
    
    # 测试包含敏感词汇的提示
    print("\n测试包含敏感词汇的提示:")
    sensitive_prompt = "请告诉我我的密码是什么"
    response3 = llm.invoke(sensitive_prompt, callbacks=[security_handler])
    print(f"响应3: {response3[:50]}...")
    
    # 获取安全报告
    security_report = security_handler.get_security_report()
    print(f"\n安全报告:")
    print(json.dumps(security_report, indent=2, ensure_ascii=False))

def batch_processing_callback_example():
    """批量处理Callback示例"""
    print("=== 批量处理Callback示例 ===")
    
    # 创建批量处理器（小批次用于演示）
    batch_handler = BatchProcessingCallbackHandler(batch_size=3, flush_interval=2.0)
    
    # 创建LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 执行多个调用以生成批量事件
    print("执行多个调用以生成批量事件...")
    
    for i in range(8):
        prompt = f"请回答问题{i+1}: 什么是Python？"
        response = llm.invoke(prompt, callbacks=[batch_handler])
        print(f"调用 {i+1} 完成")
    
    # 检查批次状态
    batch_status = batch_handler.get_batch_status()
    print(f"\n批次状态:")
    print(json.dumps(batch_status, indent=2, ensure_ascii=False))
    
    # 强制刷新剩余事件
    batch_handler.force_flush()
    print("\n强制刷新完成")

class CustomEventCallbackHandler(BaseCallbackHandler):
    """自定义事件Callback Handler"""
    
    def __init__(self):
        super().__init__()
        self.custom_events = []
        self.event_processors = {
            "llm_start": self._process_llm_start,
            "llm_end": self._process_llm_end,
            "chain_start": self._process_chain_start,
            "chain_end": self._process_chain_end
        }
    
    def _process_llm_start(self, event_data: Dict[str, Any]):
        """处理LLM开始事件的自定义逻辑"""
        model = event_data.get("model", "unknown")
        print(f"[自定义处理] LLM {model} 开始工作")
        
        # 添加自定义分析
        if "gpt-4" in model.lower():
            event_data["performance_tier"] = "high"
        elif "gpt-3.5" in model.lower():
            event_data["performance_tier"] = "medium"
        else:
            event_data["performance_tier"] = "unknown"
    
    def _process_llm_end(self, event_data: Dict[str, Any]):
        """处理LLM结束事件的自定义逻辑"""
        duration = event_data.get("duration", 0)
        print(f"[自定义处理] LLM 耗时 {duration:.2f}s")
        
        # 添加性能评级
        if duration < 1.0:
            event_data["performance_rating"] = "excellent"
        elif duration < 3.0:
            event_data["performance_rating"] = "good"
        elif duration < 5.0:
            event_data["performance_rating"] = "fair"
        else:
            event_data["performance_rating"] = "poor"
    
    def _process_chain_start(self, event_data: Dict[str, Any]):
        """处理Chain开始事件的自定义逻辑"""
        chain_type = event_data.get("chain_type", "unknown")
        print(f"[自定义处理] Chain {chain_type} 开始执行")
        
        # 添加复杂度分析
        input_size = event_data.get("input_size", 0)
        if input_size < 100:
            event_data["complexity"] = "simple"
        elif input_size < 500:
            event_data["complexity"] = "medium"
        else:
            event_data["complexity"] = "complex"
    
    def _process_chain_end(self, event_data: Dict[str, Any]):
        """处理Chain结束事件的自定义逻辑"""
        duration = event_data.get("duration", 0)
        print(f"[自定义处理] Chain 耗时 {duration:.2f}s")
        
        # 添加效率评估
        output_size = event_data.get("output_size", 1)
        efficiency = output_size / duration if duration > 0 else 0
        event_data["efficiency_score"] = efficiency
    
    def _add_custom_event(self, event_type: str, event_data: Dict[str, Any]):
        """添加自定义事件"""
        # 调用相应的处理器
        processor = self.event_processors.get(event_type)
        if processor:
            processor(event_data)
        
        # 添加基础事件信息
        event_data["event"] = event_type
        event_data["timestamp"] = time.time()
        self.custom_events.append(event_data)
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs: Any) -> None:
        """自定义LLM开始处理"""
        event_data = {
            "model": serialized.get("name", "unknown"),
            "prompt_count": len(prompts)
        }
        self._add_custom_event("llm_start", event_data)
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """自定义LLM结束处理"""
        # 这里需要计算持续时间，简化示例
        event_data = {
            "duration": 2.5,  # 模拟值
            "token_usage": response.llm_output.get("token_usage", {}),
            "generation_count": len(response.generations)
        }
        self._add_custom_event("llm_end", event_data)
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs: Any) -> None:
        """自定义Chain开始处理"""
        event_data = {
            "chain_type": serialized.get("name", "unknown"),
            "input_keys": list(inputs.keys()),
            "input_size": len(str(inputs))
        }
        self._add_custom_event("chain_start", event_data)
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """自定义Chain结束处理"""
        # 这里需要计算持续时间，简化示例
        event_data = {
            "duration": 1.8,  # 模拟值
            "output_keys": list(outputs.keys()),
            "output_size": len(str(outputs))
        }
        self._add_custom_event("chain_end", event_data)
    
    def get_custom_events(self) -> List[Dict[str, Any]]:
        """获取自定义事件"""
        return self.custom_events.copy()
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """获取性能分析"""
        llm_events = [e for e in self.custom_events if e["event"].startswith("llm")]
        chain_events = [e for e in self.custom_events if e["event"].startswith("chain")]
        
        # 分析LLM性能
        llm_performance = {}
        if llm_events:
            performance_tiers = [e.get("performance_tier") for e in llm_events if "performance_tier" in e]
            performance_ratings = [e.get("performance_rating") for e in llm_events if "performance_rating" in e]
            
            llm_performance = {
                "model_tiers": {tier: performance_tiers.count(tier) for tier in set(performance_tiers)},
                "performance_distribution": {rating: performance_ratings.count(rating) for rating in set(performance_ratings)}
            }
        
        # 分析Chain性能
        chain_performance = {}
        if chain_events:
            complexities = [e.get("complexity") for e in chain_events if "complexity" in e]
            efficiency_scores = [e.get("efficiency_score", 0) for e in chain_events if "efficiency_score" in e]
            
            chain_performance = {
                "complexity_distribution": {level: complexities.count(level) for level in set(complexities)},
                "avg_efficiency": sum(efficiency_scores) / len(efficiency_scores) if efficiency_scores else 0
            }
        
        return {
            "total_events": len(self.custom_events),
            "llm_events": len(llm_events),
            "chain_events": len(chain_events),
            "llm_performance": llm_performance,
            "chain_performance": chain_performance
        }

def custom_event_callback_example():
    """自定义事件Callback示例"""
    print("=== 自定义事件Callback示例 ===")
    
    # 创建自定义事件处理器
    custom_handler = CustomEventCallbackHandler()
    
    # 创建LLM和Chain
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 测试LLM自定义事件处理
    print("测试LLM自定义事件处理:")
    response = llm.invoke("请介绍LangChain框架的特点。", callbacks=[custom_handler])
    print(f"响应: {response[:50]}...")
    
    # 测试Chain自定义事件处理
    print("\n测试Chain自定义事件处理:")
    chain = LLMChain(
        llm=llm,
        prompt=PromptTemplate(template="{input}", input_variables=["input"])
    )
    
    result = chain.invoke({"input": "请分析LangChain的应用场景。"}, callbacks=[custom_handler])
    print(f"Chain结果: {result['text'][:50]}...")
    
    # 获取自定义事件分析
    analysis = custom_handler.get_performance_analysis()
    print(f"\n自定义事件分析:")
    print(json.dumps(analysis, indent=2, ensure_ascii=False))

async def main():
    """主函数，运行所有高级示例"""
    print("LangChain Callbacks 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 异步Callback示例
        await async_callback_example()
        
        # 事件过滤示例
        event_filter_callback_example()
        
        # 性能监控示例
        performance_monitor_callback_example()
        
        # 安全检查示例
        security_callback_example()
        
        # 批量处理示例
        batch_processing_callback_example()
        
        # 自定义事件示例
        custom_event_callback_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    asyncio.run(main())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Callbacks 组件基础示例
演示各种内置Callback Handler的基础使用方法
"""

import os
import sys
import time
from typing import Dict, List, Any
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.callbacks import (
    BaseCallbackHandler,
    StreamingStdOutCallbackHandler,
    FileCallbackHandler
)
from langchain_core.outputs import LLMResult
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.agents import create_react_agent, AgentExecutor
from langchain.tools import Tool
import json

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class SimpleCallbackHandler(BaseCallbackHandler):
    """简单的自定义Callback Handler"""
    
    def __init__(self):
        self.events = []
        self.start_time = None
    
    def on_llm_start(
        self, 
        serialized: Dict[str, Any], 
        prompts: List[str], 
        **kwargs: Any
    ) -> None:
        """LLM开始时的回调"""
        self.start_time = time.time()
        event = {
            "event": "llm_start",
            "model": serialized.get("name", "unknown"),
            "prompt_count": len(prompts),
            "timestamp": self.start_time
        }
        self.events.append(event)
        print(f"[Callback] LLM开始 - 模型: {event['model']}, 提示数: {event['prompt_count']}")
    
    def on_llm_end(self, response: LLMResult, **kwargs: Any) -> None:
        """LLM结束时的回调"""
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        event = {
            "event": "llm_end",
            "duration": duration,
            "token_usage": response.llm_output.get("token_usage", {}),
            "timestamp": end_time
        }
        self.events.append(event)
        print(f"[Callback] LLM结束 - 耗时: {duration:.2f}s, Token使用: {event['token_usage']}")
    
    def on_chain_start(
        self, 
        serialized: Dict[str, Any], 
        inputs: Dict[str, Any], 
        **kwargs: Any
    ) -> None:
        """Chain开始时的回调"""
        event = {
            "event": "chain_start",
            "chain_type": serialized.get("name", "unknown"),
            "input_keys": list(inputs.keys()),
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"[Callback] Chain开始 - 类型: {event['chain_type']}, 输入键: {event['input_keys']}")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs: Any) -> None:
        """Chain结束时的回调"""
        event = {
            "event": "chain_end",
            "output_keys": list(outputs.keys()),
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"[Callback] Chain结束 - 输出键: {event['output_keys']}")
    
    def on_tool_start(
        self, 
        serialized: Dict[str, Any], 
        input_str: str, 
        **kwargs: Any
    ) -> None:
        """工具开始时的回调"""
        event = {
            "event": "tool_start",
            "tool_name": serialized.get("name", "unknown"),
            "input_preview": input_str[:50] + "..." if len(input_str) > 50 else input_str,
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"[Callback] 工具开始 - 名称: {event['tool_name']}, 输入: {event['input_preview']}")
    
    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """工具结束时的回调"""
        event = {
            "event": "tool_end",
            "output_preview": output[:50] + "..." if len(output) > 50 else output,
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"[Callback] 工具结束 - 输出: {event['output_preview']}")
    
    def get_events(self) -> List[Dict[str, Any]]:
        """获取所有事件"""
        return self.events

def streaming_callback_example():
    """流式输出回调示例"""
    print("=== 流式输出回调示例 ===")
    
    # 创建流式回调处理器
    streaming_handler = StreamingStdOutCallbackHandler()
    
    # 创建LLM并启用流式输出
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.7,
        streaming=True,
        callbacks=[streaming_handler]
    )
    
    # 测试流式输出
    prompt = "请写一首关于春天的诗，要求4行，每行7个字。"
    print(f"提示: {prompt}")
    print("流式输出:")
    
    response = llm.invoke(prompt)
    print(f"\n完整响应: {response}")

def file_callback_example():
    """文件输出回调示例"""
    print("=== 文件输出回调示例 ===")
    
    # 创建文件回调处理器
    file_handler = FileCallbackHandler(
        filename="llm_output.txt",
        mode="w",  # 写入模式
        append=False  # 不追加
    )
    
    # 创建LLM
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.3,
        callbacks=[file_handler]
    )
    
    # 测试文件输出
    prompts = [
        "请解释什么是机器学习。",
        "请介绍深度学习的基本概念。",
        "请说明人工智能的应用领域。"
    ]
    
    for i, prompt in enumerate(prompts, 1):
        print(f"\n提示 {i}: {prompt}")
        response = llm.invoke(prompt)
        print(f"响应 {i}: {response[:50]}...")
    
    print(f"\n输出已保存到文件: {file_handler.filename}")

def chain_callback_example():
    """Chain回调示例"""
    print("=== Chain回调示例 ===")
    
    # 创建自定义回调处理器
    custom_handler = SimpleCallbackHandler()
    
    # 创建LLM
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    
    # 创建Prompt模板
    prompt_template = PromptTemplate(
        template="请分析以下主题：{topic}\n分析要点：",
        input_variables=["topic"]
    )
    
    # 创建Chain
    chain = LLMChain(
        llm=llm,
        prompt=prompt_template,
        callbacks=[custom_handler]
    )
    
    # 测试Chain
    topics = [
        "人工智能的发展趋势",
        "云计算的技术特点",
        "区块链的应用场景"
    ]
    
    for topic in topics:
        print(f"\n{'='*50}")
        print(f"主题: {topic}")
        
        result = chain.invoke({"topic": topic})
        print(f"分析结果: {result['text']}")
    
    # 显示回调事件
    print(f"\n{'='*50}")
    print("回调事件统计:")
    events = custom_handler.get_events()
    
    event_counts = {}
    for event in events:
        event_type = event["event"]
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    for event_type, count in event_counts.items():
        print(f"{event_type}: {count} 次")

def agent_callback_example():
    """Agent回调示例"""
    print("=== Agent回调示例 ===")
    
    # 创建自定义回调处理器
    agent_handler = SimpleCallbackHandler()
    
    # 创建LLM
    llm = OpenAI(temperature=0)
    
    # 创建工具
    tools = [
        Tool(
            name="Calculator",
            description="执行数学计算",
            func=lambda x: str(eval(x))
        ),
        Tool(
            name="Greeting",
            description="生成问候语",
            func=lambda x: f"你好，{x}！"
        )
    ]
    
    # 创建Agent Prompt
    from langchain import hub
    prompt = hub.pull("hwchase17/react")
    
    # 创建Agent
    agent = create_react_agent(llm, tools, prompt)
    
    # 创建Agent执行器
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        callbacks=[agent_handler],
        verbose=True
    )
    
    # 测试Agent
    questions = [
        "计算 123 * 456",
        "向张三问好",
        "计算 (100 + 200) * 3"
    ]
    
    for question in questions:
        print(f"\n{'='*60}")
        print(f"问题: {question}")
        
        try:
            result = agent_executor.invoke({"input": question})
            print(f"答案: {result['output']}")
        except Exception as e:
            print(f"执行失败: {e}")
    
    # 显示Agent回调事件
    print(f"\n{'='*60}")
    print("Agent回调事件:")
    events = agent_handler.get_events()
    
    for event in events:
        timestamp = time.strftime("%H:%M:%S", time.localtime(event["timestamp"]))
        print(f"[{timestamp}] {event['event']}: {event}")

class MetricsCallbackHandler(BaseCallbackHandler):
    """指标收集回调处理器"""
    
    def __init__(self):
        self.metrics = {
            "llm_calls": [],
            "chain_executions": [],
            "tool_usages": []
        }
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """记录LLM开始"""
        self.metrics["llm_calls"].append({
            "model": serialized.get("name", "unknown"),
            "prompt_length": len(prompts[0]) if prompts else 0,
            "timestamp": time.time()
        })
    
    def on_llm_end(self, response, **kwargs):
        """记录LLM结束"""
        if self.metrics["llm_calls"]:
            last_call = self.metrics["llm_calls"][-1]
            last_call.update({
                "duration": time.time() - last_call.get("timestamp", time.time()),
                "token_usage": response.llm_output.get("token_usage", {}),
                "output_length": len(response.generations[0][0].text) if response.generations else 0
            })
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        """记录Chain开始"""
        self.metrics["chain_executions"].append({
            "chain_type": serialized.get("name", "unknown"),
            "input_keys": list(inputs.keys()),
            "timestamp": time.time()
        })
    
    def on_chain_end(self, outputs, **kwargs):
        """记录Chain结束"""
        if self.metrics["chain_executions"]:
            last_execution = self.metrics["chain_executions"][-1]
            last_execution.update({
                "duration": time.time() - last_execution.get("timestamp", time.time()),
                "output_keys": list(outputs.keys())
            })
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        """记录工具开始"""
        self.metrics["tool_usages"].append({
            "tool_name": serialized.get("name", "unknown"),
            "input_length": len(input_str),
            "timestamp": time.time()
        })
    
    def on_tool_end(self, output, **kwargs):
        """记录工具结束"""
        if self.metrics["tool_usages"]:
            last_usage = self.metrics["tool_usages"][-1]
            last_usage.update({
                "duration": time.time() - last_usage.get("timestamp", time.time()),
                "output_length": len(output)
            })
    
    def get_metrics_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        llm_calls = self.metrics["llm_calls"]
        chain_executions = self.metrics["chain_executions"]
        tool_usages = self.metrics["tool_usages"]
        
        return {
            "llm_metrics": {
                "total_calls": len(llm_calls),
                "avg_duration": sum(c.get("duration", 0) for c in llm_calls) / len(llm_calls) if llm_calls else 0,
                "total_tokens": sum(c.get("token_usage", {}).get("total_tokens", 0) for c in llm_calls)
            },
            "chain_metrics": {
                "total_executions": len(chain_executions),
                "avg_duration": sum(e.get("duration", 0) for e in chain_executions) / len(chain_executions) if chain_executions else 0
            },
            "tool_metrics": {
                "total_usages": len(tool_usages),
                "avg_duration": sum(u.get("duration", 0) for u in tool_usages) / len(tool_usages) if tool_usages else 0
            }
        }

def metrics_callback_example():
    """指标收集回调示例"""
    print("=== 指标收集回调示例 ===")
    
    # 创建指标回调处理器
    metrics_handler = MetricsCallbackHandler()
    
    # 创建LLM和Chain
    llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.3)
    prompt = PromptTemplate(
        template="分析：{topic}",
        input_variables=["topic"]
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    
    # 测试指标收集
    test_data = [
        {"input": {"topic": "人工智能"}, "type": "chain"},
        {"input": "计算 100 + 200", "type": "agent"}
    ]
    
    for i, data in enumerate(test_data, 1):
        print(f"\n测试 {i}: {data}")
        
        if data["type"] == "chain":
            # 使用Chain测试
            result = chain.invoke(data["input"], callbacks=[metrics_handler])
            print(f"Chain结果: {result['text'][:50]}...")
        
        elif data["type"] == "agent":
            # 使用Agent测试
            calculator_tool = Tool(name="Calculator", func=lambda x: str(eval(x)))
            agent_tools = [calculator_tool]
            
            from langchain import hub
            agent_prompt = hub.pull("hwchase17/react")
            agent = create_react_agent(llm, agent_tools, agent_prompt)
            agent_executor = AgentExecutor(
                agent=agent,
                tools=agent_tools,
                callbacks=[metrics_handler]
            )
            
            try:
                result = agent_executor.invoke({"input": data["input"]})
                print(f"Agent结果: {result['output'][:50]}...")
            except Exception as e:
                print(f"Agent执行失败: {e}")
    
    # 显示指标摘要
    print(f"\n{'='*50}")
    print("性能指标摘要:")
    summary = metrics_handler.get_metrics_summary()
    
    for category, metrics in summary.items():
        print(f"\n{category}:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name}: {value}")

def multi_handler_example():
    """多Handler示例"""
    print("=== 多Handler示例 ===")
    
    # 创建多个Handler
    streaming_handler = StreamingStdOutCallbackHandler()
    custom_handler = SimpleCallbackHandler()
    
    # 创建LLM
    llm = OpenAI(
        model="gpt-3.5-turbo-instruct",
        temperature=0.7,
        streaming=True,
        callbacks=[streaming_handler, custom_handler]
    )
    
    # 测试多Handler协同工作
    prompt = "请介绍一下LangChain框架的主要特点。"
    print(f"提示: {prompt}")
    print("\n流式输出和自定义回调同时工作:")
    
    response = llm.invoke(prompt)
    
    print(f"\n自定义Handler捕获的事件数: {len(custom_handler.get_events())}")

def main():
    """主函数，运行所有示例"""
    print("LangChain Callbacks 组件基础示例")
    print("=" * 50)
    print()
    
    try:
        # 流式输出示例
        streaming_callback_example()
        
        # 文件输出示例
        file_callback_example()
        
        # Chain回调示例
        chain_callback_example()
        
        # Agent回调示例
        agent_callback_example()
        
        # 指标收集示例
        metrics_callback_example()
        
        # 多Handler示例
        multi_handler_example()
        
    except Exception as e:
        print(f"运行示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
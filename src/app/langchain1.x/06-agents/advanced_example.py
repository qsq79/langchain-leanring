#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LangChain Agents 组件高级示例
演示自定义Agent、多Agent协作、高级Agent模式等高级功能
"""

import os
import sys
import asyncio
import time
from typing import Dict, List, Any, Optional, Union
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI, OpenAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import json
import random

# 使用绝对导入配置加载器
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
from src.app.utils.config_loader import setup_openai_config

# 从环境变量加载API配置
setup_openai_config()

class PlanningAgent:
    """规划Agent - 专门负责任务分解和规划"""
    
    def __init__(self, llm=None):
        self.llm = llm or OpenAI(temperature=0)
        self.plan = []
    
    def create_plan(self, task: str) -> List[Dict[str, str]]:
        """创建执行计划"""
        prompt = f"""
        请将以下任务分解为具体的执行步骤：
        
        任务：{task}
        
        请按照以下格式输出计划：
        1. 步骤描述 - [工具名称]
        2. 步骤描述 - [工具名称]
        3. 步骤描述 - [工具名称]
        
        每个步骤都应该明确需要使用的工具。
        """
        
        response = self.llm.invoke(prompt)
        
        # 解析计划
        steps = []
        lines = response.strip().split('\n')
        
        for line in lines:
            if line.strip() and '.' in line:
                step_num = line.split('.')[0].strip()
                step_desc = line.split('.')[1].strip()
                
                # 提取工具名称
                if '[' in step_desc and ']' in step_desc:
                    tool_name = step_desc.split('[')[1].split(']')[0]
                    description = step_desc.split('[')[0].strip()
                    steps.append({
                        "step": step_num,
                        "description": description,
                        "tool": tool_name
                    })
        
        self.plan = steps
        return steps
    
    def adjust_plan(self, failed_step: Dict[str, str], error: str) -> List[Dict[str, str]]:
        """调整计划"""
        prompt = f"""
        原始计划：
        {json.dumps(self.plan, indent=2, ensure_ascii=False)}
        
        失败步骤：
        {json.dumps(failed_step, indent=2, ensure_ascii=False)}
        
        错误信息：
        {error}
        
        请调整计划以避开这个错误：
        """
        
        response = self.llm.invoke(prompt)
        print(f"调整计划: {response}")
        
        # 简化示例：移除失败步骤后的剩余步骤
        failed_index = None
        for i, step in enumerate(self.plan):
            if step["step"] == failed_step["step"]:
                failed_index = i
                break
        
        if failed_index is not None:
            return self.plan[failed_index + 1:]
        
        return self.plan

class CustomTool(BaseTool):
    """自定义工具基类"""
    
    name: str
    description: str
    success_rate: float = 1.0  # 模拟成功率
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.execution_count = 0
        self.success_count = 0
    
    def _run(self, *args, **kwargs) -> str:
        """执行工具"""
        self.execution_count += 1
        
        # 模拟随机失败
        if random.random() > self.success_rate:
            error_msg = f"{self.name}执行失败"
            print(f"工具失败: {error_msg}")
            raise Exception(error_msg)
        
        self.success_count += 1
        return self._execute_tool(*args, **kwargs)
    
    @abstractmethod
    def _execute_tool(self, *args, **kwargs) -> str:
        """实际执行工具逻辑"""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """获取工具统计"""
        success_rate = self.success_count / self.execution_count if self.execution_count > 0 else 0
        return {
            "name": self.name,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "success_rate": success_rate
        }

class SearchTool(CustomTool):
    """搜索工具"""
    
    name: str = "Search"
    description: str = "在互联网上搜索信息"
    success_rate: float = 0.8
    
    def _execute_tool(self, query: str) -> str:
        """执行搜索"""
        # 模拟搜索结果
        time.sleep(1)  # 模拟网络延迟
        
        results = {
            "Python": "Python是一种高级编程语言，具有简洁的语法和丰富的库。",
            "机器学习": "机器学习是人工智能的子领域，让计算机从数据中学习模式。",
            "天气": "今天天气晴朗，温度适宜，适合外出活动。"
        }
        
        for key in results:
            if key in query:
                return f"搜索结果：{results[key]}"
        
        return f"搜索'{query}'未找到相关结果。"

class CalculatorTool(CustomTool):
    """计算器工具"""
    
    name: str = "Calculator"
    description: str = "执行数学计算"
    success_rate: float = 0.9
    
    def _execute_tool(self, expression: str) -> str:
        """执行计算"""
        try:
            result = eval(expression)
            return f"计算结果：{expression} = {result}"
        except Exception as e:
            return f"计算错误：{str(e)}"

class WeatherTool(CustomTool):
    """天气查询工具"""
    
    name: str = "Weather"
    description: str = "查询指定地点的天气"
    success_rate: float = 0.7
    
    def _execute_tool(self, location: str) -> str:
        """查询天气"""
        # 模拟天气数据
        weather_data = {
            "北京": "晴天，25°C",
            "上海": "多云，28°C",
            "广州": "阵雨，30°C",
            "深圳": "晴天，29°C"
        }
        
        return weather_data.get(location, f"无法获取{location}的天气信息")

class CustomAgent:
    """自定义Agent实现"""
    
    def __init__(self, tools: List[CustomTool], llm=None):
        self.tools = {tool.name: tool for tool in tools}
        self.llm = llm or OpenAI(temperature=0)
        self.execution_history = []
        self.max_iterations = 10
    
    def execute_task(self, task: str) -> str:
        """执行任务"""
        print(f"开始执行任务: {task}")
        
        # 创建计划
        planning_agent = PlanningAgent(self.llm)
        plan = planning_agent.create_plan(task)
        print(f"执行计划: {json.dumps(plan, indent=2, ensure_ascii=False)}")
        
        # 执行计划
        current_plan = plan.copy()
        iteration = 0
        
        while current_plan and iteration < self.max_iterations:
            iteration += 1
            print(f"\n--- 迭代 {iteration} ---")
            
            # 获取下一步
            next_step = current_plan[0]
            print(f"执行步骤: {next_step['description']} (工具: {next_step['tool']})")
            
            try:
                # 执行工具
                tool = self.tools.get(next_step["tool"])
                if not tool:
                    raise Exception(f"未找到工具: {next_step['tool']}")
                
                # 这里简化处理，实际应该解析工具参数
                result = tool._run(task)
                print(f"执行结果: {result}")
                
                # 记录执行历史
                self.execution_history.append({
                    "step": next_step,
                    "result": result,
                    "success": True
                })
                
                # 移除已完成的步骤
                current_plan.pop(0)
                
            except Exception as e:
                print(f"步骤执行失败: {e}")
                
                # 记录失败
                self.execution_history.append({
                    "step": next_step,
                    "error": str(e),
                    "success": False
                })
                
                # 调整计划
                current_plan = planning_agent.adjust_plan(next_step, str(e))
                print(f"调整后的计划: {json.dumps(current_plan, indent=2, ensure_ascii=False)}")
        
        # 生成最终结果
        return self._generate_final_result(task)
    
    def _generate_final_result(self, task: str) -> str:
        """生成最终结果"""
        successful_steps = [h for h in self.execution_history if h["success"]]
        failed_steps = [h for h in self.execution_history if not h["success"]]
        
        result = f"任务 '{task}' 执行完成。\n"
        result += f"成功步骤: {len(successful_steps)}\n"
        result += f"失败步骤: {len(failed_steps)}\n\n"
        
        if successful_steps:
            result += "成功执行的步骤:\n"
            for step in successful_steps:
                result += f"- {step['step']['description']}: {step['result']}\n"
        
        if failed_steps:
            result += "\n失败的步骤:\n"
            for step in failed_steps:
                result += f"- {step['step']['description']}: {step['error']}\n"
        
        return result
    
    def get_tool_stats(self) -> List[Dict[str, Any]]:
        """获取工具统计"""
        return [tool.get_stats() for tool in self.tools.values()]

class MultiAgentSystem:
    """多Agent协作系统"""
    
    def __init__(self):
        self.agents = {}
        self.communication_history = []
    
    def register_agent(self, name: str, agent: CustomAgent, role: str):
        """注册Agent"""
        self.agents[name] = {
            "agent": agent,
            "role": role,
            "status": "idle"
        }
    
    def delegate_task(self, task: str) -> Dict[str, Any]:
        """任务分配"""
        # 简化的任务分配逻辑
        if "搜索" in task or "查找" in task:
            assigned_agent = "search_agent"
        elif "计算" in task or "数学" in task:
            assigned_agent = "calc_agent"
        elif "天气" in task:
            assigned_agent = "weather_agent"
        else:
            assigned_agent = "general_agent"
        
        if assigned_agent not in self.agents:
            assigned_agent = "general_agent"
        
        return {
            "agent": assigned_agent,
            "task": task,
            "role": self.agents[assigned_agent]["role"]
        }
    
    def execute_collaborative_task(self, main_task: str) -> str:
        """执行协作任务"""
        print(f"开始协作任务: {main_task}")
        
        # 分解任务
        subtasks = self._decompose_task(main_task)
        
        results = []
        for subtask in subtasks:
            # 分配子任务
            assignment = self.delegate_task(subtask)
            agent_name = assignment["agent"]
            agent_info = self.agents[agent_name]
            
            print(f"分配子任务 '{subtask}' 给 {agent_name} ({agent_info['role']})")
            
            # 执行子任务
            agent_info["status"] = "working"
            try:
                result = agent_info["agent"].execute_task(subtask)
                results.append({
                    "subtask": subtask,
                    "agent": agent_name,
                    "result": result,
                    "success": True
                })
            except Exception as e:
                results.append({
                    "subtask": subtask,
                    "agent": agent_name,
                    "result": str(e),
                    "success": False
                })
            finally:
                agent_info["status"] = "idle"
            
            # 记录通信历史
            self.communication_history.append({
                "from": "coordinator",
                "to": agent_name,
                "message": subtask,
                "timestamp": time.time()
            })
        
        # 综合结果
        return self._synthesize_results(results)
    
    def _decompose_task(self, task: str) -> List[str]:
        """任务分解"""
        # 简化的任务分解逻辑
        if "和" in task:
            return task.split("和")
        elif "，" in task:
            return task.split("，")
        else:
            return [task]
    
    def _synthesize_results(self, results: List[Dict[str, Any]]) -> str:
        """综合结果"""
        summary = f"协作任务完成。共处理 {len(results)} 个子任务。\n\n"
        
        for i, result in enumerate(results, 1):
            status = "成功" if result["success"] else "失败"
            summary += f"{i}. 子任务: {result['subtask']}\n"
            summary += f"   负责Agent: {result['agent']}\n"
            summary += f"   状态: {status}\n"
            summary += f"   结果: {result['result']}\n\n"
        
        return summary

class AgentCallbackHandler(BaseCallbackHandler):
    """Agent回调处理器"""
    
    def __init__(self):
        self.events = []
    
    def on_agent_action(self, action: AgentAction, **kwargs) -> Any:
        """Agent动作回调"""
        event = {
            "type": "action",
            "tool": action.tool,
            "input": action.tool_input,
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"Agent动作: {action.tool}({action.tool_input})")
    
    def on_agent_finish(self, finish: AgentFinish, **kwargs) -> Any:
        """Agent完成回调"""
        event = {
            "type": "finish",
            "output": finish.return_values,
            "timestamp": time.time()
        }
        self.events.append(event)
        print(f"Agent完成: {finish.return_values}")
    
    def get_events(self) -> List[Dict[str, Any]]:
        """获取事件历史"""
        return self.events

def custom_agent_example():
    """自定义Agent示例"""
    print("=== 自定义Agent示例 ===")
    
    # 创建自定义工具
    tools = [
        SearchTool(),
        CalculatorTool(),
        WeatherTool()
    ]
    
    # 创建自定义Agent
    agent = CustomAgent(tools)
    
    # 测试任务
    tasks = [
        "搜索Python编程语言的信息",
        "计算 123 * 456",
        "查询北京的天气"
    ]
    
    for task in tasks:
        print(f"\n{'='*50}")
        result = agent.execute_task(task)
        print(f"\n最终结果:\n{result}")
        
        # 显示工具统计
        print("\n工具统计:")
        for stats in agent.get_tool_stats():
            print(f"{stats['name']}: 执行{stats['execution_count']}次，成功率{stats['success_rate']:.2%}")

def multi_agent_system_example():
    """多Agent协作系统示例"""
    print("=== 多Agent协作系统示例 ===")
    
    # 创建多Agent系统
    multi_system = MultiAgentSystem()
    
    # 创建专门的Agent
    search_tools = [SearchTool()]
    search_agent = CustomAgent(search_tools)
    
    calc_tools = [CalculatorTool()]
    calc_agent = CustomAgent(calc_tools)
    
    weather_tools = [WeatherTool()]
    weather_agent = CustomAgent(weather_tools)
    
    general_tools = [SearchTool(), CalculatorTool(), WeatherTool()]
    general_agent = CustomAgent(general_tools)
    
    # 注册Agent
    multi_system.register_agent("search_agent", search_agent, "搜索专家")
    multi_system.register_agent("calc_agent", calc_agent, "计算专家")
    multi_system.register_agent("weather_agent", weather_agent, "天气专家")
    multi_system.register_agent("general_agent", general_agent, "通用助手")
    
    # 测试协作任务
    collaborative_tasks = [
        "搜索Python和计算100+200",
        "查询北京天气和搜索机器学习",
        "计算50*10和搜索天气"
    ]
    
    for task in collaborative_tasks:
        print(f"\n{'='*60}")
        result = multi_system.execute_collaborative_task(task)
        print(f"\n协作结果:\n{result}")

def agent_with_callbacks_example():
    """带回调的Agent示例"""
    print("=== 带回调的Agent示例 ===")
    
    # 创建回调处理器
    callback_handler = AgentCallbackHandler()
    
    # 创建工具
    tools = [SearchTool(), CalculatorTool()]
    
    # 创建Agent
    agent = CustomAgent(tools)
    
    # 使用LangChain的AgentExecutor来演示回调
    from langchain.agents import create_react_agent
    from langchain.prompts import PromptTemplate
    
    llm = OpenAI(temperature=0)
    prompt = PromptTemplate.from_template("""
    你是一个AI助手，可以使用以下工具：
    {tools}
    
    使用以下格式：
    Question: 需要回答的问题
    Thought: 思考如何回答
    Action: 工具名称
    Action Input: 工具输入
    Observation: 工具输出
    ... (重复直到完成)
    Final Answer: 最终答案
    
    Question: {input}
    Thought: {agent_scratchpad}
    """)
    
    react_agent = create_react_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=react_agent,
        tools=tools,
        callbacks=[callback_handler],
        verbose=True,
        max_iterations=5
    )
    
    # 执行任务
    task = "搜索人工智能信息并计算100+200"
    print(f"执行任务: {task}")
    
    try:
        result = executor.invoke({"input": task})
        print(f"\n任务完成: {result['output']}")
    except Exception as e:
        print(f"任务执行失败: {e}")
    
    # 显示回调事件
    print("\n回调事件历史:")
    for event in callback_handler.get_events():
        print(f"{event['type']}: {event}")

def async_agent_example():
    """异步Agent示例"""
    print("=== 异步Agent示例 ===")
    
    class AsyncAgent(CustomAgent):
        """异步Agent"""
        
        async def aexecute_task(self, task: str) -> str:
            """异步执行任务"""
            print(f"异步开始执行任务: {task}")
            
            # 模拟异步操作
            await asyncio.sleep(1)
            
            # 创建计划
            planning_agent = PlanningAgent(self.llm)
            plan = planning_agent.create_plan(task)
            
            # 异步执行计划
            results = []
            for step in plan:
                tool = self.tools.get(step["tool"])
                if tool:
                    # 模拟异步工具执行
                    await asyncio.sleep(0.5)
                    result = tool._run(task)
                    results.append(result)
            
            return f"异步任务完成。结果: {' | '.join(results)}"
    
    # 创建异步Agent
    tools = [SearchTool(), CalculatorTool()]
    async_agent = AsyncAgent(tools)
    
    # 执行异步任务
    async def run_async_tasks():
        tasks = [
            "搜索Python",
            "计算100+200",
            "搜索天气"
        ]
        
        # 并发执行任务
        results = await asyncio.gather(*[
            async_agent.aexecute_task(task) for task in tasks
        ])
        
        return results
    
    # 运行异步任务
    print("开始异步任务...")
    results = asyncio.run(run_async_tasks())
    
    print("\n异步执行结果:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result}")

def main():
    """主函数，运行所有高级示例"""
    print("LangChain Agents 组件高级示例")
    print("=" * 50)
    print()
    
    try:
        # 自定义Agent示例
        custom_agent_example()
        
        # 多Agent协作示例
        multi_agent_system_example()
        
        # 回调示例
        agent_with_callbacks_example()
        
        # 异步Agent示例
        async_agent_example()
        
    except Exception as e:
        print(f"运行高级示例时出错: {e}")
        print("请确保已正确设置OPENAI_API_KEY环境变量")

if __name__ == "__main__":
    main()
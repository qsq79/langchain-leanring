#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体通信管理器 - 基于 AutoGen
管理多智能体之间的协同工作和消息传递
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat
from autogen_agentchat.conditions import TextMentionTermination
from core.logger import get_logger, log_agent_message
from agents.order_agent import OrderAgent
from agents.logistics_agent import LogisticsAgent
from agents.summary_agent import SummaryAgent

logger = get_logger(__name__)


@dataclass
class AgentInteraction:
    """智能体交互记录"""
    timestamp: str
    from_agent: str
    to_agent: str
    message_type: str
    content: str
    status: str = "completed"


class AgentManager:
    """智能体通信管理器 - 基于 AutoGen"""

    def __init__(self):
        """初始化智能体管理器"""
        # 初始化各个智能体
        self.order_agent = OrderAgent("order_agent")
        self.logistics_agent = LogisticsAgent("logistics_agent")
        self.summary_agent = SummaryAgent("summary_agent")
        
        self.interactions: List[AgentInteraction] = []
        self.visualizer_enabled = True
        
        # AutoGen 智能体列表
        self.autogen_agents = []
        self._initialize_autogen_team()
        
        logger.info("智能体通信管理器初始化完成 (基于 AutoGen)")
        logger.info(f"加载智能体: {[agent.name for agent in [self.order_agent, self.logistics_agent, self.summary_agent]]}")

    def _initialize_autogen_team(self):
        """
        初始化 AutoGen 多智能体团队
        """
        try:
            # 获取 AutoGen 智能体对象
            agents = []
            if self.order_agent.get_autogen_agent():
                agents.append(self.order_agent.get_autogen_agent())
            if self.logistics_agent.get_autogen_agent():
                agents.append(self.logistics_agent.get_autogen_agent())
            if self.summary_agent.get_autogen_agent():
                agents.append(self.summary_agent.get_autogen_agent())
            
            if len(agents) >= 2:
                # 创建 RoundRobinGroupChat 团队（轮询式）
                # 注意：在实际使用中，可能需要使用更适合的团队类型
                self.autogen_agents = agents
                
                # 预设的终止条件（当收到汇总消息时终止）
                self.termination_condition = TextMentionTermination("TERMINATE")
                
                logger.info(f"AutoGen 团队初始化成功，包含 {len(agents)} 个智能体")
            else:
                logger.warning(f"AutoGen 智能体数量不足: {len(agents)}")
                self.autogen_agents = []
                
        except Exception as e:
            logger.error(f"AutoGen 团队初始化失败: {e}")
            self.autogen_agents = []

    async def process_query(
        self,
        user_query: str,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户查询请求
        
        Args:
            user_query: 用户查询字符串
            order_id: 订单编号（可选）
            
        Returns:
            处理结果字典
        """
        self.interactions.clear()
        start_time = datetime.now()
        
        logger.info("=" * 60)
        logger.info(f"开始处理用户查询: {user_query}")
        if order_id:
            logger.info(f"订单编号: {order_id}")
        logger.info("=" * 60)
        
        try:
            # 记录交互
            self._add_interaction(
                "用户",
                self.summary_agent.name,
                "QUERY_START",
                f"用户查询: {user_query}"
            )
            
            # 准备查询请求
            query_request = {
                "user_query": user_query,
                "order_id": order_id
            }
            
            # 判断需要哪些智能体
            needs_order = self._needs_order_info(user_query, order_id)
            needs_logistics = self._needs_logistics_info(user_query, order_id)
            
            logger.info(f"智能体分配 - 订单查询: {needs_order}, 物流查询: {needs_logistics}")
            
            # 记录任务分发
            if needs_order:
                self._add_interaction(
                    self.summary_agent.name,
                    self.order_agent.name,
                    "TASK_DISPATCH",
                    f"查询订单: {order_id if order_id else '从查询中提取'}"
                )
            
            if needs_logistics:
                self._add_interaction(
                    self.summary_agent.name,
                    self.logistics_agent.name,
                    "TASK_DISPATCH",
                    f"查询物流: {order_id if order_id else '从查询中提取'}"
                )
            
            # 并行执行订单查询和物流查询
            tasks = []
            order_result = None
            logistics_result = None
            
            if needs_order:
                tasks.append(self.order_agent.process_request(query_request))
            if needs_logistics:
                tasks.append(self.logistics_agent.process_request(query_request))
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # 解析结果
                result_index = 0
                if needs_order:
                    order_result = results[result_index]
                    result_index += 1
                    if isinstance(order_result, Exception):
                        logger.error(f"订单查询智能体异常: {order_result}")
                        order_result = {
                            "agent": self.order_agent.name,
                            "success": False,
                            "error": f"智能体异常: {str(order_result)}"
                        }
                
                if needs_logistics:
                    logistics_result = results[result_index]
                    if isinstance(logistics_result, Exception):
                        logger.error(f"物流查询智能体异常: {logistics_result}")
                        logistics_result = {
                            "agent": self.logistics_agent.name,
                            "success": False,
                            "error": f"智能体异常: {str(logistics_result)}"
                        }
            
            # 汇总结果
            logger.info("汇总查询结果，生成回复")
            
            if order_result:
                self._add_interaction(
                    self.order_agent.name,
                    self.summary_agent.name,
                    "RESULT传递",
                    f"订单查询结果: {order_result.get('success', False)}"
                )
            
            if logistics_result:
                self._add_interaction(
                    self.logistics_agent.name,
                    self.summary_agent.name,
                    "RESULT传递",
                    f"物流查询结果: {logistics_result.get('success', False)}"
                )
            
            summary_result = await self.summary_agent.summarize_results(
                user_query,
                order_result,
                logistics_result
            )
            
            self._add_interaction(
                self.summary_agent.name,
                "用户",
                "RESPONSE_SEND",
                f"发送回复给用户"
            )
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            logger.info("=" * 60)
            logger.info(f"查询处理完成，耗时: {processing_time:.2f}秒")
            logger.info("=" * 60)
            
            return {
                "success": True,
                "user_query": user_query,
                "order_id": order_id,
                "order_result": order_result,
                "logistics_result": logistics_result,
                "summary_result": summary_result,
                "response": summary_result.get('response', ''),
                "interactions": self.interactions,
                "processing_time": processing_time,
                "timestamp": end_time.isoformat(),
                "framework": "AutoGen"
            }
            
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            
            return {
                "success": False,
                "user_query": user_query,
                "order_id": order_id,
                "error": str(e),
                "interactions": self.interactions,
                "processing_time": processing_time,
                "timestamp": end_time.isoformat(),
                "framework": "AutoGen"
            }

    async def process_query_with_autogen(
        self,
        user_query: str,
        order_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 AutoGen 团队处理用户查询（实验性功能）
        
        Args:
            user_query: 用户查询字符串
            order_id: 订单编号（可选）
            
        Returns:
            处理结果字典
        """
        # 这个方法使用 AutoGen 的 Team 机制进行真正的多智能体协作
        # 目前作为实验性功能，主要使用 process_query 方法
        
        logger.info("[AutoGen Team] 尝试使用 Team 机制处理查询")
        
        if not self.autogen_agents:
            logger.warning("[AutoGen Team] 团队未初始化，回退到标准处理")
            return await self.process_query(user_query, order_id)
        
        try:
            # 构建消息
            if order_id:
                message = f"用户查询: {user_query}\n订单编号: {order_id}"
            else:
                message = f"用户查询: {user_query}\n请从查询中提取订单编号"
            
            # 创建团队（这里需要根据 AutoGen 的具体 API 调整）
            # 注意：AutoGen 0.4.x 的 Team API 可能与旧版本不同
            # 以下代码需要根据实际的 AutoGen 0.4.x API 进行调整
            
            # 目前回退到标准处理
            logger.info("[AutoGen Team] Team 机制暂未实现，回退到标准处理")
            return await self.process_query(user_query, order_id)
            
        except Exception as e:
            logger.error(f"[AutoGen Team] 处理失败: {e}，回退到标准处理")
            return await self.process_query(user_query, order_id)

    def _needs_order_info(self, user_query: str, order_id: Optional[str]) -> bool:
        """
        判断是否需要查询订单信息
        
        Args:
            user_query: 用户查询
            order_id: 订单编号
            
        Returns:
            是否需要查询订单信息
        """
        # 如果有订单编号，查询订单信息
        if order_id:
            return True
        
        # 根据查询内容判断
        order_keywords = ["订单", "购买", "支付", "状态", "商品", "金额", "退款"]
        return any(keyword in user_query for keyword in order_keywords)

    def _needs_logistics_info(self, user_query: str, order_id: Optional[str]) -> bool:
        """
        判断是否需要查询物流信息
        
        Args:
            user_query: 用户查询
            order_id: 订单编号
            
        Returns:
            是否需要查询物流信息
        """
        # 根据查询内容判断
        logistics_keywords = ["物流", "快递", "配送", "送达", "运输", "轨迹", "快递单"]
        return any(keyword in user_query for keyword in logistics_keywords)

    def _add_interaction(
        self,
        from_agent: str,
        to_agent: str,
        message_type: str,
        content: str
    ):
        """
        添加交互记录
        
        Args:
            from_agent: 发送智能体
            to_agent: 接收智能体
            message_type: 消息类型
            content: 消息内容
        """
        interaction = AgentInteraction(
            timestamp=datetime.now().isoformat(),
            from_agent=from_agent,
            to_agent=to_agent,
            message_type=message_type,
            content=content
        )
        self.interactions.append(interaction)
        
        # 记录到日志
        log_agent_message(from_agent, to_agent, message_type, content)

    def visualize_interactions(self, interactions: List[AgentInteraction] = None) -> str:
        """
        可视化智能体交互过程
        
        Args:
            interactions: 交互记录列表，默认使用当前记录
            
        Returns:
            可视化文本
        """
        if interactions is None:
            interactions = self.interactions
        
        if not interactions:
            return "无交互记录"
        
        output = []
        output.append("\n" + "=" * 60)
        output.append("智能体交互过程可视化 (基于 AutoGen)")
        output.append("=" * 60 + "\n")
        
        for idx, interaction in enumerate(interactions, 1):
            output.append(f"[{idx}] {interaction.timestamp[:19]}")
            output.append(f"    {interaction.from_agent} → {interaction.to_agent}")
            output.append(f"    类型: {interaction.message_type}")
            output.append(f"    内容: {interaction.content}")
            output.append("-" * 60)
        
        return '\n'.join(output)

    def get_agent_info(self) -> Dict[str, Any]:
        """
        获取所有智能体的信息
        
        Returns:
            智能体信息字典
        """
        return {
            "order_agent": self.order_agent.get_info(),
            "logistics_agent": self.logistics_agent.get_info(),
            "summary_agent": self.summary_agent.get_info(),
            "autogen_team_size": len(self.autogen_agents),
            "autogen_available": True,
            "framework": "AutoGen"
        }

    def get_autogen_team(self):
        """
        获取 AutoGen 团队对象
        
        Returns:
            AutoGen 团队对象或 None
        """
        return self.autogen_agents


# 创建全局智能体管理器实例
agent_manager = AgentManager()
logger.info("全局智能体管理器实例创建成功")
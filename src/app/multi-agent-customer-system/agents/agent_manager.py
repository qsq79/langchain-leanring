#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体通信管理器
管理多智能体之间的协同工作和消息传递
"""

import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

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
    """智能体通信管理器"""

    def __init__(self):
        """初始化智能体管理器"""
        self.order_agent = OrderAgent("Agent A")
        self.logistics_agent = LogisticsAgent("Agent B")
        self.summary_agent = SummaryAgent("Agent C")
        
        self.interactions: List[AgentInteraction] = []
        self.visualizer_enabled = True
        
        logger.info("智能体通信管理器初始化完成")
        logger.info(f"加载智能体: {[agent.name for agent in [self.order_agent, self.logistics_agent, self.summary_agent]]}")

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
            
            # 并行执行订单查询和物流查询
            logger.info(f"分发任务给订单查询智能体和物流查询智能体")
            
            self._add_interaction(
                self.summary_agent.name,
                "订单查询智能体",
                "TASK_DISPATCH",
                f"查询订单: {order_id if order_id else '从查询中提取'}"
            )
            
            self._add_interaction(
                self.summary_agent.name,
                "物流查询智能体",
                "TASK_DISPATCH",
                f"查询物流: {order_id if order_id else '从查询中提取'}"
            )
            
            # 并行执行
            order_task = self.order_agent.process_request(query_request)
            logistics_task = self.logistics_agent.process_request(query_request)
            
            order_result, logistics_result = await asyncio.gather(
                order_task, logistics_task, return_exceptions=True
            )
            
            # 处理可能的异常
            if isinstance(order_result, Exception):
                logger.error(f"订单查询智能体异常: {order_result}")
                order_result = {
                    "agent": self.order_agent.name,
                    "success": False,
                    "error": f"智能体异常: {str(order_result)}"
                }
            
            if isinstance(logistics_result, Exception):
                logger.error(f"物流查询智能体异常: {logistics_result}")
                logistics_result = {
                    "agent": self.logistics_agent.name,
                    "success": False,
                    "error": f"智能体异常: {str(logistics_result)}"
                }
            
            # 汇总结果
            logger.info("汇总查询结果，生成回复")
            
            self._add_interaction(
                "订单查询智能体",
                self.summary_agent.name,
                "RESULT传递",
                f"订单查询结果: {order_result.get('success', False)}"
            )
            
            self._add_interaction(
                "物流查询智能体",
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
                "timestamp": end_time.isoformat()
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
                "timestamp": end_time.isoformat()
            }

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
        output.append("智能体交互过程可视化")
        output.append("=" * 60 + "\n")
        
        for idx, interaction in enumerate(interactions, 1):
            output.append(f"[{idx}] {interaction.timestamp[:19]}")
            output.append(f"    {interaction.from_agent} → {interaction.to_agent}")
            output.append(f"    类型: {interaction.message_type}")
            output.append(f"    内容: {interaction.content}")
            output.append("-" * 60)
        
        return '\n'.join(output)

    def get_agent_info(self) -> Dict[str, Dict[str, str]]:
        """获取所有智能体信息"""
        return {
            "order_agent": self.order_agent.get_info(),
            "logistics_agent": self.logistics_agent.get_info(),
            "summary_agent": self.summary_agent.get_info()
        }

    def reset(self):
        """重置管理器状态"""
        self.interactions.clear()
        logger.info("智能体管理器已重置")


# 全局智能体管理器实例
agent_manager = AgentManager()
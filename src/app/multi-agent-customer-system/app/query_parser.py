#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
查询解析器模块
负责解析用户查询内容，提取订单编号和查询意图
"""

import re
from typing import Dict, Optional, Any
from enum import Enum

from core.logger import get_logger

logger = get_logger(__name__)


class QueryIntent(Enum):
    """查询意图枚举"""
    ORDER_STATUS = "order_status"  # 查询订单状态
    LOGISTICS = "logistics"  # 查询物流信息
    GENERAL = "general"  # 一般查询
    UNKNOWN = "unknown"  # 未知意图


class QueryParser:
    """查询解析器类"""

    def __init__(self):
        """初始化查询解析器"""
        # 订单编号匹配模式（ORD开头，后跟至少3位数字）
        self.order_id_pattern = re.compile(
            r'[Oo][Rr][Dd]\d{3,}',
            re.IGNORECASE
        )
        
        # 查找所有数字序列（3位以上）
        self.number_sequence_pattern = re.compile(
            r'\b\d{4,}\b'
        )
        
        # 意图关键词
        self.intent_keywords = {
            QueryIntent.ORDER_STATUS: [
                "订单", "状态", "为什么", "发货", "支付", "取消",
                "order", "status", "shipping", "payment", "cancel"
            ],
            QueryIntent.LOGISTICS: [
                "物流", "快递", "包裹", "送到", "配送", "追踪", "轨迹",
                "何时", "位置", "logistics", "delivery", "tracking", "location"
            ]
        }
        
        logger.info("查询解析器初始化完成")

    def extract_order_id(self, query: str) -> Optional[str]:
        """
        从查询中提取订单编号
        
        Args:
            query: 用户查询字符串
            
        Returns:
            订单编号（如果找到），否则返回 None
        """
        # 尝试匹配 ORD 开头的编号
        match = self.order_id_pattern.search(query)
        if match:
            order_id = match.group().upper()
            logger.info(f"提取到订单编号: {order_id}")
            return order_id
        
        # 尝试匹配长数字序列
        number_match = self.number_sequence_pattern.search(query)
        if number_match:
            # 假设任何4位以上的数字可能是订单号
            potential_id = number_match.group()
            logger.info(f"提取到潜在订单编号: {potential_id}")
            return potential_id
        
        logger.warning(f"未能从查询中提取订单编号: {query}")
        return None

    def analyze_intent(self, query: str, order_id: Optional[str] = None) -> QueryIntent:
        """
        分析查询意图
        
        Args:
            query: 用户查询字符串
            order_id: 订单编号（如果已提取）
            
        Returns:
            查询意图
        """
        query_lower = query.lower()
        
        # 如果没有订单号，可能是通用查询
        if not order_id:
            logger.info("未检测到订单编号，判定为通用查询")
            return QueryIntent.GENERAL
        
        # 统计各意图的关键词出现次数
        intent_scores = {intent: 0 for intent in self.intent_keywords}
        
        for intent, keywords in self.intent_keywords.items():
            for keyword in keywords:
                if keyword.lower() in query_lower:
                    intent_scores[intent] += 1
        
        # 找出得分最高的意图
        max_score = max(intent_scores.values())
        
        if max_score == 0:
            logger.info(f"无法明确识别查询意图: {query}")
            return QueryIntent.GENERAL
        
        best_intent = max(intent_scores, key=intent_scores.get)
        logger.info(f"识别查询意图: {best_intent.value} (得分: {max_score})")
        
        return best_intent

    def parse(self, query: str) -> Dict[str, Any]:
        """
        完整解析查询
        
        Args:
            query: 用户查询字符串
            
        Returns:
            解析结果字典，包含:
            - original_query: 原始查询
            - order_id: 订单编号
            - intent: 查询意图
            - confidence: 置信度
            - normalized_query: 规范化后的查询
        """
        logger.info(f"开始解析查询: {query}")
        
        # 提取订单编号
        order_id = self.extract_order_id(query)
        
        # 分析意图
        intent = self.analyze_intent(query, order_id)
        
        # 计算置信度
        confidence = self._calculate_confidence(query, order_id, intent)
        
        # 规范化查询（移除特殊字符，保留关键词）
        normalized_query = self._normalize_query(query)
        
        result = {
            "original_query": query.strip(),
            "order_id": order_id,
            "intent": intent.value if intent else QueryIntent.UNKNOWN.value,
            "confidence": confidence,
            "normalized_query": normalized_query
        }
        
        logger.info(f"查询解析完成: {result}")
        return result

    def _calculate_confidence(
        self,
        query: str,
        order_id: Optional[str],
        intent: QueryIntent
    ) -> float:
        """
        计算解析置信度
        
        Args:
            query: 原始查询
            order_id: 订单编号
            intent: 查询意图
            
        Returns:
            置信度（0.0-1.0）
        """
        confidence = 0.0
        
        # 有订单编号增加置信度
        if order_id:
            confidence += 0.5
        
        # 明确的意图增加置信度
        if intent in [QueryIntent.ORDER_STATUS, QueryIntent.LOGISTICS]:
            confidence += 0.3
        
        # 查询长度适中增加置信度
        if 5 <= len(query) <= 50:
            confidence += 0.1
        
        # 包含关键词增加置信度
        query_lower = query.lower()
        for keywords in self.intent_keywords.values():
            if any(kw in query_lower for kw in keywords):
                confidence += 0.1
                break
        
        return min(confidence, 1.0)

    def _normalize_query(self, query: str) -> str:
        """
        规范化查询字符串
        
        Args:
            query: 原始查询
            
        Returns:
            规范化后的查询
        """
        # 移除多余的空格和特殊字符
        normalized = re.sub(r'\s+', ' ', query.strip())
        return normalized


# 全局查询解析器实例
query_parser = QueryParser()
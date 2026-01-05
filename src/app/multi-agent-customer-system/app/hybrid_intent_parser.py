#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
混合意图解析器模块
结合规则和LLM的意图识别，实现性能和准确性的最佳平衡
"""
import re
from typing import Dict, Optional, Any, List
from enum import Enum
import asyncio

from core.logger import get_logger
from app.query_parser import QueryParser, QueryIntent

logger = get_logger(__name__)


class IntentRecognitionStrategy(Enum):
    """意图识别策略枚举"""
    RULE_BASED = "rule_based"  # 基于规则（关键词匹配）
    LLM_BASED = "llm_based"    # 基于大模型
    HYBRID = "hybrid"          # 混合模式


class HybridIntentParser:
    """
    混合意图解析器
    - 简单查询：使用关键词匹配（快速、便宜）
    - 复杂查询：使用 LLM 分析（准确、智能）
    """

    def __init__(
        self,
        strategy: IntentRecognitionStrategy = IntentRecognitionStrategy.HYBRID,
        short_query_threshold: int = 10,  # 短查询阈值（字符数）
        confidence_threshold: float = 0.7,  # 置信度阈值
        enable_llm_fallback: bool = True  # 启用 LLM 后备
    ):
        """
        初始化混合意图解析器

        Args:
            strategy: 意图识别策略
            short_query_threshold: 短查询阈值（字符数），低于此值使用规则
            confidence_threshold: 规则匹配的置信度阈值，低于此值使用 LLM
            enable_llm_fallback: 是否启用 LLM 后备
        """
        self.strategy = strategy
        self.short_query_threshold = short_query_threshold
        self.confidence_threshold = confidence_threshold
        self.enable_llm_fallback = enable_llm_fallback

        # 基础的规则解析器
        self.rule_parser = QueryParser()

        # LLM 意图识别器（延迟初始化）
        self._llm_intent_recognizer = None

        logger.info(f"混合意图解析器初始化完成 - 策略: {strategy.value}")

    async def parse(self, query: str) -> Dict[str, Any]:
        """
        解析查询意图（混合模式）

        Args:
            query: 用户查询字符串

        Returns:
            解析结果字典
        """
        logger.info(f"混合意图解析开始 - 查询: {query}")
        logger.info(f"查询长度: {len(query)} 字符 (阈值: {self.short_query_threshold})")

        # 根据策略选择识别方式
        if self.strategy == IntentRecognitionStrategy.RULE_BASED:
            logger.info("使用规则-based 意图识别")
            return self.rule_parser.parse(query)

        elif self.strategy == IntentRecognitionStrategy.LLM_BASED:
            logger.info("使用 LLM-based 意图识别")
            return await self._llm_parse(query)

        else:  # HYBRID
            return await self._hybrid_parse(query)

    async def _hybrid_parse(self, query: str) -> Dict[str, Any]:
        """
        混合模式意图识别

        策略：
        1. 短查询（<10字符）：直接使用规则匹配
        2. 长查询：先尝试规则匹配，置信度高则使用规则结果
        3. 规则匹配置信度低：使用 LLM 分析
        """
        query_len = len(query.strip())

        # 策略1: 短查询直接使用规则匹配
        if query_len < self.short_query_threshold:
            logger.info(f"短查询 ({query_len}字符)，使用规则匹配")
            result = self.rule_parser.parse(query)
            result["recognition_method"] = "rule_based_short"
            return result

        # 策略2: 长查询先尝试规则匹配
        logger.info(f"长查询 ({query_len}字符)，先尝试规则匹配")
        rule_result = self.rule_parser.parse(query)

        # 策略3: 规则匹配置信度足够高，直接使用
        if rule_result["confidence"] >= self.confidence_threshold:
            logger.info(f"规则匹配置信度高 ({rule_result['confidence']:.2f})，使用规则结果")
            rule_result["recognition_method"] = "rule_based_confident"
            return rule_result

        # 策略4: 置信度低，使用 LLM 分析
        if self.enable_llm_fallback:
            logger.info(f"规则匹配置信度低 ({rule_result['confidence']:.2f})，使用 LLM 分析")
            llm_result = await self._llm_parse(query)
            llm_result["recognition_method"] = "llm_fallback"
            llm_result["rule_confidence"] = rule_result["confidence"]
            return llm_result
        else:
            logger.info("LLM 后备未启用，使用规则结果")
            rule_result["recognition_method"] = "rule_based_low_confidence"
            return rule_result

    async def _llm_parse(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 进行意图识别

        Args:
            query: 用户查询字符串

        Returns:
            解析结果字典
        """
        logger.info("开始 LLM 意图识别")

        try:
            # 延迟初始化 LLM 识别器
            if self._llm_intent_recognizer is None:
                self._llm_intent_recognizer = LLMIntentRecognizer()

            # 调用 LLM 进行意图识别
            result = await self._llm_intent_recognizer.recognize(query)

            logger.info(f"LLM 意图识别完成: {result}")
            return result

        except Exception as e:
            logger.error(f"LLM 意图识别失败: {e}，回退到规则匹配")
            # LLM 失败时回退到规则匹配
            rule_result = self.rule_parser.parse(query)
            rule_result["recognition_method"] = "rule_fallback"
            rule_result["llm_error"] = str(e)
            return rule_result

    def set_strategy(self, strategy: IntentRecognitionStrategy):
        """动态设置意图识别策略"""
        logger.info(f"切换意图识别策略: {self.strategy.value} -> {strategy.value}")
        self.strategy = strategy

    def get_stats(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        return {
            "strategy": self.strategy.value,
            "short_query_threshold": self.short_query_threshold,
            "confidence_threshold": self.confidence_threshold,
            "llm_fallback_enabled": self.enable_llm_fallback,
            "llm_initialized": self._llm_intent_recognizer is not None
        }


class LLMIntentRecognizer:
    """
    LLM 意图识别器
    使用大模型进行智能意图识别
    """

    def __init__(self):
        """初始化 LLM 意图识别器"""
        from openai import AsyncOpenAI
        from config.settings import settings

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=getattr(settings, 'OPENAI_API_BASE', None)
        )
        self.model = getattr(settings, 'MODEL_NAME', 'gpt-4')

        logger.info(f"LLM 意图识别器初始化完成 - 模型: {self.model}")

    async def recognize(self, query: str) -> Dict[str, Any]:
        """
        使用 LLM 识别查询意图

        Args:
            query: 用户查询字符串

        Returns:
            识别结果字典
        """
        # 构建提示词
        prompt = self._build_intent_prompt(query)

        try:
            # 调用 LLM
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的客服意图识别助手。请根据用户查询识别其意图。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.1,  # 低温度，提高一致性
                max_tokens=200
            )

            # 解析响应
            result_text = response.choices[0].message.content.strip()
            result = self._parse_llm_response(result_text, query)

            logger.info(f"LLM 意图识别成功: {result['intent']}")
            return result

        except Exception as e:
            logger.error(f"LLM 调用失败: {e}")
            raise

    def _build_intent_prompt(self, query: str) -> str:
        """
        构建意图识别提示词

        Args:
            query: 用户查询

        Returns:
            提示词字符串
        """
        return f"""请分析以下用户查询的意图。

用户查询: {query}

请识别：
1. 查询意图（从以下选项选择一个）：
   - order_status: 订单状态查询（订单、发货、支付、退款等）
   - logistics: 物流信息查询（物流、快递、配送、包裹等）
   - general: 一般查询（无法明确分类）

2. 订单编号（如果存在，提取 ORD 开头的编号）

3. 置信度（0.0-1.0，表示识别的置信程度）

请按以下 JSON 格式回复（不要添加其他内容）：
{{
    "intent": "order_status | logistics | general",
    "order_id": "订单编号或 null",
    "confidence": 0.95,
    "reasoning": "简短的理由说明"
}}
"""

    def _parse_llm_response(self, response: str, original_query: str) -> Dict[str, Any]:
        """
        解析 LLM 响应

        Args:
            response: LLM 返回的文本
            original_query: 原始查询

        Returns:
            解析结果字典
        """
        try:
            import json

            # 尝试提取 JSON（处理可能的 markdown 代码块）
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
            else:
                json_str = response

            data = json.loads(json_str)

            # 映射意图
            intent_mapping = {
                "order_status": QueryIntent.ORDER_STATUS,
                "logistics": QueryIntent.LOGISTICS,
                "general": QueryIntent.GENERAL
            }

            intent = intent_mapping.get(
                data.get("intent", "general"),
                QueryIntent.GENERAL
            )

            return {
                "original_query": original_query.strip(),
                "order_id": data.get("order_id") or self._extract_order_id(original_query),
                "intent": intent.value,
                "confidence": float(data.get("confidence", 0.8)),
                "normalized_query": original_query.strip(),
                "recognition_method": "llm_based",
                "llm_reasoning": data.get("reasoning", ""),
                "llm_raw_response": response
            }

        except json.JSONDecodeError as e:
            logger.error(f"解析 LLM 响应失败: {e}，响应内容: {response}")
            # 解析失败，返回默认结果
            return {
                "original_query": original_query.strip(),
                "order_id": self._extract_order_id(original_query),
                "intent": QueryIntent.GENERAL.value,
                "confidence": 0.5,
                "normalized_query": original_query.strip(),
                "recognition_method": "llm_based_fallback",
                "parse_error": str(e),
                "llm_raw_response": response
            }

    def _extract_order_id(self, query: str) -> Optional[str]:
        """从查询中提取订单 ID"""
        pattern = re.compile(r'[Oo][Rr][Dd]\d{3,}', re.IGNORECASE)
        match = pattern.search(query)
        return match.group().upper() if match else None


# 全局混合意图解析器实例
hybrid_intent_parser = HybridIntentParser(
    strategy=IntentRecognitionStrategy.HYBRID,
    short_query_threshold=10,
    confidence_threshold=0.7,
    enable_llm_fallback=True
)


# 便捷函数
async def parse_query_intent(query: str) -> Dict[str, Any]:
    """
    解析查询意图（使用混合解析器）

    Args:
        query: 用户查询字符串

    Returns:
        解析结果字典
    """
    return await hybrid_intent_parser.parse(query)

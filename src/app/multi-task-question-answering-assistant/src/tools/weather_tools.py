#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
天气工具模块
集成高德地图天气 API
"""

import requests
from typing import Dict, Any
from langchain_core.tools import tool

from src.core.logger import get_logger
from src.config.settings import settings

logger = get_logger(__name__)


@tool
def get_weather(city: str) -> str:
    """
    获取指定城市的实时天气信息

    Args:
        city: 城市名称，如"北京"、"上海"、"广州"

    Returns:
        str: 天气信息字符串，包含温度、天气状况、空气质量等

    Examples:
        >>> get_weather("北京")
        "北京今天晴天，温度 15-25℃，空气质量良好"
    """
    try:
        logger.info(f"查询天气: {city}")

        # 如果没有配置高德 API Key，返回模拟数据
        if not settings.AMAP_API_KEY or settings.AMAP_API_KEY == "your-amap-api-key-here":
            logger.warning(f"未配置高德API Key，使用模拟数据: {city}")
            return _get_mock_weather(city)

        # 调用高德天气 API
        # 高德天气 API 文档: https://lbs.amap.com/api/webservice/guide/api/weatherinfo
        base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "key": settings.AMAP_API_KEY,
            "city": city,
            "extensions": "base"  # base: 实况天气, all: 预报天气
        }

        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        # 解析响应
        if data.get("status") == "1" and data.get("lives"):
            live = data["lives"][0]
            weather_info = (
                f"{live['city']}今天{live['weather']}，"
                f"温度 {live['temperature']}℃，"
                f"湿度 {live['humidity']}%，"
                f"风向 {live['winddirection']}风，"
                f"风力 {live['windpower']}级，"
                f"空气质量: {live.get('humidity', '未知')}"
            )
            logger.info(f"天气查询成功: {city}")
            return weather_info
        else:
            logger.error(f"天气API返回错误: {data}")
            return f"抱歉，无法获取{city}的天气信息"

    except requests.exceptions.RequestException as e:
        logger.error(f"天气API请求失败: {e}")
        return _get_mock_weather(city)
    except Exception as e:
        logger.error(f"天气查询失败: {e}")
        return f"查询{city}天气时出错: {str(e)}"


def _get_mock_weather(city: str) -> str:
    """获取模拟天气数据（用于测试）"""
    mock_data = {
        "北京": "北京今天晴天，温度 15-25℃，空气质量良好",
        "上海": "上海今天多云，温度 18-28℃，湿度 65%",
        "广州": "广州今天阴天，温度 22-30℃，有微风",
        "深圳": "深圳今天小雨，温度 20-28℃，空气潮湿",
        "杭州": "杭州今天晴转多云，温度 16-26℃，空气质量优"
    }

    # 如果城市不在模拟数据中，返回通用数据
    return mock_data.get(
        city,
        f"{city}今天天气良好，温度适宜，适合出行"
    )


@tool
def get_weather_forecast(city: str, days: int = 3) -> str:
    """
    获取指定城市的天气预报

    Args:
        city: 城市名称
        days: 预报天数（1-4天），默认3天

    Returns:
        str: 天气预报信息
    """
    try:
        logger.info(f"查询天气预报: {city}, {days}天")

        if not settings.AMAP_API_KEY:
            return _get_mock_forecast(city, days)

        # 调用高德天气预报 API
        base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        params = {
            "key": settings.AMAP_API_KEY,
            "city": city,
            "extensions": "all"  # 获取预报数据
        }

        response = requests.get(base_url, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        if data.get("status") == "1" and data.get("forecasts"):
            forecast = data["forecasts"][0]
            casts = forecast["casts"][:days]

            result = f"{city}未来{days}天天气预报:\n"
            for cast in casts:
                result += (
                    f"- {cast['date']}: {cast['dayweather']}，"
                    f"温度 {cast['nighttemperature']}~{cast['daytemperature']}℃，"
                    f"风向 {cast['daywinddirection']}风\n"
                )

            logger.info(f"天气预报查询成功: {city}")
            return result.strip()
        else:
            logger.error(f"天气预报API返回错误: {data}")
            return f"抱歉，无法获取{city}的天气预报"

    except Exception as e:
        logger.error(f"天气预报查询失败: {e}")
        return _get_mock_forecast(city, days)


def _get_mock_forecast(city: str, days: int) -> str:
    """获取模拟天气预报"""
    from datetime import datetime, timedelta

    result = f"{city}未来{days}天天气预报（模拟数据）:\n"
    for i in range(days):
        date = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
        weather = ["晴天", "多云", "阴天", "小雨"][i % 4]
        result += f"- {date}: {weather}，温度 15-25℃\n"

    return result.strip()


if __name__ == "__main__":
    # 测试天气工具
    print("=" * 60)
    print("天气工具测试")
    print("=" * 60)

    print("\n1. 实时天气:")
    print(get_weather.invoke("北京"))
    print(get_weather.invoke("上海"))

    print("\n2. 天气预报:")
    print(get_weather_forecast.invoke({"city": "北京", "days": 3}))

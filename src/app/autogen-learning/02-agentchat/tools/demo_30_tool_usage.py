"""
Demo 30: 工具调用 - 完整的工具使用流程

本演示展示如何:
1. 定义复杂的工具
2. Agent 识别和使用工具
3. 参数传递和类型转换
4. 处理工具执行结果
5. 多工具组合和链式调用

运行方式:
    python demo_30_tool_usage.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 Python 函数工具基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/tools.html
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 这样可以直接运行脚本文件，而不需要从特定目录运行
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # 向上 3 级到 autogen-learning/
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio
import json
from typing import List, Dict, Any
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 工具定义 =====
def search_database(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """搜索数据库中的信息

    
    Args:
        query: 搜索关键词或查询语句
        limit: 返回结果的最大数量（默认 5）
    
    Returns:
        匹配的结果列表，每个结果是一个字典
    """
    # 模拟数据库搜索
    mock_db = [
        {"id": 1, "title": "Python 编程指南", "category": "编程", "content": "学习 Python 基础语法和高级特性"},
        {"id": 2, "title": "机器学习入门", "category": "AI", "content": "了解机器学习的基本概念和算法"},
        {"id": 3, "title": "数据结构教程", "category": "编程", "content": "掌握常用的数据结构"},
        {"id": 4, "title": "深度学习实践", "category": "AI", "content": "使用 TensorFlow 构建神经网络"},
        {"id": 5, "title": "Web 开发基础", "category": "开发", "content": "HTML、CSS 和 JavaScript 入门"},
    ]
    
    # 简单搜索匹配
    results = []
    for item in mock_db:
        if query.lower() in item["title"].lower() or \
           query.lower() in item["category"].lower():
            results.append(item)
            if len(results) >= limit:
                break
    
    return results


def get_weather(city: str, unit: str = "celsius") -> Dict[str, Any]:
    """获取指定城市的天气信息
    
    Args:
        city: 城市名称
        unit: 温度单位，'celsius' 或 'fahrenheit'（默认 celsius）
    
    Returns:
        包含天气信息的字典
    
    Raises:
        ValueError: 如果单位不支持
    """
    if unit not in ["celsius", "fahrenheit"]:
        raise ValueError("单位必须是 'celsius' 或 'fahrenheit'")
    
    # 模拟天气数据
    weather_data = {
        "city": city,
        "temperature": 25 if unit == "celsius" else 77,
        "unit": unit,
        "condition": "晴天",
        "humidity": 60,
        "wind_speed": 10
    }
    
    return weather_data


def calculate_distance(
    point1: List[float], 
    point2: List[float],
    unit: str = "km"
) -> float:
    """计算两个经纬度点之间的距离
    
    Args:
        point1: 第一个点的 [经度, 纬度]
        point2: 第二个点的 [经度, 纬度]
        unit: 距离单位，'km'（公里）或 'mi'（英里）（默认 km）
    
    Returns:
        两点之间的距离
    
    Raises:
        ValueError: 如果单位不支持或坐标格式错误
    """
    if unit not in ["km", "mi"]:
        raise ValueError("单位必须是 'km' 或 'mi'")
    
    if len(point1) != 2 or len(point2) != 2:
        raise ValueError("坐标必须是 [经度, 纬度] 格式")
    
    # 简化的距离计算（实际应该使用 Haversine 公式）
    lat1, lon1 = point1
    lat2, lon2 = point2
    
    distance = ((lat2 - lat1) ** 2 + (lon2 - lon1) ** 2) ** 0.5
    
    if unit == "mi":
        distance *= 0.621371  # 转换为英里
    
    return round(distance, 2)


def format_json(data: Dict[str, Any], indent: int = 2) -> str:
    """将字典格式化为 JSON 字符串
    
    Args:
        data: 要格式化的字典
        indent: 缩进空格数（默认 2）
    
    Returns:
        格式化后的 JSON 字符串
    """
    return json.dumps(data, ensure_ascii=False, indent=indent)


def analyze_text(text: str, analysis_type: str = "summary") -> Dict[str, Any]:
    """分析文本内容
    
    Args:
        text: 要分析的文本
        analysis_type: 分析类型，'summary'（摘要）、'keywords'（关键词）或 'sentiment'（情感）（默认 summary）
    
    Returns:
        分析结果字典
    
    Raises:
        ValueError: 如果分析类型不支持
    """
    if analysis_type not in ["summary", "keywords", "sentiment"]:
        raise ValueError("分析类型必须是 'summary'、'keywords' 或 'sentiment'")
    
    result = {"analysis_type": analysis_type}
    
    if analysis_type == "summary":
        result["summary"] = text[:100] + "..." if len(text) > 100 else text
    elif analysis_type == "keywords":
        # 简单的关键词提取
        words = text.split()
        result["keywords"] = list(set([word for word in words if len(word) > 3]))[:5]
    elif analysis_type == "sentiment":
        # 简单的情感分析
        positive_words = ["好", "优秀", "喜欢", "成功", "棒"]
        negative_words = ["差", "失败", "不喜欢", "糟糕", "坏"]
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in negative_words if word in text)
        
        if positive_count > negative_count:
            result["sentiment"] = "positive"
        elif negative_count > positive_count:
            result["sentiment"] = "negative"
        else:
            result["sentiment"] = "neutral"
    
    return result


# ===== 演示函数 =====
async def demo_database_search():
    """演示 1: 数据库搜索工具"""
    print("=" * 80)
    print("演示 1: 数据库搜索工具")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="search_agent",
        model_client=model_client,
        description="你是一个信息检索助手，可以搜索数据库找到相关信息。",
        tools=[search_database]
    )

    print("💬 可用工具:")
    print(f"   - search_database: 搜索数据库")
    print()

    task = "搜索关于 Python 和机器学习的资源，限制返回 3 条结果"
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 响应:")
    for message in result.messages:
        print(f"\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_weather_service():
    """演示 2: 天气服务工具"""
    print("=" * 80)
    print("演示 2: 天气服务工具")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="weather_agent",
        model_client=model_client,
        description="你是一个天气助手，可以查询城市的天气信息。",
        tools=[get_weather]
    )

    print("💬 可用工具:")
    print(f"   - get_weather: 获取天气信息")
    print()

    task = "查询北京和上海的天气，使用摄氏度"
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 响应:")
    for message in result.messages:
        print(f"\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_distance_calculation():
    """演示 3: 距离计算工具"""
    print("=" * 80)
    print("演示 3: 距离计算工具")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="geo_agent",
        model_client=model_client,
        description="你是一个地理助手，可以计算地点之间的距离。",
        tools=[calculate_distance]
    )

    print("💬 可用工具:")
    print(f"   - calculate_distance: 计算两点距离")
    print()

    task = "计算北京 (116.4074, 39.9042) 和上海 (121.4737, 31.2304) 之间的距离，使用公里"
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 响应:")
    for message in result.messages:
        print(f"\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_data_processing():
    """演示 4: 数据处理工具"""
    print("=" * 80)
    print("演示 4: 数据处理工具")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="data_agent",
        model_client=model_client,
        description="你是一个数据处理助手，可以格式化和分析数据。",
        tools=[format_json, analyze_text]
    )

    print("💬 可用工具:")
    print(f"   - format_json: 格式化 JSON")
    print(f"   - analyze_text: 分析文本")
    print()

    # 准备测试数据
    test_data = {
        "name": "AutoGen 学习项目",
        "version": "0.4.0",
        "features": ["多 Agent 协作", "工具支持", "灵活架构"],
        "status": "开发中"
    }

    task = f"""执行以下操作：
1. 将以下数据格式化为 JSON: {test_data}
2. 分析这段文本的情感: "这个 AutoGen 框架太棒了，学习体验很好！"
"""
    print(f"👤 任务:")
    print(task)
    print()

    result = await agent.run(task=task)

    print("📊 响应:")
    for message in result.messages:
        print(f"\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_tool_chain():
    """演示 5: 多工具链式调用"""
    print("=" * 80)
    print("演示 5: 多工具链式调用")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="comprehensive_agent",
        model_client=model_client,
        description="你是一个全面的助手，可以使用多种工具完成复杂任务。",
        tools=[search_database, get_weather, format_json, analyze_text]
    )

    print("💬 可用工具:")
    print(f"   - search_database: 搜索数据库")
    print(f"   - get_weather: 获取天气")
    print(f"   - format_json: 格式化 JSON")
    print(f"   - analyze_text: 分析文本")
    print()

    task = """执行以下任务链：
1. 搜索关于 AI 的教程
2. 获取北京的天气
3. 将搜索结果格式化为 JSON
4. 分析这段文本："机器学习是未来的方向"的关键词
"""
    print(f"👤 任务:")
    print(task)
    print()

    result = await agent.run(task=task)

    print("📊 响应:")
    for message in result.messages:
        print(f"\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


# ===== 主函数 =====
async def main():
    """主函数"""
    print("=" * 80)
    print("""
╔══════════════════════════════════════════════════════════════╗
║                                                                ║
║          AutoGen 0.4+ - 工具调用演示                ║
║           Complete Tool Usage Workflow                   ║
║                                                                ║
╚══════════════════════════════════════════════════════════════╝
    """)
    print("=" * 80 + "\n")

    try:
        # 检查 API Key
        settings = get_settings()
        if not settings.openai_api_key:
            print("❌ 错误: 未配置 OPENAI_API_KEY")
            print("   请在 .env 文件中设置 OPENAI_API_KEY")
            return

        # 演示 1: 数据库搜索
        await demo_database_search()

        # 演示 2: 天气服务
        await demo_weather_service()

        # 演示 3: 距离计算
        await demo_distance_calculation()

        # 演示 4: 数据处理
        await demo_data_processing()

        # 演示 5: 多工具链式调用
        await demo_multi_tool_chain()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 工具可以模拟外部服务和 API")
        print("  ✓ Agent 自动识别何时使用工具")
        print("  ✓ 参数由 Agent 根据工具定义自动构造")
        print("  ✓ 工具可以组合使用实现复杂任务")
        print("  ✓ 支持类型注解和参数验证")
        print()
        print("下一步:")
        print("  1. 查看 demo_31_code_execution.py 学习代码执行")
        print("  2. 查看 advanced/ 目录学习高级特性")
        print("  3. 查看 03-extensions/ 学习扩展功能")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
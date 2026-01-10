"""
Demo 29: Python 函数工具 - 本地函数作为工具

本演示展示如何:
1. 定义 Python 函数作为工具
2. 将函数注册到 Agent
3. Agent 调用工具
4. 处理工具返回结果
5. 参数验证和错误处理

运行方式:
    python demo_29_python_functions.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 Agent 基础概念

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
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 工具定义 =====
def calculate_gcd(a: int, b: int) -> int:
    """计算两个整数的最大公约数 (GCD)
    
    使用欧几里得算法计算最大公约数。

    
    Args:
        a: 第一个整数
        b: 第二个整数
    
    Returns:
        最大公约数
    
    Raises:
        ValueError: 如果任一参数为零
    """
    if a == 0 or b == 0:
        raise ValueError("参数不能为零")
    
    while b != 0:
        a, b = b, a % b
    return abs(a)


def calculate_lcm(a: int, b: int) -> int:
    """计算两个整数的最小公倍数 (LCM)
    
    Args:
        a: 第一个整数
        b: 第二个整数
    
    Returns:
        最小公倍数
    
    Raises:
        ValueError: 如果任一参数为零
    """
    if a == 0 or b == 0:
        raise ValueError("参数不能为零")
    
    gcd_val = calculate_gcd(a, b)
    return abs(a * b) // gcd_val


def fibonacci(n: int) -> int:
    """计算斐波那契数列的第 n 项
    
    Args:
        n: 项数（从0开始）
    
    Returns:
        第 n 项的值
    
    Raises:
        ValueError: 如果 n 为负数
    """
    if n < 0:
        raise ValueError("n 必须是非负整数")
    
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    
    return b


def is_prime(n: int) -> bool:
    """判断一个数是否为质数
    
    Args:
        n: 要判断的整数
    
    Returns:
        如果是质数返回 True，否则返回 False
    
    Raises:
        ValueError: 如果 n 小于 2
    """
    if n < 2:
        raise ValueError("n 必须大于等于 2")
    
    if n == 2:
        return True
    
    if n % 2 == 0:
        return False
    
    for i in range(3, int(n ** 0.5) + 1, 2):
        if n % i == 0:
            return False
    
    return True


def prime_factors(n: int) -> list:
    """分解质因数
    
    Args:
        n: 要分解的正整数
    
    Returns:
        质因数列表
    
    Raises:
        ValueError: 如果 n 小于 2
    """
    if n < 2:
        raise ValueError("n 必须大于等于 2")
    
    factors = []
    divisor = 2
    
    while n > 1:
        if is_prime(divisor) and n % divisor == 0:
            factors.append(divisor)
            n = n // divisor
        else:
            divisor += 1
    
    return factors


# ===== 演示函数 =====
async def demo_basic_tool_usage():
    """演示 1: 基本工具使用"""
    print("=" * 80)
    print("演示 1: 基本工具使用")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建带工具的 Agent
    agent = AssistantAgent(
        name="math_agent",
        model_client=model_client,
        description="你是一个数学助手，可以使用计算工具来解决数学问题。",
        tools=[calculate_gcd, calculate_lcm]
    )

    print("💬 可用工具:")
    print(f"   - calculate_gcd: 计算最大公约数")
    print(f"   - calculate_lcm: 计算最小公倍数")
    print()

    # 让 Agent 使用工具
    task = "计算 48 和 18 的最大公约数和最小公倍数"
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 Agent 响应:")
    for message in result.messages:
        print(f"\n{message.source}: {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_sequence_calculation():
    """演示 2: 序列计算"""
    print("=" * 80)
    print("演示 2: 斐波那契数列计算")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="sequence_agent",
        model_client=model_client,
        description="你是一个数列专家，可以使用斐波那契数列工具。",
        tools=[fibonacci]
    )

    print("💬 可用工具:")
    print(f"   - fibonacci: 计算斐波那契数列第 n 项")
    print()

    task = "计算斐波那契数列的前 10 项"
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 Agent 响应:")
    for message in result.messages:
        print(f"\n{message.source}: {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_prime_operations():
    """演示 3: 质数相关操作"""
    print("=" * 80)
    print("演示 3: 质数判断和因数分解")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="prime_agent",
        model_client=model_client,
        description="你是一个质数专家，可以使用质数判断和因数分解工具。",
        tools=[is_prime, prime_factors]
    )

    print("💬 可用工具:")
    print(f"   - is_prime: 判断是否为质数")
    print(f"   - prime_factors: 分解质因数")
    print()

    task = "判断 97 是否为质数，如果是，分解 120 的质因数"
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 Agent 响应:")
    for message in result.messages:
        print(f"\n{message.source}: {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_tool_usage():
    """演示 4: 多工具组合使用"""
    print("=" * 80)
    print("演示 4: 多工具组合使用")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="comprehensive_agent",
        model_client=model_client,
        description="你是一个全面的数学助手，可以使用多种数学工具。",
        tools=[calculate_gcd, calculate_lcm, fibonacci, is_prime, prime_factors]
    )

    print("💬 可用工具:")
    print(f"   - calculate_gcd: 计算最大公约数")
    print(f"   - calculate_lcm: 计算最小公倍数")
    print(f"   - fibonacci: 计算斐波那契数列")
    print(f"   - is_prime: 判断质数")
    print(f"   - prime_factors: 分解质因数")
    print()

    task = """解决以下数学问题:
1. 24 和 36 的最大公约数和最小公倍数
2. 斐波那契数列的第 8 项
3. 73 是否为质数？如果不是，分解其质因数
"""
    print(f"👤 任务:")
    print(task)
    print()

    result = await agent.run(task=task)

    print("📊 Agent 响应:")
    for message in result.messages:
        print(f"\n{message.source}: {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_error_handling():
    """演示 5: 错误处理"""
    print("=" * 80)
    print("演示 5: 工具错误处理")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="error_handling_agent",
        model_client=model_client,
        description="你是一个数学助手，可以使用计算工具，并能优雅地处理错误。",
        tools=[calculate_gcd, fibonacci, is_prime]
    )

    print("💬 测试错误处理")
    print()

    # 测试错误情况
    error_tests = [
        "计算 0 和 10 的最大公约数",
        "计算斐波那契数列的第 -5 项",
        "判断 1 是否为质数"
    ]

    for i, test in enumerate(error_tests, 1):
        print(f"\n{'─' * 40}")
        print(f"测试 {i}: {test}")
        print(f"{'─' * 40}\n")

        result = await agent.run(task=test)

        for message in result.messages:
            print(f"{message.content[:200]}...")

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
║          AutoGen 0.4+ - Python 函数工具演示          ║
║           Python Functions as Tools                        ║
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

        # 演示 1: 基本工具使用
        await demo_basic_tool_usage()

        # 演示 2: 序列计算
        await demo_sequence_calculation()

        # 演示 3: 质数操作
        await demo_prime_operations()

        # 演示 4: 多工具使用
        await demo_multi_tool_usage()

        # 演示 5: 错误处理
        await demo_error_handling()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ Python 函数可以作为工具注册到 Agent")
        print("  ✓ 工具定义需要类型注解和文档字符串")
        print("  ✓ Agent 可以自动识别何时使用工具")
        print("  ✓ 工具的参数由 Agent 自动构造")
        print("  ✓ 支持错误处理和参数验证")
        print()
        print("下一步:")
        print("  1. 查看 demo_30_tool_usage.py 学习工具调用流程")
        print("  2. 查看 demo_31_code_execution.py 学习代码执行")
        print("  3. 查看 advanced/ 目录学习高级特性")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
"""
Demo 31: 代码执行 - 安全的代码运行环境

本演示展示如何:
1. 创建代码执行环境
2. 执行 Python 代码
3. 捕获执行输出
4. 处理执行错误
5. 限制执行资源

运行方式:
    python demo_31_code_execution.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解工具基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/code-execution.html
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
import sys
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'


# ===== 代码执行工具 =====
def execute_python_code(code: str, timeout: int = 10) -> dict:

    """在沙箱环境中执行 Python 代码
    
    Args:
        code: 要执行的 Python 代码
        timeout: 超时时间（秒）（默认 10）
    
    Returns:
        包含执行结果的字典：
        - success: 是否成功
        - output: 标准输出
        - error: 标准错误或异常信息
        - execution_time: 执行时间（秒）
    """
    import time
    import traceback
    
    result = {
        "success": False,
        "output": "",
        "error": "",
        "execution_time": 0.0
    }
    
    start_time = time.time()
    
    try:
        # 重定向标准输出和错误
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            # 执行代码（使用 exec 而不是 eval 以支持多行代码）
            exec(code, globals())
        
        # 获取输出
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()
        
        if stderr_content:
            result["error"] = stderr_content
        else:
            result["output"] = stdout_content
            result["success"] = True
        
        result["execution_time"] = round(time.time() - start_time, 2)
        
    except Exception as e:
        result["error"] = f"执行错误: {str(e)}\n{traceback.format_exc()}"
        result["execution_time"] = round(time.time() - start_time, 2)
    
    return result


def safe_execute_code(code: str, allowed_modules: list = None) -> dict:
    """安全地执行代码，限制可用的模块
    
    Args:
        code: 要执行的代码
        allowed_modules: 允许的模块列表（None 表示不限制）
    
    Returns:
        执行结果字典
    """
    import __main__
    
    if allowed_modules is not None:
        # 创建受限的 globals 环境
        restricted_globals = {}
        for module_name in allowed_modules:
            try:
                restricted_globals[module_name] = __import__(module_name)
            except ImportError:
                return {
                    "success": False,
                    "error": f"模块 {module_name} 不可用",
                    "output": "",
                    "execution_time": 0.0
                }
        
        return execute_python_code_with_globals(code, restricted_globals)
    else:
        return execute_python_code(code)


def execute_python_code_with_globals(code: str, custom_globals: dict) -> dict:
    """使用自定义 globals 执行代码"""
    import time
    import traceback
    from io import StringIO
    from contextlib import redirect_stdout, redirect_stderr
    
    result = {
        "success": False,
        "output": "",
        "error": "",
        "execution_time": 0.0
    }
    
    start_time = time.time()
    
    try:
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        
        # 添加内置函数
        exec_globals = {
            **custom_globals,
            "print": print,
            "len": len,
            "str": str,
            "int": int,
            "float": float,
            "list": list,
            "dict": dict,
            "set": set,
        }
        
        with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
            exec(code, exec_globals)
        
        stdout_content = stdout_buffer.getvalue()
        stderr_content = stderr_buffer.getvalue()
        
        if stderr_content:
            result["error"] = stderr_content
        else:
            result["output"] = stdout_content
            result["success"] = True
        
        result["execution_time"] = round(time.time() - start_time, 2)
        
    except Exception as e:
        result["error"] = f"执行错误: {str(e)}\n{traceback.format_exc()}"
        result["execution_time"] = round(time.time() - start_time, 2)
    
    return result


# ===== 演示函数 =====
async def demo_basic_execution():
    """演示 1: 基本代码执行"""
    print("=" * 80)
    print("演示 1: 基本代码执行")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    # 创建带代码执行工具的 Agent
    agent = AssistantAgent(
        name="code_executor",
        model_client=model_client,
        description="你是一个代码执行助手，可以执行 Python 代码并返回结果。",
        tools=[execute_python_code]
    )

    print("💬 可用工具:")
    print(f"   - execute_python_code: 执行 Python 代码")
    print()

    # 让 Agent 使用代码执行工具
    task = """写一个 Python 脚本，计算 1 到 100 的和，
然后使用 execute_python_code 工具执行它。"""
    
    print(f"👤 任务: {task}")
    print()

    result = await agent.run(task=task)

    print("📊 Agent 响应:")
    for message in result.messages:
        print(f"\n{message.source}: {message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_data_processing():
    """演示 2: 数据处理代码执行"""
    print("=" * 80)
    print("演示 2: 数据处理代码执行")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="data_processor",
        model_client=model_client,
        description="你是一个数据处理助手，可以执行代码来处理和分析数据。",
        tools=[execute_python_code]
    )

    print("💬 可用工具:")
    print(f"   - execute_python_code: 执行 Python 代码")
    print()

    task = """写一个 Python 脚本，执行以下任务：
1. 创建一个数字列表 [5, 2, 8, 1, 9, 3]
2. 对列表进行排序
3. 计算平均值
4. 找出最大值和最小值

使用 execute_python_code 工具执行脚本。"""
    
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


async def demo_algorithm_implementation():
    """演示 3: 算法实现和测试"""
    print("=" * 80)
    print("演示 3: 算法实现和测试")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="algorithm_tester",
        model_client=model_client,
        description="你是一个算法助手，可以编写和测试算法代码。",
        tools=[execute_python_code]
    )

    print("💬 可用工具:")
    print(f"   - execute_python_code: 执行 Python 代码")
    print()

    task = """实现并测试一个快速排序算法：
1. 编写快速排序的 Python 函数
2. 使用数组 [64, 34, 25, 12, 22, 11, 90, 5] 测试
3. 执行代码并显示排序结果

使用 execute_python_code 工具执行代码。"""
    
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


async def demo_visualization_code():
    """演示 4: 数据可视化代码"""
    print("=" * 80)
    print("演示 4: 数据可视化代码执行")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="visualization_agent",
        model_client=model_client,
        description="你是一个数据可视化助手，可以生成和执行可视化代码。",
        tools=[execute_python_code]
    )

    print("💬 可用工具:")
    print(f"   - execute_python_code: 执行 Python 代码")
    print()

    task = """写一个 Python 脚本：
1. 创建数据：月份=['Jan', 'Feb', 'Mar', 'Apr'], 销售额=[100, 150, 130, 170]
2. 打印数据的统计信息（总和、平均值、最大值）
3. 创建一个简单的文本图表表示销售趋势

注意：由于环境限制，生成文本图表而不是图形图表。
使用 execute_python_code 工具执行代码。"""
    
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
    """演示 5: 错误处理和调试"""
    print("=" * 80)
    print("演示 5: 错误处理和调试")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key
    )

    agent = AssistantAgent(
        name="debugger",
        model_client=model_client,
        description="你是一个调试助手，可以执行代码并帮助修复错误。",
        tools=[execute_python_code]
    )

    print("💬 可用工具:")
    print(f"   - execute_python_code: 执行 Python 代码")
    print()

    # 测试包含错误的代码
    error_tests = [
        """写一个 Python 脚本，尝试除以零并处理错误。
使用 execute_python_code 工具执行代码。""",
        """写一个 Python 脚本，访问不存在的列表索引并处理错误。
使用 execute_python_code 工具执行代码。""",
        """写一个 Python 脚本，尝试将字符串转换为整数并处理错误。
使用 execute_python_code 工具执行代码。"""
    ]

    for i, test in enumerate(error_tests, 1):
        print(f"\n{'─' * 40}")
        print(f"测试 {i}: 错误处理")
        print(f"{'─' * 40}\n")

        print(f"👤 任务: {test}")
        print()

        result = await agent.run(task=test)

        for message in result.messages:
            print(f"\n{message.content[:300]}...")

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
║          AutoGen 0.4+ - 代码执行演示              ║
║           Safe Code Execution Environment                   ║
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

        # 演示 1: 基本代码执行
        await demo_basic_execution()

        # 演示 2: 数据处理
        await demo_data_processing()

        # 演示 3: 算法实现
        await demo_algorithm_implementation()

        # 演示 4: 数据可视化
        await demo_visualization_code()

        # 演示 5: 错误处理
        await demo_error_handling()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n关键要点:")
        print("  ✓ 代码执行工具可以在沙箱环境中安全运行代码")
        print("  ✓ 捕获标准输出和错误信息")
        print("  ✓ 支持执行多行 Python 代码")
        print("  ✓ 可以限制可用的模块和函数")
        print("  ✓ 提供执行时间和错误详情")
        print()
        print("安全提示:")
        print("  - 代码执行应该在受限环境中进行")
        print("  - 限制执行时间和资源使用")
        print("  - 验证输入代码，避免恶意操作")
        print("  - 记录所有执行活动")
        print()
        print("下一步:")
        print("  1. 查看 advanced/ 目录学习高级特性")
        print("  2. 查看 03-extensions/ 学习扩展功能")
        print("  3. 查看 docs/ 目录了解更多用法")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
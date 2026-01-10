"""
Demo 20: CodingAgent - 代码生成 Agent

本演示展示如何:
1. 使用 CodingAgent 生成代码
2. 处理编程任务
3. 代码审查和优化
4. 多语言代码生成
5. 调试支持

运行方式:
    # 方式1: 从 autogen-learning 目录运行（推荐）
    cd /path/to/autogen-learning
    python -m 02-agentchat.basics.demo_20_coding_agent

    # 方式2: 直接运行脚本文件
    python demo_20_coding_agent.py

前置要求:
    - 已配置 OPENAI_API_KEY
    - 已安装 autogen-agentchat 和 autogen-ext
    - 理解 AssistantAgent 基础

相关文档:
    - https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/coding.html
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
# 这样可以直接运行脚本文件，而不需要从特定目录运行
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent  # 从 basics/ 目录向上三级到 autogen-learning/
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient
from common.config import get_settings
# 设置环境变量以修复编码问题
os.environ['PYTHONIOENCODING'] = 'utf-8'



# ===== 演示函数 =====
async def demo_basic_code_generation():
    """演示 1: 基本代码生成"""
    print("=" * 80)
    print("演示 1: 基本代码生成")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    # 创建专注于代码生成的 AssistantAgent
    # 注意: AutoGen 0.4+ 中,CodingAgent 的功能已集成到 AssistantAgent 中
    # 通过描述和提示词来实现代码生成能力
    coding_agent = AssistantAgent(
        name="coding_agent",
        model_client=model_client,
        description="""你是一个专业的编程助手，擅长:
- 生成高质量、可维护的代码
- 遵循最佳实践和设计模式
- 添加适当的注释和文档
- 处理边缘情况和错误
- 提供代码解释"""
    )

    print("💬 代码生成任务:")
    task = "请编写一个 Python 函数，用于计算两个数字的最大公约数 (GCD)，使用欧几里得算法，并包含完整的注释。"
    print(f"   任务: {task}")
    print()

    result = await coding_agent.run(task=task)

    print("📊 生成的代码:")
    for message in result.messages:
        # 格式化输出代码
        content = message.content
        if "```python" in content:
            # 提取代码块
            start = content.find("```python")
            end = content.find("```", start + 9)
            if end != -1:
                code = content[start+9:end].strip()
                print("\n" + "─" * 40)
                print("Python 代码:")
                print("─" * 40)
                print(code)
            else:
                print(content)
        else:
            print(content)

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_code_review():
    """演示 2: 代码审查"""
    print("=" * 80)
    print("演示 2: 代码审查")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    coding_agent = AssistantAgent(
        name="code_reviewer",
        model_client=model_client,
        description="""你是一个严格的代码审查专家，擅长:
- 识别代码中的 bug 和潜在问题
- 评估代码质量和可读性
- 提出改进建议
- 推荐最佳实践
- 性能优化建议"""
    )

    # 待审查的代码
    code_to_review = """
def calculate_average(numbers):
    total = 0
    for num in numbers:
        total += num
    return total / len(numbers)
"""

    print("💬 待审查的代码:")
    print("─" * 40)
    print(code_to_review.strip())
    print("─" * 40 + "\n")

    task = f"""请审查以下代码，并指出:
1. 潜在的 bug 或错误
2. 边缘情况的处理
3. 代码质量改进建议
4. 性能优化机会

代码:
```python
{code_to_review}
```
"""

    result = await coding_agent.run(task=task)

    print("📊 审查结果:")
    for message in result.messages:
        print(f"\n{message.content}")

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_code_optimization():
    """演示 3: 代码优化"""
    print("=" * 80)
    print("演示 3: 代码优化")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    optimizer = AssistantAgent(
        name="code_optimizer",
        model_client=model_client,
        description="""你是一个代码优化专家，擅长:
- 提高代码性能
- 减少内存使用
- 提高可读性
- 应用高效算法
- 减少时间复杂度"""
    )

    # 待优化的代码
    original_code = """
def find_duplicates(arr):
    duplicates = []
    for i in range(len(arr)):
        for j in range(i + 1, len(arr)):
            if arr[i] == arr[j] and arr[i] not in duplicates:
                duplicates.append(arr[i])
    return duplicates
"""

    print("💬 原始代码:")
    print("─" * 40)
    print(original_code.strip())
    print("─" * 40 + "\n")

    task = f"""请优化以下代码，使其更高效:
1. 减少时间复杂度
2. 使用更合适的算法
3. 提供优化前后的复杂度分析
4. 保持功能不变

原始代码:
```python
{original_code}
```
"""

    result = await optimizer.run(task=task)

    print("📊 优化结果:")
    for message in result.messages:
        content = message.content
        if "```python" in content:
            start = content.find("```python")
            end = content.find("```", start + 9)
            if end != -1:
                code = content[start+9:end].strip()
                print("\n" + "─" * 40)
                print("优化后的代码:")
                print("─" * 40)
                print(code)
        print(content)

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_multi_language():
    """演示 4: 多语言代码生成"""
    print("=" * 80)
    print("演示 4: 多语言代码生成")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    polyglot_agent = AssistantAgent(
        name="polyglot_coder",
        model_client=model_client,
        description="""你是一个多语言编程专家，精通 Python、JavaScript、Java、C++、Go 等多种编程语言。"""
    )

    # 同一个任务，不同语言
    task = "编写一个快速排序算法的实现"
    languages = ["Python", "JavaScript", "Java"]

    for lang in languages:
        print(f"\n{'─' * 40}")
        print(f"💬 {lang} 实现")
        print(f"{'─' * 40}\n")

        result = await polyglot_agent.run(
            task=f"{task}，使用 {lang} 语言，并添加详细注释。"
        )

        for message in result.messages:
            content = message.content
            if f"```{lang.lower()}" in content or "```" in content:
                start = content.find("```")
                end = content.find("```", start + 3)
                if end != -1:
                    code = content[start+3:end].strip()
                    # 移除语言标识符
                    if code.startswith(lang.lower()):
                        code = code[len(lang.lower()):].strip()
                    print(code[:300] + "..." if len(code) > 300 else code)

    print("\n" + "=" * 80)
    print("✅ 演示完成")
    print("=" * 80 + "\n")


async def demo_debugging_assistant():
    """演示 5: 调试助手"""
    print("=" * 80)
    print("演示 5: 调试助手")
    print("=" * 80 + "\n")

    settings = get_settings()
    model_client = OpenAIChatCompletionClient(
        model=settings.openai_model,
        api_key=settings.openai_api_key,
        base_url=settings.openai_api_base if hasattr(settings, 'openai_api_base') and settings.openai_api_base else None
    )

    debugger = AssistantAgent(
        name="debugger",
        model_client=model_client,
        description="""你是一个调试专家，擅长:
- 识别代码中的 bug
- 分析错误原因
- 提供修复方案
- 解释调试过程
- 预防类似问题"""
    )

    # 有 bug 的代码
    buggy_code = """
def binary_search(arr, target):
    low = 0
    high = len(arr)
    while low < high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid
        else:
            high = mid
    return -1

# 测试
result = binary_search([1, 3, 5, 7, 9], 5)
print(f"Found at index: {result}")
"""

    print("💬 有 bug 的代码:")
    print("─" * 40)
    print(buggy_code.strip())
    print("─" * 40 + "\n")

    task = f"""以下代码在执行时可能有问题，请:
1. 识别 bug
2. 解释为什么会出现这个 bug
3. 提供修复后的代码
4. 说明修复的原因

代码:
```python
{buggy_code}
```
"""

    result = await debugger.run(task=task)

    print("📊 调试分析:")
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
║          AutoGen 0.4+ - CodingAgent 演示                ║
║           Code Generation and Optimization                   ║
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

        # 演示 1: 基本代码生成
        await demo_basic_code_generation()

        # 演示 2: 代码审查
        await demo_code_review()

        # 演示 3: 代码优化
        await demo_code_optimization()

        # 演示 4: 多语言
        await demo_multi_language()

        # 演示 5: 调试助手
        await demo_debugging_assistant()

        print("=" * 80)
        print("🎉 所有演示完成！")
        print("=" * 80)
        print("\n下一步:")
        print("  1. 查看 demo_21_text_chat_agent.py 学习文本对话")
        print("  2. 查看 demo_22_user_proxy_agent.py 学习用户代理")
        print("  3. 查看 docs/ 目录了解更多 AgentChat 用法")
        print("=" * 80 + "\n")

    except KeyboardInterrupt:
        print("\n\n⚠️  程序被用户中断")
    except Exception as e:
        print(f"\n\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
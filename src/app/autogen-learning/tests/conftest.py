"""pytest 配置文件

配置测试环境和 fixtures。
"""

import pytest
import asyncio
from autogen_core import SingleThreadedAgentRuntime


@pytest.fixture(scope="function")
async def runtime():
    """创建一个测试用的 Runtime 实例

    每个测试函数都会获得一个新的 Runtime 实例
    """
    rt = SingleThreadedAgentRuntime()
    yield rt
    # 清理：停止 Runtime
    rt.stop()


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环

    用于异步测试
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# 异步测试标记
pytest_plugins = ("pytest_asyncio",)

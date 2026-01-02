#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主应用入口
多任务问答助手 - CLI 交互界面
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.core.logger import logger
from src.config.settings import settings
from src.agents.qa_agent import create_qa_agent


class MultiTaskQASystem:
    """多任务问答系统主类"""

    def __init__(self):
        """初始化系统"""
        self.agent = None
        self.running = False

    async def initialize(self):
        """初始化系统组件"""
        try:
            logger.info("=" * 60)
            logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
            logger.info("=" * 60)

            # 创建 Agent
            self.agent = create_qa_agent()

            # 显示系统信息
            agent_info = self.agent.get_agent_info()
            logger.info(f"✅ 系统初始化成功")
            logger.info(f"   模型: {agent_info['model']}")
            logger.info(f"   工具: {', '.join(agent_info['tools'])}")
            logger.info(f"   调试模式: {settings.DEBUG}")

            self.running = True

        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            raise

    async def run(self):
        """运行主循环"""
        if not self.running:
            await self.initialize()

        print("\n" + "=" * 60)
        print(f"🤖 {settings.APP_NAME} v{settings.APP_VERSION}")
        print("=" * 60)
        print("\n我可以帮你:")
        print("  📌 查询天气（如：北京今天天气怎么样？）")
        print("  📌 搜索信息（如：搜索 LangChain 教程）")
        print("  📌 搜索新闻（如：最新的 AI 新闻）")
        print("  📌 回答问题（如：什么是机器学习？）")
        print("\n输入 'exit' 或 'quit' 退出")
        print("=" * 60 + "\n")

        while self.running:
            try:
                # 获取用户输入
                user_input = input("你: ").strip()

                # 检查退出命令
                if user_input.lower() in ['exit', 'quit', '退出', 'q']:
                    print("\n👋 再见！")
                    break

                # 跳过空输入
                if not user_input:
                    continue

                # 调用 Agent
                print("\n助手: ", end="", flush=True)
                response = await self.agent.ainvoke(user_input)

                # 显示响应
                output = response.get('output', '抱歉，我没有理解您的问题。')
                print(output)
                print()

            except KeyboardInterrupt:
                print("\n\n👋 再见！")
                break
            except Exception as e:
                logger.error(f"处理请求失败: {e}")
                print(f"\n❌ 出错了: {e}\n")

    async def close(self):
        """关闭系统"""
        logger.info("关闭系统...")
        self.running = False


async def main():
    """主函数"""
    system = MultiTaskQASystem()

    try:
        await system.run()
    except Exception as e:
        logger.error(f"系统错误: {e}")
        sys.exit(1)
    finally:
        await system.close()


if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主应用入口
多智能体客服系统 - CLI 交互界面
"""

import asyncio
import sys
import argparse
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.logger import get_logger
from config.settings import settings
from app.query_parser import query_parser
from agents.agent_manager import agent_manager

logger = get_logger(__name__)


class MultiAgentCustomerSystem:
    """多智能体客服系统主类"""

    def __init__(self):
        """初始化系统"""
        self.console = Console()
        self.running = False

    def display_welcome(self):
        """显示欢迎信息"""
        welcome_text = f"""
🤖 多智能体客服系统 v{settings.APP_VERSION}

系统能力：
  📦 订单状态查询
  🚚 物流信息查询
  🤖 多智能体协同工作
  📊 交互过程可视化
"""
        panel = Panel(welcome_text, title="欢迎使用", border_style="blue")
        self.console.print(panel)

    def display_agent_info(self):
        """显示智能体信息"""
        if agent_manager is None:
            self.console.print("[yellow]警告: 智能体管理器未初始化[/yellow]")
            return
            
        agent_info = agent_manager.get_agent_info()
        
        table = Table(title="智能体信息 (基于 AutoGen)")
        table.add_column("智能体", style="cyan")
        table.add_column("角色", style="magenta")
        table.add_column("描述", style="green")
        
        for agent_name, info in agent_info.items():
            if agent_name not in ['autogen_team_size', 'autogen_available', 'framework'] and isinstance(info, dict):
                table.add_row(
                    info.get('name', ''),
                    info.get('role', ''),
                    info.get('description', '')
                )
        
        self.console.print(table)

    def display_interactions(self, interactions):
        """显示交互过程"""
        if not interactions:
            return
        
        table = Table(title="智能体交互过程")
        table.add_column("序号", style="cyan")
        table.add_column("时间", style="yellow")
        table.add_column("发送者", style="magenta")
        table.add_column("接收者", style="magenta")
        table.add_column("类型", style="green")
        table.add_column("内容", style="white")
        
        for idx, interaction in enumerate(interactions, 1):
            table.add_row(
                str(idx),
                interaction.timestamp[:19],
                interaction.from_agent,
                interaction.to_agent,
                interaction.message_type,
                interaction.content[:50] + "..." if len(interaction.content) > 50 else interaction.content
            )
        
        self.console.print(table)

    def display_result(self, result):
        """显示查询结果"""
        # 显示回复
        response_panel = Panel(
            result.get('response', '无回复'),
            title="系统回复",
            border_style="green"
        )
        self.console.print(response_panel)
        
        # 显示处理时间
        self.console.print(f"\n⏱️  处理时间: {result.get('processing_time', 0):.2f} 秒\n")

    async def process_query(self, user_input):
        """
        处理用户查询
        
        Args:
            user_input: 用户输入字符串
        """
        try:
            if agent_manager is None:
                error_panel = Panel(
                    "智能体管理器未初始化，无法处理查询",
                    title="错误",
                    border_style="red"
                )
                self.console.print(error_panel)
                return
            
            # 解析查询
            parse_result = query_parser.parse(user_input)
            
            # 显示解析结果（调试模式）
            if settings.DEBUG:
                self.console.print(f"\n[调试] 订单编号: {parse_result['order_id']}")
                self.console.print(f"[调试] 查询意图: {parse_result['intent']}")
                self.console.print(f"[调试] 置信度: {parse_result['confidence']:.2f}\n")
            
            # 处理查询
            result = await agent_manager.process_query(
                parse_result['original_query'],
                parse_result['order_id']
            )
            
            # 显示结果
            self.display_result(result)
            
            # 显示交互过程
            if settings.VISUALIZE_AGENT_INTERACTION:
                self.display_interactions(result.get('interactions', []))
            
        except KeyboardInterrupt:
            raise
        except Exception as e:
            logger.error(f"处理查询失败: {e}")
            error_panel = Panel(
                f"处理查询时出错: {str(e)}",
                title="错误",
                border_style="red"
            )
            self.console.print(error_panel)

    async def interactive_mode(self):
        """交互式模式"""
        self.display_welcome()
        
        if agent_manager:
            self.display_agent_info()
        else:
            self.console.print("[red]错误: 智能体管理器未初始化，系统无法运行[/red]\n")
            return
        
        self.console.print("\n[blue]提示: 输入 'exit' 或 'quit' 退出\n")
        
        while True:
            try:
                # 获取用户输入
                user_input = self.console.input("\n[bold cyan]您:[/bold cyan] ")
                
                # 检查退出命令
                if user_input.lower() in ['exit', 'quit', '退出', 'q']:
                    self.console.print("\n[bold green]👋 再见！[/bold green]\n")
                    break
                
                # 跳过空输入
                if not user_input.strip():
                    continue
                
                # 处理查询
                await self.process_query(user_input)
                
            except KeyboardInterrupt:
                self.console.print("\n\n[bold green]👋 再见！[/bold green]\n")
                break
            except Exception as e:
                logger.error(f"处理请求失败: {e}")
                self.console.print(f"\n[bold red]❌ 出错了: {e}[/bold red]\n")

    async def command_mode(self, query):
        """命令行模式"""
        self.display_welcome()
        
        try:
            await self.process_query(query)
        except Exception as e:
            logger.error(f"处理请求失败: {e}")
            self.console.print(f"\n[bold red]❌ 出错了: {e}[/bold red]\n")
            sys.exit(1)

    async def run(self, query: str = None):
        """
        运行系统
        
        Args:
            query: 命令行查询（如果提供，使用命令行模式）
        """
        self.running = True
        
        try:
            if query:
                # 命令行模式
                await self.command_mode(query)
            else:
                # 交互式模式
                await self.interactive_mode()
                
        finally:
            self.running = False


def main():
    """主函数"""
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(
        description="多智能体客服系统 - 基于AutoGen框架"
    )
    parser.add_argument(
        '-q', '--query',
        type=str,
        default=None,
        help='要查询的问题（命令行模式）'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式'
    )
    
    args = parser.parse_args()
    
    # 覆盖调试模式设置
    if args.debug:
        settings.DEBUG = True
        settings.LOG_LEVEL = "DEBUG"
    
    # 创建系统实例
    system = MultiAgentCustomerSystem()
    
    # 运行系统
    asyncio.run(system.run(args.query))


if __name__ == "__main__":
    main()
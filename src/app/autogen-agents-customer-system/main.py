#!/usr/bin/env python3
"""
AutoGen 多智能体客服系统 - 主入口
基于 AutoGen 框架实现多智能体协同处理客服问题

功能特点：
- 订单状态查询 (Agent A)
- 物流信息检查 (Agent B)  
- 结果汇总回复 (Agent C)
- 自动重试机制
- 详细的Agent交互过程显示

使用方法:
    python main.py --query "我的订单ORD001为什么还没发货？"  # 单次查询
"""

import sys
import os
import asyncio
from pathlib import Path
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box
import re

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入项目模块
from api.fastapi_server import start_server
from config.settings import settings
from core.logger import setup_logger
from tools.api_client import APIClient
from agents.autogen_agents import create_autogen_agents, create_group_chat

# 设置日志
logger = setup_logger(__name__)
console = Console()

# 加载环境变量
load_dotenv()

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description="AutoGen 多智能体客服系统")
    parser.add_argument("--query", type=str, help="客户查询内容")
    parser.add_argument("--order_id", type=str, default="ORD001", help="订单ID")
    parser.add_argument("--use_autogen", action="store_true", help="使用AutoGen智能体处理查询")
    return parser.parse_args()

async def start_services():
    """启动模拟服务"""
    # 使用子进程启动FastAPI服务器
    import subprocess
    import sys
    
    cmd = [sys.executable, "-m", "uvicorn", "api.fastapi_server:app", "--host", "127.0.0.1", "--port", "8000"]
    process = subprocess.Popen(cmd, cwd=str(project_root))
    
    # 等待服务启动
    await asyncio.sleep(3)
    logger.info("FastAPI模拟服务已启动")
    return process

def display_query_results(order_info: dict, logistics_info: dict):
    """展示查询成功的结果"""
    console.print("\n" + "="*80)
    console.print("[bold green]🎉 查询结果展示 🎉[/bold green]", justify="center")
    console.print("="*80)
    
    # 创建订单信息表格
    if order_info and "error" not in order_info:
        order_table = Table(title="📦 订单信息", box=box.ROUNDED, border_style="blue")
        order_table.add_column("项目", style="cyan", no_wrap=True)
        order_table.add_column("详情", style="white")
        
        order_table.add_row("订单ID", order_info.get('order_id', 'N/A'))
        order_table.add_row("订单状态", f"[bold green]{order_info.get('status', 'N/A')}[/bold green]")
        order_table.add_row("客户姓名", order_info.get('customer_name', 'N/A'))
        order_table.add_row("订单金额", f"[bold yellow]¥{order_info.get('total_amount', 0)}[/bold yellow]")
        order_table.add_row("商品列表", ', '.join(order_info.get('items', [])))
        order_table.add_row("收货地址", order_info.get('shipping_address', 'N/A'))
        order_table.add_row("创建时间", order_info.get('created_at', 'N/A'))
        order_table.add_row("更新时间", order_info.get('updated_at', 'N/A'))
        
        console.print(order_table)
        console.print()
        
        # 记录订单查询成功日志
        logger.info(f"✅ 订单查询成功展示 - 订单ID: {order_info.get('order_id')}, 状态: {order_info.get('status')}")
    else:
        error_msg = order_info.get('error', '未知错误') if order_info else '订单查询失败'
        console.print(Panel(f"[bold red]❌ 订单查询失败: {error_msg}[/bold red]", border_style="red"))
        logger.warning(f"订单查询失败: {error_msg}")
    
    # 创建物流信息表格
    if logistics_info and "error" not in logistics_info:
        logistics_table = Table(title="🚚 物流信息", box=box.ROUNDED, border_style="green")
        logistics_table.add_column("项目", style="cyan", no_wrap=True)
        logistics_table.add_column("详情", style="white")
        
        logistics_table.add_row("物流单号", logistics_info.get('tracking_number', '暂未分配'))
        logistics_table.add_row("物流状态", f"[bold green]{logistics_info.get('status', 'N/A')}[/bold green]")
        logistics_table.add_row("当前位置", logistics_info.get('current_location', 'N/A'))
        logistics_table.add_row("承运商", logistics_info.get('carrier', 'N/A'))
        logistics_table.add_row("预计送达", f"[bold yellow]{logistics_info.get('estimated_delivery', '未确定')}[/bold yellow]")
        
        # 显示物流轨迹
        if logistics_info.get('tracking_history'):
            tracking_text = ""
            for record in logistics_info['tracking_history']:
                tracking_text += f"{record.get('time', 'N/A')} - {record.get('location', 'N/A')}: {record.get('status', 'N/A')}\n"
            logistics_table.add_row("物流轨迹", tracking_text.strip())
        
        console.print(logistics_table)
        console.print()
        
        # 记录物流查询成功日志
        logger.info(f"✅ 物流查询成功展示 - 单号: {logistics_info.get('tracking_number')}, 状态: {logistics_info.get('status')}")
    else:
        error_msg = logistics_info.get('error', '未知错误') if logistics_info else '物流查询失败'
        console.print(Panel(f"[bold yellow]⚠️ 物流查询失败: {error_msg}[/bold yellow]", border_style="yellow"))
        logger.warning(f"物流查询失败: {error_msg}")
    
    console.print("="*80)
    console.print("[bold green]✨ 查询结果展示完成 ✨[/bold green]", justify="center")
    console.print("="*80 + "\n")

async def run_autogen_query(query: str):
    """使用AutoGen智能体处理查询"""
    console.print(Panel(f"[bold cyan]🤖 启动AutoGen智能体处理查询[/bold cyan]", border_style="cyan"))
    console.print(Panel(f"[bold green]客户查询:[/bold green] {query}", border_style="green"))
    
    try:
        # 创建智能体
        agents_dict = create_autogen_agents()
        manager = create_group_chat(agents_dict)
        
        # 启动群组聊天
        console.print(Panel("[bold yellow]🚀 开始智能体协作处理...[/bold yellow]", border_style="yellow"))
        
        result = agents_dict["user_proxy"].initiate_chat(
            manager,
            message=query,
            max_turns=10
        )
        
        console.print(Panel("[bold green]✅ AutoGen智能体处理完成[/bold green]", border_style="green"))
        return result
        
    except Exception as e:
        error_msg = f"AutoGen智能体处理失败: {str(e)}"
        console.print(Panel(f"[bold red]❌ {error_msg}[/bold red]", border_style="red"))
        logger.error(error_msg)
        return None

async def run_query_test(query: str, order_id: str = "ORD001"):
    """运行查询测试"""
    console.print(Panel(f"[bold green]客户查询:[/bold green] {query}", border_style="green"))
    
    # 创建API客户端
    client = APIClient()
    
    # 测试订单查询
    console.print(Panel("[bold blue]测试订单查询API[/bold blue]", border_style="blue"))
    order_info = await client.get_order_status(order_id)
    
    # 测试物流查询
    console.print(Panel("[bold blue]测试物流查询API[/bold blue]", border_style="blue"))
    logistics_info = await client.get_logistics_info(order_id)
    
    # 展示查询成功的结果
    display_query_results(order_info, logistics_info)
    
    console.print(Panel("[bold green]✅ 测试完成[/bold green]", border_style="green"))
    
    return order_info, logistics_info

async def main_async():
    """异步主函数"""
    args = parse_arguments()
    
    # 如果没有提供查询，使用默认查询
    query = args.query or f"我的订单{args.order_id}为什么还没发货？"
    
    # 从查询中提取订单ID，如果提取失败则使用命令行参数或默认值
    extracted_order_id = extract_order_id_from_query(query) if args.query else None
    order_id = extracted_order_id or args.order_id or "ORD001"
    
    logger.info(f"📋 最终使用的订单ID: {order_id}")
    
    # 启动模拟服务
    server_process = await start_services()
    
    try:
        if args.use_autogen:
            # 使用AutoGen智能体处理查询
            await run_autogen_query(query)
        else:
            # 运行基础查询测试
            await run_query_test(query, order_id)
    finally:
        # 关闭服务器进程
        if server_process:
            server_process.terminate()
            logger.info("FastAPI模拟服务已关闭")
    
    return 0

def extract_order_id_from_query(query: str) -> str:
    """
    从查询文本中提取订单ID
    
    Args:
        query: 用户查询文本
        
    Returns:
        str: 提取到的订单ID，如果没有找到则返回默认值ORD001
    """
    # 使用正则表达式匹配订单ID模式 (ORD + 数字)
    pattern = r'ORD\d+'
    match = re.search(pattern, query, re.IGNORECASE)
    
    if match:
        order_id = match.group().upper()
        logger.info(f"🔍 从查询中提取到订单ID: {order_id}")
        return order_id
    else:
        logger.warning(f"⚠️ 未能从查询中提取订单ID，使用默认值: ORD001")
        return "ORD001"

def main():
    """主函数"""
    return asyncio.run(main_async())

if __name__ == "__main__":
    # 运行方法：python main.py --query  "我的订单ORD001为什么还没发货？"
    sys.exit(main())
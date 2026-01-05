"""
API客户端工具
用于调用FastAPI模拟服务的接口
"""
import asyncio
import json
import logging
from typing import Dict, Any, Optional
from utils.retry import create_retry_decorator, RetryableHTTPClient
import httpx
from rich.console import Console
from rich.panel import Panel

logger = logging.getLogger(__name__)
console = Console()

class APIClient:
    """
    API客户端类
    负责与FastAPI模拟服务通信
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url
        self.client = RetryableHTTPClient(
            base_url=base_url,
            timeout=30.0
        )
    
    @create_retry_decorator(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        获取订单状态信息
        Agent A 使用此方法查询订单状态
        
        Args:
            order_id: 订单ID
            
        Returns:
            订单状态信息字典
        """
        try:
            logger.info(f"🔍 查询订单状态: {order_id}")
            console.print(Panel(f"[bold blue]正在查询订单[/bold blue]: {order_id}", border_style="blue"))
            
            response = await self.client.get(f"/api/orders/{order_id}")
            order_data = response.json()
            
            logger.info(f"✅ 订单查询成功: {order_id} -> {order_data['status']}")
            console.print(Panel(f"[bold green]订单查询成功[/bold green]: {order_id}", border_style="green"))
            return order_data
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"❌ 订单不存在: {order_id}")
                console.print(Panel(f"[bold yellow]订单不存在[/bold yellow]: {order_id}", border_style="yellow"))
                return {"error": f"订单 {order_id} 不存在"}
            elif e.response.status_code == 500:
                logger.warning(f"⚠️ 订单服务暂时不可用: {order_id} -> HTTP {e.response.status_code}")
                console.print(Panel(f"[bold yellow]订单服务暂时不可用[/bold yellow]: {order_id} -> HTTP {e.response.status_code}", border_style="yellow"))
                return {"error": f"订单服务暂时不可用，请稍后再试", "order_id": order_id, "status": "service_unavailable"}
            else:
                logger.error(f"❌ 订单查询失败: {order_id} -> HTTP {e.response.status_code}")
                console.print(Panel(f"[bold red]订单查询失败[/bold red]: {order_id} -> HTTP {e.response.status_code}", border_style="red"))
                return {"error": f"订单查询失败: HTTP {e.response.status_code}", "order_id": order_id, "status": "query_failed"}
        except Exception as e:
            logger.error(f"❌ 订单查询异常: {order_id} -> {str(e)}")
            console.print(Panel(f"[bold red]订单查询异常[/bold red]: {order_id} -> {str(e)}", border_style="red"))
            return {"error": f"订单查询异常: {str(e)}", "order_id": order_id, "status": "exception"}
    
    @create_retry_decorator(max_attempts=3, min_wait=1.0, max_wait=10.0)
    async def get_logistics_info(self, order_id: str) -> Dict[str, Any]:
        """
        获取物流信息
        Agent B 使用此方法查询物流信息
        
        Args:
            order_id: 订单ID
            
        Returns:
            物流信息字典
        """
        try:
            logger.info(f"🚚 查询物流信息: {order_id}")
            console.print(Panel(f"[bold blue]正在查询物流[/bold blue]: {order_id}", border_style="blue"))
            
            response = await self.client.get(f"/api/logistics/{order_id}")
            logistics_data = response.json()
            
            logger.info(f"✅ 物流查询成功: {order_id}")
            console.print(Panel(f"[bold green]物流查询成功[/bold green]: {order_id}", border_style="green"))
            return logistics_data
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"❌ 物流信息不存在: {order_id}")
                console.print(Panel(f"[bold yellow]物流信息不存在[/bold yellow]: {order_id}", border_style="yellow"))
                return {"error": f"订单 {order_id} 的物流信息不存在"}
            elif e.response.status_code == 500:
                logger.warning(f"⚠️ 物流服务暂时不可用: {order_id} -> HTTP {e.response.status_code}")
                console.print(Panel(f"[bold yellow]物流服务暂时不可用[/bold yellow]: {order_id} -> HTTP {e.response.status_code}", border_style="yellow"))
                return {"error": f"物流服务暂时不可用，请稍后再试", "order_id": order_id, "status": "service_unavailable"}
            else:
                logger.error(f"❌ 物流查询失败: {order_id} -> HTTP {e.response.status_code}")
                console.print(Panel(f"[bold red]物流查询失败[/bold red]: {order_id} -> HTTP {e.response.status_code}", border_style="red"))
                return {"error": f"物流查询失败: HTTP {e.response.status_code}", "order_id": order_id, "status": "query_failed"}
        except Exception as e:
            logger.error(f"❌ 物流查询异常: {order_id} -> {str(e)}")
            console.print(Panel(f"[bold red]物流查询异常[/bold red]: {order_id} -> {str(e)}", border_style="red"))
            return {"error": f"物流查询异常: {str(e)}", "order_id": order_id, "status": "exception"}
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            服务是否健康
        """
        try:
            logger.info("🔍 执行健康检查")
            
            response = await self.client.get("/health")
            health_data = response.json()
            
            is_healthy = health_data.get("status") == "healthy"
            if is_healthy:
                logger.info("✅ 服务健康检查通过")
            else:
                logger.warning("⚠️  服务健康检查失败")
            return is_healthy
            
        except Exception as e:
            logger.error(f"❌ 健康检查失败: {str(e)}")
            return False
    
    async def close(self):
        """关闭客户端连接"""
        await self.client.close()
        logger.info("API客户端关闭")
    
    async def __aenter__(self):
        """异步上下文管理器进入"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


# 全局API客户端实例
api_client = APIClient()
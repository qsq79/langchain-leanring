#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模拟数据存储模块
提供订单和物流的模拟数据
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


class MockOrderData:
    """模拟订单数据存储"""

    def __init__(self):
        """初始化模拟订单数据"""
        self.orders = {
            "ORD001": {
                "order_id": "ORD001",
                "created_time": "2024-01-01T10:00:00Z",
                "order_status": "待发货",
                "payment_status": "已支付",
                "shipping_status": "未发货",
                "total_amount": 299.00,
                "items": [
                    {"product_id": "P001", "name": "商品A", "quantity": 1, "price": 199.00},
                    {"product_id": "P002", "name": "商品B", "quantity": 1, "price": 100.00}
                ]
            },
            "ORD002": {
                "order_id": "ORD002",
                "created_time": "2024-01-02T14:30:00Z",
                "order_status": "已发货",
                "payment_status": "已支付",
                "shipping_status": "运输中",
                "total_amount": 599.00,
                "items": [
                    {"product_id": "P003", "name": "商品C", "quantity": 2, "price": 299.50}
                ]
            },
            "ORD003": {
                "order_id": "ORD003",
                "created_time": "2024-01-03T09:15:00Z",
                "order_status": "已完成",
                "payment_status": "已支付",
                "shipping_status": "已送达",
                "total_amount": 899.00,
                "items": [
                    {"product_id": "P004", "name": "商品D", "quantity": 1, "price": 899.00}
                ]
            },
            "ORD004": {
                "order_id": "ORD004",
                "created_time": "2024-01-04T16:45:00Z",
                "order_status": "已取消",
                "payment_status": "未支付",
                "shipping_status": "未发货",
                "total_amount": 399.00,
                "items": [
                    {"product_id": "P005", "name": "商品E", "quantity": 1, "price": 399.00}
                ]
            },
            "ORD005": {
                "order_id": "ORD005",
                "created_time": (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "order_status": "支付中",
                "payment_status": "待支付",
                "shipping_status": "未发货",
                "total_amount": 1599.00,
                "items": [
                    {"product_id": "P006", "name": "商品F", "quantity": 1, "price": 1599.00}
                ]
            }
        }

    def get_order(self, order_id: str) -> Optional[Dict]:
        """获取订单信息"""
        return self.orders.get(order_id)

    def get_all_orders(self) -> List[Dict]:
        """获取所有订单信息"""
        return list(self.orders.values())


class MockLogisticsData:
    """模拟物流数据存储"""

    def __init__(self):
        """初始化模拟物流数据"""
        self.logistics = {
            "ORD001": {
                "order_id": "ORD001",
                "logistics_status": "未发货",
                "current_location": "上海仓库",
                "estimated_delivery": None,
                "tracking_history": [
                    {
                        "time": "2024-01-01T10:00:00Z",
                        "status": "订单创建",
                        "location": "上海仓库"
                    }
                ]
            },
            "ORD002": {
                "order_id": "ORD002",
                "logistics_status": "运输中",
                "current_location": "北京转运中心",
                "estimated_delivery": "3天",
                "tracking_history": [
                    {
                        "time": "2024-01-02T14:30:00Z",
                        "status": "订单创建",
                        "location": "上海仓库"
                    },
                    {
                        "time": "2024-01-02T18:00:00Z",
                        "status": "已发货",
                        "location": "上海仓库"
                    },
                    {
                        "time": "2024-01-03T08:00:00Z",
                        "status": "运输中",
                        "location": "北京转运中心"
                    }
                ]
            },
            "ORD003": {
                "order_id": "ORD003",
                "logistics_status": "已送达",
                "current_location": "北京市朝阳区XX路XX号",
                "estimated_delivery": "已送达",
                "tracking_history": [
                    {
                        "time": "2024-01-03T09:15:00Z",
                        "status": "订单创建",
                        "location": "广州仓库"
                    },
                    {
                        "time": "2024-01-03T15:00:00Z",
                        "status": "已发货",
                        "location": "广州仓库"
                    },
                    {
                        "time": "2024-01-04T10:00:00Z",
                        "status": "运输中",
                        "location": "上海转运中心"
                    },
                    {
                        "time": "2024-01-04T16:00:00Z",
                        "status": "派送中",
                        "location": "北京市朝阳区配送站"
                    },
                    {
                        "time": "2024-01-04T14:30:00Z",
                        "status": "已送达",
                        "location": "北京市朝阳区XX路XX号"
                    }
                ]
            },
            "ORD004": {
                "order_id": "ORD004",
                "logistics_status": "已取消",
                "current_location": None,
                "estimated_delivery": None,
                "tracking_history": [
                    {
                        "time": "2024-01-04T16:45:00Z",
                        "status": "订单创建",
                        "location": "深圳仓库"
                    },
                    {
                        "time": "2024-01-04T17:00:00Z",
                        "status": "已取消",
                        "location": "深圳仓库"
                    }
                ]
            },
            "ORD005": {
                "order_id": "ORD005",
                "logistics_status": "待发货",
                "current_location": "杭州仓库",
                "estimated_delivery": None,
                "tracking_history": [
                    {
                        "time": (datetime.now() - timedelta(hours=5)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "status": "订单创建",
                        "location": "杭州仓库"
                    }
                ]
            }
        }

    def get_logistics(self, order_id: str) -> Optional[Dict]:
        """获取物流信息"""
        return self.logistics.get(order_id)

    def get_all_logistics(self) -> List[Dict]:
        """获取所有物流信息"""
        return list(self.logistics.values())


# 全局实例
order_data = MockOrderData()
logistics_data = MockLogisticsData()
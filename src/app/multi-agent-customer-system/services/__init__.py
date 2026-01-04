#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
服务层模块
"""

from services.mock_data import order_data, logistics_data
from services.retry_mechanism import RetryMechanism, global_retry_mechanism

__all__ = ['order_data', 'logistics_data', 'RetryMechanism', 'global_retry_mechanism']
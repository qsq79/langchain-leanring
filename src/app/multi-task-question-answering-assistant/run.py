#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目主入口 - 放在项目根目录
从项目根目录运行所有模块
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 导入并运行主应用
from src.app.main import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())

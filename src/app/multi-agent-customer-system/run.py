#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目主入口 - 放在项目根目录
从项目根目录运行所有模块

使用方法：
    python3 run.py          # CLI 交互模式
    python3 run.py -q "查询内容"  # 命令行查询模式
"""

import os
import subprocess
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    # 使用 -m 模式运行，确保相对导入正常工作
    # 传递所有命令行参数
    cmd = [sys.executable, "-m", "app.main"] + sys.argv[1:]
    
    # 执行命令
    result = subprocess.run(cmd, cwd=str(project_root))
    
    # 退出并返回相同的退出码
    sys.exit(result.returncode)
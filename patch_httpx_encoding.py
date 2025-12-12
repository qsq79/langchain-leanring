#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修复httpx编码问题
"""

import os
import sys
import importlib

# 设置环境变量
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['LC_ALL'] = 'en_US.UTF-8'
os.environ['LANG'] = 'en_US.UTF-8'

# 在导入任何库之前，先修复httpx的编码问题
def patch_httpx():
    """修复httpx的编码问题"""
    try:
        import httpx._models
        # 保存原始函数
        original_normalize = httpx._models._normalize_header_value
        
        def patched_normalize_header_value(value, encoding=None):
            """修复的头部值标准化函数，强制使用UTF-8"""
            if isinstance(value, str):
                # 检查是否包含非ASCII字符
                try:
                    # 尝试ASCII编码
                    value.encode('ascii')
                    return original_normalize(value, encoding)
                except UnicodeEncodeError:
                    # 如果ASCII编码失败，强制使用UTF-8
                    return value.encode('utf-8')
            else:
                return original_normalize(value, encoding)
        
        # 应用补丁
        httpx._models._normalize_header_value = patched_normalize_header_value
        print("已成功修复httpx编码问题")
        return True
    except Exception as e:
        print(f"修复httpx时出错: {e}")
        return False

# 在导入前应用补丁
patch_httpx()

# 现在导入配置
project_root = os.path.abspath(os.path.join(os.path.dirname('/Users/quan/langchain-leanring/src/app/langchain1.x/01-models/basic_example.py'), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.app.utils.config_loader import setup_openai_config
setup_openai_config()

# 测试OpenAI连接
def test_openai():
    """测试OpenAI连接"""
    try:
        from langchain_openai import OpenAI
        
        # 创建LLM实例
        llm = OpenAI(
            model="gpt-3.5-turbo-instruct",
            temperature=0.7,
            max_tokens=20
        )
        
        # 测试简单英文提示
        print("测试OpenAI连接...")
        response = llm.invoke("Hello")
        print(f"成功: {response}")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_openai()
    
    if success:
        print("\n=== httpx编码问题已修复! ===")
        print("现在可以运行原始脚本了")
    else:
        print("\n=== 需要进一步调试 ===")
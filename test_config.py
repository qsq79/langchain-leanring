#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试环境变量配置是否正常工作
"""

import os
import sys
from pathlib import Path

# 添加utils目录到系统路径
sys.path.append(str(Path(__file__).parent))

from utils.config_loader import setup_all_configs, get_optional_env, get_required_env

def test_config_loader():
    """测试配置加载器"""
    print("=== 测试配置加载器 ===")
    
    # 测试加载环境变量
    try:
        setup_all_configs()
        print("✅ 成功加载环境变量配置")
    except Exception as e:
        print(f"❌ 加载环境变量配置失败: {e}")
        return False
    
    # 测试获取环境变量
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        print(f"✅ OPENAI_API_KEY 已设置 (前缀: {api_key[:10]}...)")
    else:
        print("❌ OPENAI_API_KEY 未设置")
        return False
    
    serpapi_key = os.getenv("SERPAPI_API_KEY")
    if serpapi_key:
        print(f"✅ SERPAPI_API_KEY 已设置 (前缀: {serpapi_key[:10]}...)")
    else:
        print("⚠️ SERPAPI_API_KEY 未设置 (仅在需要搜索功能时使用)")
    
    return True

def test_simple_example():
    """测试简单的LLM示例"""
    print("\n=== 测试简单LLM示例 ===")
    
    try:
        from langchain_openai import OpenAI
        
        # 创建LLM实例
        llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0.7)
        
        # 简单测试
        prompt = "请用一句话介绍Python。"
        response = llm.invoke(prompt)
        
        print(f"✅ LLM调用成功")
        print(f"提示: {prompt}")
        print(f"回答: {response}")
        return True
        
    except Exception as e:
        print(f"❌ LLM调用失败: {e}")
        return False

def test_chat_example():
    """测试Chat模型示例"""
    print("\n=== 测试Chat模型示例 ===")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        # 创建Chat模型实例
        chat_model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
        
        # 简单测试
        messages = [HumanMessage(content="什么是LangChain？")]
        response = chat_model.invoke(messages)
        
        print(f"✅ Chat模型调用成功")
        print(f"提示: {messages[0].content}")
        print(f"回答: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ Chat模型调用失败: {e}")
        return False

def main():
    """主函数"""
    print("LangChain 环境变量配置测试")
    print("=" * 50)
    
    # 检查.env文件是否存在
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env文件存在于: {env_file.absolute()}")
    else:
        print(f"❌ .env文件不存在")
        print(f"请复制.env.example为.env并填入您的API密钥")
        return False
    
    # 测试配置加载
    if not test_config_loader():
        return False
    
    # 测试LLM调用
    if not test_simple_example():
        return False
    
    # 测试Chat模型调用
    if not test_chat_example():
        return False
    
    print("\n" + "=" * 50)
    print("✅ 所有测试通过！环境变量配置正常工作。")
    print("\n使用说明:")
    print("1. 复制.env.example为.env文件")
    print("2. 在.env文件中填入您的实际API密钥")
    print("3. 运行任何示例文件时，会自动加载环境变量")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
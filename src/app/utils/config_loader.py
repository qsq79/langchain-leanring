#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置加载工具
用于统一加载和管理环境变量配置
"""

import os
from typing import Dict, Any, Optional

def load_env(env_file: str = ".env") -> None:
    """
    从.env文件加载环境变量
    
    Args:
        env_file: 环境变量文件路径，默认为.env
    """
    try:
        # 检查python-dotenv是否可用
        try:
            from dotenv import load_dotenv
            load_dotenv(env_file, verbose=True)
            print(f"已从 {env_file} 文件加载环境变量")
        except ImportError:
            print("警告: 未安装python-dotenv包，尝试手动加载.env文件")
            _load_env_manually(env_file)
    except Exception as e:
        print(f"加载环境变量失败: {e}")

def _load_env_manually(env_file: str) -> None:
    """
    手动加载.env文件（不依赖python-dotenv）
    
    Args:
        env_file: 环境变量文件路径
    """
    if not os.path.exists(env_file):
        print(f"环境变量文件 {env_file} 不存在")
        return
    
    with open(env_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 移除各种引号（包括中文引号）
                if (value.startswith('"') and value.endswith('"')) or \
                   (value.startswith("'") and value.endswith("'")) or \
                   (value.startswith('"') and value.endswith('"')):  # 中文引号
                    value = value[1:-1]
                
                # 清理可能的额外空格
                value = value.strip()
                
                os.environ[key] = value

def get_required_env(key: str) -> str:
    """
    获取必需的环境变量，如果不存在则抛出异常
    
    Args:
        key: 环境变量名
        
    Returns:
        环境变量值
        
    Raises:
        ValueError: 当环境变量不存在时
    """
    value = os.getenv(key)
    if value is None or value == "":
        raise ValueError(f"必需的环境变量 {key} 未设置或为空")
    return value

def get_optional_env(key: str, default: Any = None) -> Any:
    """
    获取可选的环境变量，如果不存在则返回默认值
    
    Args:
        key: 环境变量名
        default: 默认值
        
    Returns:
        环境变量值或默认值
    """
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value

def setup_openai_config() -> None:
    """
    设置OpenAI配置，从环境变量中读取API密钥和基础URL
    """
    try:
        # 直接读取.env文件并解析，确保正确处理引号
        env_file = "src/.env"
        if not os.path.exists(env_file):
            # 尝试其他路径
            alternative_paths = [
                ".env",
                os.path.join(os.path.dirname(__file__), "..", "..", ".env")
            ]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    env_file = alt_path
                    break
        
        if os.path.exists(env_file):
            print(f"直接读取 {env_file} 文件...")
            
            # 手动解析.env文件，确保正确处理引号
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                        
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()
                        
                        # 移除各种引号（包括中文引号）
                        if (value.startswith('"') and value.endswith('"')) or \
                           (value.startswith("'") and value.endswith("'")) or \
                           (value.startswith('"') and value.endswith('"')):  # 中文引号
                            value = value[1:-1]
                        
                        # 清理可能的额外空格
                        value = value.strip()
                        
                        # 设置环境变量
                        os.environ[key] = value
                        
                        # 输出调试信息（对于API密钥只显示部分内容）
                        if key == "OPENAI_API_KEY":
                            print(f"已设置 {key}: {value[:10]}...{value[-4:] if len(value) > 4 else ''} (长度: {len(value)})")
                        else:
                            print(f"已设置 {key}: {value}")
        else:
            print(f"未找到环境变量文件: {env_file}")
            
            # 尝试使用dotenv作为后备
            try:
                from dotenv import load_dotenv
                load_dotenv()
                print("使用python-dotenv加载环境变量")
            except ImportError:
                print("未安装python-dotenv，无法加载环境变量")
        
        # 验证必需的环境变量
        api_key = get_required_env("OPENAI_API_KEY")
        
        # 获取可选的基础URL
        api_base = get_optional_env("OPENAI_API_BASE")
        if api_base:
            os.environ["OPENAI_API_BASE"] = api_base
            
        # 获取可选的组织ID
        organization = get_optional_env("OPENAI_ORGANIZATION")
        if organization:
            os.environ["OPENAI_ORGANIZATION"] = organization
            
        print("OpenAI配置已加载")
    except ValueError as e:
        print(f"OpenAI配置失败: {e}")
        print("请确保已在.env文件中设置了OPENAI_API_KEY")

def setup_serpapi_config() -> None:
    """
    设置SerpAPI配置，从环境变量中读取API密钥
    """
    try:
        api_key = get_required_env("SERPAPI_API_KEY")
        os.environ["SERPAPI_API_KEY"] = api_key
        print("SerpAPI配置已加载")
    except ValueError as e:
        print(f"SerpAPI配置失败: {e}")
        print("请确保已在.env文件中设置了SERPAPI_API_KEY")

def setup_all_configs() -> None:
    """
    设置所有API配置
    """
    # 首先加载环境变量文件
    load_env()
    
    # 设置各服务配置
    setup_openai_config()
    setup_serpapi_config()

# 为了向后兼容，提供一个简单的函数
def init_config(env_file: str = ".env") -> None:
    """
    初始化配置（简化函数名，便于调用）
    
    Args:
        env_file: 环境变量文件路径
    """
    setup_all_configs()

if __name__ == "__main__":
    # 测试配置加载
    print("测试配置加载...")
    setup_all_configs()
    
    # 打印加载的配置（隐藏敏感信息）
    print("\n已加载的配置:")
    print(f"OPENAI_API_KEY: {'*' * 10}{os.getenv('OPENAI_API_KEY', '未设置')[-4:] if os.getenv('OPENAI_API_KEY') else '未设置'}")
    print(f"OPENAI_API_BASE: {os.getenv('OPENAI_API_BASE', '未设置')}")
    print(f"OPENAI_ORGANIZATION: {os.getenv('OPENAI_ORGANIZATION', '未设置')}")
    print(f"SERPAPI_API_KEY: {'*' * 10}{os.getenv('SERPAPI_API_KEY', '未设置')[-4:] if os.getenv('SERPAPI_API_KEY') else '未设置'}")
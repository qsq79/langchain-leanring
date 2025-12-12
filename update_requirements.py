#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用于更新根目录requirements.txt文件的辅助脚本
"""

import os
import sys
import re
from datetime import datetime

def add_dependency(dep_name, version="", category="其他", description=""):
    """
    添加新依赖到requirements.txt文件
    
    参数:
        dep_name: 依赖名称
        version: 版本要求，如 ">=1.0.0" 或 "==1.0.0"，留空则不指定版本
        category: 依赖类别，用于注释
        description: 依赖描述
    """
    req_file = 'src/app/langchain1.x/requirements.txt'
    
    # 检查文件是否存在
    if not os.path.exists(req_file):
        print(f"错误：找不到文件 {req_file}")
        return False
    
    # 检查依赖是否已存在
    with open(req_file, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = content.split('\n')
        
    # 检查依赖是否已存在
    existing = False
    for line in lines:
        if not line.strip() or line.strip().startswith('#'):
            continue
        if dep_name.lower() in line.lower():
            print(f"⚠️ 依赖 {dep_name} 可能已存在于requirements.txt中:")
            print(f"   {line}")
            choice = input("是否要更新此依赖? (y/n): ").lower()
            if choice != 'y':
                return False
            existing = True
            # 找到要替换的行
            for i, line in enumerate(lines):
                if not line.strip() or line.strip().startswith('#'):
                    continue
                if dep_name.lower() in line.lower():
                    # 更新该行
                    version_part = f"{version}" if version else ""
                    new_line = f"{dep_name}{version_part}"
                    lines[i] = new_line
                    break
            break
    
    # 如果依赖不存在，则添加新依赖
    if not existing:
        # 找到要插入的位置（在最后一个分类注释之后）
        insert_index = -1
        for i, line in enumerate(lines):
            if "以下为各模块新增依赖" in line:
                insert_index = i - 1
                break
        
        if insert_index == -1:
            insert_index = len(lines) - 1
        
        # 构建新依赖行
        version_part = f"{version}" if version else ""
        new_dep = f"{dep_name}{version_part}"
        new_comment = f"# {category} - {description}" if description else f"# {category}"
        
        # 插入新依赖和注释
        lines.insert(insert_index, new_comment)
        lines.insert(insert_index + 1, new_dep)
        lines.insert(insert_index + 2, "")
    
    # 写回文件
    with open(req_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ {'更新' if existing else '添加'}依赖 {dep_name}{version} 成功")
    return True

def show_categories():
    """显示常见的依赖类别"""
    print("\n常见的依赖类别:")
    categories = [
        "LangChain核心依赖", "数值计算和科学计算", "HTTP请求和异步支持", 
        "数据处理", "向量数据库和搜索", "数据存储", "网页解析", 
        "缓存支持", "环境变量管理", "开发测试工具"
    ]
    for i, cat in enumerate(categories, 1):
        print(f"{i}. {cat}")
    print("11. 其他")

def main():
    print("=== 依赖更新工具 ===\n")
    
    if len(sys.argv) < 2:
        print("用法:")
        print(f"  python3 {sys.argv[0]} <依赖名称> [版本要求] [类别] [描述]")
        print("\n示例:")
        print(f"  python3 {sys.argv[0]} pinecone-client >=2.2.0 向量数据库和搜索 Pinecone向量数据库支持")
        print(f"  python3 {sys.argv[0]} tqdm \"进度条\"")
        
        # 交互式添加
        print("\n或者使用交互式模式:")
        dep_name = input("请输入依赖名称: ").strip()
        if not dep_name:
            return
        
        version = input("请输入版本要求 (如>=1.0.0，留空则不指定): ").strip()
        show_categories()
        cat_choice = input("请选择类别 (1-11): ").strip()
        description = input("请输入依赖描述: ").strip()
        
        categories = [
            "LangChain核心依赖", "数值计算和科学计算", "HTTP请求和异步支持", 
            "数据处理", "向量数据库和搜索", "数据存储", "网页解析", 
            "缓存支持", "环境变量管理", "开发测试工具", "其他"
        ]
        
        try:
            category = categories[int(cat_choice) - 1]
        except:
            category = "其他"
        
        add_dependency(dep_name, version, category, description)
    else:
        dep_name = sys.argv[1]
        version = sys.argv[2] if len(sys.argv) > 2 else ""
        category = sys.argv[3] if len(sys.argv) > 3 else "其他"
        description = sys.argv[4] if len(sys.argv) > 4 else ""
        
        add_dependency(dep_name, version, category, description)

if __name__ == "__main__":
    main()
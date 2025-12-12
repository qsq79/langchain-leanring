#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证requirements.txt是否包含所有子目录的依赖
"""

import os
import re
from collections import defaultdict

def parse_requirements(file_path):
    """解析requirements.txt文件，返回依赖字典"""
    dependencies = {}
    if not os.path.exists(file_path):
        return dependencies
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            # 跳过注释和空行
            if not line or line.startswith('#'):
                continue
            
            # 解析依赖和版本
            if '>=' in line:
                name, version = line.split('>=', 1)
                dependencies[name.strip()] = version.strip()
            elif '==' in line:
                name, version = line.split('==', 1)
                dependencies[name.strip()] = version.strip()
            else:
                # 没有版本号的依赖
                dependencies[line.strip()] = ""
    
    return dependencies

def get_all_subdir_requirements():
    """获取所有子目录的requirements.txt文件"""
    subdirs = []
    # 新的项目结构下，子目录在src/app/langchain1.x/下
    base_dir = os.path.join(os.getcwd(), 'src/app/langchain1.x')
    
    if not os.path.exists(base_dir):
        print(f"错误：找不到目录 {base_dir}")
        return subdirs
    
    # 查找所有包含requirements.txt的子目录
    for item in os.listdir(base_dir):
        item_path = os.path.join(base_dir, item)
        if os.path.isdir(item_path) and re.match(r'^\d{2}-', item):  # 匹配数字开头的目录
            req_file = os.path.join(item_path, 'requirements.txt')
            if os.path.exists(req_file):
                subdirs.append(item)
    
    return subdirs

def main():
    print("正在验证requirements.txt文件整合...")
    
    # 解析根目录的requirements.txt（现在位于src/app/langchain1.x/）
    req_file_path = 'src/app/langchain1.x/requirements.txt'
    if not os.path.exists(req_file_path):
        print(f"错误：找不到文件 {req_file_path}")
        return
    
    root_requirements = parse_requirements(req_file_path)
    print(f"根目录requirements.txt包含 {len(root_requirements)} 个依赖")
    
    # 获取所有子目录
    subdirs = get_all_subdir_requirements()
    print(f"找到 {len(subdirs)} 个包含requirements.txt的子目录")
    
    # 检查每个子目录的依赖
    all_deps = defaultdict(set)  # 依赖名 -> {版本1, 版本2, ...}
    missing_deps = set()
    
    for subdir in subdirs:
        subdir_req_file = os.path.join('src/app/langchain1.x', subdir, 'requirements.txt')
        subdir_deps = parse_requirements(subdir_req_file)
        
        print(f"\n{subdir}/requirements.txt 包含 {len(subdir_deps)} 个依赖:")
        
        for dep, version in subdir_deps.items():
            all_deps[dep].add(version)
            
            if dep not in root_requirements:
                missing_deps.add(dep)
                print(f"  ❌ 缺失依赖: {dep}>={version}")
            elif version and root_requirements[dep] != version:
                print(f"  ⚠️ 版本差异: {dep} (子目录:>={version}, 根目录:>={root_requirements[dep]})")
            else:
                print(f"  ✓ 已包含: {dep}>={version}")
    
    # 报告结果
    print("\n=== 验证结果 ===")
    if missing_deps:
        print(f"❌ 发现 {len(missing_deps)} 个缺失的依赖:")
        for dep in sorted(missing_deps):
            print(f"  - {dep}")
        print("\n请将这些依赖添加到根目录的requirements.txt文件中")
    else:
        print("✅ 所有子目录的依赖都已包含在根目录的requirements.txt中")
    
    # 检查版本冲突
    version_conflicts = {dep: versions for dep, versions in all_deps.items() 
                         if len(versions) > 1 and dep in root_requirements}
    
    if version_conflicts:
        print(f"\n⚠️ 发现 {len(version_conflicts)} 个存在版本冲突的依赖:")
        for dep, versions in version_conflicts.items():
            print(f"  - {dep}: {', '.join(sorted(versions))}")

if __name__ == "__main__":
    main()
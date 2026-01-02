#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 .env 文件中的 Unicode 字符
解决 API Key 和 URL 中的特殊引号问题
"""

import re
from pathlib import Path


def fix_unicode_in_file(file_path: str):
    """修复文件中的 Unicode 字符"""

    if not Path(file_path).exists():
        print(f"❌ 文件不存在: {file_path}")
        return False

    # 读取文件
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换 Unicode 字符
    replacements = {
        '\u201c': '"',  # 左双引号
        '\u201d': '"',  # 右双引号
        '\u201e': '"',  # 双低引号
        '\u201f': '"',  # 双高倒引号
        '\u00ab': '"',  # 左双角引号
        '\u00bb': '"',  # 右双角引号
        '\u0060': "'",  # 重音
        '\u00b4': "'",  # 锐音
        '\u2018': "'",  # 左单引号
        '\u2019': "'",  # 右单引号
    }

    original_content = content
    for unicode_char, ascii_char in replacements.items():
        content = content.replace(unicode_char, ascii_char)

    # 如果有变化，写回文件
    if content != original_content:
        # 创建备份
        backup_path = f"{file_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(original_content)
        print(f"✅ 已创建备份: {backup_path}")

        # 写入修复后的内容
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"✅ 已修复文件: {file_path}")
        print(f"   移除了 Unicode 字符")
        return True
    else:
        print(f"✅ 文件正常，无需修复: {file_path}")
        return True


if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("修复 .env 文件中的 Unicode 字符")
    print("=" * 60)
    print()

    # 默认修复 .env 文件
    env_file = ".env"

    if len(sys.argv) > 1:
        env_file = sys.argv[1]

    print(f"正在检查: {env_file}")
    print()

    fix_unicode_in_file(env_file)

    print()
    print("=" * 60)
    print("完成！")
    print("=" * 60)

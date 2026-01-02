# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## 项目概述

这是一个LangChain 1.x核心组件学习项目，包含8个主要组件的示例代码和文档，旨在帮助开发者学习和掌握LangChain框架。

## 关键运行命令

- 安装依赖: `pip install -r src/app/langchain1.x/requirements.txt`
- 运行单个示例: `python src/app/langchain1.x/[组件文件夹]/basic_example.py`
- 环境配置: 必须创建 `.env` 文件并设置 `OPENAI_API_KEY`
- 配置加载测试: `python src/app/utils/config_loader.py`

## 项目特定约定

### 环境变量管理
- 使用自定义配置加载器 `src/app/utils/config_loader.py` 而非直接使用 python-dotenv
- 支持手动解析 `.env` 文件，无需依赖外部库
- `.env` 文件应位于 `src/` 目录而非项目根目录
- 配置加载器包含引号处理和特殊字符清理功能

### 代码结构
- 每个组件都有独立的文件夹，包含 basic_example.py 和 advanced_example.py
- 所有示例文件都使用绝对路径导入配置加载器
- 项目根目录通过动态计算添加到 sys.path
- 示例代码包含错误处理和API密钥验证逻辑

### 导入约定
```python
# 标准项目路径设置模式
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 配置加载器导入
from src.app.utils.config_loader import setup_openai_config
setup_openai_config()
```

### 依赖管理
- 所有依赖已整合到 `src/app/langchain1.x/requirements.txt`
- 子目录中的 requirements.txt 文件保留用于文档参考
- 使用版本范围而非固定版本以增强兼容性

### 测试和运行
- 无标准测试框架配置，示例即测试
- 运行前必须验证API密钥配置
- 某些示例需要额外的环境变量如 SERPAPI_API_KEY

## 常见问题解决

1. **编码问题**: 所有示例已包含UTF-8编码修复和httpx补丁
2. **API密钥问题**: 使用配置加载器的 get_required_env() 函数验证
3. **导入错误**: 确保从项目根目录运行脚本
4. **模型可用性**: 某些示例包含回退机制，当特定模型不可用时自动切换

## 组件特定注意事项

- Models组件: 包含LLM、Chat Model和Embeddings的完整示例
- Chains组件: 展示各种链式组合模式
- Agents组件: 需要额外的API密钥如SERPAPI_API_KEY
- 所有组件都包含错误处理和重试逻辑

## 开发建议

- 运行任何示例前先执行配置加载器测试
- 对于新组件，遵循现有的文件夹结构和命名约定
- 添加新依赖时更新根目录的requirements.txt并添加分类注释
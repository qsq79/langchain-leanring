# LangChain 项目环境变量配置指南

本项目已优化为使用环境变量来管理API密钥和其他敏感配置，以提高安全性和可维护性。

## 📁 文件说明

- `.env.example` - 环境变量配置模板（包含所有可能的配置项）
- `.env` - 实际的环境变量文件（需要创建，不会被Git跟踪）
- `utils/config_loader.py` - 配置加载工具函数
- `.gitignore` - Git忽略规则（确保敏感信息不被提交）

## 🚀 快速开始

### 1. 创建环境变量文件

复制环境变量模板为实际的配置文件：

```bash
cp .env.example .env
```

### 2. 编辑环境变量文件

打开 `.env` 文件，填入您的实际API密钥：

```env
# OpenAI API密钥（必需）
OPENAI_API_KEY=your-actual-openai-api-key-here

# OpenAI API基础URL（可选，用于代理或自定义端点）
# OPENAI_API_BASE=https://api.openai.com/v1

# SerpAPI密钥（可选，用于搜索功能）
SERPAPI_API_KEY=your-actual-serpapi-key-here

# OpenAI组织ID（可选）
# OPENAI_ORGANIZATION=your-org-id

# 代理设置（可选）
# OPENAI_PROXY=http://your-proxy:port
```

### 3. 测试配置

运行测试脚本验证配置是否正确：

```bash
python test_config.py
```

如果所有测试通过，您就可以安全地运行任何示例文件了。

## 🔧 配置加载器功能

### 基本用法

```python
# 导入配置加载器
from utils.config_loader import setup_openai_config, setup_all_configs

# 仅设置OpenAI配置
setup_openai_config()

# 设置所有API配置（包括SerpAPI等）
setup_all_configs()
```

### 高级用法

```python
from utils.config_loader import get_required_env, get_optional_env, load_env

# 手动加载.env文件
load_env()

# 获取必需的环境变量（如果不存在会抛出异常）
api_key = get_required_env("OPENAI_API_KEY")

# 获取可选的环境变量（如果不存在返回默认值）
organization = get_optional_env("OPENAI_ORGANIZATION", "default-org")
```

## 📁 项目结构

```
langchain-learning/
├── .env.example          # 环境变量模板
├── .env                 # 实际的环境变量（需创建）
├── .gitignore           # Git忽略规则
├── utils/
│   └── config_loader.py  # 配置加载工具
├── test_config.py        # 配置测试脚本
├── 01-models/          # Models示例
├── 02-prompts/         # Prompts示例
├── 03-chains/          # Chains示例
├── 04-indexes/         # Indexes示例
├── 05-memory/          # Memory示例
├── 06-agents/          # Agents示例
├── 07-tools/          # Tools示例
└── 08-callbacks/       # Callbacks示例
```

## 🔒 安全注意事项

1. **不要提交.env文件**：`.env` 文件已在 `.gitignore` 中，确保不会被提交到版本控制系统。

2. **定期轮换密钥**：定期更新您的API密钥以提高安全性。

3. **限制访问权限**：确保 `.env` 文件仅对必要用户可读。

4. **使用环境变量**：在生产环境中，可以直接使用系统环境变量而不需要 `.env` 文件。

## 🔧 故障排除

### 问题：找不到API密钥

```
ValueError: 必需的环境变量 OPENAI_API_KEY 未设置或为空
```

**解决方案**：
1. 确保已创建 `.env` 文件
2. 检查 `.env` 文件中是否正确设置了 `OPENAI_API_KEY`
3. 确保没有额外的空格或特殊字符

### 问题：python-dotenv未安装

```
ModuleNotFoundError: No module named 'dotenv'
```

**解决方案**：
1. 安装python-dotenv：`pip install python-dotenv`
2. 或者，我们的配置加载器支持不依赖python-dotenv的加载方式

### 问题：相对导入错误

```
ModuleNotFoundError: No module named 'utils.config_loader'
```

**解决方案**：
1. 确保从项目根目录运行脚本
2. 或者将项目根目录添加到Python路径：`export PYTHONPATH=$PYTHONPATH:$(pwd)`

## 📝 更新历史

- **v1.0** - 初始版本，支持OpenAI和SerpAPI环境变量
- 添加了自动配置加载功能
- 提供了完整的测试和文档

## 🤝 贡献

如果您需要添加新的API配置项：

1. 在 `.env.example` 中添加新的配置项
2. 在 `utils/config_loader.py` 中添加对应的加载函数
3. 更新此文档说明新配置项的用途

## 📞 支持

如有问题或建议，请查看项目README或创建Issue。
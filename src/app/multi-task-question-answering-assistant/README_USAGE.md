# 多任务问答助手 - 快速开始指南

> **基于 LangChain 1.x + Python 3.10+**

## 📦 项目结构

```
multi-task-question-answering-assistant/
├── src/
│   ├── config/           # 配置管理
│   │   └── settings.py
│   ├── core/             # 核心模块
│   │   └── logger.py
│   ├── tools/            # 工具定义
│   │   ├── weather_tools.py
│   │   └── search_tools.py
│   ├── agents/           # Agent 实现
│   │   └── qa_agent.py
│   ├── api/              # Web API
│   │   └── server.py
│   └── app/              # 主应用
│       └── main.py
├── logs/                 # 日志目录
├── .env.example          # 环境变量示例
├── requirements.txt      # 依赖列表
├── start.sh             # 启动脚本
└── README.md            # 本文件
```

## 🚀 快速开始

### 1. 环境准备

**系统要求**:
- Python >= 3.10 (必须)
- 推荐使用 Python 3.11

**检查 Python 版本**:
```bash
python3 --version
# 输出应该是: Python 3.10.x 或更高
```

### 2. 配置环境

**复制配置文件**:
```bash
cp .env.example .env
```

**编辑 `.env` 文件，添加你的 API 密钥**:
```bash
# 必需：OpenAI API 密钥
OPENAI_API_KEY=your-actual-openai-api-key

# 可选：如果使用代理
OPENAI_API_BASE=https://your-proxy-url/v1

# 可选：Tavily 搜索 API
TAVILY_API_KEY=your-tavily-api-key

# 可选：高德地图 API
AMAP_API_KEY=your-amap-api-key
```

### 3. 安装依赖

**方式1: 使用启动脚本（推荐）**
```bash
./start.sh
```

**方式2: 手动安装**
```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 运行应用

**方式1: 使用启动脚本（推荐）**
```bash
./start.sh
# 然后选择模式:
# 1) CLI 交互模式
# 2) Web API 服务
```

**方式2: 直接运行**

**CLI 模式**（推荐）:
```bash
# 从项目根目录运行
python3 run.py

# 或者使用模块方式
python3 -m src.app.main
```

**Web API 模式**:
```bash
# 从项目根目录运行
python3 -m src.api.server
```

> ⚠️ **注意**: 必须从项目根目录（`multi-task-question-answering-assistant/`）运行，不是从 `src/` 目录

### CLI 模式示例
```bash
python3 src/app/main.py
```

**Web API 模式**:
```bash
python3 src/api/server.py
# 访问: http://localhost:8000
# API 文档: http://localhost:8000/docs
```

## 💡 使用示例

### CLI 模式

```bash
$ python3 src/app/main.py

============================================================
🤖 Multi-Task QA Assistant v1.0.0
============================================================

我可以帮你:
  📌 查询天气（如：北京今天天气怎么样？）
  📌 搜索信息（如：搜索 LangChain 教程）
  📌 搜索新闻（如：最新的 AI 新闻）
  📌 回答问题（如：什么是机器学习？）

输入 'exit' 或 'quit' 退出
============================================================

你: 北京今天天气怎么样？

助手: 我来帮你查询北京的天气...
[调用天气工具]

北京今天晴天，温度 15-25℃，空气质量良好

你: 搜索 LangChain 教程

助手: 我来帮你搜索 LangChain 的教程...
[调用搜索工具]

找到5条关于'LangChain教程'的搜索结果:
...

你: exit

👋 再见！
```

### Web API 模式

**启动服务**:
```bash
python3 src/api/server.py
```

**访问 API 文档**:
- 打开浏览器访问: http://localhost:8000/docs
- Swagger UI 自动生成的交互式文档

**使用 curl 测试**:
```bash
# 健康检查
curl http://localhost:8000/health

# 系统信息
curl http://localhost:8000/info

# 查询接口
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "北京今天天气怎么样？"}'
```

**使用 Python 测试**:
```python
import requests

# 发送查询
response = requests.post(
    "http://localhost:8000/query",
    json={"query": "北京今天天气怎么样？"}
)

# 获取结果
data = response.json()
print(data["answer"])
```

## 🛠️ 可用功能

### 1. 天气查询

- **实时天气**: `北京今天天气怎么样？`
- **天气预报**: `上海未来3天天气如何？`

### 2. 信息搜索

- **网络搜索**: `搜索 LangChain 最新教程`
- **新闻搜索**: `最新的 AI 新闻`

### 3. 智能问答

- **知识问答**: `什么是机器学习？`
- **代码解释**: `解释一下 Python 的列表推导式`

## 📊 日志查看

日志文件位于 `logs/` 目录:

- `app_YYYY-MM-DD.log` - 完整日志
- `error_YYYY-MM-DD.log` - 错误日志

查看实时日志:
```bash
tail -f logs/app_$(date +%Y-%m-%d).log
```

## ⚙️ 配置说明

### 模型配置

在 `.env` 文件中:

```bash
# 模型选择
MODEL_NAME=gpt-4          # gpt-4, gpt-4-turbo, gpt-3.5-turbo
MODEL_TEMPERATURE=0.7      # 0.0-1.0，越高越随机
MODEL_MAX_TOKENS=2000      # 最大输出长度
```

### 动态模型选择

```bash
# 启用动态路由（根据任务复杂度自动选择模型）
ENABLE_DYNAMIC_ROUTING=true

# 成本优化模式
COST_OPTIMIZATION_ENABLED=true
PERFORMANCE_MODE=balanced  # cost | balanced | performance
```

## 🐛 故障排查

### 问题1: Python 版本不满足

**错误**: `ModuleNotFoundError: No module named 'langchain'`

**解决**: 确认 Python >= 3.10
```bash
python3 --version
# 如果低于 3.10，请升级 Python
```

### 问题2: API 密钥错误

**错误**: `AuthenticationError: Incorrect API key provided`

**解决**: 检查 `.env` 文件中的 `OPENAI_API_KEY`

### 问题3: 依赖安装失败

**错误**: `pip install 失败`

**解决**: 升级 pip
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 问题4: 工具调用失败

**错误**: `无法获取天气信息`

**解决**:
1. 检查网络连接
2. 配置相应的 API 密钥（高德、Tavily等）
3. 或者使用模拟数据（系统会自动降级）

## 📚 更多文档

- [项目架构文档](./项目结构说明文档.md) - 完整的架构设计
- [动态模型选择](./README_动态模型选择.md) - 智能路由系统
- [LangChain 1.x 文档](https://python.langchain.com/)

## 🎓 开发指南

### 添加新工具

1. 在 `src/tools/` 创建新文件
2. 使用 `@tool` 装饰器定义工具
3. 在 `src/agents/qa_agent.py` 中注册

示例:
```python
from langchain_core.tools import tool

@tool
def my_new_tool(param: str) -> str:
    """工具描述"""
    return f"处理结果: {param}"
```

### 自定义 Agent

修改 `src/agents/qa_agent.py` 中的 `system_prompt` 来自定义 Agent 行为。

## 📞 支持

如有问题，请查看:
1. 日志文件 `logs/` 目录
2. API 文档 http://localhost:8000/docs
3. 项目架构文档

---

**版本**: 1.0.0
**更新**: 2025-01-02
**技术栈**: LangChain >= 1.0 + Python >= 3.10

# 多智能体客服系统 (Multi-Agent Customer Service System)

> 基于 **AutoGen 框架** 的企业级多智能体客服系统，通过多个专业智能体协同工作处理客户服务问题，提供订单状态查询、物流信息查询等智能服务。

## 📖 项目概述

本系统采用多智能体协同架构，通过 AutoGen 框架实现订单查询智能体、物流查询智能体和结果汇总智能体三个专门智能体协同工作，自动化处理客户关于订单状态和物流信息的查询，提供智能化的回复服务。

**重要提示**: 本系统必须安装 AutoGen 框架才能运行，不支持基础模式。

### 核心特性

- 🤖 **多智能体协同**: 三个专业智能体协同工作，并行处理订单和物流查询
- 🔄 **接口调用重试**: 采用指数级退避策略的自动重试机制，提高系统稳定性
- 📊 **交互过程可视化**: 实时显示智能体之间的交互过程和消息传递
- 💬 **智能回复生成**: 整合查询结果，生成用户友好的自然语言回复
- 🚀 **高性能**: 异步处理和并发支持，提高响应速度
- 📝 **结构化日志**: 完整的日志记录和监控系统

### 智能体架构

| 智能体 | 职责 | 能力 |
|---------|------|------|
| Agent A (订单查询智能体) | 查询订单详细状态信息 | 订单状态、支付状态、发货状态等 |
| Agent B (物流查询智能体) | 查询物流跟踪信息 | 物流状态、当前位置、预计送达时间、物流轨迹 |
| Agent C (结果汇总智能体) | 整合信息并生成自然语言回复 | 智能意图理解、信息整合、友好回复生成 |

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户交互层                                │
│                    命令行界面 CLI                             │
└────────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────────▼────────────────────────────────────┐
│                         应用层                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ 查询解析器   │  │ 用户输入处理器 │  │ 交互可视化展示器 │   │
│  └──────────────┘  └──────────────┘  └──────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────────▼────────────────────────────────────┐
│                        智能体层                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ 订单查询智能体   │  │ 物流查询智能体   │  │结果汇总智能体│ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
│                 ┌─────────────────┐                           │
│                 │ 智能体通信管理器 │                           │
│                 └─────────────────┘                           │
└────────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────────▼────────────────────────────────────┐
│                         服务层                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐│
│  │ 模拟订单数据存储 │  │ 模拟物流数据存储 │  │ 重试机制服务 ││
│  └──────────────────┘  └──────────────────┘  └──────────────┘│
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 环境要求

- Python >= 3.8
- pip (Python 包管理器）
- **AutoGen 框架** (必须安装)

### 安装步骤

1. **克隆或下载项目**

```bash
cd src/app/multi-agent-customer-system
```

2. **创建虚拟环境（推荐）**

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**

```bash
# 安装所有依赖（包括 AutoGen）
pip install -r requirements.txt

# 或单独安装 AutoGen
pip install autogen-agentchat
```

**注意**: AutoGen 是本系统的核心依赖，必须安装后才能运行系统。如果遇到 ImportError 提示 AutoGen 未安装，请先安装 AutoGen：
```bash
pip install autogen-agentchat
```

4. **配置环境变量**

复制 `.env.example` 为 `.env` 并配置你的 API 密钥：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置以下配置：

```env
# OpenAI API 配置
OPENAI_API_KEY=your-openai-api-key-here
OPENAI_API_BASE=https://api.openai.com/v1

# 模型配置
MODEL_NAME=gpt-4
MODEL_TEMPERATURE=0.7
MODEL_MAX_TOKENS=2000

# API 服务配置
API_HOST=0.0.0.0
API_PORT=8001

# 重试机制配置
RETRY_INITIAL_DELAY=1
RETRY_MAX_DELAY=10
RETRY_MULTIPLIER=2
RETRY_MAX_ATTEMPTS=3

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=logs

# 应用配置
APP_NAME=Multi-Agent Customer Service System
APP_VERSION=1.0.0
DEBUG=false

# 可视化配置
VISUALIZE_AGENT_INTERACTION=true
SHOW_API_LOGS=true
```

5. **运行系统**

使用启动脚本（推荐）：

```bash
chmod +x start.sh
./start.sh
```

或直接运行：

```bash
python3 run.py
```

### 使用方式

#### 交互式模式（默认）

```bash
python3 run.py
```

在命令行界面中输入你的问题，例如：

```
您: 我的订单ORD001为什么还没发货？
您: 查询订单ORD002的物流信息
```

#### 命令行查询模式

```bash
python3 run.py -q "我的订单ORD001为什么还没发货？"
```

#### 启动 Web API 服务

```bash
python3 src/api/server.py
```

API 服务将在 `http://localhost:8001` 启动，访问：

- API 根路径: http://localhost:8001
- 订单 API: http://localhost:8001/orders
- 物流 API: http://localhost:8001/logistics
- API 文档: http://localhost:8001/docs

## 📁 项目结构

```
multi-agent-customer-system/
├── config/                 # 配置管理模块
│   ├── __init__.py
│   └── settings.py        # 基于 Pydantic Settings 的配置
├── core/                  # 核心模块
│   ├── __init__.py
│   └── logger.py          # 日志系统（基于 Loguru）
├── app/                   # 应用层
│   ├── __init__.py
│   ├── main.py            # 主应用入口（CLI 交互界面）
│   └── query_parser.py     # 查询解析器
├── agents/                # 智能体层
│   ├── __init__.py
│   ├── agent_manager.py    # 智能体通信管理器
│   ├── order_agent.py      # 订单查询智能体（Agent A）
│   ├── logistics_agent.py   # 物流查询智能体（Agent B）
│   └── summary_agent.py    # 结果汇总智能体（Agent C）
├── api/                   # API 服务层
│   ├── __init__.py
│   ├── server.py          # 统一 API 服务器
│   ├── order_api.py       # 订单查询 API
│   └── logistics_api.py   # 物流查询 API
├── services/              # 服务层
│   ├── __init__.py
│   ├── mock_data.py       # 模拟数据存储
│   └── retry_mechanism.py # 重试机制
├── middleware/            # 中间件模块（预留）
├── scripts/               # 脚本模块（预留）
├── tools/                # 工具模块（预留）
├── utils/                # 工具模块（预留）
├── tests/                # 测试模块
│   ├── unit/              # 单元测试
│   └── integration/       # 集成测试
├── docs/                 # 文档模块
├── logs/                 # 日志目录
├── requirements.txt        # Python 依赖
├── .env.example          # 环境变量示例
├── .env                 # 环境变量（需创建）
├── run.py               # 项目主入口
├── start.sh             # 启动脚本
└── README.md            # 项目说明文档
```

## 🔧 技术栈

### 核心框架

| 技术 | 版本 | 用途 |
|-----|------|------|
| **Python** | >= 3.8 | 编程语言 |
| **AutoGen** | >= 0.4.0 | 多智能体框架 (**必须**) |
| **FastAPI** | >= 0.104.1 | Web API 框架 |
| **Uvicorn** | >= 0.24.0 | ASGI 服务器 |

**重要说明**:
- AutoGen 是本系统的核心框架，必须安装
- 系统启动时会检查 AutoGen 是否可用，如果未安装会直接报错
- 不再支持基础模式或无 AutoGen 的运行方式

### 数据处理

| 技术 | 版本 | 用途 |
|-----|------|------|
| **Pydantic** | >= 2.7.4 | 数据验证和序列化 |
| **Pydantic-Settings** | >= 2.3.4 | 配置管理 |

### 异步和网络

| 技术 | 版本 | 用途 |
|-----|------|------|
| **httpx** | >= 0.25.0 | 异步 HTTP 客户端 |
| **tenacity** | >= 8.2.0 | 重试机制 |

### UI 和工具

| 技术 | 版本 | 用途 |
|-----|------|------|
| **Rich** | >= 13.7.0 | 丰富的命令行界面 |
| **Loguru** | >= 0.7.2 | 结构化日志 |
| **python-dotenv** | >= 1.0.0 | 环境变量管理 |

### AI 和语言模型

| 技术 | 版本 | 用途 |
|-----|------|------|
| **OpenAI** | >= 1.12.0 | OpenAI API 客户端 |

## 🤖 智能体交互示例

### 场景一：查询订单发货延迟

**用户提问**: "我的订单ORD001为什么还没发货？"

**处理流程**:

1. **查询解析器** 识别订单编号 `ORD001` 和查询意图 `order_status`
2. **智能体通信管理器** 分发任务：
   - Agent A: 查询订单 ORD001 状态
   - Agent B: 查询订单 ORD001 物流
3. **Agent A (订单查询智能体)** 查询订单数据：
   ```json
   {
     "order_id": "ORD001",
     "order_status": "待发货",
     "payment_status": "已支付",
     "shipping_status": "未发货"
   }
   ```
4. **Agent B (物流查询智能体)** 查询物流数据：
   ```json
   {
     "order_id": "ORD001",
     "logistics_status": "未发货",
     "current_location": "上海仓库"
   }
   ```
5. **Agent C (结果汇总智能体)** 整合信息并生成回复：
   ```
   关于订单 ORD001：

   📦 订单状态：待发货
   💳 支付状态：已支付
   🚚 发货状态：未发货

   您的订单已完成支付，商家正在准备发货中，请您耐心等待。
   ```

### 场景二：查询物流跟踪

**用户提问**: "我的订单ORD002的物流状态如何？"

**处理流程**:

1. **查询解析器** 识别订单编号 `ORD002` 和查询意图 `logistics`
2. **智能体通信管理器** 并行执行查询
3. **Agent A 和 Agent B** 各自查询数据
4. **Agent C** 生成智能回复：
   ```
   关于订单 ORD002：

   📦 订单状态：已发货
   🚄 物流状态：运输中
   📍 当前位置：北京转运中心
   ⏰ 预计送达：3天

   最新更新：2024-01-03T08:00:00Z - 运输中 @ 北京转运中心
   ```

## 🔌 API 接口

### 订单查询 API

**获取订单信息**

- **URL**: `GET /orders/api/v1/orders/{order_id}`
- **响应示例**:

```json
{
  "order_id": "ORD001",
  "created_time": "2024-01-01T10:00:00Z",
  "order_status": "待发货",
  "payment_status": "已支付",
  "shipping_status": "未发货",
  "total_amount": 299.00,
  "items": [
    {
      "product_id": "P001",
      "name": "商品A",
      "quantity": 1,
      "price": 199.00
    }
  ]
}
```

### 物流查询 API

**获取物流信息**

- **URL**: `GET /logistics/api/v1/logistics/{order_id}`
- **响应示例**:

```json
{
  "order_id": "ORD002",
  "logistics_status": "运输中",
  "current_location": "北京转运中心",
  "estimated_delivery": "3天",
  "tracking_history": [
    {
      "time": "2024-01-02T14:30:00Z",
      "status": "已发货",
      "location": "上海仓库"
    },
    {
      "time": "2024-01-03T08:00:00Z",
      "status": "运输中",
      "location": "北京转运中心"
    }
  ]
}
```

## 📊 重试机制

系统采用**指数级退避策略**（Exponential Backoff）处理 API 调用失败：

- **初始延迟**: 1 秒
- **退避因子**: 2（每次重试延迟时间翻倍）
- **最大延迟**: 10 秒
- **最大重试次数**: 3 次

**重试示例**:

| 重试次数 | 延迟时间 | 累计延迟 |
|---------|----------|----------|
| 第 1 次 | 1 秒 | 1 秒 |
| 第 2 次 | 2 秒 | 3 秒 |
| 第 3 次 | 4 秒 | 7 秒 |

**可重试错误**:
- `ConnectionError`: 网络连接错误
- `TimeoutError`: 超时错误
- `asyncio.TimeoutError`: 异步超时

**不可重试错误**:
- `ValueError`: 数据格式错误
- `KeyError`: 订单不存在
- `LookupError`: 查找失败

## 📝 配置说明

详细配置说明请参考 `.env.example` 文件。主要配置项：

- **MODEL_NAME**: AI 模型名称（gpt-4, gpt-4-turbo, gpt-3.5-turbo）
- **MODEL_TEMPERATURE**: 模型温度（0.0-1.0）
- **MODEL_MAX_TOKENS**: 最大生成 token 数
- **API_PORT**: API 服务端口
- **RETRY_MAX_ATTEMPTS**: 最大重试次数
- **LOG_LEVEL**: 日志级别（DEBUG, INFO, WARNING, ERROR）
- **VISUALIZE_AGENT_INTERACTION**: 是否显示智能体交互过程
- **SHOW_API_LOGS**: 是否显示 API 调用日志

## 🧪 支持的查询类型

1. **订单状态查询**
   - "我的订单ORD001为什么还没发货？"
   - "查询订单ORD002的状态"
   - "订单ORD003的支付情况如何"

2. **物流信息查询**
   - "我的订单ORD001的物流状态如何？"
   - "查询订单ORD002的物流轨迹"
   - "我的包裹ORD003什么时候能送到"

3. **综合查询**
   - "我的订单ORD001怎么样了？"
   - "告诉我订单ORD002的所有信息"

## 🔍 测试数据

系统内置了以下测试订单数据：

| 订单编号 | 订单状态 | 支付状态 | 发货状态 | 物流状态 |
|---------|---------|---------|---------|---------|
| ORD001 | 待发货 | 已支付 | 未发货 | 未发货 |
| ORD002 | 已发货 | 已支付 | 运输中 | 运输中 |
| ORD003 | 已完成 | 已支付 | 已送达 | 已送达 |
| ORD004 | 已取消 | 未支付 | 未发货 | 已取消 |
| ORD005 | 支付中 | 待支付 | 未发货 | 待发货 |

## 📧 常见问题

### Q: 系统启动时提示 "AutoGen 框架未安装" 怎么办？

A: 请运行以下命令安装 AutoGen:
```bash
pip install autogen-agentchat
```
如果遇到网络问题，可以使用国内镜像源：
```bash
pip install autogen-agentchat -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: 如何启用 OpenAI API？

A: 在 `.env` 文件中设置正确的 `OPENAI_API_KEY`。如果你使用代理，还需要设置 `OPENAI_API_BASE`。

### Q: 智能体交互过程如何查看？

A: 系统默认会显示智能体交互过程（基于 AutoGen）。你也可以在日志文件 `logs/agent_interaction_YYYY-MM-DD.log` 中查看详细记录。

### Q: 如何自定义重试策略？

A: 在 `.env` 文件中修改以下配置：
- `RETRY_INITIAL_DELAY`: 初始延迟时间
- `RETRY_MAX_DELAY`: 最大延迟时间
- `RETRY_MULTIPLIER`: 退避因子
- `RETRY_MAX_ATTEMPTS`: 最大重试次数

### Q: 系统支持基础模式吗？

A: **不支持**。本系统必须使用 AutoGen 框架运行。如果 AutoGen 未安装，系统会在启动时报错并提示安装。这是为了确保系统能够充分利用 AutoGen 的多智能体协同能力。

### Q: 如何添加新的智能体？

A: 参考现有的智能体实现（`agents/` 目录），创建新的智能体类（必须基于 AutoGen 的 AssistantAgent），然后在 `agent_manager.py` 中集成。

## 📄 许可证

本项目仅供学习和参考使用。

## 👨‍💻 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题或建议，欢迎通过 Issues 联系。

---

**祝你使用愉快！** 🎉
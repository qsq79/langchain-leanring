# 工具使用 (Tools)

本目录包含 AutoGen AgentChat 中工具使用的示例，展示如何为 Agent 配置和使用各种工具。

## 学习目标

通过本章节的学习，你将掌握：
- 如何创建和定义工具
- 如何为 Agent 配置工具
- Python 函数作为工具
- 工具调用和参数处理
- 代码执行工具

## 示例列表

### Demo 29: Python 函数工具 (`demo_29_python_functions.py`)

展示 Python 函数作为工具的使用：
- 定义 Python 函数
- 将函数注册为工具
- Agent 调用工具
- 处理工具返回结果
- 参数验证和错误处理

**适用场景**：
- 快速原型开发
- 简单的计算和处理任务
- 不需要外部 API 的场景

### Demo 30: 工具调用 (`demo_30_tool_usage.py`)

展示工具调用的完整流程：
- 工具定义和注册
- Agent 识别何时使用工具
- 参数传递和类型转换
- 工具执行结果处理
- 多工具组合使用

**适用场景**：
- 需要访问外部 API
- 数据库查询和操作
- 文件系统访问
- 网络请求

### Demo 31: 代码执行 (`demo_31_code_execution.py`)

展示代码执行工具的使用：
- 安全的代码执行环境
- Python 代码执行
- 捕获执行输出
- 错误处理和限制
- 沙箱环境

**适用场景**：
- 代码生成和测试
- 数据处理脚本
- 算法验证
- 快速原型

## 关键概念

### Tool (工具)

工具是 Agent 可以调用的函数或服务，特点包括：
- 扩展 Agent 的能力
- 访问外部系统
- 执行特定操作
- 返回结构化结果

### 工具定义

在 AutoGen 中，工具通常定义为：
- Python 函数
- 带有类型注解的参数
- 返回结构化数据
- 包含文档字符串

### 工具注册

将工具注册到 Agent：
- 在创建 Agent 时指定
- 通过 `tools` 参数传递
- 可以传递单个工具或工具列表
- 支持动态添加和移除

### 工具调用流程

工具调用的完整流程：
1. Agent 分析任务
2. 识别需要的工具
3. 构造工具调用参数
4. 执行工具函数
5. 获取返回结果
6. 基于结果继续任务

## 工具类型对比

| 类型 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| Python 函数 | 简单、快速、本地执行 | 受限于本地环境 | 计算任务、数据处理 |
| API 工具 | 功能强大、可访问远程 | 需要网络、依赖外部服务 | 查询服务、远程操作 |
| 代码执行 | 灵活、可执行任意代码 | 安全风险、需要限制 | 代码测试、原型验证 |

## 最佳实践

1. **工具设计**
   - 单一职责原则
   - 清晰的参数命名
   - 完善的文档字符串
   - 合理的错误处理

2. **安全性考虑**
   - 代码执行使用沙箱
   - 验证输入参数
   - 限制资源使用
   - 避免敏感操作

3. **错误处理**
   - 提供有意义的错误信息
   - 使用适当的异常类型
   - 记录错误日志
   - 优雅降级

4. **性能优化**
   - 缓存工具结果
   - 并发执行独立工具
   - 限制工具调用次数
   - 优化复杂操作

5. **测试和验证**
   - 单元测试每个工具
   - 测试边界条件
   - 验证返回类型
   - 集成测试

## 工具示例

### 简单计算工具

```python
def calculate_sum(a: float, b: float) -> float:
    """计算两个数的和
    
    Args:
        a: 第一个数
        b: 第二个数
    
    Returns:
        两个数的和
    """
    return a + b
```

### API 调用工具

```python
import requests

def get_weather(city: str) -> dict:
    """获取指定城市的天气信息
    
    Args:
        city: 城市名称
    
    Returns:
        包含天气信息的字典
    """
    response = requests.get(f"https://api.weather.com/{city}")
    return response.json()
```

### 文件操作工具

```python
import os

def read_file(filepath: str) -> str:
    """读取文件内容
    
    Args:
        filepath: 文件路径
    
    Returns:
        文件内容
    """
    with open(filepath, 'r') as f:
        return f.read()
```

## 与其他模块的关系

- **Basics**: Agent 使用工具扩展能力
- **Conversations**: 工具调用可以在对话中进行
- **Teams**: 团队中的 Agent 可以共享和使用工具
- **Advanced**: 高级模式提供更复杂的工具管理

## 学习路径

1. 先学习 `basics/` 中的单个 Agent 使用
2. 理解 `conversations/` 中的对话模式
3. 学习 `teams/` 中的团队协作
4. 学习本目录中的工具使用
5. 进阶到 `advanced/` 中的高级特性

## 相关文档

- [AutoGen 官方文档 - Tools](https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/tools.html)
- [AgentChat API 参考](https://microsoft.github.io/autogen/stable/api/python/autogen_agentchat.html)

## 常见问题

### Q: 如何创建一个工具？

A: 定义一个 Python 函数，包含适当的参数类型注解和文档字符串，然后在创建 Agent 时通过 `tools` 参数注册。

### Q: 工具可以调用其他工具吗？

A: 可以。工具可以组合使用，也可以在工具中调用其他工具或服务。

### Q: 如何处理工具执行错误？

A: 在工具函数中使用 try-except 捕获异常，返回有意义的错误信息，Agent 可以根据错误信息调整策略。

### Q: 工具的参数如何传递？

A: Agent 会根据工具的定义和任务需求自动构造参数，确保参数类型和名称匹配。

### Q: 可以限制工具的使用次数吗？

A: 可以。可以通过中间件或自定义逻辑来跟踪和控制工具的使用次数。

## 下一步

完成本章节后，建议继续学习：
- `advanced/`: 高级特性
- `03-extensions/`: 扩展功能
- `04-integration/`: 集成案例